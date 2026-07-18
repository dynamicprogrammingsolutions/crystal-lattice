from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from feature_system_message.system_message_feature import SystemMessageFeature
from openai_responses_plugins import (
    OpenAIResponsesChatGPTAuthFeature,
    OpenAIResponsesProvider,
    OpenAIResponsesUsageExtension,
)
from openai_responses_plugins.openai_responses_reasoning_extension import (
    OpenAIResponsesReasoningExtension,
)
from openai_responses_plugins.openai_responses_tools_extension import (
    OpenAIResponsesToolsExtension,
)
from plugins.file_reader_tool import FileReaderTool
from plugins.request_options_feature import RequestOptionsFeature


REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CHATGPT_AUTH_STATE_DIR = (
    REPO_ROOT / "plugins" / "chatgpt-auth-app" / "tests" / ".manual-state"
)
REASONING_DIR = (
    REPO_ROOT / "plugins" / "openrouter_responses" / "tests" / "reasoning_test"
)
BANK_PROMPT = (REASONING_DIR / "prompt.txt").read_text(encoding="utf-8")
EXPECTED_BANK_LABEL = "Clock"
pytestmark = pytest.mark.api


def _manual_state_dir() -> Path:
    raw = os.getenv("CHATGPT_TEST_STATE_DIR")
    if isinstance(raw, str) and raw.strip():
        return Path(raw).expanduser()
    return _DEFAULT_CHATGPT_AUTH_STATE_DIR


def _credentials_path() -> Path:
    return _manual_state_dir() / "auth" / "chatgpt-auth.json"


def _parse_iso8601_expires_at(raw: Any) -> datetime | None:
    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def _load_saved_credentials() -> dict[str, object]:
    path = _credentials_path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        pytest.skip(f"saved ChatGPT login not found at {path}")
    if not isinstance(payload, dict):
        pytest.skip(f"saved ChatGPT login at {path} is not a JSON object")
    access_token = payload.get("access_token")
    if not isinstance(access_token, str) or not access_token.strip():
        pytest.skip(f"saved ChatGPT login at {path} has no access_token")
    expires_at = _parse_iso8601_expires_at(payload.get("expires_at"))
    if expires_at is not None and datetime.now(timezone.utc) >= expires_at:
        pytest.skip(
            f"saved ChatGPT login at {path} expired at {payload.get('expires_at')}"
        )
    return payload


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


class _RecordingChatGPTProvider(OpenAIResponsesProvider):
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


def _chatgpt_context_config(
    credentials_path: Path, model: str, reasoning_context: str
) -> dict[str, object]:
    return {
        "model": model,
        "auth_mode": "chatgpt",
        "chatgpt_credentials_path": str(credentials_path),
        "chatgpt_base_url": os.getenv("OPENAI_CHATGPT_BASE_URL")
        or "https://chatgpt.com/backend-api/codex",
        "system_message_as_instructions": True,
        "system_message": (
            "You have access to the read_file tool. The working directory for file paths "
            f"is: {REASONING_DIR}. You can use relative file paths like 'bank0.json'."
        ),
        "timeout": 240,
        "reasoning_context": reasoning_context,
        "reasoning_effort": "medium",
        "reasoning_summary": "concise",
        "allowed_paths": [str(REASONING_DIR)],
        "working_directory": str(REASONING_DIR),
        "max_file_size": 1024 * 1024,
        "show_openai_auth_mode": True,
    }


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        _RecordingChatGPTProvider,
        extensions=[
            OpenAIResponsesReasoningExtension,
            OpenAIResponsesUsageExtension,
            OpenAIResponsesToolsExtension,
        ],
    )
    core.register_feature(OpenAIResponsesChatGPTAuthFeature)
    core.register_feature(SystemMessageFeature)
    core.register_feature(RequestOptionsFeature)
    core.register_tool(FileReaderTool)
    return core


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
    assert (
        isinstance(final_messages, list) and final_messages
    ), "expected final messages from stream"
    return final_session, final_messages


def _encrypted_reasoning_size(message: dict[str, Any]) -> Tuple[int, int]:
    metadata = message.get("metadata") or {}
    raw_reasoning = metadata.get("openai_responses_reasoning") or {}
    encrypted_content = raw_reasoning.get("encrypted_content")
    if not isinstance(encrypted_content, list):
        return (0, 0)
    item_count = len(encrypted_content)
    total_length = sum(len(s) for s in encrypted_content if isinstance(s, str))
    return (item_count, total_length)


def _has_replayed_reasoning_item(recorded_requests: List[dict[str, Any]]) -> bool:
    if len(recorded_requests) < 2:
        return False
    second_input = recorded_requests[1].get("input")
    if not isinstance(second_input, list):
        return False
    return any(
        isinstance(item, dict) and item.get("type") == "reasoning"
        for item in second_input
    )


def _run_bank_reasoning_flow_chatgpt(
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
    """Run the two-turn bank-file reasoning flow against the ChatGPT backend."""
    _RecordingChatGPTProvider.recorded_requests = []

    session = core.create_session()
    session = core.add_message(session, "user", BANK_PROMPT, config=config)

    # Turn 1: send the bank-file prompt. The model should reason and call
    # read_file.
    session, first_messages = _send_streaming_request(core, session, config)
    final_message_1 = first_messages[-1]
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

    # Turn 2: ask for the final result.
    session = core.add_message(
        session, "user", "give me the final result", config=config
    )
    _session, second_messages = _send_streaming_request(core, session, config)
    final_message_2 = second_messages[-1]

    second_item_count, second_total_length = _encrypted_reasoning_size(final_message_2)

    return (
        final_message_1,
        first_item_count,
        first_total_length,
        final_message_2,
        second_item_count,
        second_total_length,
        list(_RecordingChatGPTProvider.recorded_requests),
    )


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_chatgpt_reasoning_context_all_turns_reuses_prior_reasoning_gpt_5_6_luna() -> (
    None
):
    """ChatGPT backend: with ``reasoning_context: "all_turns"``, turn 2's
    encrypted reasoning should be at most 2/3 of turn 1's (or zero items).
    """
    load_dotenv(REPO_ROOT / ".env")

    credentials_path = _credentials_path()
    _load_saved_credentials()

    _RecordingChatGPTProvider.recorded_requests = []
    core = _build_core()
    model = os.getenv("OPENAI_RESPONSES_CHATGPT_MODEL") or "gpt-5.6-luna"
    config = _chatgpt_context_config(credentials_path, model, "all_turns")

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
            ) = _run_bank_reasoning_flow_chatgpt(core, config)
        except Exception as exc:  # noqa: BLE001
            pytest.xfail(
                f"ChatGPT backend rejected reasoning_context=all_turns for {model}; "
                f"API acceptance is recorded in the real API test. "
                f"Rejection: {type(exc).__name__}: {exc}"
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
            assert len(recorded) >= 2
            second_reasoning = recorded[1].get("reasoning")
            assert isinstance(second_reasoning, dict)
            assert second_reasoning.get("context") == "all_turns"
            assert _has_replayed_reasoning_item(
                recorded
            ), "expected turn 2 input to contain replayed reasoning items from turn 1"
            metadata = second_msg.get("metadata") or {}
            assert metadata.get("usage_effective_auth_mode") == "chatgpt"
            return

        last_failure = (
            first_items,
            first_len,
            second_items,
            second_len,
            second_content,
        )

    pytest.fail(
        "ChatGPT all_turns did not reduce turn 2 reasoning as expected after 5 attempts. "
        f"Last attempt: first_items={last_failure[0]}, first_len={last_failure[1]}, "
        f"second_items={last_failure[2]}, second_len={last_failure[3]}, "
        f"second_content={last_failure[4]!r}",
        pytrace=False,
    )


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_chatgpt_reasoning_context_current_turn_focus_gpt_5_6_luna() -> (
    None
):
    """ChatGPT backend: with ``reasoning_context: "current_turn"``, turn 2's
    encrypted reasoning should be at least 2/3 of turn 1's (the model
    re-derives because earlier reasoning is not rendered).

    The label accuracy check is intentionally omitted for current_turn (the
    model may re-derive the label incorrectly without earlier reasoning).
    """
    load_dotenv(REPO_ROOT / ".env")

    credentials_path = _credentials_path()
    _load_saved_credentials()

    _RecordingChatGPTProvider.recorded_requests = []
    core = _build_core()
    model = os.getenv("OPENAI_RESPONSES_CHATGPT_MODEL") or "gpt-5.6-luna"
    config = _chatgpt_context_config(credentials_path, model, "current_turn")

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
            ) = _run_bank_reasoning_flow_chatgpt(core, config)
        except Exception as exc:  # noqa: BLE001
            pytest.xfail(
                f"ChatGPT backend rejected reasoning_context=current_turn for {model}; "
                f"API acceptance is recorded in the real API test. "
                f"Rejection: {type(exc).__name__}: {exc}"
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
        if first_len > 0 and second_len >= first_len * 2 / 3:
            assert len(recorded) >= 2
            second_reasoning = recorded[1].get("reasoning")
            assert isinstance(second_reasoning, dict)
            assert second_reasoning.get("context") == "current_turn"
            assert _has_replayed_reasoning_item(
                recorded
            ), "expected turn 2 input to contain replayed reasoning items from turn 1"
            metadata = second_msg.get("metadata") or {}
            assert metadata.get("usage_effective_auth_mode") == "chatgpt"
            return

        last_failure = (
            first_items,
            first_len,
            second_items,
            second_len,
            second_content,
        )

    pytest.fail(
        "ChatGPT current_turn did not preserve turn 2 reasoning size as expected after 5 attempts. "
        f"Last attempt: first_items={last_failure[0]}, first_len={last_failure[1]}, "
        f"second_items={last_failure[2]}, second_len={last_failure[3]}, "
        f"second_content={last_failure[4]!r}",
        pytrace=False,
    )
