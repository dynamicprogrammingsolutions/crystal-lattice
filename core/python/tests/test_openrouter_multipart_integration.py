"""Integration test for OpenRouter multipart (image) messages.

Requires OPENROUTER_API_KEY environment variable.

Run with:

    pytest core/python/tests/test_openrouter_multipart_integration.py -v -s -m openrouter
"""

from __future__ import annotations

import os
import base64

import pytest
import requests

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from agent_core import AgentCore
from plugins.openrouter_provider import OpenRouterProvider


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

# Model from OpenRouter's multimodal examples.
MODEL_GEMINI_FLASH_PREVIEW = "google/gemini-3-flash-preview"


@pytest.fixture(scope="module")
def ensure_api_key() -> None:
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set; skipping OpenRouter integration tests")


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_image_multipart_non_streaming(ensure_api_key) -> None:
    core = AgentCore()
    core.register_provider(OpenRouterProvider)

    config = {
        "model": MODEL_GEMINI_FLASH_PREVIEW,
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "What's in this image?",
        multipart_content=[
            {
                "type": "image",
                "content": {
                    "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
                },
                "metadata": {},
            }
        ],
    )

    _new_session, responses = core.send_request(session, config)

    assert responses
    assistant_msg = responses[-1]
    assert assistant_msg["role"] == "assistant"
    assert isinstance(assistant_msg.get("content"), str)
    assert assistant_msg["content"].strip()


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_image_multipart_data_url_non_streaming(ensure_api_key) -> None:
    core = AgentCore()
    core.register_provider(OpenRouterProvider)

    config = {
        "model": MODEL_GEMINI_FLASH_PREVIEW,
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
    }

    # Same image as the URL-based test, but use a smaller thumbnail variant
    # to keep the base64 payload size reasonable.
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/640px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
    try:
        resp = requests.get(
            image_url,
            headers={
                "User-Agent": "ai-agent-platform-tests/1.0 (+https://github.com/openai)",
            },
            timeout=30,
        )
        resp.raise_for_status()
    except Exception as exc:
        pytest.skip(f"failed to download test image for data url: {exc}")

    mime_type = (resp.headers.get("Content-Type") or "image/jpeg").split(";")[0].strip()
    image_b64 = base64.b64encode(resp.content).decode("ascii")
    data_url = f"data:{mime_type};base64,{image_b64}"

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "What's in this image?",
        multipart_content=[
            {
                "type": "image",
                "content": {
                    "url": data_url,
                },
                "metadata": {},
            }
        ],
    )

    _new_session, responses = core.send_request(session, config)

    assert responses
    assistant_msg = responses[-1]
    assert assistant_msg["role"] == "assistant"
    assert isinstance(assistant_msg.get("content"), str)
    assert assistant_msg["content"].strip()
