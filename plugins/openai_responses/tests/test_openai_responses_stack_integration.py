from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
from openai_responses_plugins.openai_responses_reasoning_extension import (
    OpenAIResponsesReasoningExtension,
)
from openai_responses_plugins.openai_responses_tools_extension import (
    OpenAIResponsesToolsExtension,
)
from openai_responses_plugins.openai_responses_usage_extension import (
    OpenAIResponsesUsageExtension,
)
from openai_responses_plugins.openai_responses_verbosity_extension import (
    OpenAIResponsesVerbosityExtension,
)
from plugins.math_tools import MathTools
from plugins.request_options_feature import RequestOptionsFeature


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI stack integration tests")
    return api_key


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[
            OpenAIResponsesReasoningExtension,
            OpenAIResponsesToolsExtension,
            OpenAIResponsesUsageExtension,
            OpenAIResponsesVerbosityExtension,
        ],
    )
    core.register_feature(RequestOptionsFeature)
    core.register_tool(MathTools)
    return core


def _config(api_key: str) -> Dict[str, Any]:
    return {
        "model": "gpt-5-mini",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
        "enable_reasoning": True,
        "reasoning_effort": "minimal",
        "reasoning_summary": "concise",
        "verbosity": "high",
    }


def _run_tool_loop(
    core: AgentCore,
    session: Any,
    config: Dict[str, Any],
    *,
    max_iterations: int = 5,
) -> Tuple[Any, List[Dict[str, Any]], bool]:
    saw_tool_call = False
    responses: List[Dict[str, Any]] = []

    for _ in range(max_iterations):
        session, responses = core.send_request(session, config)
        assert responses, "expected assistant response"

        metadata = responses[-1].get("metadata") or {}
        tool_calls = metadata.get("tool_calls") or []
        if not isinstance(tool_calls, list) or not tool_calls:
            return session, responses, saw_tool_call

        saw_tool_call = True
        tool_messages = core.execute_tool_calls(tool_calls, config)
        assert tool_messages, "expected tool execution results"
        for tool_message in tool_messages:
            session = core.add_message(
                session,
                role=tool_message.get("role", "tool"),
                content=tool_message.get("content", ""),
                metadata=tool_message.get("metadata"),
                config=config,
            )

    pytest.fail(f"tool loop did not settle within {max_iterations} iterations")


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_tool_reasoning_usage_and_verbosity_stack(
    ensure_openai_api_key: str,
) -> None:
    core = _build_core()
    config = _config(ensure_openai_api_key)

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        (
            "Use the add tool to compute 123 + 456. After you have the tool result, "
            "briefly explain the answer in two or three sentences and include the final "
            "number 579 in the reply."
        ),
    )

    final_session, responses, saw_tool_call = _run_tool_loop(core, session, config)

    assert saw_tool_call, "expected at least one tool call in the live tool loop"
    final_message = responses[-1]
    assert final_message.get("role") == "assistant"

    content = (final_message.get("content") or "").strip()
    assert "579" in content
    assert len(content) >= 40

    metadata = final_message.get("metadata") or {}
    usage = metadata.get("usage")
    assert isinstance(usage, dict)
    assert isinstance(metadata.get("usage_prompt_tokens_formatted"), str)
    assert isinstance(metadata.get("usage_completion_tokens_formatted"), str)

    native_history = (final_session.metadata or {}).get("native_messages") or []
    assert any(
        isinstance(item, dict) and item.get("type") == "reasoning"
        for item in native_history
    )
    assert any(
        isinstance(item, dict) and item.get("type") == "function_call_output"
        for item in native_history
    )