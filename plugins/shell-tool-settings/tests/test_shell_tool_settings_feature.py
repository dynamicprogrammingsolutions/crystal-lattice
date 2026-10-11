"""Tests for the shell_tool_mode session-settings feature plugin.

Covers the UI element contract (shape, options, default), schema exposure
through a real AgentCore (present with the plugin, absent without it), and
the session-override flow through the real request-config merge path:
setting ``shell_tool_mode`` for a session swaps the active shell tools from
the next request on, and removing the override restores the agent default.
"""

from __future__ import annotations

from typing import Any, Dict, List

from agent_core import AgentCore
from agent_app.config import resolve_request_config
from codex_tools.shell_command_tool import ShellCommandTool
from codex_tools.shell_tool import ShellArrayTool
from codex_tools.unified_exec_tool import ExecCommandTool, WriteStdinTool
from shell_tool_settings import (
    SHELL_TOOL_MODE_DEFAULT,
    SHELL_TOOL_MODE_OPTIONS,
    ShellToolSettingsFeature,
)


class MockProvider:
    """Minimal provider for plugin resolution tests."""

    name = "mock_provider"
    version = "1.0.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        return []


def _core_with_shell_tools(*, with_settings_feature: bool) -> AgentCore:
    core = AgentCore()
    core.register_provider(MockProvider)
    core.register_tool(ShellArrayTool)
    core.register_tool(ShellCommandTool)
    core.register_tool(ExecCommandTool)
    core.register_tool(WriteStdinTool)
    if with_settings_feature:
        core.register_feature(ShellToolSettingsFeature)
    return core


def _tool_names(core: AgentCore, config: Dict[str, Any]) -> List[str]:
    _, _, _, tools, _ = core._resolve_plugins_for_config(config)
    return [t.name for t in tools]


class TestUiElement:
    def test_element_shape(self):
        feature = ShellToolSettingsFeature()
        elements = feature.get_ui_elements({}, [], [])
        assert len(elements) == 1
        element = elements[0]
        assert element["type"] == "select"
        assert element["key"] == "shell_tool_mode"
        assert element["default"] == SHELL_TOOL_MODE_DEFAULT == "auto"
        assert element["label"]
        assert element["description"]

    def test_option_shape_matches_setting_consumers(self):
        # Both the terminal /set option matcher and the mobile settings
        # chips normalize options to {value, label} string pairs.
        for option in SHELL_TOOL_MODE_OPTIONS:
            assert isinstance(option["value"], str) and option["value"]
            assert isinstance(option["label"], str) and option["label"]

    def test_options_cover_all_modes(self):
        values = {option["value"] for option in SHELL_TOOL_MODE_OPTIONS}
        assert values == {"auto", "exec_command", "shell_command", "shell"}

    def test_feature_has_no_behavior(self):
        feature = ShellToolSettingsFeature()
        assert feature.get_tags({}, []) == []
        assert feature.get_config_schema() == {}
        assert feature.init({"model": "x"}, {"k": 1}) == {"k": 1}
        messages = [{"role": "user", "content": "hi"}]
        out, state = feature.initialize_request(messages, {})
        assert out == messages and out is not messages
        assert state == {}


class TestSchemaExposure:
    def test_schema_contains_element_with_feature(self):
        core = _core_with_shell_tools(with_settings_feature=True)
        schema = core.get_ui_schema(config={})
        matching = [
            el for el in schema if el.get("key") == "shell_tool_mode"
        ]
        assert len(matching) == 1
        element = matching[0]
        assert element["plugin"] == "shell_tool_settings"
        assert element["default"] == "auto"
        assert {opt["value"] for opt in element["options"]} == {
            "auto",
            "exec_command",
            "shell_command",
            "shell",
        }

    def test_schema_lacks_element_without_feature(self):
        core = _core_with_shell_tools(with_settings_feature=False)
        schema = core.get_ui_schema(config={})
        assert not [el for el in schema if el.get("key") == "shell_tool_mode"]


class TestSessionOverrideFlow:
    """Session overrides swap the shell tools from the next request on."""

    BASE_CONFIG: Dict[str, Any] = {"model": "gpt-6.1-sol"}

    def _resolve(self, overrides: Dict[str, Any]) -> List[str]:
        core = _core_with_shell_tools(with_settings_feature=True)
        effective = resolve_request_config(self.BASE_CONFIG, overrides)
        if "shell_tool_mode" in overrides:
            assert effective["shell_tool_mode"] == overrides["shell_tool_mode"]
        return _tool_names(core, effective)

    def test_default_is_unified_exec_for_every_model(self):
        for model in ("gpt-6.1-sol", "openai/gpt-5", "google/gemini-2.5-flash"):
            core = _core_with_shell_tools(with_settings_feature=True)
            names = _tool_names(core, {"model": model})
            assert "exec_command" in names
            assert "write_stdin" in names
            assert "shell" not in names
            assert "shell_command" not in names

    def test_session_override_selects_shell_command(self):
        names = self._resolve({"shell_tool_mode": "shell_command"})
        assert "shell_command" in names
        assert "exec_command" not in names
        assert "write_stdin" not in names
        assert "shell" not in names

    def test_session_override_selects_shell_array(self):
        names = self._resolve({"shell_tool_mode": "shell"})
        assert "shell" in names
        assert "shell_command" not in names
        assert "exec_command" not in names
        assert "write_stdin" not in names

    def test_session_override_auto_matches_default(self):
        names = self._resolve({"shell_tool_mode": "auto"})
        assert "exec_command" in names
        assert "write_stdin" in names
        assert "shell" not in names
        assert "shell_command" not in names

    def test_removing_override_restores_agent_default(self):
        # With the override present, the legacy tool is active...
        with_override = self._resolve({"shell_tool_mode": "shell_command"})
        assert "shell_command" in with_override
        # ...and with it removed (session reset), the default returns.
        without_override = self._resolve({})
        assert "shell_command" not in without_override
        assert "exec_command" in without_override

    def test_agent_level_setting_acts_as_default(self):
        core = _core_with_shell_tools(with_settings_feature=True)
        base = {"model": "gpt-6.1-sol", "shell_tool_mode": "shell_command"}
        names = _tool_names(core, resolve_request_config(base, {}))
        assert "shell_command" in names
        assert "exec_command" not in names
        # A session override still wins over the agent default.
        overridden = _tool_names(
            core, resolve_request_config(base, {"shell_tool_mode": "auto"})
        )
        assert "shell_command" not in overridden
        assert "exec_command" in overridden


class TestUpdateOverrideContract:
    """The write path used by /set stores plain JSON-serializable values."""

    def test_option_values_are_plain_strings(self):
        for option in SHELL_TOOL_MODE_OPTIONS:
            assert isinstance(option["value"], str)
            assert option["value"] in {
                "auto",
                "exec_command",
                "shell_command",
                "shell",
            }
