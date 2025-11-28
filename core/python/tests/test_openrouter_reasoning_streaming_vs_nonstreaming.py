"""Integration tests comparing streaming vs non-streaming reasoning_details.

These tests verify that reasoning_details are properly accumulated during streaming
and match the structure from non-streaming responses.

Requires OPENROUTER_API_KEY environment variable.

Run with: pytest tests/test_openrouter_reasoning_streaming_vs_nonstreaming.py -v -s -m openrouter
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
from plugins.openrouter_provider import OpenRouterProvider
from plugins.openrouter_reasoning_extension import OpenRouterReasoningExtension
from plugins.request_options_feature import RequestOptionsFeature


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

# Models for testing
# Note: Using models that support reasoning
MODELS = {
    "claude": "anthropic/claude-sonnet-4",  # Supports reasoning
    "gpt": "openai/gpt-5-mini",  # Supports reasoning
    "grok": "x-ai/grok-4.1-fast",  # Supports reasoning (paid version for reliability)
}

# Test prompt that should trigger reasoning
TEST_PROMPT = "Calculate 23 + 47 step by step. Show your reasoning."


@pytest.fixture(scope="module")
def ensure_api_key():
    """Skip tests if OpenRouter API key is not configured."""
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set; skipping OpenRouter reasoning comparison tests")


def get_reasoning_details_structure(details):
    """Extract structure info from reasoning_details for comparison."""
    if not details:
        return []

    structure = []
    for detail in details:
        structure.append(
            {
                "type": detail.get("type"),
                "format": detail.get("format"),
                "index": detail.get("index"),
                "has_text": "text" in detail,
                "has_data": "data" in detail,
                "has_summary": "summary" in detail,
                "has_signature": "signature" in detail,
                "has_id": "id" in detail,
            }
        )
    return structure


def assert_content_fields_accumulated(details, min_length=10):
    """Assert that content fields have reasonable length (accumulated, not empty)."""
    for detail in details:
        if "text" in detail:
            text = detail["text"]
            assert len(text) >= min_length, f"text too short ({len(text)} chars): {text[:50]}"
            print(f"  ✓ text length: {len(text)}")

        if "data" in detail:
            data = detail["data"]
            assert len(data) >= min_length, f"data too short ({len(data)} chars)"
            print(f"  ✓ data length: {len(data)}")

        if "summary" in detail:
            summary = detail["summary"]
            assert (
                len(summary) >= min_length
            ), f"summary too short ({len(summary)} chars): {summary[:50]}"
            print(f"  ✓ summary length: {len(summary)}")

        if "signature" in detail:
            signature = detail["signature"]
            assert len(signature) >= min_length, f"signature too short ({len(signature)} chars)"
            print(f"  ✓ signature length: {len(signature)}")


@pytest.mark.integration
@pytest.mark.openrouter
def test_claude_haiku_streaming_vs_nonstreaming(ensure_api_key):
    """Test Claude Haiku reasoning_details: streaming vs non-streaming."""
    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterReasoningExtension])
    core.register_feature(RequestOptionsFeature)

    config = {
        "model": MODELS["claude"],

        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
        "enable_reasoning": True,
    }

    print("\n=== Claude Haiku Non-Streaming ===")
    session1 = core.create_session()
    session1 = core.add_message(session1, "user", TEST_PROMPT)
    new_session1, responses1 = core.send_request(session1, config)

    msg1 = responses1[-1]
    metadata1 = msg1.get("metadata", {})
    details1 = metadata1.get("reasoning_details", [])

    print(f"Details count: {len(details1)}")
    for i, detail in enumerate(details1):
        print(f"  Detail {i}: type={detail.get('type')}, format={detail.get('format')}")

    assert len(details1) > 0, "Non-streaming should have reasoning_details"
    assert_content_fields_accumulated(details1, min_length=20)
    structure1 = get_reasoning_details_structure(details1)

    print("\n=== Claude Haiku Streaming ===")
    session2 = core.create_session()
    session2 = core.add_message(session2, "user", TEST_PROMPT)

    final_message = None
    for chunk in core.send_request_stream(session2, config):
        if chunk["type"] == "final":
            final_message = chunk["messages"][-1]

    assert final_message is not None
    metadata2 = final_message.get("metadata", {})
    details2 = metadata2.get("reasoning_details", [])

    print(f"Details count: {len(details2)}")
    for i, detail in enumerate(details2):
        print(f"  Detail {i}: type={detail.get('type')}, format={detail.get('format')}")

    assert len(details2) > 0, "Streaming should have reasoning_details"
    assert_content_fields_accumulated(details2, min_length=20)
    structure2 = get_reasoning_details_structure(details2)

    # Compare structures
    print("\n=== Comparison ===")
    print(f"Non-streaming structure: {structure1}")
    print(f"Streaming structure: {structure2}")

    # Note: OpenAI's streaming vs non-streaming may return different numbers of details
    # (e.g., non-streaming may include summary that streaming doesn't)
    # The important thing is that content fields are accumulated properly

    # Verify both have at least one detail with accumulated content
    assert len(structure1) >= 1, "Non-streaming should have at least one detail"
    assert len(structure2) >= 1, "Streaming should have at least one detail"

    # Verify formats match (both should be openai-responses-v1)
    formats1 = set(s["format"] for s in structure1)
    formats2 = set(s["format"] for s in structure2)
    assert formats1 == formats2, f"Format mismatch: {formats1} vs {formats2}"

    print("✅ GPT-5 Mini: Both have reasoning_details with accumulated content")
    print(f"   Non-streaming: {len(details1)} details")
    print(f"   Streaming: {len(details2)} details")
    print(f"   Non-streaming: {len(details1)} details")
    print(f"   Streaming: {len(details2)} details")


@pytest.mark.integration
@pytest.mark.openrouter
def test_grok_streaming_vs_nonstreaming(ensure_api_key):
    """Test Grok reasoning_details: streaming vs non-streaming."""
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

    print("\n=== Grok Non-Streaming ===")
    session1 = core.create_session()
    session1 = core.add_message(session1, "user", TEST_PROMPT)
    new_session1, responses1 = core.send_request(session1, config)

    msg1 = responses1[-1]
    metadata1 = msg1.get("metadata", {})
    details1 = metadata1.get("reasoning_details", [])

    print(f"Details count: {len(details1)}")
    for i, detail in enumerate(details1):
        print(f"  Detail {i}: type={detail.get('type')}, format={detail.get('format')}")

    if len(details1) == 0:
        print("Note: Grok free model may not return reasoning_details")
        pytest.skip("Grok did not return reasoning_details")

    assert_content_fields_accumulated(details1, min_length=10)
    structure1 = get_reasoning_details_structure(details1)

    print("\n=== Grok Streaming ===")
    session2 = core.create_session()
    session2 = core.add_message(session2, "user", TEST_PROMPT)

    final_message = None
    for chunk in core.send_request_stream(session2, config):
        if chunk["type"] == "final":
            final_message = chunk["messages"][-1]

    assert final_message is not None
    metadata2 = final_message.get("metadata", {})
    details2 = metadata2.get("reasoning_details", [])

    print(f"Details count: {len(details2)}")
    for i, detail in enumerate(details2):
        print(f"  Detail {i}: type={detail.get('type')}, format={detail.get('format')}")

    assert len(details2) > 0, "Streaming should have reasoning_details"
    assert_content_fields_accumulated(details2, min_length=10)
    structure2 = get_reasoning_details_structure(details2)

    # Compare structures
    print("\n=== Comparison ===")
    print(f"Non-streaming structure: {structure1}")
    print(f"Streaming structure: {structure2}")

    # Verify both have at least one detail with accumulated content
    assert len(structure1) >= 1, "Non-streaming should have at least one detail"
    assert len(structure2) >= 1, "Streaming should have at least one detail"

    # Verify formats match
    formats1 = set(s["format"] for s in structure1)
    formats2 = set(s["format"] for s in structure2)
    assert formats1 == formats2, f"Format mismatch: {formats1} vs {formats2}"

    print("✅ Grok: Both have reasoning_details with accumulated content")
    print(f"   Non-streaming: {len(details1)} details")
    print(f"   Streaming: {len(details2)} details")
    print(f"   Non-streaming: {len(details1)} details")
    print(f"   Streaming: {len(details2)} details")
