from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
from openai_responses_plugins.openai_responses_reasoning_extension import (
    OpenAIResponsesReasoningExtension,
)
from plugins.request_options_feature import RequestOptionsFeature


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI integration tests")
    return api_key


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[OpenAIResponsesReasoningExtension],
    )
    core.register_feature(RequestOptionsFeature)
    return core


def _config(api_key: str) -> dict[str, object]:
    return {
        "model": "gpt-5-mini",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
        "enable_reasoning": True,
        "reasoning_effort": "minimal",
        "reasoning_summary": "concise",
    }


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_non_streaming_reasoning_metadata_visible(
    ensure_openai_api_key: str,
) -> None:
    core = _build_core()
    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly: OPENAI_REASONING_OK")

    _new_session, responses = core.send_request(session, _config(ensure_openai_api_key))

    assert responses
    final = responses[-1]
    assert final.get("role") == "assistant"
    assert "OPENAI_REASONING_OK" in (final.get("content") or "")

    metadata = final.get("metadata") or {}
    reasoning = metadata.get("reasoning")
    assert isinstance(reasoning, str)
    assert reasoning.strip()

    raw_reasoning = metadata.get("openai_responses_reasoning")
    assert isinstance(raw_reasoning, dict)
    raw_items = raw_reasoning.get("items")
    assert isinstance(raw_items, list)
    assert raw_items
    assert raw_items[0].get("type") == "reasoning"


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_streaming_reasoning_metadata_visible(
    ensure_openai_api_key: str,
) -> None:
    core = _build_core()
    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly: OPENAI_REASONING_STREAM_OK",
    )

    final_message = None
    for event in core.send_request_stream(session, _config(ensure_openai_api_key)):
        if event["type"] == "final":
            messages = event.get("messages") or []
            if messages:
                final_message = messages[-1]

    assert final_message is not None
    assert final_message.get("role") == "assistant"
    assert "OPENAI_REASONING_STREAM_OK" in (final_message.get("content") or "")

    metadata = final_message.get("metadata") or {}
    reasoning = metadata.get("reasoning")
    assert isinstance(reasoning, str)
    assert reasoning.strip()

    raw_reasoning = metadata.get("openai_responses_reasoning")
    assert isinstance(raw_reasoning, dict)
    raw_items = raw_reasoning.get("items")
    assert isinstance(raw_items, list)
    assert raw_items
    assert raw_items[0].get("type") == "reasoning"