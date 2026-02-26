from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Iterator

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


def _make_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"},
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "generate_title_app.GenerateTitleAppPlugin",
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

    path = tmp_path / "config_generate_title_app.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    config_path = _make_config(tmp_path)
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
    assert isinstance(md.get("title"), str)
    assert md.get("title", "").strip() != ""


def test_application_ui_schema_includes_generate_title_actions(tmp_path: Path) -> None:
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
    app = _build_app(tmp_path)
    session_id = _create_session_with_messages(app, ["one", "two"])

    def _fake_send_request(
        core_arg: Any,
        session_arg: Any,
        base_config_arg: Dict[str, Any],
        overrides_arg: Dict[str, Any] | None = None,
        *,
        stream: bool = False,
        request_id: str | None = None,
    ) -> Iterator[Dict[str, Any]]:
        # No final assistant message.
        yield {
            "type": "request_started",
            "session_id": session_arg.session_id,
            "request_id": request_id,
        }
        yield {
            "type": "request_completed",
            "session_id": session_arg.session_id,
            "request_id": request_id,
        }

    app.send_request = _fake_send_request  # type: ignore[assignment]

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
    app = _build_app(tmp_path)
    session_id = _create_session_with_messages(app, ["hello", "world"])

    def _fake_send_request(
        core_arg: Any,
        session_arg: Any,
        base_config_arg: Dict[str, Any],
        overrides_arg: Dict[str, Any] | None = None,
        *,
        stream: bool = False,
        request_id: str | None = None,
    ) -> Iterator[Dict[str, Any]]:
        yield {
            "type": "request_started",
            "session_id": session_arg.session_id,
            "request_id": request_id,
        }
        yield {
            "type": "final",
            "session_id": session_arg.session_id,
            "request_id": request_id,
            "messages": [
                {
                    "role": "assistant",
                    "content": "Server Title\nServer description",
                }
            ],
        }
        yield {
            "type": "request_completed",
            "session_id": session_arg.session_id,
            "request_id": request_id,
        }

    app.send_request = _fake_send_request  # type: ignore[assignment]

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
