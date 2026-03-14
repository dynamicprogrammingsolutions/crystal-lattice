from __future__ import annotations

from typing import Any, Dict

from openai_responses_plugins.openai_responses_flex_processing_extension import (
    OpenAIResponsesFlexProcessingExtension,
)


def _config(**overrides: Any) -> Dict[str, Any]:
    return {
        "model": "gpt-5-mini",
        "api_key": "test_key",
        "base_url": "https://api.openai.com/v1",
        "timeout": 30,
        **overrides,
    }


def test_extension_name_tags_schema_and_required_tags() -> None:
    ext = OpenAIResponsesFlexProcessingExtension()

    assert ext.name == "openai_responses_flex_processing"
    assert ext.version == "0.1.0"
    assert ext.get_tags({}, []) == ["ext:openai_responses_flex_processing"]
    assert ext.required_tags() == ["openai_responses"]

    schema = ext.get_config_schema()
    assert set(schema) == {
        "enable_flex_processing",
        "flex_timeout_seconds",
        "enable_flex_retries",
        "flex_max_retries",
    }
    assert schema["enable_flex_processing"]["default"] is False
    assert schema["flex_timeout_seconds"]["default"] == 300.0
    assert schema["enable_flex_retries"]["default"] is True
    assert schema["flex_max_retries"]["default"] == 2


def test_get_ui_elements_exposes_all_flex_controls() -> None:
    ext = OpenAIResponsesFlexProcessingExtension()

    elements = ext.get_ui_elements(
        config={},
        tags=["openai_responses", "ext:openai_responses_flex_processing"],
        models=[{"id": "gpt-5-mini"}],
    )

    assert [element["key"] for element in elements] == [
        "enable_flex_processing",
        "flex_timeout_seconds",
        "enable_flex_retries",
        "flex_max_retries",
    ]


def test_init_and_initialize_request_are_noops_when_flex_disabled() -> None:
    ext = OpenAIResponsesFlexProcessingExtension()
    state = {"config": _config(), "request": {"payload": {"model": "gpt-5-mini"}}}

    initialized_state = ext.init(_config(), state)
    returned_native, new_state = ext.initialize_request([], initialized_state)

    assert initialized_state is state
    assert returned_native == []
    assert new_state is state


def test_init_normalizes_invalid_timeout_and_retry_values_to_defaults() -> None:
    ext = OpenAIResponsesFlexProcessingExtension()
    state = {"request": {"payload": {"model": "gpt-5-mini"}}}

    new_state = ext.init(
        _config(
            enable_flex_processing=True,
            flex_timeout_seconds="bad",
            enable_flex_retries=True,
            flex_max_retries=-4,
        ),
        state,
    )

    assert new_state["openai_responses_flex_processing"] == {
        "timeout": 300.0,
        "max_retries": 2,
    }


def test_initialize_request_injects_service_tier_timeout_and_retry_overrides() -> None:
    ext = OpenAIResponsesFlexProcessingExtension()
    state = ext.init(
        _config(
            enable_flex_processing=True,
            flex_timeout_seconds=450,
            enable_flex_retries=True,
            flex_max_retries=4,
        ),
        {"request": {"payload": {"model": "gpt-5-mini"}, "headers": {}}},
    )

    returned_native, new_state = ext.initialize_request(
        [{"type": "message", "role": "user"}],
        state,
    )

    assert returned_native == [{"type": "message", "role": "user"}]
    assert new_state["request"]["payload"]["service_tier"] == "flex"
    assert new_state["request"]["timeout"] == 450.0
    assert new_state["request"]["max_retries"] == 4


def test_initialize_request_omits_retry_override_when_flex_retries_disabled() -> None:
    ext = OpenAIResponsesFlexProcessingExtension()
    state = ext.init(
        _config(
            enable_flex_processing=True,
            flex_timeout_seconds=240,
            enable_flex_retries=False,
            flex_max_retries=9,
        ),
        {
            "request": {
                "payload": {"model": "gpt-5-mini"},
                "headers": {},
                "max_retries": 99,
            }
        },
    )

    _returned_native, new_state = ext.initialize_request([], state)

    assert new_state["request"]["payload"]["service_tier"] == "flex"
    assert new_state["request"]["timeout"] == 240.0
    assert "max_retries" not in new_state["request"]

def test_from_native_messages_surfaces_service_tier_metadata() -> None:
    ext = OpenAIResponsesFlexProcessingExtension()

    messages = [
        {
            "role": "assistant",
            "content": "hello",
            "metadata": {"native_indices": [1, 2]},
        }
    ]
    native_messages = [
        {"type": "message", "role": "user"},
        {"type": "reasoning", "_metadata": {"response_id": "resp_1"}},
        {
            "type": "message",
            "role": "assistant",
            "_metadata": {
                "response_id": "resp_1",
                "_openai_responses_service_tier": "flex",
            },
        },
    ]

    surfaced = ext.from_native_messages(native_messages, messages)

    assert surfaced[0]["metadata"]["openai_service_tier"] == "flex"
    assert surfaced[0]["metadata"]["flex_processing_applied"] is True


def test_from_native_messages_preserves_messages_without_service_tier() -> None:
    ext = OpenAIResponsesFlexProcessingExtension()

    messages = [{"role": "assistant", "content": "hello", "metadata": {"native_indices": [0]}}]
    native_messages = [{"type": "message", "role": "assistant", "_metadata": {"response_id": "resp_1"}}]

    surfaced = ext.from_native_messages(native_messages, messages)

    assert surfaced == messages
