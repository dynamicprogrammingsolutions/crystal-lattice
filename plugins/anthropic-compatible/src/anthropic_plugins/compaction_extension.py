"""Anthropic automatic native compaction extension."""

from __future__ import annotations

from typing import Any

from agent_core.types import ProviderExtensionPlugin

from .context_management import (
    COMPACTION_BETA,
    append_context_management_edits,
)


def _compaction_blocks(native: dict[str, Any]) -> list[dict[str, Any]]:
    content = native.get("content")
    if not isinstance(content, list):
        return []
    return [
        dict(block)
        for block in content
        if isinstance(block, dict) and block.get("type") == "compaction"
    ]


def _integer_at_least(value: Any, *, default: int, minimum: int) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        return default
    if value < minimum:
        raise ValueError(f"value must be at least {minimum}")
    return value


class AnthropicCompactionExtension(ProviderExtensionPlugin):
    name = "anthropic_compaction"
    version = "0.1.0"
    priority = 65

    def required_tags(self) -> list[str]:
        return ["provider:anthropic", "supports_anthropic_compaction"]

    def get_tags(
        self,
        config: dict[str, Any],
        models: list[dict[str, Any]],
    ) -> list[str]:
        return ["ext:anthropic_compaction"]

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "enable_anthropic_compaction": {
                "type": "boolean",
                "default": False,
            },
            "anthropic_compaction_trigger_tokens": {
                "type": "integer",
                "default": 150000,
                "minimum": 50000,
            },
            "anthropic_compaction_instructions": {
                "type": "string",
                "required": False,
            },
        }

    def get_ui_elements(
        self,
        config: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return [
            {
                "type": "checkbox",
                "key": "enable_anthropic_compaction",
                "label": "Enable Anthropic compaction",
                "default": bool(config.get("enable_anthropic_compaction", False)),
            },
            {
                "type": "number",
                "key": "anthropic_compaction_trigger_tokens",
                "label": "Anthropic compaction trigger tokens",
                "default": _integer_at_least(
                    config.get("anthropic_compaction_trigger_tokens"),
                    default=150000,
                    minimum=50000,
                ),
                "minimum": 50000,
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.anthropic_compaction_status",
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
        if not bool(config.get("enable_anthropic_compaction", False)):
            return list(native_messages), state
        trigger = _integer_at_least(
            config.get("anthropic_compaction_trigger_tokens"),
            default=150000,
            minimum=50000,
        )
        edit: dict[str, Any] = {
            "type": "compact_20260112",
            "trigger": {"type": "input_tokens", "value": trigger},
            "pause_after_compaction": False,
        }
        instructions = config.get("anthropic_compaction_instructions")
        if isinstance(instructions, str) and instructions.strip():
            edit["instructions"] = instructions.strip()
        return list(native_messages), append_context_management_edits(
            state,
            [edit],
            required_betas=[COMPACTION_BETA],
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
            blocks = _compaction_blocks(native)
            if not blocks:
                output.append(dict(message))
                continue
            readable = sum(
                isinstance(block.get("content"), str)
                and bool(str(block.get("content") or "").strip())
                for block in blocks
            )
            metadata = {
                **dict(message.get("metadata") or {}),
                "anthropic_compaction": {
                    "occurred": True,
                    "block_count": len(blocks),
                    "readable_summary_count": readable,
                },
                "anthropic_compaction_status": (
                    "Context compacted"
                    if len(blocks) == 1
                    else f"Context compacted {len(blocks)} times"
                ),
            }
            output.append({**message, "metadata": metadata})
        return output


__all__ = ["AnthropicCompactionExtension"]
