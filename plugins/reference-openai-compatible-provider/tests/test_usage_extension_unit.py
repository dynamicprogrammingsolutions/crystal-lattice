from __future__ import annotations

from typing import Any

import pytest

from reference_openai_compatible_provider.provider import OpenAICompatibleProvider
from reference_openai_compatible_provider.usage_extension import (
    OpenAICompatibleUsageExtension,
)


class _Resp:
    def __init__(
        self, *, ok: bool, payload: Any = None, status_code: int = 200, text: str = ""
    ):
        self.ok = ok
        self._payload = payload
        self.status_code = status_code
        self.text = text
        self.encoding = "utf-8"

    def json(self) -> Any:
        return self._payload

    def close(self) -> None:
        return None


def test_usage_extension_normalizes_common_usage_fields():
    ext = OpenAICompatibleUsageExtension()
    native_messages = [
        {
            "role": "assistant",
            "content": "hello",
            "_metadata": {
                "usage": {
                    "prompt_tokens": 12,
                    "completion_tokens": 7,
                    "total_tokens": 19,
                }
            },
        }
    ]
    messages = [{"role": "assistant", "content": "hello", "metadata": {}}]

    rebuilt = ext.from_native_messages(native_messages, messages)
    metadata = rebuilt[0]["metadata"]
    assert metadata["usage"]["prompt_tokens"] == 12
    assert metadata["usage_prompt_tokens"] == 12
    assert metadata["usage_completion_tokens"] == 7
    assert metadata["usage_total_tokens"] == 19
    assert metadata["usage_total_tokens_formatted"] == "19"


def test_usage_extension_extracts_reasoning_tokens_from_nested_details():
    ext = OpenAICompatibleUsageExtension()
    native_messages = [
        {
            "role": "assistant",
            "content": "hello",
            "_metadata": {
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 6,
                    "total_tokens": 16,
                    "completion_tokens_details": {"reasoning_tokens": 4},
                }
            },
        }
    ]
    messages = [{"role": "assistant", "content": "hello", "metadata": {}}]

    rebuilt = ext.from_native_messages(native_messages, messages)
    metadata = rebuilt[0]["metadata"]
    assert metadata["usage_reasoning_tokens"] == 4
    assert metadata["usage_reasoning_tokens_formatted"] == "4"


def test_usage_extension_exposes_openrouter_style_ui_elements():
    ext = OpenAICompatibleUsageExtension()

    assert ext.get_ui_elements({}, [], []) == [
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
        {
            "ui_type": "status_bar",
            "data": "metadata.usage_total_cost_cumulative_formatted",
            "template": "Total: {{data}}",
        },
    ]
    assert ext.get_ui_elements({"show_usage": False}, [], []) == []


def test_usage_extension_normalizes_cached_and_cost_fields_with_turn_totals():
    ext = OpenAICompatibleUsageExtension()
    native_messages = [
        {"role": "user", "content": "hi"},
        {
            "role": "assistant",
            "content": "thinking",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "lookup", "arguments": "{}"},
                }
            ],
            "_metadata": {
                "usage": {
                    "prompt_tokens": 8,
                    "completion_tokens": 4,
                    "total_tokens": 12,
                    "cost_details": {"upstream_inference_cost": 0.000123},
                    "completion_tokens_details": {"reasoning_tokens": 3},
                }
            },
        },
        {"role": "tool", "content": "ok"},
        {
            "role": "assistant",
            "content": "done",
            "_metadata": {
                "usage": {
                    "prompt_tokens": 1200,
                    "completion_tokens": 300,
                    "total_tokens": 1500,
                    "prompt_tokens_details": {"cached_tokens": 256},
                    "cost": 0.000456,
                    "completion_tokens_details": {"reasoning_tokens": 7},
                }
            },
        },
    ]
    messages = [
        {"role": "user", "content": "hi", "metadata": {}},
        {"role": "assistant", "content": "thinking", "metadata": {}},
        {"role": "tool", "content": "ok", "metadata": {}},
        {"role": "assistant", "content": "done", "metadata": {}},
    ]

    rebuilt = ext.from_native_messages(native_messages, messages)
    tool_metadata = rebuilt[1]["metadata"]
    final_metadata = rebuilt[3]["metadata"]

    assert tool_metadata["usage_total_cost_formatted"] == "$0.000123"
    assert "usage_turn_cost_cumulative_formatted" not in tool_metadata
    assert tool_metadata["usage_turn_reasoning_tokens_cumulative_formatted"] == "3"
    assert final_metadata["usage_cached_tokens"] == 256
    assert final_metadata["usage_cached_tokens_formatted"] == "256"
    assert final_metadata["usage_prompt_tokens_formatted"] == "1,200"
    assert final_metadata["usage_total_cost_formatted"] == "$0.000456"
    assert final_metadata["usage_total_cost_cumulative_formatted"] == "$0.000579"
    assert final_metadata["usage_turn_cost_cumulative_formatted"] == "$0.000579"
    # Turn token breakdown
    assert (
        final_metadata["usage_turn_input_tokens_cumulative_formatted"] == "1,208"
    )  # 8 + 1200
    assert (
        final_metadata["usage_turn_cached_tokens_cumulative_formatted"] == "256"
    )  # 256
    assert (
        final_metadata["usage_turn_output_tokens_cumulative_formatted"] == "304"
    )  # 4 + 300
    assert (
        final_metadata["usage_turn_reasoning_tokens_cumulative_formatted"] == "10"
    )  # 3 + 7


def test_usage_extension_finalize_stamps_turn_metadata() -> None:
    ext = OpenAICompatibleUsageExtension()
    final_messages = [
        {
            "role": "assistant",
            "content": "done",
            "_metadata": {
                "usage": {
                    "prompt_tokens": 12,
                    "completion_tokens": 7,
                    "total_tokens": 19,
                }
            },
        }
    ]
    native_messages = [{"role": "user", "content": "hi"}, *final_messages]

    new_finals, _new_native, _state = ext.finalize(
        final_messages, native_messages, {"config": {}}
    )
    metadata = new_finals[0].get("_metadata") or {}
    assert metadata.get("turn") == {
        "id": 1,
        "has_tool_calls": False,
        "is_terminal": True,
    }


def test_usage_extension_captures_streaming_usage_into_partial_state():
    ext = OpenAICompatibleUsageExtension()
    partial_messages = [{"role": "assistant", "content": "hi"}]
    state = {"accumulator": {"role": "assistant", "content": "hi"}}

    _partials, _finals, _native, new_state = ext.process_chunk(
        {"usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5}},
        partial_messages,
        [],
        [],
        state,
    )

    assert new_state["accumulator"]["_metadata"]["usage"] == {
        "prompt_tokens": 3,
        "completion_tokens": 2,
        "total_tokens": 5,
    }


def test_usage_extension_finalize_preserves_native_history_when_no_final_messages():
    ext = OpenAICompatibleUsageExtension()
    native_messages = [
        {"role": "user", "content": "Use a tool."},
        {
            "role": "assistant",
            "content": "",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "add", "arguments": '{"a":2,"b":3}'},
                }
            ],
            "_metadata": {
                "usage": {
                    "prompt_tokens": 7,
                    "completion_tokens": 5,
                    "total_tokens": 12,
                }
            },
        },
    ]

    finals, rebuilt_native, _state = ext.finalize([], native_messages, {"config": {}})

    assert finals == []
    assert rebuilt_native == native_messages


def test_provider_call_api_preserves_non_streaming_usage_for_extensions(monkeypatch):
    def fake_post(
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
    ):
        assert json["stream"] is False
        return _Resp(
            ok=True,
            payload={
                "choices": [{"message": {"role": "assistant", "content": "pong"}}],
                "usage": {
                    "prompt_tokens": 2,
                    "completion_tokens": 1,
                    "total_tokens": 3,
                },
            },
        )

    monkeypatch.setattr(
        "requests.sessions.Session.post",
        lambda self, url, headers, json, timeout, stream: fake_post(
            url, headers, json, timeout
        ),
    )

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [], {"config": {"model": "demo-model"}}
    )
    _partials, finals, _history, _state = provider.call_api(native_messages, state)

    assert finals[0]["_metadata"]["usage"] == {
        "prompt_tokens": 2,
        "completion_tokens": 1,
        "total_tokens": 3,
    }


def test_usage_extension_uses_last_native_message_as_length_mismatch_fallback():
    ext = OpenAICompatibleUsageExtension()
    messages = [{"role": "assistant", "content": "done", "metadata": {}}]
    native_messages = [
        {"role": "assistant", "content": "ignored"},
        {
            "role": "assistant",
            "content": "done",
            "_metadata": {
                "usage": {"prompt_tokens": 5, "completion_tokens": 4, "total_tokens": 9}
            },
        },
    ]

    rebuilt = ext.from_native_messages(native_messages, messages)
    assert rebuilt[-1]["metadata"]["usage_total_tokens"] == 9


def test_usage_extension_calculates_cost_from_token_rates():
    """Test cost calculation when provider doesn't return cost but token_rates are configured."""
    ext = OpenAICompatibleUsageExtension()

    # Simulate finalize injecting calculated cost
    final_messages = [
        {
            "role": "assistant",
            "content": "hello",
            "_metadata": {
                "usage": {
                    "prompt_tokens": 1000,
                    "completion_tokens": 500,
                    "total_tokens": 1500,
                    # No 'cost' field - provider didn't return it
                }
            },
        }
    ]
    native_messages = list(final_messages)
    state = {
        "config": {
            "token_rates": {
                "input": 0.10,  # $0.10 per million input tokens
                "cached": 0.01,  # $0.01 per million cached tokens
                "completion": 0.30,  # $0.30 per million completion tokens
            }
        }
    }

    new_finals, new_native, new_state = ext.finalize(
        final_messages, native_messages, state
    )

    # Cost should be calculated and injected
    # (1000 * 0.10/1M) + (500 * 0.30/1M) = 0.0001 + 0.00015 = 0.00025
    assert new_finals[0]["_metadata"]["usage"]["cost"] == 0.00025


def test_usage_extension_calculates_cost_with_cached_discount():
    """Test cached tokens are discounted when cached_rate is configured."""
    ext = OpenAICompatibleUsageExtension()

    final_messages = [
        {
            "role": "assistant",
            "content": "hello",
            "_metadata": {
                "usage": {
                    "prompt_tokens": 1000,
                    "completion_tokens": 500,
                    "total_tokens": 1500,
                    "prompt_tokens_details": {"cached_tokens": 200},
                }
            },
        }
    ]
    native_messages = list(final_messages)
    state = {
        "config": {
            "token_rates": {
                "input": 0.10,  # $0.10/M
                "cached": 0.02,  # $0.02/M (discounted)
                "completion": 0.30,  # $0.30/M
            }
        }
    }

    new_finals, new_native, new_state = ext.finalize(
        final_messages, native_messages, state
    )

    # Cost calculation:
    # Input: 1000 tokens at $0.10/M = 0.0001
    # Cached discount: 200 tokens * ((0.10 - 0.02) / 1M) = 0.000016 discount
    # Adjusted input cost: 0.0001 - 0.000016 = 0.000084
    # Completion: 500 tokens at $0.30/M = 0.00015
    # Total: 0.000084 + 0.00015 = 0.000234
    assert new_finals[0]["_metadata"]["usage"]["cost"] == pytest.approx(0.000234)


def test_usage_extension_provider_cost_takes_precedence():
    """Provider-returned cost should not be overwritten by calculated cost."""
    ext = OpenAICompatibleUsageExtension()

    final_messages = [
        {
            "role": "assistant",
            "content": "hello",
            "_metadata": {
                "usage": {
                    "prompt_tokens": 1000,
                    "completion_tokens": 500,
                    "total_tokens": 1500,
                    "cost": 0.001,  # Provider already returned cost
                }
            },
        }
    ]
    native_messages = list(final_messages)
    state = {
        "config": {
            "token_rates": {
                "input": 0.10,
                "completion": 0.30,
            }
        }
    }

    new_finals, new_native, new_state = ext.finalize(
        final_messages, native_messages, state
    )

    # Provider cost should remain unchanged
    assert new_finals[0]["_metadata"]["usage"]["cost"] == 0.001


def test_usage_extension_no_cost_when_no_token_rates():
    """No cost should be calculated when token_rates are not configured."""
    ext = OpenAICompatibleUsageExtension()

    final_messages = [
        {
            "role": "assistant",
            "content": "hello",
            "_metadata": {
                "usage": {
                    "prompt_tokens": 1000,
                    "completion_tokens": 500,
                    "total_tokens": 1500,
                }
            },
        }
    ]
    native_messages = list(final_messages)
    state = {"config": {}}  # No token_rates

    new_finals, new_native, new_state = ext.finalize(
        final_messages, native_messages, state
    )

    # No cost should be injected
    assert "cost" not in new_finals[0]["_metadata"]["usage"]


def test_usage_extension_incomplete_token_rates():
    """Cost should not be calculated if rates are incomplete (missing input or completion)."""
    ext = OpenAICompatibleUsageExtension()

    final_messages = [
        {
            "role": "assistant",
            "content": "hello",
            "_metadata": {
                "usage": {
                    "prompt_tokens": 1000,
                    "completion_tokens": 500,
                    "total_tokens": 1500,
                }
            },
        }
    ]
    native_messages = list(final_messages)

    # Missing completion rate
    state = {"config": {"token_rates": {"input": 0.10}}}

    new_finals, new_native, new_state = ext.finalize(
        final_messages, native_messages, state
    )

    # No cost should be injected
    assert "cost" not in new_finals[0]["_metadata"]["usage"]


def test_usage_extension_full_flow_with_calculated_cost():
    """Test full flow: finalize injects cost, from_native_messages extracts it."""
    ext = OpenAICompatibleUsageExtension()

    # After provider finalize, we have final_messages with usage but no cost
    final_messages = [
        {
            "role": "assistant",
            "content": "response",
            "_metadata": {
                "usage": {
                    "prompt_tokens": 10000,
                    "completion_tokens": 2000,
                    "total_tokens": 12000,
                }
            },
        }
    ]
    native_messages = list(final_messages)
    state = {
        "config": {
            "token_rates": {
                "input": 1.0,  # $1.00/M
                "completion": 3.0,  # $3.00/M
            }
        }
    }

    # Extension finalize injects cost
    new_finals, new_native, new_state = ext.finalize(
        final_messages, native_messages, state
    )

    # Now from_native_messages should see the calculated cost
    messages = [{"role": "assistant", "content": "response", "metadata": {}}]
    rebuilt = ext.from_native_messages(new_native, messages)

    # Cost should be: (10000 * 1.0/1M) + (2000 * 3.0/1M) = 0.01 + 0.006 = 0.016
    assert rebuilt[0]["metadata"]["usage_total_cost"] == 0.016
    assert rebuilt[0]["metadata"]["usage_total_cost_formatted"] == "$0.016000"


def test_usage_extension_session_total_across_multiple_turns():
    """Test that session total is calculated correctly across multiple turns in finalize."""
    ext = OpenAICompatibleUsageExtension()

    # Simulate full history with multiple turns
    native_messages = [
        {"role": "user", "content": "first turn"},
        {
            "role": "assistant",
            "content": "first response",
            "_metadata": {
                "usage": {
                    "prompt_tokens": 100,
                    "completion_tokens": 50,
                    "total_tokens": 150,
                    "cost": 0.001,
                }
            },
        },
        {"role": "user", "content": "second turn"},
        {
            "role": "assistant",
            "content": "tool call",
            "tool_calls": [
                {
                    "id": "call_1",
                    "type": "function",
                    "function": {"name": "test", "arguments": "{}"},
                }
            ],
            "_metadata": {
                "usage": {
                    "prompt_tokens": 200,
                    "completion_tokens": 100,
                    "total_tokens": 300,
                    "cost": 0.002,
                }
            },
        },
        {"role": "tool", "content": "result"},
        # This is the new message (final_messages)
        {
            "role": "assistant",
            "content": "final answer",
            "_metadata": {
                "usage": {
                    "prompt_tokens": 300,
                    "completion_tokens": 150,
                    "total_tokens": 450,
                    "cost": 0.003,
                }
            },
        },
    ]

    # final_messages only contains the new messages from this turn
    final_messages = [
        native_messages[3],  # tool call assistant
        native_messages[5],  # final answer
    ]

    state = {"config": {}}

    # Finalize should calculate session totals from full history
    new_finals, new_native, new_state = ext.finalize(
        final_messages, native_messages, state
    )

    # Check that the last message has correct session total
    # Total: 0.001 + 0.002 + 0.003 = 0.006
    last_msg_metadata = new_finals[-1]["_metadata"]
    assert last_msg_metadata["usage_total_cost_cumulative"] == 0.006
    assert last_msg_metadata["usage_total_cost_cumulative_formatted"] == "$0.006000"

    # Turn cost should be 0.002 + 0.003 = 0.005 (tool call + final answer)
    assert last_msg_metadata["usage_turn_cost_cumulative"] == 0.005
    assert last_msg_metadata["usage_turn_cost_cumulative_formatted"] == "$0.005000"

    # Turn token breakdown: tool call (200 input, 100 output) + final (300 input, 150 output)
    assert last_msg_metadata["usage_turn_input_tokens_cumulative"] == 500
    assert last_msg_metadata["usage_turn_output_tokens_cumulative"] == 250

    # Now test from_native_messages reads the pre-computed values
    messages = [
        {"role": "assistant", "content": "tool call", "metadata": {}},
        {"role": "assistant", "content": "final answer", "metadata": {}},
    ]
    rebuilt = ext.from_native_messages(new_native[-2:], messages)

    # Last message should have session total
    assert rebuilt[-1]["metadata"]["usage_total_cost_cumulative"] == 0.006
    assert (
        rebuilt[-1]["metadata"]["usage_total_cost_cumulative_formatted"] == "$0.006000"
    )
