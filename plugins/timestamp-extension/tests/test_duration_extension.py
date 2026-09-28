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

    native_1 = session_1.metadata.get("native_messages") or []
    assert native_1
    assert native_1[-1].get("role") == "assistant"
    internal_md = native_1[-1].get("_metadata") or {}
    assert internal_md.get("duration_ms") == md["duration_ms"]
    assert internal_md.get("turn_duration_ms") == md["turn_duration_ms"]

    # Appending a new message rebuilds core history from native history.
    session_2 = core.add_message(session_1, "user", "next", config=config)
    assistant_msgs = [msg for msg in session_2.messages if msg.role == "assistant"]
    assert assistant_msgs
    assert assistant_msgs[-1].metadata
    assert assistant_msgs[-1].metadata.get("duration_ms") == md["duration_ms"]
    assert assistant_msgs[-1].metadata.get("turn_duration_ms") == md["turn_duration_ms"]


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
    assert md.get("turn_tps_formatted") == "8"

    history_md = stamped_history[1].get("_metadata") or {}
    assert history_md.get("duration_ms") == 500


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
    assert md.get("turn_tps_formatted") == "9"


def test_ui_elements_hide_message_footers_when_disabled() -> None:
    ext = DurationExtension()

    default_elements = ext.get_ui_elements(config=None)
    assert any(el.get("ui_type") == "config" for el in default_elements)
    assert any(el.get("ui_type") == "message_footer" for el in default_elements)

    disabled_elements = ext.get_ui_elements(
        config={"duration_extension_show_duration": False}
    )
    assert any(el.get("ui_type") == "config" for el in disabled_elements)
    assert not any(el.get("ui_type") == "message_footer" for el in disabled_elements)


# ---------------------------------------------------------------------------
# finalize_tool_call: per-call and per-turn tool duration stamping
# ---------------------------------------------------------------------------


def _tool_call_context(
    session_messages: list | None = None,
    *,
    started_mono: float = 10.0,
    finished_mono: float = 10.5,
) -> Dict[str, Any]:
    context: Dict[str, Any] = {
        "tool_call_id": "call_cur",
        "tool_name": "add",
        "started_at": "2024-01-01T00:00:00+00:00",
        "started_at_mono": started_mono,
        "finished_at": "2024-01-01T00:00:01+00:00",
        "finished_at_mono": finished_mono,
    }
    if session_messages is not None:
        context["session"] = {"session_id": "s1", "messages": session_messages}
    return context


def test_finalize_tool_call_stamps_per_call_duration_from_context_facts() -> None:
    ext = DurationExtension()
    message = {
        "role": "tool",
        "content": "Result: 5",
        "metadata": {"tool_call_id": "call_cur", "tool_name": "add"},
    }

    stamped, _state = ext.finalize_tool_call(message, {}, context=_tool_call_context())

    md = stamped.get("metadata") or {}
    assert md.get("duration_ms") == 500
    assert md.get("duration_formatted") == "500ms"
    assert md.get("duration_started_at") == "2024-01-01T00:00:00+00:00"
    assert md.get("duration_finished_at") == "2024-01-01T00:00:01+00:00"
    # Existing metadata is preserved.
    assert md.get("tool_call_id") == "call_cur"
    assert md.get("tool_name") == "add"
    # No session in the context: no turn fields, no fabricated values.
    assert "turn_tool_duration_ms" not in md
    assert "turn_tool_duration_formatted" not in md


def test_finalize_tool_call_returns_message_unchanged_without_facts() -> None:
    ext = DurationExtension()
    message = {
        "role": "tool",
        "content": "Error: no tool handled 'x'",
        "metadata": {"tool_call_id": "c1"},
    }

    stamped, _state = ext.finalize_tool_call(message, {}, context={})
    assert stamped == message

    malformed = {
        "started_at_mono": "not-a-number",
        "finished_at_mono": None,
        "tool_error": "no tool handled 'x'",
    }
    stamped, _state = ext.finalize_tool_call(message, {}, context=malformed)
    assert stamped == message


def test_finalize_tool_call_stamps_only_per_call_fields() -> None:
    ext = DurationExtension()
    session_messages = [
        {"role": "user", "content": "hi"},
        {
            "role": "tool",
            "content": "r1",
            "metadata": {"tool_call_id": "c1", "duration_ms": 1200},
        },
    ]
    message = {
        "role": "tool",
        "content": "r2",
        "metadata": {"tool_call_id": "call_cur"},
    }

    stamped, _state = ext.finalize_tool_call(
        message, {}, context=_tool_call_context(session_messages)
    )

    md = stamped.get("metadata") or {}
    assert md.get("duration_ms") == 500
    # The per-turn tool total lives on the assistant message, not on the
    # tool-result message.
    assert "turn_tool_duration_ms" not in md
    assert "turn_tool_duration_formatted" not in md


def _assistant_finalize_with_tool_history(
    tool_durations_ms: list[int],
    *,
    separator: str | None = None,
    assistant_llm_duration_ms: int | None = None,
) -> Dict[str, Any]:
    """Run finalize for one assistant final over a native history.

    The history contains, per entry in ``tool_durations_ms``, an assistant
    message with tool calls followed by a tool result carrying that
    duration. ``separator`` inserts a user message before the tools when
    given (to model a turn boundary).
    """

    native_history: list[Dict[str, Any]] = [{"role": "user", "content": "hi"}]
    if separator == "user":
        native_history.append({"role": "user", "content": "new turn"})
    if separator == "assistant":
        native_history.append({"role": "assistant", "content": "done", "_metadata": {}})
    for idx, duration_ms in enumerate(tool_durations_ms):
        native_history.append(
            {
                "role": "assistant",
                "content": f"call {idx}",
                "tool_calls": [{"id": f"c{idx}", "function": {"name": "add"}}],
                "_metadata": {"tool_calls": [{"id": f"c{idx}"}]},
            }
        )
        native_history.append(
            {
                "role": "tool",
                "content": f"r{idx}",
                "_metadata": {"duration_ms": duration_ms},
            }
        )
    if assistant_llm_duration_ms is not None:
        # An assistant LLM duration must not leak into the tool turn.
        native_history.append(
            {
                "role": "assistant",
                "content": "thinking",
                "tool_calls": [{"id": "cx", "function": {"name": "add"}}],
                "_metadata": {
                    "tool_calls": [{"id": "cx"}],
                    "duration_ms": assistant_llm_duration_ms,
                },
            }
        )

    # The provider-native history passed to finalize includes the final
    # assistant message at its tail; history_before_current excludes it.
    final_message = {"role": "assistant", "content": "done", "_metadata": {}}
    native_history.append(dict(final_message))

    final_messages = [final_message]
    state: Dict[str, Any] = {
        "_duration_extension": {
            "duration_started_at": "2024-01-01T00:00:00+00:00",
            "duration_started_at_mono": 10.0,
        }
    }
    ext = DurationExtension()
    stamped_finals, _stamped_history, _state = ext.finalize(
        final_messages, native_history, state
    )
    return stamped_finals[-1].get("_metadata") or {}


def test_finalize_stamps_turn_tool_duration_on_assistant() -> None:
    md = _assistant_finalize_with_tool_history([1200, 300])

    assert md.get("turn_tool_duration_ms") == 1500
    assert md.get("turn_tool_duration_formatted") == "1.5s"


def test_finalize_turn_tool_duration_resets_after_user_message() -> None:
    md = _assistant_finalize_with_tool_history(
        [500], separator="user", assistant_llm_duration_ms=None
    )
    # Only the tool after the user separator counts.
    assert md.get("turn_tool_duration_ms") == 500


def test_finalize_turn_tool_duration_resets_after_terminal_assistant() -> None:
    md = _assistant_finalize_with_tool_history([500], separator="assistant")
    assert md.get("turn_tool_duration_ms") == 500


def test_finalize_turn_tool_duration_ignores_assistant_llm_durations() -> None:
    md = _assistant_finalize_with_tool_history([200], assistant_llm_duration_ms=4000)
    assert md.get("turn_tool_duration_ms") == 200


def test_finalize_turn_tool_duration_without_tools_is_absent() -> None:
    md = _assistant_finalize_with_tool_history([])
    # No tool calls in the turn: no turn tool duration stamp (no 0ms noise).
    assert "turn_tool_duration_ms" not in md
    assert "turn_tool_duration_formatted" not in md


def test_finalize_turn_tool_duration_skips_malformed_values() -> None:
    md = _assistant_finalize_with_tool_history([250, "not-a-number"])
    assert md.get("turn_tool_duration_ms") == 250


def test_ui_elements_footer_order() -> None:
    ext = DurationExtension()
    elements = ext.get_ui_elements(config=None)
    footers = [
        (el.get("data"), el.get("template"))
        for el in elements
        if el.get("ui_type") == "message_footer"
    ]
    # The per-call duration footer also renders on tool messages.
    assert ("metadata.duration_formatted", "duration: {{data}}") in footers
    # The turn tool total renders on assistant messages, after turn duration.
    assert (
        "metadata.turn_tool_duration_formatted",
        "turn tool duration: {{data}}",
    ) in footers
    # The rendered order is the element list order.
    assert footers == [
        ("metadata.duration_formatted", "duration: {{data}}"),
        ("metadata.turn_duration_formatted", "turn duration: {{data}}"),
        ("metadata.turn_tool_duration_formatted", "turn tool duration: {{data}}"),
        ("metadata.turn_tps_formatted", "turn TPS: {{data}}"),
    ]

    disabled = ext.get_ui_elements(config={"duration_extension_show_duration": False})
    assert not any(el.get("ui_type") == "message_footer" for el in disabled)


def test_from_native_messages_projects_tool_duration_fields() -> None:
    ext = DurationExtension()
    native_messages = [
        {
            "role": "tool",
            "content": "ok",
            "_metadata": {
                "tool_call_id": "c1",
                "duration_ms": 500,
                "duration_formatted": "500ms",
                "duration_started_at": "2024-01-01T00:00:00+00:00",
                "duration_finished_at": "2024-01-01T00:00:01+00:00",
                "turn_tool_duration_ms": 800,
                "turn_tool_duration_formatted": "800ms",
            },
        }
    ]
    messages = [{"role": "tool", "content": "ok", "metadata": {"tool_call_id": "c1"}}]

    rebuilt = ext.from_native_messages(native_messages, messages)

    md = rebuilt[0].get("metadata") or {}
    assert md.get("duration_ms") == 500
    assert md.get("duration_formatted") == "500ms"
    assert md.get("turn_tool_duration_ms") == 800
    assert md.get("turn_tool_duration_formatted") == "800ms"
