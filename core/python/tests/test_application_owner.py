from __future__ import annotations

import threading
from typing import Any

from agent_app.application_owner import (
    AgentApplicationOwner,
    ApplicationReloadPendingError,
)
from agent_app.events import InMemoryEventStore
from agent_app.notifications import (
    NotificationRevisionConflictError,
    NotificationTransitionError,
)


class _FakeApplication:
    def __init__(self, name: str, closed: list[str]) -> None:
        self.name = name
        self._closed = closed

    def close(self) -> None:
        self._closed.append(self.name)


def test_owner_waits_for_active_operation_then_replaces_application() -> None:
    event_store = InMemoryEventStore()
    closed: list[str] = []
    created: list[_FakeApplication] = []

    def factory(_control: Any) -> _FakeApplication:
        application = _FakeApplication(f"app-{len(created) + 1}", closed)
        created.append(application)
        return application

    owner = AgentApplicationOwner(factory, event_store=event_store)
    operation = owner.acquire_operation()
    result = owner.request_reload(reason="test")

    assert result["status"] == "ok"
    assert result["reload_status"] == "accepted"
    assert owner.reload_pending is True
    assert owner.wait_for_reload(result["reload_id"], timeout=0.01) is False
    try:
        owner.acquire_operation()
    except ApplicationReloadPendingError:
        pass
    else:
        raise AssertionError("new operation should be rejected during reload")

    operation.release()

    assert owner.wait_for_reload(result["reload_id"], timeout=2) is True
    assert owner.current is created[1]
    assert closed == ["app-1"]
    events = event_store.list(since_id="0", limit=20)["events"]
    assert [event["type"] for event in events] == [
        "application_reload_requested",
        "application_notification_created",
        "application_reload_ready",
        "application_reload_completed",
        "application_notification_updated",
    ]
    assert events[1]["notification"]["revision"] == 1
    assert events[-1]["notification"]["revision"] == 2
    assert events[-1]["notification"]["title"] == "Application reload completed"


def test_owner_candidate_failure_keeps_old_application_and_runs_rollback() -> None:
    event_store = InMemoryEventStore()
    closed: list[str] = []
    attempts = 0
    rollback = threading.Event()

    def factory(_control: Any) -> _FakeApplication:
        nonlocal attempts
        attempts += 1
        if attempts == 2:
            raise RuntimeError("candidate invalid")
        return _FakeApplication("old", closed)

    owner = AgentApplicationOwner(factory, event_store=event_store)
    old = owner.current
    result = owner.request_reload(reason="test", on_failure=rollback.set)

    assert owner.wait_for_reload(result["reload_id"], timeout=2) is True
    assert rollback.is_set()
    assert owner.current is old
    assert closed == []
    with owner.acquire_operation() as current:
        assert current is old
    events = event_store.list(since_id="0", limit=20)["events"]
    assert events[-1]["type"] == "application_notification_updated"
    assert events[-1]["notification"]["title"] == "Application reload failed"


def test_notification_publish_failure_does_not_block_reload() -> None:
    class _FailingEventStore:
        def publish(self, event: dict[str, Any]) -> dict[str, Any]:
            _ = event
            raise RuntimeError("event store unavailable")

    closed: list[str] = []
    created: list[_FakeApplication] = []

    def factory(_control: Any) -> _FakeApplication:
        application = _FakeApplication(f"app-{len(created) + 1}", closed)
        created.append(application)
        return application

    owner = AgentApplicationOwner(
        factory,
        event_store=_FailingEventStore(),  # type: ignore[arg-type]
    )
    result = owner.request_reload(reason="test")

    assert owner.wait_for_reload(result["reload_id"], timeout=2)
    assert owner.current is created[1]
    assert closed == ["app-1"]


def test_owner_application_notifications_create_update_and_resolve() -> None:
    event_store = InMemoryEventStore()
    owner = AgentApplicationOwner(
        lambda _control: _FakeApplication("app", []),
        event_store=event_store,
    )

    created = owner.create_notification(
        {
            "key": "dummy:application",
            "severity": "info",
            "title": "Application notification",
            "body": "Created",
            "source": {"plugin": "dummy_application_notification"},
            "display": {
                "format": "text",
                "presentation": "banner",
            },
            "model_visibility": "hidden",
        }
    )
    updated = owner.create_notification(
        {
            "key": "dummy:application",
            "severity": "success",
            "title": "Application notification",
            "body": "Updated",
            "source": {"plugin": "dummy_application_notification"},
            "display": {
                "format": "text",
                "presentation": "banner",
            },
            "model_visibility": "hidden",
        }
    )
    resolved = owner.resolve_notification(created["id"], {"action_id": "resolve_dummy"})

    assert updated["id"] == created["id"]
    assert created["revision"] == 1
    assert updated["revision"] == 2
    assert resolved["status"] == "resolved"
    assert resolved["revision"] == 3
    assert owner.list_notifications() == [resolved]
    events = event_store.list(since_id="0", limit=10)["events"]
    assert [event["type"] for event in events] == [
        "application_notification_created",
        "application_notification_updated",
        "application_notification_updated",
    ]


def test_owner_rejects_inline_application_notifications() -> None:
    owner = AgentApplicationOwner(
        lambda _control: _FakeApplication("app", []),
        event_store=InMemoryEventStore(),
    )

    try:
        owner.create_notification(
            {
                "key": "dummy:inline",
                "severity": "info",
                "title": "Unsupported inline notification",
                "body": "Application notifications do not have an inline surface.",
                "source": {"plugin": "dummy"},
                "display": {
                    "format": "text",
                    "presentation": "inline",
                },
                "model_visibility": "hidden",
            }
        )
    except ValueError as exc:
        assert "['banner', 'modal']" in str(exc)
    else:
        raise AssertionError("inline application notifications must be rejected")


def test_owner_notification_dismiss_snapshot_and_new_occurrence() -> None:
    event_store = InMemoryEventStore()
    owner = AgentApplicationOwner(
        lambda _control: _FakeApplication("app", []),
        event_store=event_store,
    )
    created = owner.create_notification(
        {
            "key": "dummy:application",
            "severity": "info",
            "title": "Application notification",
            "body": "Created",
            "source": {"plugin": "dummy_application_notification"},
            "display": {"format": "text", "presentation": "banner"},
            "model_visibility": "hidden",
        }
    )

    dismissed = owner.dismiss_notification(
        created["id"],
        reason="user",
        expected_revision=created["revision"],
    )
    assert dismissed["status"] == "dismissed"
    assert dismissed["revision"] == 2
    assert owner.list_notifications(include_terminal=False) == []
    assert owner.list_notifications(include_terminal=True) == [dismissed]

    replacement = owner.create_notification(
        {
            "key": "dummy:application",
            "severity": "warning",
            "title": "Application notification again",
            "body": "New occurrence",
            "source": {"plugin": "dummy_application_notification"},
            "display": {"format": "text", "presentation": "banner"},
            "model_visibility": "hidden",
        }
    )
    assert replacement["id"] != created["id"]
    assert replacement["revision"] == 1

    events = event_store.list(since_id="0", limit=20)["events"]
    assert [event["type"] for event in events] == [
        "application_notification_created",
        "application_notification_dismissed",
        "application_notification_created",
    ]


def test_owner_notification_revision_and_transition_conflicts() -> None:
    owner = AgentApplicationOwner(
        lambda _control: _FakeApplication("app", []),
        event_store=InMemoryEventStore(),
    )
    created = owner.create_notification(
        {
            "key": "dummy:application",
            "severity": "info",
            "title": "Application notification",
            "body": "Created",
            "source": {"plugin": "dummy_application_notification"},
            "display": {"format": "text", "presentation": "banner"},
            "model_visibility": "hidden",
        }
    )
    updated = owner.update_notification(
        created["id"],
        {"body": "Updated"},
        expected_revision=created["revision"],
    )

    try:
        owner.dismiss_notification(
            created["id"],
            expected_revision=created["revision"],
        )
    except NotificationRevisionConflictError as exc:
        assert exc.current == updated
    else:
        raise AssertionError("stale notification revision must be rejected")

    expired = owner.expire_notification(
        created["id"],
        reason="manual",
        expected_revision=updated["revision"],
    )
    assert expired["status"] == "expired"
    assert expired["expiration"]["reason"] == "manual"

    try:
        owner.resolve_notification(
            created["id"],
            {"action_id": "too-late"},
            expected_revision=expired["revision"],
        )
    except NotificationTransitionError:
        pass
    else:
        raise AssertionError("terminal notification transition must be rejected")
