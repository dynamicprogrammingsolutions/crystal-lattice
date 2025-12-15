"""Integration tests for OpenRouter web search extension.

These tests require an OpenRouter API key and exercise both
non-streaming and streaming paths, verifying that URL citations from
OpenRouter's web search plugin are surfaced on core messages.

Run with:

    pytest core/python/tests/test_openrouter_websearch_integration.py -v -s -m openrouter
"""

from __future__ import annotations

import os
from typing import Dict

import pytest

# Load .env file if it exists
try:  # pragma: no cover - optional convenience
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - optional convenience
    pass

from agent_core import AgentCore
from plugins.openrouter_provider import OpenRouterProvider
from plugins.openrouter_reasoning_extension import OpenRouterReasoningExtension
from plugins.openrouter_websearch_extension import OpenRouterWebSearchExtension


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

# Models chosen for web search testing.
MODEL_WEBSEARCH = "anthropic/claude-haiku-4.5"
MODEL_GPT5 = "openai/gpt-5.1"


@pytest.fixture(scope="module")
def ensure_api_key() -> None:
    """Skip tests if OpenRouter API key is not configured."""

    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set; skipping OpenRouter web search tests")


def _base_config() -> Dict[str, object]:
    return {
        "model": MODEL_WEBSEARCH,
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
        # Explicitly enable web search via the extension config.
        "enable_web_search": True,
    }


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_websearch_non_streaming(ensure_api_key: None) -> None:
    """Non-streaming call returns URL citations in metadata."""

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterWebSearchExtension])

    config = _base_config()

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        (
            "Use web search to find the latest news about OpenAI. "
            "Summarize briefly and include at least one source link."
        ),
    )

    new_session, responses = core.send_request(session, config)

    assert new_session is not None
    assert responses

    assistant_msg = responses[-1]
    assert assistant_msg["role"] == "assistant"

    metadata = assistant_msg.get("metadata", {})
    citations = metadata.get("url_citations")

    print("\nNon-streaming content:", assistant_msg.get("content", "")[:200])
    print("Non-streaming citations:", citations)

    assert isinstance(citations, list) and citations, "expected at least one URL citation"
    first = citations[0]
    assert "url" in first and isinstance(first["url"], str)


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_websearch_streaming_vs_nonstreaming(ensure_api_key: None) -> None:
    """Streaming path also surfaces URL citations on the final message.

    This test also implicitly exercises where annotations appear in the
    streaming chunks; running with LOG_LEVEL=DEBUG will print the
    provider-native chunks for manual inspection via logging.
    """

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterWebSearchExtension])

    config = _base_config()

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        (
            "Use web search to find a recent article about AI safety "
            "and summarize it. Include the source URL in your answer."
        ),
    )

    partial_count = 0
    final_message = None

    for event in core.send_request_stream(session, config):
        if event["type"] == "partial":
            partial = event["message"]
            text = partial.get("content", "")
            if text:
                partial_count += 1
        elif event["type"] == "final":
            final_message = event["messages"][-1]

    assert partial_count > 0, "expected streaming partials from provider"
    assert final_message is not None

    metadata = final_message.get("metadata", {})
    citations = metadata.get("url_citations")

    print("\nStreaming final content:", final_message.get("content", "")[:200])
    print("Streaming citations:", citations)

    assert isinstance(citations, list) and citations, "expected citations on streaming final"


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_websearch_gpt5_multi_turn_non_streaming(ensure_api_key: None) -> None:
    """Multi-turn non-streaming test with OpenAI GPT-5.1 and web search.

    Sends a first request that uses web search, then a second simple
    follow-up message. Both should succeed without provider errors.
    """

    core = AgentCore()
    core.register_provider(
        OpenRouterProvider,
        extensions=[OpenRouterReasoningExtension, OpenRouterWebSearchExtension],
    )

    config = {
        "model": MODEL_GPT5,
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
        "enable_reasoning": True,
        "reasoning_effort": "low",
        "enable_web_search": True,
    }

    # First turn: request that explicitly uses web search.
    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        (
            "What are three of the latest major news headlines about "
            "OpenAI today? Answer with just the headlines as a numbered "
            "list."
        ),
        config=config,
    )

    session, responses = core.send_request(session, config)
    assert responses, "expected at least one assistant response"
    first_reply = responses[-1]
    assert first_reply.get("role") == "assistant"

    # Second turn: simple follow-up that should succeed even after web search.
    session = core.add_message(session, "user", "OK", config=config)
    session, responses2 = core.send_request(session, config)

    assert responses2, "expected assistant response on second turn"
    second_reply = responses2[-1]
    assert second_reply.get("role") == "assistant"


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_websearch_gpt5_multi_turn_streaming(ensure_api_key: None) -> None:
    """Multi-turn streaming test with OpenAI GPT-5.1 and web search.

    Mirrors the non-streaming test but uses the streaming API for both
    turns, ensuring that the second streamed request succeeds.
    """

    core = AgentCore()
    core.register_provider(
        OpenRouterProvider,
        extensions=[OpenRouterReasoningExtension, OpenRouterWebSearchExtension],
    )

    config = {
        "model": MODEL_GPT5,
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
        "enable_reasoning": True,
        "reasoning_effort": "low",
        "enable_web_search": True,
    }

    # First turn: streaming request involving web search.
    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        (
            "Give three of the latest news headlines about OpenAI today, "
            "responding only with the headlines as a numbered list."
        ),
        config=config,
    )

    final_message = None
    for event in core.send_request_stream(session, config):
        if event["type"] == "final":
            session = event["session"]
            msgs = event.get("messages") or []
            if msgs:
                final_message = msgs[-1]

    assert final_message is not None
    assert final_message.get("role") == "assistant"

    # Second turn: simple follow-up via streaming; should succeed.
    session = core.add_message(session, "user", "OK", config=config)

    final_message_2 = None
    for event in core.send_request_stream(session, config):
        if event["type"] == "final":
            session = event["session"]
            msgs = event.get("messages") or []
            if msgs:
                final_message_2 = msgs[-1]

    assert final_message_2 is not None
    assert final_message_2.get("role") == "assistant"

