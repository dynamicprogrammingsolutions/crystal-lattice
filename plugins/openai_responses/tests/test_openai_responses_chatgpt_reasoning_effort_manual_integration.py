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
from plugins.request_options_feature import RequestOptionsFeature


REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CHATGPT_AUTH_STATE_DIR = (
    REPO_ROOT / "plugins" / "chatgpt-auth-app" / "tests" / ".manual-state"
)
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


def _chatgpt_config(
    credentials_path: Path, model: str, reasoning_effort: str
) -> dict[str, object]:
    return {
        "model": model,
        "auth_mode": "chatgpt",
        "chatgpt_credentials_path": str(credentials_path),
        "chatgpt_base_url": os.getenv("OPENAI_CHATGPT_BASE_URL")
        or "https://chatgpt.com/backend-api/codex",
        "system_message_as_instructions": True,
        "system_message": "You are a precise assistant. Reply exactly with the requested text.",
        "timeout": 240,
        "reasoning_effort": reasoning_effort,
        "reasoning_summary": "concise",
        "show_openai_auth_mode": True,
    }


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        _RecordingChatGPTProvider,
        extensions=[OpenAIResponsesReasoningExtension, OpenAIResponsesUsageExtension],
    )
    core.register_feature(OpenAIResponsesChatGPTAuthFeature)
    core.register_feature(SystemMessageFeature)
    core.register_feature(RequestOptionsFeature)
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


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_chatgpt_reasoning_effort_max_gpt_5_6_luna() -> None:
    load_dotenv(REPO_ROOT / ".env")

    credentials_path = _credentials_path()
    _load_saved_credentials()

    _RecordingChatGPTProvider.recorded_requests = []
    core = _build_core()
    model = os.getenv("OPENAI_RESPONSES_CHATGPT_MODEL") or "gpt-5.6-luna"
    config = _chatgpt_config(credentials_path, model, "max")

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly: CHATGPT_REASONING_MAX_OK",
        config=config,
    )

    final_session, final_messages = _send_streaming_request(core, session, config)

    final = final_messages[-1]
    assert final.get("role") == "assistant"
    assert isinstance(final.get("content"), str)
    assert "CHATGPT_REASONING_MAX_OK" in final["content"]

    assert (
        _RecordingChatGPTProvider.recorded_requests
    ), "expected at least one recorded request"
    reasoning = _RecordingChatGPTProvider.recorded_requests[0].get("reasoning")
    assert isinstance(reasoning, dict)
    assert reasoning.get("effort") == "max"

    metadata = final.get("metadata") or {}
    assert isinstance(metadata, dict)
    assert metadata.get("usage_effective_auth_mode") == "chatgpt"


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_chatgpt_reasoning_effort_ultra_gpt_5_6_sol() -> None:
    load_dotenv(REPO_ROOT / ".env")

    credentials_path = _credentials_path()
    _load_saved_credentials()

    _RecordingChatGPTProvider.recorded_requests = []
    core = _build_core()
    config = _chatgpt_config(credentials_path, "gpt-5.6-sol", "ultra")

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly: CHATGPT_REASONING_ULTRA_OK",
        config=config,
    )

    try:
        final_session, final_messages = _send_streaming_request(core, session, config)
    except (
        Exception
    ) as exc:  # noqa: BLE001 - capture exact backend rejection for documentation
        pytest.xfail(
            f"ChatGPT backend rejected reasoning_effort=ultra for gpt-5.6-sol: "
            f"{type(exc).__name__}: {exc}"
        )

    final = final_messages[-1]
    assert final.get("role") == "assistant"
    assert isinstance(final.get("content"), str)
    assert "CHATGPT_REASONING_ULTRA_OK" in final["content"]

    assert (
        _RecordingChatGPTProvider.recorded_requests
    ), "expected at least one recorded request"
    reasoning = _RecordingChatGPTProvider.recorded_requests[0].get("reasoning")
    assert isinstance(reasoning, dict)
    assert reasoning.get("effort") == "ultra"

    metadata = final.get("metadata") or {}
    assert isinstance(metadata, dict)
    assert metadata.get("usage_effective_auth_mode") == "chatgpt"
