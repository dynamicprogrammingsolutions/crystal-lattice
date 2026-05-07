from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from feature_system_message.system_message_feature import SystemMessageFeature
from openai_responses_plugins import (
    OpenAIResponsesChatGPTAuthFeature,
    OpenAIResponsesProvider,
    OpenAIResponsesToolsExtension,
    OpenAIResponsesUsageExtension,
)
from plugins.math_tools import MathTools


REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CHATGPT_AUTH_STATE_DIR = (
    REPO_ROOT / "plugins" / "chatgpt-auth-app" / "tests" / ".manual-state"
)


def _manual_state_dir() -> Path:
    raw = os.getenv("CHATGPT_TEST_STATE_DIR")
    if isinstance(raw, str) and raw.strip():
        return Path(raw).expanduser()
    return _DEFAULT_CHATGPT_AUTH_STATE_DIR


def _credentials_path() -> Path:
    return _manual_state_dir() / "auth" / "chatgpt-auth.json"


def _load_saved_credentials() -> dict[str, object]:
    path = _credentials_path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        pytest.skip(f"saved ChatGPT login not found at {path}")
    if not isinstance(payload, dict):
        pytest.skip(f"saved ChatGPT login at {path} is not a JSON object")
    return payload


def _chatgpt_config(credentials_path: Path) -> dict[str, object]:
    model = os.getenv("OPENAI_RESPONSES_CHATGPT_MODEL") or "gpt-5.5"
    return {
        "model": model,
        "auth_mode": "chatgpt",
        "chatgpt_credentials_path": str(credentials_path),
        "chatgpt_base_url": os.getenv("OPENAI_CHATGPT_BASE_URL")
        or "https://chatgpt.com/backend-api/codex",
        "system_message_as_instructions": True,
        "system_message": (
            "You are a precise assistant. "
            "When the user explicitly tells you to use a tool, you must call the tool before answering."
        ),
        "show_estimated_cached_tokens": True,
        "show_openai_auth_mode": True,
        "timeout": 180,
    }


def _send_streaming_request(
    core: AgentCore,
    session: Any,
    config: Dict[str, Any],
) -> Tuple[Any, List[Dict[str, Any]]]:
    final_session = None
    final_messages = None
    for chunk in core.send_request_stream(session, config):
        if chunk.get("type") == "final":
            final_session = chunk.get("session")
            final_messages = chunk.get("messages")
    assert final_session is not None, "expected final session from streaming request"
    assert isinstance(final_messages, list) and final_messages, "expected final messages from stream"
    return final_session, final_messages


def _response_native_items(session: Any, response_id: str) -> List[Dict[str, Any]]:
    native_history = (session.metadata or {}).get("native_messages") or []
    return [
        item
        for item in native_history
        if isinstance(item, dict)
        and isinstance(item.get("_metadata"), dict)
        and item["_metadata"].get("response_id") == response_id
    ]


def _assert_chatgpt_usage_metadata(message: Dict[str, Any], session: Any) -> int:
    metadata = message.get("metadata") or {}
    response_id = metadata.get("response_id")

    assert message.get("role") == "assistant"
    assert isinstance(response_id, str) and response_id
    assert isinstance(metadata.get("usage"), dict)
    assert metadata.get("usage_effective_auth_mode") == "chatgpt"
    assert metadata.get("usage_effective_auth_mode_label") == "ChatGPT"
    assert isinstance(metadata.get("usage_estimated_cached_tokens"), int)
    assert isinstance(metadata.get("usage_estimated_cached_tokens_formatted"), str)
    assert "usage_cached_tokens_formatted" not in metadata
    assert isinstance(metadata.get("usage_total_cost"), (int, float))
    assert isinstance(metadata.get("usage_total_cost_formatted"), str)
    assert isinstance(metadata.get("usage_turn_cost_cumulative"), (int, float))
    assert isinstance(metadata.get("usage_turn_cost_cumulative_formatted"), str)

    response_native = _response_native_items(session, response_id)
    assert response_native, "expected persisted native items for assistant response"
    assert any(
        isinstance((item.get("_metadata") or {}).get("usage"), dict)
        for item in response_native
    ), "expected at least one native response item to carry usage metadata"

    return int(metadata["usage_estimated_cached_tokens"])


def _run_tool_turn_streaming(
    core: AgentCore,
    session: Any,
    config: Dict[str, Any],
    *,
    prompt: str,
    expected_text: str,
    max_iterations: int = 5,
) -> Tuple[Any, List[Dict[str, Any]], List[int]]:
    session = core.add_message(session, "user", prompt, config=config)
    assistant_turns: List[Dict[str, Any]] = []
    estimates: List[int] = []
    saw_tool_call = False

    for _ in range(max_iterations):
        session, responses = _send_streaming_request(core, session, config)
        assistant = responses[-1]
        assistant_turns.append(assistant)
        estimates.append(_assert_chatgpt_usage_metadata(assistant, session))

        tool_calls = (assistant.get("metadata") or {}).get("tool_calls") or []
        if not isinstance(tool_calls, list) or not tool_calls:
            break

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
    else:
        pytest.fail(f"tool loop did not settle within {max_iterations} iterations")

    assert saw_tool_call, "expected at least one tool call in this ChatGPT turn"
    assert len(assistant_turns) >= 2, "expected multiple assistant turns for this user turn"
    final = assistant_turns[-1]
    assert final.get("role") == "assistant"
    assert isinstance(final.get("content"), str)
    assert expected_text in final["content"]
    return session, assistant_turns, estimates


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_chatgpt_saved_login_usage_multi_turn_tool_loop() -> None:
    load_dotenv(REPO_ROOT / ".env")

    credentials_path = _credentials_path()
    _load_saved_credentials()

    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[OpenAIResponsesToolsExtension, OpenAIResponsesUsageExtension],
    )
    core.register_feature(OpenAIResponsesChatGPTAuthFeature)
    core.register_feature(SystemMessageFeature)
    core.register_tool(MathTools)

    config = _chatgpt_config(credentials_path)

    session = core.create_session()

    session, turn1_responses, turn1_estimates = _run_tool_turn_streaming(
        core,
        session,
        config,
        prompt=(
            "Use the add tool exactly once to compute 123 + 456. "
            "After the tool result, reply with exactly: TURN1=579"
        ),
        expected_text="TURN1=579",
    )
    session, turn2_responses, turn2_estimates = _run_tool_turn_streaming(
        core,
        session,
        config,
        prompt=(
            "Use the add tool exactly once to compute 10 + 20. "
            "After the tool result, reply with exactly: TURN2=30"
        ),
        expected_text="TURN2=30",
    )

    assert len(turn1_responses) >= 2
    assert len(turn2_responses) >= 2
    assert turn1_estimates[0] == 0
    assert any(value > 0 for value in turn1_estimates[1:]), (
        "expected a later assistant response in turn 1 to have non-zero estimated cached tokens"
    )
    assert turn2_estimates[0] > 0, (
        "expected the first assistant response in turn 2 to reuse estimated cached tokens"
    )