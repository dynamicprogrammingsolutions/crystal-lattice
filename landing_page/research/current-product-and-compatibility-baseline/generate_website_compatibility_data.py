#!/usr/bin/env python3
"""Validate and generate the compact website compatibility projection."""

from __future__ import annotations

import argparse
import ast
import copy
import csv
import json
import re
from pathlib import Path
from typing import Any, Mapping


HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = HERE / "website-compatibility-selection.json"
FEATURE_CATALOG = HERE / "feature-catalog.json"
APPLICATION_FEATURES = HERE / "application-feature-compatibility.csv"
PROVIDER_MATRIX = HERE / "provider-support-matrix.json"
OUTPUT_JSON = HERE / "website-compatibility-data.json"
OUTPUT_MARKDOWN = HERE / "website-compatibility-data.md"

PUBLIC_STATUSES = {
    "available",
    "conditional",
    "optional",
    "planned",
    "unavailable",
    "not_applicable",
    "not_verified",
}

PROVIDER_STATUS_MAP = {
    "supported": "available",
    "conditional": "conditional",
    "planned": "planned",
}

PROVIDER_PACKAGES = {
    "openai-api": "openai_responses",
    "openai-chatgpt": "openai_responses",
    "openrouter-chat": "openrouter",
    "openrouter-responses": "openrouter_responses",
    "anthropic": "anthropic-compatible",
    "ollama": "reference-openai-compatible-provider",
    "fireworks": "reference-openai-compatible-provider",
    "zai": "reference-openai-compatible-provider",
    "custom-openai-compatible": "reference-openai-compatible-provider",
    "openrouter-image": "openrouter",
}

PROVIDER_FEATURE_DESCRIPTIONS = {
    "api_key_auth": "Authenticates requests with the API key configured for this provider route.",
    "subscription_account_auth": "Authenticates through a saved subscription-account session rather than a direct API key.",
    "model_discovery": "Discovers available models through the provider route and applies maintained fallbacks where documented.",
    "streaming": "Streams provider response events into the Crystal Lattice request pipeline.",
    "tool_calling": "Maps Crystal Lattice tool schemas and calls to the provider's native tool-calling format.",
    "reasoning": "Exposes provider-native reasoning controls or reasoning metadata when supported by the selected model.",
    "verbosity": "Passes a provider-native response verbosity control for model families that support it.",
    "usage_tokens": "Normalizes provider usage and token metadata for the application.",
    "cost_reporting": "Supplies provider-reported cost data or a clearly identified local estimate derived from usage.",
    "prompt_caching": "Configures and reports the provider's native prompt-caching behavior.",
    "native_web_search": "Enables the provider's own hosted web-search capability rather than a model-family search tool.",
    "native_compaction": "Uses provider-native context compaction while preserving continuation state.",
    "flex_processing": "Selects the provider's lower-priority flex processing mode.",
    "fast_mode": "Selects the provider's fast, priority, or equivalent processing tier.",
    "image_input": "Maps image attachments into the provider request format.",
    "pdf_input": "Maps PDF or file attachments into the provider request or upload flow.",
    "image_generation": "Uses the provider route to generate image output.",
    "provider_routing": "Passes provider or endpoint routing controls owned by this route.",
    "retry_rate_limit": "Applies route-specific retry, throttling, and rate-limit handling.",
}

PACKAGE_FEATURE_ENTRIES = {
    "openai_responses": {
        "api_key_auth": [
            "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider"
        ],
        "model_discovery": [
            "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider"
        ],
        "streaming": [
            "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider"
        ],
        "tool_calling": [
            "openai_responses_plugins.openai_responses_tools_extension.OpenAIResponsesToolsExtension"
        ],
        "reasoning": [
            "openai_responses_plugins.openai_responses_reasoning_extension.OpenAIResponsesReasoningExtension"
        ],
        "verbosity": [
            "openai_responses_plugins.openai_responses_verbosity_extension.OpenAIResponsesVerbosityExtension"
        ],
        "usage_tokens": [
            "openai_responses_plugins.openai_responses_usage_extension.OpenAIResponsesUsageExtension"
        ],
        "cost_reporting": [
            "openai_responses_plugins.openai_responses_usage_extension.OpenAIResponsesUsageExtension"
        ],
        "prompt_caching": [
            "openai_responses_plugins.openai_responses_prompt_caching_extension.OpenAIResponsesPromptCachingExtension"
        ],
        "native_web_search": [
            "openai_responses_plugins.openai_responses_websearch_extension.OpenAIResponsesWebSearchExtension"
        ],
        "native_compaction": [
            "openai_responses_plugins.openai_responses_native_compaction_extension.OpenAIResponsesNativeCompactionExtension"
        ],
        "flex_processing": [
            "openai_responses_plugins.openai_responses_flex_processing_extension.OpenAIResponsesFlexProcessingExtension"
        ],
        "fast_mode": [
            "openai_responses_plugins.openai_responses_fast_mode_extension.OpenAIResponsesFastModeExtension"
        ],
        "image_input": [
            "openai_responses_plugins.openai_responses_attachments_extension.OpenAIResponsesAttachmentsExtension"
        ],
        "pdf_input": [
            "openai_responses_plugins.openai_responses_attachments_extension.OpenAIResponsesAttachmentsExtension"
        ],
        "retry_rate_limit": [
            "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider"
        ],
    },
    "openrouter": {
        "api_key_auth": ["openrouter_plugins.openrouter_provider.OpenRouterProvider"],
        "model_discovery": [
            "openrouter_plugins.openrouter_provider.OpenRouterProvider"
        ],
        "streaming": ["openrouter_plugins.openrouter_provider.OpenRouterProvider"],
        "tool_calling": [
            "openrouter_plugins.openrouter_tools_extension.OpenRouterToolsExtension"
        ],
        "reasoning": [
            "openrouter_plugins.openrouter_reasoning_extension.OpenRouterReasoningExtension"
        ],
        "verbosity": [
            "openrouter_plugins.openrouter_verbosity_extension.OpenRouterVerbosityExtension"
        ],
        "usage_tokens": [
            "openrouter_plugins.openrouter_usage_extension.OpenRouterUsageExtension"
        ],
        "cost_reporting": [
            "openrouter_plugins.openrouter_usage_extension.OpenRouterUsageExtension"
        ],
        "prompt_caching": [
            "openrouter_plugins.claude_caching_extension.ClaudeCachingExtension"
        ],
        "native_web_search": [
            "openrouter_plugins.openrouter_websearch_extension.OpenRouterWebSearchExtension"
        ],
        "image_input": [
            "openrouter_plugins.openrouter_attachments_extension.OpenRouterAttachmentsExtension"
        ],
        "image_generation": [
            "openrouter_plugins.openrouter_image_generation_provider.OpenRouterImageGenerationProvider"
        ],
        "provider_routing": [
            "openrouter_plugins.openrouter_provider.OpenRouterProvider"
        ],
        "retry_rate_limit": [
            "openrouter_plugins.openrouter_provider.OpenRouterProvider"
        ],
    },
    "openrouter_responses": {
        "api_key_auth": [
            "openrouter_responses_plugins.openrouter_responses_provider.OpenRouterResponsesProvider"
        ],
        "model_discovery": [
            "openrouter_responses_plugins.openrouter_responses_provider.OpenRouterResponsesProvider"
        ],
        "streaming": [
            "openrouter_responses_plugins.openrouter_responses_provider.OpenRouterResponsesProvider"
        ],
        "tool_calling": [
            "openrouter_responses_plugins.openrouter_responses_tools_extension.OpenRouterResponsesToolsExtension"
        ],
        "reasoning": [
            "openrouter_responses_plugins.openrouter_responses_reasoning_extension.OpenRouterResponsesReasoningExtension"
        ],
        "verbosity": [
            "openrouter_responses_plugins.openrouter_responses_verbosity_extension.OpenRouterResponsesVerbosityExtension"
        ],
        "usage_tokens": [
            "openrouter_responses_plugins.openrouter_responses_usage_extension.OpenRouterResponsesUsageExtension"
        ],
        "cost_reporting": [
            "openrouter_responses_plugins.openrouter_responses_usage_extension.OpenRouterResponsesUsageExtension"
        ],
        "prompt_caching": [
            "openrouter_responses_plugins.openrouter_responses_claude_caching_extension.OpenRouterResponsesClaudeCachingExtension"
        ],
        "native_web_search": [
            "openrouter_responses_plugins.openrouter_responses_websearch_extension.OpenRouterResponsesWebSearchExtension"
        ],
        "image_input": [
            "openrouter_responses_plugins.openrouter_responses_provider.OpenRouterResponsesProvider"
        ],
        "retry_rate_limit": [
            "openrouter_responses_plugins.openrouter_responses_provider.OpenRouterResponsesProvider"
        ],
    },
    "anthropic-compatible": {
        "api_key_auth": ["anthropic_plugins.provider.AnthropicProvider"],
        "model_discovery": ["anthropic_plugins.provider.AnthropicProvider"],
        "streaming": ["anthropic_plugins.provider.AnthropicProvider"],
        "tool_calling": ["anthropic_plugins.tools_extension.AnthropicToolsExtension"],
        "reasoning": [
            "anthropic_plugins.reasoning_extension.AnthropicReasoningExtension",
            "anthropic_plugins.reasoning_controls_extension.AnthropicReasoningControlsExtension",
        ],
        "usage_tokens": ["anthropic_plugins.usage_extension.AnthropicUsageExtension"],
        "prompt_caching": [
            "anthropic_plugins.prompt_caching_extension.AnthropicPromptCachingExtension"
        ],
        "retry_rate_limit": ["anthropic_plugins.provider.AnthropicProvider"],
    },
    "reference-openai-compatible-provider": {
        "api_key_auth": [
            "reference_openai_compatible_provider.provider.OpenAICompatibleProvider"
        ],
        "model_discovery": [
            "reference_openai_compatible_provider.provider.OpenAICompatibleProvider"
        ],
        "streaming": [
            "reference_openai_compatible_provider.provider.OpenAICompatibleProvider"
        ],
        "tool_calling": [
            "reference_openai_compatible_provider.tools_extension.OpenAICompatibleToolsExtension"
        ],
        "reasoning": [
            "reference_openai_compatible_provider.reasoning_extension.OpenAICompatibleReasoningExtension"
        ],
        "usage_tokens": [
            "reference_openai_compatible_provider.usage_extension.OpenAICompatibleUsageExtension"
        ],
        "cost_reporting": [
            "reference_openai_compatible_provider.usage_extension.OpenAICompatibleUsageExtension"
        ],
        "image_input": [
            "reference_openai_compatible_provider.attachments_extension.OpenAICompatibleAttachmentsExtension"
        ],
        "provider_routing": [
            "reference_openai_compatible_provider.provider.OpenAICompatibleProvider"
        ],
        "retry_rate_limit": [
            "reference_openai_compatible_provider.provider.OpenAICompatibleProvider"
        ],
    },
}

PROVIDER_FEATURE_ENTRY_OVERRIDES = {
    ("openai-chatgpt", "subscription_account_auth"): [
        "openai_responses_plugins.openai_responses_chatgpt_auth_feature.OpenAIResponsesChatGPTAuthFeature"
    ],
    ("openrouter-image", "api_key_auth"): [
        "openrouter_plugins.openrouter_image_generation_provider.OpenRouterImageGenerationProvider"
    ],
    ("openrouter-image", "model_discovery"): [
        "openrouter_plugins.openrouter_image_generation_provider.OpenRouterImageGenerationProvider"
    ],
    ("openrouter-image", "image_input"): [
        "openrouter_plugins.openrouter_image_generation_attachments_extension.OpenRouterImageGenerationAttachmentsExtension"
    ],
    ("openrouter-image", "image_generation"): [
        "openrouter_plugins.openrouter_image_generation_provider.OpenRouterImageGenerationProvider"
    ],
    ("openrouter-chat", "image_generation"): [
        "openrouter_plugins.openrouter_image_generation_provider.OpenRouterImageGenerationProvider"
    ],
}

PROVIDER_PLANNED_PLUGIN_NAMES = {
    ("anthropic", "subscription_account_auth"): ["anthropic_oauth"],
    ("anthropic", "cost_reporting"): ["anthropic_cost_estimation"],
    ("anthropic", "native_web_search"): ["anthropic_server_web_tools"],
    ("anthropic", "native_compaction"): [
        "anthropic_compaction",
        "anthropic_context_editing",
    ],
    ("anthropic", "fast_mode"): ["anthropic_fast_mode"],
    ("anthropic", "image_input"): ["anthropic_attachments"],
    ("anthropic", "pdf_input"): ["anthropic_files"],
}

APPLICATION_STATUS_MAP = {
    "current": "available",
    "partial": "conditional",
    "optional": "optional",
    "experimental": "conditional",
    "planned": "planned",
    "unsupported": "unavailable",
    "not_applicable": "not_applicable",
    "unknown": "not_verified",
}


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _application_feature_rows() -> dict[str, dict[str, str]]:
    with APPLICATION_FEATURES.open(newline="", encoding="utf-8") as stream:
        rows = list(csv.DictReader(stream))
    result: dict[str, dict[str, str]] = {}
    for row in rows:
        source_path = str(row.get("source_path") or "")
        plugin_id = (
            source_path.removeprefix("plugins/")
            if source_path.startswith("plugins/")
            else str(row["row_id"]).removeprefix("feature:")
        )
        result[plugin_id] = row
    return result


def _descriptor_entries(package_id: str) -> set[str]:
    path = ROOT / "plugins" / package_id / "agent_plugin.json"
    if not path.is_file():
        raise ValueError(f"{package_id}: missing agent_plugin.json")
    payload = _load_json(path)
    return {str(value) for value in payload.get("entries") or []}


def _runtime_plugin_name(package_id: str, entry: str) -> str:
    module_name, class_name = entry.rsplit(".", 1)
    source_path = (
        ROOT
        / "plugins"
        / package_id
        / "src"
        / Path(*module_name.split(".")).with_suffix(".py")
    )
    if source_path.is_file():
        tree = ast.parse(source_path.read_text(encoding="utf-8"))
        for node in tree.body:
            if not isinstance(node, ast.ClassDef) or node.name != class_name:
                continue
            for statement in node.body:
                target_name = None
                value = None
                if isinstance(statement, ast.Assign):
                    if len(statement.targets) == 1 and isinstance(
                        statement.targets[0], ast.Name
                    ):
                        target_name = statement.targets[0].id
                    value = statement.value
                elif isinstance(statement, ast.AnnAssign) and isinstance(
                    statement.target, ast.Name
                ):
                    target_name = statement.target.id
                    value = statement.value
                if (
                    target_name == "name"
                    and isinstance(value, ast.Constant)
                    and isinstance(value.value, str)
                ):
                    return value.value
    return module_name.rsplit(".", 1)[-1]


def _unique(values: list[str], context: str) -> None:
    if len(values) != len(set(values)):
        raise ValueError(f"{context}: duplicate ids")


def _validate_status(status: str, context: str) -> None:
    if status not in PUBLIC_STATUSES:
        raise ValueError(f"{context}: unknown display status {status!r}")


def _validate_features(
    source: Mapping[str, Any],
    *,
    feature_catalog: Mapping[str, Any],
    application_rows: Mapping[str, Mapping[str, str]],
) -> None:
    selection = source["feature_selection"]
    selected = [str(value) for value in selection["plugin_ids"]]
    _unique(selected, "feature plugin selection")
    catalog_rows = {str(row["plugin_id"]): row for row in feature_catalog["rows"]}
    excluded_groups = selection.get("excluded_overlaps") or {}
    excluded = [
        str(plugin_id) for values in excluded_groups.values() for plugin_id in values
    ]
    _unique(excluded, "feature overlap exclusions")
    overlap = set(selected) & set(excluded)
    if overlap:
        raise ValueError(
            f"feature selection appears in both selected and excluded sets: "
            f"{sorted(overlap)}"
        )
    missing_catalog = set(selected) - set(catalog_rows)
    if missing_catalog:
        raise ValueError(
            f"feature selection has unknown catalog plugins: "
            f"{sorted(missing_catalog)}"
        )
    missing_application = set(selected) - set(application_rows)
    if missing_application:
        raise ValueError(
            f"feature selection has unknown application rows: "
            f"{sorted(missing_application)}"
        )
    classified = set(selected) | set(excluded)
    if classified != set(application_rows):
        raise ValueError(
            "feature selection must classify every application-feature row; "
            f"missing={sorted(set(application_rows) - classified)}, "
            f"extra={sorted(classified - set(application_rows))}"
        )
    for plugin_id in selected:
        catalog_row = catalog_rows[plugin_id]
        expected_path = f"plugins/{plugin_id}"
        if catalog_row.get("source_path") != expected_path:
            raise ValueError(
                f"feature:{plugin_id}: expected source path {expected_path!r}, "
                f"got {catalog_row.get('source_path')!r}"
            )
        capability_state = str(
            application_rows[plugin_id].get("capability_state") or "unknown"
        )
        status = APPLICATION_STATUS_MAP.get(capability_state)
        if status is None:
            raise ValueError(
                f"feature:{plugin_id}: unknown capability state "
                f"{capability_state!r}"
            )
        _validate_status(status, f"feature:{plugin_id}")


def _public_features(
    source: Mapping[str, Any],
    feature_catalog: Mapping[str, Any],
    application_rows: Mapping[str, Mapping[str, str]],
) -> dict[str, Any]:
    selection = source["feature_selection"]
    catalog_rows = {str(row["plugin_id"]): row for row in feature_catalog["rows"]}
    rows = []
    for plugin_id in selection["plugin_ids"]:
        catalog_row = catalog_rows[plugin_id]
        application_row = application_rows[plugin_id]
        capability_state = str(application_row.get("capability_state") or "unknown")
        rows.append(
            {
                "feature_id": plugin_id,
                "plugin_id": plugin_id,
                "plugin_path": catalog_row["source_path"],
                "status": APPLICATION_STATUS_MAP[capability_state],
                "capability_state": capability_state,
                "lifecycle_status": catalog_row["lifecycle_status"],
                "default_selected": bool(catalog_row["default_selected"]),
                "description": catalog_row["description"],
                "limitations": application_row.get("limitations") or "",
            }
        )
    return {
        "title": selection["title"],
        "description": selection["description"],
        "rows": rows,
        "represented_elsewhere": copy.deepcopy(
            selection.get("excluded_overlaps") or {}
        ),
    }


def _provider_lookup(
    provider_matrix: Mapping[str, Any],
) -> tuple[dict[str, dict[str, Any]], dict[str, dict[str, Any]]]:
    features = {
        str(feature["feature_id"]): dict(feature)
        for feature in provider_matrix["features"]
    }
    providers = {
        str(provider["provider_id"]): dict(provider)
        for provider in provider_matrix["providers"]
    }
    return features, providers


def _provider_feature_entries(
    provider_id: str,
    package_id: str,
    feature_id: str,
) -> list[str]:
    override = PROVIDER_FEATURE_ENTRY_OVERRIDES.get((provider_id, feature_id))
    if override is not None:
        return list(override)
    return list(PACKAGE_FEATURE_ENTRIES.get(package_id, {}).get(feature_id) or [])


def _provider_feature_description(
    provider_label: str,
    feature_id: str,
    status: str,
    note: str,
) -> str:
    base = PROVIDER_FEATURE_DESCRIPTIONS[feature_id]
    if status == "planned":
        base = f"Planned: {base[0].lower()}{base[1:]}"
    if note:
        return f"{base} {note}"
    return base


def _validate_providers(
    source: Mapping[str, Any],
    provider_matrix: Mapping[str, Any],
) -> None:
    selection = source["provider_selection"]
    selected = [str(value) for value in selection["provider_ids"]]
    _unique(selected, "provider selection")
    features, providers = _provider_lookup(provider_matrix)
    if set(selected) != set(providers):
        raise ValueError(
            "provider selection must include every retained provider route; "
            f"missing={sorted(set(providers) - set(selected))}, "
            f"extra={sorted(set(selected) - set(providers))}"
        )
    if set(selection["access"]) != set(selected):
        raise ValueError("provider access labels must match selected providers")
    for provider_id in selected:
        provider = providers[provider_id]
        package_id = PROVIDER_PACKAGES.get(provider_id)
        if package_id is None:
            raise ValueError(f"provider:{provider_id}: missing plugin bundle")
        if provider.get("implementation") != package_id:
            raise ValueError(
                f"provider:{provider_id}: plugin bundle {package_id!r} does not "
                f"match implementation {provider.get('implementation')!r}"
            )
        descriptor_entries = _descriptor_entries(package_id)
        for cell in provider["cells"]:
            feature_id = str(cell["feature_id"])
            if feature_id not in features:
                raise ValueError(
                    f"provider:{provider_id}: unknown feature {feature_id!r}"
                )
            source_status = str(cell["status"])
            if source_status not in PROVIDER_STATUS_MAP:
                continue
            context = f"provider:{provider_id}:{feature_id}"
            display_status = PROVIDER_STATUS_MAP[source_status]
            _validate_status(display_status, context)
            if source_status == "planned":
                planned_names = PROVIDER_PLANNED_PLUGIN_NAMES.get(
                    (provider_id, feature_id)
                )
                if not planned_names:
                    raise ValueError(
                        f"{context}: planned feature has no intended plugin name"
                    )
                continue
            entries = _provider_feature_entries(
                provider_id,
                package_id,
                feature_id,
            )
            if not entries:
                raise ValueError(f"{context}: current feature has no plugin entry")
            missing = set(entries) - descriptor_entries
            if missing:
                raise ValueError(
                    f"{context}: descriptor entries not found {sorted(missing)}"
                )


def _public_providers(
    source: Mapping[str, Any],
    provider_matrix: Mapping[str, Any],
) -> dict[str, Any]:
    selection = source["provider_selection"]
    feature_defs, provider_defs = _provider_lookup(provider_matrix)
    providers = []
    for provider_id in selection["provider_ids"]:
        provider = provider_defs[provider_id]
        package_id = PROVIDER_PACKAGES[provider_id]
        rows = []
        for cell in provider["cells"]:
            feature_id = str(cell["feature_id"])
            source_status = str(cell["status"])
            if source_status not in PROVIDER_STATUS_MAP:
                continue
            entries = (
                []
                if source_status == "planned"
                else _provider_feature_entries(
                    provider_id,
                    package_id,
                    feature_id,
                )
            )
            plugin_names = (
                list(PROVIDER_PLANNED_PLUGIN_NAMES[(provider_id, feature_id)])
                if source_status == "planned"
                else [_runtime_plugin_name(package_id, entry) for entry in entries]
            )
            rows.append(
                {
                    "feature_id": feature_id,
                    "feature": feature_defs[feature_id]["label"],
                    "status": PROVIDER_STATUS_MAP[source_status],
                    "source_status": source_status,
                    "plugin_bundle": package_id,
                    "plugin_bundle_path": f"plugins/{package_id}",
                    "plugin_names": plugin_names,
                    "plugin_entries": entries,
                    "description": _provider_feature_description(
                        str(provider["label"]),
                        feature_id,
                        source_status,
                        str(cell.get("note") or ""),
                    ),
                }
            )
        providers.append(
            {
                "provider_id": provider_id,
                "label": provider["label"],
                "access": selection["access"][provider_id],
                "availability": provider.get("availability"),
                "plugin_bundle": package_id,
                "plugin_bundle_path": f"plugins/{package_id}",
                "features": rows,
            }
        )
    return {
        "title": selection["title"],
        "description": selection["description"],
        "providers": providers,
    }


def _validate_model_tools(source: Mapping[str, Any]) -> None:
    families = source["model_tool_selection"]["families"]
    _unique([family["family_id"] for family in families], "model families")
    for family in families:
        package_id = family["package_id"]
        entries = _descriptor_entries(package_id)
        tools = family["tools"]
        _unique(
            [tool["tool_id"] for tool in tools],
            f"model family {family['family_id']}",
        )
        for tool in tools:
            context = f"model:{family['family_id']}:{tool['tool_id']}"
            status = str(tool["status"])
            _validate_status(status, context)
            source_entries = tool.get("source_entries") or []
            planning_source = tool.get("planning_source")
            if status == "planned":
                if source_entries:
                    raise ValueError(f"{context}: planned row has source entries")
                if not isinstance(planning_source, str):
                    raise ValueError(f"{context}: planned row has no planning source")
                if not (ROOT / planning_source).is_file():
                    raise ValueError(
                        f"{context}: missing planning source {planning_source}"
                    )
                continue
            if planning_source:
                raise ValueError(f"{context}: current row has a planning source")
            if not source_entries:
                raise ValueError(f"{context}: current row has no descriptor entry")
            missing = set(source_entries) - entries
            if missing:
                raise ValueError(
                    f"{context}: descriptor entries not found {sorted(missing)}"
                )


def _public_model_tools(source: Mapping[str, Any]) -> dict[str, Any]:
    selection = source["model_tool_selection"]
    families = []
    for family in selection["families"]:
        package_id = family["package_id"]
        tools = []
        for tool in family["tools"]:
            source_entries = list(tool.get("source_entries") or [])
            plugin_names = (
                [tool.get("planned_plugin_name") or tool["tool_id"]]
                if tool["status"] == "planned"
                else [
                    _runtime_plugin_name(package_id, entry) for entry in source_entries
                ]
            )
            tools.append(
                {
                    "tool_id": tool["tool_id"],
                    "name": tool["name"],
                    "status": tool["status"],
                    "plugin_bundle": package_id,
                    "plugin_bundle_path": f"plugins/{package_id}",
                    "plugin_names": plugin_names,
                    "plugin_entries": source_entries,
                    "description": tool["description"],
                }
            )
        families.append(
            {
                "family_id": family["family_id"],
                "label": family["label"],
                "plugin_bundle": package_id,
                "plugin_bundle_path": f"plugins/{package_id}",
                "tools": tools,
            }
        )
    return {
        "title": selection["title"],
        "description": selection["description"],
        "families": families,
    }


def _public_payload(
    source: Mapping[str, Any],
    feature_catalog: Mapping[str, Any],
    application_rows: Mapping[str, Mapping[str, str]],
    provider_matrix: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "1.1.0",
        "review_state": source["review_state"],
        "maturity": source["maturity"],
        "revision_policy": source["revision_policy"],
        "status_labels": source["display_statuses"],
        "identity_note": (
            "Compatibility profiles and tool bundles are Crystal Lattice "
            "implementations, not official upstream applications or sessions."
        ),
        "features": _public_features(
            source,
            feature_catalog,
            application_rows,
        ),
        "providers": _public_providers(source, provider_matrix),
        "model_family_tools": _public_model_tools(source),
    }


def _escape(value: Any) -> str:
    return (
        str(value if value is not None else "").replace("|", "\\|").replace("\n", " ")
    )


def _status_label(payload: Mapping[str, Any], status: str) -> str:
    return str(payload["status_labels"][status])


def _markdown(payload: Mapping[str, Any]) -> str:
    lines = [
        "# Website Compatibility Data",
        "",
        f"Review state: `{payload['review_state']}`",
        f"Maturity: `{payload['maturity']}`",
        "",
        payload["identity_note"],
        "",
        payload["revision_policy"],
        "",
        f"## {payload['features']['title']}",
        "",
        payload["features"]["description"],
        "",
        "| Plugin | Path | Status | Description | Limitations |",
        "|---|---|---|---|---|",
    ]
    for row in payload["features"]["rows"]:
        lines.append(
            "| `{}` | `{}` | {} | {} | {} |".format(
                _escape(row["plugin_id"]),
                _escape(row["plugin_path"]),
                _escape(_status_label(payload, row["status"])),
                _escape(row["description"]),
                _escape(row["limitations"]),
            )
        )
    lines.extend(["", "### Represented in the other matrices", ""])
    for group, plugin_ids in payload["features"]["represented_elsewhere"].items():
        label = str(group).replace("_", " ").title()
        lines.append(
            f"- **{_escape(label)}:** "
            + ", ".join(f"`{_escape(plugin_id)}`" for plugin_id in plugin_ids)
        )

    providers = payload["providers"]
    lines.extend(
        [
            "",
            f"## {providers['title']}",
            "",
            providers["description"],
            "",
        ]
    )
    for provider in providers["providers"]:
        lines.extend(
            [
                f"### {_escape(provider['label'])}",
                "",
                f"Access: {_escape(provider['access'])}",
                "",
                "| Feature | Status | Plugin bundle | Plugin name | Description |",
                "|---|---|---|---|---|",
            ]
        )
        bundle = (
            f"`{_escape(provider['plugin_bundle'])}`<br>"
            f"`{_escape(provider['plugin_bundle_path'])}`"
        )
        for feature in provider["features"]:
            names = "<br>".join(
                f"`{_escape(name)}`" for name in feature["plugin_names"]
            )
            lines.append(
                "| {} | {} | {} | {} | {} |".format(
                    _escape(feature["feature"]),
                    _escape(_status_label(payload, feature["status"])),
                    bundle,
                    names,
                    _escape(feature["description"]),
                )
            )
        lines.append("")

    model_tools = payload["model_family_tools"]
    lines.extend(
        [
            "",
            f"## {model_tools['title']}",
            "",
            model_tools["description"],
            "",
        ]
    )
    for family in model_tools["families"]:
        lines.extend(
            [
                f"### {_escape(family['label'])}",
                "",
                "| Tool | Status | Plugin bundle | Plugin name | Description |",
                "|---|---|---|---|---|",
            ]
        )
        bundle = (
            f"`{_escape(family['plugin_bundle'])}`<br>"
            f"`{_escape(family['plugin_bundle_path'])}`"
        )
        for tool in family["tools"]:
            names = "<br>".join(f"`{_escape(name)}`" for name in tool["plugin_names"])
            lines.append(
                "| {} | {} | {} | {} | {} |".format(
                    _escape(tool["name"]),
                    _escape(_status_label(payload, tool["status"])),
                    bundle,
                    names,
                    _escape(tool["description"]),
                )
            )
        lines.append("")
    return "\n".join(lines)


def _outputs() -> dict[Path, str]:
    source = _load_json(SOURCE)
    feature_catalog = _load_json(FEATURE_CATALOG)
    application_rows = _application_feature_rows()
    provider_matrix = _load_json(PROVIDER_MATRIX)
    _validate_features(
        source,
        feature_catalog=feature_catalog,
        application_rows=application_rows,
    )
    _validate_providers(source, provider_matrix)
    _validate_model_tools(source)
    payload = _public_payload(
        source,
        feature_catalog,
        application_rows,
        provider_matrix,
    )
    return {
        OUTPUT_JSON: json.dumps(payload, indent=2) + "\n",
        OUTPUT_MARKDOWN: _markdown(payload),
    }


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
                continue
            actual = path.read_text(encoding="utf-8")
            if actual != expected:
                errors.append(f"{path.name}: generated content differs")
            if re.search(r"\b020\b", actual):
                errors.append(
                    f"{path.name}: numeric task identifier leaked into public data"
                )
            if "tasks/" in actual:
                errors.append(
                    f"{path.name}: internal task path leaked into public data"
                )
        if errors:
            print("\n".join(errors))
            return 1
        print("website compatibility data check passed")
        return 0
    for path, content in outputs.items():
        path.write_text(content, encoding="utf-8")
    print("wrote " + ", ".join(path.name for path in outputs))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
