"""Integration tests comparing streaming vs non-streaming reasoning output for `/responses`.

OpenRouter `/responses` returns reasoning as output items (e.g. `type: "reasoning"`).
For the UI/terminal, the provider also exposes a `metadata.reasoning` summary
string on the final assistant core message when available.
"""

from __future__ import annotations

import os

import pytest

from agent_core import AgentCore
from openrouter_responses_plugins.openrouter_responses_provider import OpenRouterResponsesProvider
from openrouter_responses_plugins.openrouter_responses_reasoning_extension import (
    OpenRouterResponsesReasoningExtension,
)
from plugins.request_options_feature import RequestOptionsFeature


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"

MODELS = {
    "claude": "anthropic/claude-sonnet-4",
    "gpt": "openai/gpt-5-mini",
    "grok": "x-ai/grok-4.1-fast",
}

TEST_PROMPT = "Calculate 23 + 47 step by step. Show your reasoning."


@pytest.fixture(scope="module")
def ensure_api_key() -> None:
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set; skipping OpenRouter reasoning comparison tests")


def _last_response_id(native: list[dict]) -> str | None:
    for item in reversed(native):
        if not isinstance(item, dict):
            continue
        md = item.get("_metadata")
        if not isinstance(md, dict):
            continue
        rid = md.get("response_id")
        if isinstance(rid, str) and rid:
            return rid
    return None


def _extract_reasoning_formats_from_native(native: list[dict]) -> set[str]:
    rid = _last_response_id(native)
    if not rid:
        return set()
    formats: set[str] = set()
    for item in native:
        if not isinstance(item, dict) or item.get("type") != "reasoning":
            continue
        md = item.get("_metadata")
        if not isinstance(md, dict) or md.get("response_id") != rid:
            continue
        fmt = item.get("format")
        if isinstance(fmt, str) and fmt:
            formats.add(fmt)
    return formats


def _extract_reasoning_text_from_core(msg: dict) -> str:
    md = msg.get("metadata") or {}
    if not isinstance(md, dict):
        return ""
    val = md.get("reasoning")
    return val if isinstance(val, str) else ""


@pytest.mark.integration
@pytest.mark.openrouter
@pytest.mark.parametrize("model_key", ["claude", "gpt", "grok"])
def test_reasoning_items_streaming_vs_nonstreaming(ensure_api_key: None, model_key: str) -> None:
    core = AgentCore()
    core.register_provider(OpenRouterResponsesProvider, extensions=[OpenRouterResponsesReasoningExtension])
    core.register_feature(RequestOptionsFeature)

    config = {
        "model": MODELS[model_key],
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 60,
        "enable_reasoning": True,
    }

    # Non-streaming
    session1 = core.create_session()
    session1 = core.add_message(session1, "user", TEST_PROMPT)
    s1, responses1 = core.send_request(session1, config)
    msg1 = responses1[-1]

    # Streaming
    session2 = core.create_session()
    session2 = core.add_message(session2, "user", TEST_PROMPT)
    final_session = None
    for chunk in core.send_request_stream(session2, config):
        if chunk.get("type") == "final":
            final_session = chunk.get("session")
    assert final_session is not None

    md1 = getattr(s1, "metadata", None) or {}
    native1 = md1.get("native_messages") or []
    assert isinstance(native1, list)

    md2 = getattr(final_session, "metadata", None) or {}
    native2 = md2.get("native_messages") or []
    assert isinstance(native2, list)

    formats1 = _extract_reasoning_formats_from_native([m for m in native1 if isinstance(m, dict)])
    formats2 = _extract_reasoning_formats_from_native([m for m in native2 if isinstance(m, dict)])

    # Not all providers emit reasoning items consistently, but when they do we
    # expect streaming/non-streaming to agree on formats.
    if not formats1 and not formats2:
        pytest.skip(f"Model {MODELS[model_key]} did not return reasoning items")
    assert formats1 == formats2

    # UI/terminal reasoning summary is best-effort and model/provider-dependent,
    # so do not assert its presence here.
