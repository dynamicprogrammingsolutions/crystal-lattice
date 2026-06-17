from __future__ import annotations

import json
from pathlib import Path
import sys
from typing import Any, Dict

import pytest

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


ROOT = Path(__file__).resolve().parents[3]
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))


def _make_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"},
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            "tests.dummy_settings_app_plugin.DummySettingsAppPlugin",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {},
    }
    path = tmp_path / "config_server_settings.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _make_config_with_runtime_dummy_settings_plugin(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"},
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            f"path:{ROOT / 'plugins' / 'dummy-settings-app'}",
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {},
    }
    path = tmp_path / "config_runtime_dummy_settings.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    from agent_terminal_app import server as server_mod

    previous = getattr(server_mod, "_agent_app", None)
    if previous is not None:
        previous.close()

    app = AgentApplication(
        str(_make_config(tmp_path)),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    server_mod._agent_app = app
    return app


def test_server_settings_routes_patch_get_and_delete(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    assert server_mod.get_server_settings(app_instance=app) == {"settings": {}}

    patched = server_mod.patch_server_settings(
        {"values": {"dummy_server_mode": "careful"}},
        app_instance=app,
    )
    assert patched == {"settings": {"dummy_server_mode": "careful"}}
    assert server_mod.get_server_settings(app_instance=app) == patched

    deleted = server_mod.delete_server_setting(
        "dummy_server_mode",
        app_instance=app,
    )
    assert deleted == {"settings": {}}


def test_server_settings_patch_accepts_plain_object_body(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    patched = server_mod.patch_server_settings(
        {"dummy_server_enabled": True},
        app_instance=app,
    )

    assert patched == {"settings": {"dummy_server_enabled": True}}


def test_server_settings_patch_rejects_invalid_values_payload(tmp_path: Path) -> None:
    from fastapi import HTTPException
    from agent_terminal_app import server as server_mod

    app = _build_app(tmp_path)

    with pytest.raises(HTTPException) as exc_info:
        server_mod.patch_server_settings(
            {"values": ["not", "an", "object"]},
            app_instance=app,
        )

    assert exc_info.value.status_code == 400


def test_session_override_routes_use_application_settings_lifecycle(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod
    from tests.dummy_settings_app_plugin import DummySettingsAppPlugin

    app = _build_app(tmp_path)
    _core, _base_config, session = app.create_session("default")

    response = server_mod.patch_session_overrides(
        session.session_id,
        {"values": {"dummy_session_mode": "alpha"}},
        app_instance=app,
    )
    assert response["session"]["metadata"]["overrides"] == {
        "dummy_session_mode": "alpha",
    }
    assert server_mod.get_session_overrides(
        session.session_id,
        app_instance=app,
    ) == {"overrides": {"dummy_session_mode": "alpha"}}

    wrapper = getattr(app, "_app_plugins")["dummy_settings_app_plugin"]
    plugin = wrapper.plugin
    assert isinstance(plugin, DummySettingsAppPlugin)
    assert plugin.executed[-1]["action_id"] == "record_session_settings_changed"
    assert plugin.executed[-1]["context"]["source"] == "api"

    deleted = server_mod.delete_session_override(
        session.session_id,
        "dummy_session_mode",
        app_instance=app,
    )
    assert "overrides" not in deleted["session"]["metadata"]


def test_runtime_dummy_settings_plugin_path_is_config_loadable(tmp_path: Path) -> None:
    app = AgentApplication(
        str(_make_config_with_runtime_dummy_settings_plugin(tmp_path)),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )

    elements = app.get_application_ui_schema()
    assert any(
        element.get("key") == "dummy_server_mode"
        and element.get("scope") == "server"
        for element in elements
    )

    app.patch_server_settings({"dummy_server_mode": "careful"}, source="test")

    wrapper = getattr(app, "_app_plugins")["dummy_settings_app_plugin"]
    plugin = wrapper.plugin
    assert plugin.executed[-1]["action_id"] == "record_server_settings_changed"
    assert plugin.executed[-1]["context"]["new_settings"] == {
        "dummy_server_mode": "careful"
    }