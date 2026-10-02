from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

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


def _build_app(
    tmp_path: Path,
    *,
    replay_server_settings_on_startup: bool = True,
) -> AgentApplication:
    return AgentApplication(
        str(_make_config(tmp_path)),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
        replay_server_settings_on_startup=replay_server_settings_on_startup,
    )


def _build_workspace_app(tmp_path: Path, workspace_root: Path) -> AgentApplication:
    config_path = _make_config(tmp_path)
    config = json.loads(config_path.read_text(encoding="utf-8"))
    config["agents"]["default"].update(
        {
            "workspace_root": str(workspace_root),
            "working_directory": str(workspace_root),
            "allowed_paths": [str(workspace_root)],
        }
    )
    config_path.write_text(json.dumps(config), encoding="utf-8")
    return AgentApplication(
        str(config_path),
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
    reloaded_plugin = _settings_plugin(reloaded)
    assert reloaded_plugin.executed
    assert reloaded_plugin.executed[-1]["context"]["source"] == "startup"
    assert reloaded_plugin.executed[-1]["context"]["new_settings"] == settings


def test_server_settings_startup_replay_can_be_suppressed(tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    app.patch_server_settings({"dummy_server_mode": "careful"}, source="test")

    companion = _build_app(tmp_path, replay_server_settings_on_startup=False)
    plugin = _settings_plugin(companion)

    assert companion.get_server_settings() == {"dummy_server_mode": "careful"}
    assert plugin.executed == []

    companion.patch_server_settings({"dummy_server_mode": "fast"}, source="test")
    assert len(plugin.executed) == 1
    assert plugin.executed[0]["context"]["source"] == "test"
    assert plugin.executed[0]["context"]["new_settings"] == {
        "dummy_server_mode": "fast"
    }


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


def test_session_working_directory_is_canonicalized_and_workspace_is_locked(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    nested = workspace_root / "projects" / "alpha"
    sibling = tmp_path / "sibling"
    nested.mkdir(parents=True)
    sibling.mkdir()
    app = _build_workspace_app(tmp_path, workspace_root)
    _core, _base_config, session = app.create_session("default")

    app.patch_session_settings(
        session.session_id,
        {"working_directory": "projects/alpha"},
        source="test",
    )
    assert app.get_session_settings(session.session_id)["working_directory"] == str(
        nested.resolve()
    )

    for updates in (
        {"working_directory": str(sibling)},
        {"working_directory": "../sibling"},
        {"working_directory": "missing"},
        {"workspace_root": str(sibling)},
        {"allowed_paths": [str(sibling)]},
    ):
        with pytest.raises(ValueError):
            app.patch_session_settings(
                session.session_id,
                updates,
                source="test",
            )


def test_session_workspace_id_resolves_internal_private_and_external_roots(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    shared = workspace_root / "shared-project"
    external = tmp_path / "external"
    shared.mkdir(parents=True)
    external.mkdir()
    app = _build_workspace_app(tmp_path, workspace_root)
    _core, base_config, session = app.create_session("default")
    base_config["workspace_grants"] = json.dumps(
        {
            "grant-1": {
                "path": str(external),
                "display_name": "External",
                "available": True,
            }
        }
    )
    app._agent_base_configs["default"] = base_config

    app.patch_session_settings(
        session.session_id,
        {"workspace_id": "shared:shared-project"},
        source="test",
    )
    assert app.get_session_settings(session.session_id) == {
        "workspace_id": "shared:shared-project",
        "working_directory": str(shared.resolve()),
    }

    private = workspace_root / ".sessions" / session.session_id / "private-one"
    private.mkdir(parents=True)
    app.patch_session_settings(
        session.session_id,
        {"workspace_id": f"private:{session.session_id}:private-one"},
        source="test",
    )
    assert app.get_session_settings(session.session_id)["working_directory"] == str(
        private.resolve()
    )

    app.patch_session_settings(
        session.session_id,
        {"workspace_id": "external:grant-1"},
        source="test",
    )
    assert app.get_session_settings(session.session_id)["working_directory"] == str(
        external.resolve()
    )

    for workspace_id in (
        "shared:../outside",
        "shared:.sessions/other",
        "private:other-session:private-one",
        "external:missing",
    ):
        with pytest.raises(ValueError):
            app.patch_session_settings(
                session.session_id,
                {"workspace_id": workspace_id},
                source="test",
            )
