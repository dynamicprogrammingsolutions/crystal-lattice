"""Integration test for ClaudeCachingFeature with OpenRouter provider.

This test exercises the ClaudeCachingFeature plugin end-to-end:

- Register OpenRouter provider + ClaudeCachingFeature
- Send a request using an ``anthropic/`` model through OpenRouter
- Verify that the persisted native history in the session *does not* contain
  ``cache_control`` blocks (they are stripped in the feature's finalize).

To manually inspect OpenRouter's caching behavior, run this test with
debug logging enabled and inspect the HTTP payloads; the feature shapes
the outbound request but does not itself expose cache hit statistics.

Run with (requires OPENROUTER_API_KEY):

    pytest core/python/tests/test_claude_caching_feature_openrouter_integration.py \
        -q -s -m openrouter
"""

from __future__ import annotations

import os
import uuid
from typing import Any, Dict, List

import pytest

try:  # Optional .env support
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:  # pragma: no cover - optional dependency
    pass

from agent_core import AgentCore
from plugins.openrouter_provider import OpenRouterProvider
from plugins.claude_caching_feature import ClaudeCachingFeature


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"
MODEL_CLAUDE = "anthropic/claude-haiku-4.5"


@pytest.fixture(scope="module")
def ensure_api_key():
    """Skip tests if OpenRouter API key is not configured."""

    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set; skipping Claude caching tests")


def _find_cache_blocks(messages: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    blocks: List[Dict[str, Any]] = []
    for msg in messages:
        content = msg.get("content")
        if not isinstance(content, list):
            continue
        for block in content:
            if not isinstance(block, dict):
                continue
            cc = block.get("cache_control")
            if isinstance(cc, dict) and cc.get("type") == "ephemeral":
                blocks.append(block)
    return blocks


@pytest.mark.integration
@pytest.mark.openrouter
def test_claude_caching_feature_strips_cache_control_from_retained_history(ensure_api_key):
    """Ensure ClaudeCachingFeature does not persist cache_control markers.

    The cache_control breakpoint is injected into the outbound provider-native
    messages only for the duration of the request. After finalize, the
    retained native history in the session metadata must not include any
    cache_control blocks.

    This test also issues a follow-up request on the same session so that
    OpenRouter/Anthropic can exercise cached tokens on the second call.
    """

    core = AgentCore()
    core.register_provider(OpenRouterProvider)
    core.register_feature(ClaudeCachingFeature)

    config: Dict[str, Any] = {
        "provider": "openrouter",
        "model": MODEL_CLAUDE,
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 120,
        "enable_claude_caching": True,
    }

    # First request: warm up cache
    session = core.create_session()
    # Use a long synthetic "book" body (~2000+ words) to make caching
    # meaningful. Repeating a dense paragraph approximates a large context.
    # Prepend a random run-specific prefix to invalidate any provider-side
    # cache from previous test runs.
    random_prefix = f"RUN_ID_{uuid.uuid4()}"
    long_body = random_prefix + " " + " ".join(
        [
            "In the waning centuries of the Roman Empire, chronic fiscal strain, "
            "a sprawling frontier, and repeated military crises steadily eroded "
            "the resilience of imperial institutions. Senators debated reforms "
            "while provincial elites withdrew to private estates, the army was "
            "stretched thin across frontiers, and emperors rose and fell with "
            "disquieting speed, often elevated by mutinous legions rather than "
            "orderly succession.",
        ]
        * 250
    )
    session = core.add_message(
        session,
        "system",
        "You are a historian studying the fall of the Roman Empire. "
        "You know the following book very well:" "\n" + long_body,
    )
    session = core.add_message(session, "user", "What triggered the collapse?")

    new_session, responses = core.send_request(session, config)

    assert new_session is not None
    assert responses, "expected at least one assistant response"

    md = new_session.metadata if isinstance(new_session.metadata, dict) else {}
    native_messages = md.get("native_messages") or []

    print("\n--- Retained native_messages after first request (truncated) ---")
    for i, msg in enumerate(native_messages[-3:]):
        print(f"[{i}] role={msg.get('role')} keys={list(msg.keys())}")

    cache_blocks = _find_cache_blocks(native_messages)
    assert not cache_blocks, "cache_control blocks must not be persisted in native history"

    # Second request: same session, different question, intended to leverage
    # provider-side cached tokens for the long system prompt.
    followup_session = core.add_message(
        new_session,
        "user",
        "Answer in one concise paragraph.",
    )

    followup_session, followup_responses = core.send_request(followup_session, config)

    assert followup_session is not None
    assert followup_responses, "expected a follow-up assistant response"

    print("\nFirst answer:\n", responses[-1]["content"][:200])
    print("\nFollow-up answer:\n", followup_responses[-1]["content"][:200])


@pytest.mark.integration
@pytest.mark.openrouter
def test_claude_caching_feature_strips_cache_control_streaming(ensure_api_key):
    """Streaming variant of the ClaudeCachingFeature integration test.

    This test mirrors
    ``test_claude_caching_feature_strips_cache_control_from_retained_history``
    but uses ``send_request_stream`` for both requests. The same guarantees
    must hold: cache_control markers are injected only transiently and are
    not persisted in the retained provider-native history on the session.
    """

    core = AgentCore()
    core.register_provider(OpenRouterProvider)
    core.register_feature(ClaudeCachingFeature)

    config: Dict[str, Any] = {
        "provider": "openrouter",
        "model": MODEL_CLAUDE,
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 120,
        "enable_claude_caching": True,
    }

    # First request: warm up cache using streaming API.
    session = core.create_session()
    random_prefix = f"RUN_ID_{uuid.uuid4()}"
    long_body = random_prefix + " " + " ".join(
        [
            "In the waning centuries of the Roman Empire, chronic fiscal strain, "
            "a sprawling frontier, and repeated military crises steadily eroded "
            "the resilience of imperial institutions. Senators debated reforms "
            "while provincial elites withdrew to private estates, the army was "
            "stretched thin across frontiers, and emperors rose and fell with "
            "disquieting speed, often elevated by mutinous legions rather than "
            "orderly succession.",
        ]
        * 250
    )
    session = core.add_message(
        session,
        "system",
        "You are a historian studying the fall of the Roman Empire. "
        "You know the following book very well:" "\n" + long_body,
    )
    session = core.add_message(session, "user", "What triggered the collapse?")

    first_final_chunk: Dict[str, Any] | None = None
    for chunk in core.send_request_stream(session, config):
        if chunk.get("type") == "final":
            first_final_chunk = chunk

    assert first_final_chunk is not None, "expected a final streaming chunk"
    new_session = first_final_chunk["session"]
    responses: List[Dict[str, Any]] = first_final_chunk["messages"]

    assert new_session is not None
    assert responses, "expected at least one assistant response"

    md = new_session.metadata if isinstance(new_session.metadata, dict) else {}
    native_messages = md.get("native_messages") or []

    print("\n--- Retained native_messages after first streaming request (truncated) ---")
    for i, msg in enumerate(native_messages[-3:]):
        print(f"[{i}] role={msg.get('role')} keys={list(msg.keys())}")

    cache_blocks = _find_cache_blocks(native_messages)
    assert not cache_blocks, "cache_control blocks must not be persisted in native history"

    # Second request: same session, streaming again to exercise cached tokens.
    followup_session = core.add_message(
        new_session,
        "user",
        "Answer in one concise paragraph.",
    )

    second_final_chunk: Dict[str, Any] | None = None
    for chunk in core.send_request_stream(followup_session, config):
        if chunk.get("type") == "final":
            second_final_chunk = chunk

    assert second_final_chunk is not None, "expected a final streaming chunk on follow-up"
    followup_session = second_final_chunk["session"]
    followup_responses: List[Dict[str, Any]] = second_final_chunk["messages"]

    assert followup_session is not None
    assert followup_responses, "expected a follow-up assistant response"

    print("\nFirst (streaming) answer:\n", responses[-1]["content"][:200])
    print("\nFollow-up (streaming) answer:\n", followup_responses[-1]["content"][:200])

