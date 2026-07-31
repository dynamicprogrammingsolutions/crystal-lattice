from __future__ import annotations

import json
from pathlib import Path

from fastapi.testclient import TestClient

from agent_app.application_future import AgentApplication
from agent_app.application_owner import AgentApplicationOwner, ApplicationControl
from agent_app.events import InMemoryEventStore
from agent_terminal_app import server as server_mod


ROOT = Path(__file__).resolve().parents[3]


def _owner(tmp_path: Path) -> AgentApplicationOwner:
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

    def factory(control: ApplicationControl) -> AgentApplication:
        return AgentApplication(
            config_path,
            tmp_path / "sessions",
            event_store=event_store,
            application_control=control,
        )

    owner = AgentApplicationOwner(factory, event_store=event_store)
    server_mod.configure_application_owner(owner)
    return owner


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
            "emit_session_notification",
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

        events = client.get(
            "/events",
            params={"since_id": "0", "session_id": session_id},
        ).json()["events"]
        assert "session_notification_created" in {event["type"] for event in events}
