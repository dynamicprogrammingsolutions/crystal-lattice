from __future__ import annotations

from contextlib import contextmanager
import json
from pathlib import Path
from typing import Any, Dict, Iterator

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import Message, Session

from session_status_app import (
    SHOW_IN_SESSION_LIST_FOOTER_SETTING,
    STATUS_LABEL_FIELD,
)


ROOT = Path(__file__).resolve().parents[3]
PLUGIN_ROOT = ROOT / "plugins" / "session-status-app"
MESSAGE_COUNT_PLUGIN_ROOT = ROOT / "plugins" / "session-message-count-meta-app"
EXPECTED_OPTIONS = [
    {
        "value": "todo",
        "label": "To do",
        "icon": "circle",
        "tone": "muted",
    },
    {
        "value": "in_progress",
        "label": "In progress",
        "icon": "clock",
        "tone": "primary",
    },
    {
        "value": "blocked",
        "label": "Blocked",
        "icon": "alert-circle",
        "tone": "danger",
    },
    {
        "value": "done",
        "label": "Done",
        "icon": "check-circle",
        "tone": "success",
    },
]


def _build_application(
    tmp_path: Path,
    *,
    metadata_key: str = "status",
    show_footer_default: bool = True,
) -> tuple[AgentApplication, InMemoryEventStore]:
    config: Dict[str, Any] = {
        "providers": {
            "echo": {
                "provider": "echo_openai_like",
                "model": "test-model",
            }
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            f"path:{MESSAGE_COUNT_PLUGIN_ROOT}",
            f"path:{PLUGIN_ROOT}",
        ],
        "agents": {"default": {"provider": "echo"}},
        "application": {
            "session_status_metadata_key": metadata_key,
            SHOW_IN_SESSION_LIST_FOOTER_SETTING: show_footer_default,
        },
    }
    config_path = tmp_path / f"config-{metadata_key}.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    events = InMemoryEventStore()
    return (
        AgentApplication(
            config_path,
            tmp_path / f"sessions-{metadata_key}",
            event_store=events,
        ),
        events,
    )


@pytest.fixture
def application(
    tmp_path: Path,
) -> Iterator[tuple[AgentApplication, InMemoryEventStore]]:
    app, events = _build_application(tmp_path)
    try:
        yield app, events
    finally:
        app.close()


def _save(
    app: AgentApplication,
    *,
    session_id: str,
    metadata: Dict[str, Any],
) -> Session:
    session = Session(
        session_id=session_id,
        messages=(
            Message(role="system", content="system"),
            Message(role="user", content=f"preview {session_id}"),
        ),
        metadata={"agent_id": "default", **metadata},
    )
    app.save_session(session)
    return session


def _events_for(
    events: InMemoryEventStore,
    session_id: str,
) -> list[Dict[str, Any]]:
    return events.list(session_id=session_id, limit=20)["events"]


def test_status_plugin_exposes_consistent_ordinary_action_and_filter(
    application: tuple[AgentApplication, InMemoryEventStore],
) -> None:
    app, _events = application
    elements = app.get_application_ui_schema()
    action = next(
        element
        for element in elements
        if element.get("ui_type") == "session_list_action"
        and element.get("id") == "set_session_status"
    )
    chat_action = next(
        element
        for element in elements
        if element.get("ui_type") == "session_action"
        and element.get("id") == "set_session_status"
    )
    status_filter = next(
        element
        for element in elements
        if element.get("ui_type") == "session_list_filter"
        and element.get("id") == "session_status"
    )
    status_meta = next(
        element
        for element in elements
        if element.get("ui_type") == "session_list_field"
        and element.get("id") == "session_status_meta"
    )

    assert action["plugin"] == "session_status"
    assert action["action_id"] == "set_session_status"
    assert action["dialog"]["kind"] == "form"
    status_input = action["dialog"]["inputs"][0]
    assert status_input["prefill_from"] == "$session.metadata.status"
    assert status_input["default"] == "todo"
    assert status_input["options"] == EXPECTED_OPTIONS
    assert action["rich_ui"] == {
        "kind": "list",
        "value_path": "metadata.status",
        "missing_value": "todo",
        "input_name": "status",
        "default_pinned": False,
        "options": EXPECTED_OPTIONS,
    }
    assert action["rich_ui"]["options"] == status_input["options"]
    assert chat_action["plugin"] == "session_status"
    assert chat_action["action_id"] == action["action_id"]
    assert chat_action["dialog"] == action["dialog"]
    assert chat_action["param_map"] == action["param_map"]
    assert chat_action["rich_ui"] == {
        **action["rich_ui"],
        "placements": ["session_header"],
    }

    assert status_filter == {
        "ui_type": "session_list_filter",
        "id": "session_status",
        "label": "Status",
        "icon": "circle",
        "order": 20,
        "type": "select",
        "match": "one_of",
        "multiple": True,
        "data": "metadata.status",
        "missing_value": "todo",
        "default": [],
        "options": EXPECTED_OPTIONS,
        "plugin": "session_status",
    }
    assert status_filter["options"] == status_input["options"]
    assert status_meta == {
        "ui_type": "session_list_field",
        "id": "session_status_meta",
        "label": "Status",
        "role": "meta",
        "data": STATUS_LABEL_FIELD,
        "template": "Status: {{data}}",
        "order": 100,
        "plugin": "session_status",
    }

    actions = app.get_application_actions()
    assert (
        next(item for item in actions if item["id"] == "set_session_status")["plugin"]
        == "session_status"
    )
    label_action = next(
        item for item in actions if item["id"] == "compute_session_status_label"
    )
    assert label_action["plugin"] == "session_status"
    assert label_action["trigger"] == "session_list"

    server_setting = next(
        element
        for element in app.get_server_settings_ui_schema()
        if element.get("key") == SHOW_IN_SESSION_LIST_FOOTER_SETTING
    )
    assert server_setting == {
        "ui_type": "config",
        "scope": "server",
        "key": SHOW_IN_SESSION_LIST_FOOTER_SETTING,
        "type": "checkbox",
        "label": "Show status in session list footer",
        "description": "Display the current workflow status in each session row.",
        "default": True,
        "plugin": "session_status",
    }


def test_status_action_is_immutable_locked_evented_and_filterable(
    application: tuple[AgentApplication, InMemoryEventStore],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    app, events = application
    original = _save(app, session_id="missing-status", metadata={})
    _save(app, session_id="already-blocked", metadata={"status": "blocked"})

    todo = app.list_session_summaries(
        filter_values={"session_status": ["todo"]},
        apply_filter_defaults=True,
    )
    assert [item["session_id"] for item in todo] == ["missing-status"]

    lock_calls: list[str] = []
    original_lock = app.acquire_session_lock

    @contextmanager
    def tracked_lock(session_id: str) -> Iterator[None]:
        lock_calls.append(session_id)
        with original_lock(session_id):
            yield

    monkeypatch.setattr(app, "acquire_session_lock", tracked_lock)
    result = app.execute_application_action(
        plugin_id="session_status",
        action_id="set_session_status",
        params={
            "session_id": "missing-status",
            "status": "done",
            "source": "test",
        },
    )

    assert lock_calls == ["missing-status"]
    assert result["mutations"]["updated_session_ids"] == ["missing-status"]
    assert original.metadata == {"agent_id": "default"}
    stored = app.load_session_record("missing-status")
    assert stored is not None
    assert stored.metadata["status"] == "done"

    session_events = _events_for(events, "missing-status")
    metadata_events = [
        event
        for event in session_events
        if event.get("type") == "session_metadata_updated"
    ]
    assert metadata_events[-1]["fields"] == ["status"]
    assert [event for event in session_events if event.get("type") == "checkpoint"]

    ordered = app.list_session_summaries(apply_filter_defaults=True)
    selected = app.list_session_summaries(
        filter_values={"session_status": ["blocked", "done"]},
        apply_filter_defaults=True,
    )
    expected_ids = [
        item["session_id"]
        for item in ordered
        if item["metadata"].get("status") in {"blocked", "done"}
    ]
    assert [item["session_id"] for item in selected] == expected_ids

    event_count = len(_events_for(events, "missing-status"))
    no_op = app.execute_application_action(
        plugin_id="session_status",
        action_id="set_session_status",
        params={"session_id": "missing-status", "status": "done"},
    )
    assert no_op["mutations"]["updated_session_ids"] == []
    assert len(_events_for(events, "missing-status")) == event_count


def test_missing_todo_is_no_op_and_invalid_values_are_rejected(
    application: tuple[AgentApplication, InMemoryEventStore],
) -> None:
    app, events = application
    _save(app, session_id="old-session", metadata={})

    result = app.execute_application_action(
        plugin_id="session_status",
        action_id="set_session_status",
        params={"session_id": "old-session", "status": "todo"},
    )
    assert result["mutations"]["updated_session_ids"] == []
    stored = app.load_session_record("old-session")
    assert stored is not None
    assert "status" not in stored.metadata
    assert _events_for(events, "old-session") == []

    with pytest.raises(ValueError, match="status must be one of"):
        app.execute_application_action(
            plugin_id="session_status",
            action_id="set_session_status",
            params={"session_id": "old-session", "status": "unknown"},
        )


def test_custom_status_metadata_key_drives_ui_mutation_event_and_filter(
    tmp_path: Path,
) -> None:
    app, events = _build_application(tmp_path, metadata_key="workflow_state")
    try:
        _save(
            app,
            session_id="custom",
            metadata={"workflow_state": "in_progress"},
        )
        elements = app.get_application_ui_schema()
        action = next(
            item for item in elements if item.get("ui_type") == "session_list_action"
        )
        status_filter = next(
            item for item in elements if item.get("ui_type") == "session_list_filter"
        )
        assert (
            action["dialog"]["inputs"][0]["prefill_from"]
            == "$session.metadata.workflow_state"
        )
        assert action["rich_ui"]["value_path"] == "metadata.workflow_state"
        assert status_filter["data"] == "metadata.workflow_state"

        initial_summary = app.get_session_summary("custom")
        assert initial_summary[STATUS_LABEL_FIELD] == "In progress"
        assert initial_summary["presentation"]["meta"] == (
            "2 messages · Status: In progress"
        )

        app.execute_application_action(
            plugin_id="session_status",
            action_id="set_session_status",
            params={"session_id": "custom", "status": "blocked"},
        )
        stored = app.load_session_record("custom")
        assert stored is not None
        assert stored.metadata["workflow_state"] == "blocked"
        assert "status" not in stored.metadata

        metadata_event = next(
            event
            for event in _events_for(events, "custom")
            if event.get("type") == "session_metadata_updated"
        )
        assert metadata_event["fields"] == ["workflow_state"]

        matches = app.list_session_summaries(
            filter_values={"session_status": ["blocked"]},
            apply_filter_defaults=True,
        )
        assert [item["session_id"] for item in matches] == ["custom"]
        assert matches[0][STATUS_LABEL_FIELD] == "Blocked"
        assert matches[0]["presentation"]["meta"] == ("2 messages · Status: Blocked")
    finally:
        app.close()


def test_status_list_footer_uses_human_labels_order_and_live_server_override(
    tmp_path: Path,
) -> None:
    app, _events = _build_application(tmp_path)
    try:
        _save(app, session_id="todo", metadata={})
        _save(app, session_id="done", metadata={"status": "done"})
        _save(app, session_id="invalid", metadata={"status": "legacy-value"})

        summaries = {
            summary["session_id"]: summary
            for summary in app.list_session_summaries(apply_filter_defaults=True)
        }
        assert summaries["todo"][STATUS_LABEL_FIELD] == "To do"
        assert summaries["todo"]["presentation"]["meta"] == (
            "2 messages · Status: To do"
        )
        assert summaries["done"][STATUS_LABEL_FIELD] == "Done"
        assert summaries["done"]["presentation"]["meta"] == (
            "2 messages · Status: Done"
        )
        assert summaries["invalid"][STATUS_LABEL_FIELD] == "To do"

        app.patch_server_settings(
            {SHOW_IN_SESSION_LIST_FOOTER_SETTING: False},
            source="test",
        )
        hidden_elements = app.get_application_ui_schema()
        assert not any(
            element.get("id") == "session_status_meta" for element in hidden_elements
        )
        hidden = app.get_session_summary("done")
        assert hidden["presentation"]["meta"] == "2 messages"

        app.delete_server_setting(
            SHOW_IN_SESSION_LIST_FOOTER_SETTING,
            source="test",
        )
        restored = app.get_session_summary("done")
        assert restored["presentation"]["meta"] == "2 messages · Status: Done"
    finally:
        app.close()


def test_status_list_footer_can_default_off_and_be_enabled_by_server_setting(
    tmp_path: Path,
) -> None:
    app, _events = _build_application(tmp_path, show_footer_default=False)
    try:
        _save(app, session_id="done", metadata={"status": "done"})

        setting = next(
            element
            for element in app.get_server_settings_ui_schema()
            if element.get("key") == SHOW_IN_SESSION_LIST_FOOTER_SETTING
        )
        assert setting["default"] is False
        assert app.get_session_summary("done")["presentation"]["meta"] == ("2 messages")

        app.patch_server_settings(
            {SHOW_IN_SESSION_LIST_FOOTER_SETTING: True},
            source="test",
        )
        assert app.get_session_summary("done")["presentation"]["meta"] == (
            "2 messages · Status: Done"
        )
    finally:
        app.close()
