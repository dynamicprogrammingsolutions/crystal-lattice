from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


def _make_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"},
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "session_title_app.SessionTitleAppPlugin",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {},
    }

    path = tmp_path / "config_session_title_app.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    cfg_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(cfg_path), str(session_root), event_store=events)


def test_set_session_title_updates_metadata(tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    _core, _base_config, session = app.create_session("default")
    session_id = session.session_id

    result = app.execute_application_action(
        "session_title",
        "set_session_title",
        {"session_id": session_id, "title": "Project planning"},
    )

    mutations = result.get("mutations") or {}
    assert mutations.get("updated_session_ids") == [session_id]

    reloaded = app.load_session_record(session_id)
    assert reloaded is not None
    metadata = reloaded.metadata if isinstance(reloaded.metadata, dict) else {}
    assert metadata.get("title") == "Project planning"


def test_set_session_title_clears_title(tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    _core, _base_config, session = app.create_session("default")
    session_id = session.session_id

    _ = app.execute_application_action(
        "session_title",
        "set_session_title",
        {"session_id": session_id, "title": "Initial"},
    )

    _ = app.execute_application_action(
        "session_title",
        "set_session_title",
        {"session_id": session_id, "title": "   "},
    )

    reloaded = app.load_session_record(session_id)
    assert reloaded is not None
    metadata = reloaded.metadata if isinstance(reloaded.metadata, dict) else {}
    assert "title" not in metadata


def test_application_ui_schema_includes_title_fields(tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    elements = app.get_application_ui_schema()

    title_fields = [
        el
        for el in elements
        if isinstance(el, dict)
        and el.get("plugin") == "session_title"
        and el.get("ui_type") == "session_list_field"
    ]

    assert title_fields
    assert any(el.get("data") == "metadata.title" for el in title_fields)
    assert any(el.get("data") == "metadata.subtitle" for el in title_fields)
