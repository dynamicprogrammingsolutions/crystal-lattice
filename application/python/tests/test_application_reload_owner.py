from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from dotenv import dotenv_values

from agent_app.application_future import AgentApplication
from agent_app.application_notifications import InMemoryApplicationNotificationStore
from agent_app.application_owner import AgentApplicationOwner, ApplicationControl
from agent_app.events import InMemoryEventStore
from agent_terminal_app import server as server_mod


ROOT = Path(__file__).resolve().parents[3]


def _write_config(path: Path, *, include_dummy: bool = False) -> None:
    plugins: list[Any] = [
        {
            "path": str(ROOT / "plugins" / "application-config-app"),
            "entry": "application_config_app.ApplicationConfigAppPlugin",
        }
    ]
    if include_dummy:
        plugins.append("tests.dummy_app_plugin.DummyAppPlugin")
    path.write_text(
        json.dumps(
            {
                "providers": {},
                "agents": {},
                "plugins": plugins,
                "application": {
                    "observed_key": "${env:TEST_PROVIDER_KEY}",
                    "application_config": {
                        "env_file": str(path.parent / ".env"),
                        "editable_env_keys": ["TEST_PROVIDER_KEY"],
                        "provider_env_keys": {"test": "TEST_PROVIDER_KEY"},
                    },
                },
            }
        ),
        encoding="utf-8",
    )


def _build_owner(
    tmp_path: Path,
) -> tuple[AgentApplicationOwner, Path, InMemoryEventStore]:
    config_path = tmp_path / "config.json"
    _write_config(config_path)
    event_store = InMemoryEventStore()
    notification_store = InMemoryApplicationNotificationStore()

    def factory(control: ApplicationControl) -> AgentApplication:
        return AgentApplication(
            config_path,
            tmp_path / "sessions",
            event_store=event_store,
            application_notification_store=notification_store,
            application_control=control,
            config_env={
                key: value
                for key, value in dotenv_values(tmp_path / ".env").items()
                if isinstance(key, str) and isinstance(value, str)
            },
        )

    owner = AgentApplicationOwner(factory, event_store=event_store)
    server_mod.configure_application_owner(owner)
    return owner, config_path, event_store


def test_reload_action_returns_accepted_then_replaces_after_drain(
    tmp_path: Path,
) -> None:
    owner, config_path, event_store = _build_owner(tmp_path)
    old_application = owner.current
    retained = owner.acquire_operation()
    _write_config(config_path, include_dummy=True)

    with TestClient(server_mod.app) as client:
        response = client.post(
            "/actions",
            json={
                "plugin": "application_config",
                "action_id": "reload_application",
                "inputs": {},
            },
        )
        assert response.status_code == 200
        payload = response.json()
        assert payload["status"] == "ok"
        assert payload["result"]["status"] == "ok"
        assert payload["result"]["reload_status"] == "accepted"
        reload_id = payload["result"]["reload_id"]
        assert owner.current is old_application

        pending = client.get("/application/actions")
        assert pending.status_code == 503
        assert pending.json()["detail"]["error_type"] == "application_reload_pending"

        retained.release()
        assert owner.wait_for_reload(reload_id, timeout=20)
        assert owner.current is not old_application
        action_ids = {
            action["id"] for action in owner.current.get_application_actions()
        }
        assert "do_dummy" in action_ids

        events = event_store.list(since_id="0", limit=50)["events"]
        assert "application_reload_requested" in {event["type"] for event in events}
        assert "application_reload_completed" in {event["type"] for event in events}


def test_invalid_candidate_keeps_old_application_and_reopens_admission(
    tmp_path: Path,
) -> None:
    owner, config_path, event_store = _build_owner(tmp_path)
    old_application = owner.current
    config_path.write_text(
        json.dumps(
            {
                "providers": {},
                "agents": {},
                "plugins": ["missing.module.Plugin"],
            }
        ),
        encoding="utf-8",
    )

    with TestClient(server_mod.app) as client:
        response = client.post(
            "/actions",
            json={
                "plugin": "application_config",
                "action_id": "reload_application",
                "inputs": {},
            },
        )
        reload_id = response.json()["result"]["reload_id"]
        assert owner.wait_for_reload(reload_id, timeout=20)
        assert owner.current is old_application

        actions = client.get("/application/actions")
        assert actions.status_code == 200
        assert any(
            action["id"] == "reload_application" for action in actions.json()["actions"]
        )
        events = event_store.list(since_id="0", limit=50)["events"]
        assert "application_reload_failed" in {event["type"] for event in events}


def test_provider_key_action_reloads_new_dotenv_value(tmp_path: Path) -> None:
    (tmp_path / ".env").write_text("TEST_PROVIDER_KEY='old'\n", encoding="utf-8")
    owner, _config_path, _event_store = _build_owner(tmp_path)

    with TestClient(server_mod.app) as client:
        response = client.post(
            "/actions",
            json={
                "plugin": "application_config",
                "action_id": "set_provider_api_key",
                "inputs": {
                    "provider_id": "test",
                    "api_key": "new-value",
                },
            },
        )
        assert response.status_code == 200
        result = response.json()["result"]
        assert result["status"] == "ok"
        assert result["reload_status"] == "accepted"
        assert owner.wait_for_reload(result["reload_id"], timeout=20)
        assert owner.current.get_application_config()["observed_key"] == "new-value"


def test_provider_key_action_rolls_back_dotenv_when_candidate_fails(
    tmp_path: Path,
) -> None:
    env_path = tmp_path / ".env"
    env_path.write_text("TEST_PROVIDER_KEY='old'\n", encoding="utf-8")
    owner, config_path, _event_store = _build_owner(tmp_path)
    config_path.write_text("{invalid json", encoding="utf-8")

    with TestClient(server_mod.app) as client:
        response = client.post(
            "/actions",
            json={
                "plugin": "application_config",
                "action_id": "set_provider_api_key",
                "inputs": {
                    "provider_id": "test",
                    "api_key": "new-value",
                },
            },
        )
        result = response.json()["result"]
        assert owner.wait_for_reload(result["reload_id"], timeout=20)
        assert dotenv_values(env_path)["TEST_PROVIDER_KEY"] == "old"
