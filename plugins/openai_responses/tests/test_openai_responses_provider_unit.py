from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pytest

from agent_core import AgentCore
import openai_responses_plugins.openai_responses_provider as provider_module
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


class _UploadStreamingFixtureClient(_FixtureStreamingClient):
    def __init__(self, events: list[Dict[str, Any]]) -> None:
        super().__init__(events)
        self.files = _FixtureFilesResource()


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

    monkeypatch.setattr(provider_module, "OpenAI", _fake_openai)
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
    }
    assert elements[1] == {
        "ui_type": "model_picker",
        "key": "model",
        "attachment_type": "dropdown",
        "display_placement": "left",
        "options": [
            {"label": "GPT-5 Mini", "value": "gpt-5-mini"},
            {"label": "gpt-4.1-mini", "value": "gpt-4.1-mini"},
        ],
        "label": "model",
    }
    assert elements[2] == {
        "ui_type": "composer_attachment",
        "key": "openai_responses:attachment:image",
        "attachment_type": "image",
        "supports_url": True,
        "supported_file_types": ["png", "jpg", "jpeg", "webp", "gif"],
        "display_placement": "below",
        "label": "Image",
        "icon": "image",
    }


def test_get_ui_elements_falls_back_to_text_when_models_are_unavailable() -> None:
    provider = OpenAIResponsesProvider()

    elements = provider.get_ui_elements(config={}, tags=["openai_responses"], models=[])

    assert elements[0] == {
        "ui_type": "config",
        "type": "text",
        "key": "model",
        "label": "OpenAI Model",
    }
    assert elements[1]["ui_type"] == "model_picker"
    assert elements[1]["options"] == []
    assert elements[2]["ui_type"] == "composer_attachment"


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
    assert native[1]["content"] == [{"type": "output_text", "text": "working"}]
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
        {"openai_responses_attachments": {"attachment_upload_mode": "upload_before_send"}},
    )

    assert native == [
        {
            "type": "message",
            "role": "user",
            "content": [
                {"type": "input_text", "text": "read this pdf"},
                {"type": "input_file", "file_data": "JVBERi0xLjQK", "filename": "brief.pdf"},
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


def test_to_native_messages_rejects_pdf_when_upload_mode_disabled() -> None:
    provider = OpenAIResponsesProvider()

    with pytest.raises(ValueError, match="attachment_upload_mode=upload_before_send"):
        provider.to_native_messages(
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


def test_from_native_messages_collapses_commentary_and_empty_final_answer_into_one_assistant() -> None:
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


def test_from_native_messages_collapses_reasoning_and_function_call_into_one_assistant_anchor() -> None:
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


def test_from_native_messages_preserves_phase_messages_when_final_and_tool_call_share_segment() -> None:
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
    assert [entry.get("phase") for entry in phase_messages] == ["commentary", "final_answer"]
    assert [entry.get("content") for entry in phase_messages] == ["working", "done"]


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
            "arguments": "{\"a\": 1, \"b\": 2}",
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
        "arguments": "{\"a\": 1, \"b\": 2}",
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
                {"type": "input_file", "file_data": "JVBERi0xLjQK", "filename": "brief.pdf"},
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
        "openai_responses_attachments": {"attachment_upload_mode": "upload_before_send"},
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
    assert stored_input["_metadata"]["_openai_responses_attachment_sources"][0]["multipart_part"]["type"] == "image"
    assert stored_input["_metadata"]["_openai_responses_attachment_sources"][1]["multipart_part"]["type"] == "pdf"
    assert stored_input["_metadata"]["_openai_responses_uploaded_attachments"] == [
        {"content_index": 1, "uploaded_part": {"type": "input_image", "file_id": "file_1"}},
        {"content_index": 2, "uploaded_part": {"type": "input_file", "file_id": "file_2"}},
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
        "openai_responses_attachments": {"attachment_upload_mode": "upload_before_send"},
        "client": fake_client,
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 12,
        },
    }

    provider.call_api(input_items, state)

    assert len(fake_client.files.calls) == 1


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
        "openai_responses_attachments": {"attachment_upload_mode": "upload_before_send"},
        "client": fake_client,
    }

    native_after, new_state = provider.initialize_request(
        [
            {
                "type": "message",
                "role": "user",
                "content": [{"type": "input_image", "image_url": "data:image/png;base64,Zm9v"}],
            }
        ],
        state,
    )

    assert native_after == [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_image", "image_url": "data:image/png;base64,Zm9v"}],
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
        [{"type": "message", "role": "user", "content": [{"type": "input_text", "text": "hi"}]}],
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
            [{"type": "message", "role": "user", "content": [{"type": "input_text", "text": "hi"}]}],
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
        [{"type": "message", "role": "user", "content": [{"type": "input_text", "text": "hi"}]}],
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
            [{"type": "message", "role": "user", "content": [{"type": "input_text", "text": "hi"}]}],
            state,
        )
    )

    assert fake_client.option_calls == []


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
        "openai_responses_attachments": {"attachment_upload_mode": "upload_before_send"},
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
        partials, _finals, native_messages, state = provider.process_chunk(event, native_messages, state)
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


def test_response_internal_metadata_preserves_service_tier() -> None:
    provider = OpenAIResponsesProvider()

    response_md = provider._response_internal_metadata({"id": "resp_1", "service_tier": "flex"})

    assert response_md["_openai_responses_service_tier"] == "flex"
