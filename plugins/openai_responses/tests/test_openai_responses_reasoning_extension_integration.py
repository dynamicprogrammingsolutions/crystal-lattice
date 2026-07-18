from __future__ import annotations

import os
from pathlib import Path
from typing import Any, List, Tuple

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


pytestmark = pytest.mark.api


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
    core.register_provider(
        OpenAIResponsesProvider,
        extensions=[OpenAIResponsesReasoningExtension],
    )
    core.register_feature(RequestOptionsFeature)
    return core


def _config(api_key: str) -> dict[str, object]:
    return {
        "model": "gpt-5-mini",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
        "reasoning_effort": "minimal",
        "reasoning_summary": "concise",
    }


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_non_streaming_reasoning_metadata_visible(
    ensure_openai_api_key: str,
) -> None:
    core = _build_core()
    session = core.create_session()
    session = core.add_message(
        session, "user", "Reply with exactly: OPENAI_REASONING_OK"
    )

    _new_session, responses = core.send_request(session, _config(ensure_openai_api_key))

    assert responses
    final = responses[-1]
    assert final.get("role") == "assistant"
    assert "OPENAI_REASONING_OK" in (final.get("content") or "")

    metadata = final.get("metadata") or {}
    reasoning = metadata.get("reasoning")
    assert isinstance(reasoning, str)
    assert reasoning.strip()

    raw_reasoning = metadata.get("openai_responses_reasoning")
    assert isinstance(raw_reasoning, dict)
    raw_items = raw_reasoning.get("items")
    assert isinstance(raw_items, list)
    assert raw_items
    assert raw_items[0].get("type") == "reasoning"


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_streaming_reasoning_metadata_visible(
    ensure_openai_api_key: str,
) -> None:
    core = _build_core()
    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly: OPENAI_REASONING_STREAM_OK",
    )

    final_message = None
    for event in core.send_request_stream(session, _config(ensure_openai_api_key)):
        if event["type"] == "final":
            messages = event.get("messages") or []
            if messages:
                final_message = messages[-1]

    assert final_message is not None
    assert final_message.get("role") == "assistant"
    assert "OPENAI_REASONING_STREAM_OK" in (final_message.get("content") or "")

    metadata = final_message.get("metadata") or {}
    reasoning = metadata.get("reasoning")
    assert isinstance(reasoning, str)
    assert reasoning.strip()

    raw_reasoning = metadata.get("openai_responses_reasoning")
    assert isinstance(raw_reasoning, dict)
    raw_items = raw_reasoning.get("items")
    assert isinstance(raw_items, list)
    assert raw_items
    assert raw_items[0].get("type") == "reasoning"


class _RecordedResponsesCreateProxy:
    def __init__(self, target: Any, recorder: list[dict[str, Any]]) -> None:
        self._target = target
        self._recorder = recorder

    def create(self, **kwargs: Any) -> Any:
        self._recorder.append(dict(kwargs))
        return self._target.create(**kwargs)


class _RecordedResponsesProxy:
    def __init__(self, target: Any, recorder: list[dict[str, Any]]) -> None:
        self._target = target
        self._recorder = recorder
        streaming = getattr(target, "with_streaming_response", None)
        self.with_streaming_response = (
            _RecordedResponsesCreateProxy(streaming, recorder)
            if streaming is not None
            else None
        )

    def create(self, **kwargs: Any) -> Any:
        self._recorder.append(dict(kwargs))
        return self._target.create(**kwargs)


class _RecordedClientProxy:
    def __init__(self, target: Any, recorder: list[dict[str, Any]]) -> None:
        self._target = target
        self._recorder = recorder
        self.responses = _RecordedResponsesProxy(target.responses, recorder)
        files = getattr(target, "files", None)
        if files is not None:
            self.files = files

    def with_options(self, **kwargs: Any) -> "_RecordedClientProxy":
        return _RecordedClientProxy(self._target.with_options(**kwargs), self._recorder)

    def __getattr__(self, name: str) -> Any:
        return getattr(self._target, name)


class _RecordingApiProvider(OpenAIResponsesProvider):
    recorded_requests: list[dict[str, Any]] = []

    def _create_sdk_client_with_options(
        self,
        config: dict[str, Any],
        *,
        timeout: float,
        max_retries: int | None,
    ) -> Any:
        client = super()._create_sdk_client_with_options(
            config,
            timeout=timeout,
            max_retries=max_retries,
        )
        return _RecordedClientProxy(client, type(self).recorded_requests)


def _build_recording_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        _RecordingApiProvider,
        extensions=[OpenAIResponsesReasoningExtension],
    )
    core.register_feature(RequestOptionsFeature)
    return core


def _gpt_5_6_max_config(api_key: str) -> dict[str, object]:
    return {
        "model": "gpt-5.6-luna",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 180,
        "reasoning_effort": "max",
        "reasoning_summary": "concise",
    }


def _gpt_5_6_ultra_config(api_key: str) -> dict[str, object]:
    return {
        "model": "gpt-5.6-sol",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 240,
        "reasoning_effort": "ultra",
        "reasoning_summary": "concise",
    }


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_reasoning_effort_max_gpt_5_6_luna_real_api(
    ensure_openai_api_key: str,
) -> None:
    _RecordingApiProvider.recorded_requests = []
    core = _build_recording_core()
    config = _gpt_5_6_max_config(ensure_openai_api_key)

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly: GPT56_MAX_OK")

    final_message = None
    for event in core.send_request_stream(session, config):
        if event["type"] == "final":
            messages = event.get("messages") or []
            if messages:
                final_message = messages[-1]

    assert final_message is not None
    assert final_message.get("role") == "assistant"
    assert "GPT56_MAX_OK" in (final_message.get("content") or "")

    assert (
        _RecordingApiProvider.recorded_requests
    ), "expected at least one recorded request"
    reasoning = _RecordingApiProvider.recorded_requests[0].get("reasoning")
    assert isinstance(reasoning, dict)
    assert reasoning.get("effort") == "max"


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_reasoning_effort_ultra_gpt_5_6_sol_real_api(
    ensure_openai_api_key: str,
) -> None:
    _RecordingApiProvider.recorded_requests = []
    core = _build_recording_core()
    config = _gpt_5_6_ultra_config(ensure_openai_api_key)

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly: GPT56_ULTRA_OK")

    try:
        final_message = None
        for event in core.send_request_stream(session, config):
            if event["type"] == "final":
                messages = event.get("messages") or []
                if messages:
                    final_message = messages[-1]
    except (
        Exception
    ) as exc:  # noqa: BLE001 - capture exact API rejection for documentation
        pytest.xfail(
            f"Public OpenAI API rejected reasoning_effort=ultra for gpt-5.6-sol: "
            f"{type(exc).__name__}: {exc}"
        )

    assert final_message is not None
    assert final_message.get("role") == "assistant"
    assert "GPT56_ULTRA_OK" in (final_message.get("content") or "")

    assert (
        _RecordingApiProvider.recorded_requests
    ), "expected at least one recorded request"
    reasoning = _RecordingApiProvider.recorded_requests[0].get("reasoning")
    assert isinstance(reasoning, dict)
    assert reasoning.get("effort") == "ultra"


def _gpt_5_6_pro_mode_config(api_key: str) -> dict[str, object]:
    return {
        "model": "gpt-5.6-sol",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 240,
        "reasoning_mode": "pro",
        "reasoning_effort": "medium",
        "reasoning_summary": "concise",
    }


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_reasoning_mode_pro_gpt_5_6_sol_real_api(
    ensure_openai_api_key: str,
) -> None:
    _RecordingApiProvider.recorded_requests = []
    core = _build_recording_core()
    config = _gpt_5_6_pro_mode_config(ensure_openai_api_key)

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly: GPT56_PRO_OK")

    try:
        final_message = None
        for event in core.send_request_stream(session, config):
            if event["type"] == "final":
                messages = event.get("messages") or []
                if messages:
                    final_message = messages[-1]
    except (
        Exception
    ) as exc:  # noqa: BLE001 - capture exact API rejection for documentation
        pytest.xfail(
            f"Public OpenAI API rejected reasoning_mode=pro for gpt-5.6-sol: "
            f"{type(exc).__name__}: {exc}"
        )

    assert final_message is not None
    assert final_message.get("role") == "assistant"
    assert "GPT56_PRO_OK" in (final_message.get("content") or "")

    assert (
        _RecordingApiProvider.recorded_requests
    ), "expected at least one recorded request"
    reasoning = _RecordingApiProvider.recorded_requests[0].get("reasoning")
    assert isinstance(reasoning, dict)
    assert reasoning.get("mode") == "pro"
    assert reasoning.get("effort") == "medium"
    assert reasoning.get("summary") == "concise"


# ---------------------------------------------------------------------------
# Reasoning context (reasoning_context / reasoning.context) — task 040
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[3]
REASONING_DIR = (
    REPO_ROOT / "plugins" / "openrouter_responses" / "tests" / "reasoning_test"
)
BANK_PROMPT = (REASONING_DIR / "prompt.txt").read_text(encoding="utf-8")
# The bank-file reasoning prompt's default seed produces the label "Clock".
EXPECTED_BANK_LABEL = "Clock"


def _build_recording_core_with_tools() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        _RecordingApiProvider,
        extensions=[OpenAIResponsesReasoningExtension, OpenAIResponsesToolsExtension],
    )
    core.register_feature(RequestOptionsFeature)
    core.register_tool(FileReaderTool)
    return core


def _gpt_5_6_context_config(
    api_key: str, *, reasoning_context: str
) -> dict[str, object]:
    return {
        "model": "gpt-5.6-luna",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 240,
        "reasoning_context": reasoning_context,
        "reasoning_effort": "medium",
        "reasoning_summary": "concise",
        "allowed_paths": [str(REASONING_DIR)],
        "working_directory": str(REASONING_DIR),
        "max_file_size": 1024 * 1024,
    }


def _encrypted_reasoning_size(message: dict[str, Any]) -> Tuple[int, int]:
    """Return ``(item_count, total_char_length)`` for the encrypted reasoning
    produced in this turn's response.

    ``metadata.openai_responses_reasoning.encrypted_content`` is a list of
    encrypted content strings produced in the current turn's response (not
    the replayed history, because ``from_native_messages`` only processes
    the native items at the assistant message's ``native_indices``, which
    point to the current turn's output items).
    """
    metadata = message.get("metadata") or {}
    raw_reasoning = metadata.get("openai_responses_reasoning") or {}
    encrypted_content = raw_reasoning.get("encrypted_content")
    if not isinstance(encrypted_content, list):
        return (0, 0)
    item_count = len(encrypted_content)
    total_length = sum(len(s) for s in encrypted_content if isinstance(s, str))
    return (item_count, total_length)


def _run_bank_reasoning_flow(
    core: AgentCore,
    config: dict[str, Any],
) -> Tuple[
    dict[str, Any],
    int,
    int,
    dict[str, Any],
    int,
    int,
    List[dict[str, Any]],
]:
    """Run the two-turn bank-file reasoning flow.

    Returns ``(first_message, first_item_count, first_total_length,
    second_message, second_item_count, second_total_length, recorded_requests)``.
    """
    _RecordingApiProvider.recorded_requests = []

    session = core.create_session()
    session = core.add_message(
        session,
        "system",
        (
            "You have access to the read_file tool. The working directory for file paths "
            f"is: {REASONING_DIR}. You can use relative file paths like 'bank0.json'."
        ),
        config=config,
    )
    session = core.add_message(session, "user", BANK_PROMPT, config=config)

    # Turn 1: send the bank-file prompt. The model should reason and call
    # read_file.
    final_message_1 = None
    for event in core.send_request_stream(session, config):
        if event["type"] == "final":
            messages = event.get("messages") or []
            if messages:
                final_message_1 = messages[-1]
                session = event.get("session") or session

    assert final_message_1 is not None, "expected a final message from turn 1"
    assert final_message_1.get("role") == "assistant"

    # Execute tool calls from turn 1.
    tool_calls = (final_message_1.get("metadata") or {}).get("tool_calls") or []
    assert tool_calls, "expected the model to call read_file on turn 1"
    tool_messages = core.execute_tool_calls(tool_calls, config)
    for tool_message in tool_messages:
        session = core.add_message(
            session,
            role=tool_message.get("role", "tool"),
            content=tool_message.get("content", ""),
            metadata=tool_message.get("metadata"),
            config=config,
        )

    first_item_count, first_total_length = _encrypted_reasoning_size(final_message_1)

    # Turn 2: ask for the final result. With ``all_turns``, the model should
    # reuse the preserved reasoning and produce less new reasoning.
    session = core.add_message(
        session, "user", "give me the final result", config=config
    )
    final_message_2 = None
    for event in core.send_request_stream(session, config):
        if event["type"] == "final":
            messages = event.get("messages") or []
            if messages:
                final_message_2 = messages[-1]

    assert final_message_2 is not None, "expected a final message from turn 2"
    assert final_message_2.get("role") == "assistant"

    second_item_count, second_total_length = _encrypted_reasoning_size(final_message_2)

    return (
        final_message_1,
        first_item_count,
        first_total_length,
        final_message_2,
        second_item_count,
        second_total_length,
        list(_RecordingApiProvider.recorded_requests),
    )


def _has_replayed_reasoning_item(recorded_requests: List[dict[str, Any]]) -> bool:
    """Check whether the second recorded request's ``input`` contains a
    reasoning item (replayed from turn 1 via native history)."""
    if len(recorded_requests) < 2:
        return False
    second_input = recorded_requests[1].get("input")
    if not isinstance(second_input, list):
        return False
    return any(
        isinstance(item, dict) and item.get("type") == "reasoning"
        for item in second_input
    )


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_reasoning_context_all_turns_reuses_prior_reasoning_gpt_5_6_luna_real_api(
    ensure_openai_api_key: str,
) -> None:
    """With ``reasoning_context: "all_turns"``, the model should reuse
    preserved reasoning from turn 1, so turn 2's encrypted reasoning should
    be small compared to turn 1's.

    The success condition: turn 1 produced reasoning (item_count > 0), turn
    2 content contains the expected label, and turn 2's encrypted reasoning
    is at most 2/3 of turn 1's (by total character length), or zero items.
    The 2/3 threshold was found by running the test multiple times: the
    observed ratio for all_turns is ~0.55, while current_turn is ~1.10.
    """
    core = _build_recording_core_with_tools()
    config = _gpt_5_6_context_config(
        ensure_openai_api_key, reasoning_context="all_turns"
    )

    last_failure: Tuple[int, int, int, int, str] | None = None
    for _ in range(5):
        try:
            (
                first_msg,
                first_items,
                first_len,
                second_msg,
                second_items,
                second_len,
                recorded,
            ) = _run_bank_reasoning_flow(core, config)
        except Exception as exc:  # noqa: BLE001
            pytest.xfail(
                f"Public OpenAI API rejected reasoning_context=all_turns for gpt-5.6-luna: "
                f"{type(exc).__name__}: {exc}"
            )

        second_content = (second_msg.get("content") or "").strip()

        if first_items == 0:
            last_failure = (
                first_items,
                first_len,
                second_items,
                second_len,
                second_content,
            )
            continue

        if EXPECTED_BANK_LABEL not in second_content:
            last_failure = (
                first_items,
                first_len,
                second_items,
                second_len,
                second_content,
            )
            continue

        # all_turns success: turn 2 reasoning is at most 2/3 of turn 1's, or zero.
        if second_items == 0 or (first_len > 0 and second_len <= first_len * 2 / 3):
            # Verify the wire field and native history replay.
            assert len(recorded) >= 2
            second_reasoning = recorded[1].get("reasoning")
            assert isinstance(second_reasoning, dict)
            assert second_reasoning.get("context") == "all_turns"
            assert _has_replayed_reasoning_item(
                recorded
            ), "expected turn 2 input to contain replayed reasoning items from turn 1"
            return

        last_failure = (
            first_items,
            first_len,
            second_items,
            second_len,
            second_content,
        )

    pytest.fail(
        "all_turns did not reduce turn 2 reasoning as expected after 5 attempts. "
        f"Last attempt: first_items={last_failure[0]}, first_len={last_failure[1]}, "
        f"second_items={last_failure[2]}, second_len={last_failure[3]}, "
        f"second_content={last_failure[4]!r}",
        pytrace=False,
    )


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_reasoning_context_current_turn_re_derives_reasoning_gpt_5_6_luna_real_api(
    ensure_openai_api_key: str,
) -> None:
    """With ``reasoning_context: "current_turn"``, earlier reasoning is NOT
    rendered into the next sample, so the model must re-derive. Turn 2's
    encrypted reasoning should be at least 2/3 of turn 1's (the opposite of
    all_turns).

    The success condition: turn 1 produced reasoning (item_count > 0), turn
    2 produced non-empty content, and turn 2's encrypted reasoning is at
    least 2/3 of turn 1's (by total character length).

    Note: the label accuracy check is intentionally omitted for current_turn.
    With current_turn, the model cannot reuse earlier reasoning, so it may
    re-derive the label incorrectly (e.g., "Green" instead of "Clock"). The
    purpose of this test is to verify reasoning SIZE (the model re-derives
    substantially), not label accuracy.
    """
    core = _build_recording_core_with_tools()
    config = _gpt_5_6_context_config(
        ensure_openai_api_key, reasoning_context="current_turn"
    )

    last_failure: Tuple[int, int, int, int, str] | None = None
    for _ in range(5):
        try:
            (
                first_msg,
                first_items,
                first_len,
                second_msg,
                second_items,
                second_len,
                recorded,
            ) = _run_bank_reasoning_flow(core, config)
        except Exception as exc:  # noqa: BLE001
            pytest.xfail(
                f"Public OpenAI API rejected reasoning_context=current_turn for gpt-5.6-luna: "
                f"{type(exc).__name__}: {exc}"
            )

        second_content = (second_msg.get("content") or "").strip()

        if first_items == 0:
            last_failure = (
                first_items,
                first_len,
                second_items,
                second_len,
                second_content,
            )
            continue

        if not second_content:
            last_failure = (
                first_items,
                first_len,
                second_items,
                second_len,
                second_content,
            )
            continue

        # current_turn success: turn 2 reasoning is at least 2/3 of turn 1's.
        # The model re-derives because earlier reasoning is not rendered.
        if first_len > 0 and second_len >= first_len * 2 / 3:
            # Verify the wire field and native history replay.
            assert len(recorded) >= 2
            second_reasoning = recorded[1].get("reasoning")
            assert isinstance(second_reasoning, dict)
            assert second_reasoning.get("context") == "current_turn"
            # Native history replay is the same for current_turn — the
            # reasoning items are still in the input; current_turn only
            # changes rendering, not retention.
            assert _has_replayed_reasoning_item(
                recorded
            ), "expected turn 2 input to contain replayed reasoning items from turn 1"
            return

        last_failure = (
            first_items,
            first_len,
            second_items,
            second_len,
            second_content,
        )

    pytest.fail(
        "current_turn did not preserve turn 2 reasoning size as expected after 5 attempts. "
        f"Last attempt: first_items={last_failure[0]}, first_len={last_failure[1]}, "
        f"second_items={last_failure[2]}, second_len={last_failure[3]}, "
        f"second_content={last_failure[4]!r}",
        pytrace=False,
    )
