"""Unit tests for :mod:`plugins.session_title_app` application plugin.

These tests exercise the SessionTitleAppPlugin directly via the
application-layer ``AgentApplication.execute_application_action`` helper.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

import json

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore

# Ensure provider plugin is importable for dotted-path loading.
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider  # noqa: F401
from plugins.session_title_app import SessionTitleAppPlugin  # noqa: F401


def _make_config_with_session_title(tmp_path: Path) -> Path:
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

    path = tmp_path / "config_session_title.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    config_path = _make_config_with_session_title(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(config_path), str(session_root), event_store=events)


def _create_session(app: AgentApplication) -> str:
    from agent_core import AgentCore

    core, base_config, session = app.create_session("default")
    assert isinstance(core, AgentCore)

    # Persist the empty session so that it appears in filesystem-backed
    # summaries if needed.
    app.save_session(session)
    return session.session_id


def test_set_session_title_updates_metadata_and_ids(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    session_id = _create_session(app)

    result = app.execute_application_action(
        plugin_id="session_title",
        action_id="set_session_title",
        params={"session_id": session_id, "title": "Project planning"},
    )

    updated = result.get("updated_session_ids") or []
    assert updated == [session_id]

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx

    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    assert metadata.get("title") == "Project planning"


def test_set_session_title_clears_title_when_empty(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    session_id = _create_session(app)

    # First set a non-empty title.
    _ = app.execute_application_action(
        plugin_id="session_title",
        action_id="set_session_title",
        params={"session_id": session_id, "title": "Initial title"},
    )

    ctx1 = app.load_session(session_id)
    assert ctx1 is not None
    _core1, _base1, session1 = ctx1
    md1 = session1.metadata if isinstance(session1.metadata, dict) else {}
    assert md1.get("title") == "Initial title"

    # Now clear the title by providing an empty string.
    result = app.execute_application_action(
        plugin_id="session_title",
        action_id="set_session_title",
        params={"session_id": session_id, "title": "  "},
    )

    updated = result.get("updated_session_ids") or []
    assert updated == [session_id]

    ctx2 = app.load_session(session_id)
    assert ctx2 is not None
    _core2, _base2, session2 = ctx2
    md2 = session2.metadata if isinstance(session2.metadata, dict) else {}
    assert "title" not in md2


def test_set_session_title_publishes_metadata_updated_event(tmp_path: Path) -> None:
    config_path = _make_config_with_session_title(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    session_id = _create_session(app)

    _ = app.execute_application_action(
        plugin_id="session_title",
        action_id="set_session_title",
        params={"session_id": session_id, "title": "Notes"},
    )

    evs = events.list(session_id=session_id, limit=20)
    types = {ev.get("type") for ev in evs}
    assert "session_metadata_updated" in types

    meta_events = [ev for ev in evs if ev.get("type") == "session_metadata_updated"]
    assert meta_events
    ev = meta_events[-1]
    assert ev.get("session_id") == session_id
    fields = ev.get("fields") or []
    assert "title" in fields


def test_set_session_title_can_set_subtitle(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    session_id = _create_session(app)

    result = app.execute_application_action(
        plugin_id="session_title",
        action_id="set_session_title",
        params={
            "session_id": session_id,
            "title": "Project planning",
            "subtitle": "Daily standup notes",
        },
    )

    updated = result.get("updated_session_ids") or []
    assert updated == [session_id]

    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base, session = ctx

    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    assert metadata.get("title") == "Project planning"
    assert metadata.get("subtitle") == "Daily standup notes"


def test_set_session_title_clears_subtitle_when_empty(tmp_path: Path) -> None:
    app = _build_app(tmp_path)

    session_id = _create_session(app)

    _ = app.execute_application_action(
        plugin_id="session_title",
        action_id="set_session_title",
        params={
            "session_id": session_id,
            "title": "With subtitle",
            "subtitle": "Initial subtitle",
        },
    )

    ctx1 = app.load_session(session_id)
    assert ctx1 is not None
    _core1, _base1, session1 = ctx1
    md1 = session1.metadata if isinstance(session1.metadata, dict) else {}
    assert md1.get("subtitle") == "Initial subtitle"

    result = app.execute_application_action(
        plugin_id="session_title",
        action_id="set_session_title",
        params={
            "session_id": session_id,
            "title": "With subtitle",
            "subtitle": "   ",
        },
    )

    updated = result.get("updated_session_ids") or []
    assert updated == [session_id]

    ctx2 = app.load_session(session_id)
    assert ctx2 is not None
    _core2, _base2, session2 = ctx2
    md2 = session2.metadata if isinstance(session2.metadata, dict) else {}
    assert "subtitle" not in md2


def test_session_title_ui_schema_includes_subtitle_field(tmp_path: Path) -> None:
    config_path = _make_config_with_session_title(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    elements = app.get_application_ui_schema()
    subtitle_fields = [
        el
        for el in elements
        if isinstance(el, dict)
        and el.get("plugin") == "session_title"
        and el.get("ui_type") == "session_list_field"
        and el.get("role") == "subtitle"
    ]

    assert subtitle_fields
    assert any(el.get("data") == "metadata.subtitle" for el in subtitle_fields)


def test_set_session_title_from_session_list_does_not_request_navigation(
    tmp_path: Path,
) -> None:
    app = _build_app(tmp_path)

    session_id = _create_session(app)

    result = app.execute_application_action(
        plugin_id="session_title",
        action_id="set_session_title",
        params={"session_id": session_id, "title": "From list", "source": "session_list"},
    )

    # For session-list invocations, the plugin should not request that
    # frontends navigate to/open the session.
    assert result.get("updated_session_ids") == [session_id]
    assert not isinstance(result.get("selected_session_id"), str)
