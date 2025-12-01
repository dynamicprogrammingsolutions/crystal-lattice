"""Basic tests for the application layer wrapper around AgentCore."""

from __future__ import annotations

import os
from pathlib import Path

from agent_app import AgentApplication
from agent_core import AgentCore
from .dummy_provider import DummyProvider


def _make_config(tmp_path: Path) -> Path:
    cfg = {
        "providers": {
            "dummy": {"provider": "dummy_provider", "model": "test-model"}
        },
        "plugins": {
            "providers": ["tests.dummy_provider.DummyProvider"],
        },
        "agents": {
            "default": {"provider": "dummy"},
        },
    }
    path = tmp_path / "config.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


def test_create_session_and_persist(tmp_path):
    config_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    result = app.create_session({"agent_id": "default"})
    session = result["session"]
    session_id = session["session_id"]

    # Session file should exist on disk
    path = session_root / f"{session_id}.json"
    assert path.exists()


def test_add_message_updates_session(tmp_path):
    config_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    created = app.create_session({"agent_id": "default"})
    session_id = created["session"]["session_id"]

    updated = app.add_message(
        {
            "session_id": session_id,
            "message": {"role": "user", "content": "Hello"},
        }
    )

    assert len(updated["session"]["messages"]) == 1


def test_send_request_non_streaming(tmp_path):
    config_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    created = app.create_session({"agent_id": "default"})
    session_id = created["session"]["session_id"]
    app.add_message({"session_id": session_id, "message": {"role": "user", "content": "Hi"}})

    result = app.send_request({"session_id": session_id, "stream": False})

    messages = result["messages"]
    assert messages
    assert messages[-1]["role"] == "assistant"
    assert "Echo: Hi" in messages[-1]["content"]
