from __future__ import annotations

from typing import Any, Dict, List

import pytest

from openrouter_responses_plugins.openrouter_responses_usage_extension import OpenRouterResponsesUsageExtension


def _assistant_output_item(text: str, *, response_id: str = "resp") -> Dict[str, Any]:
    return {
        "type": "message",
        "role": "assistant",
        "content": [{"type": "output_text", "text": text}],
        "_metadata": {"response_id": response_id, "usage": {}},
    }


def test_turn_cost_single_response_attaches_formatted_fields() -> None:
    ext = OpenRouterResponsesUsageExtension()

    final_messages: List[Dict[str, Any]] = [_assistant_output_item("hi", response_id="resp_1")]
    native_messages: List[Dict[str, Any]] = list(final_messages)
    usage = {
        "total_tokens": 10,
        "cost": 0.123456,
        "completion_tokens_details": {"reasoning_tokens": 7},
    }
    final_messages[0]["_metadata"]["usage"] = usage
    native_messages[0]["_metadata"]["usage"] = usage
    native_chunk = {"usage": usage}

    _partials, finals, new_native, _state = ext.process_chunk(
        native_chunk=native_chunk,
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={},
    )

    assert finals and isinstance(finals[0], dict)
    md = finals[0].get("_metadata") or {}
    assert isinstance(md, dict)

    assert md.get("usage_total_cost_formatted") == "$0.123456"
    assert md.get("usage_total_cost_cumulative_formatted") == "$0.123456"

    assert md.get("usage_turn_cost_cumulative") == pytest.approx(0.123456, rel=1e-9)
    assert md.get("usage_turn_cost_cumulative_formatted") == "$0.123456"
    assert md.get("usage_turn_reasoning_tokens_cumulative") == 7
    assert md.get("usage_turn_reasoning_tokens_cumulative_formatted") == "7"
    assert md.get("has_tool_calls") is False

    assert new_native == finals


def test_turn_cost_with_separators_and_tool_calls() -> None:
    ext = OpenRouterResponsesUsageExtension()

    base_native: List[Dict[str, Any]] = [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "hi"}],
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "tool reply"}],
            "_metadata": {
                "usage": {"cost": 0.2, "completion_tokens_details": {"reasoning_tokens": 5}},
                "has_tool_calls": True,
            },
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "reply"}],
            "_metadata": {
                "usage": {"cost": 0.3, "completion_tokens_details": {"reasoning_tokens": 10}},
                "has_tool_calls": False,
            },
        },
    ]

    final_messages: List[Dict[str, Any]] = [_assistant_output_item("new", response_id="resp_3")]
    native_messages: List[Dict[str, Any]] = [*base_native, *final_messages]
    usage = {
        "total_tokens": 5,
        "cost": 0.1,
        "completion_tokens_details": {"reasoning_tokens": 3},
    }
    final_messages[0]["_metadata"]["usage"] = usage
    native_messages[-1]["_metadata"]["usage"] = usage
    native_chunk = {"usage": usage}

    _partials, finals, _native_out, _state = ext.process_chunk(
        native_chunk=native_chunk,
        partial_messages=[],
        final_messages=final_messages,
        native_messages=native_messages,
        state={},
    )

    md = finals[0].get("_metadata") or {}
    assert isinstance(md, dict)

    # Last separator is the assistant response with has_tool_calls=False, so
    # per-turn totals include only the current response.
    assert md.get("usage_turn_cost_cumulative") == pytest.approx(0.1, rel=1e-9)
    assert md.get("usage_turn_cost_cumulative_formatted") == "$0.100000"
    assert md.get("usage_turn_reasoning_tokens_cumulative") == 3
    assert md.get("usage_turn_reasoning_tokens_cumulative_formatted") == "3"


def test_from_native_messages_is_noop() -> None:
    ext = OpenRouterResponsesUsageExtension()
    messages = [{"role": "assistant", "content": "x", "metadata": {"usage": {"cost": 0.1}}}]
    assert ext.from_native_messages([], messages) == messages
