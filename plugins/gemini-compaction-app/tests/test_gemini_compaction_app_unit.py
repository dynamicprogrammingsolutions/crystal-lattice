"""Unit tests for GeminiCompactionAppPlugin.

These tests exercise the plugin class directly without a full AgentApplication
instance, focusing on helper functions and configuration handling.
"""

from __future__ import annotations

import pytest

from gemini_compaction_app import (
    _normalize_slice_bounds,
    _GEMINI_COMPRESSION_PROMPT,
    _COMPACT_INSTRUCTION,
    _VERIFICATION_PROMPT,
    _ACKNOWLEDGMENT_MESSAGE,
    GeminiCompactionAppPlugin,
)


class TestNormalizeSliceBounds:
    """Tests for _normalize_slice_bounds helper."""

    def test_basic_range(self) -> None:
        start, end = _normalize_slice_bounds(10, 2, 7)
        assert start == 2
        assert end == 7

    def test_none_start_defaults_to_zero(self) -> None:
        start, end = _normalize_slice_bounds(10, None, 5)
        assert start == 0
        assert end == 5

    def test_none_end_defaults_to_count(self) -> None:
        start, end = _normalize_slice_bounds(10, 3, None)
        assert start == 3
        assert end == 10

    def test_both_none_uses_full_range(self) -> None:
        start, end = _normalize_slice_bounds(10, None, None)
        assert start == 0
        assert end == 10

    def test_negative_start_from_end(self) -> None:
        start, end = _normalize_slice_bounds(10, -3, 10)
        assert start == 7
        assert end == 10

    def test_negative_end_from_end(self) -> None:
        start, end = _normalize_slice_bounds(10, 0, -2)
        assert start == 0
        assert end == 8

    def test_negative_bounds_clamped(self) -> None:
        # Very negative values: -100 becomes 10 + (-100) = -90, then clamped to 0
        # So start=0, end=0 which is an empty range and raises ValueError
        with pytest.raises(ValueError, match="range selects no messages"):
            _normalize_slice_bounds(10, -100, -100)

    def test_excessive_bounds_clamped(self) -> None:
        start, end = _normalize_slice_bounds(10, 0, 100)
        assert start == 0
        assert end == 10

    def test_empty_range_raises(self) -> None:
        with pytest.raises(ValueError, match="range selects no messages"):
            _normalize_slice_bounds(10, 5, 5)

    def test_inverted_range_raises(self) -> None:
        with pytest.raises(ValueError, match="range selects no messages"):
            _normalize_slice_bounds(10, 7, 3)


class TestGeminiCompactionAppPlugin:
    """Tests for GeminiCompactionAppPlugin class."""

    def test_name_and_version(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        assert plugin.name == "gemini_compaction"
        assert plugin.version == "1.0.0"

    def test_compaction_type_constant(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        assert plugin.COMPACTION_TYPE == "gemini"

    def test_get_config_schema_returns_empty(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        schema = plugin.get_config_schema()
        assert schema == {}

    def test_init_returns_empty_state(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        state = plugin.init({})
        assert state == {}

    def test_get_ui_elements_filters_by_config_when_provided(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        # When config is None (global endpoint), always return elements
        elements = plugin.get_ui_elements(plugin._state, config=None)
        assert len(elements) == 3

        # When config is provided and compaction is enabled, return elements
        config_enabled = {"compaction": {"enabled": True, "type": "gemini"}}
        elements = plugin.get_ui_elements(plugin._state, config=config_enabled)
        assert len(elements) == 3

        # When config is provided and compaction is disabled, return empty
        config_disabled = {"compaction": {"enabled": False, "type": "gemini"}}
        elements = plugin.get_ui_elements(plugin._state, config=config_disabled)
        assert elements == []

        # When config is provided but type is not gemini, return empty
        config_wrong_type = {"compaction": {"enabled": True, "type": "qwen"}}
        elements = plugin.get_ui_elements(plugin._state, config=config_wrong_type)
        assert elements == []

    def test_get_ui_elements_returns_correct_structure(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})
        elements = plugin.get_ui_elements(plugin._state, config=None)

        # Check element types
        ui_types = [e.get("ui_type") for e in elements]
        assert "session_action" in ui_types
        assert "message_action" in ui_types

        # Check action IDs
        action_ids = [e.get("action_id") for e in elements]
        assert "compact_range" in action_ids

        # Check labels
        labels = [e.get("label") for e in elements]
        assert "Compact range" in labels
        assert "Compact messages up to here" in labels
        assert "Compact full history" in labels

    def test_get_actions(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})
        actions = plugin.get_actions(plugin._state)

        assert len(actions) == 1
        assert actions[0]["id"] == "compact_range"
        assert actions[0]["label"] == "Compact range"

        # Check inputs schema
        inputs = actions[0]["inputs"]
        assert "session_id" in inputs
        assert "start" in inputs
        assert "end" in inputs
        assert "instructions" in inputs
        assert inputs["session_id"]["required"] is True
        assert inputs["start"]["required"] is False


class TestCompactionEnablement:
    """Tests for _is_compaction_enabled helper."""

    def test_disabled_by_default(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        # Flattened config: no compaction section
        config = {}
        assert plugin._is_compaction_enabled(config) is False

    def test_disabled_when_enabled_false(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        # Flattened config: compaction at root level
        config = {"compaction": {"enabled": False}}
        assert plugin._is_compaction_enabled(config) is False

    def test_disabled_when_type_not_gemini(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        # Flattened config: compaction at root level
        config = {"compaction": {"enabled": True, "type": "qwen"}}
        assert plugin._is_compaction_enabled(config) is False

    def test_disabled_when_type_null(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        # Flattened config: compaction at root level
        config = {"compaction": {"enabled": True, "type": None}}
        assert plugin._is_compaction_enabled(config) is False

    def test_disabled_when_type_missing(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        # Flattened config: compaction at root level
        config = {"compaction": {"enabled": True}}  # No type
        assert plugin._is_compaction_enabled(config) is False

    def test_enabled_when_type_gemini(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        # Flattened config: compaction at root level
        config = {"compaction": {"enabled": True, "type": "gemini"}}
        assert plugin._is_compaction_enabled(config) is True

    def test_disabled_when_compaction_not_dict(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        # Flattened config: compaction at root level
        config = {"compaction": "invalid"}
        assert plugin._is_compaction_enabled(config) is False


class TestCompactionConfig:
    """Tests for _get_compaction_config helper."""

    def test_default_values_when_missing(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        # Flattened config: no compaction section
        config = {}
        result = plugin._get_compaction_config(config)

        assert result["enabled"] is False
        assert result["type"] is None
        assert result["agent_id"] is None
        assert result["prompt"] == _GEMINI_COMPRESSION_PROMPT
        assert result["settings_overrides"] == {}
        assert result["verification_pass"] is True

    def test_custom_agent_id(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        # Flattened config: compaction at root level
        config = {"compaction": {"agent_id": "summarizer"}}
        result = plugin._get_compaction_config(config)

        assert result["agent_id"] == "summarizer"

    def test_custom_prompt(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        custom_prompt = "Custom compaction prompt."
        # Flattened config: compaction at root level
        config = {"compaction": {"prompt": custom_prompt}}
        result = plugin._get_compaction_config(config)

        assert result["prompt"] == custom_prompt

    def test_settings_overrides(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        # Flattened config: compaction at root level
        config = {"compaction": {"settings_overrides": {"model": "gpt-4o-mini"}}}
        result = plugin._get_compaction_config(config)

        assert result["settings_overrides"] == {"model": "gpt-4o-mini"}

    def test_verification_pass_false(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        # Flattened config: compaction at root level
        config = {"compaction": {"verification_pass": False}}
        result = plugin._get_compaction_config(config)

        assert result["verification_pass"] is False

    def test_verification_pass_true(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        # Flattened config: compaction at root level
        config = {"compaction": {"verification_pass": True}}
        result = plugin._get_compaction_config(config)

        assert result["verification_pass"] is True

    def test_full_config(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        # Flattened config: compaction at root level
        config = {
            "compaction": {
                "enabled": True,
                "type": "gemini",
                "agent_id": "summarizer",
                "prompt": "Custom prompt",
                "settings_overrides": {"model": "gpt-4o-mini"},
                "verification_pass": False,
            }
        }
        result = plugin._get_compaction_config(config)

        assert result["enabled"] is True
        assert result["type"] == "gemini"
        assert result["agent_id"] == "summarizer"
        assert result["prompt"] == "Custom prompt"
        assert result["settings_overrides"] == {"model": "gpt-4o-mini"}
        assert result["verification_pass"] is False


class TestPrompts:
    """Tests for prompt content."""

    def test_compression_prompt_contains_required_sections(self) -> None:
        prompt = _GEMINI_COMPRESSION_PROMPT

        # Check for required XML sections
        assert "<state_snapshot>" in prompt
        assert "</state_snapshot>" in prompt
        assert "<overall_goal>" in prompt
        assert "<active_constraints>" in prompt
        assert "<key_knowledge>" in prompt
        assert "<artifact_trail>" in prompt
        assert "<file_system_state>" in prompt
        assert "<recent_actions>" in prompt
        assert "<task_state>" in prompt

        # Check for security rules
        assert "CRITICAL SECURITY RULE" in prompt
        assert "prompt injection" in prompt

        # Check for scratchpad instruction
        assert "<scratchpad>" in prompt

    def test_compact_instruction(self) -> None:
        assert "scratchpad" in _COMPACT_INSTRUCTION
        assert "<state_snapshot>" in _COMPACT_INSTRUCTION

    def test_verification_prompt(self) -> None:
        assert "Critically evaluate" in _VERIFICATION_PROMPT
        assert "state_snapshot" in _VERIFICATION_PROMPT
        assert "FINAL" in _VERIFICATION_PROMPT

    def test_acknowledgment_message(self) -> None:
        assert "Got it" in _ACKNOWLEDGMENT_MESSAGE
        assert "Thanks" in _ACKNOWLEDGMENT_MESSAGE


class TestPluginHelpers:
    """Tests for plugin internal helper methods."""

    def test_build_compaction_user_message_without_instructions(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        msg = plugin._build_compaction_user_message(None)
        assert msg == _COMPACT_INSTRUCTION

    def test_build_compaction_user_message_with_instructions(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        msg = plugin._build_compaction_user_message("Focus on the auth module.")
        assert "Focus on the auth module." in msg
        assert _COMPACT_INSTRUCTION in msg

    def test_extract_snapshot_from_response_with_snapshot(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        messages = [
            {"role": "user", "content": "test"},
            {
                "role": "assistant",
                "content": (
                    "<state_snapshot>\n"
                    "  <overall_goal>Test goal</overall_goal>\n"
                    "</state_snapshot>"
                ),
            },
        ]

        result = plugin._extract_snapshot_from_response(messages)
        assert result is not None
        assert "<state_snapshot>" in result
        assert "</state_snapshot>" in result

    def test_extract_snapshot_from_response_without_snapshot(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        messages = [
            {"role": "user", "content": "test"},
            {"role": "assistant", "content": "Just a regular response."},
        ]

        result = plugin._extract_snapshot_from_response(messages)
        assert result == "Just a regular response."

    def test_extract_snapshot_from_response_no_assistant(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        messages = [
            {"role": "user", "content": "test"},
        ]

        result = plugin._extract_snapshot_from_response(messages)
        assert result is None

    def test_extract_snapshot_from_response_empty_messages(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        result = plugin._extract_snapshot_from_response([])
        assert result is None


class TestExecuteActionErrors:
    """Tests for error handling in execute_action."""

    def test_unknown_action_id_raises(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        with pytest.raises(ValueError, match="Unknown action_id"):
            plugin.execute_action(None, "unknown_action", {}, plugin._state)  # type: ignore[arg-type]

    def test_missing_session_id_raises(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        with pytest.raises(ValueError, match="session_id must be a non-empty string"):
            plugin.execute_action(None, "compact_range", {}, plugin._state)  # type: ignore[arg-type]

    def test_empty_session_id_raises(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        with pytest.raises(ValueError, match="session_id must be a non-empty string"):
            plugin.execute_action(None, "compact_range", {"session_id": ""}, plugin._state)  # type: ignore[arg-type]
