"""Anthropic thinking metadata and native-history extension."""

from __future__ import annotations

from typing import Any

from agent_core.types import ProviderExtensionPlugin


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
        return {}

    def get_ui_elements(
        self,
        config: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return []

    def init(self, config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        return state

    def initialize_request(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ):
        return list(native_messages), state

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
            if reasoning:
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
