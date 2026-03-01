"""Integration tests for OpenRouter reasoning extension.

Tests reasoning extraction with multiple model families.
Requires OPENROUTER_API_KEY environment variable.

Run with: pytest tests/test_openrouter_reasoning_integration.py -v -s -m openrouter
"""

from __future__ import annotations

import os
import pytest

# Load .env file if it exists
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from agent_core import AgentCore
from openrouter_plugins.openrouter_provider import OpenRouterProvider
from openrouter_plugins.openrouter_reasoning_extension import OpenRouterReasoningExtension
from plugins.request_options_feature import RequestOptionsFeature


def _get_openai_provider_options() -> dict[str, object]:
    """Build provider routing block based on OPENAI_PROVIDER.

    OPENAI_PROVIDER can be set to "openai" or "azure"; defaults to "openai".
    """
    provider_id = os.getenv("OPENAI_PROVIDER") or "openai"
    return {
        "provider": {
            "order": [provider_id],
            "allow_fallbacks": False,
        }
    }


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

# Models that support reasoning (using cheap versions)
MODELS = {
    "gemini": "google/gemini-2.5-flash-lite",
    "grok": "x-ai/grok-4.1-fast",
    "gpt": "openai/gpt-5-mini",
    # Note: Claude models may have different reasoning support
}


@pytest.fixture(scope="module")
def ensure_api_key():
    """Skip tests if OpenRouter API key is not configured."""
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set; skipping OpenRouter reasoning integration tests")


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_reasoning_gemini_non_streaming(ensure_api_key):
    """Test reasoning extraction with Gemini (non-streaming)."""
    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterReasoningExtension])

    config = {
        "model": MODELS["gemini"],
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
        "enable_reasoning": True,
        "reasoning_effort": "low",
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Calculate 15 + 27. Show your thinking step by step.",
    )

    new_session, responses = core.send_request(session, config)

    assert new_session is not None
    assert len(responses) > 0

    assistant_msg = responses[-1]
    assert assistant_msg["role"] == "assistant"
    assert isinstance(assistant_msg.get("content"), str)
    print(f"\nContent: {assistant_msg['content']}")

    # Check if reasoning is present in metadata
    metadata = assistant_msg.get("metadata", {})
    reasoning = metadata.get("reasoning")
    if reasoning:
        print(f"Reasoning: {reasoning[:200]}...")
        assert isinstance(metadata["reasoning"], str)
    else:
        print("Note: Model did not return reasoning field")


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_reasoning_gemini_streaming(ensure_api_key):
    """Test reasoning extraction with Gemini (streaming)."""
    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterReasoningExtension])

    config = {
        "model": MODELS["gemini"],
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
        "enable_reasoning": True,
        "reasoning_effort": "low",
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "What is 8 * 7? Think through it step by step.",
    )

    partial_count = 0
    final_message = None

    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "partial":
            text = chunk["message"].get("content", "")
            if text:
                partial_count += 1
                print(text, end="", flush=True)
        elif chunk["type"] == "final":
            final_message = chunk["messages"][-1]
            print(f"\n\nFinal: {final_message['content'][:100]}")

    assert partial_count > 0, "expected streaming partials"
    assert final_message is not None
    assert final_message["role"] == "assistant"

    metadata = final_message.get("metadata", {})
    if "reasoning" in metadata:
        print(f"Reasoning: {metadata['reasoning'][:200]}...")


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_reasoning_grok_non_streaming(ensure_api_key):
    """Test reasoning extraction with Grok (non-streaming)."""
    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterReasoningExtension])
    core.register_feature(RequestOptionsFeature)

    config = {
        "model": MODELS["grok"],

        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
        "enable_reasoning": True,
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Solve: 12 + 18. Explain your reasoning.",
    )

    new_session, responses = core.send_request(session, config)

    assert len(responses) > 0
    assistant_msg = responses[-1]
    print(f"\nGrok response: {assistant_msg['content'][:100]}")

    metadata = assistant_msg.get("metadata", {})
    reasoning = metadata.get("reasoning")
    if reasoning:
        print(f"Reasoning: {reasoning[:200]}...")


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_reasoning_gpt_non_streaming(ensure_api_key):
    """Test reasoning extraction with GPT-5 Mini (non-streaming)."""
    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterReasoningExtension])
    core.register_feature(RequestOptionsFeature)

    config = {
        "model": MODELS["gpt"],
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
        "enable_reasoning": True,
        "reasoning_effort": "medium",
        "request_options": _get_openai_provider_options(),
    }


    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Calculate 25 + 35. Show your thought process.",
    )

    new_session, responses = core.send_request(session, config)

    assert len(responses) > 0
    assistant_msg = responses[-1]
    print(f"\nGPT-5 Mini response: {assistant_msg['content'][:100]}")

    metadata = assistant_msg.get("metadata", {})
    reasoning = metadata.get("reasoning")
    if reasoning:
        print(f"Reasoning: {reasoning[:200]}...")


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_reasoning_without_extension():
    """Test that provider works without reasoning extension."""
    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterReasoningExtension])
    core.register_feature(RequestOptionsFeature)

    config = {
        "model": MODELS["gemini"],

        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Say 'Test'.")

    new_session, responses = core.send_request(session, config)

    assert len(responses) > 0
    assert responses[-1]["role"] == "assistant"
    print(f"\nWithout extension: {responses[-1]['content']}")


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_reasoning_disabled(ensure_api_key):
    """Test that reasoning can be disabled via config."""
    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterReasoningExtension])

    config = {
        "model": MODELS["gemini"],
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
        "enable_reasoning": False,  # Explicitly disabled
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Calculate 10 + 20.")

    new_session, responses = core.send_request(session, config)

    assert len(responses) > 0
    print(f"\nWith reasoning disabled: {responses[-1]['content']}")
