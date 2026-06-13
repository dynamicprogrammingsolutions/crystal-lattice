from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from openai_responses_plugins.openai_responses_flex_processing_extension import (
    OpenAIResponsesFlexProcessingExtension,
)
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
from openai_responses_plugins.openai_responses_usage_extension import OpenAIResponsesUsageExtension


pytestmark = pytest.mark.api


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI usage integration tests")
    return api_key


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_nonstreaming_usage_metadata_real_api(
    ensure_openai_api_key: str,
) -> None:
    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[OpenAIResponsesUsageExtension],
    )

    config = {
        "model": "gpt-5-mini",
        "api_key": ensure_openai_api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly: OPENAI_USAGE_OK")

    new_session, responses = core.send_request(session, config)

    assert new_session is not None
    assert responses

    final = responses[-1]
    assert final.get("role") == "assistant"
    assert "OPENAI_USAGE_OK" in str(final.get("content"))

    metadata = final.get("metadata") or {}
    usage = metadata.get("usage")

    assert isinstance(usage, dict)
    assert isinstance(metadata.get("usage_prompt_tokens_formatted"), str)
    assert isinstance(metadata.get("usage_completion_tokens_formatted"), str)
    assert isinstance(metadata.get("usage_total_cost"), (int, float))
    assert isinstance(metadata.get("usage_total_cost_formatted"), str)
    assert isinstance(metadata.get("usage_total_cost_cumulative"), (int, float))
    assert isinstance(metadata.get("usage_total_cost_cumulative_formatted"), str)
    assert isinstance(metadata.get("usage_turn_cost_cumulative"), (int, float))
    assert isinstance(metadata.get("usage_turn_cost_cumulative_formatted"), str)
    assert isinstance(metadata.get("usage_turn_reasoning_tokens_cumulative"), int)
    assert isinstance(metadata.get("usage_turn_reasoning_tokens_cumulative_formatted"), str)
    assert "usage_estimated_cost" not in metadata
    assert "usage_cost_source" not in metadata
    assert "usage_pricing_model" not in metadata

    native_history = (new_session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert any(
        isinstance(item, dict)
        and isinstance(item.get("_metadata"), dict)
        and isinstance(item["_metadata"].get("usage"), dict)
        for item in native_history
    )

def _maybe_skip_flex_unavailable(exc: Exception) -> None:
    message = str(exc).lower()
    skip_markers = (
        "service_tier",
        "flex",
        "unsupported",
        "not available",
        "not enabled",
        "permission",
        "entitlement",
        "invalid value",
    )
    if any(marker in message for marker in skip_markers):
        pytest.skip(f"OpenAI flex processing unavailable for this account/model: {exc}")


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_nonstreaming_usage_metadata_surfaces_flex_tier_real_api(
    ensure_openai_api_key: str,
) -> None:
    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[OpenAIResponsesFlexProcessingExtension, OpenAIResponsesUsageExtension],
    )

    config = {
        "model": "gpt-5-mini",
        "api_key": ensure_openai_api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
        "enable_flex_processing": True,
        "flex_timeout_seconds": 300,
        "enable_flex_retries": True,
        "flex_max_retries": 2,
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly: OPENAI_USAGE_FLEX_OK")

    try:
        _new_session, responses = core.send_request(session, config)
    except Exception as exc:
        _maybe_skip_flex_unavailable(exc)
        raise

    assert responses
    final = responses[-1]
    assert final.get("role") == "assistant"
    assert "OPENAI_USAGE_FLEX_OK" in str(final.get("content"))

    metadata = final.get("metadata") or {}
    assert metadata.get("usage_service_tier") == "flex"
    assert isinstance(metadata.get("usage_total_cost"), (int, float))
    assert isinstance(metadata.get("usage_total_cost_formatted"), str)
