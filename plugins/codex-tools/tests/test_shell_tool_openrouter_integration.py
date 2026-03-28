"""Integration tests for shell tool selection with OpenRouter provider.

Tests the complete shell tool selection flow using:
- Real OpenRouter provider
- CodexVariantFeature for codex-variant tag emission
- Shell tools (shell, shell_command, shell_legacy)

No real API requests are made - only config loading and plugin resolution.
"""

from __future__ import annotations

import os
from typing import Any, Dict, List

import pytest

from agent_core import AgentCore
from openrouter_plugins.openrouter_provider import OpenRouterProvider
from codex_tools.shell_tool import ShellArrayTool
from codex_tools.shell_command_tool import ShellCommandTool
from codex_tools.shell_tool_legacy import ShellTool
from codex_tools.codex_variant_feature import CodexVariantFeature


# Skip all tests if OPENROUTER_API_KEY is not set
pytestmark = pytest.mark.skipif(
    not os.environ.get("OPENROUTER_API_KEY"),
    reason="OPENROUTER_API_KEY not set",
)


class TestShellToolSelectionWithOpenRouter:
    """Tests for shell tool selection with real OpenRouter provider."""

    def _create_core_with_plugins(self) -> AgentCore:
        """Create AgentCore with OpenRouter provider and codex-tools."""
        core = AgentCore()
        core.register_provider(OpenRouterProvider)
        core.register_feature(CodexVariantFeature)
        core.register_tool(ShellArrayTool)
        core.register_tool(ShellCommandTool)
        core.register_tool(ShellTool)
        return core

    def _make_config(
        self,
        model: str,
        shell_tool_mode: str = "auto",
        force_enabled_plugins: List[str] = None,
    ) -> Dict[str, Any]:
        """Create a config dict for testing."""
        config = {
            "provider": "openrouter",
            "model": model,
            "api_key": os.environ.get("OPENROUTER_API_KEY", "test-key"),
            "shell_tool_mode": shell_tool_mode,
        }
        if force_enabled_plugins:
            config["force_enabled_plugins"] = force_enabled_plugins
        return config

    def test_codex_model_enables_shell_command_auto_mode(self):
        """Codex model (ends with -codex) should enable shell_command in auto mode."""
        core = self._create_core_with_plugins()
        config = self._make_config(model="openai/gpt-5.2-codex")

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "codex-variant" in tags, "codex-variant tag should be emitted for -codex model"
        assert "shell" not in tool_names, "shell should be disabled for codex model"
        assert "shell_command" in tool_names, "shell_command should be enabled for codex model"
        assert "shell_legacy" not in tool_names, "shell_legacy should be disabled by default"

    def test_non_codex_model_enables_shell_auto_mode(self):
        """Non-codex model should enable shell (array) in auto mode."""
        core = self._create_core_with_plugins()
        config = self._make_config(model="openai/gpt-5")

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "codex-variant" not in tags, "codex-variant tag should not be emitted for non-codex model"
        assert "shell" in tool_names, "shell should be enabled for non-codex model"
        assert "shell_command" not in tool_names, "shell_command should be disabled for non-codex model"

    def test_gpt_5_1_codex_enables_shell_command(self):
        """gpt-5.1-codex should enable shell_command."""
        core = self._create_core_with_plugins()
        config = self._make_config(model="openai/gpt-5.1-codex")

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "codex-variant" in tags
        assert "shell_command" in tool_names
        assert "shell" not in tool_names

    def test_gpt_5_3_codex_enables_shell_command(self):
        """gpt-5.3-codex should enable shell_command."""
        core = self._create_core_with_plugins()
        config = self._make_config(model="openai/gpt-5.3-codex")

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "codex-variant" in tags
        assert "shell_command" in tool_names
        assert "shell" not in tool_names

    def test_shell_mode_forces_shell_for_codex_model(self):
        """shell_tool_mode='shell' should force shell even for codex model."""
        core = self._create_core_with_plugins()
        config = self._make_config(
            model="openai/gpt-5.2-codex",
            shell_tool_mode="shell",
        )

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "codex-variant" in tags  # Tag is still emitted
        assert "shell" in tool_names, "shell should be forced on in shell mode"
        assert "shell_command" not in tool_names, "shell_command should be off in shell mode"

    def test_shell_mode_forces_shell_for_non_codex_model(self):
        """shell_tool_mode='shell' should force shell for non-codex model."""
        core = self._create_core_with_plugins()
        config = self._make_config(
            model="openai/gpt-5",
            shell_tool_mode="shell",
        )

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" in tool_names
        assert "shell_command" not in tool_names

    def test_shell_command_mode_forces_shell_command_for_non_codex(self):
        """shell_tool_mode='shell_command' should force shell_command for non-codex model."""
        core = self._create_core_with_plugins()
        config = self._make_config(
            model="openai/gpt-5",
            shell_tool_mode="shell_command",
        )

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "codex-variant" not in tags
        assert "shell" not in tool_names, "shell should be off in shell_command mode"
        assert "shell_command" in tool_names, "shell_command should be forced on"

    def test_force_enabled_plugins_enables_both_tools(self):
        """force_enabled_plugins should enable both shell tools regardless of mode."""
        core = self._create_core_with_plugins()
        config = self._make_config(
            model="openai/gpt-5.2-codex",
            shell_tool_mode="auto",
            force_enabled_plugins=["shell", "shell_command"],
        )

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" in tool_names, "force_enabled should enable shell"
        assert "shell_command" in tool_names, "force_enabled should enable shell_command"

    def test_force_enabled_enables_legacy_tool(self):
        """force_enabled_plugins should enable shell_legacy."""
        core = self._create_core_with_plugins()
        config = self._make_config(
            model="openai/gpt-5",
            shell_tool_mode="auto",
            force_enabled_plugins=["shell_legacy"],
        )

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "shell" in tool_names, "shell should be enabled for non-codex model"
        assert "shell_legacy" in tool_names, "force_enabled should enable legacy tool"

    def test_gemini_model_enables_shell(self):
        """Non-codex model (gemini) should enable shell."""
        core = self._create_core_with_plugins()
        config = self._make_config(model="google/gemini-2.5-flash")

        provider, exts, feats, tools, tags = core._resolve_plugins_for_config(config)
        tool_names = [t.name for t in tools]

        assert "codex-variant" not in tags
        assert "shell" in tool_names
        assert "shell_command" not in tool_names


class TestCodexVariantFeature:
    """Tests for CodexVariantFeature tag emission."""

    def test_feature_emits_tag_for_codex_model(self):
        """Feature should emit codex-variant tag for -codex suffix."""
        feature = CodexVariantFeature()
        tags = feature.get_tags({"model": "openai/gpt-5.2-codex"}, [])
        assert tags == ["codex-variant"]

    def test_feature_no_tag_for_non_codex_model(self):
        """Feature should not emit tag for non-codex model."""
        feature = CodexVariantFeature()
        tags = feature.get_tags({"model": "openai/gpt-5"}, [])
        assert tags == []

    def test_feature_no_tag_for_empty_model(self):
        """Feature should handle empty model gracefully."""
        feature = CodexVariantFeature()
        tags = feature.get_tags({}, [])
        assert tags == []

    def test_feature_no_tag_for_none_model(self):
        """Feature should handle None model gracefully."""
        feature = CodexVariantFeature()
        tags = feature.get_tags({"model": None}, [])
        assert tags == []

    def test_feature_handles_various_codex_models(self):
        """Feature should recognize various codex model patterns."""
        feature = CodexVariantFeature()
        
        codex_models = [
            "openai/gpt-5-codex",
            "openai/gpt-5.1-codex",
            "openai/gpt-5.2-codex",
            "openai/gpt-5.3-codex",
            "openai/gpt-5.4-codex",
        ]
        
        for model in codex_models:
            tags = feature.get_tags({"model": model}, [])
            assert tags == ["codex-variant"], f"Expected codex-variant for {model}"

    def test_feature_does_not_match_partial_codex(self):
        """Feature should not match 'codex' in middle of name."""
        feature = CodexVariantFeature()
        
        non_codex_models = [
            "openai/codex-1",  # Not at end
            "openai/codex-model",  # Not at end  
            "openai/gpt-codex-pro",  # Not at end
        ]
        
        for model in non_codex_models:
            tags = feature.get_tags({"model": model}, [])
            assert tags == [], f"Should not emit tag for {model}"