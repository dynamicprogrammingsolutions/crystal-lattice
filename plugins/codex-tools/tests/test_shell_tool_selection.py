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
from codex_tools.codex_variant_feature import CodexVariantFeature
from codex_tools.shell_tool import ShellArrayTool
from codex_tools.shell_command_tool import ShellCommandTool
from codex_tools.shell_tool_legacy import ShellTool
from codex_tools.unified_exec_tool import ExecCommandTool, WriteStdinTool


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


def _register_all_shell_tools(core: AgentCore) -> None:
    core.register_tool(ShellArrayTool)
    core.register_tool(ShellCommandTool)
    core.register_tool(ExecCommandTool)
    core.register_tool(WriteStdinTool)


class TestShellToolSelection:
    """Tests for shell tool selection based on config and tags."""

    def test_shell_array_tool_name(self):
        """Verify shell array tool has correct name."""
        assert ShellArrayTool.name == "shell"

    def test_shell_command_tool_name(self):
        """Verify shell command tool has correct name."""
        assert ShellCommandTool.name == "shell_command"

    def test_unified_exec_tool_names(self):
        """Verify unified exec tool names."""
        assert ExecCommandTool.name == "exec_command"
        assert WriteStdinTool.name == "write_stdin"

    def test_legacy_tool_name_and_default_disabled(self):
        """Verify legacy tool is renamed and disabled by default."""
        assert ShellTool.name == "shell_legacy"
        assert ShellTool.default_enabled is False

    def test_auto_mode_without_codex_variant_enables_shell(self):
        """In auto mode without codex-variant tag, shell (array) should be enabled."""
        core = AgentCore()
        core.register_provider(MockProvider)
        _register_all_shell_tools(core)

        config = {"shell_tool_mode": "auto"}

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" in tool_names, "shell should be enabled in auto mode without codex-variant"
        assert "shell_command" not in tool_names, "shell_command should be disabled in auto mode without codex-variant"
        assert "exec_command" not in tool_names, "exec_command should be disabled without codex-variant"
        assert "write_stdin" not in tool_names, "write_stdin should be disabled without codex-variant"

    def test_auto_mode_with_codex_variant_enables_unified_exec(self):
        """In auto mode with codex-variant tag, unified exec should be enabled."""
        core = AgentCore()
        core.register_provider(MockProvider)
        _register_all_shell_tools(core)

        config = {"shell_tool_mode": "auto", "is_codex_model": True}

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" not in tool_names, "shell should be disabled in auto mode with codex-variant"
        assert "shell_command" not in tool_names, "shell_command should be disabled in auto mode with codex-variant"
        assert "exec_command" in tool_names, "exec_command should be enabled in auto mode with codex-variant"
        assert "write_stdin" in tool_names, "write_stdin should be enabled in auto mode with codex-variant"

    @pytest.mark.parametrize(
        "model",
        [
            "openai/gpt-5.4",
            "gpt-5.6-sol",
            "gpt-5.6-terra",
            "gpt-5.6-luna",
            "gpt-6-sol",
            "gpt-6-luna",
            "gpt-6-astra",
        ],
    )
    def test_shell_command_family_auto_mode_enables_unified_exec(self, model: str):
        """Named modern GPT variants should select the unified exec tools."""
        core = AgentCore()
        core.register_provider(MockProvider)
        core.register_feature(CodexVariantFeature)
        _register_all_shell_tools(core)

        config = {"shell_tool_mode": "auto", "model": model}

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "codex-variant" in tags
        assert "exec_command" in tool_names
        assert "write_stdin" in tool_names
        assert "shell" not in tool_names
        assert "shell_command" not in tool_names

    def test_auto_mode_with_config_is_codex_model(self):
        """Config can trigger codex-variant tag via provider."""
        core = AgentCore()
        core.register_provider(MockProvider)
        _register_all_shell_tools(core)

        # Provider will add codex-variant tag when config has is_codex_model=True
        config = {"shell_tool_mode": "auto", "is_codex_model": True}

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" not in tool_names
        assert "shell_command" not in tool_names
        assert "exec_command" in tool_names
        assert "write_stdin" in tool_names

    def test_shell_mode_always_enables_shell(self):
        """shell_tool_mode='shell' should always enable shell (array)."""
        core = AgentCore()
        core.register_provider(MockProvider)
        _register_all_shell_tools(core)

        # Even with is_codex_model=True, shell mode forces shell on
        config = {"shell_tool_mode": "shell", "is_codex_model": True}

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" in tool_names, "shell should be forced on in shell mode"
        assert "shell_command" not in tool_names, "shell_command should be off in shell mode"
        assert "exec_command" not in tool_names, "exec_command should be off in shell mode"
        assert "write_stdin" not in tool_names, "write_stdin should be off in shell mode"

    def test_shell_command_mode_always_enables_shell_command(self):
        """shell_tool_mode='shell_command' should always enable shell_command."""
        core = AgentCore()
        core.register_provider(MockProvider)
        _register_all_shell_tools(core)

        # Without is_codex_model, shell_command mode still forces shell_command on
        config = {"shell_tool_mode": "shell_command"}

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" not in tool_names, "shell should be off in shell_command mode"
        assert "shell_command" in tool_names, "shell_command should be forced on in shell_command mode"
        assert "exec_command" not in tool_names, "exec_command should be off in shell_command mode"
        assert "write_stdin" not in tool_names, "write_stdin should be off in shell_command mode"

    def test_exec_command_mode_always_enables_unified_exec(self):
        """shell_tool_mode='exec_command' should enable the unified exec tools."""
        core = AgentCore()
        core.register_provider(MockProvider)
        _register_all_shell_tools(core)

        # Works even without the codex-variant tag
        config = {"shell_tool_mode": "exec_command"}

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" not in tool_names, "shell should be off in exec_command mode"
        assert "shell_command" not in tool_names, "shell_command should be off in exec_command mode"
        assert "exec_command" in tool_names, "exec_command should be forced on"
        assert "write_stdin" in tool_names, "write_stdin should be forced on"

    def test_force_enabled_plugins_enables_multiple(self):
        """force_enabled_plugins should enable tools regardless of mode."""
        core = AgentCore()
        core.register_provider(MockProvider)
        _register_all_shell_tools(core)

        config = {
            "shell_tool_mode": "shell",  # Would normally disable others
            "force_enabled_plugins": ["shell_command", "exec_command"],
        }

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" in tool_names
        assert "shell_command" in tool_names, "force_enabled_plugins should enable shell_command"
        assert "exec_command" in tool_names, "force_enabled_plugins should enable exec_command"

    def test_force_enabled_plugins_overrides_codex_variant(self):
        """force_enabled_plugins should override tag-based selection."""
        core = AgentCore()
        core.register_provider(MockProvider)
        _register_all_shell_tools(core)

        config = {
            "shell_tool_mode": "auto",  # codex-variant would normally disable shell
            "is_codex_model": True,
            "force_enabled_plugins": ["shell"],
        }

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" in tool_names, "force_enabled_plugins should enable shell despite codex-variant"
        assert "exec_command" in tool_names

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

    def test_unified_exec_tools_contribute_tag(self):
        """Unified exec tools should contribute shell:exec tag."""
        assert "shell:exec" in ExecCommandTool().get_tags({}, [])
        assert "shell:exec" in WriteStdinTool().get_tags({}, [])


class TestCodexVariantFeaturePatterns:
    """Tests for Codex shell-family model detection."""

    @pytest.mark.parametrize(
        ("model", "expected"),
        [
            ("openai/gpt-5", False),
            ("openai/gpt-5-mini", False),
            ("openai/gpt-5.1", True),
            ("openai/gpt-5.2", True),
            ("openai/gpt-5.2-codex", True),
            ("openai/gpt-5.4", True),
            ("openai/gpt-5.4-mini", True),
            ("openai/gpt-5.6-sol", True),
            ("gpt-5.6-terra", True),
            ("gpt-5.6-luna", True),
            ("openai/gpt-6", True),
            ("openai/gpt-6.1", True),
            ("gpt-6-sol", True),
            ("openai/gpt-6-luna", True),
            ("gpt-6-astra", True),
        ],
    )
    def test_codex_variant_feature_matches_expected_models(
        self, model: str, expected: bool
    ):
        feature = CodexVariantFeature()
        tags = feature.get_tags({"model": model}, [])
        assert ("codex-variant" in tags) is expected


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

    def test_shell_array_is_enabled_exec_command_mode(self):
        """Shell array is_enabled returns False in exec_command mode."""
        tool = ShellArrayTool()
        result = tool.is_enabled({"shell_tool_mode": "exec_command"}, [], [], {})
        assert result is False

    def test_shell_command_is_enabled_auto_without_codex(self):
        """Shell command is_enabled returns False in auto mode without codex-variant."""
        tool = ShellCommandTool()
        result = tool.is_enabled({"shell_tool_mode": "auto"}, [], [], {})
        assert result is False

    def test_shell_command_is_enabled_auto_with_codex(self):
        """Shell command is_enabled returns False in auto mode with codex-variant
        (unified exec is selected instead)."""
        tool = ShellCommandTool()
        result = tool.is_enabled({"shell_tool_mode": "auto"}, ["codex-variant"], [], {})
        assert result is False

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

    def test_shell_command_is_enabled_exec_command_mode(self):
        """Shell command is_enabled returns False in exec_command mode."""
        tool = ShellCommandTool()
        result = tool.is_enabled({"shell_tool_mode": "exec_command"}, [], [], {})
        assert result is False

    def test_unified_exec_is_enabled_matrix(self):
        """Unified exec is_enabled across the mode matrix."""
        for tool in (ExecCommandTool(), WriteStdinTool()):
            assert tool.is_enabled({"shell_tool_mode": "exec_command"}, [], [], {}) is True
            assert tool.is_enabled({"shell_tool_mode": "auto"}, ["codex-variant"], [], {}) is True
            assert tool.is_enabled({}, ["codex-variant"], [], {}) is True
            assert tool.is_enabled({"shell_tool_mode": "auto"}, [], [], {}) is False
            assert tool.is_enabled({}, [], [], {}) is False
            assert tool.is_enabled({"shell_tool_mode": "shell"}, [], [], {}) is False
            assert tool.is_enabled({"shell_tool_mode": "shell_command"}, [], [], {}) is False


class TestAllShellToolsTogether:
    """Tests for all shell tools registered together."""

    def test_all_tools_registered_auto_without_codex(self):
        """With all tools registered, auto mode without codex should enable shell only."""
        core = AgentCore()
        core.register_provider(MockProvider)
        _register_all_shell_tools(core)
        core.register_tool(ShellTool)

        config = {"shell_tool_mode": "auto"}

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" in tool_names
        assert "shell_command" not in tool_names
        assert "exec_command" not in tool_names
        assert "write_stdin" not in tool_names
        assert "shell_legacy" not in tool_names

    def test_all_tools_registered_auto_with_codex(self):
        """With all tools registered, auto mode with codex should enable unified exec only."""
        core = AgentCore()
        core.register_provider(MockProvider)
        _register_all_shell_tools(core)
        core.register_tool(ShellTool)

        config = {"shell_tool_mode": "auto", "is_codex_model": True}

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" not in tool_names
        assert "shell_command" not in tool_names
        assert "exec_command" in tool_names
        assert "write_stdin" in tool_names
        assert "shell_legacy" not in tool_names

    def test_legacy_tool_can_be_enabled_via_force_enabled(self):
        """Legacy tool can be enabled via force_enabled_plugins."""
        core = AgentCore()
        core.register_provider(MockProvider)
        _register_all_shell_tools(core)
        core.register_tool(ShellTool)

        config = {
            "shell_tool_mode": "auto",
            "is_codex_model": True,
            "force_enabled_plugins": ["shell_legacy"],
        }

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell_legacy" in tool_names, "force_enabled_plugins should enable legacy tool"
        assert "exec_command" in tool_names
