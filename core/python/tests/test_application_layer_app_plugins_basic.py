"""Basic tests for application-level plugins in the future application layer.

These tests exercise loading, introspection, and action execution for
ApplicationPlugin implementations wired into
``agent_app.application_future.AgentApplication``.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pytest

from agent_app.application_future import AgentApplication
from agent_core import AgentCore

# Import dummy plugins so they are available for dotted-path loading.
from .dummy_provider import DummyProvider  # noqa: F401
from .dummy_app_plugin import DummyAppPlugin  # noqa: F401


def _make_config_with_app_plugin(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {
            "dummy": {"provider": "dummy_provider", "model": "test-model"}
        },
        "plugins": {
            "providers": ["tests.dummy_provider.DummyProvider"],
        },
        "agents": {
            "default": {"provider": "dummy"},
        },
        "application_plugins": [
            "tests.dummy_app_plugin.DummyAppPlugin",
        ],
        "application": {
            "ui_theme": "light",
            "dummy_flag": True,
        },
    }
    path = tmp_path / "config_app_plugins.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


def test_list_application_plugins_exposes_basic_metadata(tmp_path: Path) -> None:
    config_path = _make_config_with_app_plugin(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    plugins = app.list_application_plugins()
    assert len(plugins) == 1

    entry = plugins[0]
    assert entry["id"] == "dummy_app_plugin"
    assert entry["class_name"] == "DummyAppPlugin"
    assert entry["class_path"].endswith("tests.dummy_app_plugin.DummyAppPlugin")
    # name attribute should be surfaced when present
    assert entry.get("name") == "dummy_app_plugin"


def test_get_application_actions_and_ui_schema_attach_plugin_id(tmp_path: Path) -> None:
    config_path = _make_config_with_app_plugin(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    actions = app.get_application_actions()
    assert len(actions) == 1
    action = actions[0]
    assert action["plugin"] == "dummy_app_plugin"
    assert action["id"] == "do_dummy"
    inputs = action.get("inputs") or {}
    assert "value" in inputs
    assert inputs["value"]["type"] == "string"

    ui_elements = app.get_application_ui_schema()
    assert len(ui_elements) == 1
    element = ui_elements[0]
    assert element["plugin"] == "dummy_app_plugin"
    assert element["ui_type"] == "session_action"
    assert element["action_id"] == "do_dummy"


def test_execute_application_action_invokes_plugin(tmp_path: Path) -> None:
    config_path = _make_config_with_app_plugin(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    result = app.execute_application_action(
        plugin_id="dummy_app_plugin",
        action_id="do_dummy",
        params={"value": "hello"},
    )

    assert result["echo"] == {"value": "hello"}

    # Reach into the wrapper to confirm the plugin saw the call.
    wrappers = getattr(app, "_app_plugins")
    wrapper = wrappers["dummy_app_plugin"]
    plugin = wrapper.plugin
    assert isinstance(plugin, DummyAppPlugin)
    assert plugin.executed
    last = plugin.executed[-1]
    assert last["action_id"] == "do_dummy"
    assert last["params"] == {"value": "hello"}


def test_execute_application_action_rejects_unknown_plugin_or_action(tmp_path: Path) -> None:
    config_path = _make_config_with_app_plugin(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    with pytest.raises(KeyError):
        _ = app.execute_application_action("no_such_plugin", "do_dummy", {"value": "x"})

    with pytest.raises(KeyError):
        _ = app.execute_application_action("dummy_app_plugin", "no_such_action", {})
