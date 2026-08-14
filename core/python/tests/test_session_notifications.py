from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_app.notifications import (
    NotificationOperationSupersededError,
    NotificationRevisionConflictError,
    NotificationSink,
    NotificationTransitionError,
    notification_ttl_elapsed,
)
from agent_core import AgentCore, Session

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

    created = app.create_session_notification(
        session_id, _notification(), request_id="request-1"
    )
    updated = app.create_session_notification(
        session_id,
        _notification(title="Updated notification"),
        request_id="request-2",
    )

    assert updated["id"] == created["id"]
    assert created["revision"] == 1
    assert updated["revision"] == 2
    assert updated["title"] == "Updated notification"
    assert app.list_session_notifications(session_id) == [updated]

    resolved = app.resolve_session_notification(
        session_id,
        created["id"],
        {"action_id": "resolve_dummy"},
        request_id="request-3",
    )
    assert resolved["status"] == "resolved"
    assert resolved["revision"] == 3
    assert resolved["resolution"]["action_id"] == "resolve_dummy"
    assert app.list_session_notifications(session_id) == []
    assert app.list_session_notifications(session_id, include_resolved=True) == [
        resolved
    ]

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
        event["notification"]["model_visibility"] == "hidden"
        for event in notification_events
    )


def test_update_by_id_and_key(tmp_path: Path) -> None:
    app, _store, session_id = _make_app(tmp_path)
    created = app.create_session_notification(session_id, _notification())

    by_id = app.update_session_notification(
        session_id, created["id"], {"body": "Updated by id"}
    )
    by_key = app.update_session_notification_by_key(
        session_id, created["key"], {"severity": "success"}
    )

    assert by_id["body"] == "Updated by id"
    assert by_key["severity"] == "success"
    assert by_key["display"]["variant"] == "info"


def test_producer_publication_by_key_updates_active_occurrence(
    tmp_path: Path,
) -> None:
    app, _store, session_id = _make_app(tmp_path)
    first = app.create_session_notification(session_id, _notification())
    second = app.create_session_notification(session_id, _notification())

    assert first["id"] == second["id"]
    assert second["revision"] == first["revision"] + 1


def test_producer_publication_by_key_creates_new_occurrence_after_dismissal(
    tmp_path: Path,
) -> None:
    app, _store, session_id = _make_app(tmp_path)
    created = app.create_session_notification(session_id, _notification())
    app.dismiss_session_notification(
        session_id, created["id"], expected_revision=created["revision"]
    )

    replacement = app.create_session_notification(session_id, _notification())

    assert replacement["id"] != created["id"]
    assert replacement["revision"] == 1
    active = app.list_session_notifications(session_id)
    assert [item["id"] for item in active] == [replacement["id"]]


def test_producer_publication_by_key_creates_new_occurrence_after_resolution(
    tmp_path: Path,
) -> None:
    app, _store, session_id = _make_app(tmp_path)
    created = app.create_session_notification(session_id, _notification())
    app.resolve_session_notification(
        session_id, created["id"], {"action_id": "done"}
    )

    replacement = app.create_session_notification(session_id, _notification())

    assert replacement["id"] != created["id"]
    assert replacement["revision"] == 1


def test_producer_publication_by_key_creates_new_occurrence_after_expiration(
    tmp_path: Path,
) -> None:
    app, _store, session_id = _make_app(tmp_path)
    created = app.create_session_notification(session_id, _notification())
    app.expire_session_notification(session_id, created["id"])

    replacement = app.create_session_notification(session_id, _notification())

    assert replacement["id"] != created["id"]
    assert replacement["revision"] == 1


def test_producer_resolve_and_expire_do_not_require_expected_revision(
    tmp_path: Path,
) -> None:
    app, _store, session_id = _make_app(tmp_path)
    created = app.create_session_notification(session_id, _notification())

    resolved = app.resolve_session_notification(
        session_id, created["id"], {"action_id": "done"}
    )
    assert resolved["status"] == "resolved"
    assert resolved["revision"] == created["revision"] + 1

    replacement = app.create_session_notification(session_id, _notification())
    expired = app.expire_session_notification(session_id, replacement["id"])
    assert expired["status"] == "expired"
    assert expired["revision"] == replacement["revision"] + 1


def test_dismissal_with_stale_expected_revision_returns_current_record(
    tmp_path: Path,
) -> None:
    app, _store, session_id = _make_app(tmp_path)
    created = app.create_session_notification(session_id, _notification())
    updated = app.update_session_notification(
        session_id, created["id"], {"body": "new body"}
    )

    with pytest.raises(NotificationRevisionConflictError) as conflict:
        app.dismiss_session_notification(
            session_id, created["id"], expected_revision=created["revision"]
        )
    assert conflict.value.current["revision"] == updated["revision"]


def test_stale_dismissal_does_not_hide_newer_revision(tmp_path: Path) -> None:
    app, _store, session_id = _make_app(tmp_path)
    created = app.create_session_notification(session_id, _notification())
    updated = app.update_session_notification(
        session_id, created["id"], {"body": "new body"}
    )

    with pytest.raises(NotificationRevisionConflictError):
        app.dismiss_session_notification(
            session_id, created["id"], expected_revision=created["revision"]
        )

    active = app.list_session_notifications(session_id)
    assert len(active) == 1
    assert active[0]["revision"] == updated["revision"]
    assert active[0]["body"] == "new body"


def test_dismissed_occurrence_does_not_suppress_later_publication(
    tmp_path: Path,
) -> None:
    app, _store, session_id = _make_app(tmp_path)
    created = app.create_session_notification(session_id, _notification())
    app.dismiss_session_notification(
        session_id, created["id"], expected_revision=created["revision"]
    )

    replacement = app.create_session_notification(session_id, _notification())

    active = app.list_session_notifications(session_id)
    assert [item["id"] for item in active] == [replacement["id"]]
    terminal = app.list_session_notifications(session_id, include_terminal=True)
    assert created["id"] in [item["id"] for item in terminal]
    assert replacement["id"] in [item["id"] for item in terminal]


def test_operation_occurrence_guard_rejects_late_update_from_older_operation(
    tmp_path: Path,
) -> None:
    app, _store, session_id = _make_app(tmp_path)
    first = app.create_session_notification(
        session_id,
        {**_notification(), "operation": {"id": "op-1", "state": "running"}},
    )
    # Simulate a newer operation taking over the stable key by dismissing the
    # first occurrence and creating a new one with a different operation ID.
    app.dismiss_session_notification(
        session_id, first["id"], expected_revision=first["revision"]
    )
    second = app.create_session_notification(
        session_id,
        {**_notification(), "operation": {"id": "op-2", "state": "running"}},
    )

    with pytest.raises(NotificationOperationSupersededError) as conflict:
        app.create_session_notification(
            session_id,
            {**_notification(), "operation": {"id": "op-1", "state": "running"}},
        )
    assert conflict.value.current["id"] == second["id"]

    active = app.list_session_notifications(session_id)
    assert [item["id"] for item in active] == [second["id"]]


def test_operation_occurrence_guard_allows_same_operation_update(
    tmp_path: Path,
) -> None:
    app, _store, session_id = _make_app(tmp_path)
    first = app.create_session_notification(
        session_id,
        {**_notification(), "operation": {"id": "op-1", "state": "running"}},
    )
    second = app.create_session_notification(
        session_id,
        {**_notification(), "operation": {"id": "op-1", "state": "running"}},
    )

    assert first["id"] == second["id"]
    assert second["revision"] == first["revision"] + 1


def test_operation_occurrence_guard_allows_new_operation_after_completion(
    tmp_path: Path,
) -> None:
    app, _store, session_id = _make_app(tmp_path)
    first = app.create_session_notification(
        session_id,
        {**_notification(), "operation": {"id": "op-1", "state": "succeeded"}},
    )
    # A new operation may replace a completed operation's notification.
    second = app.create_session_notification(
        session_id,
        {**_notification(), "operation": {"id": "op-2", "state": "running"}},
    )

    assert first["id"] == second["id"]
    assert second["operation"]["id"] == "op-2"


def test_update_by_key_creates_new_occurrence_when_key_is_terminal(
    tmp_path: Path,
) -> None:
    app, _store, session_id = _make_app(tmp_path)
    created = app.create_session_notification(session_id, _notification())
    app.dismiss_session_notification(
        session_id, created["id"], expected_revision=created["revision"]
    )

    replacement = app.update_session_notification_by_key(
        session_id, created["key"], _notification()
    )

    assert replacement["id"] != created["id"]
    assert replacement["revision"] == 1
    active = app.list_session_notifications(session_id)
    assert [item["id"] for item in active] == [replacement["id"]]


def test_update_by_key_creates_new_occurrence_when_key_is_absent(
    tmp_path: Path,
) -> None:
    app, _store, session_id = _make_app(tmp_path)

    created = app.update_session_notification_by_key(
        session_id, "absent:key", _notification(key="absent:key")
    )

    assert created["revision"] == 1
    active = app.list_session_notifications(session_id)
    assert [item["id"] for item in active] == [created["id"]]


def test_session_notification_ui_effects_are_normalized(tmp_path: Path) -> None:
    app, _store, session_id = _make_app(tmp_path)
    stored = app.create_session_notification(
        session_id,
        {
            **_notification(),
            "ui_effects": {
                "reload_session_ids": [session_id, session_id],
                "reload_sessions_list": True,
                "reload_application_actions": True,
                "plugin_detail": {"value": 1},
            },
        },
    )
    assert stored["ui_effects"] == {
        "reload_session_ids": [session_id],
        "reload_sessions_list": True,
        "reload_application_actions": True,
        "plugin_detail": {"value": 1},
    }
    updated = app.update_session_notification(
        session_id,
        stored["id"],
        {"body": "Presentation-only update"},
    )
    assert "ui_effects" not in updated

    repeated = app.update_session_notification(
        session_id,
        stored["id"],
        {"ui_effects": {"reload_session_ids": [session_id]}},
    )
    assert repeated["ui_effects"] == {"reload_session_ids": [session_id]}
    dismissed = app.dismiss_session_notification(
        session_id,
        stored["id"],
        expected_revision=repeated["revision"],
    )
    assert "ui_effects" not in dismissed

    with pytest.raises(ValueError, match="action-only"):
        app.update_session_notification(
            session_id,
            stored["id"],
            {"ui_effects": {"navigate_to_session_id": session_id}},
        )

    with pytest.raises(ValueError, match="must be a list"):
        app.update_session_notification(
            session_id,
            stored["id"],
            {"ui_effects": {"reload_session_ids": session_id}},
        )


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
        created = app.create_session_notification(
            session_id, _notification(f"resolved:{index}")
        )
        app.resolve_session_notification(
            session_id, created["id"], {"action_id": "resolve"}
        )
    pending = app.create_session_notification(session_id, _notification("pending:one"))

    all_items = app.list_session_notifications(session_id, include_resolved=True)
    assert len(all_items) == 4
    assert pending in all_items
    assert len([item for item in all_items if item["status"] == "resolved"]) == 3


def test_ttl_is_validated_and_remains_pending_after_deadline(tmp_path: Path) -> None:
    app, store, session_id = _make_app(tmp_path)
    deadline = datetime(2026, 8, 2, 12, 0, tzinfo=timezone.utc)

    created = app.create_session_notification(
        session_id,
        {
            **_notification("ttl"),
            "retention": {
                "policy": "ttl",
                "expires_at": deadline.isoformat().replace("+00:00", "Z"),
            },
        },
    )

    assert created["retention"] == {
        "version": 1,
        "policy": "ttl",
        "expires_at": "2026-08-02T12:00:00Z",
    }
    assert not notification_ttl_elapsed(
        created,
        now=deadline - timedelta(seconds=1),
    )
    assert notification_ttl_elapsed(created, now=deadline)
    assert app.list_session_notifications(session_id) == [created]
    assert not any(
        event["type"] == "session_notification_expired"
        for event in store.list(since_id="0", session_id=session_id, limit=20)["events"]
    )

    with pytest.raises(ValueError, match="valid RFC3339"):
        app.create_session_notification(
            session_id,
            {
                **_notification("bad-ttl"),
                "retention": {"policy": "ttl", "expires_at": "not-a-date"},
            },
        )


def test_request_and_owner_lifetime_expire_session_notifications(
    tmp_path: Path,
) -> None:
    app, store, session_id = _make_app(tmp_path)
    request_notification = app.create_session_notification(
        session_id,
        {
            **_notification("request"),
            "retention": {"policy": "until_request_complete"},
        },
        request_id="request-1",
    )
    owner_notification = app.create_session_notification(
        session_id,
        {
            **_notification("owner"),
            "retention": {"policy": "until_server_restart"},
        },
    )

    expired_request = app._session_notifications.expire_request(
        session_id,
        "request-1",
    )
    assert [item["id"] for item in expired_request] == [request_notification["id"]]
    assert expired_request[0]["expiration"]["reason"] == "request_completed"

    app._notification_owner_epoch = "replacement-owner"
    summary = app.get_session_summary(session_id)
    items = summary["metadata"]["notifications"]["items"]
    recovered_owner = next(
        item for item in items if item["id"] == owner_notification["id"]
    )
    assert recovered_owner["status"] == "expired"
    assert recovered_owner["expiration"]["reason"] == "owner_restarted"

    event_types = [
        event["type"]
        for event in store.list(since_id="0", session_id=session_id, limit=30)["events"]
        if event["type"].startswith("session_notification_")
    ]
    assert event_types[-2:] == [
        "session_notification_expired",
        "session_notification_expired",
    ]


def test_request_retention_requires_authoritative_request_id(tmp_path: Path) -> None:
    app, _store, session_id = _make_app(tmp_path)

    with pytest.raises(ValueError, match="authoritative request_id"):
        app.create_session_notification(
            session_id,
            {
                **_notification("request"),
                "retention": {"policy": "until_request_complete"},
            },
        )


def test_dismiss_persists_terminal_record_and_same_key_creates_new_occurrence(
    tmp_path: Path,
) -> None:
    app, store, session_id = _make_app(tmp_path)
    created = app.create_session_notification(session_id, _notification())

    dismissed = app.dismiss_session_notification(
        session_id,
        created["id"],
        reason="user",
        expected_revision=created["revision"],
    )

    assert dismissed["status"] == "dismissed"
    assert dismissed["revision"] == 2
    assert dismissed["dismissal"]["reason"] == "user"
    assert app.list_session_notifications(session_id) == []
    assert app.list_session_notifications(session_id, include_terminal=True) == [
        dismissed
    ]

    repeated = app.dismiss_session_notification(
        session_id,
        created["id"],
        expected_revision=dismissed["revision"],
    )
    assert repeated == dismissed

    replacement = app.create_session_notification(session_id, _notification())
    assert replacement["id"] != created["id"]
    assert replacement["revision"] == 1
    assert app.list_session_notifications(session_id) == [replacement]

    reloaded = app.load_live_session_record(session_id)
    assert reloaded is not None
    assert reloaded.metadata["notifications"]["items"] == [dismissed, replacement]

    events = store.list(since_id="0", session_id=session_id, limit=20)["events"]
    assert [event["type"] for event in events if "notification_" in event["type"]] == [
        "session_notification_created",
        "session_notification_dismissed",
        "session_notification_created",
    ]


def test_revision_conflict_and_terminal_transition_are_rejected(tmp_path: Path) -> None:
    app, _store, session_id = _make_app(tmp_path)
    created = app.create_session_notification(session_id, _notification())
    updated = app.update_session_notification(
        session_id,
        created["id"],
        {"body": "new body"},
        expected_revision=created["revision"],
    )

    with pytest.raises(NotificationRevisionConflictError) as revision_error:
        app.dismiss_session_notification(
            session_id,
            created["id"],
            expected_revision=created["revision"],
        )
    assert revision_error.value.current == updated

    dismissed = app.dismiss_session_notification(
        session_id,
        created["id"],
        expected_revision=updated["revision"],
    )
    with pytest.raises(NotificationTransitionError):
        app.resolve_session_notification(
            session_id,
            created["id"],
            {"action_id": "too-late"},
            expected_revision=dismissed["revision"],
        )


def test_legacy_updated_at_token_is_accepted_on_first_mutation(tmp_path: Path) -> None:
    app, _store, session_id = _make_app(tmp_path)
    created = app.create_session_notification(session_id, _notification())
    session = app.load_live_session_record(session_id)
    assert session is not None
    legacy = {key: value for key, value in created.items() if key != "revision"}
    app.save_session(
        Session(
            session_id=session.session_id,
            messages=session.messages,
            metadata={
                **session.metadata,
                "notifications": {"items": [legacy]},
            },
        )
    )

    dismissed = app.dismiss_session_notification(
        session_id,
        legacy["id"],
        expected_revision=legacy["updated_at"],
    )

    assert dismissed["status"] == "dismissed"
    assert dismissed["revision"] == 1


def test_expire_records_terminal_metadata(tmp_path: Path) -> None:
    app, store, session_id = _make_app(tmp_path)
    created = app.create_session_notification(session_id, _notification())

    expired = app.expire_session_notification(
        session_id,
        created["id"],
        reason="manual-test",
        expected_revision=created["revision"],
    )

    assert expired["status"] == "expired"
    assert expired["expiration"]["reason"] == "manual-test"
    assert expired["revision"] == 2
    events = store.list(since_id="0", session_id=session_id, limit=20)["events"]
    assert "session_notification_expired" in {event["type"] for event in events}
