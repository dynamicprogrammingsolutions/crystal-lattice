"""Basic integration tests for OpenRouter `/responses` provider.

Requires OPENROUTER_API_KEY.
"""

from __future__ import annotations

import os

import pytest

from agent_core import AgentCore
from openrouter_responses_plugins.openrouter_responses_provider import OpenRouterResponsesProvider


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "openai/gpt-5-mini"


@pytest.fixture(scope="module")
def ensure_api_key() -> None:
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set; skipping OpenRouter integration tests")


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_responses_non_streaming(ensure_api_key: None) -> None:
    core = AgentCore()
    core.register_provider(OpenRouterResponsesProvider)

    config = {
        "model": MODEL,
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Say 'Hello' and nothing else.")

    new_session, responses = core.send_request(session, config)

    assert new_session is not None
    assert responses
    assistant_msg = responses[-1]
    assert assistant_msg["role"] == "assistant"
    assert isinstance(assistant_msg.get("content"), str)
    assert assistant_msg["content"].strip()


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_responses_streaming(ensure_api_key: None, tmp_path) -> None:
    core = AgentCore()
    core.register_provider(OpenRouterResponsesProvider)

    debug_path = tmp_path / "openrouter_responses_sse.log"

    config = {
        "model": MODEL,
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
        "debug_sse_path": str(debug_path),
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Write one short sentence about programming.")

    partial_count = 0
    final_message = None

    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "partial":
            text = chunk["message"].get("content", "")
            if text:
                partial_count += 1
        elif chunk["type"] == "final":
            final_message = chunk["messages"][-1]

    assert partial_count > 0
    assert final_message is not None
    assert final_message["role"] == "assistant"
    assert isinstance(final_message.get("content"), str)
    assert final_message["content"].strip()
    assert debug_path.exists(), "expected SSE debug log to be created"
