from __future__ import annotations

import os
from pathlib import Path
from typing import Any

import pytest

from agent_core import AgentCore
from plugins.file_reader_tool import FileReaderTool
from plugins.request_options_feature import RequestOptionsFeature

from anthropic_plugins import (
    AnthropicContextEditingExtension,
    AnthropicProvider,
    AnthropicReasoningExtension,
    AnthropicToolsExtension,
    AnthropicUsageExtension,
)


pytestmark = [
    pytest.mark.integration,
    pytest.mark.api,
    pytest.mark.anthropic,
    pytest.mark.slow_integration,
]

REPO_ROOT = Path(__file__).resolve().parents[3]
REASONING_TEST_DIR = REPO_ROOT / "core/python/tests/reasoning_test"


def _api_key() -> str:
    value = os.getenv("ANTHROPIC_API_KEY")
    if not value:
        pytest.skip("ANTHROPIC_API_KEY is required")
    return value


def _haiku_model() -> str:
    return os.getenv("ANTHROPIC_HAIKU_TEST_MODEL", "claude-haiku-4-5-20251001")


def _sonnet_model() -> str:
    return os.getenv("ANTHROPIC_SONNET_TEST_MODEL", "claude-sonnet-5")


def _base_config(model: str, **overrides: Any) -> dict[str, Any]:
    _api_key()
    return {
        "provider": "anthropic",
        "base_url": os.getenv("ANTHROPIC_BASE_URL", "https://api.anthropic.com"),
        "model": model,
        "timeout": 180,
        "max_tokens": 2048,
        "allowed_paths": [str(REASONING_TEST_DIR)],
        "working_directory": str(REASONING_TEST_DIR),
        "max_file_size": 1024 * 1024,
        **overrides,
    }


def _manual_config() -> dict[str, Any]:
    return _base_config(
        _haiku_model(),
        request_options={
            "thinking": {
                "type": "enabled",
                "budget_tokens": 1024,
            }
        },
    )


def _adaptive_context_config(*, keep: Any) -> dict[str, Any]:
    retention = "all" if keep == "all" else "turns"
    turns_to_keep = (
        keep.get("value")
        if isinstance(keep, dict) and isinstance(keep.get("value"), int)
        else 1
    )
    return _base_config(
        _sonnet_model(),
        anthropic_thinking_retention=retention,
        anthropic_thinking_turns_to_keep=turns_to_keep,
        request_options={
            "thinking": {
                "type": "adaptive",
                "display": "summarized",
            },
            "output_config": {"effort": "high"},
        },
    )


def _core() -> AgentCore:
    core = AgentCore()
    core.register_feature(RequestOptionsFeature)
    core.register_provider(
        AnthropicProvider,
        extensions=[
            AnthropicToolsExtension,
            AnthropicReasoningExtension,
            AnthropicContextEditingExtension,
            AnthropicUsageExtension,
        ],
    )
    core.register_tool(FileReaderTool)
    return core


def _reasoning_prompt() -> str:
    return (REASONING_TEST_DIR / "prompt.txt").read_text(encoding="utf-8")


def _new_session(core: AgentCore, config: dict[str, Any]):
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You have access to the read_file tool. The working directory for file "
        f"paths is: {REASONING_TEST_DIR}. Resolve relative paths such as "
        "'bank0.json' against that directory.",
        config=config,
    )
    return core.add_message(
        session,
        "user",
        _reasoning_prompt(),
        config=config,
    )


def _request(core: AgentCore, session: Any, config: dict[str, Any], *, stream: bool):
    if not stream:
        return core.send_request(session, config)

    final_event = None
    for event in core.send_request_stream(session, config):
        if event.get("type") == "final":
            final_event = event
    assert final_event is not None, "expected final streaming event"
    return final_event["session"], final_event["messages"]


def _assistant_with_content(
    messages: list[dict[str, Any]],
) -> dict[str, Any] | None:
    for message in reversed(messages):
        if message.get("role") == "assistant" and message.get("content"):
            return message
    return None


def _assistant_reasoning(message: dict[str, Any]) -> str:
    reasoning = (message.get("metadata") or {}).get("reasoning")
    return reasoning.strip() if isinstance(reasoning, str) else ""


def _native_thinking_blocks(session: Any) -> list[dict[str, Any]]:
    native_messages = (getattr(session, "metadata", None) or {}).get("native_messages")
    if not isinstance(native_messages, list):
        return []
    return [
        block
        for message in native_messages
        if isinstance(message, dict) and message.get("role") == "assistant"
        for content in [message.get("content")]
        if isinstance(content, list)
        for block in content
        if isinstance(block, dict)
        and block.get("type") in {"thinking", "redacted_thinking"}
    ]


def _contains_runtime_scratch(value: Any) -> bool:
    if isinstance(value, list):
        return any(_contains_runtime_scratch(item) for item in value)
    if not isinstance(value, dict):
        return False
    if any(key in {"_partial_json", "_unknown_deltas"} for key in value):
        return True
    return any(_contains_runtime_scratch(item) for item in value.values())


def _cleared_thinking_turns(session: Any) -> int:
    native_messages = (getattr(session, "metadata", None) or {}).get("native_messages")
    if not isinstance(native_messages, list):
        return 0
    cleared = 0
    for message in native_messages:
        if not isinstance(message, dict):
            continue
        metadata = message.get("_metadata")
        if not isinstance(metadata, dict):
            continue
        anthropic = metadata.get("anthropic")
        if not isinstance(anthropic, dict):
            continue
        context_management = anthropic.get("context_management")
        if not isinstance(context_management, dict):
            continue
        applied_edits = context_management.get("applied_edits")
        if not isinstance(applied_edits, list):
            continue
        for edit in applied_edits:
            if not isinstance(edit, dict):
                continue
            value = edit.get("cleared_thinking_turns")
            if isinstance(value, int):
                cleared += value
    return cleared


def _append_tool_results(
    core: AgentCore,
    session: Any,
    config: dict[str, Any],
    tool_calls: list[dict[str, Any]],
):
    tool_messages = core.execute_tool_calls(tool_calls, config)
    assert tool_messages, "expected file-read tool result"
    for message in tool_messages:
        session = core.add_message(
            session,
            role=message.get("role", "tool"),
            content=message.get("content", ""),
            metadata=message.get("metadata"),
            tool_result=message.get("toolResult"),
            config=config,
        )
    return session


def _run_tool_continuity(
    config: dict[str, Any],
    *,
    stream: bool,
    max_iterations: int = 5,
):
    core = _core()
    session = _new_session(core, config)
    first_reasoning = ""
    final_responses: list[dict[str, Any]] = []

    for _ in range(max_iterations):
        session, final_responses = _request(core, session, config, stream=stream)
        assert final_responses, "expected assistant response"
        assistant = final_responses[-1]
        if not first_reasoning:
            first_reasoning = _assistant_reasoning(assistant)
        tool_calls = (assistant.get("metadata") or {}).get("tool_calls") or []
        if not tool_calls:
            break
        assert all(call.get("name") == "read_file" for call in tool_calls)
        session = _append_tool_results(core, session, config, tool_calls)

    final_message = _assistant_with_content(final_responses)
    assert final_message is not None, "expected final assistant content"
    return session, final_message, first_reasoning


def _run_interrupted_continuity(
    config: dict[str, Any],
    *,
    add_intermediate_turn: bool = False,
) -> tuple[str, int, int, Any]:
    core = _core()
    session = _new_session(core, config)
    session, first_responses = core.send_request(session, config)
    assert first_responses, "expected first assistant response"

    first_assistant = first_responses[-1]
    first_reasoning = _assistant_reasoning(first_assistant)
    assert first_reasoning, "expected first assistant reasoning"
    tool_calls = (first_assistant.get("metadata") or {}).get("tool_calls") or []
    assert tool_calls, "expected first assistant file-read tool call"
    session = _append_tool_results(core, session, config, tool_calls)
    if add_intermediate_turn:
        session = core.add_message(
            session,
            "user",
            "Do not give the final bank result yet. Reply with exactly: WAIT",
            config=config,
        )
        session, intermediate_responses = core.send_request(session, config)
        intermediate = _assistant_with_content(intermediate_responses)
        assert intermediate is not None, "expected intermediate assistant response"
        assert str(intermediate.get("content") or "").strip() == "WAIT"
    session = core.add_message(
        session,
        "user",
        "give me the final result",
        config=config,
    )

    session, second_responses = core.send_request(session, config)
    final_message = _assistant_with_content(second_responses)
    assert final_message is not None, "expected interrupted follow-up content"
    second_reasoning = _assistant_reasoning(final_message)
    return (
        str(final_message.get("content") or "").strip(),
        len(first_reasoning),
        len(second_reasoning),
        session,
    )


@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
@pytest.mark.timeout(300)
def test_anthropic_bank_reasoning_tool_continuity(stream: bool) -> None:
    last_failure: tuple[str, int] | None = None
    for _ in range(3):
        session, final_message, first_reasoning = _run_tool_continuity(
            _manual_config(),
            stream=stream,
        )
        content = str(final_message.get("content") or "")
        if "Clock" not in content or not first_reasoning:
            last_failure = (content, len(first_reasoning))
            continue
        thinking_blocks = _native_thinking_blocks(session)
        assert thinking_blocks
        assert any(
            block.get("type") == "redacted_thinking"
            or isinstance(block.get("signature"), str)
            and block.get("signature")
            for block in thinking_blocks
        )
        assert not _contains_runtime_scratch(session.metadata.get("native_messages"))
        return

    assert last_failure is not None
    pytest.fail(
        "Anthropic bank-file reasoning/tool continuity did not produce the "
        "preserved result after three attempts. "
        f"Last attempt: content={last_failure[0]!r}, "
        f"first_reasoning_length={last_failure[1]}",
        pytrace=False,
    )


@pytest.mark.timeout(360)
def test_anthropic_bank_interrupted_followup_preserves_all_reasoning() -> None:
    last_failure: tuple[str, int, int] | None = None
    for _ in range(3):
        content, first_length, second_length, session = _run_interrupted_continuity(
            _adaptive_context_config(keep="all")
        )
        if (
            "Clock" in content
            and first_length > 0
            and (second_length == 0 or second_length < first_length)
        ):
            thinking_blocks = _native_thinking_blocks(session)
            assert thinking_blocks
            assert not _contains_runtime_scratch(
                session.metadata.get("native_messages")
            )
            return
        last_failure = (content, first_length, second_length)

    assert last_failure is not None
    pytest.fail(
        "Preserved Anthropic reasoning did not survive the inserted user "
        "follow-up in the bank-file test. "
        f"Last attempt: content={last_failure[0]!r}, "
        f"first_reasoning_length={last_failure[1]}, "
        f"second_reasoning_length={last_failure[2]}",
        pytrace=False,
    )


@pytest.mark.timeout(360)
def test_anthropic_bank_latest_turn_only_reports_cleared_reasoning() -> None:
    _content, first_length, _second_length, session = _run_interrupted_continuity(
        _adaptive_context_config(keep={"type": "thinking_turns", "value": 1}),
        add_intermediate_turn=True,
    )

    assert first_length > 0
    assert _cleared_thinking_turns(session) > 0
    assert len(_native_thinking_blocks(session)) >= 2
