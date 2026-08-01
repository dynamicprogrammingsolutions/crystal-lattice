from __future__ import annotations

import json
from pathlib import Path

from agent_app.application_future import AgentApplication
from agent_app.application_notifications import (
    InMemoryApplicationNotificationStore,
    SQLiteApplicationNotificationStore,
    resolve_application_notification_store_path,
)
from agent_app.events import InMemoryEventStore
from agent_app.notifications import (
    NotificationRevisionConflictError,
    NotificationTransitionError,
)


def _write_config(path: Path) -> None:
    path.write_text(
        json.dumps({"providers": {}, "agents": {}, "plugins": []}),
        encoding="utf-8",
    )


def _notification(
    *,
    key: str = "dummy:application",
    title: str = "Application notification",
    body: str = "Created",
) -> dict[str, object]:
    return {
        "key": key,
        "severity": "info",
        "title": title,
        "body": body,
        "source": {"plugin": "dummy_application_notification"},
        "display": {
            "format": "text",
            "presentation": "banner",
        },
        "model_visibility": "hidden",
    }


def test_agent_application_owns_public_application_notification_contract(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.json"
    _write_config(config_path)
    event_store = InMemoryEventStore()
    notification_store = InMemoryApplicationNotificationStore()
    application = AgentApplication(
        config_path,
        tmp_path / "sessions",
        event_store=event_store,
        application_notification_store=notification_store,
    )

    created = application.create_application_notification(_notification())
    updated = application.create_application_notification(_notification(body="Updated"))
    resolved = application.resolve_application_notification(
        created["id"],
        {"action_id": "resolve_dummy"},
        expected_revision=updated["revision"],
    )

    assert updated["id"] == created["id"]
    assert created["revision"] == 1
    assert updated["revision"] == 2
    assert resolved["status"] == "resolved"
    assert resolved["revision"] == 3
    assert application.list_application_notifications() == [resolved]
    events = event_store.list(since_id="0", limit=10)["events"]
    assert [event["type"] for event in events] == [
        "application_notification_created",
        "application_notification_updated",
        "application_notification_updated",
    ]
    application.close()


def test_application_notification_validation_and_revision_conflicts(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.json"
    _write_config(config_path)
    application = AgentApplication(
        config_path,
        tmp_path / "sessions",
        application_notification_store=InMemoryApplicationNotificationStore(),
    )

    try:
        application.create_application_notification(
            {
                **_notification(key="dummy:inline"),
                "display": {"format": "text", "presentation": "inline"},
            }
        )
    except ValueError as exc:
        assert "['banner', 'modal']" in str(exc)
    else:
        raise AssertionError("inline application notifications must be rejected")

    created = application.create_application_notification(_notification())
    updated = application.update_application_notification(
        created["id"],
        {"body": "Updated"},
        expected_revision=created["revision"],
    )
    try:
        application.dismiss_application_notification(
            created["id"],
            expected_revision=created["revision"],
        )
    except NotificationRevisionConflictError as exc:
        assert exc.current == updated
    else:
        raise AssertionError("stale notification revision must be rejected")

    expired = application.expire_application_notification(
        created["id"],
        reason="manual",
        expected_revision=updated["revision"],
    )
    try:
        application.resolve_application_notification(
            created["id"],
            {"action_id": "too-late"},
            expected_revision=expired["revision"],
        )
    except NotificationTransitionError:
        pass
    else:
        raise AssertionError("terminal notification transition must be rejected")
    application.close()


def test_sqlite_application_notifications_survive_store_and_application_restart(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.json"
    _write_config(config_path)
    database_path = tmp_path / "notifications.sqlite3"
    first_store = SQLiteApplicationNotificationStore(database_path)
    first_application = AgentApplication(
        config_path,
        tmp_path / "sessions",
        application_notification_store=first_store,
    )
    created = first_application.create_application_notification(_notification())
    dismissed = first_application.dismiss_application_notification(
        created["id"],
        reason="user",
        expected_revision=created["revision"],
    )
    first_application.close()

    replacement_generation = AgentApplication(
        config_path,
        tmp_path / "sessions",
        application_notification_store=first_store,
    )
    assert replacement_generation.list_application_notifications() == [dismissed]
    replacement_generation.close()
    first_store.close()

    second_store = SQLiteApplicationNotificationStore(database_path)
    second_application = AgentApplication(
        config_path,
        tmp_path / "sessions",
        application_notification_store=second_store,
    )
    assert second_application.list_application_notifications() == [dismissed]
    assert (
        second_application.list_application_notifications(include_terminal=False) == []
    )

    replacement = second_application.create_application_notification(
        _notification(body="New occurrence")
    )
    assert replacement["id"] != created["id"]
    assert replacement["revision"] == 1
    second_application.close()
    second_store.close()


def test_owner_lifetime_recovery_expires_old_pending_records(tmp_path: Path) -> None:
    store = SQLiteApplicationNotificationStore(tmp_path / "notifications.sqlite3")
    created = store.create(
        {
            **_notification(key="application:reload"),
            "retention": {
                "policy": "until_server_restart",
                "owner_epoch": "owner-old",
            },
        }
    ).notification

    recovered = store.recover_owner_lifetime("owner-new")

    assert len(recovered) == 1
    assert recovered[0].notification["id"] == created["id"]
    assert recovered[0].notification["status"] == "expired"
    assert recovered[0].notification["revision"] == 2
    assert recovered[0].notification["expiration"]["reason"] == "owner_restarted"
    assert store.recover_owner_lifetime("owner-new") == []
    store.close()


def test_application_notification_store_path_uses_config_directory(
    tmp_path: Path,
) -> None:
    config_path = tmp_path / "config.json"

    assert (
        resolve_application_notification_store_path(config_path, {})
        == tmp_path / "application-notifications.sqlite3"
    )
    assert (
        resolve_application_notification_store_path(
            config_path,
            {
                "application": {
                    "notifications": {
                        "store": {
                            "type": "sqlite",
                            "path": "state/notifications.db",
                        }
                    }
                }
            },
        )
        == tmp_path / "state" / "notifications.db"
    )
