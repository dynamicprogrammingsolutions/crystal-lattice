from __future__ import annotations

from typing import Any

import pytest

from plugins.file_reader_tool import FileReaderTool
from plugins.math_tools import MathTools
from zai_test_utils import (
    REASONING_TEST_DIR,
    ZAI_REASONING_MODEL,
    build_reference_core,
    build_zai_cfg,
    reasoning_test_prompt,
    send_request_or_skip,
    zai_model,
)

pytestmark = pytest.mark.api


def _assistant_reasoning(message: dict[str, Any]) -> str:
    metadata = message.get("metadata") or {}
    reasoning = metadata.get("reasoning")
    return reasoning.strip() if isinstance(reasoning, str) else ""


def _assert_tool_calls_have_names(tool_calls: list[dict[str, Any]]) -> None:
    for call in tool_calls:
        function = call.get("function") or {}
        name = function.get("name")
        assert isinstance(name, str) and name.strip(), (
            f"expected non-empty function.name, got {call!r}"
        )


def _bank_file_cfg() -> dict[str, Any]:
    return {
        **build_zai_cfg(
            zai_model("ZAI_REASONING_MODEL", ZAI_REASONING_MODEL),
            request_options={
                "reasoning_effort": "max",
                "thinking": {"type": "enabled", "clear_thinking": False},
                "temperature": 0,
            },
        ),
        "allowed_paths": [str(REASONING_TEST_DIR)],
        "working_directory": str(REASONING_TEST_DIR),
        "max_file_size": 1024 * 1024,
    }


def _bank_file_session(core):
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You have access to the read_file tool. The working directory for file paths "
        f"is: {REASONING_TEST_DIR}. You can use relative paths like 'bank0.json'.",
    )
    return core.add_message(session, "user", reasoning_test_prompt())


def _append_tool_results(core, session, cfg, tool_calls):
    _assert_tool_calls_have_names(tool_calls)
    tool_messages = core.execute_tool_calls(tool_calls, cfg)
    assert tool_messages
    for tool_message in tool_messages:
        session = core.add_message(
            session,
            tool_message.get("role", "tool"),
            tool_message.get("content", ""),
            metadata=tool_message.get("metadata"),
            config=cfg,
        )
    return session


@pytest.mark.integration
@pytest.mark.zai
def test_tools_tool_loop_zai_openai_compat():
    cfg = build_zai_cfg(
        zai_model("ZAI_REASONING_MODEL", ZAI_REASONING_MODEL),
        request_options={"thinking": {"type": "disabled"}, "temperature": 0},
    )

    core = build_reference_core(MathTools)
    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Use the add tool to add 2 and 3. After using tools, reply with just the number.",
    )

    session2, first_finals = send_request_or_skip(core, session, cfg)
    assert first_finals and first_finals[-1]["role"] == "assistant"

    tool_calls = (first_finals[-1].get("metadata") or {}).get("tool_calls") or []
    assert tool_calls

    tool_messages = core.execute_tool_calls(tool_calls, cfg)
    assert tool_messages
    for tool_message in tool_messages:
        session2 = core.add_message(
            session2,
            tool_message.get("role", "tool"),
            tool_message.get("content", ""),
            metadata=tool_message.get("metadata"),
            config=cfg,
        )

    _session3, second_finals = send_request_or_skip(core, session2, cfg)
    assert second_finals and second_finals[-1]["role"] == "assistant"
    assert second_finals[-1].get("content", "").strip() == "5"


@pytest.mark.integration
@pytest.mark.zai
def test_reasoning_history_preserved_across_zai_tool_call():
    cfg = _bank_file_cfg()
    core = build_reference_core(FileReaderTool)

    last_failure: tuple[str, int, int] | None = None
    for _attempt in range(3):
        session = _bank_file_session(core)
        session, first_finals = send_request_or_skip(core, session, cfg)
        assert first_finals and first_finals[-1]["role"] == "assistant"

        first_assistant = first_finals[-1]
        first_reasoning = _assistant_reasoning(first_assistant)
        tool_calls = (first_assistant.get("metadata") or {}).get("tool_calls") or []
        if not first_reasoning or not tool_calls:
            last_failure = ("", len(first_reasoning), len(tool_calls))
            continue

        session = _append_tool_results(core, session, cfg, tool_calls)
        _final_session, final_finals = send_request_or_skip(core, session, cfg)
        assert final_finals and final_finals[-1]["role"] == "assistant"
        content = final_finals[-1].get("content", "").strip()

        if content == "Clock":
            return
        last_failure = (content, len(first_reasoning), len(tool_calls))

    pytest.fail(
        "Z.ai did not preserve its private bank-file reasoning across the tool call. "
        f"Last attempt: content={last_failure[0]!r}, "
        f"first_reasoning_length={last_failure[1]}, "
        f"tool_call_count={last_failure[2]}",
        pytrace=False,
    )


@pytest.mark.integration
@pytest.mark.zai
def test_reasoning_history_preserved_across_zai_user_turn():
    cfg = _bank_file_cfg()
    core = build_reference_core(FileReaderTool)

    last_failure: tuple[str, int, int] | None = None
    for _attempt in range(5):
        session = _bank_file_session(core)
        session, first_finals = send_request_or_skip(core, session, cfg)
        assert first_finals and first_finals[-1]["role"] == "assistant"

        first_assistant = first_finals[-1]
        first_reasoning = _assistant_reasoning(first_assistant)
        tool_calls = (first_assistant.get("metadata") or {}).get("tool_calls") or []
        if not first_reasoning or not tool_calls:
            last_failure = ("", len(first_reasoning), len(tool_calls))
            continue

        session = _append_tool_results(core, session, cfg, tool_calls)
        session = core.add_message(session, "user", "give me the final result")
        _final_session, final_finals = send_request_or_skip(core, session, cfg)
        assert final_finals and final_finals[-1]["role"] == "assistant"
        content = final_finals[-1].get("content", "").strip()

        if content == "Clock":
            return
        last_failure = (content, len(first_reasoning), len(tool_calls))

    pytest.fail(
        "Z.ai did not preserve its private bank-file reasoning across the inserted "
        f"user turn. Last attempt: content={last_failure[0]!r}, "
        f"first_reasoning_length={last_failure[1]}, "
        f"tool_call_count={last_failure[2]}",
        pytrace=False,
    )