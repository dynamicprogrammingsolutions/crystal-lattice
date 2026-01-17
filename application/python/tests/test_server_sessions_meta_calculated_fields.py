"""Server-level tests for session-list calculated meta fields.

These tests verify that application-level plugins with ``trigger="session_list"``
are invoked when serving ``/sessions`` and that their returned
``session_list_fields`` are merged into the session summaries.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import json

from fastapi import FastAPI
from fastapi.testclient import TestClient

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore

from agent_terminal_app import server as server_mod


def _make_config_with_message_count(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "plugins.session_message_count_meta_app.SessionMessageCountMetaAppPlugin",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {},
    }

    path = tmp_path / "config_server_sessions_meta.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    cfg_path = _make_config_with_message_count(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(cfg_path), str(session_root), event_store=events)


def _create_session_with_messages(app: AgentApplication, contents: List[str]) -> str:
    from agent_core import AgentCore

    core, base_config, session = app.create_session("default")
    assert isinstance(core, AgentCore)

    for text in contents:
        session = core.add_message(session, "user", text, None, base_config)

    app.save_session(session)
    return session.session_id


def test_sessions_include_message_count_from_triggered_action(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    # Create a couple of sessions with different message counts.
    session_id_1 = _create_session_with_messages(app, ["one", "two"])
    session_id_2 = _create_session_with_messages(app, ["alpha", "beta", "gamma"])

    # Inject the app instance into the server module.
    server_mod._agent_app = app  # type: ignore[assignment]
    fastapi_app: FastAPI = server_mod.app
    client = TestClient(fastapi_app)

    resp = client.get("/sessions")
    assert resp.status_code == 200
    body = resp.json()
    sessions = body.get("sessions") or []

    by_id = {s["session_id"]: s for s in sessions}
    assert session_id_1 in by_id
    assert session_id_2 in by_id

    assert by_id[session_id_1].get("message_count") == 2
    assert by_id[session_id_2].get("message_count") == 3
