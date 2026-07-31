from __future__ import annotations

import json
from pathlib import Path

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_app.notifications import NotificationSink
from agent_core import AgentCore

from .dummy_provider import DummyProvider  # noqa: F401
from .fixtures.dummy_notification_tool import DummyNotificationTool


def _make_app(tmp_path: Path) -> tuple[AgentApplication, InMemoryEventStore, str]:
    config = {
        "providers": {"dummy": {"provider": "dummy_provider", "model": "test-model"}},
        "plugins": ["tests.dummy_provider.DummyProvider"],
        "agents": {"default": {"provider": "dummy"}},
        "application": {"notifications": {"max_items": 3}},
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    store = InMemoryEventStore()
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
        event_store=store,
    )
    _core, _base_config, session = app.create_session("default")
    return app, store, session.session_id


def _notification(
    key: str = "dummy:notification",
    *,
    title: str = "Dummy notification",
    presentation: str = "inline",
) -> dict:
    return {
        "key": key,
        "severity": "info",
        "title": title,
        "body": "Demonstration body",
        "source": {"plugin": "dummy_notification"},
        "display": {
            "format": "text",
            "title": title,
            "body": "Demonstration body",
            "presentation": presentation,
        },
        "model_visibility": "hidden",
    }


def test_create_update_resolve_and_persist_session_notification(
    tmp_path: Path,
) -> None:
    app, store, session_id = _make_app(tmp_path)

    created = app.create_session_notification(session_id, _notification(), request_id="request-1")
    updated = app.create_session_notification(
        session_id,
        _notification(title="Updated notification"),
        request_id="request-2",
    )

    assert updated["id"] == created["id"]
    assert updated["title"] == "Updated notification"
    assert app.list_session_notifications(session_id) == [updated]

    resolved = app.resolve_session_notification(
        session_id,
        created["id"],
        {"action_id": "resolve_dummy"},
        request_id="request-3",
    )
    assert resolved["status"] == "resolved"
    assert resolved["resolution"]["action_id"] == "resolve_dummy"
    assert app.list_session_notifications(session_id) == []
    assert app.list_session_notifications(session_id, include_resolved=True) == [resolved]

    reloaded = app.load_live_session_record(session_id)
    assert reloaded is not None
    assert reloaded.metadata["notifications"]["items"] == [resolved]

    events = store.list(since_id="0", session_id=session_id, limit=20)["events"]
    notification_events = [
        event for event in events if event["type"].startswith("session_notification_")
    ]
    assert [event["type"] for event in notification_events] == [
        "session_notification_created",
        "session_notification_updated",
        "session_notification_resolved",
    ]
    assert all(
        event["notification"]["model_visibility"] == "hidden" for event in notification_events
    )


def test_update_by_id_and_key(tmp_path: Path) -> None:
    app, _store, session_id = _make_app(tmp_path)
    created = app.create_session_notification(session_id, _notification())

    by_id = app.update_session_notification(session_id, created["id"], {"body": "Updated by id"})
    by_key = app.update_session_notification_by_key(
        session_id, created["key"], {"severity": "success"}
    )

    assert by_id["body"] == "Updated by id"
    assert by_key["severity"] == "success"
    assert by_key["display"]["variant"] == "info"


def test_notification_validation_and_sink_failure_are_contained(
    tmp_path: Path,
) -> None:
    app, _store, session_id = _make_app(tmp_path)

    with pytest.raises(ValueError):
        app.create_session_notification(
            session_id,
            {**_notification(), "display": {"presentation": "unknown"}},
        )

    sink = NotificationSink(app, session_id, "request")
    assert sink.create({"key": "invalid"}) is None
    assert app.list_session_notifications(session_id) == []


def test_tool_context_notification_sink_persists_without_interrupting_tool(
    tmp_path: Path,
) -> None:
    app, _store, session_id = _make_app(tmp_path)
    _core, base_config, session = app.load_session(session_id)  # type: ignore[misc]
    context = app._context.build_tool_context(
        session=session,
        request_id="tool-request",
        base_config=base_config,
    )

    result = DummyNotificationTool().execute_tool("emit_notification", {}, {}, context)

    assert result["success"] is True
    assert result["notification_id"]
    assert app.list_session_notifications(session_id)[0]["request_id"] == "tool-request"


def test_pruning_keeps_all_pending_and_only_latest_resolved(tmp_path: Path) -> None:
    app, _store, session_id = _make_app(tmp_path)

    for index in range(5):
        created = app.create_session_notification(session_id, _notification(f"resolved:{index}"))
        app.resolve_session_notification(session_id, created["id"], {"action_id": "resolve"})
    pending = app.create_session_notification(session_id, _notification("pending:one"))

    all_items = app.list_session_notifications(session_id, include_resolved=True)
    assert len(all_items) == 3
    assert pending in all_items
    assert len([item for item in all_items if item["status"] == "resolved"]) == 2
