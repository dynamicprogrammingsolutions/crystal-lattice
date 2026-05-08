from __future__ import annotations

from typing import Any, Dict, List

from agent_core.tool_result_payloads import (
    FORMAT_OPENAI_CHAT_COMPLETIONS,
    FORMAT_OPENAI_RESPONSES,
    TOOL_RESULT_FIELD,
    make_provider_native_tool_result,
)
from openrouter_responses_plugins.openrouter_responses_provider import (
    OpenRouterResponsesProvider,
)


def test_openrouter_provider_converts_image_multipart_content() -> None:
    provider = OpenRouterResponsesProvider()
    state = provider.init(
        {
            "model": "google/gemini-2.5-flash-lite",
            "api_key": "test",
            "base_url": "https://openrouter.ai/api/v1",
        }
    )

    core_messages: List[Dict[str, Any]] = [
        {
            "role": "user",
            "content": "What's in this image?",
            "multipartContent": [
                {
                    "type": "image",
                    "content": {"url": "https://example.com/image.png"},
                    "metadata": {},
                }
            ],
        }
    ]

    native = provider.to_native_messages(core_messages, state)
    assert len(native) == 1
    msg = native[0]
    assert msg.get("type") == "message"
    assert msg.get("role") == "user"
    content = msg.get("content")
    assert isinstance(content, list)
    assert content[0] == {"type": "input_text", "text": "What's in this image?"}
    assert content[1] == {
        "type": "input_image",
        "image_url": "https://example.com/image.png",
    }


def test_openrouter_responses_provider_uses_openai_responses_tool_result_envelope() -> (
    None
):
    provider = OpenRouterResponsesProvider()
    state = provider.init({"model": "test", "api_key": "test"})
    payload = make_provider_native_tool_result(
        format=FORMAT_OPENAI_RESPONSES,
        output=[
            {"type": "input_text", "text": "<image>"},
            {"type": "input_image", "image_url": "data:image/png;base64,AAA"},
            {"type": "input_text", "text": "</image>"},
        ],
    )

    native = provider.to_native_messages(
        [
            {
                "role": "tool",
                "content": "opened image",
                TOOL_RESULT_FIELD: payload,
                "metadata": {"tool_call_id": "call_1"},
            }
        ],
        state,
    )

    assert native == [
        {
            "type": "function_call_output",
            "call_id": "call_1",
            "output": payload["output"],
        }
    ]


def test_openrouter_responses_provider_converts_openai_chat_tool_result_envelope() -> (
    None
):
    provider = OpenRouterResponsesProvider()
    state = provider.init({"model": "test", "api_key": "test"})
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
                "metadata": {"tool_call_id": "call_1"},
            }
        ],
        state,
    )

    assert native[0]["type"] == "function_call_output"
    assert native[0]["call_id"] == "call_1"
    assert native[0]["output"] == [
        {"type": "input_text", "text": "<image>"},
        {"type": "input_image", "image_url": "data:image/png;base64,AAA"},
        {"type": "input_text", "text": "</image>"},
    ]
