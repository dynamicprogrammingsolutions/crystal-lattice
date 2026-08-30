"""Anthropic thinking configuration and metadata extension."""

from __future__ import annotations

from typing import Any

from agent_core.types import ProviderExtensionPlugin


EFFORT_LEVELS = ("low", "medium", "high", "xhigh", "max")


def _reasoning_blocks(native: dict[str, Any]) -> list[dict[str, Any]]:
    content = native.get("content")
    if not isinstance(content, list):
        return []
    return [
        dict(block)
        for block in content
        if isinstance(block, dict)
        and block.get("type") in {"thinking", "redacted_thinking"}
    ]


class AnthropicReasoningExtension(ProviderExtensionPlugin):
    name = "anthropic_reasoning"
    version = "0.1.0"
    priority = 50

    def required_tags(self) -> list[str]:
        return ["provider:anthropic", "supports_reasoning"]

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "enable_reasoning": {"type": "boolean", "default": False},
            "reasoning_effort": {
                "type": "string",
                "enum": list(EFFORT_LEVELS),
                "description": (
                    "Control response effort. Availability depends on the selected "
                    "Anthropic model."
                ),
            },
            "reasoning_budget_tokens": {"type": "integer", "default": 1024},
            "show_reasoning": {"type": "boolean", "default": True},
        }

    def get_ui_elements(
        self,
        config: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return [
            {
                "type": "checkbox",
                "key": "enable_reasoning",
                "label": "Reasoning",
            },
            {
                "type": "select",
                "key": "reasoning_effort",
                "label": "Reasoning effort",
                "options": [
                    {"value": level, "label": level} for level in EFFORT_LEVELS
                ],
                "description": "Available effort levels depend on the selected model.",
            },
            {
                "type": "checkbox",
                "key": "show_reasoning",
                "label": "Show reasoning",
            },
        ]

    def init(self, config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        effort = config.get("reasoning_effort")
        return {
            **state,
            "anthropic_reasoning": {
                "enabled": bool(config.get("enable_reasoning", False)),
                "effort": effort if effort in EFFORT_LEVELS else None,
                "budget_tokens": max(
                    1, int(config.get("reasoning_budget_tokens") or 1024)
                ),
                "show": bool(config.get("show_reasoning", True)),
            },
        }

    def initialize_request(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ):
        settings = dict(state.get("anthropic_reasoning") or {})
        if not settings.get("enabled"):
            request = dict(state.get("request") or {})
            payload = dict(request.get("payload") or {})
            payload["thinking"] = {"type": "disabled"}
            return list(native_messages), {
                **state,
                "request": {**request, "payload": payload},
            }
        request = dict(state.get("request") or {})
        payload = dict(request.get("payload") or {})
        payload["thinking"] = {
            "type": "enabled",
            "budget_tokens": int(settings.get("budget_tokens") or 1024),
        }
        effort = settings.get("effort")
        if effort in EFFORT_LEVELS:
            payload["output_config"] = {"effort": effort}
        return list(native_messages), {
            **state,
            "request": {**request, "payload": payload},
        }

    def to_native_messages(
        self,
        messages: list[dict[str, Any]],
        native_messages: list[dict[str, Any]],
        state: dict[str, Any] | None = None,
        *,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if len(messages) != len(native_messages):
            return list(native_messages)
        output: list[dict[str, Any]] = []
        for message, native in zip(messages, native_messages):
            metadata = dict(message.get("metadata") or {})
            blocks = metadata.get("anthropic_reasoning_blocks")
            if (
                message.get("role") == "assistant"
                and isinstance(blocks, list)
                and isinstance(native.get("content"), str)
            ):
                text = native.get("content")
                native = {
                    **native,
                    "content": [
                        *[dict(block) for block in blocks if isinstance(block, dict)],
                        *(
                            [{"type": "text", "text": text}]
                            if isinstance(text, str) and text
                            else []
                        ),
                    ],
                }
            output.append(dict(native))
        return output

    def from_native_messages(
        self,
        native_messages: list[dict[str, Any]],
        messages: list[dict[str, Any]],
        state: dict[str, Any] | None = None,
        *,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if len(messages) != len(native_messages):
            return list(messages)
        output: list[dict[str, Any]] = []
        show_reasoning = bool(
            (state or {}).get("anthropic_reasoning", {}).get("show", True)
        )
        for native, message in zip(native_messages, messages):
            blocks = _reasoning_blocks(native)
            if not blocks:
                output.append(dict(message))
                continue
            reasoning = "\n".join(
                str(block.get("thinking") or "")
                for block in blocks
                if block.get("type") == "thinking"
            )
            metadata = {
                **dict(message.get("metadata") or {}),
                "anthropic_reasoning_blocks": blocks,
            }
            if reasoning and show_reasoning:
                metadata["reasoning"] = reasoning
            output.append({**message, "metadata": metadata})
        return output

    def process_chunk(
        self,
        native_chunk: dict[str, Any] | None,
        partial_messages: list[dict[str, Any]],
        final_messages: list[dict[str, Any]],
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ):
        event = native_chunk or {}
        delta = event.get("delta")
        if (
            event.get("type") != "content_block_delta"
            or not isinstance(delta, dict)
            or delta.get("type") != "thinking_delta"
            or not partial_messages
        ):
            return (
                list(partial_messages),
                list(final_messages),
                list(native_messages),
                state,
            )
        thinking = delta.get("thinking")
        if not isinstance(thinking, str) or not thinking:
            return (
                list(partial_messages),
                list(final_messages),
                list(native_messages),
                state,
            )
        if not bool((state.get("anthropic_reasoning") or {}).get("show", True)):
            return (
                list(partial_messages),
                list(final_messages),
                list(native_messages),
                state,
            )
        patched = [
            *partial_messages[:-1],
            {
                **partial_messages[-1],
                "_metadata": {
                    **dict(partial_messages[-1].get("_metadata") or {}),
                    "reasoning": thinking,
                },
            },
        ]
        return patched, list(final_messages), list(native_messages), state
