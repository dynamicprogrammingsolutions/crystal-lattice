from __future__ import annotations

from typing import Any

from agent_core.types import ProviderExtensionPlugin

from reference_openai_compatible_provider._extension_accumulator import (
    AccumulatorExtensionMixin,
    _merge_delta_content,
)

_REASONING_TEXT_FIELDS = ("reasoning", "reasoning_content")
_PATCH_REASONING_PRIORITY = ("reasoning", "reasoning_content")


def _has_reasoning_payload(value: Any) -> bool:
    if isinstance(value, str):
        return bool(value)
    return value is not None


def _get_reasoning_fields(state: dict[str, Any]) -> tuple[str, ...]:
    """Return reasoning fields based on config or defaults.

    If `reasoning_field` is set in state, use only that field.
    Otherwise, use all supported reasoning fields.
    """
    reasoning_field = state.get("reasoning_field")
    if isinstance(reasoning_field, str) and reasoning_field:
        return (reasoning_field,)
    return _REASONING_TEXT_FIELDS


def _reasoning_metadata_from_native(
    native_message: dict[str, Any], state: dict[str, Any]
) -> dict[str, Any]:
    """Extract reasoning metadata from native message based on configured fields."""
    metadata: dict[str, Any] = {}
    generic_reasoning: str | None = None
    fields = _get_reasoning_fields(state)
    for key in fields:
        value = native_message.get(key)
        if isinstance(value, str) and value:
            metadata[key] = value
            if generic_reasoning is None:
                generic_reasoning = value

    if isinstance(generic_reasoning, str) and generic_reasoning:
        metadata["reasoning"] = generic_reasoning

    return metadata


class OpenAICompatibleReasoningExtension(
    AccumulatorExtensionMixin, ProviderExtensionPlugin
):
    name = "reference_openai_reasoning"
    version = "0.2.0"

    def required_tags(self) -> list[str]:
        return ["provider:openai_compatible"]

    def get_config_schema(self) -> dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        config: dict[str, Any],
        tags: list[str],
        models: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        return []

    def init(self, config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        """Store reasoning_field from config in state for use by other methods."""
        reasoning_field = config.get("reasoning_field")
        if isinstance(reasoning_field, str) and reasoning_field:
            return {**state, "reasoning_field": reasoning_field}
        return state

    def extract_delta(self, native_chunk: dict[str, Any]) -> dict[str, Any]:
        choice0 = (native_chunk.get("choices") or [{}])[0]
        return choice0 if isinstance(choice0, dict) else {}

    def process_delta(
        self, delta: dict[str, Any], accumulated: dict[str, Any] | None, state: dict[str, Any] | None = None
    ):
        base = accumulated or {}
        payload = delta.get("delta") or delta.get("message") or {}
        if not isinstance(payload, dict):
            return None, base

        fields = _get_reasoning_fields(state or {})
        new_acc = dict(base)
        patch_fragments: dict[str, str] = {}

        for key in fields:
            frag = payload.get(key)
            if not isinstance(frag, str) or not frag:
                continue
            new_acc = _merge_delta_content(new_acc, {key: frag}, accumulate=(key,))
            patch_fragments[key] = frag

        # Determine patch priority: use configured field first, then default priority
        reasoning_field = (state or {}).get("reasoning_field")
        if isinstance(reasoning_field, str) and reasoning_field:
            # When a custom field is configured, use it for the patch
            patch_reasoning = patch_fragments.get(reasoning_field, "")
        else:
            # Default behavior: use priority order
            patch_reasoning = next(
                (patch_fragments[key] for key in _PATCH_REASONING_PRIORITY if key in patch_fragments),
                "",
            )

        if not patch_reasoning:
            return None, base

        return {"reasoning": patch_reasoning}, new_acc

    def process_chunk(
        self,
        native_chunk: dict[str, Any] | None,
        partial_messages: list[dict[str, Any]],
        final_messages: list[dict[str, Any]],
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ):
        delta = self.extract_delta(native_chunk or {})
        accumulated = (
            state.get("partial") if isinstance(state.get("partial"), dict) else {}
        )
        patch, new_acc = self.process_delta(delta, accumulated, state)

        new_partials = partial_messages
        if isinstance(patch, dict) and patch:
            if partial_messages:
                new_partials = [*partial_messages[:-1], {**partial_messages[-1], **patch}]

        return (
            new_partials,
            final_messages,
            list(native_messages),
            {**state, "partial": new_acc},
        )

    def to_native_messages(
        self, messages: list[dict[str, Any]], native_messages: list[dict[str, Any]], state: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        if len(messages) != len(native_messages):
            return native_messages

        fields = _get_reasoning_fields(state or {})
        out: list[dict[str, Any]] = []
        for msg, native_msg in zip(messages, native_messages):
            enhanced_native = dict(native_msg)
            metadata = msg.get("metadata") or {}
            if msg.get("role") == "assistant" and isinstance(metadata, dict):
                for key in fields:
                    value = metadata.get(key)
                    if _has_reasoning_payload(value):
                        enhanced_native[key] = value
            out.append(enhanced_native)
        return out

    def from_native_messages(
        self, native_messages: list[dict[str, Any]], messages: list[dict[str, Any]], state: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        if len(messages) != len(native_messages):
            return messages

        return [
            {
                **msg,
                "metadata": {
                    **dict(msg.get("metadata") or {}),
                    **_reasoning_metadata_from_native(native_msg, state or {}),
                },
            }
            for msg, native_msg in zip(messages, native_messages)
        ]