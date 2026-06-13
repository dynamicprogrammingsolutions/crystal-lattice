from __future__ import annotations

import pytest

from plugins.math_tools import MathTools
from zai_test_utils import (
    ZAI_BASIC_MODEL,
    ZAI_REASONING_MODEL,
    build_reference_core,
    build_zai_cfg,
    iter_request_stream_or_skip,
    send_request_or_skip,
    zai_model,
)

pytestmark = pytest.mark.api


@pytest.mark.integration
@pytest.mark.zai
def test_usage_metadata_zai_openai_compat():
    cfg = build_zai_cfg(
        zai_model("ZAI_BASIC_MODEL", ZAI_BASIC_MODEL),
        request_options={"thinking": {"type": "disabled"}, "temperature": 0},
    )

    core = build_reference_core()
    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly pong.")

    _session2, finals = send_request_or_skip(core, session, cfg)
    assert finals and finals[-1]["role"] == "assistant"

    metadata = finals[-1].get("metadata") or {}
    assert isinstance(metadata.get("usage"), dict)
    assert isinstance(metadata.get("usage_prompt_tokens"), int)
    assert isinstance(metadata.get("usage_completion_tokens"), int)
    assert isinstance(metadata.get("usage_total_tokens"), int)


@pytest.mark.integration
@pytest.mark.zai
def test_streaming_usage_metadata_zai_openai_compat():
    cfg = build_zai_cfg(
        zai_model("ZAI_BASIC_MODEL", ZAI_BASIC_MODEL),
        request_options={
            "thinking": {"type": "disabled"},
            "temperature": 0,
            "stream_options": {"include_usage": True},
        },
    )

    core = build_reference_core()
    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly pong.")

    final_event = None
    for event in iter_request_stream_or_skip(core, session, cfg):
        if event.get("type") == "final":
            final_event = event

    assert final_event is not None
    assistant = final_event["messages"][-1]
    metadata = assistant.get("metadata") or {}

    assert assistant.get("content", "").strip().lower() == "pong"
    assert isinstance(metadata.get("usage"), dict)
    assert isinstance(metadata.get("usage_total_tokens"), int)


@pytest.mark.integration
@pytest.mark.zai
def test_usage_turn_reasoning_accumulates_across_zai_tool_turn():
    cfg = build_zai_cfg(
        zai_model("ZAI_REASONING_MODEL", ZAI_REASONING_MODEL),
        request_options={"thinking": {"type": "enabled"}, "temperature": 0},
    )

    core = build_reference_core(MathTools)
    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Use the add tool to add 19 and 23. Think step by step before the tool call and again after the tool result. "
        "After the tool result, reply with only the number.",
    )

    session_after_tool_call, first_finals = send_request_or_skip(core, session, cfg)
    assert first_finals and first_finals[-1]["role"] == "assistant"

    first_tool_call = first_finals[-1]
    first_tool_metadata = first_tool_call.get("metadata") or {}
    first_tool_calls = first_tool_metadata.get("tool_calls") or []
    assert first_tool_calls

    tool_messages = core.execute_tool_calls(first_tool_calls, cfg)
    assert tool_messages
    for tool_message in tool_messages:
        session_after_tool_call = core.add_message(
            session_after_tool_call,
            tool_message.get("role", "tool"),
            tool_message.get("content", ""),
            metadata=tool_message.get("metadata"),
            config=cfg,
        )

    final_session, second_finals = send_request_or_skip(core, session_after_tool_call, cfg)
    assert second_finals and second_finals[-1]["role"] == "assistant"
    assert second_finals[-1].get("content", "").strip() == "42"

    assistant_messages = [message for message in final_session.messages if message.role == "assistant"]
    assert len(assistant_messages) == 2

    first_assistant_md = assistant_messages[0].metadata or {}
    second_assistant_md = assistant_messages[1].metadata or {}

    first_reasoning = first_assistant_md.get("usage_reasoning_tokens")
    second_reasoning = second_assistant_md.get("usage_reasoning_tokens")
    first_turn_reasoning = first_assistant_md.get("usage_turn_reasoning_tokens_cumulative")
    second_turn_reasoning = second_assistant_md.get("usage_turn_reasoning_tokens_cumulative")

    assert isinstance(first_reasoning, int) and first_reasoning > 0
    assert isinstance(second_reasoning, int) and second_reasoning > 0
    assert isinstance(first_turn_reasoning, int) and first_turn_reasoning > 0
    assert isinstance(second_turn_reasoning, int) and second_turn_reasoning > 0

    assert first_turn_reasoning == first_reasoning
    assert second_turn_reasoning == first_reasoning + second_reasoning
    assert first_assistant_md.get("usage_turn_reasoning_tokens_cumulative_formatted") == str(
        first_turn_reasoning
    )
    assert second_assistant_md.get("usage_turn_reasoning_tokens_cumulative_formatted") == str(
        second_turn_reasoning
    )