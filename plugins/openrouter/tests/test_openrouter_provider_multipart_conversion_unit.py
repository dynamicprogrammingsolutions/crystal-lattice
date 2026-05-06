from __future__ import annotations

from typing import Any, Dict, List

from agent_core.tool_result_payloads import (
    FORMAT_OPENAI_CHAT_COMPLETIONS,
    make_provider_native_tool_result,
)
from openrouter_plugins.openrouter_provider import OpenRouterProvider


def test_openrouter_provider_converts_image_multipart_content() -> None:
    provider = OpenRouterProvider()
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
    assert msg.get("role") == "user"
    content = msg.get("content")
    assert isinstance(content, list)
    assert content[0] == {"type": "text", "text": "What's in this image?"}
    assert content[1] == {
        "type": "image_url",
        "image_url": {"url": "https://example.com/image.png"},
    }


def test_openrouter_provider_preserves_provider_native_tool_result_content() -> None:
    provider = OpenRouterProvider()
    state = provider.init(
        {
            "model": "moonshotai/kimi-k2.5",
            "api_key": "test",
            "base_url": "https://openrouter.ai/api/v1",
        }
    )
    payload = make_provider_native_tool_result(
        format=FORMAT_OPENAI_CHAT_COMPLETIONS,
        content=[
            {"type": "text", "text": '<image path="sample.png">'},
            {
                "type": "image_url",
                "image_url": {"url": "data:image/png;base64,QUJDRA=="},
            },
            {"type": "text", "text": "</image>"},
        ],
    )

    native = provider.to_native_messages(
        [
            {
                "role": "tool",
                "content": payload,
                "metadata": {"tool_call_id": "call_1"},
            }
        ],
        state,
    )

    assert native == [
        {
            "role": "tool",
            "content": payload["content"],
            "tool_call_id": "call_1",
        }
    ]
    assert "QUJDRA==" not in native[0]["content"][0]["text"]
    assert "QUJDRA==" not in native[0]["content"][2]["text"]
