"""Unit tests for GeminiCompactionFeaturePlugin.

Tests the plugin's enablement logic, configuration handling, and action definitions
without requiring a real LLM.
"""

from __future__ import annotations

import pytest
from typing import Any, Dict

from gemini_compaction_feature import GeminiCompactionFeaturePlugin


class TestCompactionEnablement:
    """Tests for compaction enablement logic."""

    def test_disabled_by_default(self) -> None:
        """Plugin should be disabled when no compaction config exists."""
        plugin = GeminiCompactionFeaturePlugin()
        config = {}  # No compaction section
        assert plugin._is_compaction_enabled(config) is False

    def test_disabled_when_enabled_false(self) -> None:
        """Plugin should be disabled when enabled is false."""
        plugin = GeminiCompactionFeaturePlugin()
        config = {"compaction": {"enabled": False}}
        assert plugin._is_compaction_enabled(config) is False

    def test_disabled_when_type_not_gemini(self) -> None:
        """Plugin should be disabled when type is not 'gemini'."""
        plugin = GeminiCompactionFeaturePlugin()
        config = {"compaction": {"enabled": True, "type": "qwen"}}
        assert plugin._is_compaction_enabled(config) is False

    def test_disabled_when_type_null(self) -> None:
        """Plugin should be disabled when type is null."""
        plugin = GeminiCompactionFeaturePlugin()
        config = {"compaction": {"enabled": True, "type": None}}
        assert plugin._is_compaction_enabled(config) is False

    def test_disabled_when_type_missing(self) -> None:
        """Plugin should be disabled when type is missing."""
        plugin = GeminiCompactionFeaturePlugin()
        config = {"compaction": {"enabled": True}}  # No type
        assert plugin._is_compaction_enabled(config) is False

    def test_enabled_when_type_gemini(self) -> None:
        """Plugin should be enabled when enabled=true and type='gemini'."""
        plugin = GeminiCompactionFeaturePlugin()
        config = {"compaction": {"enabled": True, "type": "gemini"}}
        assert plugin._is_compaction_enabled(config) is True

    def test_enabled_with_all_options(self) -> None:
        """Plugin should be enabled with all options configured."""
        plugin = GeminiCompactionFeaturePlugin()
        config = {
            "compaction": {
                "enabled": True,
                "type": "gemini",
                "agent_id": "summarizer",
                "prompt": "Custom prompt",
                "settings_overrides": {"model": "gpt-4o"},
                "verification_pass": False,
            }
        }
        assert plugin._is_compaction_enabled(config) is True


class TestCompactionConfig:
    """Tests for compaction configuration extraction."""

    def test_get_compaction_config_defaults(self) -> None:
        """Test default values for missing config keys."""
        plugin = GeminiCompactionFeaturePlugin()
        config = {"compaction": {"enabled": True, "type": "gemini"}}

        result = plugin._get_compaction_config(config)

        assert result["enabled"] is True
        assert result["type"] == "gemini"
        assert result["agent_id"] is None
        assert result["prompt"] is not None  # Should be default prompt
        assert result["settings_overrides"] == {}
        assert result["verification_pass"] is True  # Default

    def test_get_compaction_config_custom_values(self) -> None:
        """Test custom values are properly extracted."""
        plugin = GeminiCompactionFeaturePlugin()
        config = {
            "compaction": {
                "enabled": True,
                "type": "gemini",
                "agent_id": "summarizer",
                "prompt": "Custom prompt",
                "settings_overrides": {"model": "gpt-4o"},
                "verification_pass": False,
            }
        }

        result = plugin._get_compaction_config(config)

        assert result["agent_id"] == "summarizer"
        assert result["prompt"] == "Custom prompt"
        assert result["settings_overrides"] == {"model": "gpt-4o"}
        assert result["verification_pass"] is False

    def test_get_compaction_config_empty_dict(self) -> None:
        """Test behavior with empty compaction dict."""
        plugin = GeminiCompactionFeaturePlugin()
        config = {"compaction": {}}

        result = plugin._get_compaction_config(config)

        assert result["enabled"] is False
        assert result["type"] is None
        assert result["agent_id"] is None
        assert result["verification_pass"] is True  # Default


class TestActionDefinitions:
    """Tests for action definitions."""

    def test_get_actions_returns_compact_range(self) -> None:
        """Test that get_actions returns the compact_range action."""
        plugin = GeminiCompactionFeaturePlugin()
        actions = plugin.get_actions({})

        assert len(actions) == 1
        assert actions[0]["id"] == "compact_range"
        assert "start" in actions[0]["inputs"]
        assert "end" in actions[0]["inputs"]
        assert "end_inclusive" in actions[0]["inputs"]
        assert "instructions" in actions[0]["inputs"]

    def test_execute_action_unknown_action_returns_error(self) -> None:
        """Test that unknown action returns error."""
        plugin = GeminiCompactionFeaturePlugin()

        # Mock session and native_messages
        class MockSession:
            messages = []
            session_id = "test"
            metadata = {}

        result = plugin.execute_action(
            "unknown_action",
            MockSession(),
            [],
            {},
            {"core": None, "config": {}},
            {},
        )

        assert "error" in result
        assert result["error"]["type"] == "unknown_action"

    def test_execute_action_missing_core_returns_error(self) -> None:
        """Test that missing core in context returns error."""
        plugin = GeminiCompactionFeaturePlugin()

        class MockSession:
            messages = []
            session_id = "test"
            metadata = {}

        result = plugin.execute_action(
            "compact_range",
            MockSession(),
            [],
            {},
            {},  # No core
            {},
        )

        assert "error" in result
        assert result["error"]["type"] in ("invalid_context", "missing_core")


class TestAnchorInstruction:
    """Tests for anchor instruction building."""

    def test_build_anchor_instruction_first_snapshot(self) -> None:
        """Test anchor instruction for first snapshot."""
        plugin = GeminiCompactionFeaturePlugin()
        instruction = plugin._build_anchor_instruction(has_previous_snapshot=False)
        assert "Generate a new <state_snapshot>" in instruction

    def test_build_anchor_instruction_with_previous(self) -> None:
        """Test anchor instruction when previous snapshot exists."""
        plugin = GeminiCompactionFeaturePlugin()
        instruction = plugin._build_anchor_instruction(has_previous_snapshot=True)
        assert "A previous <state_snapshot> exists" in instruction
        assert "integrate all still-relevant information" in instruction


class TestSnapshotDetection:
    """Tests for previous snapshot detection."""

    def test_has_previous_snapshot_true(self) -> None:
        """Test detection of previous snapshot."""
        plugin = GeminiCompactionFeaturePlugin()

        class MockMessage:
            def __init__(self, content: str):
                self.content = content

        messages = [
            MockMessage("Hello"),
            MockMessage("<state_snapshot>...</state_snapshot>"),
        ]

        assert plugin._has_previous_snapshot(messages) is True

    def test_has_previous_snapshot_false(self) -> None:
        """Test detection when no previous snapshot."""
        plugin = GeminiCompactionFeaturePlugin()

        class MockMessage:
            def __init__(self, content: str):
                self.content = content

        messages = [
            MockMessage("Hello"),
            MockMessage("No snapshot here"),
        ]

        assert plugin._has_previous_snapshot(messages) is False
