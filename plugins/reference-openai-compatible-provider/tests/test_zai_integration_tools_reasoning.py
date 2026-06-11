from __future__ import annotations

import re

import pytest

from plugins.math_tools import MathTools
from zai_test_utils import (
    ZAI_REASONING_MODEL,
    build_reference_core,
    build_zai_cfg,
    send_request_or_skip,
    zai_model,
)

_HIDDEN_WORD_OPTIONS = [
    "North",
    "South",
    "East",
    "West",
]
pytestmark = pytest.mark.api


def _extract_hidden_word(reasoning: str) -> str | None:
    if not reasoning:
        return None

    match = re.search(r"SECRET_WORD=(?P<word>[A-Za-z]+)", reasoning, flags=re.IGNORECASE)
    if match:
        word = match.group("word")
        if word in _HIDDEN_WORD_OPTIONS:
            return word

    hits = [
        option
        for option in _HIDDEN_WORD_OPTIONS
        if re.search(rf"\b{re.escape(option)}\b", reasoning)
    ]
    return hits[-1] if hits else None


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
def test_tools_reasoning_round_trip_zai():
    cfg = build_zai_cfg(
        zai_model("ZAI_REASONING_MODEL", ZAI_REASONING_MODEL),
        request_options={"thinking": {"type": "enabled"}, "temperature": 0},
    )

    core = build_reference_core(MathTools)
    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Use the add tool to add 2 and 3. Keep your reasoning private. "
        "After the tool result, reply with only the number.",
    )

    session2, first_finals = send_request_or_skip(core, session, cfg)
    assert first_finals and first_finals[-1]["role"] == "assistant"

    first_assistant = first_finals[-1]
    first_metadata = first_assistant.get("metadata") or {}
    first_reasoning = first_metadata.get("reasoning_content") or first_metadata.get(
        "reasoning"
    )
    first_tool_calls = first_metadata.get("tool_calls") or []

    assert isinstance(first_reasoning, str) and first_reasoning.strip()
    assert first_tool_calls

    tool_messages = core.execute_tool_calls(first_tool_calls, cfg)
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

    second_assistant = second_finals[-1]
    second_metadata = second_assistant.get("metadata") or {}
    second_reasoning = second_metadata.get("reasoning_content") or second_metadata.get(
        "reasoning"
    )

    assert second_assistant.get("content", "").strip() == "5"
    assert isinstance(second_reasoning, str) and second_reasoning.strip()


@pytest.mark.integration
@pytest.mark.zai
def test_preserved_reasoning_hidden_word_zai():
    cfg = build_zai_cfg(
        zai_model("ZAI_REASONING_MODEL", ZAI_REASONING_MODEL),
        request_options={
            "thinking": {"type": "enabled", "clear_thinking": False},
            "temperature": 0,
        },
    )

    core = build_reference_core(MathTools)
    prompt = (
        "Before calling any tools, privately create a random integer seed between 100 and 999. "
        "Use that private seed to select exactly one hidden word from this ordered list: "
        + ", ".join(_HIDDEN_WORD_OPTIONS)
        + ". Use this private rule: hidden_index = (seed + 2 * SUM) mod 4, "
        "where SUM is the result of adding 19 and 23 with the add tool. "
        "Do not reveal the seed, hidden_index, or hidden word in visible output. "
        "After you receive the tool result, keep a private checkpoint line exactly formatted as "
        "SECRET_WORD=<word> in your private reasoning only. "
        "Never include SECRET_WORD or the hidden word in visible content. "
        "Visible output after the tool result must be only the numeric sum and nothing else."
    )
    followup = (
        "The prior secrecy rule applied only to the previous turn. You are now explicitly "
        "allowed to reveal the stored SECRET_WORD. Return only the <word> value from your "
        "previous private reasoning."
    )

    last_failure: tuple[str | None, str | None, str | None] | None = None
    for _ in range(5):
        session = core.create_session()
        session = core.add_message(session, "user", prompt)

        session2, first_finals = send_request_or_skip(core, session, cfg)
        assert first_finals and first_finals[-1]["role"] == "assistant"

        first_tool_calls = (first_finals[-1].get("metadata") or {}).get("tool_calls") or []
        assert first_tool_calls

        tool_messages = core.execute_tool_calls(first_tool_calls, cfg)
        for tool_message in tool_messages:
            session2 = core.add_message(
                session2,
                tool_message.get("role", "tool"),
                tool_message.get("content", ""),
                metadata=tool_message.get("metadata"),
                config=cfg,
            )

        session3, second_finals = send_request_or_skip(core, session2, cfg)
        assert second_finals and second_finals[-1]["role"] == "assistant"

        second_assistant = second_finals[-1]
        second_content = second_assistant.get("content", "").strip()
        second_metadata = second_assistant.get("metadata") or {}
        second_reasoning = second_metadata.get("reasoning_content") or ""
        hidden_word = _extract_hidden_word(second_reasoning)

        if second_content != "42":
            last_failure = (hidden_word, second_content, None)
            continue
        if not isinstance(second_reasoning, str) or not second_reasoning.strip():
            last_failure = (hidden_word, second_content, None)
            continue
        if hidden_word not in _HIDDEN_WORD_OPTIONS:
            last_failure = (hidden_word, second_content, None)
            continue
        if hidden_word in second_content:
            last_failure = (hidden_word, second_content, None)
            continue

        session3 = core.add_message(session3, "user", followup)
        _session4, third_finals = send_request_or_skip(core, session3, cfg)
        assert third_finals and third_finals[-1]["role"] == "assistant"
        third_content = third_finals[-1].get("content", "").strip()
        if third_content == hidden_word:
            return
        last_failure = (hidden_word, second_content, third_content)

    pytest.fail(
        "Preserved Z.ai reasoning checkpoint did not survive the follow-up turn. "
        f"Last attempt details: hidden_word={last_failure[0]!r}, "
        f"second_content={last_failure[1]!r}, third_content={last_failure[2]!r}",
        pytrace=False,
    )