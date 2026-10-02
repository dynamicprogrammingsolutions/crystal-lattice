#!/usr/bin/env python3
"""Generate the maintained product compatibility matrices."""

from __future__ import annotations

import argparse
import copy
import csv
import io
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

from agent_app.config import load_raw_config, load_resolved_config
from build_plugin_packaging_support import analyze_packaging_plugins


CONFIG = ROOT / "application/python/agent_terminal_app/default_config/config.json"
PLUGINS = ROOT / "plugins"
SOURCE = HERE / "compatibility-matrix-source.json"
FEATURE_REVIEW = HERE / "application-feature-compatibility.csv"

FEATURE_JSON = HERE / "feature-catalog.json"
FEATURE_CSV = HERE / "feature-catalog.csv"
PROVIDER_JSON = HERE / "provider-support-matrix.json"
PROVIDER_CSV = HERE / "provider-support-matrix.csv"
MODEL_JSON = HERE / "model-family-feature-matrix.json"
MODEL_CSV = HERE / "model-family-feature-matrix.csv"
MARKDOWN = HERE / "compatibility-matrices.md"

VALID_CELL_STATUSES = {
    "supported",
    "conditional",
    "planned",
    "unsupported",
    "not_applicable",
    "unknown",
}

ENV_OVERRIDES = {
    "CONFIG_DIR": str(CONFIG.parent),
    "BUILTIN_PLUGINS": str(PLUGINS),
    "WORKING_DIR": str(ROOT),
    "CLOUD_RUNTIME_BUILD_CONTEXT": str(
        CONFIG.parent / "__cloud_runtime_build_context__"
    ),
    "OPENROUTER_API_KEY": "matrix-placeholder",
    "ANTHROPIC_API_KEY": "matrix-placeholder",
    "OPENAI_API_KEY": "matrix-placeholder",
    "FIREWORKS_API_KEY": "matrix-placeholder",
    "ZAI_API_KEY": "matrix-placeholder",
    "GEMINI_API_KEY": "matrix-placeholder",
    "TAVILY_API_KEY": "matrix-placeholder",
    "CLOUD_ORCHESTRATOR_URL": "http://matrix.invalid",
    "CLOUD_ORCHESTRATOR_TOKEN": "matrix-placeholder",
}


def _join(values: Iterable[Any]) -> str:
    return "|".join(str(value) for value in values if value not in ("", None))


def _source_payload() -> dict[str, Any]:
    return json.loads(SOURCE.read_text(encoding="utf-8"))


def _descriptor(project_dir: Path) -> dict[str, Any]:
    path = project_dir / "agent_plugin.json"
    if not path.is_file():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def _descriptor_entries(descriptor: Mapping[str, Any]) -> list[str]:
    entries = [str(value) for value in descriptor.get("entries") or []]
    for item in descriptor.get("bash_tools") or []:
        if isinstance(item, dict) and item.get("file"):
            entries.append(f"bash:{item['file']}")
    return entries


def _descriptor_kinds(descriptor: Mapping[str, Any]) -> list[str]:
    explicit = sorted(set((descriptor.get("kinds") or {}).values()))
    if explicit:
        return explicit
    if descriptor.get("bash_tools"):
        return ["tools"]
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
    inferred: set[str] = set()
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


def _package_json_entries(project_dir: Path) -> tuple[list[str], list[str]]:
    package_path = project_dir / "package.json"
    if not package_path.is_file():
        return [], []
    package = json.loads(package_path.read_text(encoding="utf-8"))
    agent = package.get("agent")
    if not isinstance(agent, dict):
        return [], []
    tools = agent.get("tools")
    entries: list[str] = []
    if isinstance(tools, list):
        for item in tools:
            if isinstance(item, str):
                entries.append(item)
            elif isinstance(item, dict):
                value = item.get("entry") or item.get("path") or item.get("name")
                if value:
                    entries.append(str(value))
    elif isinstance(tools, dict):
        entries.extend(str(key) for key in tools)
    return entries, ["tools"] if entries else []


def _readme_description(project_dir: Path) -> str:
    path = project_dir / "README.md"
    if not path.is_file():
        return ""
    lines = path.read_text(encoding="utf-8").splitlines()
    paragraph: list[str] = []
    paragraph_end = -1
    in_code = False
    for index, raw in enumerate(lines):
        line = raw.strip()
        if line.startswith("```"):
            in_code = not in_code
            if paragraph:
                break
            continue
        if in_code or not line:
            if paragraph:
                paragraph_end = index
                break
            continue
        if (
            line.startswith("#")
            or line.startswith("[![")
            or line.startswith("|")
            or line.startswith("- ")
            or re.match(r"^\d+\.\s", line)
        ):
            if paragraph:
                paragraph_end = index
                break
            continue
        paragraph.append(line)
    if paragraph_end < 0:
        paragraph_end = len(lines)
    description = " ".join(paragraph)
    if description.endswith(":"):
        bullets = []
        for raw in lines[paragraph_end:]:
            line = raw.strip()
            if not line and not bullets:
                continue
            if line.startswith("- "):
                bullets.append(line[2:].strip())
                if len(bullets) >= 6:
                    break
                continue
            if bullets:
                break
            if line.startswith("#"):
                break
        if bullets:
            description += " " + "; ".join(bullets) + "."
    return description


def _project_name_from_spec(spec: Any) -> str | None:
    if not isinstance(spec, str):
        return None
    if not spec.startswith(("path:", "bash:", "node:")):
        return None
    raw = spec.split(":", 1)[1]
    path = Path(raw)
    return path.name if path.name else None


def _selected_scopes(resolved: Mapping[str, Any]) -> dict[str, list[str]]:
    scopes: dict[str, list[str]] = {}

    def add(spec: Any, scope: str) -> None:
        name = _project_name_from_spec(spec)
        if name:
            scopes.setdefault(name, []).append(scope)

    for spec in resolved.get("plugins") or []:
        add(spec, "global")
    for provider_id, provider in (resolved.get("providers") or {}).items():
        if not isinstance(provider, dict):
            continue
        for spec in provider.get("plugins") or []:
            add(spec, f"provider:{provider_id}")
    for agent_id, agent in (resolved.get("agents") or {}).items():
        if not isinstance(agent, dict):
            continue
        for spec in agent.get("plugins") or []:
            add(spec, f"agent:{agent_id}")
    return {name: sorted(set(values)) for name, values in scopes.items()}


def _feature_review_rows() -> dict[str, dict[str, str]]:
    with FEATURE_REVIEW.open(newline="", encoding="utf-8") as stream:
        return {
            row["project_name"]: row
            for row in csv.DictReader(stream)
            if row.get("project_name")
        }


def _lifecycle(
    project_name: str,
    *,
    selected_names: set[str],
    local_names: set[str],
    overrides: Mapping[str, Any],
) -> tuple[str, str]:
    override = overrides.get(project_name)
    if isinstance(override, dict) and override.get("lifecycle"):
        lifecycle = str(override["lifecycle"])
        audience = str(override.get("audience") or "advanced users")
        return lifecycle, audience
    if project_name in selected_names:
        return "default_selected", "users"
    if project_name in local_names:
        return "default_dependency", "maintainers"
    return "optional", "advanced users"


def _capability_status(lifecycle: str) -> str:
    if lifecycle == "default_selected":
        return "current"
    if lifecycle in {"optional", "distribution_specific"}:
        return "optional"
    if lifecycle == "default_dependency":
        return "internal"
    if lifecycle in {"development_fixture", "example", "template", "support_library"}:
        return "internal"
    return "unknown"


def _load_inventory_inputs() -> tuple[
    dict[str, Any],
    set[str],
    set[str],
    dict[str, list[str]],
]:
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
    fatal = [
        error
        for error in [*errors, *analysis.config_errors]
        if error.get("severity") != "warning" and error.get("type") != "env_missing"
    ]
    if fatal:
        raise RuntimeError(json.dumps(fatal, indent=2))
    scopes = _selected_scopes(resolved)
    for project_name in analysis.local_project_names - analysis.selected_plugin_names:
        scopes.setdefault(project_name, []).append("dependency")
    return (
        resolved,
        set(analysis.selected_plugin_names),
        set(analysis.local_project_names),
        {name: sorted(set(values)) for name, values in scopes.items()},
    )


def _feature_catalog(source: Mapping[str, Any]) -> dict[str, Any]:
    _resolved, selected, local, scopes = _load_inventory_inputs()
    review_rows = _feature_review_rows()
    overrides = source.get("feature_catalog_overrides") or {}
    rows: list[dict[str, Any]] = []
    for project_dir in sorted(path for path in PLUGINS.iterdir() if path.is_dir()):
        if project_dir.name == "docs":
            continue
        descriptor = _descriptor(project_dir)
        entries = _descriptor_entries(descriptor)
        kinds = _descriptor_kinds(descriptor)
        package_entries, package_kinds = _package_json_entries(project_dir)
        entries = [*entries, *package_entries]
        kinds = sorted(set([*kinds, *package_kinds]))
        dependencies = [
            str(item.get("name") or Path(str(item.get("path") or "")).name)
            for item in descriptor.get("local_workspace_dependencies") or []
            if isinstance(item, dict)
        ]
        lifecycle, audience = _lifecycle(
            project_dir.name,
            selected_names=selected,
            local_names=local,
            overrides=overrides,
        )
        review = review_rows.get(project_dir.name) or {}
        override = overrides.get(project_dir.name)
        description_override = (
            str(override.get("description") or "")
            if isinstance(override, dict)
            else ""
        )
        rows.append(
            {
                "plugin_id": project_dir.name,
                "description": description_override or _readme_description(project_dir),
                "lifecycle_status": lifecycle,
                "capability_status": (
                    review.get("capability_state") or _capability_status(lifecycle)
                ),
                "default_selected": project_dir.name in selected,
                "selected_scopes": scopes.get(project_dir.name, []),
                "plugin_kinds": kinds,
                "entries": entries,
                "local_dependencies": dependencies,
                "audience": audience,
                "source_path": str(project_dir.relative_to(ROOT)),
                "documentation_path": (
                    str((project_dir / "README.md").relative_to(ROOT))
                    if (project_dir / "README.md").is_file()
                    else ""
                ),
                "verification_state": review.get("verification_state") or "unknown",
                "review_state": str(source.get("review_state") or "needs_review"),
                "limitations": review.get("limitations") or "",
            }
        )
    return {
        "schema_version": "1.0.0",
        "status": str(source.get("review_state") or "needs_review"),
        "scope": "All plugin projects under plugins/, excluding the documentation directory.",
        "rows": rows,
    }


def _normalize_cell(raw: Any, default_status: str) -> dict[str, str]:
    if raw is None:
        return {"status": default_status, "note": ""}
    if isinstance(raw, str):
        status = raw
        note = ""
    elif isinstance(raw, dict):
        status = str(raw.get("status") or default_status)
        note = str(raw.get("note") or "")
    else:
        raise ValueError(f"Invalid matrix cell {raw!r}")
    if status not in VALID_CELL_STATUSES:
        raise ValueError(f"Unknown matrix status {status!r}")
    return {"status": status, "note": note}


def _expanded_matrix(
    raw_matrix: Mapping[str, Any],
    *,
    entity_key: str,
    entities_key: str,
    review_state: str,
) -> dict[str, Any]:
    features = list(raw_matrix.get("features") or [])
    feature_ids = [str(item["feature_id"]) for item in features]
    if len(feature_ids) != len(set(feature_ids)):
        raise ValueError(f"Duplicate feature ids in {entities_key}")
    entities = []
    for raw_entity in raw_matrix.get(entities_key) or []:
        entity = copy.deepcopy(raw_entity)
        entity_id = str(entity[entity_key])
        entity.setdefault("availability", "default_configured")
        entity["review_state"] = review_state
        default_status = str(entity.pop("default_status", "unknown"))
        if default_status not in VALID_CELL_STATUSES:
            raise ValueError(f"{entity_id}: invalid default status {default_status}")
        raw_cells = entity.pop("features", {})
        unknown = set(raw_cells) - set(feature_ids)
        if unknown:
            raise ValueError(f"{entity_id}: unknown feature ids {sorted(unknown)}")
        entity["cells"] = [
            {
                "feature_id": feature_id,
                **_normalize_cell(raw_cells.get(feature_id), default_status),
            }
            for feature_id in feature_ids
        ]
        entities.append(entity)
    return {
        "schema_version": "1.0.0",
        "status": review_state,
        "status_vocabulary": _source_payload()["status_vocabulary"],
        "features": features,
        entities_key: entities,
    }


def _csv_text(fieldnames: list[str], rows: Iterable[Mapping[str, Any]]) -> str:
    stream = io.StringIO(newline="")
    writer = csv.DictWriter(
        stream,
        fieldnames=fieldnames,
        lineterminator="\n",
    )
    writer.writeheader()
    writer.writerows(rows)
    return stream.getvalue()


def _feature_csv(payload: Mapping[str, Any]) -> str:
    fieldnames = [
        "plugin_id",
        "description",
        "lifecycle_status",
        "capability_status",
        "default_selected",
        "selected_scopes",
        "plugin_kinds",
        "entries",
        "local_dependencies",
        "audience",
        "source_path",
        "documentation_path",
        "verification_state",
        "review_state",
        "limitations",
    ]
    rows = []
    for row in payload["rows"]:
        normalized = dict(row)
        for key in (
            "selected_scopes",
            "plugin_kinds",
            "entries",
            "local_dependencies",
        ):
            normalized[key] = _join(normalized[key])
        normalized["default_selected"] = (
            "true" if normalized["default_selected"] else "false"
        )
        rows.append(normalized)
    return _csv_text(fieldnames, rows)


def _matrix_csv(
    payload: Mapping[str, Any],
    *,
    entities_key: str,
    entity_key: str,
    entity_label_key: str,
    extra_fields: list[str],
) -> str:
    labels = {
        feature["feature_id"]: feature["label"] for feature in payload["features"]
    }
    fieldnames = [
        entity_key,
        entity_label_key,
        *extra_fields,
        "feature_id",
        "feature_label",
        "status",
        "note",
    ]
    rows = []
    for entity in payload[entities_key]:
        for cell in entity["cells"]:
            row = {
                entity_key: entity[entity_key],
                entity_label_key: entity[entity_label_key],
                "feature_id": cell["feature_id"],
                "feature_label": labels[cell["feature_id"]],
                "status": cell["status"],
                "note": cell["note"],
            }
            for field in extra_fields:
                value = entity.get(field, "")
                row[field] = _join(value) if isinstance(value, list) else value
            rows.append(row)
    return _csv_text(fieldnames, rows)


def _escape_md(value: Any) -> str:
    text = str(value if value is not None else "")
    return text.replace("|", "\\|").replace("\n", " ")


def _markdown(
    feature_catalog: Mapping[str, Any],
    provider_matrix: Mapping[str, Any],
    model_matrix: Mapping[str, Any],
) -> str:
    lines = [
        "# Product Compatibility Matrices",
        "",
        "Status: " + str(feature_catalog["status"]).replace("_", " ").title(),
        "",
        "These matrices describe Crystal Lattice product behavior. Compatibility",
        "profiles are Crystal Lattice configurations, not official upstream",
        "applications, accounts, or sessions.",
        "",
        "## Status legend",
        "",
        "| Status | Meaning |",
        "|---|---|",
    ]
    for status, meaning in provider_matrix["status_vocabulary"].items():
        lines.append(f"| `{_escape_md(status)}` | {_escape_md(meaning)} |")

    lines.extend(
        [
            "",
            "## Feature catalog",
            "",
            "| Plugin | Kinds | Lifecycle | Capability | Default | Description |",
            "|---|---|---|---|---:|---|",
        ]
    )
    for row in feature_catalog["rows"]:
        lines.append(
            "| `{}` | {} | `{}` | `{}` | {} | {} |".format(
                _escape_md(row["plugin_id"]),
                _escape_md(", ".join(row["plugin_kinds"]) or "support/other"),
                _escape_md(row["lifecycle_status"]),
                _escape_md(row["capability_status"]),
                "yes" if row["default_selected"] else "no",
                _escape_md(row["description"]),
            )
        )

    provider_labels = {
        feature["feature_id"]: feature["label"]
        for feature in provider_matrix["features"]
    }
    lines.extend(["", "## Provider support", ""])
    for provider in provider_matrix["providers"]:
        lines.extend(
            [
                f"### {_escape_md(provider['label'])}",
                "",
                f"- Implementation: `{_escape_md(provider['implementation'])}`",
                f"- Availability: `{_escape_md(provider['availability'])}`",
                "",
                "| Native/provider feature | Status | Notes |",
                "|---|---|---|",
            ]
        )
        for cell in provider["cells"]:
            lines.append(
                "| {} | `{}` | {} |".format(
                    _escape_md(provider_labels[cell["feature_id"]]),
                    _escape_md(cell["status"]),
                    _escape_md(cell["note"]),
                )
            )
        lines.append("")

    model_labels = {
        feature["feature_id"]: feature["label"]
        for feature in model_matrix["features"]
    }
    lines.extend(["## Model-family-specific features", ""])
    for family in model_matrix["families"]:
        lines.extend(
            [
                f"### {_escape_md(family['label'])}",
                "",
                "- Profiles: {}".format(
                    ", ".join(f"`{_escape_md(value)}`" for value in family["profile_ids"])
                    or "distribution-specific; no default profile ID"
                ),
                "- Provider routes: {}".format(
                    ", ".join(
                        f"`{_escape_md(value)}`"
                        for value in family["provider_routes"]
                    )
                ),
                f"- Availability: `{_escape_md(family.get('availability', 'default_configured'))}`",
                "",
                "| Feature | Status | Notes |",
                "|---|---|---|",
            ]
        )
        for cell in family["cells"]:
            lines.append(
                "| {} | `{}` | {} |".format(
                    _escape_md(model_labels[cell["feature_id"]]),
                    _escape_md(cell["status"]),
                    _escape_md(cell["note"]),
                )
            )
        lines.append("")

    lines.extend(
        [
            "## Interpretation boundaries",
            "",
            "- Default selection is not the same as successful clean-runtime loading.",
            "- Conditional provider cells require the stated model, account, route,",
            "  capability discovery, or explicit setting.",
            "- Provider-native web search is separate from model-family tools backed",
            "  by Gemini, Tavily, or local URL fetching.",
            "- Profile-level compaction is separate from provider-native compaction.",
            "- Cost values may be provider-reported or locally estimated and are not",
            "  automatically billing or invoice truth.",
            "- Planned cells are not current support.",
            "",
        ]
    )
    return "\n".join(lines)


def _generated_outputs() -> dict[Path, str]:
    source = _source_payload()
    feature_catalog = _feature_catalog(source)
    provider_matrix = _expanded_matrix(
        source["provider_matrix"],
        entity_key="provider_id",
        entities_key="providers",
        review_state=str(source.get("review_state") or "needs_review"),
    )
    model_matrix = _expanded_matrix(
        source["model_family_matrix"],
        entity_key="family_id",
        entities_key="families",
        review_state=str(source.get("review_state") or "needs_review"),
    )
    return {
        FEATURE_JSON: json.dumps(feature_catalog, indent=2) + "\n",
        FEATURE_CSV: _feature_csv(feature_catalog),
        PROVIDER_JSON: json.dumps(provider_matrix, indent=2) + "\n",
        PROVIDER_CSV: _matrix_csv(
            provider_matrix,
            entities_key="providers",
            entity_key="provider_id",
            entity_label_key="label",
            extra_fields=["implementation", "availability", "review_state"],
        ),
        MODEL_JSON: json.dumps(model_matrix, indent=2) + "\n",
        MODEL_CSV: _matrix_csv(
            model_matrix,
            entities_key="families",
            entity_key="family_id",
            entity_label_key="label",
            extra_fields=[
                "availability",
                "review_state",
                "profile_ids",
                "provider_routes",
            ],
        ),
        MARKDOWN: _markdown(feature_catalog, provider_matrix, model_matrix),
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = _generated_outputs()
    if args.check:
        errors = []
        for path, expected in outputs.items():
            if not path.is_file():
                errors.append(f"{path.name}: missing")
                continue
            actual = path.read_text(encoding="utf-8")
            if actual != expected:
                errors.append(f"{path.name}: generated content differs")
            if re.search(r"\b020\b", actual, flags=re.IGNORECASE):
                errors.append(
                    f"{path.name}: numeric task identifier leaked into "
                    "product-facing matrix content"
                )
        if errors:
            print("\n".join(errors), file=sys.stderr)
            return 1
        print("compatibility matrix check passed")
        return 0
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    print(
        "wrote "
        + ", ".join(path.name for path in outputs)
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())