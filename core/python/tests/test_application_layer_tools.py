"""Tool loop behaviour tests for the application layer."""

from __future__ import annotations

import json
from pathlib import Path

from agent_app import AgentApplication
from agent_core import AgentCore
from .dummy_tool import DummyCalculator


def _make_tool_config(tmp_path: Path) -> Path:
    # Use DummyProvider plus the OpenAI tools extension to surface tool_calls
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


def test_execute_tool_calls_non_streaming(tmp_path):
    config_path = _make_tool_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    created = app.create_session({"agent_id": "default"})
    session_id = created["session"]["session_id"]

    # Simulate a tool call by adding an assistant message with tool_calls metadata
    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "add", "arguments": json.dumps({"a": 2, "b": 3})},
    }
    app.add_message(
        {
            "session_id": session_id,
            "message": {
                "role": "assistant",
                "content": "",
                "metadata": {"tool_calls": [tool_call]},
            },
        }
    )

    result = app.send_request({"session_id": session_id, "stream": False})

    # Tool result should have been appended as a tool message in the session
    new_session = result["session"]
    tool_messages = [m for m in new_session["messages"] if m["role"] == "tool"]
    assert tool_messages
    assert "Result:" in tool_messages[-1]["content"]


def test_execute_tool_calls_streaming(tmp_path):
    config_path = _make_tool_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    created = app.create_session({"agent_id": "default"})
    session_id = created["session"]["session_id"]

    tool_call = {
        "id": "call_1",
        "type": "function",
        "function": {"name": "add", "arguments": json.dumps({"a": 1, "b": 4})},
    }
    app.add_message(
        {
            "session_id": session_id,
            "message": {
                "role": "assistant",
                "content": "",
                "metadata": {"tool_calls": [tool_call]},
            },
        }
    )

    started = app.send_request({"session_id": session_id, "stream": True})
    request_id = started["request_id"]

    # Poll events until request_completed
    since_id = None
    import time

    tool_results_seen = False
    start = time.time()
    while time.time() - start < 5.0:
        batch = app.get_events({"since_id": since_id, "request_id": request_id})["events"]
        if batch:
            since_id = batch[-1]["event_id"]
        for ev in batch:
            if ev["type"] == "tool_results":
                tool_results_seen = True
        if any(ev["type"] == "request_completed" for ev in batch):
            break
        time.sleep(0.01)

    assert tool_results_seen
