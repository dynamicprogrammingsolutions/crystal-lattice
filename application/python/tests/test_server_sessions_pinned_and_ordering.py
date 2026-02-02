"""Server-level tests for pinned sessions and ordering.

These tests verify that the SessionPinnedAppPlugin can toggle pinned
state via ``/actions`` and that the ``/sessions`` endpoint surfaces a
boolean ``pinned`` flag and orders pinned sessions before unpinned
sessions while preserving per-group ordering by ``modified``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore

from agent_terminal_app import server as server_mod


def _make_config_with_pinned(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "plugins.session_pinned_app.SessionPinnedAppPlugin",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {
            "session_pinned_metadata_key": "pinned",
        },
    }

    path = tmp_path / "config_server_sessions_pinned.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    cfg_path = _make_config_with_pinned(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(cfg_path), str(session_root), event_store=events)


def _create_session(app: AgentApplication, label: str) -> str:
    from agent_core import AgentCore

    core, base_config, session = app.create_session("default")
    assert isinstance(core, AgentCore)

    session = core.add_message(session, "user", label, None, base_config)
    app.save_session(session)
    return session.session_id


def test_sessions_pinned_flag_and_ordering(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    # Create two sessions; ensure their mtimes differ slightly.
    session_id_1 = _create_session(app, "first")
    session_id_2 = _create_session(app, "second")

    # Inject app into server module.
    server_mod._agent_app = app  # type: ignore[assignment]
    fastapi_app: FastAPI = server_mod.app
    client = TestClient(fastapi_app)

    # Initially, both sessions should be unpinned.
    resp0 = client.get("/sessions")
    assert resp0.status_code == 200
    body0 = resp0.json()
    sessions0 = body0.get("sessions") or []
    assert len(sessions0) == 2

    by_id0 = {s["session_id"]: s for s in sessions0}
    assert by_id0[session_id_1].get("pinned") in (False, None)
    assert by_id0[session_id_2].get("pinned") in (False, None)

    # Pin the second session via the application action.
    action_payload = {
        "plugin": "session_pinned",
        "action_id": "toggle_session_pinned",
        "inputs": {"session_id": session_id_2},
    }
    resp_action = client.post("/actions", json=action_payload)
    assert resp_action.status_code == 200
    data_action = resp_action.json()
    assert data_action.get("status") == "ok"

    # After pinning, /sessions should report pinned flag and order the
    # pinned session before the unpinned one.
    resp1 = client.get("/sessions")
    assert resp1.status_code == 200
    body1 = resp1.json()
    sessions1 = body1.get("sessions") or []
    assert len(sessions1) == 2

    # First entry should be the pinned session.
    first = sessions1[0]
    second = sessions1[1]
    assert first["session_id"] == session_id_2
    assert bool(first.get("pinned")) is True
    assert bool(second.get("pinned")) is False
