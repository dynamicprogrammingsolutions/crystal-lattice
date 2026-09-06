from __future__ import annotations

import base64
import json
import threading
import time
from pathlib import Path
from typing import Any, Dict

import pytest

from agent_app.session_assets import FilesystemSessionAssetStore
from agent_core import AgentCore
from agent_core.tool_result_payloads import (
    FORMAT_OPENAI_CHAT_COMPLETIONS,
    FORMAT_OPENAI_RESPONSES,
    TOOL_RESULT_FIELD,
    make_provider_native_tool_result,
)
from agent_core.types import ProviderRequestCancelled
import openai_responses_plugins.openai_responses_provider as provider_module
import openai_responses_plugins.openai_responses_runtime as runtime_module
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
from openai_responses_plugins.openai_responses_tools_extension import (
    OpenAIResponsesToolsExtension,
)


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
        self.option_calls: list[Dict[str, Any]] = []

    def with_options(self, **kwargs: Any) -> "_FixtureClient":
        self.option_calls.append(kwargs)
        return self


class _FixtureFileObject:
    def __init__(self, file_id: str) -> None:
        self.id = file_id

    def model_dump(self, mode: str = "python") -> Dict[str, Any]:
        _ = mode
        return {"id": self.id}


class _FixtureFilesResource:
    def __init__(self) -> None:
        self.calls: list[Dict[str, Any]] = []
        self._cursor = 0

    def create(self, **kwargs: Any) -> _FixtureFileObject:
        self.calls.append(kwargs)
        self._cursor += 1
        return _FixtureFileObject(f"file_{self._cursor}")


class _UploadFixtureClient(_FixtureClient):
    def __init__(self, payload: Dict[str, Any]) -> None:
        super().__init__(payload)
        self.files = _FixtureFilesResource()


class _FixtureModelObject:
    def __init__(self, model_id: str, name: str | None = None) -> None:
        self.id = model_id
        self.name = name


class _FixtureModelListResponse:
    def __init__(self, data: list[Any]) -> None:
        self.data = data


class _FixtureModelsResource:
    def __init__(self, result: Any = None, error: Exception | None = None) -> None:
        self._result = result
        self._error = error
        self.calls = 0

    def list(self) -> Any:
        self.calls += 1
        if self._error is not None:
            raise self._error
        return self._result


class _FixtureModelsClient:
    def __init__(self, result: Any = None, error: Exception | None = None) -> None:
        self.models = _FixtureModelsResource(result=result, error=error)


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
        self.option_calls: list[Dict[str, Any]] = []

    def with_options(self, **kwargs: Any) -> "_FixtureStreamingClient":
        self.option_calls.append(kwargs)
        return self


class _FixtureRawSSEStream:
    def __init__(
        self,
        events: list[Dict[str, Any]],
        headers: Dict[str, str] | None = None,
    ) -> None:
        self._events = events
        self.headers = headers or {}

    def __enter__(self) -> "_FixtureRawSSEStream":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        _ = (exc_type, exc, tb)

    def iter_lines(self):
        for event in self._events:
            yield f"data: {json.dumps(event)}"
            yield ""
        yield "data: [DONE]"
        yield ""


class _FixtureRawStreamingCreateResource:
    def __init__(self, events: list[Dict[str, Any]]) -> None:
        self._events = events
        self.calls: list[Dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _FixtureRawSSEStream:
        self.calls.append(kwargs)
        if kwargs.get("stream") is not True:
            raise AssertionError("expected stream=True")
        return _FixtureRawSSEStream(self._events)


class _FixtureRawStreamingResponsesResource:
    def __init__(self, events: list[Dict[str, Any]]) -> None:
        self.with_streaming_response = _FixtureRawStreamingCreateResource(events)

    def create(self, **kwargs: Any) -> Any:
        _ = kwargs
        raise AssertionError("expected ChatGPT raw streaming path")


class _FixtureRawStreamingClient:
    def __init__(self, events: list[Dict[str, Any]]) -> None:
        self.responses = _FixtureRawStreamingResponsesResource(events)
        self.option_calls: list[Dict[str, Any]] = []

    def with_options(self, **kwargs: Any) -> "_FixtureRawStreamingClient":
        self.option_calls.append(kwargs)
        return self


class _UploadStreamingFixtureClient(_FixtureStreamingClient):
    def __init__(self, events: list[Dict[str, Any]]) -> None:
        super().__init__(events)
        self.files = _FixtureFilesResource()


class _SequentialStreamingResponsesResource:
    def __init__(self, event_batches: list[list[Dict[str, Any]]]) -> None:
        self._event_batches = event_batches
        self._cursor = 0
        self.calls: list[Dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _FixtureStream:
        self.calls.append(kwargs)
        if kwargs.get("stream") is not True:
            raise AssertionError("expected stream=True")
        index = (
            self._cursor
            if self._cursor < len(self._event_batches)
            else len(self._event_batches) - 1
        )
        self._cursor += 1
        return _FixtureStream(self._event_batches[index])


class _SequentialStreamingClient:
    def __init__(self, event_batches: list[list[Dict[str, Any]]]) -> None:
        self.responses = _SequentialStreamingResponsesResource(event_batches)
        self.option_calls: list[Dict[str, Any]] = []

    def with_options(self, **kwargs: Any) -> "_SequentialStreamingClient":
        self.option_calls.append(kwargs)
        return self


class _RetryOnceResponsesResource:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload
        self.calls: list[Dict[str, Any]] = []
        self._failed = False

    def create(self, **kwargs: Any) -> _FixtureResponse:
        self.calls.append(kwargs)
        if not self._failed:
            self._failed = True
            raise RuntimeError("No such file: file_stale")
        return _FixtureResponse(self._payload)


class _RetryOnceUploadFixtureClient(_UploadFixtureClient):
    def __init__(self, payload: Dict[str, Any]) -> None:
        super().__init__(payload)
        self.responses = _RetryOnceResponsesResource(payload)


class _ErrorResponsesResource:
    def create(self, **kwargs: Any) -> Any:
        _ = kwargs
        raise RuntimeError("boom")


class _ErrorClient:
    responses = _ErrorResponsesResource()


class _BlockingResponsesResource:
    def __init__(self, gate: threading.Event) -> None:
        self._gate = gate
        self.calls: list[Dict[str, Any]] = []

    def create(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        while not self._gate.wait(0.05):
            continue
        raise RuntimeError("closed")


class _BlockingClient:
    def __init__(self) -> None:
        self._gate = threading.Event()
        self.responses = _BlockingResponsesResource(self._gate)
        self.option_calls: list[Dict[str, Any]] = []

    def with_options(self, **kwargs: Any) -> "_BlockingClient":
        self.option_calls.append(kwargs)
        return self

    def close(self) -> None:
        self._gate.set()


class _BlockingStream:
    def __init__(self) -> None:
        self.closed = threading.Event()

    def __enter__(self) -> "_BlockingStream":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        _ = (exc_type, exc, tb)

    def close(self) -> None:
        self.closed.set()

    def __iter__(self):
        while not self.closed.wait(0.05):
            continue
        raise RuntimeError("stream closed")


class _BlockingStreamingResponsesResource:
    def __init__(self, stream: _BlockingStream) -> None:
        self._stream = stream
        self.calls: list[Dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _BlockingStream:
        self.calls.append(kwargs)
        return self._stream


class _BlockingStreamingClient:
    def __init__(self) -> None:
        self.stream = _BlockingStream()
        self.responses = _BlockingStreamingResponsesResource(self.stream)
        self.option_calls: list[Dict[str, Any]] = []

    def with_options(self, **kwargs: Any) -> "_BlockingStreamingClient":
        self.option_calls.append(kwargs)
        return self

    def close(self) -> None:
        self.stream.close()


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


def _chatgpt_raw_stream_events_missing_completed_output() -> list[Dict[str, Any]]:
    return [
        {
            "type": "response.created",
            "response": {
                "id": "resp_chatgpt_raw_1",
                "status": "in_progress",
            },
        },
        {
            "type": "response.output_text.delta",
            "delta": "RAW_OK",
        },
        {
            "type": "response.output_item.done",
            "item": {
                "type": "message",
                "id": "msg_chatgpt_raw_1",
                "role": "assistant",
                "status": "completed",
                "content": [{"type": "output_text", "text": "RAW_OK"}],
            },
        },
        {
            "type": "response.completed",
            "response": {
                "id": "resp_chatgpt_raw_1",
                "status": "completed",
                "usage": {
                    "input_tokens": 1,
                    "output_tokens": 1,
                    "total_tokens": 2,
                },
            },
        },
    ]


class _RawChatGPTCompletedWithoutOutputProvider(OpenAIResponsesProvider):
    last_client: _FixtureRawStreamingClient | None = None

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        state = super().init(config)
        client = _FixtureRawStreamingClient(
            _chatgpt_raw_stream_events_missing_completed_output()
        )
        type(self).last_client = client
        state["client"] = client
        return state


def _premature_stream_events(*, include_partial: bool) -> list[Dict[str, Any]]:
    events: list[Dict[str, Any]] = [
        {
            "type": "response.created",
            "sequence_number": 0,
            "response": {
                "id": "resp_retry_fixture",
                "status": "in_progress",
                "output": [],
            },
        },
        {
            "type": "response.in_progress",
            "sequence_number": 1,
            "response": {
                "id": "resp_retry_fixture",
                "status": "in_progress",
                "output": [],
            },
        },
    ]
    if include_partial:
        events.append(
            {
                "type": "response.output_text.delta",
                "sequence_number": 2,
                "delta": "partial ",
                "item_id": "msg_retry_fixture_1",
                "output_index": 0,
                "content_index": 0,
                "logprobs": [],
            }
        )
    return events


class _RecoveryProviderBase(OpenAIResponsesProvider):
    recovery_mode = "early_only"
    include_partial = False
    last_client: _SequentialStreamingClient | None = None

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        state = super().init(config)
        client = _SequentialStreamingClient(
            [
                _premature_stream_events(include_partial=self.include_partial),
                _load_stream_fixture_events(),
            ]
        )
        type(self).last_client = client
        state["client"] = client
        return state

    def initialize_request(
        self,
        native_messages: list[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> tuple[list[Dict[str, Any]], Dict[str, Any]]:
        native_after, next_state = super().initialize_request(native_messages, state)
        request = dict(next_state.get("request") or {})
        payload = dict(request.get("payload") or {})
        payload["service_tier"] = "flex"
        request["payload"] = payload
        request["stream_recovery_mode"] = self.recovery_mode
        request["stream_recovery_retries"] = 3
        return native_after, {**next_state, "request": request}


class _EarlyOnlyRecoveryProvider(_RecoveryProviderBase):
    recovery_mode = "early_only"
    include_partial = False


class _EarlyOnlyVisiblePartialProvider(_RecoveryProviderBase):
    recovery_mode = "early_only"
    include_partial = True


class _AggressiveRecoveryProvider(_RecoveryProviderBase):
    recovery_mode = "aggressive"
    include_partial = True


def test_provider_metadata_schema_and_tags() -> None:
    provider = OpenAIResponsesProvider()

    assert provider.name == "openai_responses"
    assert provider.version == "0.1.0"

    schema = provider.get_config_schema()
    assert "model" in schema
    assert "api_key" in schema
    assert "base_url" in schema
    assert "instructions" not in schema
    assert "timeout" in schema
    assert "enable_terminal_error_retries" in schema
    assert "terminal_error_max_retries" in schema

    tags = provider.get_tags({"model": "gpt-5-mini"}, [{"id": "gpt-5-mini"}])
    assert tags == [
        "provider:openai_responses",
        "openai_responses",
        "supports_streaming",
        "supports_reasoning",
        "supports_reasoning_effort",
        "supports_tools",
        "supports_verbosity",
    ]


def test_get_tags_does_not_advertise_verbosity_for_non_gpt5_models() -> None:
    provider = OpenAIResponsesProvider()

    tags = provider.get_tags({"model": "gpt-4.1-mini"}, [{"id": "gpt-4.1-mini"}])

    assert "supports_verbosity" not in tags


def test_get_models_uses_sdk_and_normalizes_response(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OpenAIResponsesProvider()
    captured: dict[str, Any] = {}
    fake_client = _FixtureModelsClient(
        _FixtureModelListResponse(
            [
                _FixtureModelObject("gpt-5-mini"),
                {"id": "gpt-4.1-mini", "name": "GPT 4.1 Mini"},
                _FixtureModelObject("", "skip-me"),
                {"name": "missing id"},
            ]
        )
    )

    def _fake_openai(**kwargs: Any) -> _FixtureModelsClient:
        captured.update(kwargs)
        return fake_client

    monkeypatch.setattr(runtime_module, "OpenAI", _fake_openai)
    monkeypatch.setenv("OPENAI_API_KEY", "test_env_key")

    models = provider.get_models({"base_url": "https://example.test/v1", "timeout": 15})

    assert captured == {
        "api_key": "test_env_key",
        "base_url": "https://example.test/v1",
        "timeout": 15.0,
    }
    assert fake_client.models.calls == 1
    assert models == [
        {"id": "gpt-5-mini"},
        {"id": "gpt-4.1-mini", "name": "GPT 4.1 Mini"},
    ]


def test_get_models_returns_empty_list_and_logs_warning_when_credentials_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OpenAIResponsesProvider()
    warnings: list[tuple[str, dict[str, Any]]] = []

    class _Logger:
        def warning(self, message: str, **kwargs: Any) -> None:
            warnings.append((message, kwargs))

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    monkeypatch.setattr(provider_module, "get_logger", lambda name: _Logger())

    models = provider.get_models({"base_url": "https://api.openai.com/v1"})

    assert models == []
    assert warnings
    assert warnings[0][0] == "Failed to fetch models from OpenAI"
    assert "api_key is required" in warnings[0][1]["error"]


def test_get_models_returns_empty_list_and_logs_warning_when_sdk_call_fails(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OpenAIResponsesProvider()
    warnings: list[tuple[str, dict[str, Any]]] = []

    class _Logger:
        def warning(self, message: str, **kwargs: Any) -> None:
            warnings.append((message, kwargs))

    monkeypatch.setattr(
        provider,
        "_create_sdk_client_for_discovery",
        lambda config: _FixtureModelsClient(error=RuntimeError("network boom")),
    )
    monkeypatch.setattr(provider_module, "get_logger", lambda name: _Logger())

    models = provider.get_models({"api_key": "test_key"})

    assert models == []
    assert warnings
    assert warnings[0][0] == "Failed to fetch models from OpenAI"
    assert warnings[0][1]["error"] == "network boom"


def test_get_models_uses_codex_catalog_for_chatgpt_discovery(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    provider = OpenAIResponsesProvider()
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text(
        json.dumps(
            {
                "access_token": "chatgpt-access-token",
                "account_id": "acct-123",
                "expires_at": "2999-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    captured: dict[str, Any] = {}

    def _fake_fetch_codex_models(config: Dict[str, Any]) -> list[Dict[str, Any]]:
        captured["config"] = dict(config)
        return [
            {"id": "gpt-5.4", "name": "gpt-5.4"},
            {"id": "gpt-5.3-codex", "name": "gpt-5.3-codex"},
        ]

    monkeypatch.setattr(provider, "_fetch_codex_models", _fake_fetch_codex_models)
    monkeypatch.setattr(
        provider_module, "_load_snapshot_model_descriptors_shared", lambda: []
    )
    monkeypatch.setattr(
        provider_module, "_load_manual_chatgpt_model_descriptors_shared", lambda: []
    )

    models = provider.get_models(
        {
            "auth_mode": "chatgpt",
            "chatgpt_base_url": "https://chatgpt.example.test/backend-api/codex",
            "chatgpt_credentials_path": str(credentials_path),
            "timeout": 15,
        }
    )

    assert models == [
        {"id": "gpt-5.3-codex", "name": "gpt-5.3-codex"},
        {"id": "gpt-5.4", "name": "gpt-5.4"},
    ]
    assert captured["config"]["auth_mode"] == "chatgpt"


def test_get_models_merges_chatgpt_manual_models_into_codex_catalog(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    provider = OpenAIResponsesProvider()
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text(
        json.dumps(
            {
                "access_token": "chatgpt-access-token",
                "expires_at": "2999-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        provider,
        "_fetch_codex_models",
        lambda config: [{"id": "gpt-5.4", "name": "gpt-5.4"}],
    )
    monkeypatch.setattr(
        provider_module, "_load_snapshot_model_descriptors_shared", lambda: []
    )
    monkeypatch.setattr(
        provider_module,
        "_load_manual_chatgpt_model_descriptors_shared",
        lambda: [
            {"id": "gpt-5.5", "name": "gpt-5.5"},
            {"id": "gpt-5.4", "name": "GPT-5.4 Override"},
        ],
    )

    models = provider.get_models(
        {
            "auth_mode": "chatgpt",
            "chatgpt_credentials_path": str(credentials_path),
        }
    )

    assert models == [
        {"id": "gpt-5.4", "name": "gpt-5.4"},
        {"id": "gpt-5.5", "name": "gpt-5.5"},
    ]


def test_get_models_falls_back_to_chatgpt_models_endpoint_when_codex_fetch_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    provider = OpenAIResponsesProvider()
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text(
        json.dumps(
            {
                "access_token": "chatgpt-access-token",
                "account_id": "acct-123",
                "expires_at": "2999-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )
    captured: dict[str, Any] = {}

    monkeypatch.setattr(
        provider,
        "_fetch_codex_models",
        lambda config: (_ for _ in ()).throw(RuntimeError("codex unavailable")),
    )
    monkeypatch.setattr(
        provider_module, "_load_snapshot_model_descriptors_shared", lambda: []
    )
    monkeypatch.setattr(
        provider_module,
        "_load_manual_chatgpt_model_descriptors_shared",
        lambda: [{"id": "gpt-5.5", "name": "gpt-5.5"}],
    )

    class _FakeHttpResponse:
        def __enter__(self) -> "_FakeHttpResponse":
            return self

        def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
            _ = (exc_type, exc, tb)

        def read(self) -> bytes:
            return json.dumps(
                {
                    "models": [
                        {"slug": "gpt-5.2-codex", "display_name": "GPT-5.2 Codex"},
                    ]
                }
            ).encode("utf-8")

    def _fake_urlopen(request: Any, timeout: float) -> _FakeHttpResponse:
        captured["url"] = request.full_url
        captured["headers"] = dict(request.header_items())
        captured["timeout"] = timeout
        return _FakeHttpResponse()

    monkeypatch.setattr(provider_module, "urlopen", _fake_urlopen)

    models = provider.get_models(
        {
            "auth_mode": "chatgpt",
            "chatgpt_base_url": "https://chatgpt.example.test/backend-api/codex",
            "chatgpt_credentials_path": str(credentials_path),
            "chatgpt_client_version": "0.1.0",
            "timeout": 15,
        }
    )

    assert (
        captured["url"]
        == "https://chatgpt.example.test/backend-api/codex/models?client_version=0.1.0"
    )
    normalized_headers = {
        key.lower(): value for key, value in captured["headers"].items()
    }
    assert normalized_headers["authorization"] == "Bearer chatgpt-access-token"
    assert normalized_headers["chatgpt-account-id"] == "acct-123"
    assert captured["timeout"] == 15.0
    assert models == [
        {"id": "gpt-5.2-codex", "name": "GPT-5.2 Codex"},
        {"id": "gpt-5.5", "name": "gpt-5.5"},
    ]


def test_get_models_uses_snapshot_when_live_codex_fetch_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    provider = OpenAIResponsesProvider()
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text(
        json.dumps(
            {
                "access_token": "chatgpt-access-token",
                "expires_at": "2999-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        provider,
        "_fetch_codex_models",
        lambda config: (_ for _ in ()).throw(RuntimeError("codex unavailable")),
    )
    monkeypatch.setattr(
        provider_module,
        "_load_snapshot_model_descriptors_shared",
        lambda: [{"id": "gpt-5.4", "name": "gpt-5.4 snapshot"}],
    )
    monkeypatch.setattr(
        provider_module,
        "_load_manual_chatgpt_model_descriptors_shared",
        lambda: [{"id": "gpt-5.5", "name": "gpt-5.5"}],
    )

    models = provider.get_models(
        {
            "auth_mode": "chatgpt",
            "chatgpt_credentials_path": str(credentials_path),
        }
    )

    assert models == [
        {"id": "gpt-5.4", "name": "gpt-5.4 snapshot"},
        {"id": "gpt-5.5", "name": "gpt-5.5"},
    ]


def test_get_models_applies_live_over_snapshot_over_manual_precedence(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    provider = OpenAIResponsesProvider()
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text(
        json.dumps(
            {
                "access_token": "chatgpt-access-token",
                "expires_at": "2999-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        provider_module,
        "_load_manual_chatgpt_model_descriptors_shared",
        lambda: [
            {"id": "gpt-5.4", "name": "manual 5.4", "description": "manual"},
            {"id": "gpt-5.5", "name": "manual 5.5"},
        ],
    )
    monkeypatch.setattr(
        provider_module,
        "_load_snapshot_model_descriptors_shared",
        lambda: [
            {"id": "gpt-5.4", "name": "snapshot 5.4"},
            {"id": "gpt-5.6", "name": "snapshot 5.6"},
        ],
    )
    monkeypatch.setattr(
        provider,
        "_fetch_codex_models",
        lambda config: [
            {"id": "gpt-5.4", "name": "live 5.4"},
            {"id": "gpt-5.7", "name": "live 5.7"},
        ],
    )

    models = provider.get_models(
        {
            "auth_mode": "chatgpt",
            "chatgpt_credentials_path": str(credentials_path),
        }
    )

    assert models == [
        {"id": "gpt-5.4", "name": "live 5.4"},
        {"id": "gpt-5.5", "name": "manual 5.5"},
        {"id": "gpt-5.6", "name": "snapshot 5.6"},
        {"id": "gpt-5.7", "name": "live 5.7"},
    ]


def test_get_models_live_codex_overrides_stale_snapshot_and_manual_for_gpt_5_6(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    provider = OpenAIResponsesProvider()
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text(
        json.dumps(
            {
                "access_token": "chatgpt-access-token",
                "expires_at": "2999-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        provider_module,
        "_load_manual_chatgpt_model_descriptors_shared",
        lambda: [
            {
                "id": "gpt-5.6-sol",
                "name": "manual sol",
                "description": "stale manual",
            },
        ],
    )
    monkeypatch.setattr(
        provider_module,
        "_load_snapshot_model_descriptors_shared",
        lambda: [
            {
                "id": "gpt-5.6-sol",
                "name": "snapshot sol",
                "description": "stale snapshot",
            },
            {"id": "gpt-5.6-terra", "name": "snapshot terra"},
        ],
    )
    monkeypatch.setattr(
        provider,
        "_fetch_codex_models",
        lambda config: [
            {
                "id": "gpt-5.6-sol",
                "name": "GPT-5.6-Sol",
                "description": "Latest frontier agentic coding model.",
            },
            {
                "id": "gpt-5.6-terra",
                "name": "GPT-5.6-Terra",
                "description": "Balanced agentic coding model for everyday work.",
            },
            {
                "id": "gpt-5.6-luna",
                "name": "GPT-5.6-Luna",
                "description": "Fast and affordable agentic coding model.",
            },
        ],
    )

    models = provider.get_models(
        {
            "auth_mode": "chatgpt",
            "chatgpt_credentials_path": str(credentials_path),
        }
    )

    assert models == [
        {"id": "gpt-5.6-luna", "name": "GPT-5.6-Luna"},
        {"id": "gpt-5.6-sol", "name": "GPT-5.6-Sol"},
        {"id": "gpt-5.6-terra", "name": "GPT-5.6-Terra"},
    ]


def test_get_models_snapshot_supplies_all_three_gpt_5_6_when_live_fetch_fails(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    provider = OpenAIResponsesProvider()
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text(
        json.dumps(
            {
                "access_token": "chatgpt-access-token",
                "expires_at": "2999-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    def _raise_codex_error(config: Dict[str, Any]) -> list[Dict[str, Any]]:
        raise RuntimeError("codex unavailable")

    monkeypatch.setattr(provider, "_fetch_codex_models", _raise_codex_error)
    monkeypatch.setattr(
        provider_module,
        "_load_snapshot_model_descriptors_shared",
        lambda: [
            {
                "id": "gpt-5.6-luna",
                "name": "GPT-5.6-Luna",
                "description": "Fast and affordable agentic coding model.",
            },
            {
                "id": "gpt-5.6-sol",
                "name": "GPT-5.6-Sol",
                "description": "Latest frontier agentic coding model.",
            },
            {
                "id": "gpt-5.6-terra",
                "name": "GPT-5.6-Terra",
                "description": "Balanced agentic coding model for everyday work.",
            },
        ],
    )
    monkeypatch.setattr(
        provider_module,
        "_load_manual_chatgpt_model_descriptors_shared",
        lambda: [{"id": "gpt-5.5", "name": "gpt-5.5"}],
    )

    def _fail_if_chatgpt_models_called(config: Dict[str, Any]) -> Dict[str, Any]:
        raise AssertionError(
            "ChatGPT /models must not be called when snapshot is available"
        )

    monkeypatch.setattr(
        provider, "_fetch_chatgpt_models", _fail_if_chatgpt_models_called
    )

    models = provider.get_models(
        {
            "auth_mode": "chatgpt",
            "chatgpt_credentials_path": str(credentials_path),
        }
    )

    assert models == [
        {"id": "gpt-5.5", "name": "gpt-5.5"},
        {"id": "gpt-5.6-luna", "name": "GPT-5.6-Luna"},
        {"id": "gpt-5.6-sol", "name": "GPT-5.6-Sol"},
        {"id": "gpt-5.6-terra", "name": "GPT-5.6-Terra"},
    ]


def test_get_models_does_not_call_chatgpt_models_endpoint_when_snapshot_available(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    provider = OpenAIResponsesProvider()
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text(
        json.dumps(
            {
                "access_token": "chatgpt-access-token",
                "expires_at": "2999-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    def _raise_codex_error(config: Dict[str, Any]) -> list[Dict[str, Any]]:
        raise RuntimeError("codex unavailable")

    monkeypatch.setattr(provider, "_fetch_codex_models", _raise_codex_error)
    monkeypatch.setattr(
        provider_module,
        "_load_snapshot_model_descriptors_shared",
        lambda: [{"id": "gpt-5.4", "name": "gpt-5.4 snapshot"}],
    )
    monkeypatch.setattr(
        provider_module,
        "_load_manual_chatgpt_model_descriptors_shared",
        lambda: [],
    )

    chatgpt_calls: list[Dict[str, Any]] = []

    def _fail_if_chatgpt_models_called(config: Dict[str, Any]) -> Dict[str, Any]:
        chatgpt_calls.append(config)
        raise AssertionError(
            "ChatGPT /models must not be called when snapshot is available"
        )

    monkeypatch.setattr(
        provider, "_fetch_chatgpt_models", _fail_if_chatgpt_models_called
    )

    models = provider.get_models(
        {
            "auth_mode": "chatgpt",
            "chatgpt_credentials_path": str(credentials_path),
        }
    )

    assert chatgpt_calls == []
    assert models == [{"id": "gpt-5.4", "name": "gpt-5.4 snapshot"}]


def test_get_models_handles_empty_chatgpt_models_payload(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    provider = OpenAIResponsesProvider()
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text(
        json.dumps(
            {
                "access_token": "chatgpt-access-token",
                "expires_at": "2999-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    def _raise_codex_error(config: Dict[str, Any]) -> list[Dict[str, Any]]:
        raise RuntimeError("codex unavailable")

    monkeypatch.setattr(provider, "_fetch_codex_models", _raise_codex_error)
    monkeypatch.setattr(
        provider_module,
        "_load_snapshot_model_descriptors_shared",
        lambda: [],
    )
    monkeypatch.setattr(
        provider_module,
        "_load_manual_chatgpt_model_descriptors_shared",
        lambda: [{"id": "gpt-5.5", "name": "gpt-5.5"}],
    )
    monkeypatch.setattr(
        provider,
        "_fetch_chatgpt_models",
        lambda config: {"models": []},
    )

    models = provider.get_models(
        {
            "auth_mode": "chatgpt",
            "chatgpt_credentials_path": str(credentials_path),
        }
    )

    assert models == [{"id": "gpt-5.5", "name": "gpt-5.5"}]


def test_get_models_manual_models_only_fill_gaps(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    provider = OpenAIResponsesProvider()
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text(
        json.dumps(
            {
                "access_token": "chatgpt-access-token",
                "expires_at": "2999-01-01T00:00:00Z",
            }
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(
        provider_module,
        "_load_manual_chatgpt_model_descriptors_shared",
        lambda: [
            {"id": "gpt-5.5", "name": "manual 5.5"},
            {"id": "gpt-5.6-sol", "name": "manual sol"},
        ],
    )
    monkeypatch.setattr(
        provider_module,
        "_load_snapshot_model_descriptors_shared",
        lambda: [],
    )
    monkeypatch.setattr(
        provider,
        "_fetch_codex_models",
        lambda config: [
            {
                "id": "gpt-5.6-sol",
                "name": "GPT-5.6-Sol",
                "description": "Latest frontier agentic coding model.",
            },
        ],
    )

    models = provider.get_models(
        {
            "auth_mode": "chatgpt",
            "chatgpt_credentials_path": str(credentials_path),
        }
    )

    assert models == [
        {"id": "gpt-5.5", "name": "manual 5.5"},
        {"id": "gpt-5.6-sol", "name": "GPT-5.6-Sol"},
    ]


def test_get_ui_elements_uses_dropdown_when_models_are_available() -> None:
    provider = OpenAIResponsesProvider()

    elements = provider.get_ui_elements(
        config={},
        tags=["openai_responses"],
        models=[
            {"id": "gpt-5-mini", "name": "GPT-5 Mini"},
            {"id": "gpt-4.1-mini"},
        ],
    )

    assert elements[0] == {
        "ui_type": "config",
        "type": "dropdown",
        "key": "model",
        "label": "OpenAI Model",
        "options": [
            {"label": "GPT-5 Mini", "value": "gpt-5-mini"},
            {"label": "gpt-4.1-mini", "value": "gpt-4.1-mini"},
        ],
        "placeholder": "Search models or enter a model ID",
        "custom_value": {
            "enabled": True,
            "pattern": r"^[^\s]+$",
            "option_label": "Use '{value}' as a custom model ID",
        },
        "rich_ui": {
            "kind": "dropdown",
            "label": "Model",
            "show_label": False,
            "options": [
                {"label": "GPT-5 Mini", "value": "gpt-5-mini"},
                {"label": "gpt-4.1-mini", "value": "gpt-4.1-mini"},
            ],
            "placeholder": "Search models or enter a model ID",
            "custom_value": {
                "enabled": True,
                "pattern": r"^[^\s]+$",
                "option_label": "Use '{value}' as a custom model ID",
            },
            "placements": ["composer"],
            "default_pinned": True,
            "icon": "cpu",
        },
    }
    assert elements[1] == {
        "ui_type": "config",
        "type": "select",
        "key": "auth_mode",
        "label": "OpenAI auth mode",
        "options": [
            {"value": "api", "label": "API"},
            {"value": "chatgpt", "label": "ChatGPT"},
            {"value": "auto", "label": "Auto"},
        ],
        "default": "api",
    }
    assert elements[2] == {
        "ui_type": "config",
        "type": "checkbox",
        "key": "enable_terminal_error_retries",
        "label": "Retry on terminal stream errors",
    }
    assert elements[3] == {
        "ui_type": "config",
        "type": "number",
        "key": "terminal_error_max_retries",
        "label": "Terminal error max retries",
    }
    assert elements[4] == {
        "ui_type": "composer_attachment",
        "key": "openai_responses:attachment:image",
        "attachment_type": "image",
        "attachment_action_plugin": "openai_responses_attachments",
        "supports_url": True,
        "supported_file_types": ["png", "jpg", "jpeg", "webp", "gif"],
        "display_placement": "below",
        "label": "Image",
        "icon": "image",
    }


def test_get_ui_elements_keeps_custom_dropdown_when_models_are_unavailable() -> None:
    provider = OpenAIResponsesProvider()

    elements = provider.get_ui_elements(config={}, tags=["openai_responses"], models=[])

    assert elements[0] == {
        "ui_type": "config",
        "type": "dropdown",
        "key": "model",
        "label": "OpenAI Model",
        "options": [],
        "placeholder": "Search models or enter a model ID",
        "custom_value": {
            "enabled": True,
            "pattern": r"^[^\s]+$",
            "option_label": "Use '{value}' as a custom model ID",
        },
        "rich_ui": {
            "kind": "dropdown",
            "label": "Model",
            "show_label": False,
            "options": [],
            "placeholder": "Search models or enter a model ID",
            "custom_value": {
                "enabled": True,
                "pattern": r"^[^\s]+$",
                "option_label": "Use '{value}' as a custom model ID",
            },
            "placements": ["composer"],
            "default_pinned": True,
            "icon": "cpu",
        },
    }
    assert elements[1]["ui_type"] == "config"
    assert elements[1]["key"] == "auth_mode"
    assert elements[2]["ui_type"] == "config"
    assert elements[2]["key"] == "enable_terminal_error_retries"
    assert elements[3]["ui_type"] == "config"
    assert elements[3]["key"] == "terminal_error_max_retries"
    assert elements[4]["ui_type"] == "composer_attachment"


def test_init_uses_env_api_key_when_not_in_config(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
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


def test_call_api_uses_request_instructions() -> None:
    provider = OpenAIResponsesProvider()
    fixture_client = _FixtureClient(_load_fixture())
    native_messages = provider.to_native_messages(
        [{"role": "user", "content": "hello"}],
        {},
    )
    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 42,
        },
        "client": fixture_client,
        "request": {
            "url": "https://api.openai.com/v1/responses",
            "payload": {"model": "gpt-5-mini"},
            "headers": {
                "Authorization": "Bearer test_key",
                "Content-Type": "application/json",
            },
            "timeout": 42.0,
            "instructions": "Compiled system instructions",
        },
    }

    provider.call_api(native_messages, state)

    assert fixture_client.responses.calls
    assert (
        fixture_client.responses.calls[0]["instructions"]
        == "Compiled system instructions"
    )


def test_call_api_can_strip_leading_system_message_from_request_history() -> None:
    provider = OpenAIResponsesProvider()
    fixture_client = _FixtureClient(_load_fixture())
    native_messages = provider.to_native_messages(
        [
            {"role": "system", "content": "Legacy system prompt"},
            {"role": "user", "content": "hello"},
        ],
        {},
    )
    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 42,
            "strip_leading_system_or_developer_message": True,
        },
        "client": fixture_client,
        "request": {
            "url": "https://api.openai.com/v1/responses",
            "payload": {"model": "gpt-5-mini"},
            "headers": {
                "Authorization": "Bearer test_key",
                "Content-Type": "application/json",
            },
            "timeout": 42.0,
            "instructions": "Compiled system instructions",
        },
    }

    provider.call_api(native_messages, state)

    sent_input = fixture_client.responses.calls[0]["input"]
    assert len(sent_input) == 1
    assert sent_input[0]["role"] == "user"


def test_api_mode_keeps_leading_system_message_without_strip_flag() -> None:
    provider = OpenAIResponsesProvider()
    fixture_client = _FixtureClient(_load_fixture())
    native_messages = provider.to_native_messages(
        [
            {"role": "system", "content": "Visible system prompt"},
            {"role": "user", "content": "hello"},
        ],
        {},
    )
    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 42,
        },
        "client": fixture_client,
        "request": {
            "url": "https://api.openai.com/v1/responses",
            "payload": {"model": "gpt-5-mini"},
            "headers": {
                "Authorization": "Bearer test_key",
                "Content-Type": "application/json",
            },
            "timeout": 42.0,
        },
    }

    provider.call_api(native_messages, state)

    call = fixture_client.responses.calls[0]
    assert "instructions" not in call
    assert [item["role"] for item in call["input"]] == ["system", "user"]


def test_chatgpt_stream_moves_leading_system_message_to_instructions() -> None:
    provider = OpenAIResponsesProvider()
    fixture_client = _FixtureStreamingClient(_load_stream_fixture_events())
    native_messages = provider.to_native_messages(
        [
            {"role": "system", "content": "Visible system prompt"},
            {"role": "user", "content": "hello"},
        ],
        {},
    )
    original_native = list(native_messages)
    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 42,
            "_openai_responses_effective_auth_mode": "chatgpt",
        },
        "client": fixture_client,
        "request": {
            "url": "https://chatgpt.com/backend-api/codex/responses",
            "payload": {"model": "gpt-5-mini"},
            "headers": {
                "Authorization": "Bearer test_key",
                "Content-Type": "application/json",
            },
            "timeout": 42.0,
        },
    }

    list(provider.stream_api(native_messages, state))

    call = fixture_client.responses.calls[0]
    assert call["instructions"] == "Visible system prompt"
    assert [item["role"] for item in call["input"]] == ["user"]
    assert native_messages == original_native


def test_chatgpt_stream_moves_leading_developer_message_to_instructions() -> None:
    provider = OpenAIResponsesProvider()
    fixture_client = _FixtureStreamingClient(_load_stream_fixture_events())
    native_messages = provider.to_native_messages(
        [
            {"role": "developer", "content": "Visible developer prompt"},
            {"role": "user", "content": "hello"},
        ],
        {},
    )
    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 42,
            "_openai_responses_effective_auth_mode": "chatgpt",
        },
        "client": fixture_client,
        "request": {
            "url": "https://chatgpt.com/backend-api/codex/responses",
            "payload": {"model": "gpt-5-mini"},
            "headers": {
                "Authorization": "Bearer test_key",
                "Content-Type": "application/json",
            },
            "timeout": 42.0,
        },
    }

    list(provider.stream_api(native_messages, state))

    call = fixture_client.responses.calls[0]
    assert call["instructions"] == "Visible developer prompt"
    assert [item["role"] for item in call["input"]] == ["user"]


def test_chatgpt_stream_preserves_existing_request_instructions() -> None:
    provider = OpenAIResponsesProvider()
    fixture_client = _FixtureStreamingClient(_load_stream_fixture_events())
    native_messages = provider.to_native_messages(
        [
            {"role": "system", "content": "Visible system prompt"},
            {"role": "user", "content": "hello"},
        ],
        {},
    )
    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 42,
            "_openai_responses_effective_auth_mode": "chatgpt",
        },
        "client": fixture_client,
        "request": {
            "url": "https://chatgpt.com/backend-api/codex/responses",
            "payload": {"model": "gpt-5-mini"},
            "headers": {
                "Authorization": "Bearer test_key",
                "Content-Type": "application/json",
            },
            "timeout": 42.0,
            "instructions": "Explicit instructions",
        },
    }

    list(provider.stream_api(native_messages, state))

    call = fixture_client.responses.calls[0]
    assert call["instructions"] == "Explicit instructions"
    assert [item["role"] for item in call["input"]] == ["system", "user"]


def test_runtime_extracts_leading_system_text_from_responses_parts() -> None:
    native_messages = [
        {
            "type": "message",
            "role": "system",
            "content": [
                {"type": "input_text", "text": "First"},
                {"type": "input_image", "image_url": "data:image/png;base64,AAA"},
                {"type": "text", "text": "Second"},
            ],
        },
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "hello"}],
        },
    ]

    prepared = runtime_module.prepare_input_and_instructions_for_endpoint(
        native_messages,
        None,
        {"_openai_responses_effective_auth_mode": "chatgpt"},
    )

    assert prepared.instructions == "First\nSecond"
    assert prepared.input_items == [native_messages[1]]
    assert prepared.stripped_leading_message == native_messages[0]


def test_stream_api_can_strip_leading_developer_message_from_request_history() -> None:
    provider = OpenAIResponsesProvider()
    fixture_client = _FixtureStreamingClient(_load_stream_fixture_events())
    native_messages = provider.to_native_messages(
        [
            {"role": "developer", "content": "Legacy developer prompt"},
            {"role": "user", "content": "hello"},
        ],
        {},
    )
    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 42,
            "strip_leading_system_or_developer_message": True,
        },
        "client": fixture_client,
        "request": {
            "url": "https://api.openai.com/v1/responses",
            "payload": {"model": "gpt-5-mini"},
            "headers": {
                "Authorization": "Bearer test_key",
                "Content-Type": "application/json",
            },
            "timeout": 42.0,
            "instructions": "Compiled system instructions",
        },
    }

    list(provider.stream_api(native_messages, state))

    sent_input = fixture_client.responses.calls[0]["input"]
    assert len(sent_input) == 1
    assert sent_input[0]["role"] == "user"


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
            "content": '{"ok": true}',
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
    assert native[1]["content"] == [{"type": "output_text", "text": "working"}]
    assert native[1]["phase"] == "commentary"

    assert native[2]["type"] == "function_call_output"
    assert native[2]["call_id"] == "call_123"
    assert native[2]["output"] == '{"ok": true}'
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
    assert rebuilt[2]["content"] == '{"ok": true}'
    assert rebuilt[2]["metadata"]["tool_call_id"] == "call_123"
    assert rebuilt[2]["metadata"]["trace_id"] == "t1"
    assert rebuilt[2]["metadata"]["native_indices"] == [2]


def test_to_native_messages_supports_image_url_and_data_url() -> None:
    provider = OpenAIResponsesProvider()

    native = provider.to_native_messages(
        [
            {
                "role": "user",
                "content": "describe these",
                "multipartContent": [
                    {
                        "type": "image",
                        "content": {"url": "https://example.com/cat.png"},
                        "metadata": {},
                    },
                    {
                        "type": "image",
                        "content": {"url": "data:image/png;base64,Zm9v"},
                        "metadata": {},
                    },
                ],
            }
        ],
        {},
    )

    assert native == [
        {
            "type": "message",
            "role": "user",
            "content": [
                {"type": "input_text", "text": "describe these"},
                {"type": "input_image", "image_url": "https://example.com/cat.png"},
                {"type": "input_image", "image_url": "data:image/png;base64,Zm9v"},
            ],
            "_metadata": {
                "_openai_responses_attachment_sources": [
                    {
                        "content_index": 1,
                        "multipart_part": {
                            "type": "image",
                            "content": {"url": "https://example.com/cat.png"},
                            "metadata": {},
                        },
                    },
                    {
                        "content_index": 2,
                        "multipart_part": {
                            "type": "image",
                            "content": {"url": "data:image/png;base64,Zm9v"},
                            "metadata": {},
                        },
                    },
                ]
            },
        }
    ]


def test_to_native_messages_uses_tool_result_without_metadata_duplication() -> None:
    provider = OpenAIResponsesProvider()
    image_item = {
        "type": "input_image",
        "image_url": "data:image/png;base64,AAA",
        "detail": "high",
    }
    payload = make_provider_native_tool_result(
        format=FORMAT_OPENAI_RESPONSES,
        output=[image_item],
        text='{"image_url":"data:image/png;base64,AAA"}',
    )

    native = provider.to_native_messages(
        [
            {
                "role": "tool",
                "content": '{"image_url":"data:image/png;base64,AAA"}',
                TOOL_RESULT_FIELD: payload,
                "metadata": {
                    "tool_call_id": "call_view_1",
                    "trace_id": "t1",
                },
            }
        ],
        {},
    )

    assert native == [
        {
            "type": "function_call_output",
            "call_id": "call_view_1",
            "output": [image_item],
            "_metadata": {
                "trace_id": "t1",
            },
        }
    ]


def test_to_native_messages_uses_openai_responses_tool_result_envelope() -> None:
    provider = OpenAIResponsesProvider()
    image_item = {"type": "input_image", "image_url": "data:image/png;base64,AAA"}
    payload = make_provider_native_tool_result(
        format=FORMAT_OPENAI_RESPONSES,
        output=[
            {"type": "input_text", "text": "<image>"},
            image_item,
            {"type": "input_text", "text": "</image>"},
        ],
    )

    native = provider.to_native_messages(
        [
            {
                "role": "tool",
                "content": "opened image",
                TOOL_RESULT_FIELD: payload,
                "metadata": {"tool_call_id": "call_view_1"},
            }
        ],
        {},
    )

    assert native == [
        {
            "type": "function_call_output",
            "call_id": "call_view_1",
            "output": payload["output"],
        }
    ]


def test_to_native_messages_converts_openai_chat_tool_result_envelope() -> None:
    provider = OpenAIResponsesProvider()
    payload = make_provider_native_tool_result(
        format=FORMAT_OPENAI_CHAT_COMPLETIONS,
        content=[
            {"type": "text", "text": "<image>"},
            {
                "type": "image_url",
                "image_url": {"url": "data:image/png;base64,AAA"},
            },
            {"type": "text", "text": "</image>"},
        ],
    )

    native = provider.to_native_messages(
        [
            {
                "role": "tool",
                "content": "opened image",
                TOOL_RESULT_FIELD: payload,
                "metadata": {"tool_call_id": "call_view_1"},
            }
        ],
        {},
    )

    assert native[0]["type"] == "function_call_output"
    assert native[0]["call_id"] == "call_view_1"
    assert native[0]["output"] == [
        {"type": "input_text", "text": "<image>"},
        {"type": "input_image", "image_url": "data:image/png;base64,AAA"},
        {"type": "input_text", "text": "</image>"},
    ]


def test_to_native_messages_converts_image_data_base64_to_data_url() -> None:
    provider = OpenAIResponsesProvider()

    native = provider.to_native_messages(
        [
            {
                "role": "user",
                "content": "what is this",
                "multipartContent": [
                    {
                        "type": "image",
                        "content": {
                            "data_base64": "YWJjMTIz",
                            "mime_type": "image/png",
                            "filename": "tiny.png",
                        },
                        "metadata": {},
                    }
                ],
            }
        ],
        {},
    )

    assert native == [
        {
            "type": "message",
            "role": "user",
            "content": [
                {"type": "input_text", "text": "what is this"},
                {"type": "input_image", "image_url": "data:image/png;base64,YWJjMTIz"},
            ],
            "_metadata": {
                "_openai_responses_attachment_sources": [
                    {
                        "content_index": 1,
                        "multipart_part": {
                            "type": "image",
                            "content": {
                                "data_base64": "YWJjMTIz",
                                "mime_type": "image/png",
                                "filename": "tiny.png",
                            },
                            "metadata": {},
                        },
                    }
                ]
            },
        }
    ]


def test_to_native_messages_raises_for_image_data_base64_without_mime_type() -> None:
    provider = OpenAIResponsesProvider()

    with pytest.raises(ValueError, match="requires mime_type"):
        provider.to_native_messages(
            [
                {
                    "role": "user",
                    "content": "broken",
                    "multipartContent": [
                        {
                            "type": "image",
                            "content": {"data_base64": "YWJjMTIz"},
                            "metadata": {},
                        }
                    ],
                }
            ],
            {},
        )


def test_to_native_messages_adds_pdf_input_file_when_upload_mode_enabled() -> None:
    provider = OpenAIResponsesProvider()

    native = provider.to_native_messages(
        [
            {
                "role": "user",
                "content": "read this pdf",
                "multipartContent": [
                    {
                        "type": "pdf",
                        "content": {
                            "data_base64": "JVBERi0xLjQK",
                            "mime_type": "application/pdf",
                            "filename": "brief.pdf",
                        },
                        "metadata": {},
                    }
                ],
            }
        ],
        {
            "openai_responses_attachments": {
                "attachment_upload_mode": "upload_before_send"
            }
        },
    )

    assert native == [
        {
            "type": "message",
            "role": "user",
            "content": [
                {"type": "input_text", "text": "read this pdf"},
                {
                    "type": "input_file",
                    "file_data": "JVBERi0xLjQK",
                    "filename": "brief.pdf",
                },
            ],
            "_metadata": {
                "_openai_responses_attachment_sources": [
                    {
                        "content_index": 1,
                        "multipart_part": {
                            "type": "pdf",
                            "content": {
                                "data_base64": "JVBERi0xLjQK",
                                "mime_type": "application/pdf",
                                "filename": "brief.pdf",
                            },
                            "metadata": {},
                        },
                    }
                ]
            },
        }
    ]


def test_to_native_messages_accepts_pdf_without_visible_upload_toggle() -> None:
    provider = OpenAIResponsesProvider()

    native = provider.to_native_messages(
        [
            {
                "role": "user",
                "content": "read this pdf",
                "multipartContent": [
                    {
                        "type": "pdf",
                        "content": {
                            "data_base64": "JVBERi0xLjQK",
                            "mime_type": "application/pdf",
                            "filename": "brief.pdf",
                        },
                        "metadata": {},
                    }
                ],
            }
        ],
        {},
    )

    assert native[0]["content"][1] == {
        "type": "input_file",
        "file_data": "JVBERi0xLjQK",
        "filename": "brief.pdf",
    }


def test_attachment_modes_normalize_legacy_direct_to_inline_images() -> None:
    provider = OpenAIResponsesProvider()

    mode = provider._image_attachment_mode(
        {"config": {"attachment_upload_mode": "direct"}}
    )

    assert mode == "inline"
    assert provider._attachment_upload_mode(
        {"config": {"attachment_upload_mode": "direct"}}
    ) == ("upload_before_send")


def test_from_native_messages_preserves_image_multipart_content() -> None:
    provider = OpenAIResponsesProvider()

    rebuilt = provider.from_native_messages(
        [
            {
                "type": "message",
                "role": "assistant",
                "content": [
                    {"type": "output_text", "text": "here you go"},
                    {"type": "input_image", "image_url": "data:image/png;base64,Zm9v"},
                ],
                "_metadata": {"response_id": "resp_img_1"},
            }
        ],
        {},
    )

    assert rebuilt == [
        {
            "role": "assistant",
            "content": "here you go",
            "metadata": {
                "response_id": "resp_img_1",
                "native_indices": [0],
                "phase_messages": [
                    {
                        "content": "here you go",
                        "native_index": 0,
                        "multipartContent": [
                            {
                                "type": "image",
                                "content": {"url": "data:image/png;base64,Zm9v"},
                                "metadata": {},
                            }
                        ],
                    }
                ],
            },
            "multipartContent": [
                {
                    "type": "image",
                    "content": {"url": "data:image/png;base64,Zm9v"},
                    "metadata": {},
                }
            ],
        }
    ]


def test_from_native_messages_preserves_uploaded_attachment_sources() -> None:
    provider = OpenAIResponsesProvider()

    rebuilt = provider.from_native_messages(
        [
            {
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "see both"},
                    {"type": "input_image", "file_id": "file_img_1"},
                    {"type": "input_file", "file_id": "file_pdf_1"},
                ],
                "_metadata": {
                    "_openai_responses_attachment_sources": [
                        {
                            "content_index": 1,
                            "multipart_part": {
                                "type": "image",
                                "content": {
                                    "url": "data:image/png;base64,Zm9v",
                                    "mime_type": "image/png",
                                    "filename": "image.png",
                                },
                                "metadata": {},
                            },
                        },
                        {
                            "content_index": 2,
                            "multipart_part": {
                                "type": "pdf",
                                "content": {
                                    "data_base64": "JVBERi0xLjQK",
                                    "mime_type": "application/pdf",
                                    "filename": "brief.pdf",
                                },
                                "metadata": {},
                            },
                        },
                    ]
                },
            }
        ],
        {},
    )

    assert rebuilt == [
        {
            "role": "user",
            "content": "see both",
            "metadata": {"native_indices": [0]},
            "multipartContent": [
                {
                    "type": "image",
                    "content": {
                        "url": "data:image/png;base64,Zm9v",
                        "mime_type": "image/png",
                        "filename": "image.png",
                    },
                    "metadata": {},
                },
                {
                    "type": "pdf",
                    "content": {
                        "data_base64": "JVBERi0xLjQK",
                        "mime_type": "application/pdf",
                        "filename": "brief.pdf",
                    },
                    "metadata": {},
                },
            ],
        }
    ]


def test_from_native_messages_assigns_response_segment_indices_for_unconverted_items() -> (
    None
):
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


def test_from_native_messages_collapses_commentary_and_empty_final_answer_into_one_assistant() -> (
    None
):
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
            "phase": "commentary",
            "content": [{"type": "output_text", "text": "working"}],
            "_metadata": {"response_id": "resp_1", "trace_id": "commentary"},
        },
        {
            "type": "message",
            "role": "assistant",
            "phase": "final_answer",
            "content": [],
            "_metadata": {"response_id": "resp_1", "trace_id": "final"},
        },
    ]

    rebuilt = provider.from_native_messages(native_messages, {})

    assistants = [msg for msg in rebuilt if msg.get("role") == "assistant"]
    assert len(assistants) == 1
    assistant = assistants[0]
    assert assistant["content"] == "working"

    md = assistant.get("metadata") or {}
    assert md.get("response_id") == "resp_1"
    assert md.get("native_indices") == [0, 1, 2]
    assert md.get("phase") == "commentary"

    phase_messages = md.get("phase_messages") or []
    assert len(phase_messages) == 2
    assert phase_messages[0]["phase"] == "commentary"
    assert phase_messages[0]["content"] == "working"
    assert phase_messages[1]["phase"] == "final_answer"
    assert phase_messages[1]["content"] == ""


def test_from_native_messages_collapses_reasoning_and_function_call_into_one_assistant_anchor() -> (
    None
):
    provider = OpenAIResponsesProvider()
    tools_ext = OpenAIResponsesToolsExtension()

    native_messages = [
        {
            "type": "reasoning",
            "summary": [{"type": "summary_text", "text": "thinking"}],
            "_metadata": {"response_id": "resp_2"},
        },
        {
            "type": "function_call",
            "call_id": "call_1",
            "name": "lookup",
            "arguments": '{"id":1}',
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
    rebuilt = tools_ext.from_native_messages(native_messages, rebuilt)

    assistants = [msg for msg in rebuilt if msg.get("role") == "assistant"]
    assert len(assistants) == 1
    assistant = assistants[0]
    assert assistant["content"] == "Calling tool"

    md = assistant.get("metadata") or {}
    assert md.get("response_id") == "resp_2"
    assert md.get("native_indices") == [0, 1, 2]
    tool_calls = md.get("tool_calls") or []
    assert len(tool_calls) == 1
    assert tool_calls[0]["id"] == "call_1"
    assert (tool_calls[0].get("function") or {}).get("name") == "lookup"


def test_from_native_messages_preserves_phase_messages_when_final_and_tool_call_share_segment() -> (
    None
):
    provider = OpenAIResponsesProvider()

    native_messages = [
        {
            "type": "reasoning",
            "summary": [{"type": "summary_text", "text": "thinking"}],
            "_metadata": {"response_id": "resp_3"},
        },
        {
            "type": "message",
            "role": "assistant",
            "phase": "commentary",
            "content": [{"type": "output_text", "text": "working"}],
            "_metadata": {"response_id": "resp_3"},
        },
        {
            "type": "message",
            "role": "assistant",
            "phase": "final_answer",
            "content": [{"type": "output_text", "text": "done"}],
            "_metadata": {"response_id": "resp_3"},
        },
        {
            "type": "function_call",
            "call_id": "call_3",
            "name": "lookup",
            "arguments": "{}",
            "_metadata": {"response_id": "resp_3"},
        },
    ]

    rebuilt = provider.from_native_messages(native_messages, {})

    assistants = [msg for msg in rebuilt if msg.get("role") == "assistant"]
    assert len(assistants) == 1
    assistant = assistants[0]
    assert assistant["content"] == "done"

    md = assistant.get("metadata") or {}
    assert md.get("phase") == "final_answer"
    assert md.get("native_indices") == [0, 1, 2, 3]
    phase_messages = md.get("phase_messages") or []
    assert [entry.get("phase") for entry in phase_messages] == [
        "commentary",
        "final_answer",
    ]
    assert [entry.get("content") for entry in phase_messages] == ["working", "done"]


def test_from_native_messages_assigns_tool_call_indices_without_tool_calls_metadata() -> (
    None
):
    provider = OpenAIResponsesProvider()

    native_messages = [
        {
            "type": "function_call",
            "call_id": "call_1",
            "name": "lookup",
            "arguments": '{"id":1}',
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
    assert call_kwargs["timeout"] == 12.0


def test_call_api_strips_output_only_fields_from_input_history() -> None:
    provider = OpenAIResponsesProvider()
    fixture = _load_fixture()
    fake_client = _FixtureClient(fixture)

    input_items = [
        {
            "type": "function_call",
            "call_id": "call_123",
            "name": "add",
            "arguments": '{"a": 1, "b": 2}',
            "id": "fc_123",
            "status": "completed",
            "namespace": None,
            "_metadata": {"response_id": "resp_1"},
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

    provider.call_api(input_items, state)

    sent_item = fake_client.responses.calls[0]["input"][0]
    assert sent_item == {
        "type": "function_call",
        "call_id": "call_123",
        "name": "add",
        "arguments": '{"a": 1, "b": 2}',
    }


def test_call_api_normalizes_assistant_input_text_history_to_output_text() -> None:
    provider = OpenAIResponsesProvider()
    fixture = _load_fixture()
    fake_client = _FixtureClient(fixture)

    input_items = [
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "input_text", "text": "legacy assistant text"}],
            "phase": "commentary",
            "_metadata": {"response_id": "resp_legacy"},
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

    provider.call_api(input_items, state)

    sent_item = fake_client.responses.calls[0]["input"][0]
    assert sent_item == {
        "type": "message",
        "role": "assistant",
        "content": [{"type": "output_text", "text": "legacy assistant text"}],
    }


def test_call_api_upload_mode_rewrites_inline_image_and_pdf_before_send() -> None:
    provider = OpenAIResponsesProvider()
    fixture = _load_fixture()
    fake_client = _UploadFixtureClient(fixture)

    input_items = [
        {
            "type": "message",
            "role": "user",
            "content": [
                {"type": "input_text", "text": "see attachments"},
                {"type": "input_image", "image_url": "data:image/png;base64,Zm9v"},
                {
                    "type": "input_file",
                    "file_data": "JVBERi0xLjQK",
                    "filename": "brief.pdf",
                },
            ],
            "_metadata": {
                "_openai_responses_attachment_sources": [
                    {
                        "content_index": 1,
                        "multipart_part": {
                            "type": "image",
                            "content": {
                                "url": "data:image/png;base64,Zm9v",
                                "mime_type": "image/png",
                                "filename": "pixel.png",
                            },
                            "metadata": {},
                        },
                    },
                    {
                        "content_index": 2,
                        "multipart_part": {
                            "type": "pdf",
                            "content": {
                                "data_base64": "JVBERi0xLjQK",
                                "mime_type": "application/pdf",
                                "filename": "brief.pdf",
                            },
                            "metadata": {},
                        },
                    },
                ]
            },
        }
    ]

    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 12,
        },
        "openai_responses_attachments": {
            "attachment_upload_mode": "upload_before_send",
            "image_attachment_mode": "upload",
        },
        "client": fake_client,
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 12,
        },
    }

    _partials, _finals, full_native, new_state = provider.call_api(input_items, state)

    sent_content = fake_client.responses.calls[0]["input"][0]["content"]
    assert sent_content == [
        {"type": "input_text", "text": "see attachments"},
        {"type": "input_image", "file_id": "file_1"},
        {"type": "input_file", "file_id": "file_2"},
    ]
    assert len(fake_client.files.calls) == 2
    assert fake_client.files.calls[0]["purpose"] == "vision"
    assert fake_client.files.calls[1]["purpose"] == "user_data"

    stored_input = full_native[0]
    assert stored_input["content"][1] == {
        "type": "input_image",
        "image_url": "data:image/png;base64,Zm9v",
    }
    assert stored_input["content"][2] == {
        "type": "input_file",
        "file_data": "JVBERi0xLjQK",
        "filename": "brief.pdf",
    }
    assert (
        stored_input["_metadata"]["_openai_responses_attachment_sources"][0][
            "multipart_part"
        ]["type"]
        == "image"
    )
    assert (
        stored_input["_metadata"]["_openai_responses_attachment_sources"][1][
            "multipart_part"
        ]["type"]
        == "pdf"
    )
    assert stored_input["_metadata"]["_openai_responses_uploaded_attachments"] == [
        {
            "content_index": 1,
            "uploaded_part": {"type": "input_image", "file_id": "file_1"},
        },
        {
            "content_index": 2,
            "uploaded_part": {"type": "input_file", "file_id": "file_2"},
        },
    ]
    assert new_state["_openai_responses_upload_cache"]


def test_call_api_upload_mode_reuses_cached_upload_for_request_and_history() -> None:
    provider = OpenAIResponsesProvider()
    fixture = _load_fixture()
    fake_client = _UploadFixtureClient(fixture)

    input_items = [
        {
            "type": "message",
            "role": "user",
            "content": [
                {"type": "input_text", "text": "see image"},
                {"type": "input_image", "image_url": "data:image/png;base64,Zm9v"},
            ],
            "_metadata": {
                "_openai_responses_attachment_sources": [
                    {
                        "content_index": 1,
                        "multipart_part": {
                            "type": "image",
                            "content": {
                                "url": "data:image/png;base64,Zm9v",
                                "mime_type": "image/png",
                                "filename": "pixel.png",
                            },
                            "metadata": {},
                        },
                    }
                ]
            },
        }
    ]

    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 12,
        },
        "openai_responses_attachments": {
            "attachment_upload_mode": "upload_before_send",
            "image_attachment_mode": "upload",
        },
        "client": fake_client,
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 12,
        },
    }

    provider.call_api(input_items, state)

    assert len(fake_client.files.calls) == 1


def test_call_api_leaves_inline_images_direct_when_image_mode_is_inline() -> None:
    provider = OpenAIResponsesProvider()
    fixture = _load_fixture()
    fake_client = _UploadFixtureClient(fixture)

    input_items = [
        {
            "type": "message",
            "role": "user",
            "content": [
                {"type": "input_text", "text": "see image"},
                {"type": "input_image", "image_url": "data:image/png;base64,Zm9v"},
            ],
            "_metadata": {
                "_openai_responses_attachment_sources": [
                    {
                        "content_index": 1,
                        "multipart_part": {
                            "type": "image",
                            "content": {
                                "url": "data:image/png;base64,Zm9v",
                                "mime_type": "image/png",
                                "filename": "pixel.png",
                            },
                            "metadata": {},
                        },
                    }
                ]
            },
        }
    ]

    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 12,
        },
        "openai_responses_attachments": {
            "attachment_upload_mode": "upload_before_send",
            "image_attachment_mode": "inline",
        },
        "client": fake_client,
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 12,
        },
    }

    provider.call_api(input_items, state)

    assert fake_client.files.calls == []
    assert fake_client.responses.calls[0]["input"][0]["content"][1] == {
        "type": "input_image",
        "image_url": "data:image/png;base64,Zm9v",
    }


def test_to_native_messages_resolves_session_asset_refs_to_inline_parts(
    tmp_path: Path,
) -> None:
    provider = OpenAIResponsesProvider()
    asset_store = FilesystemSessionAssetStore(tmp_path / "session_assets")
    image_record = asset_store.store_base64(
        session_id="sess_asset",
        attachment_type="image",
        filename="square.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"image-bytes").decode("ascii"),
    )
    pdf_record = asset_store.store_base64(
        session_id="sess_asset",
        attachment_type="pdf",
        filename="brief.pdf",
        mime_type="application/pdf",
        data_base64=base64.b64encode(b"pdf-bytes").decode("ascii"),
    )

    native = provider.to_native_messages(
        [
            {
                "role": "user",
                "content": "review these",
                "multipartContent": [
                    {
                        "type": "image",
                        "content": {
                            "asset_ref": image_record.asset_ref(),
                            "filename": image_record.filename,
                            "mime_type": image_record.mime_type,
                        },
                        "metadata": {},
                    },
                    {
                        "type": "pdf",
                        "content": {
                            "asset_ref": pdf_record.asset_ref(),
                            "filename": pdf_record.filename,
                            "mime_type": pdf_record.mime_type,
                        },
                        "metadata": {},
                    },
                ],
            }
        ],
        {
            "config": {
                "model": "gpt-5-mini",
                "api_key": "test_key",
                "base_url": "https://api.openai.com/v1",
                "timeout": 12,
                "_session_asset_store": asset_store,
            },
            "openai_responses_attachments": {
                "attachment_upload_mode": "upload_before_send",
                "image_attachment_mode": "inline",
            },
        },
    )

    assert native == [
        {
            "type": "message",
            "role": "user",
            "content": [
                {"type": "input_text", "text": "review these"},
                {
                    "type": "input_image",
                    "image_url": "data:image/png;base64,"
                    + base64.b64encode(b"image-bytes").decode("ascii"),
                },
                {
                    "type": "input_file",
                    "file_data": base64.b64encode(b"pdf-bytes").decode("ascii"),
                    "filename": "brief.pdf",
                },
            ],
            "_metadata": {
                "_openai_responses_attachment_sources": [
                    {
                        "content_index": 1,
                        "multipart_part": {
                            "type": "image",
                            "content": {
                                "asset_ref": image_record.asset_ref(),
                                "filename": "square.png",
                                "mime_type": "image/png",
                            },
                            "metadata": {},
                        },
                    },
                    {
                        "content_index": 2,
                        "multipart_part": {
                            "type": "pdf",
                            "content": {
                                "asset_ref": pdf_record.asset_ref(),
                                "filename": "brief.pdf",
                                "mime_type": "application/pdf",
                            },
                            "metadata": {},
                        },
                    },
                ]
            },
        }
    ]


def test_call_api_upload_mode_uses_cached_session_asset_provider_ref_without_reupload(
    tmp_path: Path,
) -> None:
    provider = OpenAIResponsesProvider()
    fixture = _load_fixture()
    fake_client = _UploadFixtureClient(fixture)
    asset_store = FilesystemSessionAssetStore(tmp_path / "session_assets")
    image_record = asset_store.store_base64(
        session_id="sess_asset",
        attachment_type="image",
        filename="square.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"image-bytes").decode("ascii"),
        provider_refs={
            "openai_responses": {
                "status": "uploaded",
                "file_id": "file_existing",
                "purpose": "vision",
                "filename": "square.png",
                "mime_type": "image/png",
            }
        },
    )

    input_items = provider.to_native_messages(
        [
            {
                "role": "user",
                "content": "review image",
                "multipartContent": [
                    {
                        "type": "image",
                        "content": {
                            "asset_ref": image_record.asset_ref(),
                            "filename": image_record.filename,
                            "mime_type": image_record.mime_type,
                        },
                        "metadata": {},
                    }
                ],
            }
        ],
        {
            "config": {
                "model": "gpt-5-mini",
                "api_key": "test_key",
                "base_url": "https://api.openai.com/v1",
                "timeout": 12,
                "_session_asset_store": asset_store,
            },
            "openai_responses_attachments": {
                "attachment_upload_mode": "upload_before_send"
            },
        },
    )

    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 12,
            "_session_asset_store": asset_store,
        },
        "openai_responses_attachments": {
            "attachment_upload_mode": "upload_before_send",
            "image_attachment_mode": "upload",
        },
        "client": fake_client,
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 12,
        },
    }

    provider.call_api(input_items, state)

    sent_content = fake_client.responses.calls[0]["input"][0]["content"]
    assert sent_content == [
        {"type": "input_text", "text": "review image"},
        {"type": "input_image", "file_id": "file_existing"},
    ]
    assert fake_client.files.calls == []
    assert (
        asset_store.load("sess_asset", image_record.asset_id).provider_refs
        == image_record.provider_refs
    )


def test_call_api_upload_mode_reuploads_session_asset_when_cached_ref_is_rejected(
    tmp_path: Path,
) -> None:
    provider = OpenAIResponsesProvider()
    fixture = _load_fixture()
    fake_client = _RetryOnceUploadFixtureClient(fixture)
    asset_store = FilesystemSessionAssetStore(tmp_path / "session_assets")
    image_record = asset_store.store_base64(
        session_id="sess_asset",
        attachment_type="image",
        filename="square.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"image-bytes").decode("ascii"),
        provider_refs={
            "openai_responses": {
                "status": "uploaded",
                "file_id": "file_stale",
                "purpose": "vision",
                "filename": "square.png",
                "mime_type": "image/png",
            }
        },
    )

    input_items = provider.to_native_messages(
        [
            {
                "role": "user",
                "content": "review image",
                "multipartContent": [
                    {
                        "type": "image",
                        "content": {
                            "asset_ref": image_record.asset_ref(),
                            "filename": image_record.filename,
                            "mime_type": image_record.mime_type,
                        },
                        "metadata": {},
                    }
                ],
            }
        ],
        {
            "config": {
                "model": "gpt-5-mini",
                "api_key": "test_key",
                "base_url": "https://api.openai.com/v1",
                "timeout": 12,
                "_session_asset_store": asset_store,
            },
            "openai_responses_attachments": {
                "attachment_upload_mode": "upload_before_send",
                "image_attachment_mode": "upload",
            },
        },
    )

    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 12,
            "_session_asset_store": asset_store,
        },
        "openai_responses_attachments": {
            "attachment_upload_mode": "upload_before_send",
            "image_attachment_mode": "upload",
        },
        "client": fake_client,
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 12,
        },
    }

    _partials, _finals, full_native, _new_state = provider.call_api(input_items, state)

    assert len(fake_client.responses.calls) == 2
    assert fake_client.responses.calls[0]["input"][0]["content"][1] == {
        "type": "input_image",
        "file_id": "file_stale",
    }
    assert fake_client.responses.calls[1]["input"][0]["content"][1] == {
        "type": "input_image",
        "file_id": "file_1",
    }
    assert len(fake_client.files.calls) == 1
    assert fake_client.files.calls[0]["purpose"] == "vision"
    assert full_native[0]["_metadata"]["_openai_responses_uploaded_attachments"] == [
        {
            "content_index": 1,
            "uploaded_part": {"type": "input_image", "file_id": "file_1"},
        }
    ]

    updated_record = asset_store.load("sess_asset", image_record.asset_id)
    assert updated_record.provider_refs["openai_responses"]["file_id"] == "file_1"
    assert updated_record.provider_refs["openai_responses"]["purpose"] == "vision"


def test_initialize_request_does_not_upload_attachments() -> None:
    provider = OpenAIResponsesProvider()
    fake_client = _UploadFixtureClient(_load_fixture())
    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 12,
        },
        "openai_responses_attachments": {
            "attachment_upload_mode": "upload_before_send"
        },
        "client": fake_client,
    }

    native_after, new_state = provider.initialize_request(
        [
            {
                "type": "message",
                "role": "user",
                "content": [
                    {"type": "input_image", "image_url": "data:image/png;base64,Zm9v"}
                ],
            }
        ],
        state,
    )

    assert native_after == [
        {
            "type": "message",
            "role": "user",
            "content": [
                {"type": "input_image", "image_url": "data:image/png;base64,Zm9v"}
            ],
        }
    ]
    assert fake_client.files.calls == []
    assert new_state["request"]["payload"] == {"model": "gpt-5-mini"}


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
            [
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "hi"}],
                }
            ],
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
            [
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "hi"}],
                }
            ],
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
    assert call_kwargs["timeout"] == 30.0


def test_call_api_applies_request_retry_override_via_sdk_options() -> None:
    provider = OpenAIResponsesProvider()
    fixture = _load_fixture()
    fake_client = _FixtureClient(fixture)

    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 12,
        },
        "client": fake_client,
        "request": {
            "payload": {"model": "gpt-5-mini", "service_tier": "flex"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 300,
            "max_retries": 4,
        },
    }

    provider.call_api(
        [
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "hi"}],
            }
        ],
        state,
    )

    assert fake_client.option_calls == [{"timeout": 300.0, "max_retries": 4}]
    call_kwargs = fake_client.responses.calls[0]
    assert call_kwargs["service_tier"] == "flex"
    assert call_kwargs["timeout"] == 300.0


def test_stream_api_applies_request_retry_override_via_sdk_options() -> None:
    provider = OpenAIResponsesProvider()
    fake_client = _FixtureStreamingClient(_load_stream_fixture_events())

    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 30,
        },
        "client": fake_client,
        "request": {
            "payload": {"model": "gpt-5-mini", "service_tier": "flex"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 420,
            "max_retries": 2,
        },
    }

    list(
        provider.stream_api(
            [
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "hi"}],
                }
            ],
            state,
        )
    )

    assert fake_client.option_calls == [{"timeout": 420.0, "max_retries": 2}]
    call_kwargs = fake_client.responses.calls[0]
    assert call_kwargs["service_tier"] == "flex"
    assert call_kwargs["timeout"] == 420.0


def test_call_api_preserves_existing_behavior_without_retry_override() -> None:
    provider = OpenAIResponsesProvider()
    fixture = _load_fixture()
    fake_client = _FixtureClient(fixture)

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

    provider.call_api(
        [
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "hi"}],
            }
        ],
        state,
    )

    assert fake_client.option_calls == []


def test_stream_api_preserves_existing_behavior_without_retry_override() -> None:
    provider = OpenAIResponsesProvider()
    fake_client = _FixtureStreamingClient(_load_stream_fixture_events())

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

    list(
        provider.stream_api(
            [
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "hi"}],
                }
            ],
            state,
        )
    )

    assert fake_client.option_calls == []


def test_stream_api_retries_terminal_error_event_when_enabled() -> None:
    provider = OpenAIResponsesProvider()
    error_batch = [{"type": "error", "message": "simulated terminal error"}]
    success_events = _load_stream_fixture_events()
    fake_client = _SequentialStreamingClient([error_batch, success_events])

    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 30,
            "enable_terminal_error_retries": True,
            "terminal_error_max_retries": 2,
        },
        "client": fake_client,
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 30,
        },
    }

    normalized = list(
        provider.stream_api(
            [
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "hi"}],
                }
            ],
            state,
        )
    )

    assert len(fake_client.responses.calls) == 2
    assert all(isinstance(ev, dict) for ev in normalized)
    assert any(ev.get("type") == "response.output_text.delta" for ev in normalized)
    assert any(ev.get("type") == "response.completed" for ev in normalized)
    assert not any(ev.get("type") == "error" for ev in normalized)


def test_stream_api_propagates_terminal_error_event_when_retries_disabled() -> None:
    provider = OpenAIResponsesProvider()
    error_batch = [{"type": "error", "message": "simulated terminal error"}]
    fake_client = _FixtureStreamingClient(error_batch)

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

    normalized = list(
        provider.stream_api(
            [
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "hi"}],
                }
            ],
            state,
        )
    )

    assert len(fake_client.responses.calls) == 1
    assert any(ev.get("type") == "error" for ev in normalized)


def test_stream_api_propagates_terminal_error_event_when_retries_exhausted() -> None:
    provider = OpenAIResponsesProvider()
    error_batch = [{"type": "error", "message": "simulated terminal error"}]
    fake_client = _SequentialStreamingClient([error_batch, error_batch, error_batch])

    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 30,
            "enable_terminal_error_retries": True,
            "terminal_error_max_retries": 2,
        },
        "client": fake_client,
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 30,
        },
    }

    with pytest.raises(RuntimeError, match="terminal event error"):
        list(
            provider.stream_api(
                [
                    {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": "hi"}],
                    }
                ],
                state,
            )
        )

    assert len(fake_client.responses.calls) == 3


def test_stream_api_does_not_retry_terminal_error_after_visible_output() -> None:
    provider = OpenAIResponsesProvider()
    batch_with_output = [
        {"type": "response.output_text.delta", "delta": "hello"},
        {"type": "error", "message": "simulated terminal error"},
    ]
    fake_client = _FixtureStreamingClient(batch_with_output)

    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 30,
            "enable_terminal_error_retries": True,
            "terminal_error_max_retries": 2,
        },
        "client": fake_client,
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 30,
        },
    }

    normalized = list(
        provider.stream_api(
            [
                {
                    "type": "message",
                    "role": "user",
                    "content": [{"type": "input_text", "text": "hi"}],
                }
            ],
            state,
        )
    )

    assert len(fake_client.responses.calls) == 1
    assert any(ev.get("type") == "response.output_text.delta" for ev in normalized)
    assert any(ev.get("type") == "error" for ev in normalized)


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
                [
                    {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": "hi"}],
                    }
                ],
                state,
            )
        )


def test_stream_api_upload_mode_rewrites_inline_image_before_send() -> None:
    provider = OpenAIResponsesProvider()
    fake_client = _UploadStreamingFixtureClient(_load_stream_fixture_events())

    input_items = [
        {
            "type": "message",
            "role": "user",
            "content": [
                {"type": "input_text", "text": "stream image"},
                {"type": "input_image", "image_url": "data:image/png;base64,Zm9v"},
            ],
            "_metadata": {
                "_openai_responses_attachment_sources": [
                    {
                        "content_index": 1,
                        "multipart_part": {
                            "type": "image",
                            "content": {
                                "url": "data:image/png;base64,Zm9v",
                                "mime_type": "image/png",
                                "filename": "pixel.png",
                            },
                            "metadata": {},
                        },
                    }
                ]
            },
        }
    ]

    state = {
        "config": {
            "model": "gpt-5-mini",
            "api_key": "test_key",
            "base_url": "https://api.openai.com/v1",
            "timeout": 30,
        },
        "openai_responses_attachments": {
            "attachment_upload_mode": "upload_before_send",
            "image_attachment_mode": "upload",
        },
        "client": fake_client,
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 30,
        },
    }

    list(provider.stream_api(input_items, state))

    assert len(fake_client.files.calls) == 1
    sent_content = fake_client.responses.calls[0]["input"][0]["content"]
    assert sent_content == [
        {"type": "input_text", "text": "stream image"},
        {"type": "input_image", "file_id": "file_1"},
    ]


def test_process_chunk_emits_partials_and_completed_finals_only() -> None:
    provider = OpenAIResponsesProvider()
    events = _load_stream_fixture_events()

    native_messages: list[Dict[str, Any]] = []
    partials_out: list[Dict[str, Any]] = []
    finals_out: list[Dict[str, Any]] = []

    for event in events:
        partials, finals, native_messages, _state = provider.process_chunk(
            event, native_messages, {}
        )
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


def test_process_chunk_emits_reasoning_delta_as_independent_partial() -> None:
    provider = OpenAIResponsesProvider()

    partials, finals, native_messages, _state = provider.process_chunk(
        {"type": "response.reasoning_summary_text.delta", "delta": "thinking..."},
        [],
        {},
    )

    assert finals == []
    assert native_messages == []
    assert partials == [
        {"role": "assistant", "content": "", "_metadata": {"reasoning": "thinking..."}}
    ]


def test_process_chunk_keeps_stream_deltas_as_separate_chunks() -> None:
    provider = OpenAIResponsesProvider()
    events = [
        {"type": "response.output_text.delta", "delta": "A"},
        {"type": "response.output_text.delta", "delta": "B"},
        {"type": "response.reasoning.delta", "delta": "r1"},
        {"type": "response.reasoning.delta", "delta": "r2"},
    ]

    seen_partials: list[Dict[str, Any]] = []
    native_messages: list[Dict[str, Any]] = []
    state: Dict[str, Any] = {}

    for event in events:
        partials, _finals, native_messages, state = provider.process_chunk(
            event, native_messages, state
        )
        seen_partials.extend(partials)

    assert seen_partials == [
        {"role": "assistant", "content": "A"},
        {"role": "assistant", "content": "B"},
        {"role": "assistant", "content": "", "_metadata": {"reasoning": "r1"}},
        {"role": "assistant", "content": "", "_metadata": {"reasoning": "r2"}},
    ]


def test_process_chunk_raises_on_completed_event_without_output() -> None:
    provider = OpenAIResponsesProvider()

    with pytest.raises(RuntimeError, match="missing output list"):
        provider.process_chunk(
            {"type": "response.completed", "response": {"id": "resp_bad"}},
            [],
            {},
        )


def test_process_chunk_uses_accumulated_output_items_when_completed_event_omits_output() -> (
    None
):
    provider = OpenAIResponsesProvider()
    state: Dict[str, Any] = {}
    native_messages: list[Dict[str, Any]] = []

    _partials, _finals, native_messages, state = provider.process_chunk(
        {
            "type": "response.output_item.done",
            "item": {
                "type": "message",
                "role": "assistant",
                "content": [{"type": "output_text", "text": "Recovered final"}],
            },
        },
        native_messages,
        state,
    )

    _partials, finals, next_native_messages, next_state = provider.process_chunk(
        {
            "type": "response.completed",
            "response": {
                "id": "resp_missing_output",
                "usage": {"input_tokens": 1, "output_tokens": 2, "total_tokens": 3},
            },
        },
        native_messages,
        state,
    )

    assert finals == [
        {
            "type": "message",
            "role": "assistant",
            "content": [{"type": "output_text", "text": "Recovered final"}],
            "_metadata": {
                "response_id": "resp_missing_output",
                "_openai_responses_usage_raw": {
                    "input_tokens": 1,
                    "output_tokens": 2,
                    "total_tokens": 3,
                },
            },
        }
    ]
    assert next_native_messages == finals
    assert next_state["_openai_responses_stream_completed"] is True
    assert next_state["_openai_responses_stream_output_items"] == []


def test_process_chunk_raises_on_response_failed_terminal_event() -> None:
    provider = OpenAIResponsesProvider()
    events = _load_failed_stream_fixture_events()

    native_messages: list[Dict[str, Any]] = []
    state: Dict[str, Any] = {}

    for event in events[:-1]:
        _partials, _finals, native_messages, state = provider.process_chunk(
            event, native_messages, state
        )

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
        _partials, _finals, native_messages, state = provider.process_chunk(
            event, native_messages, state
        )

    final_messages, native_after_finalize, _state = provider.finalize(
        native_messages, state
    )

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


def test_send_request_stream_chatgpt_raw_completed_without_output_uses_output_item_fallback() -> (
    None
):
    core = AgentCore()
    core.register_provider(_RawChatGPTCompletedWithoutOutputProvider)

    config = {
        "model": "gpt-5-mini",
        "auth_mode": "chatgpt",
        "chatgpt_access_token": "chatgpt-access-token",
        "chatgpt_token_type": "Bearer",
        "chatgpt_account_id": "acct-123",
        "chatgpt_base_url": "https://chatgpt.example.test/backend-api/codex",
        "timeout": 30,
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with RAW_OK")

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

    assert partial_fragments == ["RAW_OK"]
    assert final_session is not None
    assert len(final_messages) == 1
    assert final_messages[0]["role"] == "assistant"
    assert final_messages[0]["content"] == "RAW_OK"
    assert final_messages[0]["metadata"]["response_id"] == "resp_chatgpt_raw_1"
    assert final_messages[0]["metadata"]["native_indices"] == [1]

    native_history = (final_session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert len(native_history) == 2
    assert native_history[0] == {
        "type": "message",
        "role": "user",
        "content": [{"type": "input_text", "text": "Reply with RAW_OK"}],
    }
    assert native_history[1]["type"] == "message"
    assert native_history[1]["role"] == "assistant"
    assert native_history[1]["content"] == [{"type": "output_text", "text": "RAW_OK"}]
    assert native_history[1]["_metadata"]["response_id"] == "resp_chatgpt_raw_1"
    assert native_history[1]["_metadata"]["_openai_responses_usage_raw"] == {
        "input_tokens": 1,
        "output_tokens": 1,
        "total_tokens": 2,
    }

    client = _RawChatGPTCompletedWithoutOutputProvider.last_client
    assert client is not None
    assert len(client.responses.with_streaming_response.calls) == 1
    assert client.responses.with_streaming_response.calls[0]["stream"] is True


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


def test_send_request_stream_recovers_premature_flex_stream_in_early_only_mode() -> (
    None
):
    core = AgentCore()
    core.register_provider(_EarlyOnlyRecoveryProvider)

    config = {
        "model": "gpt-5-mini",
        "api_key": "test_key",
        "base_url": "https://api.openai.com/v1",
        "timeout": 30,
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with STREAM_OK")

    events = list(core.send_request_stream(session, config))

    finals = [event for event in events if event.get("type") == "final"]

    assert len(finals) == 1
    assert finals[0]["messages"]

    client = _EarlyOnlyRecoveryProvider.last_client
    assert client is not None
    assert [call.get("stream") for call in client.responses.calls] == [True, True]


def test_send_request_stream_does_not_recover_visible_partials_in_early_only_mode() -> (
    None
):
    core = AgentCore()
    core.register_provider(_EarlyOnlyVisiblePartialProvider)

    config = {
        "model": "gpt-5-mini",
        "api_key": "test_key",
        "base_url": "https://api.openai.com/v1",
        "timeout": 30,
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with STREAM_OK")

    with pytest.raises(RuntimeError, match="without response.completed"):
        list(core.send_request_stream(session, config))

    client = _EarlyOnlyVisiblePartialProvider.last_client
    assert client is not None
    assert [call.get("stream") for call in client.responses.calls] == [True]


def test_send_request_stream_recovers_visible_partials_in_aggressive_mode() -> None:
    core = AgentCore()
    core.register_provider(_AggressiveRecoveryProvider)

    config = {
        "model": "gpt-5-mini",
        "api_key": "test_key",
        "base_url": "https://api.openai.com/v1",
        "timeout": 30,
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with STREAM_OK")

    events = list(core.send_request_stream(session, config))

    partials = [event for event in events if event.get("type") == "partial"]
    finals = [event for event in events if event.get("type") == "final"]

    assert partials
    assert any(partial["message"].get("content") == "partial " for partial in partials)
    assert len(finals) == 1
    assert finals[0]["messages"]

    client = _AggressiveRecoveryProvider.last_client
    assert client is not None
    assert [call.get("stream") for call in client.responses.calls] == [True, True]


def test_response_internal_metadata_preserves_service_tier() -> None:
    provider = OpenAIResponsesProvider()

    response_md = provider._response_internal_metadata(
        {"id": "resp_1", "service_tier": "flex"}
    )

    assert response_md["_openai_responses_service_tier"] == "flex"


def test_response_internal_metadata_extracts_reasoning_context() -> None:
    provider = OpenAIResponsesProvider()

    response_md = provider._response_internal_metadata(
        {
            "id": "resp_ctx_1",
            "reasoning": {"context": "all_turns"},
        }
    )

    assert response_md["_openai_responses_reasoning_context"] == "all_turns"


def test_response_internal_metadata_extracts_current_turn_context() -> None:
    provider = OpenAIResponsesProvider()

    response_md = provider._response_internal_metadata(
        {
            "id": "resp_ctx_2",
            "reasoning": {"context": "current_turn"},
        }
    )

    assert response_md["_openai_responses_reasoning_context"] == "current_turn"


def test_response_internal_metadata_omits_reasoning_context_when_absent() -> None:
    provider = OpenAIResponsesProvider()

    response_md = provider._response_internal_metadata(
        {"id": "resp_no_ctx", "reasoning": {"effort": "medium"}}
    )

    assert "_openai_responses_reasoning_context" not in response_md


def test_response_internal_metadata_omits_reasoning_context_when_no_reasoning_obj() -> (
    None
):
    provider = OpenAIResponsesProvider()

    response_md = provider._response_internal_metadata({"id": "resp_no_reasoning"})

    assert "_openai_responses_reasoning_context" not in response_md


def test_response_internal_metadata_omits_reasoning_context_when_not_string() -> None:
    provider = OpenAIResponsesProvider()

    response_md = provider._response_internal_metadata(
        {"id": "resp_bad_ctx", "reasoning": {"context": 123}}
    )

    assert "_openai_responses_reasoning_context" not in response_md


def test_response_internal_metadata_omits_reasoning_context_when_empty() -> None:
    provider = OpenAIResponsesProvider()

    response_md = provider._response_internal_metadata(
        {"id": "resp_empty_ctx", "reasoning": {"context": ""}}
    )

    assert "_openai_responses_reasoning_context" not in response_md


def test_response_internal_metadata_extracts_reasoning_mode() -> None:
    provider = OpenAIResponsesProvider()

    response_md = provider._response_internal_metadata(
        {
            "id": "resp_mode_1",
            "reasoning": {"mode": "pro"},
        }
    )

    assert response_md["_openai_responses_reasoning_mode"] == "pro"


def test_response_internal_metadata_extracts_reasoning_mode_and_context() -> None:
    provider = OpenAIResponsesProvider()

    response_md = provider._response_internal_metadata(
        {
            "id": "resp_mode_ctx",
            "reasoning": {"mode": "pro", "context": "all_turns"},
        }
    )

    assert response_md["_openai_responses_reasoning_mode"] == "pro"
    assert response_md["_openai_responses_reasoning_context"] == "all_turns"


def test_response_internal_metadata_omits_reasoning_mode_when_absent() -> None:
    provider = OpenAIResponsesProvider()

    response_md = provider._response_internal_metadata(
        {"id": "resp_no_mode", "reasoning": {"effort": "medium"}}
    )

    assert "_openai_responses_reasoning_mode" not in response_md


def test_response_internal_metadata_omits_reasoning_mode_when_no_reasoning_obj() -> (
    None
):
    provider = OpenAIResponsesProvider()

    response_md = provider._response_internal_metadata({"id": "resp_no_reasoning_obj"})

    assert "_openai_responses_reasoning_mode" not in response_md


def test_response_internal_metadata_omits_reasoning_mode_when_not_string() -> None:
    provider = OpenAIResponsesProvider()

    response_md = provider._response_internal_metadata(
        {"id": "resp_bad_mode", "reasoning": {"mode": 123}}
    )

    assert "_openai_responses_reasoning_mode" not in response_md


def test_response_internal_metadata_omits_reasoning_mode_when_empty() -> None:
    provider = OpenAIResponsesProvider()

    response_md = provider._response_internal_metadata(
        {"id": "resp_empty_mode", "reasoning": {"mode": ""}}
    )

    assert "_openai_responses_reasoning_mode" not in response_md
    provider = OpenAIResponsesProvider()
    assert provider.cancel_request("missing-request") is False


def test_stream_api_can_be_cancelled_by_request_id() -> None:
    provider = OpenAIResponsesProvider()
    client = _BlockingStreamingClient()
    state = provider.init({"model": "gpt-5-mini", "api_key": "test_key"})
    state = {
        **state,
        "client": client,
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "timeout": 30,
            "headers": {},
        },
    }

    outcome: dict[str, object] = {}

    def _consume() -> None:
        try:
            list(
                provider.stream_api(
                    [
                        {
                            "type": "message",
                            "role": "user",
                            "content": [{"type": "input_text", "text": "hello"}],
                        }
                    ],
                    state,
                    request_id="req_openai_stream_cancel",
                )
            )
        except Exception as exc:  # noqa: BLE001
            outcome["error"] = exc

    worker = threading.Thread(target=_consume)
    worker.start()

    time.sleep(0.2)
    assert provider.cancel_request("req_openai_stream_cancel") is True

    worker.join(timeout=5)
    assert not worker.is_alive()
    assert isinstance(outcome.get("error"), ProviderRequestCancelled)
    assert provider.cancel_request("req_openai_stream_cancel") is False


def test_call_api_can_be_cancelled_by_request_id() -> None:
    provider = OpenAIResponsesProvider()
    client = _BlockingClient()
    state = provider.init({"model": "gpt-5-mini", "api_key": "test_key"})
    state = {
        **state,
        "client": client,
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "timeout": 30,
            "headers": {},
        },
    }

    outcome: dict[str, object] = {}

    def _consume() -> None:
        try:
            provider.call_api(
                [
                    {
                        "type": "message",
                        "role": "user",
                        "content": [{"type": "input_text", "text": "hello"}],
                    }
                ],
                state,
                request_id="req_openai_call_cancel",
            )
        except Exception as exc:  # noqa: BLE001
            outcome["error"] = exc

    worker = threading.Thread(target=_consume)
    worker.start()

    time.sleep(0.2)
    assert provider.cancel_request("req_openai_call_cancel") is True

    worker.join(timeout=5)
    assert not worker.is_alive()
    assert isinstance(outcome.get("error"), ProviderRequestCancelled)
    assert provider.cancel_request("req_openai_call_cancel") is False


def test_streaming_fixture_finals_receive_feature_finalize_stamps() -> None:
    """Regression: openai_responses streaming finals must be processed by feature finalize.

    When a provider emits finals during streaming (via process_chunk), those
    finals accumulate in aggregated_native_finals. The core must pass the
    combined list (aggregated + provider.finalize) into feature finalize so
    that features like TimestampExtension and DurationExtension can stamp
    metadata onto the real assistant messages.
    """
    from dataclasses import dataclass
    from typing import List, Tuple

    from agent_core.types import FeaturePlugin

    @dataclass
    class _StampFeature(FeaturePlugin):
        name: str = "stamp_feature"
        version: str = "1.0.0"

        def get_config_schema(self) -> Dict[str, Any]:
            return {}

        def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
            return state

        def finalize(
            self,
            final_messages: List[Dict[str, Any]],
            native_messages: List[Dict[str, Any]],
            state: Dict[str, Any],
        ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
            stamped = [
                {**m, "_metadata": {**(m.get("_metadata") or {}), "stamped": True}}
                for m in final_messages
            ]
            # Also stamp history so native rebuilds keep the marker
            start = (
                len(native_messages) - len(stamped)
                if len(stamped) <= len(native_messages)
                else 0
            )
            stamped_history = list(native_messages)
            for offset, final_msg in enumerate(stamped):
                hist_idx = start + offset
                if 0 <= hist_idx < len(stamped_history):
                    stamped_history[hist_idx] = final_msg
            return stamped, stamped_history, state

    core = AgentCore()
    core.register_provider(_StreamingFixtureProvider)
    core.register_feature(_StampFeature)

    config = {
        "model": "gpt-5-mini",
        "api_key": "test_key",
        "base_url": "https://api.openai.com/v1",
        "timeout": 30,
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with STREAM_OK")

    final_messages: list[Dict[str, Any]] = []
    final_session = None
    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "final":
            final_messages = chunk.get("messages") or []
            final_session = chunk.get("session")

    assert final_messages
    assistant = final_messages[-1]
    assert assistant.get("role") == "assistant"
    # Feature stamps _metadata; provider from_native_messages copies relevant
    # internal metadata into core message metadata.
    assert assistant.get("metadata", {}).get("stamped") is True

    # Verify native history persistence
    assert final_session is not None
    native_history = (final_session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    last_native = native_history[-1]
    assert isinstance(last_native, dict)
    assert last_native.get("_metadata", {}).get("stamped") is True
