from __future__ import annotations

from typing import Any

import pytest

from fireworks_test_utils import (
    FIREWORKS_GLM_MODEL,
    FIREWORKS_KIMI_MODEL,
    REASONING_TEST_DIR,
    build_fireworks_cfg,
    build_reference_core,
    fireworks_model,
    iter_request_stream_or_skip,
    reasoning_test_prompt,
    send_request_or_skip,
)
from plugins.file_reader_tool import FileReaderTool


MODELS = {
    "glm_fireworks": FIREWORKS_GLM_MODEL,
    "kimi_fireworks": FIREWORKS_KIMI_MODEL,
}
pytestmark = pytest.mark.api


def _assistant_with_content(messages: list[dict[str, Any]]) -> dict[str, Any] | None:
    for message in reversed(messages):
        if message.get("role") == "assistant" and message.get("content"):
            return message
    return None


def _assistant_reasoning(message: dict[str, Any]) -> str:
    metadata = message.get("metadata") or {}
    reasoning = metadata.get("reasoning_content") or metadata.get("reasoning")
    if isinstance(reasoning, str):
        return reasoning.strip()
    return ""


def _assert_tool_calls_have_names(tool_calls: list[dict[str, Any]], *, model: str, stream: bool):
    for call in tool_calls:
        function = call.get("function") or {}
        name = function.get("name")
        assert isinstance(name, str) and name.strip(), (
            f"expected non-empty function.name for {model} (stream={stream}), got {call!r}"
        )


def _request(core, session, cfg: dict[str, Any], *, stream: bool):
    if not stream:
        return send_request_or_skip(core, session, cfg)

    final_event = None
    for event in iter_request_stream_or_skip(core, session, cfg):
        if event.get("type") == "final":
            final_event = event
    assert final_event is not None
    return final_event["session"], final_event["messages"]


def run_reasoning_test(
    model: str,
    *,
    stream: bool = False,
    max_iterations: int = 5,
) -> tuple[Any, list[dict[str, Any]]]:
    cfg = {
        **build_fireworks_cfg(
            fireworks_model(
                "FIREWORKS_KIMI_MODEL" if model == FIREWORKS_KIMI_MODEL else "FIREWORKS_GLM_MODEL",
                model,
            ),
            request_options={"temperature": 0, "seed": 2},
        ),
        "allowed_paths": [str(REASONING_TEST_DIR)],
        "working_directory": str(REASONING_TEST_DIR),
        "max_file_size": 1024 * 1024,
    }

    core = build_reference_core(FileReaderTool)
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You have access to the read_file tool. The working directory for file paths "
        f"is: {REASONING_TEST_DIR}. You can use relative file paths like 'bank0.json'.",
    )
    session = core.add_message(session, "user", reasoning_test_prompt())

    final_responses: list[dict[str, Any]] = []
    for _ in range(max_iterations):
        session, final_responses = _request(core, session, cfg, stream=stream)
        if not final_responses:
            break

        last_message = final_responses[-1]
        if last_message.get("role") != "assistant":
            break

        tool_calls = (last_message.get("metadata") or {}).get("tool_calls") or []
        if not tool_calls:
            break

        _assert_tool_calls_have_names(tool_calls, model=model, stream=stream)
        tool_messages = core.execute_tool_calls(tool_calls, cfg)
        for tool_message in tool_messages:
            session = core.add_message(
                session,
                role=tool_message.get("role", "tool"),
                content=tool_message.get("content", ""),
                metadata=tool_message.get("metadata"),
                config=cfg,
            )

    return session, final_responses


def run_interrupted_reasoning_test(
    *,
    request_options: dict[str, Any],
) -> tuple[str, int, int]:
    cfg = {
        **build_fireworks_cfg(
            fireworks_model("FIREWORKS_GLM_MODEL", FIREWORKS_GLM_MODEL),
            request_options={"temperature": 0, "seed": 2, **request_options},
        ),
        "allowed_paths": [str(REASONING_TEST_DIR)],
        "working_directory": str(REASONING_TEST_DIR),
        "max_file_size": 1024 * 1024,
    }

    core = build_reference_core(FileReaderTool)
    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        "You have access to the read_file tool. The working directory for file paths "
        f"is: {REASONING_TEST_DIR}. You can use relative file paths like 'bank0.json'.",
    )
    session = core.add_message(session, "user", reasoning_test_prompt())

    session, first_responses = send_request_or_skip(core, session, cfg)
    assert first_responses, "expected first assistant response"

    first_assistant = first_responses[-1]
    assert first_assistant.get("role") == "assistant"
    first_reasoning = _assistant_reasoning(first_assistant)
    assert first_reasoning, "expected first assistant reasoning"

    tool_calls = (first_assistant.get("metadata") or {}).get("tool_calls") or []
    assert tool_calls, "expected first assistant tool call"
    _assert_tool_calls_have_names(tool_calls, model=cfg["model"], stream=False)

    tool_messages = core.execute_tool_calls(tool_calls, cfg)
    for tool_message in tool_messages:
        session = core.add_message(
            session,
            role=tool_message.get("role", "tool"),
            content=tool_message.get("content", ""),
            metadata=tool_message.get("metadata"),
            config=cfg,
        )

    session = core.add_message(session, "user", "give me the final result")
    _session, second_responses = send_request_or_skip(core, session, cfg)
    assert second_responses, "expected interrupted follow-up assistant response"

    final_message = _assistant_with_content(second_responses)
    assert final_message is not None, "no final assistant content after interrupted follow-up"

    content = final_message.get("content", "").strip()
    second_reasoning = _assistant_reasoning(final_message)
    return content, len(first_reasoning), len(second_reasoning)


@pytest.mark.integration
@pytest.mark.fireworks
@pytest.mark.parametrize("model_name,model_id", list(MODELS.items()))
@pytest.mark.parametrize("stream", [False, True], ids=["non-streaming", "streaming"])
def test_reasoning_test_fireworks_original_port(model_name, model_id, stream):
    session, responses = run_reasoning_test(model_id, stream=stream)

    assert responses, f"expected responses for {model_name}"

    final_message = _assistant_with_content(responses)
    assert final_message is not None, f"no final assistant content for {model_name}"

    content = final_message.get("content", "").strip()
    assert "Clock" in content, f"expected 'Clock' for {model_name}, got: {content!r}"

    native_messages = (getattr(session, "metadata", None) or {}).get("native_messages") or []
    assistant_messages = [
        message
        for message in native_messages
        if isinstance(message, dict) and message.get("role") == "assistant"
    ]
    assert len(assistant_messages) >= 2, (
        f"expected at least two assistant native messages for {model_name}, got {len(assistant_messages)}"
    )

    reasoning_lengths = []
    for message in assistant_messages[:2]:
        reasoning = message.get("reasoning_content") or message.get("reasoning") or ""
        reasoning_lengths.append(len(reasoning.strip()) if isinstance(reasoning, str) else 0)

    assert reasoning_lengths[0] > 0, f"expected first assistant reasoning for {model_name}"
    assert reasoning_lengths[1] > 0, f"expected second assistant reasoning for {model_name}"


@pytest.mark.integration
@pytest.mark.fireworks
def test_reasoning_test_interrupted_user_followup_fireworks_glm_preserved():
    last_failure: tuple[str, int, int] | None = None
    for _ in range(5):
        content, first_reasoning_length, second_reasoning_length = (
            run_interrupted_reasoning_test(
                request_options={"reasoning_history": "preserved"}
            )
        )
        if (
            "Clock" in content
            and first_reasoning_length > 0
            and (
                second_reasoning_length == 0
                or second_reasoning_length < first_reasoning_length
            )
        ):
            return
        last_failure = (content, first_reasoning_length, second_reasoning_length)

    pytest.fail(
        "Preserved Fireworks reasoning did not survive the inserted user follow-up "
        "in the bank-file reasoning test. "
        f"Last attempt details: content={last_failure[0]!r}, "
        f"first_reasoning_length={last_failure[1]}, "
        f"second_reasoning_length={last_failure[2]}",
        pytrace=False,
    )


@pytest.mark.integration
@pytest.mark.fireworks
@pytest.mark.xfail(
    strict=True,
    reason=(
        "Interleaved Fireworks reasoning history should break the interrupted "
        "bank-file reasoning continuity check."
    ),
)
def test_reasoning_test_interrupted_user_followup_fireworks_glm_interleaved():
    content, first_reasoning_length, second_reasoning_length = (
        run_interrupted_reasoning_test(request_options={"reasoning_history": "interleaved"})
    )

    assert "Clock" in content
    assert first_reasoning_length > 0
    assert (
        second_reasoning_length == 0
        or second_reasoning_length < first_reasoning_length
    )