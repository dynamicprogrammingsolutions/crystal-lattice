"""Anthropic thinking and tool-use context editing extension."""

from __future__ import annotations

from typing import Any

from agent_core.types import ProviderExtensionPlugin

from .context_management import (
    CONTEXT_EDITING_BETA,
    append_context_management_edits,
)

_RETENTION_MODES = ("provider_default", "all", "turns")


def _integer_at_least(value: Any, *, default: int, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return default
    if value < minimum:
        raise ValueError(f"value must be at least {minimum}")
    return value


def _applied_edit_summary(native: dict[str, Any]) -> dict[str, int]:
    metadata = native.get("_metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    anthropic = metadata.get("anthropic")
    anthropic = anthropic if isinstance(anthropic, dict) else {}
    context_management = anthropic.get("context_management")
    context_management = (
        context_management if isinstance(context_management, dict) else {}
    )
    raw_edits = context_management.get("applied_edits")
    edits = raw_edits if isinstance(raw_edits, list) else []
    summary = {
        "applied_edit_count": 0,
        "cleared_input_tokens": 0,
        "cleared_thinking_turns": 0,
        "cleared_tool_uses": 0,
    }
    for edit in edits:
        if not isinstance(edit, dict):
            continue
        summary["applied_edit_count"] += 1
        for key in (
            "cleared_input_tokens",
            "cleared_thinking_turns",
            "cleared_tool_uses",
        ):
            value = edit.get(key)
            if isinstance(value, int) and not isinstance(value, bool) and value >= 0:
                summary[key] += value
    return summary


class AnthropicContextEditingExtension(ProviderExtensionPlugin):
    name = "anthropic_context_editing"
    version = "0.1.0"
    priority = 64

    def required_tags(self) -> list[str]:
        return ["provider:anthropic", "supports_anthropic_context_editing"]

    def get_tags(
        self,
        config: dict[str, Any],
        models: list[dict[str, Any]],
    ) -> list[str]:
        return ["ext:anthropic_context_editing"]

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "anthropic_thinking_retention": {
                "type": "string",
                "enum": list(_RETENTION_MODES),
                "default": "provider_default",
            },
            "anthropic_thinking_turns_to_keep": {
                "type": "integer",
                "default": 1,
                "minimum": 1,
            },
            "enable_anthropic_tool_use_clearing": {
                "type": "boolean",
                "default": False,
            },
            "anthropic_tool_use_clear_trigger_tokens": {
                "type": "integer",
                "default": 100000,
                "minimum": 10000,
            },
            "anthropic_tool_uses_to_keep": {
                "type": "integer",
                "default": 3,
                "minimum": 0,
            },
            "anthropic_tool_use_clear_at_least_tokens": {
                "type": "integer",
                "required": False,
                "minimum": 1,
            },
            "anthropic_clear_tool_inputs": {
                "type": "boolean",
                "default": False,
            },
            "anthropic_tool_use_excluded_tools": {
                "type": "array",
                "items": {"type": "string"},
                "default": [],
            },
        }

    def get_ui_elements(
        self,
        config: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        retention = config.get("anthropic_thinking_retention")
        retention = retention if retention in _RETENTION_MODES else "provider_default"
        turns_to_keep = _integer_at_least(
            config.get("anthropic_thinking_turns_to_keep"),
            default=1,
            minimum=1,
        )
        recent_turns_label = (
            "Keep latest turn"
            if turns_to_keep == 1
            else f"Keep latest {turns_to_keep} turns"
        )
        return [
            {
                "type": "select",
                "key": "anthropic_thinking_retention",
                "label": "Anthropic thinking retention",
                "options": [
                    {"value": "provider_default", "label": "Provider default"},
                    {"value": "all", "label": "Keep all thinking"},
                    {"value": "turns", "label": recent_turns_label},
                ],
                "default": retention,
            },
            {
                "type": "checkbox",
                "key": "enable_anthropic_tool_use_clearing",
                "label": "Enable Anthropic tool-use clearing",
                "default": bool(
                    config.get("enable_anthropic_tool_use_clearing", False)
                ),
            },
            {
                "type": "number",
                "key": "anthropic_tool_use_clear_trigger_tokens",
                "label": "Anthropic tool-use clearing trigger tokens",
                "default": _integer_at_least(
                    config.get("anthropic_tool_use_clear_trigger_tokens"),
                    default=100000,
                    minimum=10000,
                ),
                "minimum": 10000,
            },
            {
                "type": "number",
                "key": "anthropic_tool_uses_to_keep",
                "label": "Anthropic tool uses to keep",
                "default": _integer_at_least(
                    config.get("anthropic_tool_uses_to_keep"),
                    default=3,
                    minimum=0,
                ),
                "minimum": 0,
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.anthropic_context_editing_status",
                "template": "{{data}}",
            },
        ]

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
        edits: list[dict[str, Any]] = []

        retention = config.get("anthropic_thinking_retention")
        if retention == "all":
            edits.append(
                {
                    "type": "clear_thinking_20251015",
                    "keep": "all",
                }
            )
        elif retention == "turns":
            turns = _integer_at_least(
                config.get("anthropic_thinking_turns_to_keep"),
                default=1,
                minimum=1,
            )
            edits.append(
                {
                    "type": "clear_thinking_20251015",
                    "keep": {"type": "thinking_turns", "value": turns},
                }
            )

        if bool(config.get("enable_anthropic_tool_use_clearing", False)):
            trigger = _integer_at_least(
                config.get("anthropic_tool_use_clear_trigger_tokens"),
                default=100000,
                minimum=10000,
            )
            keep = _integer_at_least(
                config.get("anthropic_tool_uses_to_keep"),
                default=3,
                minimum=0,
            )
            tool_edit: dict[str, Any] = {
                "type": "clear_tool_uses_20250919",
                "trigger": {"type": "input_tokens", "value": trigger},
                "keep": {"type": "tool_uses", "value": keep},
                "clear_tool_inputs": bool(
                    config.get("anthropic_clear_tool_inputs", False)
                ),
            }
            clear_at_least = config.get("anthropic_tool_use_clear_at_least_tokens")
            if isinstance(clear_at_least, int) and not isinstance(clear_at_least, bool):
                if clear_at_least < 1:
                    raise ValueError(
                        "anthropic_tool_use_clear_at_least_tokens must be positive"
                    )
                tool_edit["clear_at_least"] = {
                    "type": "input_tokens",
                    "value": clear_at_least,
                }
            excluded = config.get("anthropic_tool_use_excluded_tools")
            excluded = (
                [item for item in excluded if isinstance(item, str) and item]
                if isinstance(excluded, list)
                else []
            )
            if excluded:
                tool_edit["exclude_tools"] = excluded
            edits.append(tool_edit)

        if not edits:
            return list(native_messages), state
        return list(native_messages), append_context_management_edits(
            state,
            edits,
            required_betas=[CONTEXT_EDITING_BETA],
        )

    def from_native_messages(
        self,
        native_messages: list[dict[str, Any]],
        messages: list[dict[str, Any]],
        state: dict[str, Any] | None = None,
        *,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if len(native_messages) != len(messages):
            return list(messages)
        output: list[dict[str, Any]] = []
        for native, message in zip(native_messages, messages):
            summary = _applied_edit_summary(native)
            if summary["applied_edit_count"] == 0:
                output.append(dict(message))
                continue
            status_parts = []
            if summary["cleared_thinking_turns"]:
                status_parts.append(
                    f"{summary['cleared_thinking_turns']} thinking turns"
                )
            if summary["cleared_tool_uses"]:
                status_parts.append(f"{summary['cleared_tool_uses']} tool uses")
            if summary["cleared_input_tokens"]:
                status_parts.append(f"{summary['cleared_input_tokens']:,} input tokens")
            metadata = {
                **dict(message.get("metadata") or {}),
                "anthropic_context_editing": summary,
                "anthropic_context_editing_status": (
                    "Context edited: " + ", ".join(status_parts)
                    if status_parts
                    else "Context edited"
                ),
            }
            output.append({**message, "metadata": metadata})
        return output


__all__ = ["AnthropicContextEditingExtension"]
