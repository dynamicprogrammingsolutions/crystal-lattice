"""Tool loop behaviour tests for the future application layer.

These tests exercise :mod:`agent_app.application_future` and its
``send_request`` helper instead of the legacy dict-based API.
"""

from __future__ import annotations

import json
import pytest
from pathlib import Path
from types import SimpleNamespace
from typing import Dict

from agent_app.app_context import ApplicationContext
from agent_app.application_future import AgentApplication
from agent_app.tool_loop import ToolLoopRunner
from agent_core import AgentCore, Session
from .dummy_tool import DummyCalculator  # noqa: F401  (imported for side effects)


def _make_tool_config(tmp_path: Path) -> Path:
    # Use DummyProvider plus DummyCalculator tool to surface tool_calls.
    cfg = {
        "providers": {"dummy": {"provider": "dummy_provider", "model": "test-model"}},
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.dummy_tool.DummyCalculator",
        ],
        "agents": {
            "default": {"provider": "dummy"},
        },
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def test_execute_tool_calls_non_streaming(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    config_path = _make_tool_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")

    # Simulate a tool call by adding an assistant message with tool_calls metadata.
    tool_call: Dict[str, object] = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "add", "arguments": json.dumps({"a": 2, "b": 3})},
    }
    session = core.add_message(
        session,
        "assistant",
        "",
        {"tool_calls": [tool_call]},
    )
    app.save_session(session)

    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))

    # Ensure no streaming tool events were produced in non-streaming mode.
    assert not any(ev["type"] == "tool_partial" for ev in events)

    # Find the latest session checkpoint from events and inspect the
    # stored messages to verify that tool output was appended.
    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    assert checkpoints, "expected at least one session_checkpoint event"
    final_session = checkpoints[-1]["session"]
    assert isinstance(final_session, Session)

    messages = list(final_session.messages)
    tool_messages = [m for m in messages if getattr(m, "role", None) == "tool"]
    assert tool_messages
    assert "Result:" in str(getattr(tool_messages[-1], "content", ""))
    assert "context_reserved_key_clash_external" not in capsys.readouterr().out


def test_execute_tool_calls_streaming(tmp_path: Path) -> None:
    config_path = _make_tool_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")

    tool_call: Dict[str, object] = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "add", "arguments": json.dumps({"a": 1, "b": 4})},
    }
    session = core.add_message(
        session,
        "assistant",
        "",
        {"tool_calls": [tool_call]},
    )
    app.save_session(session)

    events = list(app.send_request(core, session, base_config, overrides=None, stream=True))

    # Streaming path should surface both partials and final tool_results.
    partial_events = [ev for ev in events if ev.get("type") == "tool_partial"]
    assert partial_events
    assert any(
        isinstance(ev.get("payload"), dict) and "part" in (ev.get("payload") or {})
        for ev in partial_events
    )
    assert any(ev.get("type") == "tool_results" for ev in events)


def test_pending_tool_calls_ignored_after_follow_up_user_message() -> None:
    core = AgentCore()
    runner = ToolLoopRunner(
        core=core,
        config={},
        request_id="req_pending",
        tool_loop_cfg=SimpleNamespace(max_loops=8),
        app_context=ApplicationContext(app=None),
        base_config={},
    )

    tool_call: Dict[str, object] = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "add", "arguments": json.dumps({"a": 2, "b": 3})},
    }

    session = core.create_session()
    session = core.add_message(session, "assistant", "", {"tool_calls": [tool_call]})
    session = core.add_message(session, "user", "Thanks, now answer directly.")

    assert runner._extract_pending_tool_calls_from_session(session) == []


def test_pending_tool_calls_returned_for_unresolved_tail_assistant() -> None:
    core = AgentCore()
    runner = ToolLoopRunner(
        core=core,
        config={},
        request_id="req_pending_tail",
        tool_loop_cfg=SimpleNamespace(max_loops=8),
        app_context=ApplicationContext(app=None),
        base_config={},
    )

    tool_call: Dict[str, object] = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "add", "arguments": json.dumps({"a": 2, "b": 3})},
    }

    session = core.create_session()
    session = core.add_message(session, "assistant", "", {"tool_calls": [tool_call]})

    assert runner._extract_pending_tool_calls_from_session(session) == [tool_call]
