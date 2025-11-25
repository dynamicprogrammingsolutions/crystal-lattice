"""Tests for RequestOptionsFeature (request options feature plugin)."""

from agent_core import AgentCore
from plugins.openai_provider import OpenAICompatibleProvider
from plugins.request_options_feature import RequestOptionsFeature


def _build_core_with_openai_and_request_options():
    core = AgentCore()
    core.register_provider(OpenAICompatibleProvider)
    core.register_feature(RequestOptionsFeature)
    return core


def test_request_options_merged_into_openai_request_payload():
    core = _build_core_with_openai_and_request_options()

    # Minimal session with a single user message
    session = core.create_session()
    session = core.add_message(session, "user", "hello")

    config = {
        "model": "test-model",
        "base_url": "https://api.openai.com/v1",
        # Feature-specific config: arbitrary request options
        "request_options": {"temperature": 0.3, "max_tokens": 256},
    }

    # Run only the pre-request path by calling the private helper
    provider, exts, features, tools, _tags = core._resolve_plugins_for_config(config)  # type: ignore[attr-defined]
    provider.set_active_extensions(exts)
    messages, _native_messages, state = core._pre_request(
        session,
        config,
        provider,
        features,
        tools,
    )  # type: ignore[attr-defined]
    # Sanity check core messages flow
    assert messages[-1]["content"] == "hello"

    # The provider state should now contain request payload with merged options
    request = state.get("request") or {}
    payload = request.get("payload") or {}

    assert payload["model"] == "test-model"
    assert payload["temperature"] == 0.3
    assert payload["max_tokens"] == 256


def test_request_options_can_override_existing_payload_keys():
    core = _build_core_with_openai_and_request_options()

    session = core.create_session()
    session = core.add_message(session, "user", "hi")

    # Provider sets model in payload; feature overrides it via request_options
    config = {
        "model": "original-model",
        "base_url": "https://api.openai.com/v1",
        "request_options": {"model": "override-model"},
    }

    provider, exts, features, tools, _tags = core._resolve_plugins_for_config(config)  # type: ignore[attr-defined]
    provider.set_active_extensions(exts)
    _messages, _native_messages, state = core._pre_request(
        session,
        config,
        provider,
        features,
        tools,
    )  # type: ignore[attr-defined]

    request = state.get("request") or {}
    payload = request.get("payload") or {}

    assert payload["model"] == "override-model"


def test_request_options_noop_when_not_dict_or_empty():
    core = _build_core_with_openai_and_request_options()

    session = core.create_session()
    session = core.add_message(session, "user", "hello")

    # request_options is not a dict -> ignored
    config = {
        "model": "test-model",
        "base_url": "https://api.openai.com/v1",
        "request_options": None,
    }

    provider, exts, features, tools, _tags = core._resolve_plugins_for_config(config)  # type: ignore[attr-defined]
    provider.set_active_extensions(exts)
    _messages, _native_messages, state = core._pre_request(
        session,
        config,
        provider,
        features,
        tools,
    )  # type: ignore[attr-defined]

    request = state.get("request") or {}
    payload = request.get("payload") or {}

    # Only provider-supplied keys should be present
    assert payload == {"model": "test-model"}
