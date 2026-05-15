from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import json

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore

from plugins.controllable_openai_test_provider import (
    reset_controllable_openai_test_provider_state,
)


def _make_config(
    tmp_path: Path,
    *,
    provider_config: Dict[str, Any] | None = None,
    application_config: Dict[str, Any] | None = None,
) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "controlled": {
                "provider": "controllable_openai_test_provider",
                "model": "test-model",
                **dict(provider_config or {}),
            },
        },
        "plugins": [
            "plugins.controllable_openai_test_provider.ControllableOpenAITestProvider",
            "generate_title_app.GenerateTitleAppPlugin",
        ],
        "agents": {
            "default": {"provider": "controlled"},
        },
        "application": {
            "generate_title_agent_id": "default",
            "generate_title_prompt_template": "Generate a concise title.",
            "generate_title_max_messages": 10,
            **dict(application_config or {}),
        },
    }

    path = tmp_path / "config_generate_title_app.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(
    tmp_path: Path,
    *,
    provider_config: Dict[str, Any] | None = None,
    application_config: Dict[str, Any] | None = None,
) -> AgentApplication:
    config_path = _make_config(
        tmp_path,
        provider_config=provider_config,
        application_config=application_config,
    )
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    return AgentApplication(str(config_path), str(session_root), event_store=events)


def _create_session_with_messages(app: AgentApplication, contents: List[str]) -> str:
    core, base_config, session = app.create_session("default")

    for text in contents:
        session = core.add_message(session, "user", text, metadata=None, config=base_config)

    app.save_session(session)
    return session.session_id


def test_generate_title_action_updates_session_metadata(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(tmp_path)
    session_id = _create_session_with_messages(app, ["hello", "world"])

    result = app.execute_application_action(
        "generate_title",
        "generate_title_for_session",
        {"session_id": session_id},
    )

    mutations = result.get("mutations") or {}
    assert mutations.get("updated_session_ids") == [session_id]

    updated = app.load_session_record(session_id)
    assert updated is not None
    md = updated.metadata if isinstance(updated.metadata, dict) else {}
    assert md.get("title") == "Generated title"


def test_application_ui_schema_includes_generate_title_actions(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(tmp_path)
    elements = app.get_application_ui_schema()

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


def test_generate_title_error_does_not_modify_session(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(tmp_path, provider_config={"response_mode": "none"})
    session_id = _create_session_with_messages(app, ["one", "two"])

    result = app.execute_application_action(
        "generate_title",
        "generate_title_for_session",
        {"session_id": session_id},
    )

    assert result.get("status") == "error"
    assert result.get("error_type") == "plugin_error"

    updated = app.load_session_record(session_id)
    assert updated is not None
    md = updated.metadata if isinstance(updated.metadata, dict) else {}
    assert "title" not in md


def test_generate_title_sets_description_metadata_when_enabled(tmp_path: Path) -> None:
    reset_controllable_openai_test_provider_state()
    app = _build_app(
        tmp_path,
        provider_config={"response_text": "Server Title\nServer description"},
    )
    session_id = _create_session_with_messages(app, ["hello", "world"])

    result = app.execute_application_action(
        "generate_title",
        "generate_title_for_session",
        {"session_id": session_id},
    )

    mutations = result.get("mutations") or {}
    assert mutations.get("updated_session_ids") == [session_id]

    updated = app.load_session_record(session_id)
    assert updated is not None
    md = updated.metadata if isinstance(updated.metadata, dict) else {}
    assert md.get("title") == "Server Title"
    assert md.get("subtitle") == "Server description"