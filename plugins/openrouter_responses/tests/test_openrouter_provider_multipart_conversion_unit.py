from __future__ import annotations

from typing import Any, Dict, List

from openrouter_responses_plugins.openrouter_responses_provider import OpenRouterResponsesProvider


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
    assert content[1] == {"type": "input_image", "image_url": "https://example.com/image.png"}
