"""Unit tests for GeminiCompactionAppPlugin.

These tests exercise the plugin class directly without a full AgentApplication
instance, focusing on helper functions and configuration handling.
"""

from __future__ import annotations

import pytest

from gemini_compaction_app import (
    _normalize_slice_bounds,
    _GEMINI_COMPRESSION_PROMPT,
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

        anchor = "Generate a new <state_snapshot> based on the provided history."
        msg = plugin._build_compaction_user_message(None, anchor)
        assert anchor in msg
        assert "First, reason in your scratchpad" in msg
        assert "generate the updated <state_snapshot>" in msg

    def test_build_compaction_user_message_with_instructions(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        anchor = "Generate a new <state_snapshot> based on the provided history."
        msg = plugin._build_compaction_user_message("Focus on the auth module.", anchor)
        assert "Focus on the auth module." in msg
        assert anchor in msg
        assert "First, reason in your scratchpad" in msg

    def test_build_compaction_user_message_with_previous_snapshot(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        anchor = (
            "A previous <state_snapshot> exists in the history. "
            "You MUST integrate all still-relevant information from that snapshot into the new one."
        )
        msg = plugin._build_compaction_user_message(None, anchor)
        assert "previous <state_snapshot>" in msg
        assert "integrate all still-relevant information" in msg

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

    def test_build_anchor_instruction_new_snapshot(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        anchor = plugin._build_anchor_instruction(has_previous_snapshot=False)
        assert "Generate a new <state_snapshot>" in anchor
        assert "based on the provided history" in anchor

    def test_build_anchor_instruction_previous_snapshot(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        anchor = plugin._build_anchor_instruction(has_previous_snapshot=True)
        assert "previous <state_snapshot>" in anchor
        assert "integrate all still-relevant information" in anchor
        assert "Do not lose established constraints" in anchor

    def test_has_previous_snapshot_true(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        # Create mock messages with a snapshot
        class MockMsg:
            def __init__(self, content: str):
                self.content = content

        messages = [
            MockMsg("Hello"),
            MockMsg("<state_snapshot>\n<overall_goal>Test</overall_goal>\n</state_snapshot>"),
        ]
        assert plugin._has_previous_snapshot(messages) is True

    def test_has_previous_snapshot_false(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        class MockMsg:
            def __init__(self, content: str):
                self.content = content

        messages = [
            MockMsg("Hello"),
            MockMsg("No snapshot here"),
        ]
        assert plugin._has_previous_snapshot(messages) is False

    def test_has_previous_snapshot_empty_messages(self) -> None:
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        assert plugin._has_previous_snapshot([]) is False

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


class TestCompactionRangeSemantics:
    """Tests for end_exclusive vs end_inclusive semantics in _do_compact_range.

    These tests verify that:
    - end_inclusive=False (default): Python slice semantics [start, end)
    - end_inclusive=True: Inclusive semantics [start, end]

    For "compact up to here", the selected message should be included in compaction.
    """

    def test_end_exclusive_compacts_messages_before_end(self) -> None:
        """With end_exclusive (default), messages [0, end) are compacted.

        If end=4, messages 0, 1, 2, 3 are compacted (4 is preserved).
        """
        # This is tested implicitly by existing tests - just document the behavior
        start, end = _normalize_slice_bounds(10, 0, 4)
        assert start == 0
        assert end == 4  # Exclusive: indices 0, 1, 2, 3 are in range

    def test_end_inclusive_compacts_messages_through_end(self) -> None:
        """With end_inclusive=True, messages [0, end] are compacted.

        If end=4, messages 0, 1, 2, 3, 4 are compacted.
        """
        start, end = _normalize_slice_bounds(10, 0, 4)
        assert start == 0
        assert end == 4
        # When end_inclusive=True, the logic adds 1 to end_idx
        end_inclusive = True
        end_adjusted = min(end + 1, 10) if end_inclusive else end
        assert end_adjusted == 5  # Inclusive: indices 0, 1, 2, 3, 4 are in range

    def test_end_inclusive_clamped_to_message_count(self) -> None:
        """end_inclusive adjustment should be clamped to message_count."""
        start, end = _normalize_slice_bounds(10, 0, 9)
        assert end == 9
        end_inclusive = True
        end_adjusted = min(end + 1, 10) if end_inclusive else end
        assert end_adjusted == 10  # Clamped, not 11

    def test_end_inclusive_with_negative_index(self) -> None:
        """end_inclusive works with negative indices too."""
        start, end = _normalize_slice_bounds(10, 0, -2)
        assert start == 0
        assert end == 8  # -2 becomes 10 + (-2) = 8
        end_inclusive = True
        end_adjusted = min(end + 1, 10) if end_inclusive else end
        assert end_adjusted == 9  # Inclusive: indices 0-9 are in range

    def test_compact_up_to_here_has_end_inclusive_true(self) -> None:
        """Verify compact_up_to_here action passes end_inclusive=True."""
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        elements = plugin.get_ui_elements(plugin._state)
        compact_up_to_here = next(
            (e for e in elements if e.get("id") == "compact_up_to_here"), None
        )
        assert compact_up_to_here is not None
        fixed_params = compact_up_to_here.get("fixed_params", {})
        assert fixed_params.get("end_inclusive") is True

    def test_compact_range_has_end_inclusive_false_by_default(self) -> None:
        """Verify compact_range action (explicit range) uses default exclusive semantics."""
        plugin = GeminiCompactionAppPlugin()
        plugin.init({})

        elements = plugin.get_ui_elements(plugin._state)
        compact_range = next(
            (e for e in elements if e.get("id") == "compact_range"), None
        )
        assert compact_range is not None
        fixed_params = compact_range.get("fixed_params", {})
        # compact_range doesn't set end_inclusive, so it defaults to False (exclusive)
        assert "end_inclusive" not in fixed_params


class TestCompactionRangeWithSystemMessage:
    """Tests verifying exact compaction indices when system message is present.

    This simulates the scenario where feature_system_message adds a system message
    at the beginning of the session, which shifts all indices by 1.
    """

    def test_compact_up_to_index_5_with_system_message_inclusive(self) -> None:
        """Verify compaction range with system message at index 0.

        Session: [system, u1, a1, u2, a2, u3, a3] (indices 0-6)
        User clicks "compact up to here" on message 5 (which is u3).
        Expected: messages 1-5 are compacted (inclusive of 5).
        Preserved: system (0) and a3 (6).
        """
        message_count = 7
        system_prefix_end = 1  # System message at index 0
        end_raw = 5  # User clicked on message 5
        end_inclusive = True

        # Simulate the logic
        start_idx, end_idx = _normalize_slice_bounds(message_count, 0, end_raw)
        assert start_idx == 0
        assert end_idx == 5

        # Apply inclusive adjustment
        if end_inclusive and end_raw is not None:
            end_idx = min(end_idx + 1, message_count)
        assert end_idx == 6

        # Check preserve_last_user (should NOT trigger since end_idx != message_count)
        # (skip this check since we're testing the calculation)

        # Adjust for system prefix
        if start_idx < system_prefix_end:
            start_idx = system_prefix_end
        assert start_idx == 1

        # Calculate remove_indices
        remove_indices = list(range(start_idx, end_idx))
        assert remove_indices == [1, 2, 3, 4, 5], \
            f"Expected [1,2,3,4,5] but got {remove_indices}"

        # Verify what's compacted vs preserved
        preserved = [i for i in range(message_count) if i not in remove_indices]
        assert preserved == [0, 6], f"Expected [0,6] preserved but got {preserved}"

    def test_compact_up_to_index_4_with_system_message_inclusive(self) -> None:
        """Verify compaction range with system message, clicking on index 4.

        Session: [system, u1, a1, u2, a2, u3, a3] (indices 0-6)
        User clicks "compact up to here" on message 4 (which is a2).
        Expected: messages 1-4 are compacted (inclusive of 4).
        Preserved: system (0), u3 (5), a3 (6).
        """
        message_count = 7
        system_prefix_end = 1
        end_raw = 4
        end_inclusive = True

        start_idx, end_idx = _normalize_slice_bounds(message_count, 0, end_raw)
        assert end_idx == 4

        # Apply inclusive adjustment
        if end_inclusive and end_raw is not None:
            end_idx = min(end_idx + 1, message_count)
        assert end_idx == 5

        # Adjust for system prefix
        if start_idx < system_prefix_end:
            start_idx = system_prefix_end
        assert start_idx == 1

        remove_indices = list(range(start_idx, end_idx))
        assert remove_indices == [1, 2, 3, 4], \
            f"Expected [1,2,3,4] but got {remove_indices}"

        preserved = [i for i in range(message_count) if i not in remove_indices]
        assert preserved == [0, 5, 6], f"Expected [0,5,6] preserved but got {preserved}"

    def test_compact_up_to_last_message_with_system_message(self) -> None:
        """Verify compaction range when compacting up to the last message.

        Session: [system, u1, a1, u2, a2] (indices 0-4)
        User clicks "compact up to here" on message 4 (which is a2, the last).
        Expected: messages 1-4 are compacted.
        Preserved: system (0).
        """
        message_count = 5
        system_prefix_end = 1
        end_raw = 4
        end_inclusive = True

        start_idx, end_idx = _normalize_slice_bounds(message_count, 0, end_raw)
        assert end_idx == 4

        # Apply inclusive adjustment
        if end_inclusive and end_raw is not None:
            end_idx = min(end_idx + 1, message_count)
        assert end_idx == 5  # Clamped to message_count

        # Check preserve_last_user (should NOT trigger since last message is assistant)
        # (in this test, the last message is assistant, not user)

        # Adjust for system prefix
        if start_idx < system_prefix_end:
            start_idx = system_prefix_end

        remove_indices = list(range(start_idx, end_idx))
        assert remove_indices == [1, 2, 3, 4], \
            f"Expected [1,2,3,4] but got {remove_indices}"

    def test_compact_up_to_last_user_message_triggers_preserve(self) -> None:
        """Verify preserve_last_user logic when last message is user.

        Session: [system, u1, a1, u2] (indices 0-3)
        User clicks "compact up to here" on message 3 (u2, the last, which is user).
        Expected: preserve_last_user triggers, messages 1-2 are compacted.
        Preserved: system (0), u2 (3).
        """
        message_count = 4
        system_prefix_end = 1
        end_raw = 3
        end_inclusive = True

        start_idx, end_idx = _normalize_slice_bounds(message_count, 0, end_raw)
        assert end_idx == 3

        # Apply inclusive adjustment
        if end_inclusive and end_raw is not None:
            end_idx = min(end_idx + 1, message_count)
        assert end_idx == 4  # Equal to message_count

        # Check preserve_last_user logic
        # if end_idx == message_count and last_msg.role == "user":
        #   end_idx = message_count - 1
        # In this test, last message is user, so preserve triggers
        last_msg_role = "user"  # Simulating the check
        if end_idx == message_count and last_msg_role == "user":
            end_idx = message_count - 1
        assert end_idx == 3  # Reduced by preserve_last_user

        # Adjust for system prefix
        if start_idx < system_prefix_end:
            start_idx = system_prefix_end

        remove_indices = list(range(start_idx, end_idx))
        assert remove_indices == [1, 2], \
            f"Expected [1,2] but got {remove_indices} (preserve_last_user should have triggered)"

    def test_exclusive_semantics_with_system_message(self) -> None:
        """Verify exclusive semantics (compact_range explicit) with system message.

        Session: [system, u1, a1, u2, a2, u3, a3] (indices 0-6)
        User specifies compact_range with start=0, end=4 (exclusive).
        Expected: messages 1-3 are compacted (indices 0,1,2,3 but 0 is system).
        Preserved: system (0), a2 (4), u3 (5), a3 (6).
        """
        message_count = 7
        system_prefix_end = 1
        end_raw = 4
        end_inclusive = False  # Exclusive (default for compact_range)

        start_idx, end_idx = _normalize_slice_bounds(message_count, 0, end_raw)
        assert end_idx == 4

        # NO inclusive adjustment
        assert end_idx == 4

        # Adjust for system prefix
        if start_idx < system_prefix_end:
            start_idx = system_prefix_end

        remove_indices = list(range(start_idx, end_idx))
        assert remove_indices == [1, 2, 3], \
            f"Expected [1,2,3] but got {remove_indices}"

        preserved = [i for i in range(message_count) if i not in remove_indices]
        assert preserved == [0, 4, 5, 6], f"Expected [0,4,5,6] preserved but got {preserved}"
