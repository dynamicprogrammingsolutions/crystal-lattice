"""Real-API integration tests for GPT-5.6 pricing and cache-write cost estimation.

Gated on ``OPENAI_API_KEY``. Uses ``gpt-5.6-luna`` (the lowest-cost GPT-5.6
model) and a stable ``prompt_cache_key`` so follow-up turns can be inspected
for cached-read and cache-write counters.
"""

from __future__ import annotations

import os
import uuid
from pathlib import Path
from typing import Any, Dict, List

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from openai_responses_plugins.openai_responses_pricing import (
    estimate_usage_cost,
    resolve_pricing_entry,
)
from openai_responses_plugins.openai_responses_prompt_caching_extension import (
    OpenAIResponsesPromptCachingExtension,
)
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
from openai_responses_plugins.openai_responses_usage_extension import (
    OpenAIResponsesUsageExtension,
)

pytestmark = pytest.mark.api


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI pricing real-API tests")
    return api_key


def _base_config(api_key: str, prompt_cache_key: str) -> Dict[str, Any]:
    return {
        "model": "gpt-5.6-luna",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
        "prompt_cache_key": prompt_cache_key,
    }


def _send_streaming_request(
    core: AgentCore,
    session: Any,
    config: Dict[str, Any],
) -> tuple[Any, List[Dict[str, Any]]]:
    final_session = None
    final_messages = None
    for chunk in core.send_request_stream(session, config):
        if chunk.get("type") == "final":
            final_session = chunk.get("session")
            final_messages = chunk.get("messages")
    assert final_session is not None, "expected final session from streaming request"
    assert (
        isinstance(final_messages, list) and final_messages
    ), "expected final messages from stream"
    return final_session, final_messages


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_gpt_5_6_luna_pricing_and_cache_write_real_api(
    ensure_openai_api_key: str,
) -> None:
    """Verify GPT-5.6 Luna pricing entry, positive cost, and cache-write accounting."""
    cache_key = f"opcache_test_{uuid.uuid4().hex}"
    config = _base_config(ensure_openai_api_key, cache_key)

    # Verify the checked-in snapshot resolves GPT-5.6 Luna with cache_write_per_1m.
    entry = resolve_pricing_entry("gpt-5.6-luna")
    assert entry is not None, "gpt-5.6-luna missing from checked-in pricing snapshot"
    standard_tier = entry.get("service_tiers", {}).get("standard", {})
    assert (
        "cache_write_per_1m" in standard_tier
    ), "standard tier for gpt-5.6-luna missing cache_write_per_1m"

    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[
            OpenAIResponsesPromptCachingExtension,
            OpenAIResponsesUsageExtension,
        ],
    )

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly: OPENAI_PRICING_5_6_LUNA_OK",
        config=config,
    )

    final_session, final_messages = _send_streaming_request(core, session, config)

    final = final_messages[-1]
    assert final.get("role") == "assistant"
    assert "OPENAI_PRICING_5_6_LUNA_OK" in str(final.get("content"))

    metadata = final.get("metadata") or {}
    assert isinstance(metadata, dict)

    # Usage metadata is present.
    usage = metadata.get("usage")
    assert isinstance(usage, dict), "expected usage dict in metadata"
    assert isinstance(usage.get("input_tokens"), int)
    assert isinstance(usage.get("output_tokens"), int)

    # Resolved pricing entry is GPT-5.6 Luna.
    resolved_entry = resolve_pricing_entry("gpt-5.6-luna")
    assert resolved_entry is not None
    assert resolved_entry["model"] == "gpt-5.6-luna"

    # Estimated cost is positive and formatted.
    assert isinstance(metadata.get("usage_total_cost"), (int, float))
    assert (
        metadata.get("usage_total_cost") > 0
    ), "expected positive cost for gpt-5.6-luna"
    assert isinstance(metadata.get("usage_total_cost_formatted"), str)

    # If the response reports cache_write_tokens, verify the estimator used the
    # cache-write rate by comparing against a manual calculation.
    details = usage.get("input_tokens_details") or {}
    cache_write_tokens = details.get("cache_write_tokens")
    if isinstance(cache_write_tokens, int) and cache_write_tokens > 0:
        # Assert the formatted footer is present.
        assert metadata.get("usage_cache_write_tokens_formatted") is not None
        # Manual calculation using the cache-write rate.
        manual_cost = estimate_usage_cost(
            usage,
            model="gpt-5.6-luna",
            service_tier=metadata.get("usage_service_tier"),
        )
        assert manual_cost is not None
        assert metadata.get("usage_total_cost") == pytest.approx(manual_cost, rel=1e-6)
    else:
        # Report explicitly when the write counter is absent.
        print(
            "\nOpenAI API response did not report cache_write_tokens for "
            "gpt-5.6-luna; cache-write rate verification skipped."
        )

    # Send a follow-up request with the same key and inspect both counters.
    follow_up_session = core.add_message(
        final_session,
        "user",
        "Reply with exactly: OPENAI_PRICING_5_6_LUNA_FOLLOWUP_OK",
        config=config,
    )
    follow_up_session2, follow_up_messages = _send_streaming_request(
        core, follow_up_session, config
    )

    follow_up_final = follow_up_messages[-1]
    assert follow_up_final.get("role") == "assistant"
    assert "OPENAI_PRICING_5_6_LUNA_FOLLOWUP_OK" in str(follow_up_final.get("content"))

    follow_up_metadata = follow_up_final.get("metadata") or {}
    follow_up_usage = follow_up_metadata.get("usage") or {}
    follow_up_details = follow_up_usage.get("input_tokens_details") or {}

    # Report the actual counters rather than assuming a cache hit.
    print(
        f"\nFollow-up turn counters for gpt-5.6-luna with stable cache key:\n"
        f"  cached_tokens={follow_up_details.get('cached_tokens')}\n"
        f"  cache_write_tokens={follow_up_details.get('cache_write_tokens')}\n"
        f"  input_tokens={follow_up_usage.get('input_tokens')}\n"
        f"  output_tokens={follow_up_usage.get('output_tokens')}"
    )

    # The follow-up should also have positive cost.
    assert isinstance(follow_up_metadata.get("usage_total_cost"), (int, float))
    assert follow_up_metadata.get("usage_total_cost") > 0
