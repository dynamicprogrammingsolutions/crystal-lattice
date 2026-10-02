from __future__ import annotations

from typing import Any, Dict

from openai_responses_plugins.openai_responses_fast_mode_extension import (
    OpenAIResponsesFastModeExtension,
)


def _config(**overrides: Any) -> Dict[str, Any]:
    return {
        "model": "gpt-5.5",
        "auth_mode": "chatgpt",
        "_openai_responses_effective_auth_mode": "chatgpt",
        "timeout": 30,
        **overrides,
    }


def _fast_mode_state(config: Dict[str, Any]) -> Dict[str, Any]:
    ext = OpenAIResponsesFastModeExtension()
    return ext.init(
        config,
        {
            "config": config,
            "request": {"payload": {"model": "gpt-5.5"}, "headers": {}},
        },
    )


def test_extension_name_tags_schema_and_required_tags() -> None:
    ext = OpenAIResponsesFastModeExtension()

    assert ext.name == "openai_responses_fast_mode"
    assert ext.version == "0.1.0"
    assert ext.get_tags({}, []) == ["ext:openai_responses_fast_mode"]
    assert ext.required_tags() == ["openai_responses"]

    schema = ext.get_config_schema()
    assert set(schema) == {"enable_fast_mode"}
    assert schema["enable_fast_mode"]["default"] is False
    assert "API-key and ChatGPT auth modes" in schema["enable_fast_mode"]["description"]
    assert 'service_tier: "fast"' in schema["enable_fast_mode"]["description"]


def test_get_ui_elements_exposes_fast_mode_toggle() -> None:
    ext = OpenAIResponsesFastModeExtension()

    elements = ext.get_ui_elements(
        config={},
        tags=["openai_responses", "ext:openai_responses_fast_mode"],
        models=[{"id": "gpt-5.5"}],
    )

    assert elements == [
        {
            "type": "checkbox",
            "key": "enable_fast_mode",
            "label": "Enable Fast mode",
            "description": (
                "Applies the fast processing tier "
                '(``service_tier: "fast"``, or the legacy ``"priority"`` '
                "name required by the ChatGPT backend) to Responses calls "
                "for both API-key and ChatGPT auth modes."
            ),
        }
    ]


def test_get_ui_elements_hides_fast_mode_for_chatgpt_or_explicitly_disabled_ui() -> None:
    ext = OpenAIResponsesFastModeExtension()

    assert ext.get_ui_elements(config={"auth_mode": "chatgpt"}) == []
    assert ext.get_ui_elements(
        config={"auth_mode": "api", "show_fast_mode_ui": False}
    ) == []


def test_init_and_initialize_request_are_noops_when_fast_mode_disabled() -> None:
    ext = OpenAIResponsesFastModeExtension()
    state = {
        "config": _config(),
        "request": {"payload": {"model": "gpt-5.5"}},
    }

    initialized_state = ext.init(_config(), state)
    returned_native, new_state = ext.initialize_request([], initialized_state)

    assert initialized_state is state
    assert returned_native == []
    assert new_state is state


def test_initialize_request_injects_priority_for_chatgpt_auth() -> None:
    """The ChatGPT backend only accepts the legacy ``priority`` tier name;
    sending ``fast`` fails with a 400 ``Unsupported service_tier``."""
    ext = OpenAIResponsesFastModeExtension()
    state = _fast_mode_state(_config(enable_fast_mode=True))

    returned_native, new_state = ext.initialize_request(
        [{"type": "message", "role": "user"}],
        state,
    )

    assert returned_native == [{"type": "message", "role": "user"}]
    assert new_state["request"]["payload"]["service_tier"] == "priority"


def test_initialize_request_injects_fast_for_api_auth() -> None:
    """The official API accepts the current ``fast`` tier name."""
    ext = OpenAIResponsesFastModeExtension()
    state = _fast_mode_state(
        _config(
            auth_mode="api_key",
            _openai_responses_effective_auth_mode="api",
            enable_fast_mode=True,
        )
    )

    returned_native, new_state = ext.initialize_request(
        [{"type": "message", "role": "user"}],
        state,
    )

    assert returned_native == [{"type": "message", "role": "user"}]
    assert new_state["request"]["payload"]["service_tier"] == "fast"


def test_initialize_request_injects_fast_for_auto_resolving_to_api() -> None:
    ext = OpenAIResponsesFastModeExtension()
    state = _fast_mode_state(
        _config(
            auth_mode="auto",
            _openai_responses_effective_auth_mode="api",
            enable_fast_mode=True,
        )
    )

    returned_native, new_state = ext.initialize_request(
        [{"type": "message", "role": "user"}],
        state,
    )

    assert returned_native == [{"type": "message", "role": "user"}]
    assert new_state["request"]["payload"]["service_tier"] == "fast"


def test_initialize_request_injects_priority_for_auto_resolving_to_chatgpt() -> None:
    ext = OpenAIResponsesFastModeExtension()
    state = _fast_mode_state(
        _config(
            auth_mode="auto",
            _openai_responses_effective_auth_mode="chatgpt",
            enable_fast_mode=True,
        )
    )

    returned_native, new_state = ext.initialize_request(
        [{"type": "message", "role": "user"}],
        state,
    )

    assert returned_native == [{"type": "message", "role": "user"}]
    assert new_state["request"]["payload"]["service_tier"] == "priority"


def test_initialize_request_uses_requested_auth_mode_without_effective_key() -> None:
    """When the effective-auth-mode key is absent (for example when the auth
    feature has not run), the requested ``auth_mode`` alone decides the wire
    tier name."""
    ext = OpenAIResponsesFastModeExtension()

    chatgpt_state = _fast_mode_state(
        {
            "model": "gpt-5.5",
            "auth_mode": "chatgpt",
            "timeout": 30,
            "enable_fast_mode": True,
        }
    )
    _native, chatgpt_new_state = ext.initialize_request([], chatgpt_state)
    assert chatgpt_new_state["request"]["payload"]["service_tier"] == "priority"

    api_state = _fast_mode_state(
        {
            "model": "gpt-5.5",
            "auth_mode": "api_key",
            "timeout": 30,
            "enable_fast_mode": True,
        }
    )
    _native, api_new_state = ext.initialize_request([], api_state)
    assert api_new_state["request"]["payload"]["service_tier"] == "fast"


def test_from_native_messages_surfaces_fast_service_tier_metadata() -> None:
    ext = OpenAIResponsesFastModeExtension()

    messages = [
        {
            "role": "assistant",
            "content": "hello",
            "metadata": {"native_indices": [1]},
        }
    ]
    native_messages = [
        {"type": "message", "role": "user"},
        {
            "type": "message",
            "role": "assistant",
            "_metadata": {
                "response_id": "resp_1",
                "_openai_responses_service_tier": "fast",
            },
        },
    ]

    surfaced = ext.from_native_messages(native_messages, messages)

    assert surfaced[0]["metadata"]["openai_service_tier"] == "fast"
    assert surfaced[0]["metadata"]["fast_mode_applied"] is True


def test_from_native_messages_accepts_obsolete_priority_report() -> None:
    ext = OpenAIResponsesFastModeExtension()

    messages = [
        {
            "role": "assistant",
            "content": "hello",
            "metadata": {"native_indices": [1]},
        }
    ]
    native_messages = [
        {"type": "message", "role": "user"},
        {
            "type": "message",
            "role": "assistant",
            "_metadata": {
                "response_id": "resp_1",
                # The official API still reports the legacy ``priority``
                # name even when the request sent ``fast``.
                "_openai_responses_service_tier": "priority",
            },
        },
    ]

    surfaced = ext.from_native_messages(native_messages, messages)

    assert surfaced[0]["metadata"]["openai_service_tier"] == "priority"
    assert surfaced[0]["metadata"]["fast_mode_applied"] is True
