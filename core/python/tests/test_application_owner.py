from __future__ import annotations

import threading
from typing import Any

from agent_app.application_notifications import (
    ApplicationNotificationMutation,
    InMemoryApplicationNotificationStore,
)
from agent_app.application_owner import (
    AgentApplicationOwner,
    ApplicationReloadPendingError,
)
from agent_app.events import InMemoryEventStore


class _FakeApplication:
    def __init__(
        self,
        name: str,
        closed: list[str],
        *,
        notification_store: InMemoryApplicationNotificationStore,
        event_store: Any,
    ) -> None:
        self.name = name
        self._closed = closed
        self._notification_store = notification_store
        self._event_store = event_store

    def close(self) -> None:
        self._closed.append(self.name)

    def create_application_notification(
        self,
        notification: dict[str, Any],
    ) -> dict[str, Any]:
        return self._complete(self._notification_store.create(notification))

    def update_application_notification(
        self,
        notification_id: str,
        patch: dict[str, Any],
        *,
        expected_revision: int | str | None = None,
    ) -> dict[str, Any]:
        return self._complete(
            self._notification_store.update(
                notification_id,
                patch,
                expected_revision=expected_revision,
            )
        )

    def _complete(
        self,
        mutation: ApplicationNotificationMutation,
    ) -> dict[str, Any]:
        if mutation.event_type is not None:
            try:
                self._event_store.publish(
                    {
                        "type": mutation.event_type,
                        "notification": mutation.notification,
                    }
                )
            except Exception:
                pass
        return mutation.notification


def _factory(
    closed: list[str],
    created: list[_FakeApplication],
    *,
    notification_store: InMemoryApplicationNotificationStore,
    event_store: Any,
):
    def create(_control: Any) -> _FakeApplication:
        application = _FakeApplication(
            f"app-{len(created) + 1}",
            closed,
            notification_store=notification_store,
            event_store=event_store,
        )
        created.append(application)
        return application

    return create


def test_owner_waits_for_active_operation_then_replaces_application() -> None:
    event_store = InMemoryEventStore()
    notification_store = InMemoryApplicationNotificationStore()
    closed: list[str] = []
    created: list[_FakeApplication] = []
    owner = AgentApplicationOwner(
        _factory(
            closed,
            created,
            notification_store=notification_store,
            event_store=event_store,
        ),
        event_store=event_store,
    )
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
        "application_notification_created",
        "application_reload_requested",
        "application_reload_ready",
        "application_notification_updated",
        "application_reload_completed",
    ]
    assert events[0]["notification"]["revision"] == 1
    assert events[-2]["notification"]["revision"] == 2
    assert events[-2]["notification"]["title"] == "Application reload completed"


def test_owner_candidate_failure_keeps_old_application_and_runs_rollback() -> None:
    event_store = InMemoryEventStore()
    notification_store = InMemoryApplicationNotificationStore()
    closed: list[str] = []
    attempts = 0
    rollback = threading.Event()

    def factory(_control: Any) -> _FakeApplication:
        nonlocal attempts
        attempts += 1
        if attempts == 2:
            raise RuntimeError("candidate invalid")
        return _FakeApplication(
            "old",
            closed,
            notification_store=notification_store,
            event_store=event_store,
        )

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
    assert events[-1]["type"] == "application_reload_failed"
    assert events[-2]["type"] == "application_notification_updated"
    assert events[-2]["notification"]["title"] == "Application reload failed"


def test_notification_publish_failure_does_not_block_reload() -> None:
    class _FailingEventStore:
        def publish(self, event: dict[str, Any]) -> dict[str, Any]:
            _ = event
            raise RuntimeError("event store unavailable")

    event_store = _FailingEventStore()
    notification_store = InMemoryApplicationNotificationStore()
    closed: list[str] = []
    created: list[_FakeApplication] = []
    owner = AgentApplicationOwner(
        _factory(
            closed,
            created,
            notification_store=notification_store,
            event_store=event_store,
        ),
        event_store=event_store,  # type: ignore[arg-type]
    )
    result = owner.request_reload(reason="test")

    assert owner.wait_for_reload(result["reload_id"], timeout=2)
    assert owner.current is created[1]
    assert closed == ["app-1"]
