"""Tests for the summarize_range application action via server endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import sys

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


def _make_config_with_summarize_range(tmp_path: Path) -> Path:
    """Return a config path wiring SummarizeRangeAppPlugin into the app."""

    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
        "plugins": {
            "providers": [
                "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            ],
            "features": [],
            "tools": [],
            "extensions": [],
        },
        "agents": {
            "default": {"provider": "echo"},
        },
        "application_plugins": [
            "plugins.summarize_range_app.SummarizeRangeAppPlugin",
        ],
        "application": {
            "summarize_range_agent_id": "default",
            "summarize_range_prompt": "Summarize this range succinctly.",
        },
    }

    path = tmp_path / "config_server_summarize_range.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    from agent_terminal_app import server as server_mod

    config_path = _make_config_with_summarize_range(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Ensure the server uses this application instance when needed.
    server_mod._agent_app = app
    return app


def test_server_actions_summarize_range_modifies_session(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    # Create a session and seed a few user messages.
    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    for text in ["m0", "m1", "m2", "m3"]:
        server_mod.add_message(
            session_id,
            {"role": "user", "content": text, "metadata": None},
            app_instance=app,
        )

    resp = server_mod.execute_action(
        {
            "plugin": "summarize_range",
            "action_id": "summarize_range",
            "inputs": {"session_id": session_id, "start": 1, "end": 3},
        },
        app_instance=app,
    )

    assert resp["status"] == "ok"
    assert resp["plugin"] == "summarize_range"
    assert resp["action_id"] == "summarize_range"

    result = resp.get("result") or {}
    assert result.get("updated_session_ids") == [session_id]

    # Reload messages via the messages endpoint and verify the range was
    # collapsed into a single assistant summary message.
    msg_resp = server_mod.list_session_messages(session_id, app_instance=app)
    messages = msg_resp.get("messages") or []

    assert len(messages) == 3
    roles = [m["message"]["role"] for m in messages]
    contents = [m["message"]["content"] for m in messages]

    assert roles[0] == "user"
    assert roles[2] == "user"
    assert contents[0] == "m0"
    assert contents[2] == "m3"
    assert roles[1] == "assistant"
    assert isinstance(contents[1], str) and contents[1]


def test_server_actions_summarize_range_validation_error_bubbles(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # Seed a couple of messages so that an invalid range can be detected.
    for text in ["one", "two"]:
        server_mod.add_message(
            session_id,
            {"role": "user", "content": text, "metadata": None},
            app_instance=app,
        )

    # Use an inverted range so that the underlying helper raises ValueError.
    resp = server_mod.execute_action(
        {
            "plugin": "summarize_range",
            "action_id": "summarize_range",
            "inputs": {"session_id": session_id, "start": 5, "end": 1},
        },
        app_instance=app,
    )

    assert resp["status"] == "error"
    assert resp["error_type"] == "validation"
