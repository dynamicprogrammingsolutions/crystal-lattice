from __future__ import annotations

from typing import Any

from reference_openai_compatible_provider.provider import OpenAICompatibleProvider
from reference_openai_compatible_provider.usage_extension import (
    OpenAICompatibleUsageExtension,
)


class _Resp:
    def __init__(
        self, *, ok: bool, payload: Any = None, status_code: int = 200, text: str = ""
    ):
        self.ok = ok
        self._payload = payload
        self.status_code = status_code
        self.text = text
        self.encoding = "utf-8"

    def json(self) -> Any:
        return self._payload


def test_usage_extension_normalizes_common_usage_fields():
    ext = OpenAICompatibleUsageExtension()
    native_messages = [
        {
            "role": "assistant",
            "content": "hello",
            "_metadata": {
                "usage": {
                    "prompt_tokens": 12,
                    "completion_tokens": 7,
                    "total_tokens": 19,
                }
            },
        }
    ]
    messages = [{"role": "assistant", "content": "hello", "metadata": {}}]

    rebuilt = ext.from_native_messages(native_messages, messages)
    metadata = rebuilt[0]["metadata"]
    assert metadata["usage"]["prompt_tokens"] == 12
    assert metadata["usage_prompt_tokens"] == 12
    assert metadata["usage_completion_tokens"] == 7
    assert metadata["usage_total_tokens"] == 19
    assert metadata["usage_total_tokens_formatted"] == "19"


def test_usage_extension_extracts_reasoning_tokens_from_nested_details():
    ext = OpenAICompatibleUsageExtension()
    native_messages = [
        {
            "role": "assistant",
            "content": "hello",
            "_metadata": {
                "usage": {
                    "prompt_tokens": 10,
                    "completion_tokens": 6,
                    "total_tokens": 16,
                    "completion_tokens_details": {"reasoning_tokens": 4},
                }
            },
        }
    ]
    messages = [{"role": "assistant", "content": "hello", "metadata": {}}]

    rebuilt = ext.from_native_messages(native_messages, messages)
    metadata = rebuilt[0]["metadata"]
    assert metadata["usage_reasoning_tokens"] == 4
    assert metadata["usage_reasoning_tokens_formatted"] == "4"


def test_usage_extension_captures_streaming_usage_into_partial_state():
    ext = OpenAICompatibleUsageExtension()
    partial_messages = [{"role": "assistant", "content": "hi"}]
    state = {"partial": {"role": "assistant", "content": "hi"}}

    _partials, _finals, _native, new_state = ext.process_chunk(
        {"usage": {"prompt_tokens": 3, "completion_tokens": 2, "total_tokens": 5}},
        partial_messages,
        [],
        [],
        state,
    )

    assert new_state["partial"]["_metadata"]["usage"] == {
        "prompt_tokens": 3,
        "completion_tokens": 2,
        "total_tokens": 5,
    }


def test_provider_call_api_preserves_non_streaming_usage_for_extensions(monkeypatch):
    def fake_post(
        url: str,
        headers: dict[str, str],
        json: dict[str, Any],
        timeout: float,
    ):
        assert json["stream"] is False
        return _Resp(
            ok=True,
            payload={
                "choices": [{"message": {"role": "assistant", "content": "pong"}}],
                "usage": {
                    "prompt_tokens": 2,
                    "completion_tokens": 1,
                    "total_tokens": 3,
                },
            },
        )

    monkeypatch.setattr("requests.post", fake_post)

    provider = OpenAICompatibleProvider()
    native_messages, state = provider.initialize_request(
        [], {"config": {"model": "demo-model"}}
    )
    _partials, finals, _history, _state = provider.call_api(native_messages, state)

    assert finals[0]["_metadata"]["usage"] == {
        "prompt_tokens": 2,
        "completion_tokens": 1,
        "total_tokens": 3,
    }


def test_usage_extension_uses_last_native_message_as_length_mismatch_fallback():
    ext = OpenAICompatibleUsageExtension()
    messages = [{"role": "assistant", "content": "done", "metadata": {}}]
    native_messages = [
        {"role": "assistant", "content": "ignored"},
        {
            "role": "assistant",
            "content": "done",
            "_metadata": {
                "usage": {"prompt_tokens": 5, "completion_tokens": 4, "total_tokens": 9}
            },
        },
    ]

    rebuilt = ext.from_native_messages(native_messages, messages)
    assert rebuilt[-1]["metadata"]["usage_total_tokens"] == 9
