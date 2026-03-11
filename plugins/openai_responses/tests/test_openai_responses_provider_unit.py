from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from agent_core import AgentCore
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider


FIXTURE_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "openai_responses_gpt5mini_nonstreaming.json"
)

STREAM_FIXTURE_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "openai_responses_gpt5mini_streaming_events.json"
)

STREAM_FAILED_FIXTURE_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "openai_responses_gpt5mini_streaming_failed_events.json"
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


class _FixtureStreamEvent:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def model_dump(self, mode: str = "python") -> Dict[str, Any]:
        _ = mode
        return self._payload


class _FixtureStream:
    def __init__(self, events: list[Dict[str, Any]]) -> None:
        self._events = events

    def __enter__(self) -> "_FixtureStream":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        _ = (exc_type, exc, tb)

    def __iter__(self):
        for idx, event in enumerate(self._events):
            # Mix object + dict event payloads to verify normalization.
            if idx % 2 == 0:
                yield _FixtureStreamEvent(event)
            else:
                yield event


class _FixtureStreamingResponsesResource:
    def __init__(self, events: list[Dict[str, Any]]) -> None:
        self._events = events
        self.calls: list[Dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _FixtureStream:
        self.calls.append(kwargs)
        if kwargs.get("stream") is not True:
            raise AssertionError("expected stream=True")
        return _FixtureStream(self._events)


class _FixtureStreamingClient:
    def __init__(self, events: list[Dict[str, Any]]) -> None:
        self.responses = _FixtureStreamingResponsesResource(events)


class _ErrorResponsesResource:
    def create(self, **kwargs: Any) -> Any:
        _ = kwargs
        raise RuntimeError("boom")


class _ErrorClient:
    responses = _ErrorResponsesResource()


def _load_fixture() -> Dict[str, Any]:
    return json.loads(FIXTURE_PATH.read_text(encoding="utf-8"))


def _load_stream_fixture_events() -> list[Dict[str, Any]]:
    payload = json.loads(STREAM_FIXTURE_PATH.read_text(encoding="utf-8"))
    events = payload.get("events")
    if not isinstance(events, list):
        raise RuntimeError("streaming fixture missing events list")
    return [ev for ev in events if isinstance(ev, dict)]


def _load_failed_stream_fixture_events() -> list[Dict[str, Any]]:
    payload = json.loads(STREAM_FAILED_FIXTURE_PATH.read_text(encoding="utf-8"))
    events = payload.get("events")
    if not isinstance(events, list):
        raise RuntimeError("streaming failure fixture missing events list")
    return [ev for ev in events if isinstance(ev, dict)]


class _StreamingFixtureProvider(OpenAIResponsesProvider):
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        state = super().init(config)
        state["client"] = _FixtureStreamingClient(_load_stream_fixture_events())
        return state


class _StreamingFailureFixtureProvider(OpenAIResponsesProvider):
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        state = super().init(config)
        state["client"] = _FixtureStreamingClient(_load_failed_stream_fixture_events())
        return state


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
        "supports_reasoning",
        "supports_reasoning_effort",
        "supports_tools",
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


def test_from_native_messages_assigns_response_segment_indices_for_unconverted_items() -> None:
    provider = OpenAIResponsesProvider()

    native_messages = [
        {
            "type": "reasoning",
            "summary": [{"type": "summary_text", "text": "thinking"}],
            "_metadata": {"response_id": "resp_1"},
        },
        {
            "type": "message",
            "role": "assistant",
            "phase": "final_answer",
            "content": [{"type": "output_text", "text": "done"}],
            "_metadata": {"response_id": "resp_1"},
        },
    ]

    rebuilt = provider.from_native_messages(native_messages, {})

    assert rebuilt
    owner = rebuilt[-1]
    assert owner["role"] == "assistant"
    assert owner["content"] == "done"
    md = owner.get("metadata") or {}
    assert md.get("response_id") == "resp_1"
    assert md.get("native_indices") == [0, 1]


def test_from_native_messages_assigns_tool_call_indices_without_tool_calls_metadata() -> None:
    provider = OpenAIResponsesProvider()

    native_messages = [
        {
            "type": "function_call",
            "call_id": "call_1",
            "name": "lookup",
            "arguments": "{\"id\":1}",
            "_metadata": {"response_id": "resp_2"},
        },
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "Calling tool"}],
            "_metadata": {"response_id": "resp_2"},
        },
    ]

    rebuilt = provider.from_native_messages(native_messages, {})

    assert rebuilt
    owner = rebuilt[-1]
    assert owner["role"] == "assistant"
    assert owner["content"] == "Calling tool"
    md = owner.get("metadata") or {}
    assert md.get("response_id") == "resp_2"
    assert md.get("native_indices") == [0, 1]
    assert "tool_calls" not in md


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
    assert all(
        not (
            isinstance(item, dict)
            and isinstance(item.get("_metadata"), dict)
            and "usage" in item["_metadata"]
        )
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


def test_stream_api_normalizes_events_and_strips_internal_metadata() -> None:
    provider = OpenAIResponsesProvider()
    stream_events = _load_stream_fixture_events()
    fake_client = _FixtureStreamingClient(stream_events)

    input_items = [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "stream hi"}],
            "_metadata": {"trace": "internal-only"},
        }
    ]

    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 30,
        },
        "client": fake_client,
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 30,
        },
    }

    normalized = list(provider.stream_api(input_items, state))

    assert normalized
    assert all(isinstance(ev, dict) for ev in normalized)
    assert any(ev.get("type") == "response.output_text.delta" for ev in normalized)
    assert any(ev.get("type") == "response.completed" for ev in normalized)

    call_kwargs = fake_client.responses.calls[0]
    assert call_kwargs["stream"] is True
    assert isinstance(call_kwargs["input"], list)
    assert "_metadata" not in call_kwargs["input"][0]


def test_stream_api_wraps_sdk_error() -> None:
    provider = OpenAIResponsesProvider()
    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 30,
        },
        "client": _ErrorClient(),
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 30,
        },
    }

    with pytest.raises(RuntimeError, match="OpenAI Responses stream failed"):
        list(
            provider.stream_api(
                [{"type": "message", "role": "user", "content": [{"type": "input_text", "text": "hi"}]}],
                state,
            )
        )


def test_process_chunk_emits_partials_and_completed_finals_only() -> None:
    provider = OpenAIResponsesProvider()
    events = _load_stream_fixture_events()

    native_messages: list[Dict[str, Any]] = []
    partials_out: list[Dict[str, Any]] = []
    finals_out: list[Dict[str, Any]] = []

    for event in events:
        partials, finals, native_messages, _state = provider.process_chunk(event, native_messages, {})
        partials_out.extend(partials)
        finals_out.extend(finals)

        if event.get("type") != "response.completed":
            assert finals == []

    assert any(
        isinstance(p, dict)
        and p.get("role") == "assistant"
        and isinstance(p.get("content"), str)
        and p.get("content")
        for p in partials_out
    )

    assert finals_out
    assert native_messages[-len(finals_out) :] == finals_out

    assert any(
        isinstance(item, dict)
        and isinstance(item.get("_metadata"), dict)
        and isinstance(item["_metadata"].get("response_id"), str)
        for item in finals_out
    )

    assert all(
        not (
            isinstance(item, dict)
            and isinstance(item.get("type"), str)
            and item["type"].startswith("response.")
        )
        for item in native_messages
    )


def test_process_chunk_raises_on_completed_event_without_output() -> None:
    provider = OpenAIResponsesProvider()

    with pytest.raises(RuntimeError, match="missing output list"):
        provider.process_chunk(
            {"type": "response.completed", "response": {"id": "resp_bad"}},
            [],
            {},
        )


def test_process_chunk_raises_on_response_failed_terminal_event() -> None:
    provider = OpenAIResponsesProvider()
    events = _load_failed_stream_fixture_events()

    native_messages: list[Dict[str, Any]] = []
    state: Dict[str, Any] = {}

    for event in events[:-1]:
        _partials, _finals, native_messages, state = provider.process_chunk(event, native_messages, state)

    with pytest.raises(RuntimeError, match="response.failed"):
        provider.process_chunk(events[-1], native_messages, state)


def test_process_chunk_raises_on_response_incomplete_terminal_event() -> None:
    provider = OpenAIResponsesProvider()

    with pytest.raises(RuntimeError, match="response.incomplete"):
        provider.process_chunk(
            {
                "type": "response.incomplete",
                "response": {
                    "id": "resp_incomplete_1",
                    "incomplete_details": {"reason": "max_output_tokens"},
                },
            },
            [],
            {},
        )


def test_finalize_is_noop_after_streaming_reduction() -> None:
    provider = OpenAIResponsesProvider()
    events = _load_stream_fixture_events()

    native_messages: list[Dict[str, Any]] = []
    state: Dict[str, Any] = {}
    for event in events:
        _partials, _finals, native_messages, state = provider.process_chunk(event, native_messages, state)

    final_messages, native_after_finalize, _state = provider.finalize(native_messages, state)

    assert final_messages == []
    assert native_after_finalize == native_messages


def test_finalize_raises_when_stream_ended_without_completed() -> None:
    provider = OpenAIResponsesProvider()

    _partials, _finals, _native_messages, state = provider.process_chunk(
        {"type": "response.created", "response": {"id": "resp_pending"}},
        [],
        {},
    )

    with pytest.raises(RuntimeError, match="without response.completed"):
        provider.finalize([], state)


def test_send_request_stream_wrapper_compatibility_with_streaming_finals() -> None:
    core = AgentCore()
    core.register_provider(_StreamingFixtureProvider)

    config = {
        "model": "gpt-5-mini",
        "api_key": "test_key",
        "base_url": "https://api.openai.com/v1",
        "timeout": 30,
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with STREAM_OK")

    partial_fragments: list[str] = []
    final_session = None
    final_messages: list[Dict[str, Any]] = []

    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "partial":
            text = chunk["message"].get("content")
            if isinstance(text, str) and text:
                partial_fragments.append(text)
        elif chunk["type"] == "final":
            final_session = chunk["session"]
            final_messages = chunk["messages"]

    assert partial_fragments
    assert final_session is not None
    assert final_messages

    assistant_msg = final_messages[-1]
    assert assistant_msg.get("role") == "assistant"
    assert isinstance(assistant_msg.get("content"), str)
    assert "STREAM_OK" in assistant_msg["content"]

    native_history = (final_session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert all(
        not (
            isinstance(item, dict)
            and isinstance(item.get("type"), str)
            and item["type"].startswith("response.")
        )
        for item in native_history
    )


def test_send_request_stream_raises_on_failed_terminal_event() -> None:
    core = AgentCore()
    core.register_provider(_StreamingFailureFixtureProvider)

    config = {
        "model": "gpt-5-mini",
        "api_key": "test_key",
        "base_url": "https://api.openai.com/v1",
        "timeout": 30,
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with STREAM_OK")

    with pytest.raises(RuntimeError, match="response.failed"):
        list(core.send_request_stream(session, config))
