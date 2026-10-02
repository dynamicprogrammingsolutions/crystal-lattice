"""Shared Anthropic native context-management helpers."""

from __future__ import annotations

from typing import Any

COMPACTION_BETA = "compact-2026-01-12"
CONTEXT_EDITING_BETA = "context-management-2025-06-27"
REQUEST_REQUIRED_BETAS_KEY = "anthropic_required_betas"


def _supported(value: Any) -> bool:
    return isinstance(value, dict) and value.get("supported") is True


def _selected_context_capabilities(
    config: dict[str, Any],
    models: list[dict[str, Any]],
) -> dict[str, Any]:
    selected = config.get("model")
    if not isinstance(selected, str) or not selected:
        return {}
    for model in models:
        if not isinstance(model, dict) or model.get("id") != selected:
            continue
        capabilities = model.get("capabilities")
        capabilities = capabilities if isinstance(capabilities, dict) else {}
        context_management = capabilities.get("context_management")
        return context_management if isinstance(context_management, dict) else {}
    return {}


def compaction_supported(
    config: dict[str, Any],
    models: list[dict[str, Any]],
) -> bool:
    capabilities = config.get("capabilities")
    capabilities = capabilities if isinstance(capabilities, dict) else {}
    explicit = capabilities.get("anthropic_compaction")
    if isinstance(explicit, bool):
        return explicit
    context_management = _selected_context_capabilities(config, models)
    return _supported(context_management.get("compact_20260112"))


def context_editing_supported(
    config: dict[str, Any],
    models: list[dict[str, Any]],
) -> bool:
    capabilities = config.get("capabilities")
    capabilities = capabilities if isinstance(capabilities, dict) else {}
    explicit = capabilities.get("anthropic_context_editing")
    if isinstance(explicit, bool):
        return explicit
    context_management = _selected_context_capabilities(config, models)
    return _supported(context_management.get("clear_thinking_20251015")) or _supported(
        context_management.get("clear_tool_uses_20250919")
    )


def append_context_management_edits(
    state: dict[str, Any],
    edits: list[dict[str, Any]],
    *,
    required_betas: list[str],
) -> dict[str, Any]:
    if not edits:
        return state
    request = state.get("request")
    request = request if isinstance(request, dict) else {}
    payload = dict(request.get("payload") or {})
    context_management = payload.get("context_management")
    context_management = (
        dict(context_management) if isinstance(context_management, dict) else {}
    )
    raw_edits = context_management.get("edits")
    existing_edits = (
        [dict(edit) for edit in raw_edits if isinstance(edit, dict)]
        if isinstance(raw_edits, list)
        else []
    )
    context_management["edits"] = [
        *existing_edits,
        *[dict(edit) for edit in edits],
    ]
    payload["context_management"] = context_management

    raw_required = request.get(REQUEST_REQUIRED_BETAS_KEY)
    existing_required = (
        [item for item in raw_required if isinstance(item, str) and item]
        if isinstance(raw_required, list)
        else []
    )
    merged_required = list(dict.fromkeys([*existing_required, *required_betas]))
    return {
        **state,
        "request": {
            **request,
            "payload": payload,
            REQUEST_REQUIRED_BETAS_KEY: merged_required,
        },
    }


def request_required_betas(state: dict[str, Any]) -> list[str]:
    request = state.get("request")
    request = request if isinstance(request, dict) else {}
    value = request.get(REQUEST_REQUIRED_BETAS_KEY)
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


__all__ = [
    "COMPACTION_BETA",
    "CONTEXT_EDITING_BETA",
    "REQUEST_REQUIRED_BETAS_KEY",
    "append_context_management_edits",
    "compaction_supported",
    "context_editing_supported",
    "request_required_betas",
]
