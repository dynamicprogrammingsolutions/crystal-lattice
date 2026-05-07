from __future__ import annotations

import os
import sys
from typing import Any, Dict, List

import pytest

# Ensure repo root is importable (tests live under plugins/openrouter/tests)
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from openrouter_plugins.openrouter_usage_extension import OpenRouterUsageExtension


def make_partial() -> Dict[str, Any]:
    return {"role": "assistant", "content": "", "_metadata": {}}


def test_turn_cost_single_assistant_no_tools() -> None:
    ext = OpenRouterUsageExtension()

    state = {"partial": make_partial()}
    native_chunk = {"usage": {"total_tokens": 10, "cost": 0.123456, "completion_tokens_details": {"reasoning_tokens": 7}}}

    # No prior native messages
    partials, finals, native_messages, new_state = ext.process_chunk(
        native_chunk=native_chunk,
        partial_messages=[],
        final_messages=[],
        native_messages=[],
        state=state,
    )

    accumulated = new_state.get("partial") or {}
    internal_md = accumulated.get("_metadata") or {}

    # Expect formatted fields
    assert internal_md.get("usage_total_cost_formatted") == "$0.123456"
    assert internal_md.get("usage_total_cost_cumulative_formatted") == "$0.123456"

    # Per-turn cumulative should equal the current cost (no prior messages)
    assert internal_md.get("usage_turn_cost_cumulative") == pytest.approx(0.123456, rel=1e-9)
    assert internal_md.get("usage_turn_cost_cumulative_formatted") == "$0.123456"
    assert internal_md.get("usage_turn_input_tokens_cumulative") == 0
    assert internal_md.get("usage_turn_input_tokens_cumulative_formatted") == "0"
    assert internal_md.get("usage_turn_cached_tokens_cumulative") == 0
    assert internal_md.get("usage_turn_cached_tokens_cumulative_formatted") == "0"
    assert internal_md.get("usage_turn_output_tokens_cumulative") == 0
    assert internal_md.get("usage_turn_output_tokens_cumulative_formatted") == "0"
    # Per-turn reasoning tokens should equal the current reasoning tokens
    assert internal_md.get("usage_turn_reasoning_tokens_cumulative") == 7
    assert internal_md.get("usage_turn_reasoning_tokens_cumulative_formatted") == "7"


def test_turn_cost_with_separators_and_tool_calls() -> None:
    ext = OpenRouterUsageExtension()

    # Build a retained native history:
    # user -> assistant (with tool_calls) cost 0.2 -> assistant (no tools) cost 0.3
    native_messages: List[Dict[str, Any]] = [
        {"role": "user", "content": "hi"},
        {
            "role": "assistant",
            "content": "tool reply",
            "_metadata": {"usage": {"cost": 0.2, "completion_tokens_details": {"reasoning_tokens": 5}}},
            "tool_calls": [{"id": "t1"}],
        },
        {"role": "assistant", "content": "reply", "_metadata": {"usage": {"cost": 0.3, "completion_tokens_details": {"reasoning_tokens": 10}}}},
    ]

    state = {"partial": make_partial()}
    native_chunk = {"usage": {"total_tokens": 5, "cost": 0.1, "completion_tokens_details": {"reasoning_tokens": 3}}}

    _, _, _, new_state = ext.process_chunk(
        native_chunk=native_chunk,
        partial_messages=[],
        final_messages=[],
        native_messages=native_messages,
        state=state,
    )

    internal_md = new_state.get("partial", {}).get("_metadata") or {}

    # Last separator is the assistant (no tools) at index 2, so turn total
    # should include only messages after that (none) plus current cost.
    assert internal_md.get("usage_turn_cost_cumulative") == pytest.approx(0.1, rel=1e-9)
    assert internal_md.get("usage_turn_cost_cumulative_formatted") == "$0.100000"
    # No assistant messages after the last separator, so turn reasoning is current only
    assert internal_md.get("usage_turn_reasoning_tokens_cumulative") == 3
    assert internal_md.get("usage_turn_reasoning_tokens_cumulative_formatted") == "3"


def test_turn_token_breakdown_fields_are_exposed_for_openrouter() -> None:
    ext = OpenRouterUsageExtension()

    state = {"partial": make_partial()}
    native_messages: List[Dict[str, Any]] = [
        {"role": "user", "content": "hi"},
        {
            "role": "assistant",
            "content": "tool reply",
            "_metadata": {
                "usage": {
                    "prompt_tokens": 8,
                    "prompt_tokens_details": {"cached_tokens": 2},
                    "completion_tokens": 4,
                },
                "turn": {"id": 1, "has_tool_calls": True, "is_terminal": False},
            },
            "tool_calls": [{"id": "t1"}],
        },
    ]
    native_chunk = {
        "usage": {
            "prompt_tokens": 12,
            "prompt_tokens_details": {"cached_tokens": 3},
            "completion_tokens": 5,
            "cost": 0.1,
        }
    }

    _, _, _, new_state = ext.process_chunk(
        native_chunk=native_chunk,
        partial_messages=[],
        final_messages=[],
        native_messages=native_messages,
        state=state,
    )

    internal_md = new_state.get("partial", {}).get("_metadata") or {}
    assert internal_md.get("usage_turn_input_tokens_cumulative") == 20
    assert internal_md.get("usage_turn_input_tokens_cumulative_formatted") == "20"
    assert internal_md.get("usage_turn_cached_tokens_cumulative") == 5
    assert internal_md.get("usage_turn_cached_tokens_cumulative_formatted") == "5"
    assert internal_md.get("usage_turn_output_tokens_cumulative") == 9
    assert internal_md.get("usage_turn_output_tokens_cumulative_formatted") == "9"
    assert internal_md.get("turn") == {"id": 1, "has_tool_calls": False, "is_terminal": True}


def test_from_native_messages_turn_field_visibility() -> None:
    ext = OpenRouterUsageExtension()

    # Native assistant with tool_calls should not surface turn-cost fields
    native_with_tools = {
        "role": "assistant",
        "_metadata": {"usage": {"cost": 0.2}, "usage_turn_cost_cumulative": 0.2, "usage_turn_cost_cumulative_formatted": "$0.200000", "usage_turn_reasoning_tokens_cumulative": 5, "usage_turn_reasoning_tokens_cumulative_formatted": "5"},
        "tool_calls": [{"id": "t1"}],
    }

    # Native assistant without tool_calls should surface turn-cost
    native_no_tools = {
        "role": "assistant",
        "_metadata": {"usage": {"cost": 0.3}, "usage_turn_cost_cumulative": 0.3, "usage_turn_cost_cumulative_formatted": "$0.300000", "usage_turn_reasoning_tokens_cumulative": 8, "usage_turn_reasoning_tokens_cumulative_formatted": "8"},
    }

    messages = [{"role": "assistant", "content": "", "metadata": {}}, {"role": "assistant", "content": "", "metadata": {}}]

    out = ext.from_native_messages([native_with_tools, native_no_tools], messages)

    # First message should NOT have the turn-cost fields
    md0 = out[0].get("metadata") or {}
    assert "usage_turn_cost_cumulative" not in md0
    assert "usage_turn_cost_cumulative_formatted" not in md0

    # Second message should have them
    md1 = out[1].get("metadata") or {}
    assert md1.get("usage_turn_cost_cumulative") == pytest.approx(0.3, rel=1e-9)
    assert md1.get("usage_turn_cost_cumulative_formatted") == "$0.300000"
    # Reasoning tokens only surfaced for the second (no-tool) message
    assert "usage_turn_reasoning_tokens_cumulative" not in md0
    assert md1.get("usage_turn_reasoning_tokens_cumulative") == 8
    assert md1.get("usage_turn_reasoning_tokens_cumulative_formatted") == "8"
