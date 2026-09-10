from __future__ import annotations

from typing import Any, Dict

import pytest

from agent_core import AgentCore

from plugins.echo_openai_like_provider import EchoOpenAILikeProvider
from timestamp_extension.duration_extension import DurationExtension


def _make_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(EchoOpenAILikeProvider)
    core.register_feature(DurationExtension)
    return core


def test_assistant_duration_persisted_in_native_history_and_survives_rebuild() -> None:
    core = _make_core()
    config: Dict[str, Any] = {"model": "test-model"}

    session = core.create_session()
    session = core.add_message(session, "user", "hi", config=config)

    session_1, finals = core.send_request(session, config)
    assert finals

    md = finals[-1].get("metadata") or {}
    assert isinstance(md.get("duration_started_at"), str) and md["duration_started_at"]
    assert (
        isinstance(md.get("duration_finished_at"), str) and md["duration_finished_at"]
    )
    assert isinstance(md.get("duration_ms"), int)
    assert md["duration_ms"] >= 0
    assert isinstance(md.get("duration_formatted"), str) and md["duration_formatted"]

    assert md.get("turn_duration_ms") == md.get("duration_ms")
    assert md.get("turn_duration_formatted") == md.get("duration_formatted")
    assert md.get("total_duration_ms") == md.get("duration_ms")
    assert md.get("total_duration_formatted") == md.get("duration_formatted")

    native_1 = session_1.metadata.get("native_messages") or []
    assert native_1
    assert native_1[-1].get("role") == "assistant"
    internal_md = native_1[-1].get("_metadata") or {}
    assert internal_md.get("duration_ms") == md["duration_ms"]
    assert internal_md.get("turn_duration_ms") == md["turn_duration_ms"]
    assert internal_md.get("total_duration_ms") == md["total_duration_ms"]
    assert internal_md.get("_duration_extension_owner") is True

    # Appending a new message rebuilds core history from native history.
    session_2 = core.add_message(session_1, "user", "next", config=config)
    assistant_msgs = [msg for msg in session_2.messages if msg.role == "assistant"]
    assert assistant_msgs
    assert assistant_msgs[-1].metadata
    assert assistant_msgs[-1].metadata.get("duration_ms") == md["duration_ms"]
    assert assistant_msgs[-1].metadata.get("turn_duration_ms") == md["turn_duration_ms"]
    assert (
        assistant_msgs[-1].metadata.get("total_duration_ms") == md["total_duration_ms"]
    )

    session_3, second_finals = core.send_request(session_2, config)
    assert session_3.messages
    second_md = second_finals[-1].get("metadata") or {}
    assert second_md.get("turn_duration_ms") == second_md.get("duration_ms")
    assert second_md.get("total_duration_ms") == (
        md["duration_ms"] + second_md["duration_ms"]
    )


def test_turn_duration_sums_assistant_durations_since_last_separator() -> None:
    core = _make_core()
    config: Dict[str, Any] = {"model": "test-model"}

    session = core.create_session()
    session = core.add_message(session, "user", "hi", config=config)

    seeded_duration_ms = 123
    tool_calls = [
        {
            "id": "call_1",
            "type": "function",
            "function": {"name": "dummy", "arguments": "{}"},
        }
    ]

    session = core.add_message(
        session,
        "assistant",
        "need tool",
        metadata={
            "tool_calls": tool_calls,
            "duration_ms": seeded_duration_ms,
            "duration_formatted": "123ms",
            "turn_duration_ms": seeded_duration_ms,
            "turn_duration_formatted": "123ms",
            "duration_started_at": "2020-01-01T00:00:00+00:00",
            "duration_finished_at": "2020-01-01T00:00:01+00:00",
        },
        config=config,
    )
    session = core.add_message(
        session,
        "tool",
        "tool result",
        metadata={"tool_call_id": "call_1"},
        config=config,
    )

    assistant_msgs = [msg for msg in session.messages if msg.role == "assistant"]
    assert assistant_msgs
    tool_call_msg = assistant_msgs[-1]
    assert tool_call_msg.metadata
    assert tool_call_msg.metadata.get("duration_ms") == seeded_duration_ms
    assert tool_call_msg.metadata.get("turn_duration_ms") == seeded_duration_ms
    assert tool_call_msg.metadata.get("turn_duration_formatted") == "123ms"

    session_1, finals = core.send_request(session, config)
    assert finals
    md = finals[-1].get("metadata") or {}
    assert isinstance(md.get("duration_ms"), int)
    current_duration_ms = md["duration_ms"]
    assert md.get("turn_duration_ms") == seeded_duration_ms + current_duration_ms
    assert isinstance(md.get("turn_duration_formatted"), str)

    native_1 = session_1.metadata.get("native_messages") or []
    assert native_1
    internal_md = native_1[-1].get("_metadata") or {}
    assert (
        internal_md.get("turn_duration_ms") == seeded_duration_ms + current_duration_ms
    )


def test_turn_duration_uses_usage_extension_turn_metadata_for_responses_style_history() -> (
    None
):
    ext = DurationExtension()

    state = {
        "_duration_extension": {
            "duration_started_at": "2024-01-01T00:00:00+00:00",
            "duration_started_at_mono": 100.0,
        }
    }

    native_messages = [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "hi"}],
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "calling tool"}],
            "_metadata": {
                "duration_ms": 123,
                "turn_duration_ms": 123,
                "turn": {"id": 1, "has_tool_calls": True, "is_terminal": False},
                "usage_turn_input_tokens_cumulative": 50,
                "usage_turn_output_tokens_cumulative": 5,
            },
        },
        {
            "type": "function_call",
            "call_id": "call_1",
            "name": "lookup",
            "arguments": "{}",
            "_metadata": {
                "turn": {"id": 1, "has_tool_calls": True, "is_terminal": False}
            },
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "done"}],
            "_metadata": {
                "turn": {"id": 1, "has_tool_calls": False, "is_terminal": True},
                "usage_turn_input_tokens_cumulative": 200,
                "usage_turn_output_tokens_cumulative": 80,
            },
        },
    ]
    final_messages = [native_messages[-1]]

    from unittest.mock import patch

    with patch(
        "timestamp_extension.duration_extension.time.monotonic", return_value=100.2
    ):
        stamped_finals, stamped_history, _state = ext.finalize(
            final_messages,
            native_messages,
            state,
        )

    md = stamped_finals[0].get("_metadata") or {}
    assert md.get("duration_ms") == 200
    assert md.get("turn_duration_ms") == 323
    assert md.get("total_duration_ms") == 323
    assert md.get("turn_tps") == pytest.approx(80 / 0.323, rel=1e-9)
    assert md.get("turn_tps_formatted") == "247.68"

    core_messages = [{"role": "assistant", "content": "done", "metadata": {}}]
    rebuilt = ext.from_native_messages(stamped_finals, core_messages)
    rebuilt_md = rebuilt[0].get("metadata") or {}
    assert rebuilt_md.get("turn_duration_ms") == 323
    assert rebuilt_md.get("turn_tps_formatted") == "247.68"


def test_turn_tps_falls_back_to_input_tokens_when_output_total_is_missing() -> None:
    ext = DurationExtension()

    state = {
        "_duration_extension": {
            "duration_started_at": "2024-01-01T00:00:00+00:00",
            "duration_started_at_mono": 50.0,
        }
    }

    native_messages = [
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "done"}],
            "_metadata": {
                "turn": {"id": 1, "has_tool_calls": False, "is_terminal": True},
                "usage_turn_input_tokens_cumulative": 120,
            },
        },
    ]

    from unittest.mock import patch

    with patch(
        "timestamp_extension.duration_extension.time.monotonic", return_value=50.3
    ):
        stamped_finals, _stamped_history, _state = ext.finalize(
            native_messages,
            native_messages,
            state,
        )

    md = stamped_finals[0].get("_metadata") or {}
    duration_ms = md.get("turn_duration_ms")
    assert isinstance(duration_ms, int)
    assert md.get("turn_tps") == pytest.approx((120 * 1000.0) / duration_ms, rel=1e-9)
    assert md.get("turn_tps_formatted") == "401.34"


def test_from_native_messages_uses_native_indices_for_responses_segments() -> None:
    ext = DurationExtension()

    native_messages = [
        {
            "type": "function_call",
            "call_id": "call_1",
            "name": "lookup",
            "arguments": "{}",
            "_metadata": {
                "turn": {"id": 2, "has_tool_calls": True, "is_terminal": False}
            },
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": ""}],
            "_metadata": {
                "duration_started_at": "2024-01-01T00:00:00+00:00",
                "duration_finished_at": "2024-01-01T00:00:02+00:00",
                "duration_ms": 2000,
                "duration_formatted": "2s",
                "turn_duration_ms": 3500,
                "turn_duration_formatted": "3.5s",
                "total_duration_ms": 7000,
                "total_duration_formatted": "7s",
                "turn_tps": 12.0,
                "turn_tps_formatted": "12",
                "turn": {"id": 2, "has_tool_calls": False, "is_terminal": True},
            },
        },
        {
            "type": "function_call_output",
            "call_id": "call_1",
            "output": "ok",
            "_metadata": {
                "turn": {"id": 2, "has_tool_calls": False, "is_terminal": True}
            },
        },
    ]

    messages = [
        {
            "role": "assistant",
            "content": "",
            "metadata": {"native_indices": [0, 1, 2]},
        },
        {
            "role": "tool",
            "content": "ok",
            "metadata": {"native_indices": [2]},
        },
    ]

    rebuilt = ext.from_native_messages(native_messages, messages)
    assistant_md = rebuilt[0].get("metadata") or {}
    assert assistant_md.get("duration_ms") == 2000
    assert assistant_md.get("duration_formatted") == "2s"
    assert assistant_md.get("turn_duration_ms") == 3500
    assert assistant_md.get("turn_duration_formatted") == "3.5s"
    assert assistant_md.get("total_duration_ms") == 7000
    assert assistant_md.get("total_duration_formatted") == "7s"
    assert assistant_md.get("turn_tps_formatted") == "12"

    tool_md = rebuilt[1].get("metadata") or {}
    assert "duration_ms" not in tool_md


def test_finalize_stamps_duration_on_tool_only_response_owner() -> None:
    ext = DurationExtension()
    state = {
        "_duration_extension": {
            "duration_started_at": "2024-01-01T00:00:00+00:00",
            "duration_started_at_mono": 10.0,
        }
    }

    final_messages = [
        {
            "type": "function_call",
            "call_id": "call_1",
            "name": "shell_command",
            "arguments": "{}",
            "_metadata": {
                "turn": {"id": 3, "has_tool_calls": True, "is_terminal": False}
            },
        },
        {
            "type": "function_call",
            "call_id": "call_2",
            "name": "shell_command",
            "arguments": "{}",
            "_metadata": {
                "usage": {"input_tokens": 10, "output_tokens": 4},
                "turn": {"id": 3, "has_tool_calls": True, "is_terminal": False},
                "usage_turn_output_tokens_cumulative": 4,
            },
        },
    ]
    native_messages = list(final_messages)

    from unittest.mock import patch

    with patch(
        "timestamp_extension.duration_extension.time.monotonic", return_value=10.5
    ):
        stamped_finals, stamped_history, _state = ext.finalize(
            final_messages,
            native_messages,
            state,
        )

    assert "_metadata" in stamped_finals[1]
    md = stamped_finals[1].get("_metadata") or {}
    assert md.get("duration_ms") == 500
    assert md.get("duration_formatted") == "500ms"
    assert md.get("turn_duration_ms") == 500
    assert md.get("total_duration_ms") == 500
    assert md.get("turn_tps_formatted") == "8"

    history_md = stamped_history[1].get("_metadata") or {}
    assert history_md.get("duration_ms") == 500

    rebuilt = ext.from_native_messages(
        stamped_finals,
        [
            {
                "role": "assistant",
                "content": "",
                "metadata": {"native_indices": [0, 1]},
            }
        ],
    )
    rebuilt_md = rebuilt[0].get("metadata") or {}
    assert rebuilt_md.get("duration_ms") == 500
    assert rebuilt_md.get("total_duration_ms") == 500


def test_turn_duration_accumulates_prior_tool_only_response_duration() -> None:
    ext = DurationExtension()
    state = {
        "_duration_extension": {
            "duration_started_at": "2024-01-01T00:00:00+00:00",
            "duration_started_at_mono": 20.0,
        }
    }

    native_messages = [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "hi"}],
        },
        {
            "type": "function_call",
            "call_id": "call_prev",
            "name": "shell_command",
            "arguments": "{}",
            "_metadata": {
                "duration_ms": 1200,
                "turn_duration_ms": 1200,
                "turn": {"id": 4, "has_tool_calls": True, "is_terminal": False},
                "usage_turn_output_tokens_cumulative": 12,
            },
        },
        {
            "type": "function_call",
            "call_id": "call_cur",
            "name": "shell_command",
            "arguments": "{}",
            "_metadata": {
                "usage": {"input_tokens": 20, "output_tokens": 6},
                "turn": {"id": 4, "has_tool_calls": True, "is_terminal": False},
                "usage_turn_output_tokens_cumulative": 18,
            },
        },
    ]
    final_messages = [native_messages[-1]]

    from unittest.mock import patch

    with patch(
        "timestamp_extension.duration_extension.time.monotonic", return_value=20.8
    ):
        stamped_finals, _stamped_history, _state = ext.finalize(
            final_messages,
            native_messages,
            state,
        )

    md = stamped_finals[0].get("_metadata") or {}
    assert md.get("duration_ms") == 800
    assert md.get("turn_duration_ms") == 2000
    assert md.get("total_duration_ms") == 2000
    assert md.get("turn_tps_formatted") == "9"


def test_session_total_ignores_unowned_duration_metadata() -> None:
    ext = DurationExtension()
    state = {
        "_duration_extension": {
            "duration_started_at": "2024-01-01T00:00:00+00:00",
            "duration_started_at_mono": 30.0,
        }
    }
    native_messages = [
        {
            "role": "assistant",
            "content": "prior",
            "_metadata": {
                "duration_ms": 125,
                "turn_duration_ms": 125,
            },
        },
        {
            "role": "tool",
            "content": "tool result",
            "_metadata": {
                "duration_ms": 900,
                "duration_formatted": "900ms",
            },
        },
        {
            "role": "assistant",
            "content": "current",
            "_metadata": {},
        },
    ]

    from unittest.mock import patch

    with patch(
        "timestamp_extension.duration_extension.time.monotonic", return_value=30.2
    ):
        stamped_finals, _stamped_history, _state = ext.finalize(
            [native_messages[-1]],
            native_messages,
            state,
        )

    md = stamped_finals[0].get("_metadata") or {}
    current_duration_ms = md.get("duration_ms")
    assert isinstance(current_duration_ms, int)
    assert md.get("total_duration_ms") == 125 + current_duration_ms
    assert md.get("total_duration_formatted") == (f"{125 + current_duration_ms}ms")


def test_session_total_ignores_malformed_owned_duration_values() -> None:
    ext = DurationExtension()
    native_history = [
        {"_metadata": {"duration_ms": True, "turn_duration_ms": 1}},
        {"_metadata": {"duration_ms": "100", "turn_duration_ms": 100}},
        {"_metadata": {"duration_ms": float("inf"), "turn_duration_ms": 100}},
        {"_metadata": {"duration_ms": -10, "turn_duration_ms": 100}},
        {"_metadata": {"duration_ms": 25.9, "turn_duration_ms": 100}},
    ]

    assert ext._sum_session_duration_ms(native_history) == 25


def test_ui_elements_control_message_footers_and_status_total_independently() -> None:
    ext = DurationExtension()
    schema = ext.get_config_schema()
    assert schema["duration_extension_show_status_total"]["default"] is True

    default_elements = ext.get_ui_elements(config=None)
    assert any(el.get("ui_type") == "config" for el in default_elements)
    assert any(el.get("ui_type") == "message_footer" for el in default_elements)
    assert any(
        el.get("ui_type") == "status_bar"
        and el.get("data") == "metadata.total_duration_formatted"
        and el.get("template") == "Total duration: {{data}}"
        for el in default_elements
    )

    disabled_elements = ext.get_ui_elements(
        config={"duration_extension_show_duration": False}
    )
    assert any(el.get("ui_type") == "config" for el in disabled_elements)
    assert not any(el.get("ui_type") == "message_footer" for el in disabled_elements)
    assert any(el.get("ui_type") == "status_bar" for el in disabled_elements)

    footer_only_elements = ext.get_ui_elements(
        config={"duration_extension_show_status_total": False}
    )
    assert any(el.get("ui_type") == "message_footer" for el in footer_only_elements)
    assert not any(el.get("ui_type") == "status_bar" for el in footer_only_elements)

    aggregated_elements = _make_core().get_ui_schema({"model": "test-model"})
    assert any(
        el.get("ui_type") == "status_bar"
        and el.get("plugin") == "duration_extension"
        and el.get("data") == "metadata.total_duration_formatted"
        for el in aggregated_elements
    )
