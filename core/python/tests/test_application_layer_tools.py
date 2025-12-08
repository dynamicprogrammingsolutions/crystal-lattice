"""Tool loop behaviour tests for the future application layer.

These tests exercise :mod:`agent_app.application_future` and its
``send_request`` helper instead of the legacy dict-based API.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from agent_app.application_future import AgentApplication
from agent_core import AgentCore
from .dummy_tool import DummyCalculator  # noqa: F401  (imported for side effects)


def _make_tool_config(tmp_path: Path) -> Path:
    # Use DummyProvider plus DummyCalculator tool to surface tool_calls.
    cfg = {
        "providers": {
            "dummy": {"provider": "dummy_provider", "model": "test-model"}
        },
        "plugins": {
            "providers": ["tests.dummy_provider.DummyProvider"],
            "tools": ["tests.dummy_tool.DummyCalculator"],
        },
        "agents": {
            "default": {"provider": "dummy"},
        },
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def test_execute_tool_calls_non_streaming(tmp_path: Path) -> None:
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

    events = list(app.send_request(core, session, base_config, overrides=None, stream=False))

    # Ensure no streaming tool events were produced in non-streaming mode.
    assert not any(ev["type"] == "tool_partial" for ev in events)

    # Find the latest session snapshot from events.
    final_session_dict: Dict[str, object] | None = None
    for ev in events:
        sess = ev.get("session")  # type: ignore[assignment]
        if isinstance(sess, dict):
            final_session_dict = sess  # type: ignore[assignment]

    assert final_session_dict is not None
    messages: List[Dict[str, object]] = list(final_session_dict["messages"])  # type: ignore[index]
    tool_messages = [m for m in messages if m.get("role") == "tool"]
    assert tool_messages
    assert "Result:" in str(tool_messages[-1].get("content", ""))


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

    events = list(app.send_request(core, session, base_config, overrides=None, stream=True))

    # Streaming path should surface both partials and final tool_results.
    partial_events = [ev for ev in events if ev.get("type") == "tool_partial"]
    assert partial_events
    assert any(
        isinstance(ev.get("payload"), dict)
        and "part" in (ev.get("payload") or {})
        for ev in partial_events
    )
    assert any(ev.get("type") == "tool_results" for ev in events)
