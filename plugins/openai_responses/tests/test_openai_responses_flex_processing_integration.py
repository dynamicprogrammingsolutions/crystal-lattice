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


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI flex integration tests")
    return api_key


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[OpenAIResponsesFlexProcessingExtension],
    )
    return core


def _config(api_key: str) -> dict[str, object]:
    return {
        "model": "gpt-5-mini",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
        "enable_flex_processing": True,
        "flex_timeout_seconds": 300,
        "enable_flex_retries": True,
        "flex_max_retries": 2,
    }


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
def test_openai_responses_non_streaming_surfaces_flex_service_tier(
    ensure_openai_api_key: str,
) -> None:
    core = _build_core()
    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly: OPENAI_FLEX_OK")

    try:
        _new_session, responses = core.send_request(session, _config(ensure_openai_api_key))
    except Exception as exc:
        _maybe_skip_flex_unavailable(exc)
        raise

    assert responses
    final = responses[-1]
    assert final.get("role") == "assistant"
    assert "OPENAI_FLEX_OK" in str(final.get("content"))

    metadata = final.get("metadata") or {}
    assert metadata.get("openai_service_tier") == "flex"
    assert metadata.get("flex_processing_applied") is True
