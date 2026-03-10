from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider


FIXTURE_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "openai_responses_gpt5mini_nonstreaming.json"
)


class _FixtureResponse:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def model_dump(self, mode: str = "python") -> Dict[str, Any]:
        _ = mode
        return self._payload


class _FixtureResponsesResource:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload
        self.calls: list[Dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _FixtureResponse:
        self.calls.append(kwargs)
        return _FixtureResponse(self._payload)


class _FixtureClient:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self.responses = _FixtureResponsesResource(payload)


class _ErrorResponsesResource:
    def create(self, **kwargs: Any) -> Any:
        _ = kwargs
        raise RuntimeError("boom")


class _ErrorClient:
    responses = _ErrorResponsesResource()


def _load_fixture() -> Dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def test_provider_metadata_schema_and_tags() -> None:
    provider = OpenAIResponsesProvider()

    assert provider.name == "openai_responses"
    assert provider.version == "0.1.0"

    schema = provider.get_config_schema()
    assert "model" in schema
    assert "api_key" in schema
    assert "base_url" in schema
    assert "timeout" in schema

    tags = provider.get_tags({"model": "gpt-5-mini"}, [{"id": "gpt-5-mini"}])
    assert tags == [
        "provider:openai_responses",
        "openai_responses",
        "supports_streaming",
    ]


def test_init_uses_env_api_key_when_not_in_config(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "test_env_key")
    provider = OpenAIResponsesProvider()

    state = provider.init({"model": "gpt-5-mini"})

    cfg = state["config"]
    assert cfg["model"] == "gpt-5-mini"
    assert cfg["api_key"] == "test_env_key"
    assert cfg["base_url"] == "https://api.openai.com/v1"
    assert cfg["timeout"] == 60.0
    assert state.get("client") is not None


def test_init_raises_for_invalid_config(monkeypatch: pytest.MonkeyPatch) -> None:
    provider = OpenAIResponsesProvider()

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(ValueError, match="api_key is required"):
        provider.init({"model": "gpt-5-mini"})

    with pytest.raises(ValueError, match="model is required"):
        provider.init({"api_key": "x"})

    with pytest.raises(ValueError, match="timeout"):
        provider.init({"model": "gpt-5-mini", "api_key": "x", "timeout": 0})


def test_initialize_request_builds_request_state() -> None:
    provider = OpenAIResponsesProvider()
    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 42,
        }
    }

    native_after, new_state = provider.initialize_request([], state)

    assert native_after == []
    req = new_state["request"]
    assert req["url"] == "https://api.openai.com/v1/responses"
    assert req["payload"] == {"model": "gpt-5-mini"}
    assert req["headers"]["Authorization"] == "Bearer test_key"
    assert req["headers"]["Content-Type"] == "application/json"
    assert req["timeout"] == 42.0


def test_to_native_and_from_native_roundtrip_with_tool_output() -> None:
    provider = OpenAIResponsesProvider()

    core_messages = [
        {
            "role": "user",
            "content": "hello",
            "metadata": {"trace_id": "u1", "native_indices": [999]},
        },
        {
            "role": "assistant",
            "content": "working",
            "metadata": {"phase": "commentary", "trace_id": "a1"},
        },
        {
            "role": "tool",
            "content": "{\"ok\": true}",
            "metadata": {"tool_call_id": "call_123", "trace_id": "t1"},
        },
    ]

    native = provider.to_native_messages(core_messages, {})
    assert native[0]["type"] == "message"
    assert native[0]["role"] == "user"
    assert native[0]["content"] == [{"type": "input_text", "text": "hello"}]
    assert native[0]["_metadata"] == {"trace_id": "u1"}

    assert native[1]["type"] == "message"
    assert native[1]["role"] == "assistant"
    assert native[1]["phase"] == "commentary"

    assert native[2]["type"] == "function_call_output"
    assert native[2]["call_id"] == "call_123"
    assert native[2]["output"] == "{\"ok\": true}"
    assert native[2]["_metadata"] == {"trace_id": "t1"}

    rebuilt = provider.from_native_messages(native, {})
    assert rebuilt[0]["role"] == "user"
    assert rebuilt[0]["content"] == "hello"
    assert rebuilt[0]["metadata"]["trace_id"] == "u1"
    assert rebuilt[0]["metadata"]["native_indices"] == [0]

    assert rebuilt[1]["role"] == "assistant"
    assert rebuilt[1]["content"] == "working"
    assert rebuilt[1]["metadata"]["phase"] == "commentary"
    assert rebuilt[1]["metadata"]["native_indices"] == [1]

    assert rebuilt[2]["role"] == "tool"
    assert rebuilt[2]["content"] == "{\"ok\": true}"
    assert rebuilt[2]["metadata"]["tool_call_id"] == "call_123"
    assert rebuilt[2]["metadata"]["trace_id"] == "t1"
    assert rebuilt[2]["metadata"]["native_indices"] == [2]


def test_to_native_tool_without_tool_call_id_raises() -> None:
    provider = OpenAIResponsesProvider()

    with pytest.raises(ValueError, match="tool_call_id"):
        provider.to_native_messages(
            [{"role": "tool", "content": "x", "metadata": {}}],
            {},
        )


def test_call_api_uses_fixture_payload_shape_and_normalizes_output() -> None:
    provider = OpenAIResponsesProvider()
    fixture = _load_fixture()
    fake_client = _FixtureClient(fixture)

    input_items = [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "hi"}],
            "_metadata": {"trace": "keep-local-only"},
        }
    ]

    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 12,
        },
        "client": fake_client,
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 12,
        },
    }

    partials, finals, full_native, _new_state = provider.call_api(input_items, state)

    assert partials == []
    assert finals
    assert full_native[:1] == input_items
    assert full_native[1:] == finals

    call_kwargs = fake_client.responses.calls[0]
    assert call_kwargs["model"] == "gpt-5-mini"
    assert call_kwargs["stream"] is False
    assert isinstance(call_kwargs["input"], list)
    assert "_metadata" not in call_kwargs["input"][0]

    assert any(
        isinstance(item, dict)
        and item.get("type") == "message"
        and isinstance(item.get("_metadata"), dict)
        and isinstance(item["_metadata"].get("response_id"), str)
        for item in finals
    )


def test_call_api_raises_on_invalid_input_item_shape() -> None:
    provider = OpenAIResponsesProvider()
    fixture = _load_fixture()

    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 12,
        },
        "client": _FixtureClient(fixture),
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 12,
        },
    }

    with pytest.raises(RuntimeError, match="missing 'type'"):
        provider.call_api([{"role": "user", "content": "hi"}], state)


def test_call_api_wraps_sdk_error() -> None:
    provider = OpenAIResponsesProvider()

    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 12,
        },
        "client": _ErrorClient(),
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 12,
        },
    }

    with pytest.raises(RuntimeError, match="OpenAI Responses call failed"):
        provider.call_api(
            [{"type": "message", "role": "user", "content": [{"type": "input_text", "text": "hi"}]}],
            state,
        )


def test_call_api_raises_on_missing_output_in_response() -> None:
    provider = OpenAIResponsesProvider()

    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 12,
        },
        "client": _FixtureClient({"id": "resp_123"}),
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 12,
        },
    }

    with pytest.raises(RuntimeError, match="missing output list"):
        provider.call_api(
            [{"type": "message", "role": "user", "content": [{"type": "input_text", "text": "hi"}]}],
            state,
        )
