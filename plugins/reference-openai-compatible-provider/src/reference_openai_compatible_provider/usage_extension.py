from __future__ import annotations

from typing import Any

from agent_core.types import ProviderExtensionPlugin

from .cost_bucket import resolve_cost_bucket


def _format_token_count(value: int | None) -> str | None:
    if not isinstance(value, int):
        return None
    return f"{value:,}"


def _current_turn_id(native_messages: list[dict[str, Any]]) -> int:
    last_assigned = 0
    max_seen_turn_id = 0
    current_open: int | None = None

    for native_message in native_messages:
        if not isinstance(native_message, dict):
            continue
        role = native_message.get("role")
        if role in ("user", "system"):
            current_open = None
            continue

        # Track max existing turn ID from prior metadata so that truncated
        # or rebuilt history cannot produce overlapping turn IDs.
        turn_md = native_message.get("_metadata", {}).get("turn")
        if isinstance(turn_md, dict):
            tid = _as_int(turn_md.get("id"))
            if tid is not None and tid > max_seen_turn_id:
                max_seen_turn_id = tid

        usage = _message_usage(native_message)
        if not isinstance(usage, dict):
            continue

        # If this message already has a turn ID, use it for state tracking
        # instead of computing a new one. This preserves open/closed turn
        # state from prior finalizations and prevents double-counting.
        existing_turn_id = (
            _as_int(turn_md.get("id")) if isinstance(turn_md, dict) else None
        )
        if existing_turn_id is not None:
            if current_open is None:
                current_open = existing_turn_id
            last_assigned = max(last_assigned, existing_turn_id)
            if not _message_has_tool_calls(native_message):
                current_open = None
        else:
            if current_open is None:
                current_open = max(last_assigned, max_seen_turn_id) + 1
            last_assigned = max(last_assigned, current_open)
            if not _message_has_tool_calls(native_message):
                current_open = None

    return (
        current_open
        if current_open is not None
        else (
            max(last_assigned, max_seen_turn_id) + 1
            if max(last_assigned, max_seen_turn_id) > 0
            else 1
        )
    )


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


def _usage_input_tokens(usage: dict[str, Any]) -> int | None:
    return _as_int(usage.get("prompt_tokens"))


def _usage_output_tokens(usage: dict[str, Any]) -> int | None:
    return _as_int(usage.get("completion_tokens"))


def _provider_usage_cost(usage: dict[str, Any]) -> float | None:
    for value in (
        usage.get("cost"),
        (usage.get("cost_details") or {}).get("upstream_inference_cost"),
    ):
        if isinstance(value, bool):
            continue
        if isinstance(value, (int, float)):
            return float(value)
    return None


def _clamp_cached_tokens(cached_tokens: int, prompt_tokens: int) -> int:
    return min(max(0, cached_tokens), max(0, prompt_tokens))


def _usage_cost(
    usage: dict[str, Any],
    token_rates: dict[str, Any] | None = None,
    *,
    cached_tokens_override: int | None = None,
) -> float | None:
    """Extract cost from usage or calculate from token_rates.

    Provider-returned cost takes precedence. If no provider cost and token_rates
    are configured, calculate cost from token counts and rates.

    Args:
        usage: Usage dict with token counts and optional cost.
        token_rates: Optional dict with 'input', 'cached', 'completion' rates
                     in USD per million tokens.

    Returns:
        Cost in USD, or None if not available.
    """
    provider_cost = _provider_usage_cost(usage)
    if provider_cost is not None:
        return provider_cost

    # No provider cost - try to calculate from token_rates
    if not isinstance(token_rates, dict):
        return None

    input_rate = token_rates.get("input")
    cached_rate = token_rates.get("cached")
    completion_rate = token_rates.get("completion")

    # Need at least input and completion rates to calculate
    if not isinstance(input_rate, (int, float)) or not isinstance(
        completion_rate, (int, float)
    ):
        return None

    prompt_tokens = _as_int(usage.get("prompt_tokens"))
    completion_tokens = _as_int(usage.get("completion_tokens"))

    if prompt_tokens is None or completion_tokens is None:
        return None

    cached_tokens = (
        cached_tokens_override
        if cached_tokens_override is not None
        else _usage_cached_tokens(usage)
    )
    effective_cached_tokens = (
        _clamp_cached_tokens(cached_tokens, prompt_tokens)
        if cached_tokens is not None
        else 0
    )
    ordinary_input_tokens = max(0, prompt_tokens) - effective_cached_tokens
    effective_cached_rate = (
        float(cached_rate)
        if isinstance(cached_rate, (int, float)) and not isinstance(cached_rate, bool)
        else float(input_rate)
    )

    # Rates are in USD per million tokens. Cached tokens fall back to the
    # ordinary input rate when no distinct cached rate is configured.
    return (
        ordinary_input_tokens * float(input_rate)
        + effective_cached_tokens * effective_cached_rate
        + max(0, completion_tokens) * float(completion_rate)
    ) / 1_000_000


def _calculate_cost_from_rates(
    usage: dict[str, Any],
    token_rates: dict[str, Any] | None,
    *,
    cached_tokens_override: int | None = None,
) -> float | None:
    """Calculate cost from token counts and configured rates.

    Kept as a separate helper for clarity. Rates are in USD per million tokens.

    Args:
        usage: Usage dict with token counts.
        token_rates: Dict with 'input', 'cached', 'completion' rates in $/M tokens.

    Returns:
        Cost in USD, or None if rates or token counts are incomplete.
    """
    return _usage_cost(
        usage,
        token_rates=token_rates,
        cached_tokens_override=cached_tokens_override,
    )


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


def _reduced_history_markers(
    native_messages: list[dict[str, Any]],
) -> list[tuple[str, int]]:
    """Reduce chat history to user boundaries and usage-bearing generations."""
    markers: list[tuple[str, int]] = []
    for native_message in native_messages:
        if not isinstance(native_message, dict):
            continue
        role = native_message.get("role")
        if role == "user":
            markers.append(("user", 0))
            continue
        if role != "assistant":
            continue
        usage = _message_usage(native_message)
        if not isinstance(usage, dict):
            continue
        prompt_tokens = _usage_input_tokens(usage)
        if prompt_tokens is not None:
            markers.append(("usage", max(0, prompt_tokens)))
    return markers


def _estimated_cached_tokens_from_markers(
    markers: list[tuple[str, int]],
) -> list[int]:
    estimates: list[int] = []
    previous_turn_first_usage_input: int | None = None
    previous_turn_last_usage_input: int | None = None
    current_turn_first_usage_input: int | None = None
    current_turn_last_usage_input: int | None = None

    for kind, prompt_tokens in markers:
        if kind == "user":
            if current_turn_first_usage_input is not None:
                previous_turn_first_usage_input = current_turn_first_usage_input
                previous_turn_last_usage_input = current_turn_last_usage_input
            current_turn_first_usage_input = None
            current_turn_last_usage_input = None
            continue

        if current_turn_last_usage_input is not None:
            estimated = (
                current_turn_last_usage_input
                if current_turn_last_usage_input <= prompt_tokens
                else 0
            )
        elif previous_turn_first_usage_input is not None:
            if (
                previous_turn_last_usage_input is not None
                and prompt_tokens > previous_turn_last_usage_input
            ):
                estimated = previous_turn_last_usage_input
            elif previous_turn_first_usage_input <= prompt_tokens:
                estimated = previous_turn_first_usage_input
            else:
                estimated = 0
        else:
            estimated = 0

        estimates.append(estimated)
        if current_turn_first_usage_input is None:
            current_turn_first_usage_input = prompt_tokens
        current_turn_last_usage_input = prompt_tokens

    return estimates


def _estimated_cached_tokens_for_current(
    base_native: list[dict[str, Any]],
    usage: dict[str, Any],
) -> int | None:
    prompt_tokens = _usage_input_tokens(usage)
    if prompt_tokens is None:
        return None
    markers = _reduced_history_markers(base_native)
    markers.append(("usage", max(0, prompt_tokens)))
    estimates = _estimated_cached_tokens_from_markers(markers)
    if not estimates:
        return None
    return estimates[-1]


def _estimated_cached_tokens_from_message(
    native_message: dict[str, Any],
) -> int | None:
    internal_md = native_message.get("_metadata")
    if not isinstance(internal_md, dict):
        return None
    return _as_int(internal_md.get("usage_estimated_cached_tokens"))


def _effective_cached_tokens_from_message(
    native_message: dict[str, Any],
) -> int | None:
    usage = _message_usage(native_message)
    if not isinstance(usage, dict):
        return None
    prompt_tokens = _usage_input_tokens(usage)
    if prompt_tokens is None:
        return None

    reported = _usage_cached_tokens(usage)
    if reported is not None:
        return _clamp_cached_tokens(reported, prompt_tokens)

    estimated = _estimated_cached_tokens_from_message(native_message)
    if estimated is not None:
        return _clamp_cached_tokens(estimated, prompt_tokens)
    return None


def _last_turn_separator_index(
    native_messages: list[dict[str, Any]], current_index: int
) -> int:
    """Find the index of the last 'separator' message before current_index.

    A separator is:
    - Any user or system message
    - Any assistant message without tool calls (final answer, not intermediate)

    The turn starts after the separator.
    """
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
    """Sum a metric across all assistant messages with usage in the range."""
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


def _sum_assistant_effective_cached_tokens(
    native_messages: list[dict[str, Any]],
    end_index: int,
    *,
    start_index: int = 0,
) -> int | None:
    total = 0
    found = False
    for native_message in native_messages[start_index : end_index + 1]:
        if (
            not isinstance(native_message, dict)
            or native_message.get("role") != "assistant"
        ):
            continue
        value = _effective_cached_tokens_from_message(native_message)
        if value is None:
            continue
        total += value
        found = True
    return total if found else None


def _native_indices_for_final_messages(
    native_messages: list[dict[str, Any]],
    final_messages: list[dict[str, Any]],
) -> list[int | None]:
    """Locate final messages in native history without assuming they are contiguous."""
    used: set[int] = set()
    resolved: list[int | None] = []

    for final_message in final_messages:
        match = next(
            (
                index
                for index, native_message in enumerate(native_messages)
                if index not in used and native_message is final_message
            ),
            None,
        )
        if match is None:
            match = next(
                (
                    index
                    for index, native_message in enumerate(native_messages)
                    if index not in used and native_message == final_message
                ),
                None,
            )
        if match is not None:
            used.add(match)
        resolved.append(match)

    return resolved


def _session_totals(native_messages: list[dict[str, Any]]) -> dict[str, Any]:
    """Calculate session-level totals from full native history.

    Returns dict with:
    - usage_total_cost_cumulative: total cost across all assistant messages
    - usage_total_cost_cumulative_formatted: formatted string
    """
    total_cost = _sum_assistant_metric(
        native_messages, len(native_messages) - 1, _usage_cost
    )

    result: dict[str, Any] = {}
    if total_cost is not None:
        result["usage_total_cost_cumulative"] = total_cost
        result["usage_total_cost_cumulative_formatted"] = _format_cost(total_cost)
    return result


def _turn_totals(
    native_messages: list[dict[str, Any]],
    final_messages: list[dict[str, Any]],
) -> dict[str, Any]:
    """Calculate turn-level totals from full native history.

    Returns dict with:
    - usage_turn_cost_cumulative: total cost in the current turn
    - usage_turn_cost_cumulative_formatted: formatted string
    - usage_turn_input_tokens_cumulative: total input tokens in turn
    - usage_turn_input_tokens_cumulative_formatted: formatted string
    - usage_turn_cached_tokens_cumulative: total cached tokens in turn
    - usage_turn_cached_tokens_cumulative_formatted: formatted string
    - usage_turn_output_tokens_cumulative: total output tokens in turn
    - usage_turn_output_tokens_cumulative_formatted: formatted string
    - usage_turn_reasoning_tokens_cumulative: total reasoning tokens in turn (if any)
    - usage_turn_reasoning_tokens_cumulative_formatted: formatted string
    """
    if not final_messages:
        return {}

    # Find the last assistant message in final_messages to determine turn boundaries
    # The turn includes all assistant messages after the last separator
    # We need to map final_messages back to native_messages indices

    # Get the end index in native_messages for the last final message
    end_index = len(native_messages) - 1

    # Find the separator (turn starts after this)
    separator_index = _last_turn_separator_index(native_messages, end_index)
    turn_start = separator_index + 1

    # Sum metrics for the turn (from turn_start to end_index)
    turn_cost = _sum_assistant_metric(
        native_messages, end_index, _usage_cost, start_index=turn_start
    )
    turn_input = _sum_assistant_metric(
        native_messages, end_index, _usage_input_tokens, start_index=turn_start
    )
    turn_cached = _sum_assistant_effective_cached_tokens(
        native_messages, end_index, start_index=turn_start
    )
    turn_output = _sum_assistant_metric(
        native_messages, end_index, _usage_output_tokens, start_index=turn_start
    )
    turn_reasoning = _sum_assistant_metric(
        native_messages, end_index, _usage_reasoning_tokens, start_index=turn_start
    )

    result: dict[str, Any] = {}

    if turn_cost is not None:
        result["usage_turn_cost_cumulative"] = turn_cost
        result["usage_turn_cost_cumulative_formatted"] = _format_cost(turn_cost)

    if turn_input is not None:
        result["usage_turn_input_tokens_cumulative"] = turn_input
        result["usage_turn_input_tokens_cumulative_formatted"] = _format_token_count(
            turn_input
        )

    if turn_cached is not None:
        result["usage_turn_cached_tokens_cumulative"] = turn_cached
        result["usage_turn_cached_tokens_cumulative_formatted"] = _format_token_count(
            turn_cached
        )

    if turn_output is not None:
        result["usage_turn_output_tokens_cumulative"] = turn_output
        result["usage_turn_output_tokens_cumulative_formatted"] = _format_token_count(
            turn_output
        )

    if turn_reasoning is not None:
        result["usage_turn_reasoning_tokens_cumulative"] = turn_reasoning
        result["usage_turn_reasoning_tokens_cumulative_formatted"] = (
            _format_token_count(turn_reasoning)
        )

    return result


def _per_message_metadata(usage: dict[str, Any]) -> dict[str, Any]:
    """Extract per-message usage metadata (non-cumulative)."""
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


class OpenAICompatibleUsageExtension(ProviderExtensionPlugin):
    name = "reference_openai_usage"
    version = "0.1.0"
    # Must run before the generic cost tracking extension (priority 70):
    # this extension stamps the provider-defined ``usage_bucket`` that cost
    # tracking records rows under. The wrapper default (100) would run it
    # too late, so cost tracking would see usage without a bucket.
    priority: int = 60

    def required_tags(self) -> list[str]:
        return ["provider:openai_compatible"]

    def get_config_schema(self) -> dict[str, Any]:
        return {
            "show_usage": {"type": "boolean", "default": True},
            "cost_bucket": {
                "type": "string",
                "required": False,
                "default": "openai-compatible",
                "description": (
                    "Base name of the provider-defined cost bucket used by the "
                    "generic cost tracking plugin. The provider appends a slug "
                    "of the endpoint URL host to form the final bucket."
                ),
            },
            "estimate_cached_tokens": {
                "type": "boolean",
                "default": False,
                "description": "Estimate cached tokens from prior usage-bearing generations when the provider omits prompt_tokens_details.cached_tokens.",
            },
            "show_estimated_cached_tokens": {
                "type": "boolean",
                "default": False,
                "description": "Show estimated cached tokens in message footers.",
            },
            "token_rates": {
                "type": "object",
                "required": False,
                "description": "Token pricing rates in USD per million tokens. Used to calculate cost when provider doesn't return it.",
                "properties": {
                    "input": {
                        "type": "number",
                        "description": "Rate per million input/prompt tokens (USD)",
                    },
                    "cached": {
                        "type": "number",
                        "description": "Rate per million cached tokens (USD) - typically discounted",
                    },
                    "completion": {
                        "type": "number",
                        "description": "Rate per million completion/output tokens (USD)",
                    },
                },
            },
        }

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
            *(
                [
                    {
                        "ui_type": "message_footer",
                        "data": "metadata.usage_estimated_cached_tokens_formatted",
                        "template": "estimated cached: {{data}}",
                        "condition": {
                            "path": "metadata.usage_estimated_cached_tokens_formatted",
                            "exists": True,
                        },
                    }
                ]
                if config.get("show_estimated_cached_tokens") is True
                else []
            ),
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
                "template": "turn reasoning: {{data}}",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_turn_input_tokens_cumulative_formatted",
                "template": "turn input: {{data}}",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_turn_cached_tokens_cumulative_formatted",
                "template": "turn cached: {{data}}",
            },
            {
                "ui_type": "message_footer",
                "data": "metadata.usage_turn_output_tokens_cumulative_formatted",
                "template": "turn output: {{data}}",
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

        accumulator = state.get("accumulator")
        accumulator_dict = dict(accumulator) if isinstance(accumulator, dict) else {}
        internal_md = accumulator_dict.get("_metadata")
        base_internal_md = internal_md if isinstance(internal_md, dict) else {}
        accumulator_dict["_metadata"] = {**base_internal_md, "usage": usage}

        return (
            partial_messages,
            final_messages,
            native_messages,
            {**state, "accumulator": accumulator_dict},
        )

    def finalize(
        self,
        final_messages: list[dict[str, Any]],
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
        """Calculate and inject all usage metadata.

        This method runs after the provider's finalize, when we have access to
        the FULL native_messages history. We calculate:

        1. Per-message usage (tokens, cost)
        2. Session total cost (cumulative across all messages)
        3. Turn totals (cost, input/cached/output tokens for current turn)
        4. Cost from token_rates if provider didn't return it

        All values are stored in _metadata so from_native_messages can read them.
        """
        if not final_messages:
            return final_messages, list(native_messages), state

        config = state.get("config") or {}
        token_rates = config.get("token_rates")
        estimate_cached_tokens = config.get("estimate_cached_tokens") is True
        usage_bucket = resolve_cost_bucket(config)

        final_native_indices = _native_indices_for_final_messages(
            native_messages, final_messages
        )
        matched_indices = [
            index for index in final_native_indices if isinstance(index, int)
        ]
        history_before_current = (
            native_messages[: min(matched_indices)]
            if matched_indices
            else (
                native_messages[: -len(final_messages)]
                if len(native_messages) >= len(final_messages)
                else []
            )
        )
        current_turn_id = _current_turn_id(history_before_current)
        provisional_native = list(native_messages)
        provisional_finals: list[dict[str, Any]] = []

        for final_position, msg in enumerate(final_messages):
            native_index = final_native_indices[final_position]
            estimation_history = (
                provisional_native[:native_index]
                if isinstance(native_index, int)
                else list(provisional_native)
            )
            if not isinstance(msg, dict):
                provisional_finals.append(msg)
                continue

            internal_md = msg.get("_metadata")
            if not isinstance(internal_md, dict):
                provisional_finals.append(msg)
                continue

            usage = internal_md.get("usage")
            if not isinstance(usage, dict):
                provisional_finals.append(msg)
                continue

            estimated_cached_tokens: int | None = None
            if estimate_cached_tokens and _usage_cached_tokens(usage) is None:
                estimated_cached_tokens = _estimated_cached_tokens_for_current(
                    estimation_history, usage
                )

            provider_cost = _provider_usage_cost(usage)
            if provider_cost is None and isinstance(token_rates, dict):
                calculated_cost = _calculate_cost_from_rates(
                    usage,
                    token_rates,
                    cached_tokens_override=estimated_cached_tokens,
                )
                if calculated_cost is not None:
                    usage = {**usage, "cost": calculated_cost}

            per_msg_metadata = _per_message_metadata(usage)
            provisional_metadata = {
                **per_msg_metadata,
                "usage_bucket": usage_bucket,
                "turn": {
                    "id": current_turn_id,
                    "has_tool_calls": _message_has_tool_calls(msg),
                    "is_terminal": not _message_has_tool_calls(msg),
                },
            }
            if estimated_cached_tokens is not None:
                provisional_metadata["usage_estimated_cached_tokens"] = (
                    estimated_cached_tokens
                )
                provisional_metadata["usage_estimated_cached_tokens_formatted"] = (
                    _format_token_count(estimated_cached_tokens)
                )

            provisional_msg = {
                **msg,
                "_metadata": {**internal_md, **provisional_metadata},
            }
            provisional_finals.append(provisional_msg)
            if isinstance(native_index, int):
                provisional_native[native_index] = provisional_msg
            else:
                provisional_native.append(provisional_msg)

        session_metadata = _session_totals(provisional_native)
        turn_metadata = _turn_totals(provisional_native, provisional_finals)

        cumulative_metadata = {
            "usage_bucket": usage_bucket,
            **session_metadata,
            **turn_metadata,
        }
        new_finals: list[dict[str, Any]] = []
        for msg in provisional_finals:
            if not isinstance(msg, dict):
                new_finals.append(msg)
                continue
            internal_md = msg.get("_metadata")
            if not isinstance(internal_md, dict):
                new_finals.append(msg)
                continue
            new_finals.append(
                {
                    **msg,
                    "_metadata": {**internal_md, **cumulative_metadata},
                }
            )

        new_native = list(provisional_native)
        for final_position, msg in enumerate(new_finals):
            native_index = final_native_indices[final_position]
            if isinstance(native_index, int):
                new_native[native_index] = msg
            elif msg not in new_native:
                new_native.append(msg)
        return new_finals, new_native, state

    def from_native_messages(
        self, native_messages: list[dict[str, Any]], messages: list[dict[str, Any]]
    ) -> list[dict[str, Any]]:
        """Convert native messages to core messages with usage metadata.

        This method handles two scenarios:
        1. Normal flow: receives only new messages, reads pre-computed metadata from _metadata
        2. Rebuild flow: receives full history, computes metadata on-the-fly

        Also handles length mismatches where native_messages may be longer than messages.
        """
        if not native_messages or not messages:
            return messages

        # Check if this looks like a rebuild (full history with metadata already computed)
        # vs normal flow (new messages that went through finalize)
        has_precomputed_metadata = False
        first_with_metadata = next(
            (m for m in native_messages if isinstance(m.get("_metadata"), dict)), None
        )
        if first_with_metadata:
            internal_md = first_with_metadata["_metadata"]
            # If usage_prompt_tokens exists in _metadata, finalize already ran
            has_precomputed_metadata = "usage_prompt_tokens" in internal_md

        if has_precomputed_metadata:
            # Fast path: just read from _metadata (set in finalize)
            out: list[dict[str, Any]] = []
            for native_msg, core_msg in zip(native_messages, messages):
                metadata = dict(core_msg.get("metadata") or {})

                internal_md = native_msg.get("_metadata")
                if isinstance(internal_md, dict):
                    for key, value in internal_md.items():
                        if key.startswith("usage_") or key == "usage":
                            metadata[key] = value

                out.append({**core_msg, "metadata": metadata})

            # Handle length mismatch: if native_messages longer, attach trailing metadata
            if len(native_messages) > len(messages):
                # Get metadata from the last native message and merge into last output
                last_native = native_messages[-1]
                if isinstance(last_native.get("_metadata"), dict):
                    trailing_metadata = {}
                    for key, value in last_native["_metadata"].items():
                        if key.startswith("usage_") or key == "usage":
                            trailing_metadata[key] = value
                    if trailing_metadata and out:
                        out[-1] = {
                            **out[-1],
                            "metadata": {
                                **out[-1].get("metadata", {}),
                                **trailing_metadata,
                            },
                        }

            return out

        # Rebuild path: compute metadata on-the-fly for full history
        # This handles the case where from_native_messages is called with full history
        # without finalize having run (e.g., session rebuild)

        # Calculate session totals
        session_metadata = _session_totals(native_messages)

        # Calculate turn totals for the last message
        turn_metadata = _turn_totals(native_messages, native_messages)

        # Handle length mismatch
        if len(messages) != len(native_messages):
            # Only process the last message with trailing native metadata
            out = list(messages)
            trailing_metadata = {}

            last_native = native_messages[-1]
            if isinstance(last_native.get("_metadata"), dict):
                internal_md = last_native["_metadata"]
                usage = internal_md.get("usage")
                if isinstance(usage, dict):
                    trailing_metadata = _per_message_metadata(usage)
                    trailing_metadata |= session_metadata
                    trailing_metadata |= turn_metadata

            if trailing_metadata:
                out[-1] = {
                    **out[-1],
                    "metadata": {**out[-1].get("metadata", {}), **trailing_metadata},
                }
            return out

        # Normal rebuild: lengths match
        out: list[dict[str, Any]] = []
        for index, (native_msg, core_msg) in enumerate(zip(native_messages, messages)):
            metadata = dict(core_msg.get("metadata") or {})

            internal_md = native_msg.get("_metadata")
            if not isinstance(internal_md, dict):
                out.append(core_msg)
                continue

            usage = internal_md.get("usage")
            if not isinstance(usage, dict):
                out.append(core_msg)
                continue

            # Per-message metadata
            per_msg = _per_message_metadata(usage)
            metadata |= per_msg

            # Session totals (same for all messages)
            metadata |= session_metadata

            # Turn totals only for the last assistant message in a turn
            if native_msg.get("role") == "assistant":
                separator_index = _last_turn_separator_index(native_messages, index)
                turn_start = separator_index + 1

                # Turn reasoning is useful on every assistant message in the turn,
                # including tool-call assistants that precede the turn-closing reply.
                turn_reasoning = _sum_assistant_metric(
                    native_messages,
                    index,
                    _usage_reasoning_tokens,
                    start_index=turn_start,
                )
                if turn_reasoning is not None:
                    metadata["usage_turn_reasoning_tokens_cumulative"] = turn_reasoning
                    metadata["usage_turn_reasoning_tokens_cumulative_formatted"] = (
                        _format_token_count(turn_reasoning)
                    )

                # Check if this is the last message or next message is a separator
                is_last = index == len(native_messages) - 1
                next_is_separator = False
                if index < len(native_messages) - 1:
                    next_msg = native_messages[index + 1]
                    if isinstance(next_msg, dict):
                        next_role = next_msg.get("role")
                        next_is_separator = next_role in ("user", "system")

                if is_last or (
                    next_is_separator and not _message_has_tool_calls(native_msg)
                ):
                    # Calculate turn totals ending at this message
                    turn_cost = _sum_assistant_metric(
                        native_messages, index, _usage_cost, start_index=turn_start
                    )
                    turn_input = _sum_assistant_metric(
                        native_messages,
                        index,
                        _usage_input_tokens,
                        start_index=turn_start,
                    )
                    turn_cached = _sum_assistant_effective_cached_tokens(
                        native_messages,
                        index,
                        start_index=turn_start,
                    )
                    turn_output = _sum_assistant_metric(
                        native_messages,
                        index,
                        _usage_output_tokens,
                        start_index=turn_start,
                    )

                    if turn_cost is not None:
                        metadata["usage_turn_cost_cumulative"] = turn_cost
                        metadata["usage_turn_cost_cumulative_formatted"] = _format_cost(
                            turn_cost
                        )
                    if turn_input is not None:
                        metadata["usage_turn_input_tokens_cumulative"] = turn_input
                        metadata["usage_turn_input_tokens_cumulative_formatted"] = (
                            _format_token_count(turn_input)
                        )
                    if turn_cached is not None:
                        metadata["usage_turn_cached_tokens_cumulative"] = turn_cached
                        metadata["usage_turn_cached_tokens_cumulative_formatted"] = (
                            _format_token_count(turn_cached)
                        )
                    if turn_output is not None:
                        metadata["usage_turn_output_tokens_cumulative"] = turn_output
                        metadata["usage_turn_output_tokens_cumulative_formatted"] = (
                            _format_token_count(turn_output)
                        )

            out.append({**core_msg, "metadata": metadata})

        return out
