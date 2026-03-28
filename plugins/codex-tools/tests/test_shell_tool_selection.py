"""Integration tests for shell tool selection.

Tests the shell tool selection system including:
- is_enabled method with shell_tool_mode config
- Selection based on codex-variant tag
- force_enabled_plugins override
- default_enabled attribute on legacy tool
"""

from __future__ import annotations

from typing import Any, Dict, List

import pytest

from agent_core import AgentCore
from codex_tools.shell_tool import ShellArrayTool
from codex_tools.shell_command_tool import ShellCommandTool
from codex_tools.shell_tool_legacy import ShellTool


class MockProvider:
    """Minimal provider for testing shell tool selection."""

    name = "mock_provider"
    version = "1.0.0"

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        tags = []
        # Allow config to add codex-variant tag
        if config.get("is_codex_model"):
            tags.append("codex-variant")
        return tags


class TestShellToolSelection:
    """Tests for shell tool selection based on config and tags."""

    def test_shell_array_tool_name(self):
        """Verify shell array tool has correct name."""
        assert ShellArrayTool.name == "shell"

    def test_shell_command_tool_name(self):
        """Verify shell command tool has correct name."""
        assert ShellCommandTool.name == "shell_command"

    def test_legacy_tool_name_and_default_disabled(self):
        """Verify legacy tool is renamed and disabled by default."""
        assert ShellTool.name == "shell_legacy"
        assert ShellTool.default_enabled is False

    def test_auto_mode_without_codex_variant_enables_shell(self):
        """In auto mode without codex-variant tag, shell (array) should be enabled."""
        core = AgentCore()
        core.register_provider(MockProvider)
        core.register_tool(ShellArrayTool)
        core.register_tool(ShellCommandTool)

        config = {"shell_tool_mode": "auto"}

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" in tool_names, "shell should be enabled in auto mode without codex-variant"
        assert "shell_command" not in tool_names, "shell_command should be disabled in auto mode without codex-variant"

    def test_auto_mode_with_codex_variant_enables_shell_command(self):
        """In auto mode with codex-variant tag, shell_command should be enabled."""
        core = AgentCore()
        core.register_provider(MockProvider)
        core.register_tool(ShellArrayTool)
        core.register_tool(ShellCommandTool)

        config = {"shell_tool_mode": "auto", "is_codex_model": True}

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" not in tool_names, "shell should be disabled in auto mode with codex-variant"
        assert "shell_command" in tool_names, "shell_command should be enabled in auto mode with codex-variant"

    def test_auto_mode_with_config_is_codex_model(self):
        """Config can trigger codex-variant tag via provider."""
        core = AgentCore()
        core.register_provider(MockProvider)
        core.register_tool(ShellArrayTool)
        core.register_tool(ShellCommandTool)

        # Provider will add codex-variant tag when config has is_codex_model=True
        config = {"shell_tool_mode": "auto", "is_codex_model": True}

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" not in tool_names
        assert "shell_command" in tool_names

    def test_shell_mode_always_enables_shell(self):
        """shell_tool_mode='shell' should always enable shell (array)."""
        core = AgentCore()
        core.register_provider(MockProvider)
        core.register_tool(ShellArrayTool)
        core.register_tool(ShellCommandTool)

        # Even with is_codex_model=True, shell mode forces shell on
        config = {"shell_tool_mode": "shell", "is_codex_model": True}

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" in tool_names, "shell should be forced on in shell mode"
        assert "shell_command" not in tool_names, "shell_command should be off in shell mode"

    def test_shell_command_mode_always_enables_shell_command(self):
        """shell_tool_mode='shell_command' should always enable shell_command."""
        core = AgentCore()
        core.register_provider(MockProvider)
        core.register_tool(ShellArrayTool)
        core.register_tool(ShellCommandTool)

        # Without is_codex_model, shell_command mode still forces shell_command on
        config = {"shell_tool_mode": "shell_command"}

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" not in tool_names, "shell should be off in shell_command mode"
        assert "shell_command" in tool_names, "shell_command should be forced on in shell_command mode"

    def test_force_enabled_plugins_enables_both(self):
        """force_enabled_plugins should enable both tools regardless of mode."""
        core = AgentCore()
        core.register_provider(MockProvider)
        core.register_tool(ShellArrayTool)
        core.register_tool(ShellCommandTool)

        config = {
            "shell_tool_mode": "shell",  # Would normally disable shell_command
            "force_enabled_plugins": ["shell_command"],
        }

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" in tool_names
        assert "shell_command" in tool_names, "force_enabled_plugins should enable shell_command"

    def test_force_enabled_plugins_overrides_codex_variant(self):
        """force_enabled_plugins should override tag-based selection."""
        core = AgentCore()
        core.register_provider(MockProvider)
        core.register_tool(ShellArrayTool)
        core.register_tool(ShellCommandTool)

        config = {
            "shell_tool_mode": "auto",  # codex-variant would normally disable shell
            "is_codex_model": True,
            "force_enabled_plugins": ["shell"],
        }

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" in tool_names, "force_enabled_plugins should enable shell despite codex-variant"
        assert "shell_command" in tool_names

    def test_legacy_tool_disabled_by_default(self):
        """Legacy shell tool should be disabled by default (not in tool list)."""
        core = AgentCore()
        core.register_provider(MockProvider)
        core.register_tool(ShellTool)  # Legacy tool

        config = {}

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell_legacy" not in tool_names, "legacy tool should be disabled by default"


class TestShellToolTags:
    """Tests for shell tool tag contributions."""

    def test_shell_array_tool_contributes_tag(self):
        """Shell array tool should contribute shell:array tag."""
        tool = ShellArrayTool()
        tags = tool.get_tags({}, [])
        assert "shell:array" in tags

    def test_shell_command_tool_contributes_tag(self):
        """Shell command tool should contribute shell:command tag."""
        tool = ShellCommandTool()
        tags = tool.get_tags({}, [])
        assert "shell:command" in tags


class TestShellToolIsEnabled:
    """Tests for shell tool is_enabled method directly."""

    def test_shell_array_is_enabled_auto_without_codex(self):
        """Shell array is_enabled returns True in auto mode without codex-variant."""
        tool = ShellArrayTool()
        result = tool.is_enabled({"shell_tool_mode": "auto"}, [], [], {})
        assert result is True

    def test_shell_array_is_enabled_auto_with_codex(self):
        """Shell array is_enabled returns False in auto mode with codex-variant."""
        tool = ShellArrayTool()
        result = tool.is_enabled({"shell_tool_mode": "auto"}, ["codex-variant"], [], {})
        assert result is False

    def test_shell_array_is_enabled_shell_mode(self):
        """Shell array is_enabled returns True in shell mode."""
        tool = ShellArrayTool()
        result = tool.is_enabled({"shell_tool_mode": "shell"}, ["codex-variant"], [], {})
        assert result is True

    def test_shell_array_is_enabled_shell_command_mode(self):
        """Shell array is_enabled returns False in shell_command mode."""
        tool = ShellArrayTool()
        result = tool.is_enabled({"shell_tool_mode": "shell_command"}, [], [], {})
        assert result is False

    def test_shell_command_is_enabled_auto_without_codex(self):
        """Shell command is_enabled returns False in auto mode without codex-variant."""
        tool = ShellCommandTool()
        result = tool.is_enabled({"shell_tool_mode": "auto"}, [], [], {})
        assert result is False

    def test_shell_command_is_enabled_auto_with_codex(self):
        """Shell command is_enabled returns True in auto mode with codex-variant."""
        tool = ShellCommandTool()
        result = tool.is_enabled({"shell_tool_mode": "auto"}, ["codex-variant"], [], {})
        assert result is True

    def test_shell_command_is_enabled_shell_mode(self):
        """Shell command is_enabled returns False in shell mode."""
        tool = ShellCommandTool()
        result = tool.is_enabled({"shell_tool_mode": "shell"}, ["codex-variant"], [], {})
        assert result is False

    def test_shell_command_is_enabled_shell_command_mode(self):
        """Shell command is_enabled returns True in shell_command mode."""
        tool = ShellCommandTool()
        result = tool.is_enabled({"shell_tool_mode": "shell_command"}, [], [], {})
        assert result is True


class TestAllShellToolsTogether:
    """Tests for all shell tools registered together."""

    def test_all_tools_registered_auto_without_codex(self):
        """With all tools registered, auto mode without codex should enable shell only."""
        core = AgentCore()
        core.register_provider(MockProvider)
        core.register_tool(ShellArrayTool)
        core.register_tool(ShellCommandTool)
        core.register_tool(ShellTool)

        config = {"shell_tool_mode": "auto"}

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" in tool_names
        assert "shell_command" not in tool_names
        assert "shell_legacy" not in tool_names

    def test_all_tools_registered_auto_with_codex(self):
        """With all tools registered, auto mode with codex should enable shell_command only."""
        core = AgentCore()
        core.register_provider(MockProvider)
        core.register_tool(ShellArrayTool)
        core.register_tool(ShellCommandTool)
        core.register_tool(ShellTool)

        config = {"shell_tool_mode": "auto", "is_codex_model": True}

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" not in tool_names
        assert "shell_command" in tool_names
        assert "shell_legacy" not in tool_names

    def test_legacy_tool_can_be_enabled_via_force_enabled(self):
        """Legacy tool can be enabled via force_enabled_plugins."""
        core = AgentCore()
        core.register_provider(MockProvider)
        core.register_tool(ShellArrayTool)
        core.register_tool(ShellCommandTool)
        core.register_tool(ShellTool)

        config = {
            "shell_tool_mode": "auto",
            "is_codex_model": True,
            "force_enabled_plugins": ["shell_legacy"],
        }

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell_legacy" in tool_names, "force_enabled_plugins should enable legacy tool"