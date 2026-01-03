"""Tests for the session_title application action via server endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import sys


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


def _make_config_with_session_title(tmp_path: Path) -> Path:
    """Return a config path wiring SessionTitleAppPlugin into the app."""

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
            "plugins.session_title_app.SessionTitleAppPlugin",
        ],
        "application": {},
    }

    path = tmp_path / "config_server_session_title.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    from agent_terminal_app import server as server_mod

    config_path = _make_config_with_session_title(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Ensure the server uses this application instance when needed.
    server_mod._agent_app = app
    return app


def test_server_actions_set_session_title_updates_metadata_and_sessions_list(
    tmp_path: Path,
) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    resp = server_mod.execute_action(
        {
            "plugin": "session_title",
            "action_id": "set_session_title",
            "inputs": {"session_id": session_id, "title": "Project planning"},
        },
        app_instance=app,
    )

    assert resp["status"] == "ok"
    assert resp["plugin"] == "session_title"
    assert resp["action_id"] == "set_session_title"

    result = resp.get("result") or {}
    assert result.get("updated_session_ids") == [session_id]

    sessions_resp = server_mod.list_sessions(app_instance=app)
    summaries = sessions_resp.get("sessions") or []
    entry = next(s for s in summaries if s.get("session_id") == session_id)
    metadata = entry.get("metadata") or {}
    assert metadata.get("title") == "Project planning"


def test_server_actions_set_session_title_clears_title(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    create_resp = server_mod.create_session({"agent_id": "default"}, app_instance=app)
    session_id = create_resp["session"]["session_id"]

    # Set an initial title.
    _ = server_mod.execute_action(
        {
            "plugin": "session_title",
            "action_id": "set_session_title",
            "inputs": {"session_id": session_id, "title": "Initial"},
        },
        app_instance=app,
    )

    # Clear the title via an empty string.
    resp = server_mod.execute_action(
        {
            "plugin": "session_title",
            "action_id": "set_session_title",
            "inputs": {"session_id": session_id, "title": "   "},
        },
        app_instance=app,
    )

    assert resp["status"] == "ok"

    sessions_resp = server_mod.list_sessions(app_instance=app)
    summaries = sessions_resp.get("sessions") or []
    entry = next(s for s in summaries if s.get("session_id") == session_id)
    metadata = entry.get("metadata") or {}
    assert "title" not in metadata


def test_application_ui_schema_includes_session_list_field_for_title(
    tmp_path: Path,
) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    resp = server_mod.list_application_ui_schema(app_instance=app)
    elements = resp.get("elements") or []

    title_fields = [
        el
        for el in elements
        if isinstance(el, dict)
        and el.get("plugin") == "session_title"
        and el.get("ui_type") == "session_list_field"
    ]

    assert title_fields
    # Default metadata key is "title".
    assert any(el.get("data") == "metadata.title" for el in title_fields)
