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
from agent_app.app_plugins import ApplicationPluginWrapper
from agent_app.command_ui import CommandCatalogError
from agent_core import AgentCore

# Import dummy plugins so they are available for dotted-path loading.
from .dummy_provider import DummyProvider  # noqa: F401
from .dummy_app_plugin import DummyAppPlugin  # noqa: F401


def _make_config_with_app_plugin(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "providers": {"dummy": {"provider": "dummy_provider", "model": "test-model"}},
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.dummy_app_plugin.DummyAppPlugin",
        ],
        "agents": {
            "default": {"provider": "dummy"},
        },
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

    commands = app.get_application_commands()
    assert len(commands) == 1
    command = commands[0]
    assert command["plugin"] == "dummy_app_plugin"
    assert command["name"] == "dummy-command"
    assert command["action_id"] == "do_dummy"
    assert command["args"][0]["name"] == "value"

    cli_elements = app.get_application_command_ui_elements("cli_command")
    assert [
        (element["path"], element["legacy"], element["action_id"])
        for element in cli_elements
    ] == [(["dummy-command"], True, "do_dummy")]
    assert app.get_application_command_ui_elements("slash_command") == []

    with pytest.raises(CommandCatalogError, match="built-in.*dummy_app_plugin"):
        app.get_application_command_ui_elements(
            "cli_command",
            reserved_paths=[("dummy-command",)],
        )


def test_application_ui_schema_context_includes_authoritative_server_settings(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    config_path = _make_config_with_app_plugin(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
    app.patch_server_settings({"footer_visible": False}, source="test")

    wrapper = getattr(app, "_app_plugins")["dummy_app_plugin"]
    seen_contexts: List[Dict[str, Any]] = []

    def _ui_elements(
        state: Dict[str, Any],
        config: Dict[str, Any] | None = None,
        context: Dict[str, Any] | None = None,
    ) -> List[Dict[str, Any]]:
        _ = state, config
        seen_contexts.append(dict(context or {}))
        return [
            {
                "ui_type": "session_list_field",
                "id": "server-aware-field",
                "role": "meta",
                "data": "metadata.value",
            }
        ]

    monkeypatch.setattr(wrapper.plugin, "get_ui_elements", _ui_elements)

    elements = app.get_application_ui_schema(
        context={"server_settings": {"footer_visible": True}},
    )

    assert elements[0]["id"] == "server-aware-field"
    assert seen_contexts[-1]["ui_context"] == "application"
    assert seen_contexts[-1]["server_settings"] == {"footer_visible": False}


def test_get_session_application_ui_schema_delegates_session_context_and_filters_plugin(
    tmp_path: Path,
) -> None:
    config_path = _make_config_with_app_plugin(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)
    _core, _base_config, session = app.create_session("default")

    elements = app.get_session_application_ui_schema(
        session.session_id,
        plugin="dummy_app_plugin",
    )

    assert len(elements) == 1
    assert elements[0]["plugin"] == "dummy_app_plugin"
    assert elements[0]["id"] == "dummy_ui"
    assert (
        app.get_session_application_ui_schema(
            session.session_id,
            plugin="missing",
        )
        == []
    )


def test_application_plugin_ui_wrapper_passes_context_to_new_signature() -> None:
    class ContextAwareAppPlugin:
        name = "context_aware"
        version = "1.0.0"

        def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
            return {"initialized": True}

        def get_config_schema(self) -> Dict[str, Any]:
            return {}

        def get_ui_elements(
            self,
            state: Dict[str, Any],
            config: Dict[str, Any] | None = None,
            context: Dict[str, Any] | None = None,
        ) -> List[Dict[str, Any]]:
            return [
                {
                    "ui_type": "config",
                    "key": "server_mode",
                    "state_initialized": state.get("initialized"),
                    "config_model": (config or {}).get("model"),
                    "server_mode": (context or {})
                    .get("server_settings", {})
                    .get("server_mode"),
                    "tags": (context or {}).get("tags"),
                    "models": (context or {}).get("models"),
                }
            ]

        def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
            return []

        def execute_action(
            self,
            app: Any,
            action_id: str,
            params: Dict[str, Any],
            context: Dict[str, Any] | None,
            state: Dict[str, Any],
        ) -> Dict[str, Any]:
            return {}

    wrapper = ApplicationPluginWrapper("context_aware", ContextAwareAppPlugin)
    wrapper.init({})

    elements = wrapper.get_ui_elements(
        config={"model": "test-model"},
        context={
            "server_settings": {"server_mode": "careful"},
            "tags": ["demo"],
            "models": [{"id": "m"}],
        },
    )

    assert elements == [
        {
            "ui_type": "config",
            "key": "server_mode",
            "state_initialized": True,
            "config_model": "test-model",
            "server_mode": "careful",
            "tags": ["demo"],
            "models": [{"id": "m"}],
        }
    ]


def test_application_plugin_ui_wrapper_keeps_legacy_tags_models_signature() -> None:
    class LegacyAppPlugin:
        name = "legacy"
        version = "1.0.0"

        def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
            return {}

        def get_config_schema(self) -> Dict[str, Any]:
            return {}

        def get_ui_elements(
            self,
            state: Dict[str, Any],
            config: Dict[str, Any] | None = None,
            tags: List[str] | None = None,
            models: List[Dict[str, Any]] | None = None,
        ) -> List[Dict[str, Any]]:
            return [
                {
                    "ui_type": "config",
                    "key": "legacy",
                    "tags": tags or [],
                    "models": models or [],
                }
            ]

        def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
            return []

        def execute_action(
            self,
            app: Any,
            action_id: str,
            params: Dict[str, Any],
            context: Dict[str, Any] | None,
            state: Dict[str, Any],
        ) -> Dict[str, Any]:
            return {}

    wrapper = ApplicationPluginWrapper("legacy", LegacyAppPlugin)
    wrapper.init({})

    elements = wrapper.get_ui_elements(
        config={},
        context={"tags": ["legacy-tag"], "models": [{"id": "legacy-model"}]},
    )

    assert elements == [
        {
            "ui_type": "config",
            "key": "legacy",
            "tags": ["legacy-tag"],
            "models": [{"id": "legacy-model"}],
        }
    ]


def test_application_plugin_wrapper_close_passes_state() -> None:
    class ClosingAppPlugin:
        name = "closing"
        version = "1.0.0"

        def __init__(self) -> None:
            self.closed_state: Dict[str, Any] | None = None

        def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
            _ = app_config
            return {"resource": "open"}

        def get_config_schema(self) -> Dict[str, Any]:
            return {}

        def get_ui_elements(
            self,
            state: Dict[str, Any],
            config: Dict[str, Any] | None = None,
            context: Dict[str, Any] | None = None,
        ) -> List[Dict[str, Any]]:
            _ = state, config, context
            return []

        def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
            _ = state
            return []

        def execute_action(
            self,
            app: Any,
            action_id: str,
            params: Dict[str, Any],
            context: Dict[str, Any] | None,
            state: Dict[str, Any],
        ) -> Dict[str, Any]:
            _ = app, action_id, params, context, state
            return {}

        def close(self, state: Dict[str, Any]) -> None:
            self.closed_state = dict(state)

    wrapper = ApplicationPluginWrapper("closing", ClosingAppPlugin)
    wrapper.init({})
    wrapper.close()

    plugin = wrapper.plugin
    assert isinstance(plugin, ClosingAppPlugin)
    assert plugin.closed_state == {"resource": "open"}


def test_agent_application_close_closes_application_plugins(tmp_path: Path) -> None:
    config_path = _make_config_with_app_plugin(tmp_path)
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    wrappers = getattr(app, "_app_plugins")
    wrapper = wrappers["dummy_app_plugin"]
    closed: List[str] = []

    def close_wrapper() -> None:
        closed.append(wrapper.plugin_id)

    wrapper.close = close_wrapper  # type: ignore[method-assign]

    app.close()

    assert closed == ["dummy_app_plugin"]


def test_agent_application_close_is_idempotent(tmp_path: Path) -> None:
    config_path = _make_config_with_app_plugin(tmp_path)
    session_root = tmp_path / "sessions"
    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    wrappers = getattr(app, "_app_plugins")
    wrapper = wrappers["dummy_app_plugin"]
    closed: List[str] = []

    def close_wrapper() -> None:
        closed.append(wrapper.plugin_id)

    wrapper.close = close_wrapper  # type: ignore[method-assign]

    app.close()
    app.close()

    assert closed == ["dummy_app_plugin"]


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


def test_execute_application_action_rejects_unknown_plugin_or_action(
    tmp_path: Path,
) -> None:
    config_path = _make_config_with_app_plugin(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    with pytest.raises(KeyError):
        _ = app.execute_application_action("no_such_plugin", "do_dummy", {"value": "x"})

    with pytest.raises(KeyError):
        _ = app.execute_application_action("dummy_app_plugin", "no_such_action", {})


def test_execute_application_action_validation_errors(tmp_path: Path) -> None:
    config_path = _make_config_with_app_plugin(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    # Missing required parameter.
    with pytest.raises(AgentApplication._ApplicationActionValidationError):  # type: ignore[attr-defined]
        _ = app.execute_application_action("dummy_app_plugin", "do_dummy", {})

    # Wrong type for value.
    with pytest.raises(AgentApplication._ApplicationActionValidationError):  # type: ignore[attr-defined]
        _ = app.execute_application_action(
            "dummy_app_plugin", "do_dummy", {"value": 123}
        )
