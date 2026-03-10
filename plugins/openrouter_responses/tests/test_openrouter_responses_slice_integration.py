"""Integration tests for `/responses` native-index slicing behavior.

These tests validate that response-segment `native_indices` ownership is
compatible with `AgentCore.slice_session()` and `fork_session()`.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Dict, List, Set

import pytest

from agent_core import AgentCore
from openrouter_responses_plugins.openrouter_responses_provider import OpenRouterResponsesProvider
from openrouter_responses_plugins.openrouter_responses_reasoning_extension import (
    OpenRouterResponsesReasoningExtension,
)
from openrouter_responses_plugins.openrouter_responses_tools_extension import (
    OpenRouterResponsesToolsExtension,
)
from plugins.file_reader_tool import FileReaderTool
from plugins.request_options_feature import RequestOptionsFeature


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"
MODEL = "openai/gpt-5-mini"


def _get_openai_provider_options() -> Dict[str, Any]:
    provider_id = os.getenv("OPENAI_PROVIDER") or "openai"
    return {
        "provider": {
            "order": [provider_id],
            "allow_fallbacks": False,
        }
    }


def _run_turn_with_tool_loop(
    core: AgentCore,
    session: Any,
    config: Dict[str, Any],
    *,
    max_iterations: int = 5,
) -> tuple[Any, bool]:
    saw_tool_call = False

    for _ in range(max_iterations):
        session, responses = core.send_request(session, config)
        assert responses, "expected assistant response"

        last = responses[-1]
        metadata = last.get("metadata") or {}
        tool_calls = metadata.get("tool_calls") or []
        if not isinstance(tool_calls, list) or not tool_calls:
            return session, saw_tool_call

        saw_tool_call = True
        tool_messages = core.execute_tool_calls(tool_calls, config)
        assert tool_messages, "expected tool results when tool_calls are present"
        for tool_msg in tool_messages:
            session = core.add_message(
                session,
                role=tool_msg.get("role", "tool"),
                content=tool_msg.get("content", ""),
                metadata=tool_msg.get("metadata"),
                config=config,
            )

    pytest.fail(f"tool loop did not settle within {max_iterations} iterations")


def _collect_response_ids_from_messages(messages: List[Any], start: int, end: int) -> Set[str]:
    out: Set[str] = set()
    for idx in range(start, end + 1):
        md = messages[idx].metadata or {}
        rid = md.get("response_id")
        if isinstance(rid, str) and rid:
            out.add(rid)
    return out


def _collect_native_response_ids(native_messages: List[Dict[str, Any]]) -> Set[str]:
    out: Set[str] = set()
    for item in native_messages:
        if not isinstance(item, dict):
            continue
        md = item.get("_metadata")
        if not isinstance(md, dict):
            continue
        rid = md.get("response_id")
        if isinstance(rid, str) and rid:
            out.add(rid)
    return out


def _assert_no_dangling_tool_outputs(messages: List[Any]) -> None:
    seen_tool_call_ids: Set[str] = set()
    for msg in messages:
        md = msg.metadata or {}
        if msg.role == "assistant":
            tool_calls = md.get("tool_calls")
            if not isinstance(tool_calls, list):
                continue
            for tc in tool_calls:
                if not isinstance(tc, dict):
                    continue
                call_id = tc.get("id")
                if isinstance(call_id, str) and call_id:
                    seen_tool_call_ids.add(call_id)
            continue

        if msg.role != "tool":
            continue

        tcid = md.get("tool_call_id")
        assert isinstance(tcid, str) and tcid, "tool message missing tool_call_id"
        assert tcid in seen_tool_call_ids, f"dangling tool output for call_id={tcid!r}"


@pytest.fixture(scope="module")
def ensure_api_key() -> None:
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set; skipping OpenRouter slice integration tests")


@pytest.fixture(scope="module")
def two_turn_session_data(ensure_api_key: None) -> Dict[str, Any]:
    core = AgentCore()
    core.register_provider(
        OpenRouterResponsesProvider,
        extensions=[OpenRouterResponsesReasoningExtension, OpenRouterResponsesToolsExtension],
    )
    core.register_feature(RequestOptionsFeature)
    core.register_tool(FileReaderTool)

    test_dir = Path(__file__).parent / "reasoning_test"
    prompt = (test_dir / "prompt.txt").read_text(encoding="utf-8")

    config: Dict[str, Any] = {
        "model": MODEL,
        "api_key": OPENROUTER_API_KEY,
        "base_url": BASE_URL,
        "timeout": 240,
        "enable_reasoning": True,
        "reasoning_effort": "high",
        "allowed_paths": [str(test_dir)],
        "working_directory": str(test_dir),
        "max_file_size": 1024 * 1024,
        "request_options": _get_openai_provider_options(),
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        (
            "You have access to read_file. Use relative paths from the working "
            f"directory: {test_dir}."
        ),
    )

    session = core.add_message(session, "user", prompt)
    first_user_index = len(session.messages) - 1

    session, first_turn_saw_tool_call = _run_turn_with_tool_loop(
        core,
        session,
        config,
    )
    assert first_turn_saw_tool_call, "expected at least one tool call in first turn"
    first_turn_end_index = len(session.messages) - 1

    native_messages = session.metadata.get("native_messages") or []
    assert isinstance(native_messages, list)

    tool_call_assistant = next(
        (
            m
            for m in session.messages[first_user_index + 1 : first_turn_end_index + 1]
            if m.role == "assistant"
            and isinstance((m.metadata or {}).get("tool_calls"), list)
            and (m.metadata or {}).get("tool_calls")
        ),
        None,
    )
    assert tool_call_assistant is not None, "expected a tool-call assistant message in first turn"
    tmd = tool_call_assistant.metadata or {}
    rid = tmd.get("response_id")
    assert isinstance(rid, str) and rid, "expected tool-call assistant response_id"

    owned_indices = tmd.get("native_indices") or []
    assert isinstance(owned_indices, list) and all(isinstance(i, int) for i in owned_indices)
    assert len(owned_indices) > 1, "expected segment-wide native_indices mapping for tool-call assistant"

    segment_indices = [
        i
        for i, item in enumerate(native_messages)
        if isinstance(item, dict)
        and isinstance(item.get("_metadata"), dict)
        and item["_metadata"].get("response_id") == rid
    ]
    assert segment_indices, "expected native response segment for tool-call assistant"
    assert set(owned_indices) == set(segment_indices)

    session = core.add_message(
        session,
        "user",
        "Without using tools, repeat your previous answer in uppercase only.",
        config=config,
    )
    second_user_index = len(session.messages) - 1

    session, _second_turn_saw_tool_call = _run_turn_with_tool_loop(
        core,
        session,
        config,
        max_iterations=3,
    )
    second_turn_end_index = len(session.messages) - 1

    first_turn_response_ids = _collect_response_ids_from_messages(
        session.messages,
        first_user_index,
        first_turn_end_index,
    )
    second_turn_response_ids = _collect_response_ids_from_messages(
        session.messages,
        second_user_index,
        second_turn_end_index,
    )

    assert first_turn_response_ids, "expected first-turn response ids"
    assert second_turn_response_ids, "expected second-turn response ids"

    return {
        "core": core,
        "config": config,
        "session": session,
        "first_user_index": first_user_index,
        "first_turn_end_index": first_turn_end_index,
        "second_user_index": second_user_index,
        "second_turn_end_index": second_turn_end_index,
        "first_turn_response_ids": first_turn_response_ids,
        "second_turn_response_ids": second_turn_response_ids,
    }


@pytest.mark.integration
@pytest.mark.openrouter
def test_slice_delete_first_turn_removes_first_turn_native_segments(
    two_turn_session_data: Dict[str, Any],
) -> None:
    core: AgentCore = two_turn_session_data["core"]
    config: Dict[str, Any] = two_turn_session_data["config"]
    session = two_turn_session_data["session"]

    first_user_index = two_turn_session_data["first_user_index"]
    first_turn_end_index = two_turn_session_data["first_turn_end_index"]
    first_turn_response_ids: Set[str] = two_turn_session_data["first_turn_response_ids"]
    second_turn_response_ids: Set[str] = two_turn_session_data["second_turn_response_ids"]

    remove_indices = list(range(first_user_index, first_turn_end_index + 1))
    sliced = core.slice_session(session, config, remove_indices=remove_indices)

    new_native = sliced.metadata.get("native_messages") or []
    assert isinstance(new_native, list)
    new_native_response_ids = _collect_native_response_ids(new_native)
    assert first_turn_response_ids.isdisjoint(new_native_response_ids)
    assert second_turn_response_ids.issubset(new_native_response_ids)

    _assert_no_dangling_tool_outputs(sliced.messages)

    followup = core.add_message(
        sliced,
        "user",
        "Answer with OK only.",
        config=config,
    )
    next_session, next_responses = core.send_request(followup, config)
    assert next_session is not None
    assert isinstance(next_responses, list) and next_responses


@pytest.mark.integration
@pytest.mark.openrouter
def test_fork_first_turn_keeps_only_first_turn_native_segments(
    two_turn_session_data: Dict[str, Any],
) -> None:
    core: AgentCore = two_turn_session_data["core"]
    config: Dict[str, Any] = two_turn_session_data["config"]
    session = two_turn_session_data["session"]

    first_turn_end_index = two_turn_session_data["first_turn_end_index"]
    first_turn_response_ids: Set[str] = two_turn_session_data["first_turn_response_ids"]
    second_turn_response_ids: Set[str] = two_turn_session_data["second_turn_response_ids"]

    forked = core.fork_session(session, config, upto_index=first_turn_end_index, new_session_id="slice-fork")

    new_native = forked.metadata.get("native_messages") or []
    assert isinstance(new_native, list)
    new_native_response_ids = _collect_native_response_ids(new_native)
    assert first_turn_response_ids.issubset(new_native_response_ids)
    assert second_turn_response_ids.isdisjoint(new_native_response_ids)

    core._verify_native_integrity(forked)  # type: ignore[attr-defined]
    _assert_no_dangling_tool_outputs(forked.messages)

    followup = core.add_message(
        forked,
        "user",
        "Answer with DONE only.",
        config=config,
    )
    next_session, next_responses = core.send_request(followup, config)
    assert next_session is not None
    assert isinstance(next_responses, list) and next_responses