from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
from openai_responses_plugins.openai_responses_verbosity_extension import (
    OpenAIResponsesVerbosityExtension,
)


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI verbosity integration tests")
    return api_key


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[OpenAIResponsesVerbosityExtension],
    )
    return core


def _config(api_key: str) -> dict[str, object]:
    return {
        "model": "gpt-5-mini",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
        "verbosity": "high",
    }


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_non_streaming_accepts_verbosity_request(
    ensure_openai_api_key: str,
) -> None:
    core = _build_core()
    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "In two short paragraphs, explain why unit tests help prevent regressions.",
    )

    _new_session, responses = core.send_request(session, _config(ensure_openai_api_key))

    assert responses
    final = responses[-1]
    assert final.get("role") == "assistant"

    content = (final.get("content") or "").strip()
    assert content
    assert len(content) >= 40