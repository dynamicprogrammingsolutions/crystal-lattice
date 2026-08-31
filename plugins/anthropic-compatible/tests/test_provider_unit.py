from __future__ import annotations

from typing import Any

from anthropic_plugins.content_blocks import reduce_event
from anthropic_plugins.provider import AnthropicProvider


class Dumpable:
    def __init__(self, value: dict[str, Any]):
        self.value = value

    def model_dump(self, **_: Any) -> dict[str, Any]:
        return self.value


class FakeMessages:
    def __init__(self, response: Any):
        self.response = response
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        return self.response


class FakeModels:
    def list(self, **_: Any) -> list[Dumpable]:
        return [
            Dumpable(
                {
                    "id": "claude-test",
                    "display_name": "Claude Test",
                    "max_input_tokens": 1000,
                    "max_tokens": 200,
                    "capabilities": {"tools": {"supported": True}},
                }
            )
        ]


class FakeClient:
    def __init__(self, response: Any):
        self.messages: Any = FakeMessages(response)
        self.models: Any = FakeModels()
        self.closed = False

    def close(self) -> None:
        self.closed = True


def test_provider_identity_schema_and_tags() -> None:
    provider = AnthropicProvider()
    schema = provider.get_config_schema()

    assert provider.name == "anthropic"
    assert schema["model"]["required"] is True
    assert schema["base_url"]["default"] == "https://api.anthropic.com"
    assert "supports_tools" in provider.get_tags({}, [])
    assert "supports_reasoning" in provider.get_tags({}, [])
    assert "supports_usage" in provider.get_tags({}, [])


def test_provider_config_ui_uses_renderable_control_types() -> None:
    elements = AnthropicProvider().get_ui_elements(
        {"model": "claude-test"},
        {"models": [{"id": "claude-test", "name": "Claude Test"}]},
    )

    assert elements[0]["type"] == "select"
    assert elements[0]["options"] == [{"value": "claude-test", "label": "Claude Test"}]
    assert elements[1]["type"] == "text"


def test_provider_converts_plain_messages_and_separates_system() -> None:
    provider = AnthropicProvider()
    config = {"model": "m", "api_key": "secret"}
    state = provider.init(config)
    core_messages = [
        {"role": "system", "content": "Be concise.", "metadata": {}},
        {"role": "user", "content": "Hello", "metadata": {"trace": "x"}},
    ]

    native = provider.to_native_messages(core_messages, state)
    native, state = provider.initialize_request(native, state, request_id="r1")

    assert native[1]["_metadata"]["trace"] == "x"
    assert state["request"]["payload"]["system"] == "Be concise."
    assert state["request"]["payload"]["messages"] == [
        {"role": "user", "content": "Hello"}
    ]


def test_non_streaming_call_preserves_blocks_and_raw_usage(monkeypatch) -> None:
    response = Dumpable(
        {
            "id": "msg_1",
            "model": "claude-test",
            "role": "assistant",
            "content": [{"type": "text", "text": "Hello"}],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 3, "output_tokens": 2},
        }
    )
    client = FakeClient(response)
    provider = AnthropicProvider()
    monkeypatch.setattr(provider, "_client", lambda config: client)
    state = provider.init({"model": "claude-test", "api_key": "secret"})
    native = [{"role": "user", "content": "Hi"}]
    native, state = provider.initialize_request(native, state)

    partials, finals, history, new_state = provider.call_api(native, state)

    assert partials == []
    assert finals[0]["content"] == [{"type": "text", "text": "Hello"}]
    assert finals[0]["_metadata"]["anthropic_usage"]["input_tokens"] == 3
    assert history[-1] == finals[0]
    assert new_state["anthropic_runtime"]["completed"] is True
    assert client.messages.calls[0]["stream"] is False
    assert client.closed is True


def test_model_discovery_normalizes_sdk_models(monkeypatch) -> None:
    client = FakeClient(response=None)
    provider = AnthropicProvider()
    monkeypatch.setattr(provider, "_client", lambda config: client)

    models = provider.get_models({"api_key": "secret"})

    assert models == [
        {
            "id": "claude-test",
            "name": "Claude Test",
            "created_at": None,
            "max_input_tokens": 1000,
            "max_output_tokens": 200,
            "capabilities": {"tools": {"supported": True}},
            "raw": {
                "id": "claude-test",
                "display_name": "Claude Test",
                "max_input_tokens": 1000,
                "max_tokens": 200,
                "capabilities": {"tools": {"supported": True}},
            },
        }
    ]
    assert client.closed is True


def test_model_discovery_failure_returns_empty_list(monkeypatch) -> None:
    class BrokenModels:
        def list(self, **_: Any) -> Any:
            raise RuntimeError("unavailable")

    client = FakeClient(response=None)
    client.models = BrokenModels()
    provider = AnthropicProvider()
    monkeypatch.setattr(provider, "_client", lambda config: client)

    assert provider.get_models({"api_key": "secret"}) == []
    assert client.closed is True


def test_sdk_client_uses_provider_owned_retry_and_transport_config(monkeypatch) -> None:
    captured: dict[str, Any] = {}

    class CapturedClient:
        def __init__(self, **kwargs: Any):
            captured.update(kwargs)

    monkeypatch.setattr("anthropic_plugins.provider.Anthropic", CapturedClient)
    provider = AnthropicProvider()

    provider._client(
        {
            "api_key": "secret",
            "base_url": "http://example.test",
            "timeout": 12,
            "max_retries": 4,
            "anthropic_version": "2023-06-01",
        }
    )

    assert captured["api_key"] == "secret"
    assert captured["base_url"] == "http://example.test"
    assert captured["timeout"] == 12
    assert captured["max_retries"] == 4
    assert captured["default_headers"]["anthropic-version"] == "2023-06-01"


def test_cancel_request_closes_active_stream_and_client() -> None:
    class Closable:
        def __init__(self) -> None:
            self.closed = False

        def close(self) -> None:
            self.closed = True

    provider = AnthropicProvider()
    stream = Closable()
    client = Closable()
    provider._active["request-1"] = (stream, client)

    assert provider.cancel_request("request-1") is True
    assert stream.closed is True
    assert client.closed is True
    assert provider.cancel_request("unknown") is False


def test_stream_reducer_preserves_text_thinking_signature_and_tool_json() -> None:
    accumulator = None
    events = [
        {
            "type": "message_start",
            "message": {
                "id": "msg_1",
                "model": "m",
                "content": [],
                "usage": {"input_tokens": 4, "output_tokens": 0},
            },
        },
        {
            "type": "content_block_start",
            "index": 0,
            "content_block": {"type": "thinking", "thinking": "", "signature": ""},
        },
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "thinking_delta", "thinking": "check"},
        },
        {
            "type": "content_block_delta",
            "index": 0,
            "delta": {"type": "signature_delta", "signature": "sig"},
        },
        {"type": "content_block_stop", "index": 0},
        {
            "type": "content_block_start",
            "index": 1,
            "content_block": {
                "type": "tool_use",
                "id": "tool_1",
                "name": "echo",
                "input": {},
            },
        },
        {
            "type": "content_block_delta",
            "index": 1,
            "delta": {"type": "input_json_delta", "partial_json": '{"x":'},
        },
        {
            "type": "content_block_delta",
            "index": 1,
            "delta": {"type": "input_json_delta", "partial_json": "1}"},
        },
        {"type": "content_block_stop", "index": 1},
        {
            "type": "content_block_start",
            "index": 2,
            "content_block": {"type": "text", "text": ""},
        },
        {
            "type": "content_block_delta",
            "index": 2,
            "delta": {"type": "text_delta", "text": "done"},
        },
        {"type": "content_block_stop", "index": 2},
        {"type": "message_stop"},
    ]
    completed = False
    for event in events:
        _partial, accumulator, completed = reduce_event(accumulator, event)

    assert completed is True
    assert isinstance(accumulator, dict)
    assert accumulator["content"] == [
        {"type": "thinking", "thinking": "check", "signature": "sig"},
        {"type": "tool_use", "id": "tool_1", "name": "echo", "input": {"x": 1}},
        {"type": "text", "text": "done"},
    ]


def test_error_redacts_configured_api_key(monkeypatch) -> None:
    class BrokenMessages:
        def create(self, **_: Any) -> Any:
            raise RuntimeError("request included secret-value")

    client = FakeClient(response=None)
    client.messages = BrokenMessages()
    provider = AnthropicProvider()
    monkeypatch.setattr(provider, "_client", lambda config: client)
    state = provider.init({"model": "m", "api_key": "secret-value"})
    native, state = provider.initialize_request(
        [{"role": "user", "content": "Hi"}], state
    )

    try:
        provider.call_api(native, state)
    except RuntimeError as exc:
        assert "secret-value" not in str(exc)
        assert "<redacted>" in str(exc)
    else:
        raise AssertionError("expected request error")
