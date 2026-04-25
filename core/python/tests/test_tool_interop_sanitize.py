"""Tests for tool call sanitization in tool_interop."""

import pytest

from agent_core.tool_interop import (
    DEFAULT_TOOL_INTEROP_REGISTRY,
    OpenAIChatToolCallAccessor,
    OpenAIResponsesFunctionCallAccessor,
    OpenAIResponsesCustomToolCallAccessor,
    ToolInteropError,
)


class TestOpenAIChatToolCallAccessorSanitize:
    """Tests for OpenAIChatToolCallAccessor.sanitize_call."""

    def test_sanitize_valid_json_arguments(self) -> None:
        """Valid JSON arguments should be unchanged."""
        accessor = OpenAIChatToolCallAccessor()
        call = {
            "id": "call_123",
            "type": "function",
            "function": {"name": "test", "arguments": '{"a": 1, "b": 2}'},
        }
        result = accessor.sanitize_call(call)
        assert result == call
        assert result["function"]["arguments"] == '{"a": 1, "b": 2}'

    def test_sanitize_invalid_json_arguments(self) -> None:
        """Invalid JSON arguments should be replaced with empty object."""
        accessor = OpenAIChatToolCallAccessor()
        call = {
            "id": "call_123",
            "type": "function",
            "function": {"name": "test", "arguments": "{corrupted json"},
        }
        result = accessor.sanitize_call(call)
        assert result["function"]["arguments"] == "{}"
        assert result["id"] == "call_123"
        assert result["function"]["name"] == "test"

    def test_sanitize_dict_arguments(self) -> None:
        """Dict arguments (already parsed) should be unchanged."""
        accessor = OpenAIChatToolCallAccessor()
        call = {
            "id": "call_123",
            "type": "function",
            "function": {"name": "test", "arguments": {"a": 1, "b": 2}},
        }
        result = accessor.sanitize_call(call)
        assert result == call
        assert result["function"]["arguments"] == {"a": 1, "b": 2}

    def test_sanitize_empty_string_arguments(self) -> None:
        """Empty string arguments should be valid JSON empty object."""
        accessor = OpenAIChatToolCallAccessor()
        call = {
            "id": "call_123",
            "type": "function",
            "function": {"name": "test", "arguments": ""},
        }
        result = accessor.sanitize_call(call)
        # Empty string is valid JSON (not what we want but it parses)
        # Actually empty string is NOT valid JSON, so it should be sanitized
        assert result["function"]["arguments"] == "{}"

    def test_sanitize_missing_function(self) -> None:
        """Missing function object should return call unchanged."""
        accessor = OpenAIChatToolCallAccessor()
        call = {"id": "call_123", "type": "function"}
        result = accessor.sanitize_call(call)
        assert result == call

    def test_sanitize_missing_arguments(self) -> None:
        """Missing arguments should return call unchanged."""
        accessor = OpenAIChatToolCallAccessor()
        call = {
            "id": "call_123",
            "type": "function",
            "function": {"name": "test"},
        }
        result = accessor.sanitize_call(call)
        assert result == call


class TestOpenAIResponsesFunctionCallAccessorSanitize:
    """Tests for OpenAIResponsesFunctionCallAccessor.sanitize_call."""

    def test_sanitize_valid_json_arguments(self) -> None:
        """Valid JSON arguments should be unchanged."""
        accessor = OpenAIResponsesFunctionCallAccessor()
        call = {
            "type": "function_call",
            "call_id": "call_123",
            "name": "test",
            "arguments": '{"a": 1}',
        }
        result = accessor.sanitize_call(call)
        assert result == call

    def test_sanitize_invalid_json_arguments(self) -> None:
        """Invalid JSON arguments should be replaced with empty object."""
        accessor = OpenAIResponsesFunctionCallAccessor()
        call = {
            "type": "function_call",
            "call_id": "call_123",
            "name": "test",
            "arguments": "{corrupted",
        }
        result = accessor.sanitize_call(call)
        assert result["arguments"] == "{}"
        assert result["call_id"] == "call_123"
        assert result["name"] == "test"

    def test_sanitize_dict_arguments(self) -> None:
        """Dict arguments should be unchanged."""
        accessor = OpenAIResponsesFunctionCallAccessor()
        call = {
            "type": "function_call",
            "call_id": "call_123",
            "name": "test",
            "arguments": {"a": 1},
        }
        result = accessor.sanitize_call(call)
        assert result == call

    def test_sanitize_missing_arguments(self) -> None:
        """Missing arguments should return call unchanged."""
        accessor = OpenAIResponsesFunctionCallAccessor()
        call = {
            "type": "function_call",
            "call_id": "call_123",
            "name": "test",
        }
        result = accessor.sanitize_call(call)
        assert result == call


class TestOpenAIResponsesCustomToolCallAccessorSanitize:
    """Tests for OpenAIResponsesCustomToolCallAccessor.sanitize_call."""

    def test_sanitize_returns_unchanged_for_text_payload(self) -> None:
        """Custom tool calls with text payloads should be unchanged."""
        accessor = OpenAIResponsesCustomToolCallAccessor()
        call = {
            "type": "custom_tool_call",
            "call_id": "call_123",
            "name": "test",
            "input": "any text content",
        }
        result = accessor.sanitize_call(call)
        assert result == call

    def test_sanitize_unchanged_for_various_inputs(self) -> None:
        """Custom tool calls should never be modified."""
        accessor = OpenAIResponsesCustomToolCallAccessor()
        call = {
            "type": "custom_tool_call",
            "call_id": "call_123",
            "name": "test",
            "input": "{corrupted json",  # This is text, not JSON
        }
        result = accessor.sanitize_call(call)
        assert result == call
        assert result["input"] == "{corrupted json"


class TestToolInteropRegistrySanitize:
    """Tests for ToolInteropRegistry.sanitize_tool_call."""

    def test_sanitize_tool_call_delegates_to_correct_accessor(self) -> None:
        """Registry should delegate to the correct accessor based on format."""
        # OpenAI Chat format
        chat_call = {
            "id": "call_123",
            "type": "function",
            "function": {"name": "test", "arguments": "{bad"},
        }
        result = DEFAULT_TOOL_INTEROP_REGISTRY.sanitize_tool_call(chat_call)
        assert result["function"]["arguments"] == "{}"

        # OpenAI Responses function_call format
        responses_call = {
            "type": "function_call",
            "call_id": "call_456",
            "name": "test",
            "arguments": "{also_bad",
        }
        result = DEFAULT_TOOL_INTEROP_REGISTRY.sanitize_tool_call(responses_call)
        assert result["arguments"] == "{}"

        # OpenAI Responses custom_tool_call format (no sanitization)
        custom_call = {
            "type": "custom_tool_call",
            "call_id": "call_789",
            "name": "test",
            "input": "any text",
        }
        result = DEFAULT_TOOL_INTEROP_REGISTRY.sanitize_tool_call(custom_call)
        assert result == custom_call

    def test_sanitize_tool_call_returns_unchanged_for_valid_json(self) -> None:
        """Valid JSON should pass through unchanged."""
        call = {
            "id": "call_123",
            "type": "function",
            "function": {"name": "test", "arguments": '{"a": 1}'},
        }
        result = DEFAULT_TOOL_INTEROP_REGISTRY.sanitize_tool_call(call)
        assert result == call

    def test_sanitize_tool_call_returns_unchanged_for_unknown_format(self) -> None:
        """Unknown format should return call unchanged."""
        call = {"unknown": "format"}
        result = DEFAULT_TOOL_INTEROP_REGISTRY.sanitize_tool_call(call)
        assert result == call


class TestOpenAIChatToolCallAccessorGetPayload:
    """Tests for OpenAIChatToolCallAccessor.get_payload after removing get_arguments."""

    def test_get_payload_parses_valid_json_string(self) -> None:
        """Valid JSON string should be parsed to dict."""
        accessor = OpenAIChatToolCallAccessor()
        call = {
            "id": "call_123",
            "type": "function",
            "function": {"name": "test", "arguments": '{"a": 1, "b": 2}'},
        }
        result = accessor.get_payload(call)
        assert result == {"a": 1, "b": 2}

    def test_get_payload_returns_empty_dict_for_invalid_json(self) -> None:
        """Invalid JSON string should return empty dict."""
        accessor = OpenAIChatToolCallAccessor()
        call = {
            "id": "call_123",
            "type": "function",
            "function": {"name": "test", "arguments": "{corrupted"},
        }
        result = accessor.get_payload(call)
        assert result == {}

    def test_get_payload_returns_dict_for_dict_arguments(self) -> None:
        """Dict arguments should be returned as-is."""
        accessor = OpenAIChatToolCallAccessor()
        call = {
            "id": "call_123",
            "type": "function",
            "function": {"name": "test", "arguments": {"a": 1}},
        }
        result = accessor.get_payload(call)
        assert result == {"a": 1}

    def test_get_payload_returns_empty_for_missing_function(self) -> None:
        """Missing function should return empty dict."""
        accessor = OpenAIChatToolCallAccessor()
        call = {"id": "call_123", "type": "function"}
        result = accessor.get_payload(call)
        assert result == {}

    def test_get_payload_returns_empty_for_non_dict_parsed(self) -> None:
        """Non-dict parsed JSON should return empty dict."""
        accessor = OpenAIChatToolCallAccessor()
        call = {
            "id": "call_123",
            "type": "function",
            "function": {"name": "test", "arguments": "[1, 2, 3]"},  # Array, not object
        }
        result = accessor.get_payload(call)
        assert result == {}


class TestOpenAIResponsesFunctionCallAccessorGetPayload:
    """Tests for OpenAIResponsesFunctionCallAccessor.get_payload."""

    def test_get_payload_parses_valid_json_string(self) -> None:
        """Valid JSON string should be parsed to dict."""
        accessor = OpenAIResponsesFunctionCallAccessor()
        call = {
            "type": "function_call",
            "call_id": "call_123",
            "name": "test",
            "arguments": '{"a": 1}',
        }
        result = accessor.get_payload(call)
        assert result == {"a": 1}

    def test_get_payload_returns_empty_dict_for_invalid_json(self) -> None:
        """Invalid JSON string should return empty dict."""
        accessor = OpenAIResponsesFunctionCallAccessor()
        call = {
            "type": "function_call",
            "call_id": "call_123",
            "name": "test",
            "arguments": "{bad",
        }
        result = accessor.get_payload(call)
        assert result == {}

    def test_get_payload_returns_empty_for_missing_arguments(self) -> None:
        """Missing arguments should return empty dict."""
        accessor = OpenAIResponsesFunctionCallAccessor()
        call = {
            "type": "function_call",
            "call_id": "call_123",
            "name": "test",
        }
        result = accessor.get_payload(call)
        assert result == {}


class TestOpenAIResponsesCustomToolCallAccessorGetPayload:
    """Tests for OpenAIResponsesCustomToolCallAccessor.get_payload."""

    def test_get_payload_returns_text_input(self) -> None:
        """Input should be returned as text string."""
        accessor = OpenAIResponsesCustomToolCallAccessor()
        call = {
            "type": "custom_tool_call",
            "call_id": "call_123",
            "name": "test",
            "input": "some text content",
        }
        result = accessor.get_payload(call)
        assert result == "some text content"

    def test_get_payload_returns_empty_string_for_missing_input(self) -> None:
        """Missing input should return empty string."""
        accessor = OpenAIResponsesCustomToolCallAccessor()
        call = {
            "type": "custom_tool_call",
            "call_id": "call_123",
            "name": "test",
        }
        result = accessor.get_payload(call)
        assert result == ""