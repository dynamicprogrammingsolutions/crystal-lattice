"""Official Anthropic reasoning controls and model capability normalization."""

from __future__ import annotations

import re
from typing import Any

from agent_core.types import ProviderExtensionPlugin


_EFFORT_ORDER = ("low", "medium", "high", "xhigh", "max")
_THINKING_TYPE_ORDER = ("enabled", "adaptive")
_DISPLAY_OPTIONS = ("summarized", "omitted")
_INTERLEAVED_BETA = "interleaved-thinking-2025-05-14"


def _supported(value: Any) -> bool:
    return isinstance(value, dict) and value.get("supported") is True


def _string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [item for item in value if isinstance(item, str) and item]


def _merge_details(
    base: dict[str, Any],
    overlay: dict[str, Any],
) -> dict[str, Any]:
    merged = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = _merge_details(merged[key], value)
        elif isinstance(value, dict):
            merged[key] = _merge_details({}, value)
        elif isinstance(value, list):
            merged[key] = list(value)
        else:
            merged[key] = value
    return merged


def _normalize_details(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    thinking_types = [
        item
        for item in _THINKING_TYPE_ORDER
        if item in _string_list(value.get("thinking_types"))
    ]
    effort_levels = [
        item
        for item in _EFFORT_ORDER
        if item in _string_list(value.get("effort_levels"))
    ]
    context_raw = value.get("context_management")
    context = (
        {
            str(key): bool(enabled)
            for key, enabled in context_raw.items()
            if isinstance(key, str) and isinstance(enabled, bool)
        }
        if isinstance(context_raw, dict)
        else {}
    )
    result: dict[str, Any] = {}
    if thinking_types:
        result["thinking_types"] = thinking_types
    if effort_levels:
        result["effort_levels"] = effort_levels
    if isinstance(value.get("adaptive_interleaving"), bool):
        result["adaptive_interleaving"] = value["adaptive_interleaving"]
    manual_beta = value.get("manual_interleaving_beta")
    if isinstance(manual_beta, str) and manual_beta:
        result["manual_interleaving_beta"] = manual_beta
    if context:
        result["context_management"] = context
    return result


def _details_from_official_capabilities(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    thinking = value.get("thinking")
    thinking = thinking if isinstance(thinking, dict) else {}
    thinking_types_raw = thinking.get("types")
    thinking_types_raw = (
        thinking_types_raw if isinstance(thinking_types_raw, dict) else {}
    )
    thinking_types = [
        item
        for item in _THINKING_TYPE_ORDER
        if _supported(thinking_types_raw.get(item))
    ]

    effort = value.get("effort")
    effort = effort if isinstance(effort, dict) else {}
    effort_levels = [item for item in _EFFORT_ORDER if _supported(effort.get(item))]

    context_raw = value.get("context_management")
    context_raw = context_raw if isinstance(context_raw, dict) else {}
    context = {
        key: True
        for key in (
            "clear_thinking_20251015",
            "clear_tool_uses_20250919",
            "compact_20260112",
        )
        if _supported(context_raw.get(key))
    }

    result: dict[str, Any] = {}
    if thinking_types:
        result["thinking_types"] = thinking_types
    if effort_levels:
        result["effort_levels"] = effort_levels
    if "adaptive" in thinking_types:
        result["adaptive_interleaving"] = True
    if context:
        result["context_management"] = context
    return result


_FALLBACK_RULES: tuple[tuple[re.Pattern[str], dict[str, Any]], ...] = (
    (
        re.compile(r"^claude-(?:haiku|sonnet|opus)-4-5(?:$|-\d{8}$)"),
        {"thinking_types": ["enabled"]},
    ),
    (
        re.compile(r"^claude-(?:sonnet|opus)-4-5(?:$|-\d{8}$)"),
        {"manual_interleaving_beta": _INTERLEAVED_BETA},
    ),
    (
        re.compile(r"^claude-opus-4-5(?:$|-\d{8}$)"),
        {"effort_levels": ["low", "medium", "high"]},
    ),
    (
        re.compile(r"^claude-(?:sonnet|opus)-4-6$"),
        {
            "thinking_types": ["enabled", "adaptive"],
            "effort_levels": ["low", "medium", "high", "max"],
            "adaptive_interleaving": True,
            "manual_interleaving_beta": _INTERLEAVED_BETA,
        },
    ),
    (
        re.compile(r"^claude-(?:sonnet-5|opus-4-(?:7|8)|opus-5|fable-5|mythos-5)$"),
        {
            "thinking_types": ["adaptive"],
            "effort_levels": ["low", "medium", "high", "xhigh", "max"],
            "adaptive_interleaving": True,
        },
    ),
    (
        re.compile(r"^claude-mythos-preview$"),
        {
            "thinking_types": ["adaptive"],
            "effort_levels": ["low", "medium", "high", "max"],
            "adaptive_interleaving": True,
        },
    ),
)


def _fallback_details(model_id: str) -> dict[str, Any]:
    result: dict[str, Any] = {}
    normalized = model_id.strip().lower()
    for pattern, overlay in _FALLBACK_RULES:
        if pattern.search(normalized):
            result = _merge_details(result, overlay)
    return _normalize_details(result)


def _selected_details(
    config: dict[str, Any],
    models: list[dict[str, Any]],
) -> dict[str, Any]:
    selected = config.get("model")
    if isinstance(selected, str):
        for model in models:
            if model.get("id") == selected:
                value = model.get("anthropic_reasoning_controls")
                if isinstance(value, dict):
                    return _normalize_details(value)
    explicit = config.get("anthropic_reasoning_capabilities")
    return _normalize_details(explicit)


class AnthropicReasoningControlsExtension(ProviderExtensionPlugin):
    """Own official-style Anthropic reasoning controls and their UI."""

    name = "anthropic_reasoning_controls"
    version = "0.1.0"
    priority = 60

    def required_tags(self) -> list[str]:
        return [
            "provider:anthropic",
            "supports_anthropic_reasoning_controls",
        ]

    def get_tags(
        self,
        config: dict[str, Any],
        models: list[dict[str, Any]],
    ) -> list[str]:
        return ["ext:anthropic_reasoning_controls"]

    def get_models(
        self,
        config: dict[str, Any],
        models: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        explicit = _normalize_details(config.get("anthropic_reasoning_capabilities"))
        selected = config.get("model")
        output: list[dict[str, Any]] = []
        selected_seen = False

        for model in models:
            model_id = model.get("id")
            if not isinstance(model_id, str) or not model_id:
                output.append(dict(model))
                continue
            selected_seen = selected_seen or model_id == selected
            raw_capabilities = model.get("capabilities")
            has_reasoning_descriptor = isinstance(raw_capabilities, dict) and any(
                key in raw_capabilities for key in ("thinking", "effort")
            )
            details = (
                _details_from_official_capabilities(raw_capabilities)
                if has_reasoning_descriptor
                else _fallback_details(model_id)
            )
            if model_id == selected and explicit:
                details = _merge_details(details, explicit)
            normalized = _normalize_details(details)
            output.append(
                {
                    **model,
                    **(
                        {"anthropic_reasoning_controls": normalized}
                        if normalized
                        else {}
                    ),
                }
            )

        if isinstance(selected, str) and selected and not selected_seen:
            details = _fallback_details(selected)
            if explicit:
                details = _merge_details(details, explicit)
            normalized = _normalize_details(details)
            if normalized:
                output.append(
                    {
                        "id": selected,
                        "name": selected,
                        "anthropic_reasoning_controls": normalized,
                    }
                )

        return output

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "anthropic_reasoning_capabilities": {
                "type": "object",
                "required": False,
            },
            "anthropic_reasoning_mode": {
                "type": "string",
                "enum": ["disabled", "manual", "adaptive"],
                "required": False,
            },
            "anthropic_reasoning_effort": {
                "type": "string",
                "enum": list(_EFFORT_ORDER),
                "required": False,
            },
            "anthropic_reasoning_budget_tokens": {
                "type": "integer",
                "default": 1024,
            },
            "anthropic_reasoning_display": {
                "type": "string",
                "enum": list(_DISPLAY_OPTIONS),
                "required": False,
            },
        }

    def get_ui_elements(
        self,
        config: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        models = (context or {}).get("models")
        models = models if isinstance(models, list) else []
        details = _selected_details(config, models)
        thinking_types = _string_list(details.get("thinking_types"))
        effort_levels = _string_list(details.get("effort_levels"))
        if not thinking_types and not effort_levels:
            return []

        elements: list[dict[str, Any]] = []
        mode_values = ["disabled"]
        if "enabled" in thinking_types:
            mode_values.append("manual")
        if "adaptive" in thinking_types:
            mode_values.append("adaptive")
        if len(mode_values) > 1:
            mode_element: dict[str, Any] = {
                "type": "select",
                "key": "anthropic_reasoning_mode",
                "label": "Anthropic reasoning mode",
                "options": [
                    {"value": value, "label": value.title()} for value in mode_values
                ],
            }
            if "anthropic_reasoning_mode" in config:
                mode_element["default"] = config["anthropic_reasoning_mode"]
            elements.append(mode_element)

        if effort_levels:
            effort_options = [
                {
                    "value": value,
                    "label": value,
                }
                for value in effort_levels
            ]
            effort_element: dict[str, Any] = {
                "ui_type": "config",
                "type": "select",
                "key": "anthropic_reasoning_effort",
                "label": "Anthropic reasoning effort",
                "icon": "sliders",
                "options": effort_options,
                "rich_ui": {
                    "kind": "dropdown",
                    "label": "Reasoning effort",
                    "show_label": False,
                    "show_icon": False,
                    "options": effort_options,
                    "placements": ["composer"],
                    "default_pinned": True,
                },
            }
            if "anthropic_reasoning_effort" in config:
                effort_element["default"] = config["anthropic_reasoning_effort"]
            elements.append(effort_element)

        if "enabled" in thinking_types:
            budget_element: dict[str, Any] = {
                "type": "number",
                "key": "anthropic_reasoning_budget_tokens",
                "label": "Anthropic reasoning budget tokens",
                "default": int(config.get("anthropic_reasoning_budget_tokens") or 1024),
            }
            elements.append(budget_element)

        display_element: dict[str, Any] = {
            "type": "select",
            "key": "anthropic_reasoning_display",
            "label": "Anthropic reasoning display",
            "options": [
                {"value": value, "label": value.title()} for value in _DISPLAY_OPTIONS
            ],
        }
        if "anthropic_reasoning_display" in config:
            display_element["default"] = config["anthropic_reasoning_display"]
        elements.append(display_element)
        return elements

    def init(self, config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        return state

    def initialize_request(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ):
        config = state.get("config")
        config = config if isinstance(config, dict) else {}
        request = state.get("request")
        request = request if isinstance(request, dict) else {}
        payload = dict(request.get("payload") or {})
        changed = False

        mode = config.get("anthropic_reasoning_mode")
        display = config.get("anthropic_reasoning_display")
        if mode in {"disabled", "manual", "adaptive"}:
            thinking = dict(payload.get("thinking") or {})
            if mode == "disabled":
                thinking = {"type": "disabled"}
            elif mode == "manual":
                thinking["type"] = "enabled"
                thinking["budget_tokens"] = max(
                    1, int(config.get("anthropic_reasoning_budget_tokens") or 1024)
                )
            else:
                thinking["type"] = "adaptive"
                thinking.pop("budget_tokens", None)
            if mode != "disabled" and display in _DISPLAY_OPTIONS:
                thinking["display"] = display
            else:
                thinking.pop("display", None)
            payload["thinking"] = thinking
            changed = True

        effort = config.get("anthropic_reasoning_effort")
        if isinstance(effort, str) and effort:
            output_config = dict(payload.get("output_config") or {})
            output_config["effort"] = effort
            payload["output_config"] = output_config
            changed = True

        if not changed:
            return list(native_messages), state
        return list(native_messages), {
            **state,
            "request": {**request, "payload": payload},
        }


__all__ = [
    "AnthropicReasoningControlsExtension",
]
