"""Anthropic token usage formatting and cumulative accounting."""

from __future__ import annotations

from typing import Any

from agent_core.types import ProviderExtensionPlugin


def _integer(value: Any) -> int:
    return value if isinstance(value, int) and value >= 0 else 0


def _format_tokens(value: int) -> str:
    return f"{value:,}"


def _normalized_usage(raw: dict[str, Any]) -> dict[str, int]:
    details = raw.get("output_tokens_details")
    details = details if isinstance(details, dict) else {}
    input_tokens = _integer(raw.get("input_tokens"))
    output_tokens = _integer(raw.get("output_tokens"))
    return {
        "input": input_tokens,
        "output": output_tokens,
        "total": input_tokens + output_tokens,
        "cached": _integer(raw.get("cache_read_input_tokens")),
        "cache_write": _integer(raw.get("cache_creation_input_tokens")),
        "reasoning": _integer(details.get("thinking_tokens")),
    }


def _message_usage(native: dict[str, Any]) -> dict[str, int]:
    metadata = native.get("_metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    raw = metadata.get("anthropic_usage")
    return _normalized_usage(raw if isinstance(raw, dict) else {})


def _usage_metadata(
    usage: dict[str, int],
    *,
    turn: dict[str, int],
    session: dict[str, int],
) -> dict[str, Any]:
    return {
        "usage_prompt_tokens": usage["input"],
        "usage_prompt_tokens_formatted": _format_tokens(usage["input"]),
        "usage_completion_tokens": usage["output"],
        "usage_completion_tokens_formatted": _format_tokens(usage["output"]),
        "usage_total_tokens": usage["total"],
        "usage_total_tokens_formatted": _format_tokens(usage["total"]),
        "usage_cached_tokens": usage["cached"],
        "usage_cached_tokens_formatted": _format_tokens(usage["cached"]),
        "usage_cache_write_tokens": usage["cache_write"],
        "usage_cache_write_tokens_formatted": _format_tokens(usage["cache_write"]),
        "usage_reasoning_tokens": usage["reasoning"],
        "usage_reasoning_tokens_formatted": _format_tokens(usage["reasoning"]),
        "usage_turn_input_tokens_cumulative": turn["input"],
        "usage_turn_input_tokens_cumulative_formatted": _format_tokens(turn["input"]),
        "usage_turn_output_tokens_cumulative": turn["output"],
        "usage_turn_output_tokens_cumulative_formatted": _format_tokens(turn["output"]),
        "usage_turn_cached_tokens_cumulative": turn["cached"],
        "usage_turn_cached_tokens_cumulative_formatted": _format_tokens(turn["cached"]),
        "usage_turn_cache_write_tokens_cumulative": turn["cache_write"],
        "usage_turn_cache_write_tokens_cumulative_formatted": _format_tokens(
            turn["cache_write"]
        ),
        "usage_turn_reasoning_tokens_cumulative": turn["reasoning"],
        "usage_turn_reasoning_tokens_cumulative_formatted": _format_tokens(
            turn["reasoning"]
        ),
        "usage_input_tokens_cumulative": session["input"],
        "usage_output_tokens_cumulative": session["output"],
        "usage_total_tokens_cumulative": session["total"],
        "usage_cached_tokens_cumulative": session["cached"],
        "usage_cache_write_tokens_cumulative": session["cache_write"],
        "usage_reasoning_tokens_cumulative": session["reasoning"],
    }


def _sum_usage(messages: list[dict[str, Any]]) -> dict[str, int]:
    total = {
        "input": 0,
        "output": 0,
        "total": 0,
        "cached": 0,
        "cache_write": 0,
        "reasoning": 0,
    }
    for message in messages:
        usage = _message_usage(message)
        total = {key: total[key] + usage[key] for key in total}
    return total


def _turn_messages(messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
    boundary = 0
    for index, message in enumerate(messages):
        metadata = message.get("_metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        if message.get("role") == "user" and metadata.get("core_role") != "tool":
            boundary = index
    return messages[boundary:]


def _current_turn_id(messages: list[dict[str, Any]]) -> int:
    turn_id = 0
    for message in messages:
        metadata = message.get("_metadata")
        metadata = metadata if isinstance(metadata, dict) else {}
        if message.get("role") == "user" and metadata.get("core_role") != "tool":
            turn_id += 1
    return max(turn_id, 1)


def _has_tool_calls(message: dict[str, Any]) -> bool:
    metadata = message.get("_metadata")
    metadata = metadata if isinstance(metadata, dict) else {}
    calls = metadata.get("tool_calls")
    if isinstance(calls, list) and calls:
        return True
    content = message.get("content")
    return isinstance(content, list) and any(
        isinstance(block, dict) and block.get("type") == "tool_use" for block in content
    )


class AnthropicUsageExtension(ProviderExtensionPlugin):
    name = "anthropic_usage"
    version = "0.1.0"
    priority = 80

    def required_tags(self) -> list[str]:
        return ["provider:anthropic", "supports_usage"]

    def get_config_schema(self) -> dict[str, Any]:
        return {"show_usage": {"type": "boolean", "default": True}}

    def get_ui_elements(
        self,
        config: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        if not bool(config.get("show_usage", True)):
            return []
        return [
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_prompt_tokens_formatted",
                "template": "In: {{data}}",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_cached_tokens_formatted",
                "template": "Cached: {{data}}",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_cache_write_tokens_formatted",
                "template": "Cache write: {{data}}",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_completion_tokens_formatted",
                "template": "Out: {{data}}",
            },
        ]

    def init(self, config: dict[str, Any], state: dict[str, Any]) -> dict[str, Any]:
        return {
            **state,
            "anthropic_usage": {
                "show": bool(config.get("show_usage", True)),
                "raw": {},
            },
        }

    def process_chunk(
        self,
        native_chunk: dict[str, Any] | None,
        partial_messages: list[dict[str, Any]],
        final_messages: list[dict[str, Any]],
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ):
        event = native_chunk or {}
        raw = event.get("usage")
        if event.get("type") == "message_start":
            message = event.get("message")
            raw = message.get("usage") if isinstance(message, dict) else raw
        usage_state = dict(state.get("anthropic_usage") or {})
        if isinstance(raw, dict):
            usage_state["raw"] = {**dict(usage_state.get("raw") or {}), **raw}
        return (
            list(partial_messages),
            list(final_messages),
            list(native_messages),
            {**state, "anthropic_usage": usage_state},
        )

    def finalize(
        self,
        final_messages: list[dict[str, Any]],
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
        *,
        context: dict[str, Any] | None = None,
    ):
        if not final_messages:
            return list(final_messages), list(native_messages), state
        raw = dict((state.get("anthropic_usage") or {}).get("raw") or {})
        if not raw:
            metadata = final_messages[-1].get("_metadata")
            metadata = metadata if isinstance(metadata, dict) else {}
            raw_value = metadata.get("anthropic_usage")
            raw = dict(raw_value) if isinstance(raw_value, dict) else {}
        current_usage = _normalized_usage(raw)
        provisional = list(native_messages)
        final_count = len(final_messages)
        prefix = provisional[:-final_count] if final_count <= len(provisional) else []
        session = _sum_usage([*prefix, *final_messages])
        turn = _sum_usage(_turn_messages([*prefix, *final_messages]))
        public = _usage_metadata(current_usage, turn=turn, session=session)
        turn_id = _current_turn_id([*prefix, *final_messages])

        updated_finals: list[dict[str, Any]] = []
        for message in final_messages:
            has_tool_calls = _has_tool_calls(message)
            metadata = {
                **dict(message.get("_metadata") or {}),
                "anthropic_usage": raw,
                **public,
                "turn": {
                    "id": turn_id,
                    "has_tool_calls": has_tool_calls,
                    "is_terminal": not has_tool_calls,
                },
            }
            updated_finals.append({**message, "_metadata": metadata})
        updated_history = [*prefix, *updated_finals]
        return (
            updated_finals,
            updated_history,
            {
                **state,
                "anthropic_usage": {
                    **dict(state.get("anthropic_usage") or {}),
                    "raw": raw,
                },
            },
        )
