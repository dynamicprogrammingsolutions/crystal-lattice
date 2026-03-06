"""Unit tests for OpenRouter provider plugin."""

from __future__ import annotations

import pytest

from openrouter_plugins.openrouter_provider import OpenRouterProvider


def test_provider_name_and_version():
    """Provider has correct name and version."""
    provider = OpenRouterProvider()
    assert provider.name == "openrouter"
    assert provider.version == "0.1.0"


def test_get_config_schema():
    """Config schema includes required fields."""
    provider = OpenRouterProvider()
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
    provider = OpenRouterProvider()
    config = {"model": "test-model", "api_key": "test-key"}
    models = [{"id": "test-model", "supported_parameters": ["tools", "reasoning"]}]

    tags = provider.get_tags(config, models)

    assert "provider:openrouter" in tags
    assert "openrouter" in tags
    assert "supports_streaming" in tags
    assert "supports_tools" in tags
    assert "supports_reasoning" in tags
    assert "supports_reasoning_effort" in tags


def test_get_tags_without_capability_data_returns_base_tags():
    """Provider returns only base tags when model capability data is unavailable."""
    provider = OpenRouterProvider()
    config = {"model": "test-model", "api_key": "test-key"}
    models = [{"id": "test-model"}]

    tags = provider.get_tags(config, models)

    assert tags == ["provider:openrouter", "openrouter", "supports_streaming"]


def test_get_models(monkeypatch):
    """Provider returns model descriptors from the API helper."""
    provider = OpenRouterProvider()
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
    provider = OpenRouterProvider()
    config = {"api_key": "test-key"}

    monkeypatch.setattr(provider, "_fetch_models_from_api", lambda cfg: [])

    models = provider.get_models(config)

    assert models == []


def test_init():
    """Init creates initial state with config."""
    provider = OpenRouterProvider()
    config = {"model": "test-model", "api_key": "test-key"}

    state = provider.init(config)

    assert "config" in state
    assert state["config"] == config


def test_initialize_request_with_required_fields():
    """Initialize request creates proper request structure."""
    provider = OpenRouterProvider()
    config = {
        "model": "openai/gpt-5-mini",
        "api_key": "sk-test-key-123",
        "base_url": "https://openrouter.ai/api/v1",
        "timeout": 30,
    }
    state = provider.init(config)
    native_messages = [{"role": "user", "content": "Hello"}]

    native_after, new_state = provider.initialize_request(native_messages, state)

    # Provider should not alter native history shape here.
    assert native_after == native_messages
    assert "request" in new_state
    request = new_state["request"]
    assert request["url"] == "https://openrouter.ai/api/v1/chat/completions"
    assert request["payload"]["model"] == "openai/gpt-5-mini"
    assert request["headers"]["Authorization"] == "Bearer sk-test-key-123"
    assert request["headers"]["Content-Type"] == "application/json"
    assert request["timeout"] == 30
    assert new_state["partial"] is None


def test_initialize_request_with_optional_headers():
    """Initialize request includes optional OpenRouter headers."""
    provider = OpenRouterProvider()
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
    provider = OpenRouterProvider()
    config = {"model": "test-model"}
    state = provider.init(config)

    with pytest.raises(ValueError) as exc:
        provider.initialize_request([], state)

    assert "api_key is required" in str(exc.value)


def test_to_native_messages():
    """Convert core messages to provider-native format."""
    provider = OpenRouterProvider()
    messages = [
        {"role": "system", "content": "You are helpful.", "metadata": {}},
        {"role": "user", "content": "Hello", "metadata": {}},
        {"role": "assistant", "content": "Hi there", "metadata": {}},
    ]
    state = {}

    native = provider.to_native_messages(messages, state)

    assert len(native) == 3
    assert native[0] == {"role": "system", "content": "You are helpful."}
    assert native[1] == {"role": "user", "content": "Hello"}
    assert native[2] == {"role": "assistant", "content": "Hi there"}


def test_from_native_messages():
    """Convert provider-native messages to core format."""
    provider = OpenRouterProvider()
    native_messages = [
        {"role": "user", "content": "Test"},
        {"role": "assistant", "content": "Response"},
    ]
    state = {}

    messages = provider.from_native_messages(native_messages, state)

    assert len(messages) == 2
    assert messages[0]["role"] == "user"
    assert messages[0]["content"] == "Test"
    assert messages[0]["metadata"] == {}
    assert messages[1]["role"] == "assistant"
    assert messages[1]["content"] == "Response"


def test_from_native_messages_ignores_reasoning_field():
    """Base provider conversion ignores reasoning; extensions handle it."""
    provider = OpenRouterProvider()
    native_messages = [
        {"role": "assistant", "content": "Answer", "reasoning": "Thought process"},
    ]
    state = {}

    messages = provider.from_native_messages(native_messages, state)

    assert len(messages) == 1
    assert messages[0]["role"] == "assistant"
    assert messages[0]["content"] == "Answer"
    # Base provider should not surface reasoning directly
    assert "reasoning" not in messages[0]


def test_validate_message_list_valid():
    """Validate message list accepts valid messages."""
    provider = OpenRouterProvider()
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi"},
    ]

    provider._validate_message_list(messages)


def test_validate_message_list_invalid_type():
    """Validate message list raises on non-dict items."""
    provider = OpenRouterProvider()
    messages = [
        {"role": "user", "content": "Hello"},
        "invalid",
    ]

    with pytest.raises(RuntimeError) as exc:
        provider._validate_message_list(messages)

    assert "invalid message at index 1" in str(exc.value)
    assert "expected dict" in str(exc.value)


def test_validate_message_list_missing_fields():
    """Validate message list raises on missing required fields."""
    provider = OpenRouterProvider()
    messages = [
        {"role": "user"},
    ]

    with pytest.raises(RuntimeError) as exc:
        provider._validate_message_list(messages)

    assert "invalid message at index 0" in str(exc.value)
    assert "missing 'role' or 'content'" in str(exc.value)


def test_extract_delta():
    """Extract delta from streaming chunk."""
    provider = OpenRouterProvider()
    chunk = {"choices": [{"delta": {"role": "assistant", "content": "Hello"}}]}

    delta = provider.extract_delta(chunk)

    assert delta == {"delta": {"role": "assistant", "content": "Hello"}}


def test_extract_delta_empty_chunk():
    """Extract delta returns empty dict for chunk without choices."""
    provider = OpenRouterProvider()
    chunk = {}

    delta = provider.extract_delta(chunk)

    assert delta == {}


def test_process_delta_content_accumulation():
    """Process delta accumulates content fragments."""
    provider = OpenRouterProvider()
    delta = {"delta": {"role": "assistant", "content": "Hello"}}
    accumulated = {}

    partial, new_accumulated = provider.process_delta(delta, accumulated)

    assert partial == {"role": "assistant", "content": "Hello"}
    assert new_accumulated["content"] == "Hello"
    assert new_accumulated["role"] == "assistant"

def test_finalize_with_accumulated_content():
    """Finalize emits accumulated partial as final."""
    provider = OpenRouterProvider()
    native_messages = [{"role": "user", "content": "Hi"}]
    state = {"partial": {"role": "assistant", "content": "Response"}}

    finals, new_natives, new_state = provider.finalize(native_messages, state)

    assert len(finals) == 1
    assert finals[0] == {"role": "assistant", "content": "Response"}
    assert len(new_natives) == 2
    assert new_natives[-1] == {"role": "assistant", "content": "Response"}


def test_finalize_without_partial():
    """Finalize returns empty when no partial accumulated."""
    provider = OpenRouterProvider()
    native_messages = [{"role": "user", "content": "Hi"}]
    state = {"partial": None}

    finals, new_natives, new_state = provider.finalize(native_messages, state)

    assert finals == []
    assert new_natives == native_messages


def test_to_display_format():
    """Display format returns message unchanged."""
    provider = OpenRouterProvider()
    message = {"role": "assistant", "content": "Hello"}
    state = {}

    display = provider.to_display_format(message, state)

    assert display == message
