#!/usr/bin/env python3
"""Generate the reviewed version-two website compatibility projection."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import subprocess
from pathlib import Path
from typing import Any, Mapping


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
BASELINE = ROOT / "landing_page/research/current-product-and-compatibility-baseline"
CONFIG = HERE / "projection-config.json"
DEFAULT_CONFIG = (
    ROOT / "application/python/agent_terminal_app/default_config/config.json"
)

ACCEPTED_AGENTS = BASELINE / "configured-agent-compatibility.csv"
ACCEPTED_PROVIDER_ACCOUNTS = BASELINE / "provider-account-compatibility.csv"
ACCEPTED_AGENT_FAMILIES = BASELINE / "model-family-feature-matrix.json"
ACCEPTED_PROVIDERS = BASELINE / "provider-support-matrix.json"
ACCEPTED_PLUGINS = BASELINE / "feature-catalog.json"
ACCEPTED_WEBSITE = BASELINE / "website-compatibility-data.json"
ACCEPTED_MANIFEST = BASELINE / "input-manifest.json"

OUTPUT_JSON = HERE / "compatibility-projection-v2.json"
OUTPUT_MARKDOWN = HERE / "compatibility-projection-v2.md"
DRIFT_JSON = HERE / "drift-report.json"
DRIFT_MARKDOWN = HERE / "drift-report.md"
INPUT_MANIFEST = HERE / "input-manifest.json"

MONITORED_PATHS = (
    "application/python/agent_terminal_app/default_config/config.json",
    "plugins",
)

PROVIDER_STATUS_MAP = {
    "supported": "available",
    "conditional": "conditional",
    "planned": "planned",
    "unsupported": "unsupported",
    "not_applicable": "not_applicable",
    "unknown": "not_verified",
}

PROVIDER_ACCOUNT_ROWS = {
    "openai-api": "openai",
    "openai-chatgpt": "openai",
    "openrouter-chat": "openrouter",
    "openrouter-responses": None,
    "anthropic": "anthropic",
    "ollama": "ollama",
    "fireworks": "fireworks",
    "zai": "zai",
    "custom-openai-compatible": None,
    "openrouter-image": "openrouter_image_generation",
}

AGENT_PROVIDER_REFS = {
    "anthropic": ["anthropic"],
    "fireworks": ["fireworks"],
    "ollama": ["ollama"],
    "openrouter": ["openrouter-chat"],
    "openrouter_image_generation": ["openrouter-image"],
    "zai": ["zai"],
}

REFRESHED_PLUGIN_IDS = {
    "anthropic-compatible",
    "claude-tools",
    "codex-tools",
    "embedded-workspace-settings",
    "interleaved-thinking",
    "shell-tool-settings",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _csv_rows(path: Path, key: str) -> dict[str, dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as stream:
        return {str(row[key]): row for row in csv.DictReader(stream)}


def _split(value: str | None) -> list[str]:
    return [part for part in str(value or "").split("|") if part]


def _public_text(value: Any) -> str:
    text = str(value if value is not None else "")
    replacements = (
        ("AI Agent Platform", "Crystal Lattice"),
        ("source/profile", "source/configuration"),
        ("profile-local", "configured-agent-specific"),
        ("profiles", "configurations"),
        ("profile", "configuration"),
    )
    for source, replacement in replacements:
        text = text.replace(source, replacement)
    return text


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _git(*args: str) -> str:
    completed = subprocess.run(
        ["git", *args],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    return completed.stdout.strip()


def _current_product_revision() -> tuple[str, str]:
    revision = _git("log", "-1", "--format=%H", "--", *MONITORED_PATHS)
    observed = _git("show", "-s", "--format=%cI", revision)
    return revision, observed


def _descriptor_entries(plugin_id: str) -> list[str]:
    descriptor = ROOT / "plugins" / plugin_id / "agent_plugin.json"
    if not descriptor.is_file():
        return []
    return [str(value) for value in _load_json(descriptor).get("entries") or []]


def _source_plugin_ids() -> list[str]:
    return sorted(
        entry.name
        for entry in (ROOT / "plugins").iterdir()
        if entry.is_dir() and entry.name != "docs"
    )


def _provider_refs(agent_row: Mapping[str, str]) -> list[str]:
    route = str(agent_row["provider_route"])
    if route == "openai":
        if agent_row.get("auth_mode") == "api":
            return ["openai-api"]
        return ["openai-chatgpt", "openai-api"]
    return list(AGENT_PROVIDER_REFS.get(route) or [])


def _agent_core_drift(
    current_agent: Mapping[str, Any],
    accepted: Mapping[str, str],
) -> list[str]:
    differences: list[str] = []
    comparisons = {
        "provider": (
            str(current_agent.get("provider") or ""),
            str(accepted.get("provider_route") or ""),
        ),
        "model": (
            str(current_agent.get("model") or ""),
            str(accepted.get("model") or ""),
        ),
        "plugins": (
            list(current_agent.get("plugins") or []),
            _split(accepted.get("agent_plugin_specs")),
        ),
        "disabled_plugins": (
            list(current_agent.get("disabled_plugins") or []),
            _split(accepted.get("disabled_plugins")),
        ),
        "enabled_plugins": (
            list(current_agent.get("enabled_plugins") or []),
            _split(accepted.get("enabled_plugins")),
        ),
        "shell_tool_mode": (
            str(current_agent.get("shell_tool_mode") or ""),
            str(accepted.get("shell_tool_mode") or ""),
        ),
    }
    for field, (current, prior) in comparisons.items():
        if field == "model" and not current:
            continue
        if current != prior:
            differences.append(field)
    return differences


def _agent_projection(
    config: Mapping[str, Any],
    *,
    accepted_rows: Mapping[str, Mapping[str, str]],
    family_matrix: Mapping[str, Any],
    current_config: Mapping[str, Any],
    accepted_revision: str,
    current_revision: str,
) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    accepted_families = {
        str(family["family_id"]): family for family in family_matrix["families"]
    }
    profile_to_harness: dict[str, str] = {}
    group_profiles: dict[str, list[str]] = {}
    for group in config["harness_groups"]:
        profiles: list[str] = []
        for family_id in group["agent_family_ids"]:
            family = accepted_families.get(str(family_id))
            if family is None:
                raise ValueError(f"unknown accepted agent family {family_id}")
            profiles.extend(str(value) for value in family.get("profile_ids") or [])
        group_profiles[str(group["harness_id"])] = profiles
        for profile_id in profiles:
            if profile_id in profile_to_harness:
                raise ValueError(f"agent {profile_id} appears in two harness groups")
            profile_to_harness[profile_id] = str(group["harness_id"])

    accepted_agent_ids = set(accepted_rows)
    if set(profile_to_harness) != accepted_agent_ids:
        raise ValueError(
            "configured-agent harness grouping mismatch: "
            f"missing={sorted(accepted_agent_ids - set(profile_to_harness))}, "
            f"extra={sorted(set(profile_to_harness) - accepted_agent_ids)}"
        )

    current_agents = current_config.get("agents") or {}
    if set(current_agents) != accepted_agent_ids:
        raise ValueError(
            "current configured-agent IDs changed: "
            f"missing={sorted(accepted_agent_ids - set(current_agents))}, "
            f"extra={sorted(set(current_agents) - accepted_agent_ids)}"
        )

    agent_drift: list[dict[str, Any]] = []
    projected: dict[str, list[dict[str, Any]]] = {
        str(group["harness_id"]): [] for group in config["harness_groups"]
    }
    for agent_id, accepted in accepted_rows.items():
        current = current_agents[agent_id]
        changed_fields = _agent_core_drift(current, accepted)
        if changed_fields:
            agent_drift.append(
                {
                    "agent_id": agent_id,
                    "changed_fields": changed_fields,
                }
            )
        display = current.get("display") or {}
        harness_id = profile_to_harness[agent_id]
        tool_surface = _public_text(accepted.get("tool_surface") or "")
        if harness_id == "codex-oriented":
            disabled = set(current.get("disabled_plugins") or [])
            details = [
                "codex-tools",
                "exec_command",
                "write_stdin",
                (
                    "apply_patch plugin disabled"
                    if "apply_patch" in disabled
                    else "apply_patch"
                ),
                "image",
                "skills",
                "MCP default-off",
            ]
            tool_surface = "; ".join(details)
        limitations = _public_text(accepted.get("limitations") or "")
        if agent_id == "claude-anthropic":
            limitations = (
                "Independent Crystal Lattice implementation, not official "
                "Claude Code. Native compaction and context editing are "
                "capability-gated; image/file input and hosted-provider "
                "verification remain unavailable."
            )
        projected[profile_to_harness[agent_id]].append(
            {
                "agent_id": agent_id,
                "title": _public_text(display.get("title") or agent_id),
                "description": _public_text(display.get("description") or ""),
                "order": display.get("order"),
                "compatibility_family": _public_text(
                    accepted.get("compatibility_family") or ""
                ),
                "harness_id": profile_to_harness[agent_id],
                "provider_route": accepted.get("provider_route") or "",
                "provider_refs": _provider_refs(accepted),
                "tool_surface": tool_surface,
                "availability": "included",
                "capability_status": accepted.get("capability_state") or "unknown",
                "runtime_prerequisites": _public_text(
                    accepted.get("runtime_prerequisites") or ""
                ),
                "verification_state": accepted.get("verification_state") or "unknown",
                "real_provider_verification": (
                    accepted.get("real_provider_verification") or "unknown"
                ),
                "limitations": limitations,
                "technical_details": {
                    "default_model": accepted.get("model") or "",
                    "plugin_packages": [
                        value.removeprefix("path:${env:BUILTIN_PLUGINS}/")
                        for value in _split(accepted.get("agent_plugin_specs"))
                    ],
                    "evidence_ids": _split(accepted.get("evidence_ids")),
                },
                "accepted_source_revision": accepted_revision,
                "display_metadata_source_revision": current_revision,
                "source_state": (
                    "accepted_with_current_display_metadata"
                    if not changed_fields
                    else "current_source_drift_requires_review"
                ),
            }
        )

    groups = []
    for group in config["harness_groups"]:
        harness_id = str(group["harness_id"])
        agents = sorted(
            projected[harness_id],
            key=lambda row: (
                row["order"] is None,
                row["order"] if row["order"] is not None else 0,
                row["agent_id"],
            ),
        )
        groups.append(
            {
                "harness_id": harness_id,
                "label": group["label"],
                "description": group["description"],
                "agents": agents,
            }
        )
    return (
        {
            "title": "Included configured agents",
            "description": (
                "Named Crystal Lattice configurations grouped by their "
                "material harness behavior and mapped to provider routes."
            ),
            "groups": groups,
        },
        agent_drift,
    )


def _harness_projection(
    config: Mapping[str, Any],
    *,
    accepted_website: Mapping[str, Any],
    current_revision: str,
) -> dict[str, Any]:
    source_families = {
        str(family["family_id"]): family
        for family in accepted_website["model_family_tools"]["families"]
    }
    families = []
    for group in config["harness_groups"]:
        tool_family_id = group.get("tool_family_id")
        if not tool_family_id:
            continue
        source = source_families[str(tool_family_id)]
        capabilities = []
        for source_tool in source["tools"]:
            tool = dict(source_tool)
            tool["source_state"] = "accepted"
            if tool["status"] == "optional":
                tool["status"] = "available"
                tool["availability"] = "optional"
            elif tool["status"] == "planned":
                tool["availability"] = "planned"
            if tool_family_id == "codex" and tool["tool_id"] == "shell":
                tool.update(
                    {
                        "name": "Legacy shell modes",
                        "status": "available",
                        "availability": "optional",
                        "description": (
                            "Select the retained array or string-command shell "
                            "surface explicitly; unified exec is the default."
                        ),
                        "source_state": "refreshed",
                    }
                )
            elif tool_family_id == "codex" and tool["tool_id"] in {
                "exec_command",
                "write_stdin",
            }:
                tool.update(
                    {
                        "status": "available",
                        "availability": "included",
                        "source_state": "refreshed",
                        "plugin_names": [tool["tool_id"]],
                        "plugin_entries": [
                            (
                                "codex_tools.unified_exec_tool.ExecCommandTool"
                                if tool["tool_id"] == "exec_command"
                                else "codex_tools.unified_exec_tool.WriteStdinTool"
                            )
                        ],
                    }
                )
            elif tool_family_id == "claude" and tool["tool_id"] == "compaction":
                tool.update(
                    {
                        "description": (
                            "Run manual or background Claude-compatible "
                            "compaction for full history, a prefix, or a selected "
                            "range with snapshots, notifications, cancellation, "
                            "and retry support."
                        ),
                        "source_state": "refreshed",
                        "plugin_names": [
                            "claude_compaction",
                            "claude_compaction_app",
                        ],
                        "plugin_entries": [
                            "claude_tools.claude_compaction_feature.ClaudeCompactionFeature",
                            "claude_tools.claude_compaction_app.ClaudeCompactionAppPlugin",
                        ],
                    }
                )
            tool.setdefault(
                "availability",
                "included",
            )
            if tool["source_state"] == "refreshed":
                tool["source_revision"] = current_revision
            capabilities.append(tool)
        families.append(
            {
                "harness_id": group["harness_id"],
                "label": group["label"],
                "description": group["description"],
                "plugin_bundle": source["plugin_bundle"],
                "plugin_bundle_path": source["plugin_bundle_path"],
                "capabilities": capabilities,
            }
        )
    return {
        "title": "Harness capabilities",
        "description": (
            "Material tool, context, and extension behavior supplied by "
            "Crystal Lattice harness packages."
        ),
        "families": families,
    }


def _provider_projection(
    config: Mapping[str, Any],
    *,
    accepted_matrix: Mapping[str, Any],
    accepted_website: Mapping[str, Any],
    accepted_accounts: Mapping[str, Mapping[str, str]],
    current_revision: str,
) -> dict[str, Any]:
    feature_defs = {
        str(feature["feature_id"]): str(feature["label"])
        for feature in accepted_matrix["features"]
    }
    rich_providers = {
        str(provider["provider_id"]): provider
        for provider in accepted_website["providers"]["providers"]
    }
    rich_features = {
        (provider_id, str(feature["feature_id"])): feature
        for provider_id, provider in rich_providers.items()
        for feature in provider["features"]
    }
    providers = []
    for provider in accepted_matrix["providers"]:
        provider_id = str(provider["provider_id"])
        account_row_id = PROVIDER_ACCOUNT_ROWS[provider_id]
        account = accepted_accounts.get(account_row_id or "", {})
        features = []
        for cell in provider["cells"]:
            feature_id = str(cell["feature_id"])
            source_status = str(cell["status"])
            rich = rich_features.get((provider_id, feature_id), {})
            row = {
                "feature_id": feature_id,
                "feature": feature_defs[feature_id],
                "status": PROVIDER_STATUS_MAP[source_status],
                "source_status": source_status,
                "note": str(cell.get("note") or ""),
                "description": str(
                    rich.get("description")
                    or cell.get("note")
                    or feature_defs[feature_id]
                ),
                "plugin_bundle": rich.get("plugin_bundle"),
                "plugin_bundle_path": rich.get("plugin_bundle_path"),
                "plugin_names": list(rich.get("plugin_names") or []),
                "plugin_entries": list(rich.get("plugin_entries") or []),
                "source_state": "accepted",
            }
            if provider_id == "anthropic" and feature_id == "native_compaction":
                row.update(
                    {
                        "status": "conditional",
                        "source_status": "conditional",
                        "note": (
                            "Implemented for models/endpoints that advertise "
                            "Anthropic compact_20260112 support."
                        ),
                        "description": (
                            "Uses Anthropic automatic request-time compaction "
                            "and preserves complete provider-native continuation "
                            "blocks for later requests."
                        ),
                        "plugin_bundle": "anthropic-compatible",
                        "plugin_bundle_path": "plugins/anthropic-compatible",
                        "plugin_names": ["anthropic_compaction"],
                        "plugin_entries": [
                            "anthropic_plugins.compaction_extension.AnthropicCompactionExtension"
                        ],
                        "source_state": "refreshed",
                        "source_revision": current_revision,
                    }
                )
            features.append(row)
        if provider_id == "anthropic":
            features.append(
                {
                    "feature_id": "native_context_editing",
                    "feature": "Native context editing",
                    "status": "conditional",
                    "source_status": "conditional",
                    "note": (
                        "Capability-gated thinking retention and tool-use "
                        "clearing; the direct Anthropic configuration enables "
                        "supported behavior."
                    ),
                    "description": (
                        "Applies Anthropic-native thinking-retention and old "
                        "tool-use clearing policies without deleting the local "
                        "visible transcript."
                    ),
                    "plugin_bundle": "anthropic-compatible",
                    "plugin_bundle_path": "plugins/anthropic-compatible",
                    "plugin_names": ["anthropic_context_editing"],
                    "plugin_entries": [
                        "anthropic_plugins.context_editing_extension.AnthropicContextEditingExtension"
                    ],
                    "source_state": "refreshed",
                    "source_revision": current_revision,
                }
            )
        providers.append(
            {
                "provider_id": provider_id,
                "label": provider["label"],
                "implementation": provider["implementation"],
                "availability": provider["availability"],
                "access": config["provider_access"][provider_id],
                "limitations": (
                    "No hosted auth, model, compaction, or context-editing "
                    "request was run for this refresh. Image/file input, "
                    "subscription-account authentication, and cost estimation "
                    "remain unavailable or separately planned."
                    if provider_id == "anthropic"
                    else _public_text(account.get("limitations") or "")
                ),
                "verification_state": account.get("verification_state") or "unknown",
                "real_provider_verification": (
                    account.get("real_provider_verification") or "unknown"
                ),
                "features": features,
                "source_state": (
                    "refreshed" if provider_id == "anthropic" else "accepted"
                ),
            }
        )
    return {
        "title": "Provider support",
        "description": (
            "Provider and account routes with native capability status, "
            "prerequisites, limitations, and verification boundaries."
        ),
        "providers": providers,
    }


def _plugin_status(row: Mapping[str, Any]) -> str:
    lifecycle = str(row["lifecycle_status"])
    capability = str(row["capability_status"])
    if lifecycle in {
        "development_fixture",
        "example",
        "support_library",
        "template",
    }:
        return "internal"
    if lifecycle == "distribution_specific":
        return "conditional"
    if lifecycle == "optional":
        return "available"
    if capability == "current":
        return "included"
    if capability in {"partial", "optional"}:
        return "conditional"
    if capability == "experimental":
        return "experimental"
    if capability == "planned":
        return "planned"
    return "not_verified"


def _plugin_group(row: Mapping[str, Any]) -> str:
    lifecycle = str(row["lifecycle_status"])
    if lifecycle == "default_selected":
        return "included"
    if lifecycle == "optional":
        return "optional"
    if lifecycle == "distribution_specific":
        return "distribution_specific"
    return "developer_internal"


def _plugin_projection(
    config: Mapping[str, Any],
    *,
    accepted_catalog: Mapping[str, Any],
    current_revision: str,
) -> tuple[dict[str, Any], list[str], list[str]]:
    rows = [dict(row) for row in accepted_catalog["rows"]]
    accepted_ids = {str(row["plugin_id"]) for row in rows}
    supplements = [dict(row) for row in config["plugin_supplements"]]
    supplement_ids = {str(row["plugin_id"]) for row in supplements}
    if accepted_ids & supplement_ids:
        raise ValueError("plugin supplement duplicates an accepted plugin")
    rows.extend(supplements)

    current_ids = set(_source_plugin_ids())
    new_ids = sorted(current_ids - accepted_ids)
    removed_ids = sorted(accepted_ids - current_ids)
    if new_ids != sorted(supplement_ids):
        raise ValueError(
            "plugin supplements do not match current source additions: "
            f"expected={new_ids}, configured={sorted(supplement_ids)}"
        )
    if removed_ids:
        raise ValueError(f"accepted plugin projects removed: {removed_ids}")

    groups = {
        "included": [],
        "optional": [],
        "distribution_specific": [],
        "developer_internal": [],
    }
    for row in sorted(rows, key=lambda item: str(item["plugin_id"])):
        plugin_id = str(row["plugin_id"])
        projected = {
            "plugin_id": plugin_id,
            "description": row["description"],
            "status": _plugin_status(row),
            "availability": _plugin_group(row),
            "lifecycle_status": row["lifecycle_status"],
            "capability_status": row["capability_status"],
            "default_selected": bool(row["default_selected"]),
            "plugin_kinds": list(row.get("plugin_kinds") or []),
            "audience": row.get("audience") or "",
            "source_path": row["source_path"],
            "documentation_path": row.get("documentation_path") or "",
            "verification_state": row.get("verification_state") or "unknown",
            "limitations": _public_text(row.get("limitations") or ""),
            "source_state": (
                "refreshed"
                if plugin_id in REFRESHED_PLUGIN_IDS
                else "accepted"
            ),
        }
        if projected["source_state"] == "refreshed":
            projected["source_revision"] = current_revision
        projected["description"] = _public_text(projected["description"])
        if plugin_id == "anthropic-compatible":
            projected["description"] = (
                "Direct Anthropic Messages provider and extensions for tools, "
                "reasoning, prompt caching, usage, native compaction, and "
                "native context editing."
            )
            projected["limitations"] = (
                "No hosted result was run for this refresh; image/file input, "
                "subscription-account authentication, and cost estimation "
                "remain unavailable or separately planned."
            )
        elif plugin_id == "claude-tools":
            projected["description"] = (
                "Claude-compatible file, search, shell, web, MCP, background "
                "task, and manual/background compaction bundle."
            )
        elif plugin_id == "codex-tools":
            projected["description"] = (
                "Codex-oriented unified exec, patch, image, MCP, skills, and "
                "legacy shell-mode bundle."
            )
        groups[_plugin_group(row)].append(projected)

    return (
        {
            "title": "Plugins and application features",
            "description": (
                "User-facing, optional, distribution-specific, and "
                "developer/internal plugin projects kept as explicit lifecycle "
                "groups."
            ),
            "groups": [
                {
                    "group_id": "included",
                    "label": "Included by default",
                    "rows": groups["included"],
                },
                {
                    "group_id": "optional",
                    "label": "Available optional plugins",
                    "rows": groups["optional"],
                },
                {
                    "group_id": "distribution-specific",
                    "label": "Distribution-specific plugins",
                    "rows": groups["distribution_specific"],
                },
                {
                    "group_id": "developer-internal",
                    "label": "Developer examples, templates, support, and fixtures",
                    "rows": groups["developer_internal"],
                },
            ],
        },
        new_ids,
        removed_ids,
    )


def _descriptor_drift(accepted_catalog: Mapping[str, Any]) -> list[dict[str, Any]]:
    changes = []
    for row in accepted_catalog["rows"]:
        plugin_id = str(row["plugin_id"])
        accepted_entries = [str(value) for value in row.get("entries") or []]
        if any(value.startswith(("bash:", "node:")) for value in accepted_entries):
            continue
        current_entries = _descriptor_entries(plugin_id)
        if not current_entries:
            continue
        if current_entries != accepted_entries:
            changes.append(
                {
                    "plugin_id": plugin_id,
                    "accepted_entries": accepted_entries,
                    "current_entries": current_entries,
                    "added_entries": [
                        value for value in current_entries if value not in accepted_entries
                    ],
                    "removed_entries": [
                        value for value in accepted_entries if value not in current_entries
                    ],
                }
            )
    return changes


def _projection_and_drift() -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    config = _load_json(CONFIG)
    accepted_manifest = _load_json(ACCEPTED_MANIFEST)
    accepted_revision = str(accepted_manifest["source_commit"])
    current_revision, current_revision_date = _current_product_revision()

    accepted_agents = _csv_rows(ACCEPTED_AGENTS, "agent_id")
    accepted_accounts = _csv_rows(ACCEPTED_PROVIDER_ACCOUNTS, "provider_id")
    agent_families = _load_json(ACCEPTED_AGENT_FAMILIES)
    provider_matrix = _load_json(ACCEPTED_PROVIDERS)
    plugin_catalog = _load_json(ACCEPTED_PLUGINS)
    accepted_website = _load_json(ACCEPTED_WEBSITE)
    current_config = _load_json(DEFAULT_CONFIG)

    agents, agent_drift = _agent_projection(
        config,
        accepted_rows=accepted_agents,
        family_matrix=agent_families,
        current_config=current_config,
        accepted_revision=accepted_revision,
        current_revision=current_revision,
    )
    harnesses = _harness_projection(
        config,
        accepted_website=accepted_website,
        current_revision=current_revision,
    )
    providers = _provider_projection(
        config,
        accepted_matrix=provider_matrix,
        accepted_website=accepted_website,
        accepted_accounts=accepted_accounts,
        current_revision=current_revision,
    )
    plugins, new_plugins, removed_plugins = _plugin_projection(
        config,
        accepted_catalog=plugin_catalog,
        current_revision=current_revision,
    )
    descriptor_changes = _descriptor_drift(plugin_catalog)

    projection = {
        "schema_version": config["schema_version"],
        "review_state": config["review_state"],
        "maturity": config["maturity"],
        "observation_date": config["observation_date"],
        "accepted_source_revision": accepted_revision,
        "current_product_revision": current_revision,
        "identity_note": config["identity_note"],
        "revision_policy": config["revision_policy"],
        "status_labels": config["status_labels"],
        "configured_agents": agents,
        "harnesses": harnesses,
        "providers": providers,
        "plugins": plugins,
    }

    drift = {
        "schema_version": "1.0.0",
        "observation_date": config["observation_date"],
        "accepted_source_revision": accepted_revision,
        "current_product_revision": current_revision,
        "current_product_revision_date": current_revision_date,
        "status": "focused_refresh_required_and_applied_to_projection",
        "configured_agent_core_drift": agent_drift,
        "configured_agent_display_metadata": {
            "status": "added_after_accepted_baseline",
            "agent_count": len(accepted_agents),
            "projection_use": "current titles, descriptions, and order",
        },
        "new_plugin_projects": new_plugins,
        "removed_plugin_projects": removed_plugins,
        "descriptor_changes": descriptor_changes,
        "public_claim_refreshes": [
            {
                "area": "Anthropic provider",
                "change": (
                    "Native automatic compaction moved from planned to "
                    "conditional current support; native context editing was "
                    "added as a conditional capability."
                ),
                "projection_state": "refreshed",
            },
            {
                "area": "Codex-oriented harness",
                "change": (
                    "exec_command and write_stdin moved from planned to "
                    "included current tools; legacy shell modes remain optional."
                ),
                "projection_state": "refreshed",
            },
            {
                "area": "Claude-compatible harness",
                "change": (
                    "The existing compaction capability now includes a "
                    "background application plugin with notifications, "
                    "cancellation, retry, and pre-commit snapshots."
                ),
                "projection_state": "refreshed",
            },
            {
                "area": "Plugin catalogue",
                "change": (
                    "Added embedded-workspace-settings, interleaved-thinking, "
                    "and shell-tool-settings with distribution/optional "
                    "lifecycle boundaries."
                ),
                "projection_state": "refreshed",
            },
        ],
        "focused_verification": config["focused_verification"],
        "remaining_limits": [
            "No hosted provider request was run for this focused refresh.",
            "Anthropic compaction and context editing remain capability-gated.",
            "The accepted catalogue was not broadly regenerated or re-audited.",
            "Unchanged accepted rows retain their original verification state and limitations.",
            "The complete compatibility route and responsive presentation are not implemented.",
        ],
    }

    manifest_inputs = [
        Path(__file__).resolve(),
        CONFIG,
        DEFAULT_CONFIG,
        ACCEPTED_AGENTS,
        ACCEPTED_PROVIDER_ACCOUNTS,
        ACCEPTED_AGENT_FAMILIES,
        ACCEPTED_PROVIDERS,
        ACCEPTED_PLUGINS,
        ACCEPTED_WEBSITE,
        ACCEPTED_MANIFEST,
    ]
    manifest = {
        "schema_version": "1.0.0",
        "projection_schema_version": config["schema_version"],
        "observation_date": config["observation_date"],
        "accepted_source_revision": accepted_revision,
        "current_product_revision": current_revision,
        "generator": "generate_compatibility_projection.py",
        "inputs": [
            {
                "path": str(path.relative_to(ROOT)),
                "sha256": _sha256(path),
            }
            for path in manifest_inputs
        ],
        "outputs": [
            OUTPUT_JSON.name,
            OUTPUT_MARKDOWN.name,
            DRIFT_JSON.name,
            DRIFT_MARKDOWN.name,
        ],
        "status": "awaiting_canonical_public_selection",
    }
    return projection, drift, manifest


def _escape(value: Any) -> str:
    return str(value if value is not None else "").replace("|", "\\|").replace(
        "\n", " "
    )


def _status_label(projection: Mapping[str, Any], status: str) -> str:
    return str(projection["status_labels"].get(status, status))


def _projection_markdown(projection: Mapping[str, Any]) -> str:
    agent_count = sum(
        len(group["agents"]) for group in projection["configured_agents"]["groups"]
    )
    harness_count = len(projection["harnesses"]["families"])
    provider_count = len(projection["providers"]["providers"])
    plugin_count = sum(
        len(group["rows"]) for group in projection["plugins"]["groups"]
    )
    lines = [
        "# Compatibility Projection V2",
        "",
        f"Review state: `{projection['review_state']}`",
        f"Maturity: `{projection['maturity']}`",
        f"Observed: `{projection['observation_date']}`",
        "",
        projection["identity_note"],
        "",
        projection["revision_policy"],
        "",
        "## Projection summary",
        "",
        f"- Configured agents: {agent_count}",
        f"- Harness families with capability detail: {harness_count}",
        f"- Provider/account routes: {provider_count}",
        f"- Plugin projects: {plugin_count}",
        "",
        "## Included configured agents",
        "",
    ]
    for group in projection["configured_agents"]["groups"]:
        lines.extend(
            [
                f"### {_escape(group['label'])}",
                "",
                _escape(group["description"]),
                "",
                "| Agent | Provider route | Tool/harness summary | Status | Limitations |",
                "|---|---|---|---|---|",
            ]
        )
        for agent in group["agents"]:
            providers = ", ".join(agent["provider_refs"]) or agent["provider_route"]
            lines.append(
                "| {}<br><code>{}</code> | {} | {} | {} | {} |".format(
                    _escape(agent["title"]),
                    _escape(agent["agent_id"]),
                    _escape(providers),
                    _escape(agent["tool_surface"]),
                    _escape(_status_label(projection, agent["availability"])),
                    _escape(agent["limitations"]),
                )
            )
        lines.extend(
            [
                "",
                "<details>",
                "<summary>Technical configured-agent defaults</summary>",
                "",
            ]
        )
        for agent in group["agents"]:
            technical = agent["technical_details"]
            packages = ", ".join(technical["plugin_packages"]) or "none"
            lines.append(
                "- `{}` — model `{}`; agent plugin packages: {}".format(
                    _escape(agent["agent_id"]),
                    _escape(technical["default_model"]),
                    _escape(packages),
                )
            )
        lines.extend(["", "</details>", ""])

    lines.extend(["## Harness capabilities", ""])
    for family in projection["harnesses"]["families"]:
        lines.extend(
            [
                f"### {_escape(family['label'])}",
                "",
                _escape(family["description"]),
                "",
                "| Capability | Status | Availability | Description | Source state |",
                "|---|---|---|---|---|",
            ]
        )
        for capability in family["capabilities"]:
            lines.append(
                "| {} | {} | {} | {} | {} |".format(
                    _escape(capability["name"]),
                    _escape(_status_label(projection, capability["status"])),
                    _escape(capability.get("availability") or ""),
                    _escape(capability["description"]),
                    _escape(capability["source_state"]),
                )
            )
        lines.append("")

    lines.extend(["## Provider support", ""])
    for provider in projection["providers"]["providers"]:
        lines.extend(
            [
                f"### {_escape(provider['label'])}",
                "",
                f"Access: {_escape(provider['access'])}",
                "",
                "| Capability | Status | Description / condition | Source state |",
                "|---|---|---|---|",
            ]
        )
        for feature in provider["features"]:
            lines.append(
                "| {} | {} | {} | {} |".format(
                    _escape(feature["feature"]),
                    _escape(_status_label(projection, feature["status"])),
                    _escape(feature["description"]),
                    _escape(feature["source_state"]),
                )
            )
        if provider["limitations"]:
            lines.extend(["", f"Limitations: {_escape(provider['limitations'])}"])
        lines.append("")

    lines.extend(["## Plugins and application features", ""])
    for group in projection["plugins"]["groups"]:
        lines.extend(
            [
                f"### {_escape(group['label'])}",
                "",
                "| Plugin | Status | Lifecycle | Kinds | Description | Verification | Limitations |",
                "|---|---|---|---|---|---|---|",
            ]
        )
        for plugin in group["rows"]:
            lines.append(
                "| `{}` | {} | `{}` | {} | {} | `{}` | {} |".format(
                    _escape(plugin["plugin_id"]),
                    _escape(_status_label(projection, plugin["status"])),
                    _escape(plugin["lifecycle_status"]),
                    _escape(", ".join(plugin["plugin_kinds"])),
                    _escape(plugin["description"]),
                    _escape(plugin["verification_state"]),
                    _escape(plugin["limitations"]),
                )
            )
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def _drift_markdown(drift: Mapping[str, Any]) -> str:
    lines = [
        "# Compatibility Source Drift",
        "",
        f"Observed: `{drift['observation_date']}`",
        f"Accepted source: `{drift['accepted_source_revision']}`",
        f"Current product source: `{drift['current_product_revision']}`",
        "",
        "## Outcome",
        "",
        "Focused source drift exists and is represented in the version-two projection.",
        "",
        "## Refreshed public claims",
        "",
    ]
    for item in drift["public_claim_refreshes"]:
        lines.append(f"- **{item['area']}:** {item['change']}")
    lines.extend(
        [
            "",
            "## Configured agents",
            "",
            (
                f"- Current display metadata is available for "
                f"{drift['configured_agent_display_metadata']['agent_count']} agents."
            ),
        ]
    )
    if drift["configured_agent_core_drift"]:
        for item in drift["configured_agent_core_drift"]:
            lines.append(
                f"- `{item['agent_id']}` changed: "
                + ", ".join(item["changed_fields"])
            )
    else:
        lines.append(
            "- No provider/model/plugin/shell-mode drift was detected in the "
            "accepted configured-agent rows."
        )
    lines.extend(["", "## Plugin project drift", ""])
    lines.append(
        "- Added: "
        + (
            ", ".join(f"`{value}`" for value in drift["new_plugin_projects"])
            or "none"
        )
    )
    lines.append(
        "- Removed: "
        + (
            ", ".join(f"`{value}`" for value in drift["removed_plugin_projects"])
            or "none"
        )
    )
    lines.extend(["", "### Descriptor changes", ""])
    for item in drift["descriptor_changes"]:
        lines.append(
            f"- `{item['plugin_id']}` added "
            + (
                ", ".join(f"`{value}`" for value in item["added_entries"])
                or "no entries"
            )
            + (
                "; removed "
                + ", ".join(f"`{value}`" for value in item["removed_entries"])
                if item["removed_entries"]
                else ""
            )
            + "."
        )
    lines.extend(["", "## Focused verification", ""])
    for item in drift["focused_verification"]:
        lines.extend(
            [
                f"- **{item['area']}:** `{item['result']}`",
                f"  - `{item['command']}`",
            ]
        )
    lines.extend(["", "## Remaining limits", ""])
    for item in drift["remaining_limits"]:
        lines.append(f"- {item}")
    return "\n".join(lines).rstrip() + "\n"


def _validate_projection(projection: Mapping[str, Any]) -> None:
    labels = set(projection["status_labels"])
    agent_rows = [
        row
        for group in projection["configured_agents"]["groups"]
        for row in group["agents"]
    ]
    harness_rows = [
        row
        for family in projection["harnesses"]["families"]
        for row in family["capabilities"]
    ]
    provider_rows = [
        row
        for provider in projection["providers"]["providers"]
        for row in provider["features"]
    ]
    plugin_rows = [
        row for group in projection["plugins"]["groups"] for row in group["rows"]
    ]
    if len(agent_rows) != 20:
        raise ValueError(f"expected 20 configured agents, got {len(agent_rows)}")
    if len(projection["harnesses"]["families"]) != 6:
        raise ValueError("expected six public harness capability families")
    if len(projection["providers"]["providers"]) != 10:
        raise ValueError("expected ten provider/account routes")
    if len(plugin_rows) != len(_source_plugin_ids()):
        raise ValueError("plugin projection does not cover every current plugin project")
    for row in agent_rows:
        if "model" in row:
            raise ValueError("default model must remain in progressive technical detail")
        if not row.get("technical_details", {}).get("default_model"):
            raise ValueError(f"agent {row['agent_id']}: missing default model detail")
    for row in [*harness_rows, *provider_rows, *plugin_rows]:
        if row["status"] not in labels:
            raise ValueError(f"unknown public status {row['status']!r}")
    for row in harness_rows:
        if row["status"] == "planned" and row.get("availability") != "planned":
            raise ValueError(
                f"harness capability {row['tool_id']}: planned availability drift"
            )
    anthropic = next(
        provider
        for provider in projection["providers"]["providers"]
        if provider["provider_id"] == "anthropic"
    )
    refreshed = {
        row["feature_id"]: row
        for row in anthropic["features"]
        if row["source_state"] == "refreshed"
    }
    if set(refreshed) != {"native_compaction", "native_context_editing"}:
        raise ValueError("Anthropic focused refresh is incomplete")


def _outputs() -> dict[Path, str]:
    projection, drift, manifest = _projection_and_drift()
    _validate_projection(projection)
    outputs = {
        OUTPUT_JSON: json.dumps(projection, indent=2) + "\n",
        OUTPUT_MARKDOWN: _projection_markdown(projection),
        DRIFT_JSON: json.dumps(drift, indent=2) + "\n",
        DRIFT_MARKDOWN: _drift_markdown(drift),
        INPUT_MANIFEST: json.dumps(manifest, indent=2) + "\n",
    }
    public_outputs = outputs[OUTPUT_JSON] + outputs[OUTPUT_MARKDOWN]
    if "tasks/" in public_outputs:
        raise ValueError("internal task path leaked into the public projection")
    if re.search(r"\bWEB-[A-Z]+-\d+\b", public_outputs):
        raise ValueError("internal requirement identifier leaked into projection")
    if "AI Agent Platform" in public_outputs:
        raise ValueError("obsolete product category leaked into projection")
    if re.search(r"\bprofiles?\b", public_outputs, flags=re.IGNORECASE):
        raise ValueError("obsolete public profile terminology leaked into projection")
    return outputs


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    outputs = _outputs()
    if args.check:
        errors = []
        for path, expected in outputs.items():
            if not path.is_file():
                errors.append(f"{path.name}: missing")
            elif path.read_text(encoding="utf-8") != expected:
                errors.append(f"{path.name}: generated content differs")
        if errors:
            print("\n".join(errors))
            return 1
        print("compatibility projection v2 check passed")
        return 0
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    print("wrote " + ", ".join(path.name for path in outputs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())