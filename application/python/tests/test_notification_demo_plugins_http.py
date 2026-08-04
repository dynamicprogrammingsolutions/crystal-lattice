from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from agent_app.application_future import AgentApplication
from agent_app.application_notifications import (
    ApplicationNotificationStore,
    InMemoryApplicationNotificationStore,
    SQLiteApplicationNotificationStore,
)
from agent_app.application_owner import AgentApplicationOwner, ApplicationControl
from agent_app.events import InMemoryEventStore
from agent_terminal_app import server as server_mod


ROOT = Path(__file__).resolve().parents[3]


def _owner(
    tmp_path: Path,
    *,
    notification_store: ApplicationNotificationStore | None = None,
) -> AgentApplicationOwner:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "providers": {
                    "dummy": {
                        "provider": "dummy_provider",
                        "model": "test-model",
                    }
                },
                "agents": {"default": {"provider": "dummy"}},
                "plugins": [
                    "tests.dummy_provider.DummyProvider",
                    {
                        "path": str(
                            ROOT / "plugins" / "dummy-application-notification-app"
                        ),
                        "entry": "dummy_application_notification_app.DummyApplicationNotificationPlugin",
                    },
                    {
                        "path": str(
                            ROOT / "plugins" / "dummy-session-notification-app"
                        ),
                        "entry": "dummy_session_notification_app.DummySessionNotificationPlugin",
                    },
                    {
                        "path": str(ROOT / "plugins" / "dummy-action-display-app"),
                        "entry": "dummy_action_display_app.DummyActionDisplayPlugin",
                    },
                ],
            }
        ),
        encoding="utf-8",
    )
    event_store = InMemoryEventStore()
    effective_notification_store = (
        notification_store or InMemoryApplicationNotificationStore()
    )

    def factory(control: ApplicationControl) -> AgentApplication:
        return AgentApplication(
            config_path,
            tmp_path / "sessions",
            event_store=event_store,
            application_notification_store=effective_notification_store,
            application_control=control,
        )

    owner = AgentApplicationOwner(factory, event_store=event_store)
    server_mod.configure_application_owner(owner)
    return owner


def test_application_notification_history_survives_server_owner_restart(
    tmp_path: Path,
) -> None:
    database_path = tmp_path / "application-notifications.sqlite3"
    first_store = SQLiteApplicationNotificationStore(database_path)
    first_owner = _owner(tmp_path, notification_store=first_store)
    with TestClient(server_mod.app) as client:
        response = client.post(
            "/actions",
            json={
                "plugin": "dummy_application_notification",
                "action_id": "emit_application_notification",
                "inputs": {"presentation": "banner", "variant": "success"},
            },
        )
        assert response.status_code == 200
        notification = client.get("/application/notifications").json()["notifications"][
            0
        ]
        dismissed = client.post(
            f"/application/notifications/{notification['id']}/dismiss",
            json={"expected_revision": notification["revision"]},
        ).json()["notification"]
    first_owner.close()
    first_store.close()

    second_store = SQLiteApplicationNotificationStore(database_path)
    second_owner = _owner(tmp_path, notification_store=second_store)
    with TestClient(server_mod.app) as client:
        assert client.get("/application/notifications").json()["notifications"] == []
        assert client.get(
            "/application/notifications",
            params={"include_terminal": True},
        ).json()["notifications"] == [dismissed]
    second_owner.close()
    second_store.close()


def test_notification_ui_effects_survive_public_http_contract(
    tmp_path: Path,
) -> None:
    owner = _owner(tmp_path)
    with TestClient(server_mod.app) as client:
        created = client.post("/sessions", json={"agent_id": "default"}).json()
        session_id = created["session"]["session_id"]
        common = {
            "severity": "success",
            "title": "Refresh requested",
            "body": "Refresh connection data.",
            "source": {"plugin": "http_contract_test"},
            "model_visibility": "hidden",
            "ui_effects": {
                "reload_session_ids": [session_id],
                "reload_sessions_list": True,
                "reload_application_actions": True,
                "plugin_detail": {"preserved": True},
            },
        }
        owner.current.create_application_notification(
            {
                **common,
                "key": "http:application:ui-effects",
                "display": {"format": "text", "presentation": "banner"},
            }
        )
        owner.current.create_session_notification(
            session_id,
            {
                **common,
                "key": "http:session:ui-effects",
                "display": {"format": "text", "presentation": "inline"},
            },
        )

        application_notification = client.get("/application/notifications").json()[
            "notifications"
        ][0]
        session_notification = client.get(
            f"/sessions/{session_id}/notifications"
        ).json()["notifications"][0]

        assert application_notification["ui_effects"] == common["ui_effects"]
        assert session_notification["ui_effects"] == common["ui_effects"]
        events = client.get(
            "/events",
            params={"since_id": "0", "session_id": session_id},
        ).json()["events"]
        assert any(
            event.get("notification", {}).get("ui_effects") == common["ui_effects"]
            for event in events
        )
    owner.close()


def test_demo_plugins_exercise_public_notification_and_display_contract(
    tmp_path: Path,
) -> None:
    owner = _owner(tmp_path)
    with TestClient(server_mod.app) as client:
        action_ids = {
            action["id"]
            for action in client.get("/application/actions").json()["actions"]
        }
        assert {
            "emit_application_notification",
            "expire_application_notification",
            "emit_session_notification",
            "expire_session_notification",
            "show_action_display",
        } <= action_ids

        application_response = client.post(
            "/actions",
            json={
                "plugin": "dummy_application_notification",
                "action_id": "emit_application_notification",
                "inputs": {"presentation": "banner", "variant": "success"},
            },
        ).json()
        assert application_response["status"] == "ok"
        application_notification = client.get("/application/notifications").json()[
            "notifications"
        ][0]
        assert application_notification["revision"] == 1

        application_dismiss = client.post(
            f"/application/notifications/{application_notification['id']}/dismiss",
            json={
                "expected_revision": application_notification["revision"],
                "reason": "integration-test",
            },
        )
        assert application_dismiss.status_code == 200
        dismissed_application_notification = application_dismiss.json()["notification"]
        assert dismissed_application_notification["status"] == "dismissed"
        assert dismissed_application_notification["revision"] == 2
        assert client.get("/application/notifications").json()["notifications"] == []
        assert client.get(
            "/application/notifications",
            params={"include_terminal": True},
        ).json()["notifications"] == [dismissed_application_notification]

        stale_application_dismiss = client.post(
            f"/application/notifications/{application_notification['id']}/dismiss",
            json={"expected_revision": application_notification["revision"]},
        )
        assert stale_application_dismiss.status_code == 409
        assert (
            stale_application_dismiss.json()["detail"]["error_type"]
            == "notification_revision_conflict"
        )

        client.post(
            "/actions",
            json={
                "plugin": "dummy_application_notification",
                "action_id": "emit_application_notification",
                "inputs": {"presentation": "banner", "variant": "warning"},
            },
        )
        application_expire = client.post(
            "/actions",
            json={
                "plugin": "dummy_application_notification",
                "action_id": "expire_application_notification",
                "inputs": {},
            },
        ).json()
        assert application_expire["status"] == "ok"
        assert any(
            item["status"] == "expired"
            for item in client.get(
                "/application/notifications",
                params={"include_terminal": True},
            ).json()["notifications"]
        )

        unsupported_application_response = client.post(
            "/actions",
            json={
                "plugin": "dummy_application_notification",
                "action_id": "emit_application_notification",
                "inputs": {"presentation": "inline", "variant": "info"},
            },
        ).json()
        assert unsupported_application_response["status"] == "error"
        assert "['banner', 'modal']" in unsupported_application_response["message"]

        display_response = client.post(
            "/actions",
            json={
                "plugin": "dummy_action_display",
                "action_id": "show_action_display",
                "inputs": {"presentation": "modal", "variant": "warning"},
            },
        ).json()
        assert display_response["result"]["display"]["presentation"] == "modal"

        created = client.post("/sessions", json={"agent_id": "default"}).json()
        session_id = created["session"]["session_id"]
        session_response = client.post(
            f"/sessions/{session_id}/actions",
            json={
                "plugin": "dummy_session_notification",
                "action_id": "emit_session_notification",
                "action_owner": "application",
                "inputs": {"presentation": "inline", "variant": "info"},
            },
        ).json()
        assert session_response["status"] == "ok"

        stored = owner.current.load_live_session_record(session_id)
        assert stored is not None
        notification = stored.metadata["notifications"]["items"][0]
        assert notification["display"]["presentation"] == "inline"
        assert notification["model_visibility"] == "hidden"
        assert client.get(f"/sessions/{session_id}/notifications").json()[
            "notifications"
        ] == [notification]

        session_dismiss = client.post(
            f"/sessions/{session_id}/notifications/{notification['id']}/dismiss",
            json={
                "expected_revision": notification["revision"],
                "reason": "integration-test",
            },
        )
        assert session_dismiss.status_code == 200
        dismissed_session_notification = session_dismiss.json()["notification"]
        assert dismissed_session_notification["status"] == "dismissed"
        assert dismissed_session_notification["revision"] == 2
        assert (
            client.get(f"/sessions/{session_id}/notifications").json()["notifications"]
            == []
        )
        assert client.get(
            f"/sessions/{session_id}/notifications",
            params={"include_terminal": True},
        ).json()["notifications"] == [dismissed_session_notification]

        client.post(
            f"/sessions/{session_id}/actions",
            json={
                "plugin": "dummy_session_notification",
                "action_id": "emit_session_notification",
                "action_owner": "application",
                "inputs": {"presentation": "inline", "variant": "warning"},
            },
        )
        session_expire = client.post(
            f"/sessions/{session_id}/actions",
            json={
                "plugin": "dummy_session_notification",
                "action_id": "expire_session_notification",
                "action_owner": "application",
                "inputs": {},
            },
        ).json()
        assert session_expire["status"] == "ok"
        assert any(
            item["status"] == "expired"
            for item in client.get(
                f"/sessions/{session_id}/notifications",
                params={"include_terminal": True},
            ).json()["notifications"]
        )

        events = client.get(
            "/events",
            params={"since_id": "0", "session_id": session_id},
        ).json()["events"]
        event_types = {event["type"] for event in events}
        assert "session_notification_created" in event_types
        assert "session_notification_dismissed" in event_types
