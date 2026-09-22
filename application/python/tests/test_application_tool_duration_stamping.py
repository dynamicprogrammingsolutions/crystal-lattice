"""Application-layer integration tests for tool-call duration stamping.

Exercises the realistic public flow: an ``AgentApplication`` request whose
session tail carries pending tool calls runs the tool loop, and the
``DurationExtension`` feature stamps per-call and per-turn tool duration on
the tool-result messages through the ``finalize_tool_call`` hook. The stamps
must flow to frontends through the existing tool events and survive a
session reload (provider-native history round-trip).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import AgentCore, Session


def _make_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {
                "provider": "echo_openai_like",
                "model": "test-model",
            }
        },
        "agents": {
            "default": {
                "provider": "echo",
                "working_directory": str(tmp_path),
                "allowed_paths": [str(tmp_path)],
            }
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "plugins.file_reader_tool.FileReaderTool",
            "timestamp_extension.duration_extension.DurationExtension",
        ],
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(cfg), encoding="utf-8")
    return config_path


def _make_app(tmp_path: Path) -> AgentApplication:
    config_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"
    return AgentApplication(
        str(config_path),
        str(session_root),
        core_factory=AgentCore,
        event_store=InMemoryEventStore(),
    )


def _read_file_call(call_id: str, path: Path) -> Dict[str, Any]:
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": "read_file",
            "arguments": json.dumps({"file_path": str(path)}),
        },
    }


def _seed_pending_tool_calls(
    app: AgentApplication,
    core: AgentCore,
    session: Session,
    tool_calls: List[Dict[str, Any]],
) -> Session:
    session = core.add_message(
        session,
        "assistant",
        "",
        {"tool_calls": tool_calls},
    )
    app.save_session(session)
    return session


def _tool_messages(session: Session) -> List[Any]:
    return [m for m in session.messages if getattr(m, "role", None) == "tool"]


def test_tool_duration_stamped_on_checkpoint_session_and_survives_reload(
    tmp_path: Path,
) -> None:
    app = _make_app(tmp_path)
    core, base_config, session = app.create_session("default")

    target = tmp_path / "hello.txt"
    target.write_text("hello", encoding="utf-8")
    session = _seed_pending_tool_calls(
        app, core, session, [_read_file_call("call_1", target)]
    )

    events = list(
        app.send_request(core, session, base_config, overrides=None, stream=False)
    )

    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    assert checkpoints, "expected at least one session_checkpoint event"
    final_session = checkpoints[-1]["session"]
    assert isinstance(final_session, Session)

    tool_msgs = _tool_messages(final_session)
    assert tool_msgs
    metadata = tool_msgs[-1].metadata or {}
    assert isinstance(metadata.get("tool_call_id"), str)
    assert isinstance(metadata.get("duration_ms"), int)
    assert metadata["duration_ms"] >= 0
    assert isinstance(metadata.get("duration_formatted"), str)
    assert metadata["duration_formatted"]
    assert isinstance(metadata.get("duration_started_at"), str)
    assert isinstance(metadata.get("duration_finished_at"), str)
    # Single call in the turn: the tool turn equals the call duration.
    assert metadata.get("turn_tool_duration_ms") == metadata["duration_ms"]

    # The stamps survive a save + reload (native-history round-trip).
    app.save_session(final_session)
    loaded = app.load_session(final_session.session_id)
    assert loaded is not None
    _core2, _config2, reloaded = loaded
    reloaded_tool_msgs = _tool_messages(reloaded)
    assert reloaded_tool_msgs
    reloaded_md = reloaded_tool_msgs[-1].metadata or {}
    assert reloaded_md.get("duration_ms") == metadata["duration_ms"]
    assert reloaded_md.get("turn_tool_duration_ms") == metadata["turn_tool_duration_ms"]
    assert reloaded_md.get("duration_formatted") == metadata["duration_formatted"]


def test_tool_duration_flows_through_streaming_tool_events(
    tmp_path: Path,
) -> None:
    app = _make_app(tmp_path)
    core, base_config, session = app.create_session("default")

    target = tmp_path / "hello.txt"
    target.write_text("hello", encoding="utf-8")
    session = _seed_pending_tool_calls(
        app, core, session, [_read_file_call("call_1", target)]
    )

    events = list(
        app.send_request(core, session, base_config, overrides=None, stream=True)
    )

    end_events = [
        ev
        for ev in events
        if ev.get("type") == "tool_partial" and ev.get("phase") == "end"
    ]
    assert end_events, "expected tool_partial end events in streaming mode"
    result = end_events[-1].get("payload", {}).get("result")
    assert isinstance(result, dict)
    metadata = result.get("metadata") or {}
    assert isinstance(metadata.get("duration_ms"), int)
    assert metadata["duration_ms"] >= 0
    assert isinstance(metadata.get("duration_formatted"), str)

    tool_results = [ev for ev in events if ev.get("type") == "tool_results"]
    assert tool_results
    results_messages = tool_results[-1].get("messages") or []
    assert results_messages
    results_md = results_messages[-1].get("metadata") or {}
    assert isinstance(results_md.get("duration_ms"), int)
    assert results_md.get("duration_ms") >= 0


def test_multiple_tool_calls_accumulate_turn_tool_duration(
    tmp_path: Path,
) -> None:
    app = _make_app(tmp_path)
    core, base_config, session = app.create_session("default")

    target_a = tmp_path / "a.txt"
    target_a.write_text("a", encoding="utf-8")
    target_b = tmp_path / "b.txt"
    target_b.write_text("b", encoding="utf-8")
    session = _seed_pending_tool_calls(
        app,
        core,
        session,
        [
            _read_file_call("call_1", target_a),
            _read_file_call("call_2", target_b),
        ],
    )

    events = list(
        app.send_request(core, session, base_config, overrides=None, stream=False)
    )

    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    final_session = checkpoints[-1]["session"]
    tool_msgs = _tool_messages(final_session)
    assert len(tool_msgs) == 2

    first_md = tool_msgs[0].metadata or {}
    second_md = tool_msgs[1].metadata or {}
    assert isinstance(first_md.get("duration_ms"), int)
    assert isinstance(second_md.get("duration_ms"), int)
    # The second call's tool turn is the sum of both calls' durations.
    assert (
        second_md.get("turn_tool_duration_ms")
        == first_md["duration_ms"] + second_md["duration_ms"]
    )
    assert first_md.get("turn_tool_duration_ms") == first_md["duration_ms"]
