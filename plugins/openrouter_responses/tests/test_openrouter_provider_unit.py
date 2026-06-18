"""Unit tests for OpenRouter provider plugin."""

from __future__ import annotations

import pytest

from openrouter_responses_plugins.openrouter_responses_provider import (
    OpenRouterResponsesProvider,
)


def test_provider_name_and_version():
    """Provider has correct name and version."""
    provider = OpenRouterResponsesProvider()
    assert provider.name == "openrouter_responses"
    assert provider.version == "0.1.0"


def test_get_config_schema():
    """Config schema includes required fields."""
    provider = OpenRouterResponsesProvider()
    schema = provider.get_config_schema()

    assert "model" in schema
    assert schema["model"]["type"] == "string"
    assert schema["model"]["required"] is True

    assert "api_key" in schema
    assert schema["api_key"]["type"] == "string"
    assert schema["api_key"]["required"] is True

    assert "base_url" in schema
    assert schema["base_url"]["default"] == "https://openrouter.ai/api/v1"

    assert "timeout" in schema
    assert schema["timeout"]["default"] == 60

    assert "site_url" in schema
    assert "app_name" in schema


def test_get_tags():
    """Provider returns correct capability tags."""
    provider = OpenRouterResponsesProvider()
    config = {"model": "test-model", "api_key": "test-key"}
    models = [{"id": "test-model", "supported_parameters": ["tools", "reasoning"]}]

    tags = provider.get_tags(config, models)

    assert "provider:openrouter_responses" in tags
    assert "openrouter_responses" in tags
    assert "supports_streaming" in tags
    assert "supports_tools" in tags
    assert "supports_reasoning" in tags
    assert "supports_reasoning_effort" in tags


def test_get_tags_without_capability_data_returns_base_tags():
    """Provider returns only base tags when model capability data is unavailable."""
    provider = OpenRouterResponsesProvider()
    config = {"model": "test-model", "api_key": "test-key"}
    models = [{"id": "test-model"}]

    tags = provider.get_tags(config, models)

    assert tags == [
        "provider:openrouter_responses",
        "openrouter_responses",
        "supports_streaming",
    ]


def test_get_models(monkeypatch):
    """Provider returns model descriptors from the API helper."""
    provider = OpenRouterResponsesProvider()
    config = {"model": "google/gemini-2.5-flash-lite", "api_key": "test-key"}
    expected = [
        {"id": "google/gemini-2.5-flash-lite"},
        {"id": "openai/gpt-5-mini"},
    ]

    monkeypatch.setattr(provider, "_fetch_models_from_api", lambda cfg: expected)

    models = provider.get_models(config)

    assert models == expected


def test_get_models_empty_when_api_returns_no_models(monkeypatch):
    """Provider returns an empty list when the API helper returns no models."""
    provider = OpenRouterResponsesProvider()
    config = {"api_key": "test-key"}

    monkeypatch.setattr(provider, "_fetch_models_from_api", lambda cfg: [])

    models = provider.get_models(config)

    assert models == []


def test_init():
    """Init creates initial state with config."""
    provider = OpenRouterResponsesProvider()
    config = {"model": "test-model", "api_key": "test-key"}

    state = provider.init(config)

    assert "config" in state
    assert state["config"] == config


def test_initialize_request_with_required_fields():
    """Initialize request creates proper request structure."""
    provider = OpenRouterResponsesProvider()
    config = {
        "model": "openai/gpt-5-mini",
        "api_key": "sk-test-key-123",
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 30,
    }
    state = provider.init(config)
    native_messages = [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "Hello"}],
        }
    ]

    native_after, new_state = provider.initialize_request(native_messages, state)

    # Provider should not alter native history shape here.
    assert native_after == native_messages
    assert "request" in new_state
    request = new_state["request"]
    assert request["url"] == "https://openrouter.ai/api/v1/responses"
    assert request["payload"]["model"] == "openai/gpt-5-mini"
    assert request["headers"]["Authorization"] == "Bearer sk-test-key-123"
    assert request["headers"]["Content-Type"] == "application/json"
    assert request["timeout"] == 30


def test_initialize_request_with_optional_headers():
    """Initialize request includes optional OpenRouter headers."""
    provider = OpenRouterResponsesProvider()
    config = {
        "model": "test-model",
        "api_key": "test-key",
        "site_url": "https://example.com",
        "app_name": "Test App",
    }
    state = provider.init(config)

    native_after, new_state = provider.initialize_request([], state)

    headers = new_state["request"]["headers"]
    assert headers["HTTP-Referer"] == "https://example.com"
    assert headers["X-Title"] == "Test App"


def test_initialize_request_raises_without_api_key():
    """Initialize request raises ValueError when api_key is missing."""
    provider = OpenRouterResponsesProvider()
    config = {"model": "test-model"}
    state = provider.init(config)

    with pytest.raises(ValueError) as exc:
        provider.initialize_request([], state)

    assert "api_key is required" in str(exc.value)


def test_to_native_messages():
    """Convert core messages to provider-native format."""
    provider = OpenRouterResponsesProvider()
    messages = [
        {"role": "system", "content": "You are helpful.", "metadata": {}},
        {"role": "user", "content": "Hello", "metadata": {}},
        {"role": "assistant", "content": "Hi there", "metadata": {}},
    ]
    state = {}

    native = provider.to_native_messages(messages, state)

    assert len(native) == 3
    assert native[0] == {
        "type": "message",
        "role": "system",
        "content": [{"type": "input_text", "text": "You are helpful."}],
    }
    assert native[1] == {
        "type": "message",
        "role": "user",
        "content": [{"type": "input_text", "text": "Hello"}],
    }
    assert native[2] == {
        "type": "message",
        "role": "assistant",
        "content": [{"type": "input_text", "text": "Hi there"}],
    }


def test_from_native_messages():
    """Convert provider-native messages to core format."""
    provider = OpenRouterResponsesProvider()
    native_messages = [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "Test"}],
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "Response"}],
        },
    ]
    state = {}

    messages = provider.from_native_messages(native_messages, state)

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Test"
    assert messages[0]["metadata"].get("native_indices") == [0]
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Response"


def test_from_native_messages_ignores_reasoning_field():
    """Base provider conversion ignores reasoning; extensions handle it."""
    provider = OpenRouterResponsesProvider()
    native_messages = [
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "Answer"}],
        },
        {
            "type": "reasoning",
            "summary": [{"type": "summary_text", "text": "Thought process"}],
        },
    ]
    state = {}

    messages = provider.from_native_messages(native_messages, state)

    assert len(messages) == 1
    assert messages[0]["role"] == "assistant"
    assert messages[0]["content"] == "Answer"
    # Base provider should not surface reasoning directly
    assert "reasoning" not in messages[0]


def test_from_native_messages_aggregates_function_calls_to_last_assistant_message() -> (
    None
):
    provider = OpenRouterResponsesProvider()
    native_messages = [
        {
            "type": "function_call",
            "call_id": "call_1",
            "name": "add",
            "arguments": '{"a":1}',
            "_metadata": {"response_id": "resp_1"},
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "OK"}],
            "_metadata": {"response_id": "resp_1"},
        },
    ]
    out = provider.from_native_messages(native_messages, {})
    assert len(out) == 1
    assert out[0]["role"] == "assistant"
    assert out[0]["content"] == "OK"
    md = out[0].get("metadata") or {}
    tcs = md.get("tool_calls") or []
    assert isinstance(tcs, list) and tcs
    assert md.get("native_indices") == [0, 1]


def test_from_native_messages_assigns_segment_native_indices_to_final_answer_assistant() -> (
    None
):
    provider = OpenRouterResponsesProvider()
    native_messages = [
        {
            "type": "reasoning",
            "summary": [{"type": "summary_text", "text": "r"}],
            "_metadata": {"response_id": "resp_1"},
        },
        {
            "type": "message",
            "role": "assistant",
            "phase": "commentary",
            "content": [{"type": "output_text", "text": "thinking"}],
            "_metadata": {"response_id": "resp_1"},
        },
        {
            "type": "message",
            "role": "assistant",
            "phase": "final_answer",
            "content": [{"type": "output_text", "text": "answer"}],
            "_metadata": {"response_id": "resp_1"},
        },
    ]

    out = provider.from_native_messages(native_messages, {})

    assistants = [m for m in out if m.get("role") == "assistant"]
    assert len(assistants) == 1
    final = assistants[0]
    assert final.get("content") == "answer"
    md = final.get("metadata") or {}
    assert md.get("phase") == "final_answer"
    assert md.get("native_indices") == [0, 1, 2]
    phase_messages = md.get("phase_messages") or []
    assert [entry.get("phase") for entry in phase_messages] == [
        "commentary",
        "final_answer",
    ]
    assert [entry.get("content") for entry in phase_messages] == ["thinking", "answer"]


def test_from_native_messages_assigns_segment_native_indices_to_tool_call_assistant() -> (
    None
):
    provider = OpenRouterResponsesProvider()
    native_messages = [
        {
            "type": "reasoning",
            "summary": [{"type": "summary_text", "text": "r"}],
            "_metadata": {"response_id": "resp_1"},
        },
        {
            "type": "message",
            "role": "assistant",
            "phase": "commentary",
            "content": [{"type": "output_text", "text": "thinking"}],
            "_metadata": {"response_id": "resp_1"},
        },
        {
            "type": "function_call",
            "call_id": "call_1",
            "name": "add",
            "arguments": '{"a":1}',
            "_metadata": {"response_id": "resp_1"},
        },
    ]

    out = provider.from_native_messages(native_messages, {})

    tool_call_assistant = next(
        (
            m
            for m in out
            if m.get("role") == "assistant"
            and isinstance((m.get("metadata") or {}).get("tool_calls"), list)
            and (m.get("metadata") or {}).get("tool_calls")
        ),
        None,
    )
    assert isinstance(tool_call_assistant, dict)
    md = tool_call_assistant.get("metadata") or {}
    assert md.get("native_indices") == [0, 1, 2]


def test_validate_message_list_valid():
    """Validate message list accepts valid messages."""
    provider = OpenRouterResponsesProvider()
    messages = [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "Hello"}],
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "Hi"}],
        },
    ]

    provider._validate_message_list(messages)


def test_validate_message_list_invalid_type():
    """Validate message list raises on non-dict items."""
    provider = OpenRouterResponsesProvider()
    messages = [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "Hello"}],
        },
        "invalid",
    ]

    with pytest.raises(RuntimeError) as exc:
        provider._validate_message_list(messages)

    assert "invalid item at index 1" in str(exc.value)
    assert "expected dict" in str(exc.value)


def test_validate_message_list_missing_fields():
    """Validate message list raises when an item has no type."""
    provider = OpenRouterResponsesProvider()
    messages = [
        {"role": "user", "content": "hi"},
    ]

    with pytest.raises(RuntimeError) as exc:
        provider._validate_message_list(messages)

    assert "invalid item at index 0" in str(exc.value)
    assert "missing 'type'" in str(exc.value)


def test_finalize_with_accumulated_content():
    """Finalize is a no-op for `/responses` streaming."""
    provider = OpenRouterResponsesProvider()
    native_messages = [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "Hi"}],
        }
    ]
    state = {"accumulator": {"role": "assistant", "content": "Response"}}

    finals, new_natives, new_state = provider.finalize(native_messages, state)

    assert finals == []
    assert new_natives == native_messages


def test_finalize_without_partial():
    """Finalize returns empty when no partial accumulated."""
    provider = OpenRouterResponsesProvider()
    native_messages = [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "Hi"}],
        }
    ]
    state = {"accumulator": None}

    finals, new_natives, new_state = provider.finalize(native_messages, state)

    assert finals == []
    assert new_natives == native_messages
