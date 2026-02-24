from __future__ import annotations

from typing import Any, Dict

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
    assert isinstance(md.get("duration_finished_at"), str) and md["duration_finished_at"]
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
    assert "turn_duration_ms" not in tool_call_msg.metadata
    assert "turn_duration_formatted" not in tool_call_msg.metadata

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
    assert internal_md.get("turn_duration_ms") == seeded_duration_ms + current_duration_ms
