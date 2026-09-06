from __future__ import annotations

from typing import Any

from plugins.request_options_feature import RequestOptionsFeature

from anthropic_plugins import (
    AnthropicPromptCachingExtension,
    AnthropicProvider,
)


def _state(config: dict[str, Any]) -> dict[str, Any]:
    return {
        "config": config,
        "request": {"payload": {"model": "m", "messages": []}},
    }


def test_provider_prompt_caching_capability_tag_is_explicit() -> None:
    provider = AnthropicProvider()

    assert "supports_prompt_caching" not in provider.get_tags({}, [])
    assert "supports_prompt_caching" not in provider.get_tags(
        {"capabilities": {"prompt_caching": False}},
        [],
    )
    assert "supports_prompt_caching" in provider.get_tags(
        {"capabilities": {"prompt_caching": True}},
        [],
    )


def test_provider_reasoning_controls_tag_detects_or_obeys_explicit_capability() -> None:
    provider = AnthropicProvider()
    models = [
        {
            "id": "claude-sonnet-5",
            "anthropic_reasoning_controls": {"thinking_types": ["adaptive"]},
        }
    ]

    assert "supports_anthropic_reasoning_controls" in provider.get_tags(
        {"model": "claude-sonnet-5"},
        models,
    )
    assert "supports_anthropic_reasoning_controls" not in provider.get_tags(
        {
            "model": "claude-sonnet-5",
            "capabilities": {"anthropic_reasoning_controls": False},
        },
        models,
    )
    assert "supports_anthropic_reasoning_controls" in provider.get_tags(
        {
            "model": "custom-model",
            "capabilities": {"anthropic_reasoning_controls": True},
        },
        [],
    )


def test_prompt_caching_schema_and_ui() -> None:
    extension = AnthropicPromptCachingExtension()

    schema = extension.get_config_schema()
    elements = {element["key"]: element for element in extension.get_ui_elements({})}

    assert schema["enable_prompt_caching"]["default"] is True
    assert schema["prompt_cache_ttl"]["enum"] == ["5m", "1h"]
    assert elements["enable_prompt_caching"]["type"] == "checkbox"
    assert [item["value"] for item in elements["prompt_cache_ttl"]["options"]] == [
        "5m",
        "1h",
    ]


def test_prompt_caching_adds_default_and_one_hour_cache_control() -> None:
    extension = AnthropicPromptCachingExtension()

    _messages, default_state = extension.initialize_request([], _state({}))
    _messages, one_hour_state = extension.initialize_request(
        [],
        _state({"prompt_cache_ttl": "1h"}),
    )

    assert default_state["request"]["payload"]["cache_control"] == {
        "type": "ephemeral",
        "ttl": "5m",
    }
    assert one_hour_state["request"]["payload"]["cache_control"] == {
        "type": "ephemeral",
        "ttl": "1h",
    }


def test_prompt_caching_disabled_adds_nothing() -> None:
    extension = AnthropicPromptCachingExtension()
    original = _state({"enable_prompt_caching": False})

    _messages, state = extension.initialize_request([], original)

    assert state is original
    assert "cache_control" not in state["request"]["payload"]


def test_raw_request_options_override_automatic_cache_control() -> None:
    extension = AnthropicPromptCachingExtension()
    feature = RequestOptionsFeature()
    config = {
        "prompt_cache_ttl": "5m",
        "request_options": {"cache_control": {"type": "ephemeral", "ttl": "1h"}},
    }
    state = _state(config)

    _messages, state = extension.initialize_request([], state)
    state = feature.init(config, state)
    _messages, state = feature.initialize_request([], state)

    assert state["request"]["payload"]["cache_control"] == {
        "type": "ephemeral",
        "ttl": "1h",
    }
