"""Contract tests for the archive application plugin."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import AgentCore


ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = ROOT / "plugins" / "session-archive-app"


def _build_app(
    tmp_path: Path,
    *,
    metadata_key: str = "archived",
) -> tuple[AgentApplication, InMemoryEventStore]:
    config = {
        "providers": {
            "echo": {
                "provider": "echo_openai_like",
                "model": "test-model",
            }
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            f"path:{PLUGIN_ROOT}",
        ],
        "agents": {"default": {"provider": "echo"}},
        "application": {"session_archived_metadata_key": metadata_key},
    }
    config_path = tmp_path / "archive-config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    events = InMemoryEventStore()
    return (
        AgentApplication(config_path, tmp_path / "sessions", event_store=events),
        events,
    )


def _create_session(app: AgentApplication) -> str:
    core, _config, session = app.create_session("default")
    assert isinstance(core, AgentCore)
    app.save_session(session)
    return session.session_id


def test_archive_declarations_share_configured_metadata_path(tmp_path: Path) -> None:
    app, _events = _build_app(tmp_path, metadata_key="hidden")
    try:
        elements = app.get_application_ui_schema()
        action = next(
            element
            for element in elements
            if element.get("ui_type") == "session_list_action"
        )
        archive_filter = next(
            element
            for element in elements
            if element.get("ui_type") == "session_list_filter"
        )

        assert action == {
            "ui_type": "session_list_action",
            "id": "toggle_session_archived",
            "label": "Archive/restore session",
            "icon": "archive",
            "order": 20,
            "action_id": "toggle_session_archived",
            "param_map": {"session_id": "$session.session_id"},
            "dialog": {"kind": "none"},
            "rich_ui": {
                "kind": "toggle",
                "value_path": "metadata.hidden",
                "missing_value": False,
                "active_value": True,
                "default_pinned": True,
                "appearance": {
                    "active": {"tone": "primary"},
                    "inactive": {"tone": "muted"},
                },
            },
            "plugin": "session_archive",
        }
        assert archive_filter["id"] == "archive_state"
        assert archive_filter["data"] == "metadata.hidden"
        assert archive_filter["default"] is False
    finally:
        app.close()


def test_archive_toggle_is_immutable_evented_and_filters_by_default(
    tmp_path: Path,
) -> None:
    app, events = _build_app(tmp_path)
    try:
        first_id = _create_session(app)
        second_id = _create_session(app)
        original = app.load_session_record(first_id)
        assert original is not None

        assert {
            summary["session_id"]
            for summary in app.list_session_summaries(apply_filter_defaults=True)
        } == {first_id, second_id}

        result = app.execute_application_action(
            plugin_id="session_archive",
            action_id="toggle_session_archived",
            params={"session_id": first_id},
        )
        assert result["mutations"]["updated_session_ids"] == [first_id]
        assert original.metadata.get("archived") is None
        stored = app.load_session_record(first_id)
        assert stored is not None
        assert stored.metadata["archived"] is True

        default_visible = app.list_session_summaries(apply_filter_defaults=True)
        assert [item["session_id"] for item in default_visible] == [second_id]
        archived = app.list_session_summaries(
            filter_values={"archive_state": True},
            apply_filter_defaults=True,
        )
        assert [item["session_id"] for item in archived] == [first_id]
        all_sessions = app.list_session_summaries(
            filter_values={"archive_state": None},
            apply_filter_defaults=True,
        )
        assert {item["session_id"] for item in all_sessions} == {first_id, second_id}

        session_events: list[dict[str, Any]] = events.list(
            session_id=first_id,
            limit=20,
        )["events"]
        update = next(
            event
            for event in session_events
            if event.get("type") == "session_metadata_updated"
        )
        assert update["fields"] == ["archived"]
        assert any(event.get("type") == "checkpoint" for event in session_events)
    finally:
        app.close()
