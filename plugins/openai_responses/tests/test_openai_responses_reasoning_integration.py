from __future__ import annotations

import json
import os
import re
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
from plugins.file_reader_tool import FileReaderTool
from plugins.request_options_feature import RequestOptionsFeature


REPO_ROOT = Path(__file__).resolve().parents[3]
REASONING_DIR = REPO_ROOT / "plugins" / "openrouter_responses" / "tests" / "reasoning_test"
PROMPT_TEMPLATE = (REASONING_DIR / "prompt.txt").read_text(encoding="utf-8")
DEFAULT_SEED = "Fennel 983; Olive 193; Graphite 668."
FOLLOW_UP_SEED = "Juniper 741; Amber 202; Quartz 515."


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    load_dotenv(REPO_ROOT / ".env")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI reasoning integration tests")
    return api_key


def _prompt_for_seed(seed: str) -> str:
    return PROMPT_TEMPLATE.replace(DEFAULT_SEED, seed)


def _expected_label(seed: str) -> str:
    letters = [ch.upper() for ch in seed if ch.isalpha()]
    letter_values = {chr(ord("A") + idx): idx + 1 for idx in range(26)}
    salpha = sum(letter_values[ch] * ((idx % 3) + 1) for idx, ch in enumerate(letters))
    sdigits = sum(int(ch) for ch in seed if ch.isdigit())
    words = re.findall(r"[A-Za-z]+", seed)
    even_initials = {"B", "D", "F", "H", "J", "L", "N", "P", "R", "T", "V", "X", "Z"}
    wc = sum(1 for word in words if word[:1].upper() in even_initials)
    lval = len(letters)
    pval = (salpha + 7 * sdigits + 11 * wc + lval) % 10
    slen = sum(len(word) for word in words)
    bank_index = (slen + lval + pval) % 3

    bank = json.loads((REASONING_DIR / f"bank{bank_index}.json").read_text(encoding="utf-8"))
    items = bank.get("items") if isinstance(bank, dict) else None
    if not isinstance(items, list):
        raise RuntimeError("expected reasoning bank fixture to expose an items list")
    for item in items:
        if isinstance(item, dict) and item.get("id") == pval:
            payload = item.get("payload")
            label = payload.get("label") if isinstance(payload, dict) else None
            if isinstance(label, str) and label:
                return label
    raise RuntimeError(f"expected label for id={pval} in bank{bank_index}.json")


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[OpenAIResponsesReasoningExtension, OpenAIResponsesToolsExtension],
    )
    core.register_feature(RequestOptionsFeature)
    core.register_tool(FileReaderTool)
    return core


def _config(api_key: str) -> Dict[str, Any]:
    return {
        "model": "gpt-5-mini",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 240,
        "temperature": 0.0,
        "reasoning_effort": "high",
        "reasoning_summary": "detailed",
        "allowed_paths": [str(REASONING_DIR)],
        "working_directory": str(REASONING_DIR),
        "max_file_size": 1024 * 1024,
    }


def _run_tool_loop(
    core: AgentCore,
    session: Any,
    config: Dict[str, Any],
    *,
    stream: bool = False,
    max_iterations: int = 6,
) -> Tuple[Any, List[Dict[str, Any]], bool]:
    saw_tool_call = False
    responses: List[Dict[str, Any]] = []

    for _ in range(max_iterations):
        if stream:
            final_session = None
            final_messages: List[Dict[str, Any]] = []
            for chunk in core.send_request_stream(session, config):
                if chunk["type"] == "final":
                    final_session = chunk.get("session")
                    final_messages = chunk.get("messages") or []
                    break
            assert final_session is not None, "expected final streaming event"
            session = final_session
            responses = final_messages
        else:
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


def _new_response_ids(native_messages: List[Dict[str, Any]], seen: set[str]) -> set[str]:
    out: set[str] = set()
    for item in native_messages:
        if not isinstance(item, dict):
            continue
        metadata = item.get("_metadata")
        if not isinstance(metadata, dict):
            continue
        response_id = metadata.get("response_id")
        if isinstance(response_id, str) and response_id and response_id not in seen:
            out.add(response_id)
    return out


def _function_call_output_count(native_messages: List[Dict[str, Any]]) -> int:
    return sum(
        1
        for item in native_messages
        if isinstance(item, dict) and item.get("type") == "function_call_output"
    )


def _response_ids_with_reasoning(native_messages: List[Dict[str, Any]]) -> set[str]:
    out: set[str] = set()
    for item in native_messages:
        if not isinstance(item, dict) or item.get("type") != "reasoning":
            continue
        metadata = item.get("_metadata")
        if not isinstance(metadata, dict):
            continue
        response_id = metadata.get("response_id")
        if isinstance(response_id, str) and response_id:
            out.add(response_id)
    return out


def _assert_reasoning_metadata(message: Dict[str, Any]) -> None:
    metadata = message.get("metadata") or {}
    reasoning = metadata.get("reasoning")
    assert isinstance(reasoning, str)
    assert reasoning.strip()


def _make_session(core: AgentCore, prompt: str) -> Any:
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        (
            "You have access to the read_file tool. The working directory for file paths is: "
            f"{REASONING_DIR}. Use relative paths like 'bank0.json'."
        ),
    )
    session = core.add_message(session, "user", prompt)
    return session


@pytest.mark.integration
@pytest.mark.openai
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_openai_responses_reasoning_single_turn_with_tools(
    ensure_openai_api_key: str,
    stream: bool,
) -> None:
    core = _build_core()
    config = _config(ensure_openai_api_key)

    session = _make_session(core, _prompt_for_seed(DEFAULT_SEED))
    session, responses, saw_tool_call = _run_tool_loop(
        core,
        session,
        config,
        stream=stream,
    )

    assert saw_tool_call, "expected the reasoning scenario to trigger a tool call"
    final_message = responses[-1]
    assert final_message.get("role") == "assistant"
    assert (final_message.get("content") or "").strip() == _expected_label(DEFAULT_SEED)
    _assert_reasoning_metadata(final_message)

    native_messages = (session.metadata or {}).get("native_messages") or []
    assert _function_call_output_count(native_messages) >= 1


@pytest.mark.integration
@pytest.mark.openai
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_openai_responses_reasoning_follow_up_runs_fresh_tool_cycle(
    ensure_openai_api_key: str,
    stream: bool,
) -> None:
    core = _build_core()
    config = _config(ensure_openai_api_key)

    session = _make_session(core, _prompt_for_seed(DEFAULT_SEED))
    session, first_responses, first_saw_tool_call = _run_tool_loop(
        core,
        session,
        config,
        stream=stream,
    )
    assert first_saw_tool_call, "expected a tool call in the initial reasoning turn"
    assert (first_responses[-1].get("content") or "").strip() == _expected_label(DEFAULT_SEED)

    native_before = (session.metadata or {}).get("native_messages") or []
    seen_response_ids = _new_response_ids(native_before, set())
    tool_output_count_before = _function_call_output_count(native_before)
    reasoning_response_ids_before = _response_ids_with_reasoning(native_before)

    session = core.add_message(session, "user", _prompt_for_seed(FOLLOW_UP_SEED), config=config)
    session, second_responses, second_saw_tool_call = _run_tool_loop(
        core,
        session,
        config,
        stream=stream,
    )

    assert second_saw_tool_call, "expected the follow-up reasoning turn to trigger a fresh tool call"
    final_message = second_responses[-1]
    assert final_message.get("role") == "assistant"
    assert (final_message.get("content") or "").strip() == _expected_label(FOLLOW_UP_SEED)

    native_after = (session.metadata or {}).get("native_messages") or []
    assert _function_call_output_count(native_after) > tool_output_count_before
    fresh_response_ids = _new_response_ids(native_after, seen_response_ids)
    assert len(fresh_response_ids) >= 2
    assert _response_ids_with_reasoning(native_after) - reasoning_response_ids_before