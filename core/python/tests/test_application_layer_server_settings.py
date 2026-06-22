from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from agent_app.application_future import AgentApplication
from agent_core import AgentCore

from .dummy_provider import DummyProvider  # noqa: F401
from .dummy_settings_app_plugin import DummySettingsAppPlugin


def _make_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "dummy": {"provider": "dummy_provider", "model": "test-model"},
        },
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.dummy_settings_app_plugin.DummySettingsAppPlugin",
        ],
        "agents": {
            "default": {"provider": "dummy"},
        },
        "application": {},
    }
    path = tmp_path / "config_server_settings.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    return AgentApplication(
        str(_make_config(tmp_path)),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
    )


def _settings_plugin(app: AgentApplication) -> DummySettingsAppPlugin:
    wrapper = getattr(app, "_app_plugins")["dummy_settings_app_plugin"]
    plugin = wrapper.plugin
    assert isinstance(plugin, DummySettingsAppPlugin)
    return plugin


def test_server_settings_persist_and_fire_lifecycle(tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    plugin = _settings_plugin(app)

    assert app.get_server_settings() == {}

    settings = app.patch_server_settings(
        {"dummy_server_mode": "careful", "dummy_server_enabled": True},
        source="test",
    )

    assert settings == {
        "dummy_server_mode": "careful",
        "dummy_server_enabled": True,
    }
    assert app.get_server_settings() == settings
    assert plugin.executed
    record = plugin.executed[-1]
    assert record["action_id"] == "record_server_settings_changed"
    context = record["context"]
    assert context["lifecycle"] == "server_settings_changed"
    assert context["scope"] == "server"
    assert context["old_settings"] == {}
    assert context["new_settings"] == settings
    assert context["changed_keys"] == [
        "dummy_server_enabled",
        "dummy_server_mode",
    ]
    assert context["source"] == "test"

    reloaded = _build_app(tmp_path)
    assert reloaded.get_server_settings() == settings


def test_server_settings_delete_and_noop_do_not_fire_lifecycle(tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    plugin = _settings_plugin(app)

    app.patch_server_settings({"dummy_server_mode": "fast"}, source="test")
    first_count = len(plugin.executed)

    unchanged = app.patch_server_settings({"dummy_server_mode": "fast"}, source="test")
    assert unchanged == {"dummy_server_mode": "fast"}
    assert len(plugin.executed) == first_count

    settings = app.delete_server_setting("dummy_server_mode", source="test")
    assert settings == {}
    assert len(plugin.executed) == first_count + 1
    context = plugin.executed[-1]["context"]
    assert context["old_settings"] == {"dummy_server_mode": "fast"}
    assert context["new_settings"] == {}
    assert context["changed_keys"] == ["dummy_server_mode"]

    app.delete_server_setting("dummy_server_mode", source="test")
    assert len(plugin.executed) == first_count + 1


def test_session_settings_helpers_fire_lifecycle(tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    plugin = _settings_plugin(app)
    _core, _base_config, session = app.create_session("default")

    updated = app.patch_session_settings(
        session.session_id,
        {"dummy_session_mode": "alpha"},
        source="test",
    )

    assert app.get_session_settings(session.session_id) == {
        "dummy_session_mode": "alpha",
    }
    assert updated.metadata["overrides"] == {"dummy_session_mode": "alpha"}
    record = plugin.executed[-1]
    assert record["action_id"] == "record_session_settings_changed"
    context = record["context"]
    assert context["lifecycle"] == "session_settings_changed"
    assert context["scope"] == "session"
    assert context["session_id"] == session.session_id
    assert context["old_settings"] == {}
    assert context["new_settings"] == {"dummy_session_mode": "alpha"}
    assert context["changed_keys"] == ["dummy_session_mode"]
    assert context["source"] == "test"

    deleted = app.delete_session_setting(
        session.session_id,
        "dummy_session_mode",
        source="test",
    )
    assert "overrides" not in deleted.metadata
    assert app.get_session_settings(session.session_id) == {}
    assert plugin.executed[-1]["context"]["changed_keys"] == ["dummy_session_mode"]