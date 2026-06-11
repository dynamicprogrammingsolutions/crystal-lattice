"""Integration test for OpenRouter multipart (image) messages.

Requires OPENROUTER_API_KEY environment variable.

Run with:

    pytest plugins/openrouter/tests/test_openrouter_multipart_integration.py -v -s
"""

from __future__ import annotations

import os

import pytest

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from agent_core import AgentCore
from openrouter_plugins.openrouter_provider import OpenRouterProvider


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"
pytestmark = pytest.mark.api

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
                    "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/1280px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
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
