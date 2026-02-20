"""Integration test for OpenRouter usage/cost tracking extension.

Verifies that usage metadata from streaming chunks is exposed on the
final assistant message metadata, including formatted total tokens and
total cost fields suitable for UI display.

Run with:
    pytest core/python/tests/test_openrouter_usage_extension_integration.py -v -s -m openrouter
"""

from __future__ import annotations

import os

import pytest

from agent_core import AgentCore
from plugins.openrouter_provider import OpenRouterProvider
from plugins.openrouter_usage_extension import OpenRouterUsageExtension


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"


@pytest.fixture(scope="module")
def ensure_api_key():
    """Skip tests if OpenRouter API key is not configured."""

    if not OPENROUTER_API_KEY:
        pytest.skip(
            "OPENROUTER_API_KEY not set; skipping OpenRouter usage integration tests",
        )


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_usage_metadata_streaming(ensure_api_key):
    """Test that usage metadata and cumulative cost are attached.

    Uses streaming so that the extension can capture the ``usage``
    block from the provider's final chunk. Sends two turns to verify
    that the cumulative cost metadata reflects the sum of costs from
    previous assistant messages.
    """

    core = AgentCore()
    core.register_provider(OpenRouterProvider, extensions=[OpenRouterUsageExtension])

    # Use a reasonably small/cheap model; the exact model is not
    # critical for this test as long as it is available via OpenRouter.
    config = {
        "model": "openai/gpt-5-mini",
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
    }

    # ---- First turn ----
    session = core.create_session()
    session = core.add_message(session, "user", "Say a short greeting.")

    final_message_1 = None

    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "final":
            assert chunk["messages"], "expected at least one final message"
            final_message_1 = chunk["messages"][-1]
            session = chunk["session"]
            break

    assert final_message_1 is not None, "expected first final assistant message"
    assert final_message_1["role"] == "assistant"

    md1 = final_message_1.get("metadata") or {}
    usage1 = md1.get("usage")
    assert isinstance(usage1, dict), "expected usage dict in first message metadata"

    tokens_str_1 = md1.get("usage_total_tokens_formatted")
    cost_str_1 = md1.get("usage_total_cost_formatted")

    assert isinstance(tokens_str_1, str) and tokens_str_1
    assert isinstance(cost_str_1, str) and cost_str_1

    # Normalize cost value: prefer explicit "cost" field, fall back to
    # cost_details.upstream_inference_cost when present.
    def _usage_cost(usage: dict) -> float:
        if not isinstance(usage, dict):
            return 0.0
        c = usage.get("cost")
        if isinstance(c, (int, float)) and c:
            return float(c)
        return float((usage.get("cost_details") or {}).get("upstream_inference_cost", 0.0) or 0.0)

    cost1 = _usage_cost(usage1)

    # ---- Second turn ----
    session = core.add_message(session, "user", "Say another short greeting.", config=config)

    final_message_2 = None

    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "final":
            assert chunk["messages"], "expected at least one final message"
            final_message_2 = chunk["messages"][-1]
            break

    assert final_message_2 is not None, "expected second final assistant message"
    assert final_message_2["role"] == "assistant"

    md2 = final_message_2.get("metadata") or {}
    usage2 = md2.get("usage")
    assert isinstance(usage2, dict), "expected usage dict in second message metadata"

    tokens_str_2 = md2.get("usage_total_tokens_formatted")
    cost_str_2 = md2.get("usage_total_cost_formatted")

    assert isinstance(tokens_str_2, str) and tokens_str_2
    assert isinstance(cost_str_2, str) and cost_str_2

    cost2 = _usage_cost(usage2)

    # Cumulative cost metadata should be present and approximately
    # equal to the sum of the individual response costs.
    cumulative_cost = md2.get("usage_total_cost_cumulative")
    cumulative_cost_str = md2.get("usage_total_cost_cumulative_formatted")

    assert isinstance(cumulative_cost, (int, float)), "missing numeric cumulative cost"
    assert isinstance(cumulative_cost_str, str) and cumulative_cost_str, "missing formatted cumulative cost"

    expected_total = cost1 + cost2
    assert cumulative_cost == pytest.approx(expected_total, rel=1e-6, abs=1e-9)

    print(f"First turn cost: {cost1}")
    print(f"Second turn cost: {cost2}")
    print(f"Cumulative cost (metadata): {cumulative_cost}")
    print(f"Cumulative cost (formatted): {cumulative_cost_str}")
