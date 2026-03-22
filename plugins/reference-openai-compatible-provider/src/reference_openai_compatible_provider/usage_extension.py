from __future__ import annotations

from typing import Any

from agent_core.types import ProviderExtensionPlugin


def _format_token_count(value: int | None) -> str | None:
    if not isinstance(value, int):
        return None
    return f"{value:,}"


def _as_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return int(value)
    return None


def _usage_reasoning_tokens(usage: dict[str, Any]) -> int | None:
    for key in ("completion_tokens_details", "output_tokens_details"):
        details = usage.get(key)
        if not isinstance(details, dict):
            continue
        value = _as_int(details.get("reasoning_tokens"))
        if value is not None:
            return value
    return None


def _normalized_usage_metadata(usage: dict[str, Any]) -> dict[str, Any]:
    prompt_tokens = _as_int(usage.get("prompt_tokens"))
    completion_tokens = _as_int(usage.get("completion_tokens"))
    total_tokens = _as_int(usage.get("total_tokens"))
    reasoning_tokens = _usage_reasoning_tokens(usage)

    metadata: dict[str, Any] = {"usage": usage}
    if prompt_tokens is not None:
        metadata["usage_prompt_tokens"] = prompt_tokens
        metadata["usage_prompt_tokens_formatted"] = _format_token_count(prompt_tokens)
    if completion_tokens is not None:
        metadata["usage_completion_tokens"] = completion_tokens
        metadata["usage_completion_tokens_formatted"] = _format_token_count(
            completion_tokens
        )
    if total_tokens is not None:
        metadata["usage_total_tokens"] = total_tokens
        metadata["usage_total_tokens_formatted"] = _format_token_count(total_tokens)
    if reasoning_tokens is not None:
        metadata["usage_reasoning_tokens"] = reasoning_tokens
        metadata["usage_reasoning_tokens_formatted"] = _format_token_count(
            reasoning_tokens
        )
    return metadata


class OpenAICompatibleUsageExtension(ProviderExtensionPlugin):
    name = "reference_openai_usage"
    version = "0.1.0"

    def required_tags(self) -> list[str]:
        return ["provider:openai_compatible"]

    def get_tags(
        self,
        config: dict[str, Any],
        models: list[dict[str, Any]],
    ) -> list[str]:
        return ["ext:reference_openai_usage"]

    def process_chunk(
        self,
        native_chunk: dict[str, Any] | None,
        partial_messages: list[dict[str, Any]],
        final_messages: list[dict[str, Any]],
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ):
        usage = (native_chunk or {}).get("usage")
        if not isinstance(usage, dict):
            return partial_messages, final_messages, native_messages, state

        partial = state.get("partial")
        partial_dict = dict(partial) if isinstance(partial, dict) else {}
        internal_md = partial_dict.get("_metadata")
        base_internal_md = internal_md if isinstance(internal_md, dict) else {}
        partial_dict["_metadata"] = {**base_internal_md, "usage": usage}

        return (
            partial_messages,
            final_messages,
            native_messages,
            {**state, "partial": partial_dict},
        )

    def from_native_messages(
        self, native_messages: list[dict[str, Any]], messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        if len(messages) == len(native_messages):
            out: list[dict[str, Any]] = []
            for msg, native_msg in zip(messages, native_messages):
                metadata = dict(msg.get("metadata") or {})
                internal_md = native_msg.get("_metadata")
                if isinstance(internal_md, dict) and isinstance(
                    internal_md.get("usage"), dict
                ):
                    metadata |= _normalized_usage_metadata(internal_md["usage"])
                out.append({**msg, "metadata": metadata})
            return out

        if not native_messages or not messages:
            return messages

        native_last = (
            native_messages[-1] if isinstance(native_messages[-1], dict) else {}
        )
        internal_md = native_last.get("_metadata")
        usage = internal_md.get("usage") if isinstance(internal_md, dict) else None
        if not isinstance(usage, dict):
            return messages

        out = list(messages)
        last_message = dict(out[-1])
        metadata = dict(last_message.get("metadata") or {})
        metadata |= _normalized_usage_metadata(usage)
        out[-1] = {**last_message, "metadata": metadata}
        return out
