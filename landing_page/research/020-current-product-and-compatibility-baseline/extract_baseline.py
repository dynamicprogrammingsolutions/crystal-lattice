#!/usr/bin/env python3
"""Extract stable task-020 catalog rows from the checked-in default config."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
import re
import sys
from pathlib import Path
from typing import Any, Iterable, Mapping
from unittest.mock import patch


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
CORE = ROOT / "core/python"
SCRIPTS = ROOT / "scripts"
for path in (CORE, SCRIPTS):
    if str(path) not in sys.path:
        sys.path.insert(0, str(path))

from agent_app.config import build_agent_config, load_raw_config, load_resolved_config
from build_plugin_packaging_support import analyze_packaging_plugins


CONFIG = ROOT / "application/python/agent_terminal_app/default_config/config.json"
PLUGINS = ROOT / "plugins"
SCHEMA = HERE / "catalog-schema.json"
MANIFEST = HERE / "input-manifest.json"
OPTIONAL_FEATURES = HERE / "optional-feature-inputs.json"
REVIEW_OVERRIDES = HERE / "catalog-review-overrides.json"
CLAIM_EVIDENCE = HERE / "claim-evidence.jsonl"
SEPARATOR = "|"

ENV_OVERRIDES = {
    "CONFIG_DIR": str(CONFIG.parent),
    "BUILTIN_PLUGINS": str(PLUGINS),
    "WORKING_DIR": str(ROOT),
    "CLOUD_RUNTIME_BUILD_CONTEXT": str(
        CONFIG.parent / "__cloud_runtime_build_context__"
    ),
    "OPENROUTER_API_KEY": "audit-placeholder",
    "ANTHROPIC_API_KEY": "audit-placeholder",
    "OPENAI_API_KEY": "audit-placeholder",
    "FIREWORKS_API_KEY": "audit-placeholder",
    "ZAI_API_KEY": "audit-placeholder",
    "GEMINI_API_KEY": "audit-placeholder",
    "TAVILY_API_KEY": "audit-placeholder",
    "CLOUD_ORCHESTRATOR_URL": "http://audit.invalid",
    "CLOUD_ORCHESTRATOR_TOKEN": "audit-placeholder",
}

DEFAULT_REVIEW_VALUES = {
    "capability_state": "unknown",
    "source_presence": "present",
    "packaging_state": "unknown",
    "default_enablement": "unknown",
    "http_support": "unknown",
    "terminal_support": "unknown",
    "mobile_support": "unknown",
    "desktop_support": "unknown",
    "verification_state": "unknown",
    "real_provider_verification": "unknown",
    "confidence": "unresolved",
    "review_state": "generated",
}


def _join(values: Iterable[Any]) -> str:
    return SEPARATOR.join(str(value) for value in values if value not in (None, ""))


def _text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, separators=(",", ":"))
    return str(value)


def _source_commit() -> str:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    return str(manifest["source_commit"])


def _schema() -> dict[str, Any]:
    return json.loads(SCHEMA.read_text(encoding="utf-8"))


def _fieldnames(catalog_name: str) -> list[str]:
    catalog = _schema()["catalogs"][catalog_name]
    return [*catalog["generated_fields"], *catalog["review_fields"]]


def _review_fields(catalog_name: str) -> set[str]:
    return set(_schema()["catalogs"][catalog_name]["review_fields"])


def _review_overrides(catalog_name: str, row_id: str) -> dict[str, Any]:
    if not REVIEW_OVERRIDES.is_file():
        return {}
    payload = json.loads(REVIEW_OVERRIDES.read_text(encoding="utf-8"))
    catalogs = payload.get("catalogs") or {}
    catalog = catalogs.get(catalog_name) or {}
    override = catalog.get(row_id) or {}
    if not isinstance(override, dict):
        return {}
    unknown = set(override) - _review_fields(catalog_name)
    if unknown:
        raise ValueError(
            f"{REVIEW_OVERRIDES.name}:{catalog_name}:{row_id}: "
            f"unknown review fields {sorted(unknown)}"
        )
    return override


def _existing_rows(path: Path) -> dict[str, dict[str, str]]:
    if not path.is_file():
        return {}
    with path.open(newline="", encoding="utf-8") as stream:
        return {row["row_id"]: row for row in csv.DictReader(stream)}


def _with_review_defaults(
    catalog_name: str,
    generated: Mapping[str, Any],
    existing: Mapping[str, str] | None,
) -> dict[str, str]:
    row = {field: "" for field in _fieldnames(catalog_name)}
    for field, value in generated.items():
        row[field] = _text(value)
    for field in _review_fields(catalog_name):
        if existing and existing.get(field, "") != "":
            row[field] = existing[field]
        elif field in DEFAULT_REVIEW_VALUES:
            row[field] = DEFAULT_REVIEW_VALUES[field]
    for field, value in _review_overrides(
        catalog_name,
        str(generated["row_id"]),
    ).items():
        row[field] = _text(value)
    return row


def _plugin_project_from_spec(spec: str) -> tuple[str, str, Path | None]:
    if spec.startswith("path:"):
        path = Path(spec[5:]).resolve()
        return "path", path.name, path
    if spec.startswith("bash:"):
        path = Path(spec[5:]).resolve()
        return "bash", path.name, path
    if spec.startswith("node:"):
        path = Path(spec[5:]).resolve()
        return "node", path.name, path
    return "python", spec.rsplit(".", 1)[-1], None


def _descriptor(project_path: Path | None) -> dict[str, Any]:
    if project_path is None:
        return {}
    descriptor = project_path / "agent_plugin.json"
    if not descriptor.is_file():
        return {}
    return json.loads(descriptor.read_text(encoding="utf-8"))


def _descriptor_kinds(descriptor: Mapping[str, Any]) -> list[str]:
    explicit = sorted(set((descriptor.get("kinds") or {}).values()))
    if explicit:
        return explicit
    plugin_type = str(descriptor.get("plugin_type") or "").strip().lower()
    type_map = {
        "application": "application",
        "extension": "extensions",
        "feature": "features",
        "provider": "providers",
        "tool": "tools",
    }
    if plugin_type in type_map:
        return [type_map[plugin_type]]
    inferred = set()
    for entry in descriptor.get("entries") or []:
        class_name = str(entry).rsplit(".", 1)[-1]
        if class_name.endswith("AppPlugin"):
            inferred.add("application")
        elif class_name.endswith("Extension"):
            inferred.add("extensions")
        elif class_name.endswith("Feature"):
            inferred.add("features")
        elif class_name.endswith("Provider"):
            inferred.add("providers")
        elif class_name.endswith("Tool"):
            inferred.add("tools")
    return sorted(inferred)


def _agent_rows(
    raw: Mapping[str, Any],
    resolved: Mapping[str, Any],
    selected_projects: set[str],
    source_commit: str,
) -> list[dict[str, Any]]:
    rows = []
    raw_agents = raw.get("agents") or {}
    resolved_agents = resolved.get("agents") or {}
    for agent_id in sorted(raw_agents):
        raw_agent = raw_agents[agent_id]
        resolved_agent = resolved_agents[agent_id]
        effective = build_agent_config(resolved, agent_id)
        raw_specs = list(raw_agent.get("plugins") or [])
        resolved_specs = list(resolved_agent.get("plugins") or [])
        project_names = {
            _plugin_project_from_spec(str(spec))[1]
            for spec in resolved_specs
            if isinstance(spec, str)
        }
        packaging = (
            "selected_source_config"
            if project_names and project_names.issubset(selected_projects)
            else "unknown"
        )
        rows.append(
            {
                "row_id": f"agent:{agent_id}",
                "agent_id": agent_id,
                "provider_route": raw_agent.get("provider", ""),
                "provider_plugin": effective.get("provider", ""),
                "model": effective.get("model", ""),
                "auth_mode": effective.get("auth_mode", ""),
                "mixin_refs": _join(raw_agent.get("mixin_refs") or []),
                "agent_plugin_specs": _join(raw_specs),
                "disabled_plugins": _join(
                    resolved_agent.get("disabled_plugins") or []
                ),
                "enabled_plugins": _join(
                    resolved_agent.get("enabled_plugins") or []
                ),
                "shell_tool_mode": effective.get("shell_tool_mode", ""),
                "reasoning_enabled": effective.get("enable_reasoning", ""),
                "reasoning_effort": effective.get("reasoning_effort", ""),
                "system_message_enabled": effective.get(
                    "system_message_enabled", ""
                ),
                "mcp_enabled": effective.get("mcp_enabled", ""),
                "skills_enabled": effective.get("skills_enabled", ""),
                "source_presence": "present",
                "packaging_state": packaging,
                "loading_scope": "configured_agent",
                "default_enablement": "configured_profile",
                "source_commit": source_commit,
                "source_path": (
                    "application/python/agent_terminal_app/default_config/"
                    "config.json"
                ),
            }
        )
    return rows


def _provider_rows(
    raw: Mapping[str, Any],
    resolved: Mapping[str, Any],
    selected_projects: set[str],
    source_commit: str,
) -> list[dict[str, Any]]:
    rows = []
    raw_providers = raw.get("providers") or {}
    resolved_providers = resolved.get("providers") or {}
    for provider_id in sorted(raw_providers):
        raw_provider = raw_providers[provider_id]
        provider = resolved_providers[provider_id]
        raw_specs = list(raw_provider.get("plugins") or [])
        resolved_specs = list(provider.get("plugins") or [])
        project_names = {
            _plugin_project_from_spec(str(spec))[1]
            for spec in resolved_specs
            if isinstance(spec, str)
        }
        packaging = (
            "selected_source_config"
            if not project_names or project_names.issubset(selected_projects)
            else "unknown"
        )
        api_key = raw_provider.get("api_key", "")
        rows.append(
            {
                "row_id": f"provider:{provider_id}",
                "provider_id": provider_id,
                "provider_plugin": provider.get("provider", provider_id),
                "base_url": raw_provider.get("base_url", ""),
                "auth_mode": provider.get("auth_mode", ""),
                "api_key_reference": api_key,
                "configured_model": provider.get("model", ""),
                "provider_plugin_specs": _join(raw_specs),
                "reasoning_enabled": provider.get("enable_reasoning", ""),
                "reasoning_effort": provider.get("reasoning_effort", ""),
                "source_presence": "present",
                "packaging_state": packaging,
                "loading_scope": "provider_route",
                "default_enablement": "configured_route",
                "source_commit": source_commit,
                "source_path": (
                    "application/python/agent_terminal_app/default_config/"
                    "config.json"
                ),
            }
        )
    return rows


def _normalize_feature_id(source_kind: str, project_name: str, spec: str) -> str:
    if source_kind in {"path", "bash", "node"}:
        return project_name
    return re.sub(r"[^a-z0-9]+", "-", spec.lower()).strip("-")


def _feature_default_enablement(
    *,
    source_kind: str,
    descriptor_kinds: Iterable[str],
    loading_scope: str,
) -> str:
    if loading_scope == "optional_not_default":
        return "optional"
    kinds = set(descriptor_kinds)
    if source_kind == "python" or (kinds and kinds <= {"application", "features"}):
        return "default_enabled"
    return "conditional"


def _feature_rows(
    raw: Mapping[str, Any],
    resolved: Mapping[str, Any],
    selected_projects: set[str],
    local_projects: set[str],
    source_commit: str,
) -> list[dict[str, Any]]:
    rows = []
    raw_specs = list(raw.get("plugins") or [])
    resolved_specs = list(resolved.get("plugins") or [])
    if len(raw_specs) != len(resolved_specs):
        raise RuntimeError("Global plugin spec count changed during resolution")
    for raw_value, resolved_value in zip(raw_specs, resolved_specs):
        raw_spec = str(raw_value)
        resolved_spec = str(resolved_value)
        source_kind, project_name, project_path = _plugin_project_from_spec(
            resolved_spec
        )
        feature_id = _normalize_feature_id(
            source_kind, project_name, resolved_spec
        )
        descriptor = _descriptor(project_path)
        entries = list(descriptor.get("entries") or [])
        kinds = _descriptor_kinds(descriptor)
        dependencies = [
            item.get("name", "")
            for item in descriptor.get("local_workspace_dependencies") or []
            if isinstance(item, dict)
        ]
        if project_name in selected_projects:
            packaging = "selected_source_config"
        elif project_name in local_projects:
            packaging = "selected_dependency"
        else:
            packaging = "unknown" if source_kind == "python" else "not_selected"
        rows.append(
            {
                "row_id": f"feature:{feature_id}",
                "plugin_spec": raw_spec,
                "plugin_id": feature_id,
                "source_kind": source_kind,
                "project_name": project_name,
                "descriptor_entries": _join(entries),
                "descriptor_kinds": _join(kinds),
                "local_dependencies": _join(dependencies),
                "source_presence": (
                    "present"
                    if project_path is None or project_path.exists()
                    else "absent"
                ),
                "packaging_state": packaging,
                "loading_scope": "global",
                "default_enablement": _feature_default_enablement(
                    source_kind=source_kind,
                    descriptor_kinds=kinds,
                    loading_scope="global",
                ),
                "source_commit": source_commit,
                "source_path": (
                    str(project_path.relative_to(ROOT))
                    if project_path is not None and project_path.is_relative_to(ROOT)
                    else (
                        "application/python/agent_terminal_app/default_config/"
                        "config.json"
                    )
                ),
            }
        )
    optional_input = json.loads(OPTIONAL_FEATURES.read_text(encoding="utf-8"))
    existing_ids = {str(row["plugin_id"]) for row in rows}
    for item in optional_input.get("features") or []:
        if not isinstance(item, dict):
            continue
        project_name = str(item.get("project_name") or "").strip()
        if not project_name or project_name in existing_ids:
            continue
        project_path = PLUGINS / project_name
        descriptor = _descriptor(project_path)
        entries = list(descriptor.get("entries") or [])
        kinds = _descriptor_kinds(descriptor)
        dependencies = [
            dependency.get("name", "")
            for dependency in descriptor.get("local_workspace_dependencies") or []
            if isinstance(dependency, dict)
        ]
        packaging = (
            "selected_dependency"
            if project_name in local_projects
            else "not_selected"
        )
        rows.append(
            {
                "row_id": f"feature:{project_name}",
                "plugin_spec": f"path:${{env:BUILTIN_PLUGINS}}/{project_name}",
                "plugin_id": project_name,
                "source_kind": "path",
                "project_name": project_name,
                "descriptor_entries": _join(entries),
                "descriptor_kinds": _join(kinds),
                "local_dependencies": _join(dependencies),
                "source_presence": (
                    "present" if project_path.is_dir() else "absent"
                ),
                "packaging_state": packaging,
                "loading_scope": "optional_not_default",
                "default_enablement": _feature_default_enablement(
                    source_kind="path",
                    descriptor_kinds=kinds,
                    loading_scope="optional_not_default",
                ),
                "source_commit": source_commit,
                "source_path": f"plugins/{project_name}",
                "reviewer_note": str(item.get("reason") or ""),
            }
        )
    return sorted(rows, key=lambda row: row["row_id"])


def _write_catalog(name: str, generated_rows: list[dict[str, Any]]) -> None:
    path = HERE / name
    existing = _existing_rows(path)
    rows = [
        _with_review_defaults(name, row, existing.get(str(row["row_id"])))
        for row in generated_rows
    ]
    with path.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(
            stream,
            fieldnames=_fieldnames(name),
            lineterminator="\n",
        )
        writer.writeheader()
        writer.writerows(rows)


def _check_catalog(name: str, generated_rows: list[dict[str, Any]]) -> list[str]:
    path = HERE / name
    if not path.is_file():
        return [f"{name}: missing"]
    with path.open(newline="", encoding="utf-8") as stream:
        reader = csv.DictReader(stream)
        actual_rows = list(reader)
        actual_fields = list(reader.fieldnames or [])
    expected_fields = _fieldnames(name)
    errors = []
    if actual_fields != expected_fields:
        errors.append(f"{name}: header mismatch")
    actual_by_id = {row.get("row_id", ""): row for row in actual_rows}
    expected_ids = {str(row["row_id"]) for row in generated_rows}
    if set(actual_by_id) != expected_ids:
        errors.append(
            f"{name}: row ids differ actual={sorted(actual_by_id)} "
            f"expected={sorted(expected_ids)}"
        )
    generated_fields = _schema()["catalogs"][name]["generated_fields"]
    for expected in generated_rows:
        row_id = str(expected["row_id"])
        actual = actual_by_id.get(row_id)
        if actual is None:
            continue
        for field in generated_fields:
            expected_value = _text(expected.get(field, ""))
            if actual.get(field, "") != expected_value:
                errors.append(
                    f"{name}:{row_id}:{field}: "
                    f"{actual.get(field, '')!r} != {expected_value!r}"
                )
    return errors


def _check_review_and_evidence(
    catalogs: Mapping[str, list[dict[str, Any]]],
) -> list[str]:
    errors: list[str] = []
    row_ids = {
        str(row["row_id"])
        for rows in catalogs.values()
        for row in rows
    }
    overrides = json.loads(REVIEW_OVERRIDES.read_text(encoding="utf-8"))
    for catalog_name, catalog_overrides in (
        overrides.get("catalogs") or {}
    ).items():
        if catalog_name not in catalogs:
            errors.append(f"{REVIEW_OVERRIDES.name}: unknown catalog {catalog_name}")
            continue
        expected_ids = {str(row["row_id"]) for row in catalogs[catalog_name]}
        for row_id in catalog_overrides:
            if row_id not in expected_ids:
                errors.append(
                    f"{REVIEW_OVERRIDES.name}:{catalog_name}: "
                    f"unknown row {row_id}"
                )

    required = set(_schema()["evidence_record"]["required_fields"])
    claim_ids: set[str] = set()
    claim_rows: dict[str, dict[str, Any]] = {}
    for line_number, line in enumerate(
        CLAIM_EVIDENCE.read_text(encoding="utf-8").splitlines(),
        1,
    ):
        if not line.strip():
            continue
        try:
            claim = json.loads(line)
        except json.JSONDecodeError as exc:
            errors.append(f"{CLAIM_EVIDENCE.name}:{line_number}: {exc}")
            continue
        missing = sorted(required - set(claim))
        if missing:
            errors.append(
                f"{CLAIM_EVIDENCE.name}:{line_number}: missing {missing}"
            )
        claim_id = str(claim.get("claim_id") or "")
        if not claim_id:
            errors.append(
                f"{CLAIM_EVIDENCE.name}:{line_number}: empty claim_id"
            )
        elif claim_id in claim_ids:
            errors.append(
                f"{CLAIM_EVIDENCE.name}:{line_number}: duplicate {claim_id}"
            )
        else:
            claim_ids.add(claim_id)
            claim_rows[claim_id] = claim
        for row_id in claim.get("row_ids") or []:
            if str(row_id) not in row_ids:
                errors.append(
                    f"{CLAIM_EVIDENCE.name}:{line_number}: "
                    f"unknown row {row_id}"
                )

    for catalog_name, path_rows in (
        (name, _existing_rows(HERE / name)) for name in catalogs
    ):
        for row_id, row in path_rows.items():
            for evidence_id in filter(
                None,
                row.get("evidence_ids", "").split(SEPARATOR),
            ):
                if evidence_id not in claim_rows:
                    errors.append(
                        f"{catalog_name}:{row_id}: "
                        f"unknown evidence_id {evidence_id}"
                    )
    return errors


def _update_manifest(
    *,
    resolved_errors: list[dict[str, Any]],
    selected_projects: set[str],
    local_projects: set[str],
) -> None:
    manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
    broader_execution = manifest.get("broader_audit_execution") or {}
    human_review = (
        broader_execution.get("human_review")
        if isinstance(broader_execution, dict)
        else None
    )
    website_projection = manifest.get("website_projection") or {}
    human_review_status = (
        human_review.get("status") if isinstance(human_review, dict) else None
    )
    if manifest.get("completion_manifest") or manifest.get("status") == "complete":
        manifest["status"] = "complete"
    elif human_review_status == "pending":
        manifest["status"] = "awaiting_human_review"
    elif (
        human_review_status == "approved"
        and isinstance(website_projection, dict)
        and website_projection.get("status") == "needs_review"
    ):
        manifest["status"] = "awaiting_website_projection_review"
    elif human_review_status == "approved":
        manifest["status"] = "human_review_complete"
    elif broader_execution:
        manifest["status"] = "in_progress_broader_audit"
    else:
        manifest["status"] = "in_progress_catalog_extraction_complete"
    manifest["transformation_version"] = "compatibility-baseline-v2"
    manifest["catalog_schema"] = "catalog-schema.json"
    manifest["extractor"] = "extract_baseline.py"
    manifest["resolved_config_summary"] = {
        "agent_ids": 20,
        "provider_routes": 7,
        "global_plugin_specs": 28,
        "selected_plugin_projects": len(selected_projects),
        "selected_local_plugin_projects": len(local_projects),
        "warning_types": sorted(
            {
                str(error.get("type"))
                for error in resolved_errors
                if error.get("type")
            }
        ),
    }
    manifest["catalog_outputs"] = {
        "configured_agent_rows": 20,
        "provider_account_rows": 7,
        "application_feature_rows": 33,
        "global_application_feature_rows": 28,
        "optional_application_feature_rows": 5,
        "generated_fields_refreshable": True,
        "review_fields_preserved_on_refresh": True,
        "human_review_complete": human_review_status == "approved",
    }
    MANIFEST.write_text(
        json.dumps(manifest, indent=2, sort_keys=False) + "\n",
        encoding="utf-8",
    )


def _inputs() -> tuple[
    dict[str, Any],
    dict[str, Any],
    list[dict[str, Any]],
    set[str],
    set[str],
]:
    raw = load_raw_config(CONFIG)
    with patch.dict(os.environ, ENV_OVERRIDES, clear=False):
        resolved, errors, _ = load_resolved_config(
            CONFIG,
            env={},
            env_overrides=ENV_OVERRIDES,
        )
        analysis = analyze_packaging_plugins(
            config_path=CONFIG,
            plugins_root=PLUGINS,
        )
    fatal_errors = [
        error
        for error in [*errors, *analysis.config_errors]
        if error.get("severity") != "warning" and error.get("type") != "env_missing"
    ]
    if fatal_errors:
        raise RuntimeError(json.dumps(fatal_errors, indent=2))
    return (
        raw,
        resolved,
        [*errors, *analysis.config_errors],
        set(analysis.selected_plugin_names),
        set(analysis.local_project_names),
    )


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Validate generated fields without rewriting review fields.",
    )
    args = parser.parse_args()

    raw, resolved, errors, selected_projects, local_projects = _inputs()
    source_commit = _source_commit()
    catalogs = {
        "configured-agent-compatibility.csv": _agent_rows(
            raw, resolved, selected_projects, source_commit
        ),
        "provider-account-compatibility.csv": _provider_rows(
            raw, resolved, selected_projects, source_commit
        ),
        "application-feature-compatibility.csv": _feature_rows(
            raw, resolved, selected_projects, local_projects, source_commit
        ),
    }
    if args.check:
        check_errors = []
        for name, rows in catalogs.items():
            check_errors.extend(_check_catalog(name, rows))
        check_errors.extend(_check_review_and_evidence(catalogs))
        if check_errors:
            print("\n".join(check_errors), file=sys.stderr)
            return 1
        config_hash = hashlib.sha256(CONFIG.read_bytes()).hexdigest()
        manifest = json.loads(MANIFEST.read_text(encoding="utf-8"))
        if manifest.get("source_config_sha256") != config_hash:
            print("input-manifest.json: source_config_sha256 mismatch", file=sys.stderr)
            return 1
        print("catalog extraction check passed")
        return 0

    for name, rows in catalogs.items():
        _write_catalog(name, rows)
    _update_manifest(
        resolved_errors=errors,
        selected_projects=selected_projects,
        local_projects=local_projects,
    )
    print(
        "wrote "
        + ", ".join(f"{name}={len(rows)}" for name, rows in catalogs.items())
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())