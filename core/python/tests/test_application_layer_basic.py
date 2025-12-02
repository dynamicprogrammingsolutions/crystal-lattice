"""Basic tests for the future application layer wrapper around AgentCore.

These tests exercise :mod:`agent_app.application_future` instead of the
original, dict-based application layer. They use the typed
``create_session`` helper and the ``send_request`` event
iterator.
"""

from __future__ import annotations

from pathlib import Path

from agent_app.application_future import AgentApplication
from agent_core import AgentCore
from .dummy_provider import DummyProvider  # noqa: F401  (imported for side effects)


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


def test_create_session_and_persist(tmp_path: Path) -> None:
    config_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    # Session file should exist on disk
    path = session_root / f"{session_id}.json"
    assert path.exists()


def test_add_message_updates_session(tmp_path: Path) -> None:
    config_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")

    # Add a user message via the core-first API.
    new_session = core.add_message(session, "user", "Hello")
    app.save_session(new_session)

    as_dict = new_session.to_dict()
    assert len(as_dict["messages"]) == 1
    assert as_dict["messages"][0]["role"] == "user"
    assert as_dict["messages"][0]["content"] == "Hello"


def test_send_request_non_streaming(tmp_path: Path) -> None:
    config_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "Hi")

    final_messages: list[dict] = []

    # Use the new core-first event iterator instead of the legacy
    # dict-based send_request API.
    for ev in app.send_request(core, session, base_config, overrides=None, stream=False):
        if ev.get("type") == "final":
            final_messages = list(ev.get("messages") or [])

    assert final_messages, "expected at least one final message"
    last = final_messages[-1]
    assert last["role"] == "assistant"
    assert "Echo: Hi" in last.get("content", "")
