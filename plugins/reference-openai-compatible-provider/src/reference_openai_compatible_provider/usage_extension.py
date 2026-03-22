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


def _usage_cached_tokens(usage: dict[str, Any]) -> int | None:
    details = usage.get("prompt_tokens_details")
    if not isinstance(details, dict):
        return None
    return _as_int(details.get("cached_tokens"))


def _usage_cost(usage: dict[str, Any]) -> float | None:
    for value in (
        usage.get("cost"),
        (usage.get("cost_details") or {}).get("upstream_inference_cost"),
    ):
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            return float(value)
    return None


def _format_cost(value: float | None) -> str | None:
    if not isinstance(value, (int, float)):
        return None
    return f"${float(value):.6f}"


def _message_usage(native_message: dict[str, Any]) -> dict[str, Any] | None:
    internal_md = native_message.get("_metadata")
    if not isinstance(internal_md, dict):
        return None
    usage = internal_md.get("usage")
    return usage if isinstance(usage, dict) else None


def _message_has_tool_calls(native_message: dict[str, Any]) -> bool:
    tool_calls = native_message.get("tool_calls")
    return isinstance(tool_calls, list) and bool(tool_calls)


def _last_turn_separator_index(
    native_messages: list[dict[str, Any]], current_index: int
) -> int:
    separator_index = -1
    for index, native_message in enumerate(native_messages[:current_index]):
        if not isinstance(native_message, dict):
            continue
        role = native_message.get("role")
        if role in ("user", "system"):
            separator_index = index
            continue
        if role == "assistant" and not _message_has_tool_calls(native_message):
            separator_index = index
    return separator_index


def _sum_assistant_metric(
    native_messages: list[dict[str, Any]],
    end_index: int,
    metric,
    *,
    start_index: int = 0,
) -> Any:
    total = 0
    found = False
    for native_message in native_messages[start_index : end_index + 1]:
        if not isinstance(native_message, dict):
            continue
        if native_message.get("role") != "assistant":
            continue
        usage = _message_usage(native_message)
        if not isinstance(usage, dict):
            continue
        value = metric(usage)
        if value is None:
            continue
        total += value
        found = True
    return total if found else None


def _normalized_usage_metadata(usage: dict[str, Any]) -> dict[str, Any]:
    prompt_tokens = _as_int(usage.get("prompt_tokens"))
    completion_tokens = _as_int(usage.get("completion_tokens"))
    total_tokens = _as_int(usage.get("total_tokens"))
    cached_tokens = _usage_cached_tokens(usage)
    reasoning_tokens = _usage_reasoning_tokens(usage)
    total_cost = _usage_cost(usage)

    metadata: dict[str, Any] = {"usage": usage}
    if prompt_tokens is not None:
        metadata["usage_prompt_tokens"] = prompt_tokens
        metadata["usage_prompt_tokens_formatted"] = _format_token_count(prompt_tokens)
    if cached_tokens is not None:
        metadata["usage_cached_tokens"] = cached_tokens
        metadata["usage_cached_tokens_formatted"] = _format_token_count(cached_tokens)
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
    if total_cost is not None:
        metadata["usage_total_cost"] = total_cost
        metadata["usage_total_cost_formatted"] = _format_cost(total_cost)
    return metadata


def _usage_metadata_for_native_message(
    native_messages: list[dict[str, Any]],
    index: int,
) -> dict[str, Any]:
    if index < 0 or index >= len(native_messages):
        return {}
    native_message = native_messages[index]
    if not isinstance(native_message, dict):
        return {}

    usage = _message_usage(native_message)
    if not isinstance(usage, dict):
        return {}

    metadata = _normalized_usage_metadata(usage)
    current_cost = _usage_cost(usage)
    separator_index = _last_turn_separator_index(native_messages, index)
    has_tool_calls = _message_has_tool_calls(native_message)

    cumulative_cost = _sum_assistant_metric(native_messages, index, _usage_cost)
    if cumulative_cost is not None:
        metadata["usage_total_cost_cumulative"] = cumulative_cost
        metadata["usage_total_cost_cumulative_formatted"] = _format_cost(
            cumulative_cost
        )

    if current_cost is not None and not has_tool_calls:
        turn_cost = _sum_assistant_metric(
            native_messages,
            index,
            _usage_cost,
            start_index=separator_index + 1,
        )
        if turn_cost is not None:
            metadata["usage_turn_cost_cumulative"] = turn_cost
            metadata["usage_turn_cost_cumulative_formatted"] = _format_cost(turn_cost)

    if not has_tool_calls:
        turn_reasoning = _sum_assistant_metric(
            native_messages,
            index,
            _usage_reasoning_tokens,
            start_index=separator_index + 1,
        )
        if turn_reasoning is not None:
            metadata["usage_turn_reasoning_tokens_cumulative"] = turn_reasoning
            metadata["usage_turn_reasoning_tokens_cumulative_formatted"] = (
                _format_token_count(turn_reasoning)
            )

    return metadata


class OpenAICompatibleUsageExtension(ProviderExtensionPlugin):
    name = "reference_openai_usage"
    version = "0.1.0"

    def required_tags(self) -> list[str]:
        return ["provider:openai_compatible"]

    def get_config_schema(self) -> dict[str, Any]:
        return {"show_usage": {"type": "boolean", "default": True}}

    def get_ui_elements(
        self,
        config: dict[str, Any],
        tags: list[str],
        models: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        if config.get("show_usage") is False:
            return []
        return [
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_prompt_tokens_formatted",
                "template": "input: {{data}}",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_cached_tokens_formatted",
                "template": "cached: {{data}}",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_completion_tokens_formatted",
                "template": "completion: {{data}}",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_total_cost_formatted",
                "template": "cost: {{data}}",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_turn_cost_cumulative_formatted",
                "template": "turn: {{data}}",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_turn_reasoning_tokens_cumulative_formatted",
                "template": "reasoning: {{data}}",
            },
            {
                "ui_type": "status_bar",
                "data": "metadata.usage_total_cost_cumulative_formatted",
                "template": "Total: {{data}}",
            },
        ]

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
            for index, msg in enumerate(messages):
                metadata = dict(msg.get("metadata") or {})
                metadata |= _usage_metadata_for_native_message(native_messages, index)
                out.append({**msg, "metadata": metadata})
            return out

        if not native_messages or not messages:
            return messages

        trailing_metadata = _usage_metadata_for_native_message(
            native_messages, len(native_messages) - 1
        )
        if not trailing_metadata:
            return messages

        out = list(messages)
        last_message = dict(out[-1])
        metadata = dict(last_message.get("metadata") or {})
        metadata |= trailing_metadata
        out[-1] = {**last_message, "metadata": metadata}
        return out
