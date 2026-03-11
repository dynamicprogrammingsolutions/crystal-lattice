from __future__ import annotations

import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from openai_responses_plugins.openai_responses_native_compaction_extension import (
    OpenAIResponsesNativeCompactionExtension,
)
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider


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
    core.register_provider(OpenAIResponsesProvider, [OpenAIResponsesNativeCompactionExtension])
    return core


def _config(api_key: str) -> dict[str, object]:
    return {
        "provider": "openai_responses",
        "model": "gpt-5-mini",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
    }


def _assert_has_compaction_placeholder(session) -> None:
    assert any(
        (message.metadata or {}).get("openai_responses_compaction")
        for message in session.messages
    )


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_full_compaction_allows_followup_turn(ensure_openai_api_key: str) -> None:
    core = _build_core()
    config = _config(ensure_openai_api_key)

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly FULL_COMPACTION_TURN_ONE",
        config=config,
    )
    session, first_finals = core.send_request(session, config)

    assert "FULL_COMPACTION_TURN_ONE" in first_finals[-1]["content"]

    compacted_session, result = core.execute_session_action(
        session,
        config,
        plugin_id="openai_responses_native_compaction",
        action_id="compact_native_history",
        params={},
    )

    assert result["message"] == "Compacted the full visible history."
    _assert_has_compaction_placeholder(compacted_session)

    compacted_session = core.add_message(
        compacted_session,
        "user",
        "Reply with exactly FULL_COMPACTION_TURN_TWO",
        config=config,
    )
    session_after_second, second_finals = core.send_request(compacted_session, config)

    assert "FULL_COMPACTION_TURN_TWO" in second_finals[-1]["content"]
    _assert_has_compaction_placeholder(session_after_second)


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_partial_compaction_allows_followup_turn(ensure_openai_api_key: str) -> None:
    core = _build_core()
    config = _config(ensure_openai_api_key)

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly PARTIAL_COMPACTION_TURN_ONE",
        config=config,
    )
    session, first_finals = core.send_request(session, config)
    assert "PARTIAL_COMPACTION_TURN_ONE" in first_finals[-1]["content"]

    session = core.add_message(
        session,
        "user",
        "Reply with exactly PARTIAL_COMPACTION_TURN_TWO",
        config=config,
    )
    session, second_finals = core.send_request(session, config)
    assert "PARTIAL_COMPACTION_TURN_TWO" in second_finals[-1]["content"]

    compacted_session, result = core.execute_session_action(
        session,
        config,
        plugin_id="openai_responses_native_compaction",
        action_id="compact_native_history",
        params={"end_index": 2},
    )

    assert result["message"] == "Compacted visible messages [:2]"
    _assert_has_compaction_placeholder(compacted_session)
    assert any(
        message.content == "PARTIAL_COMPACTION_TURN_TWO"
        for message in compacted_session.messages
    )

    compacted_session = core.add_message(
        compacted_session,
        "user",
        "Reply with exactly PARTIAL_COMPACTION_TURN_THREE",
        config=config,
    )
    session_after_third, third_finals = core.send_request(compacted_session, config)

    assert "PARTIAL_COMPACTION_TURN_THREE" in third_finals[-1]["content"]
    _assert_has_compaction_placeholder(session_after_third)