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


def test_usage_extension_exposes_openrouter_style_ui_elements():
    ext = OpenAICompatibleUsageExtension()

    assert ext.get_ui_elements({}, [], []) == [
        {
            "ui_type": "message_footer",
            "data": "metadata.usage_prompt_tokens_formatted",
            "template": "input: {{data}}",
        },
        {
            "ui_type": "message_footer",
            "data": "metadata.usage_cached_tokens_formatted",
            "template": "cached: {{data}}",
        },
        {
            "ui_type": "message_footer",
            "data": "metadata.usage_completion_tokens_formatted",
            "template": "completion: {{data}}",
        },
        {
            "ui_type": "message_footer",
            "data": "metadata.usage_total_cost_formatted",
            "template": "cost: {{data}}",
        },
        {
            "ui_type": "message_footer",
            "data": "metadata.usage_turn_cost_cumulative_formatted",
            "template": "turn: {{data}}",
        },
        {
            "ui_type": "message_footer",
            "data": "metadata.usage_turn_reasoning_tokens_cumulative_formatted",
            "template": "reasoning: {{data}}",
        },
        {
            "ui_type": "status_bar",
            "data": "metadata.usage_total_cost_cumulative_formatted",
            "template": "Total: {{data}}",
        },
    ]
    assert ext.get_ui_elements({"show_usage": False}, [], []) == []


def test_usage_extension_normalizes_cached_and_cost_fields_with_turn_totals():
    ext = OpenAICompatibleUsageExtension()
    native_messages = [
        {"role": "user", "content": "hi"},
        {
            "role": "assistant",
            "content": "thinking",
            "tool_calls": [{"id": "call_1", "type": "function", "function": {"name": "lookup", "arguments": "{}"}}],
            "_metadata": {
                "usage": {
                    "prompt_tokens": 8,
                    "completion_tokens": 4,
                    "total_tokens": 12,
                    "cost_details": {"upstream_inference_cost": 0.000123},
                    "completion_tokens_details": {"reasoning_tokens": 3},
                }
            },
        },
        {"role": "tool", "content": "ok"},
        {
            "role": "assistant",
            "content": "done",
            "_metadata": {
                "usage": {
                    "prompt_tokens": 1200,
                    "completion_tokens": 300,
                    "total_tokens": 1500,
                    "prompt_tokens_details": {"cached_tokens": 256},
                    "cost": 0.000456,
                    "completion_tokens_details": {"reasoning_tokens": 7},
                }
            },
        },
    ]
    messages = [
        {"role": "user", "content": "hi", "metadata": {}},
        {"role": "assistant", "content": "thinking", "metadata": {}},
        {"role": "tool", "content": "ok", "metadata": {}},
        {"role": "assistant", "content": "done", "metadata": {}},
    ]

    rebuilt = ext.from_native_messages(native_messages, messages)
    tool_metadata = rebuilt[1]["metadata"]
    final_metadata = rebuilt[3]["metadata"]

    assert tool_metadata["usage_total_cost_formatted"] == "$0.000123"
    assert "usage_turn_cost_cumulative_formatted" not in tool_metadata
    assert final_metadata["usage_cached_tokens"] == 256
    assert final_metadata["usage_cached_tokens_formatted"] == "256"
    assert final_metadata["usage_prompt_tokens_formatted"] == "1,200"
    assert final_metadata["usage_total_cost_formatted"] == "$0.000456"
    assert final_metadata["usage_total_cost_cumulative_formatted"] == "$0.000579"
    assert final_metadata["usage_turn_cost_cumulative_formatted"] == "$0.000579"
    assert final_metadata["usage_turn_reasoning_tokens_cumulative_formatted"] == "10"


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
