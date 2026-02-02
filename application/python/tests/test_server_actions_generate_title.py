"""Tests for the generate_title application action via server endpoints."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

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


def _make_config_with_generate_title(tmp_path: Path) -> Path:
    """Return a config path wiring GenerateTitleAppPlugin into the app."""

    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "plugins.generate_title_app.GenerateTitleAppPlugin",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {
            "generate_title_agent_id": "default",
            "generate_title_prompt_template": "Generate a concise title.",
            "generate_title_max_messages": 10,
        },
    }

    path = tmp_path / "config_server_generate_title.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    from agent_terminal_app import server as server_mod

    config_path = _make_config_with_generate_title(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Ensure the server uses this application instance when needed.
    server_mod._agent_app = app
    return app


def _create_session_with_messages(app: AgentApplication, contents: List[str]) -> str:
    from agent_core import AgentCore

    core, base_config, session = app.create_session("default")
    assert isinstance(core, AgentCore)

    for text in contents:
        session = core.add_message(session, "user", text, None, base_config)

    app.save_session(session)
    return session.session_id


def test_server_generate_title_updates_metadata_and_sessions_list(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    session_id = _create_session_with_messages(app, ["hello", "world"])

    resp = server_mod.execute_action(
        {
            "plugin": "generate_title",
            "action_id": "generate_title_for_session",
            "inputs": {"session_id": session_id},
        },
        app_instance=app,
    )

    assert resp["status"] == "ok"
    assert resp["plugin"] == "generate_title"
    assert resp["action_id"] == "generate_title_for_session"

    result = resp.get("result") or {}
    mutations = result.get("mutations") or {}
    assert mutations.get("updated_session_ids") == [session_id]

    sessions_resp = server_mod.list_sessions(app_instance=app)
    summaries = sessions_resp.get("sessions") or []
    entry = next(s for s in summaries if s.get("session_id") == session_id)
    metadata = entry.get("metadata") or {}
    assert "title" in metadata
    assert isinstance(metadata["title"], str)
    assert metadata["title"].strip() != ""


def test_application_ui_schema_includes_generate_title_actions(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    resp = server_mod.list_application_ui_schema(app_instance=app)
    elements = resp.get("elements") or []

    list_actions = [
        el
        for el in elements
        if isinstance(el, dict)
        and el.get("plugin") == "generate_title"
        and el.get("ui_type") == "session_list_action"
    ]
    assert list_actions
    assert any(el.get("action_id") == "generate_title_for_session" for el in list_actions)

    view_actions = [
        el
        for el in elements
        if isinstance(el, dict)
        and el.get("plugin") == "generate_title"
        and el.get("ui_type") == "session_action"
    ]
    assert view_actions
    assert any(el.get("action_id") == "generate_title_for_session" for el in view_actions)


def test_server_generate_title_error_does_not_modify_session(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    session_id = _create_session_with_messages(app, ["one", "two"])

    # Monkeypatch send_request on this app instance so that no assistant
    # reply is produced.
    from agent_core import Session as CoreSession

    def _fake_send_request(
        core_arg: Any,
        session_arg: CoreSession,
        base_config_arg: Dict[str, Any],
        overrides_arg: Dict[str, Any] | None = None,
        *,
        stream: bool = False,
        request_id: str | None = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "type": "request_started",
                "session_id": session_arg.session_id,
                "request_id": request_id,
            },
            {
                "type": "request_completed",
                "session_id": session_arg.session_id,
                "request_id": request_id,
            },
        ]

    app.send_request = _fake_send_request  # type: ignore[assignment]

    resp = server_mod.execute_action(
        {
            "plugin": "generate_title",
            "action_id": "generate_title_for_session",
            "inputs": {"session_id": session_id},
        },
        app_instance=app,
    )

    # Transport-level status remains ok; the plugin reports its own status
    # inside the result payload.
    assert resp["status"] == "ok"
    result = resp.get("result") or {}
    assert result.get("status") == "error"
    assert result.get("error_type") == "plugin_error"

    sessions_resp = server_mod.list_sessions(app_instance=app)
    summaries = sessions_resp.get("sessions") or []
    entry = next(s for s in summaries if s.get("session_id") == session_id)
    metadata = entry.get("metadata") or {}
    assert "title" not in metadata


def test_server_generate_title_sets_description_metadata_when_enabled(
    tmp_path: Path,
) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    session_id = _create_session_with_messages(app, ["hello", "world"])

    # Monkeypatch send_request to return a two-line assistant reply so that
    # both title and description are populated.
    from agent_core import Session as CoreSession

    def _fake_send_request(
        core_arg: Any,
        session_arg: CoreSession,
        base_config_arg: Dict[str, Any],
        overrides_arg: Dict[str, Any] | None = None,
        *,
        stream: bool = False,
        request_id: str | None = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "type": "request_started",
                "session_id": session_arg.session_id,
                "request_id": request_id,
            },
            {
                "type": "final",
                "session_id": session_arg.session_id,
                "request_id": request_id,
                "messages": [
                    {
                        "role": "assistant",
                        "content": "Server Title\nServer description",
                    }
                ],
            },
            {
                "type": "request_completed",
                "session_id": session_arg.session_id,
                "request_id": request_id,
            },
        ]

    app.send_request = _fake_send_request  # type: ignore[assignment]

    resp = server_mod.execute_action(
        {
            "plugin": "generate_title",
            "action_id": "generate_title_for_session",
            "inputs": {"session_id": session_id},
        },
        app_instance=app,
    )

    assert resp["status"] == "ok"
    result = resp.get("result") or {}
    mutations = result.get("mutations") or {}
    assert mutations.get("updated_session_ids") == [session_id]

    sessions_resp = server_mod.list_sessions(app_instance=app)
    summaries = sessions_resp.get("sessions") or []
    entry = next(s for s in summaries if s.get("session_id") == session_id)
    metadata = entry.get("metadata") or {}
    assert metadata.get("title") == "Server Title"
    # Default description metadata key should be "subtitle".
    assert metadata.get("subtitle") == "Server description"
