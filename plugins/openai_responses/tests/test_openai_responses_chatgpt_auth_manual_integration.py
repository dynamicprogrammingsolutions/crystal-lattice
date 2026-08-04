from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from feature_system_message.system_message_feature import SystemMessageFeature
from openai_responses_plugins import (
    OpenAIResponsesChatGPTAuthFeature,
    OpenAIResponsesFastModeExtension,
    OpenAIResponsesProvider,
    OpenAIResponsesUsageExtension,
)
from openai_responses_plugins.openai_responses_native_compaction_extension import (
    OpenAIResponsesNativeCompactionExtension,
)


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


def _load_saved_credentials() -> dict[str, object]:
    path = _credentials_path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        pytest.skip(f"saved ChatGPT login not found at {path}")
    if not isinstance(payload, dict):
        pytest.skip(f"saved ChatGPT login at {path} is not a JSON object")
    return payload


def _chatgpt_config(credentials_path: Path) -> dict[str, object]:
    model = os.getenv("OPENAI_RESPONSES_CHATGPT_MODEL") or "gpt-5.5"
    return {
        "model": model,
        "auth_mode": "chatgpt",
        "chatgpt_credentials_path": str(credentials_path),
        "chatgpt_base_url": os.getenv("OPENAI_CHATGPT_BASE_URL")
        or "https://chatgpt.com/backend-api/codex",
        "system_message_as_instructions": True,
        "system_message": "You are a precise assistant. Reply exactly with the requested text.",
        "timeout": 120,
    }


def _chatgpt_visible_system_config(credentials_path: Path) -> dict[str, object]:
    config = dict(_chatgpt_config(credentials_path))
    config.pop("system_message_as_instructions", None)
    config.pop("strip_leading_system_or_developer_message", None)
    config["system_message"] = (
        "You are a precise assistant. Reply exactly with the requested text."
    )
    return config


def _fast_mode_models() -> list[str]:
    raw = os.getenv("OPENAI_RESPONSES_CHATGPT_FAST_MODE_MODELS")
    if isinstance(raw, str) and raw.strip():
        models = [item.strip() for item in raw.split(",") if item.strip()]
        if models:
            return models
    single = os.getenv("OPENAI_RESPONSES_CHATGPT_MODEL") or "gpt-5.5"
    return [single]


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


def _last_assistant_message(messages: list[dict[str, object]]) -> dict[str, object]:
    assert messages
    final = messages[-1]
    assert isinstance(final, dict)
    assert final.get("role") == "assistant"
    return final


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_chatgpt_saved_login_real_request() -> None:
    load_dotenv(REPO_ROOT / ".env")

    credentials_path = _credentials_path()
    _load_saved_credentials()

    core = AgentCore()
    core.register_provider(OpenAIResponsesProvider)
    core.register_feature(OpenAIResponsesChatGPTAuthFeature)
    core.register_feature(SystemMessageFeature)

    config = _chatgpt_config(credentials_path)

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly: CHATGPT_AUTH_RESPONSES_OK",
        config=config,
    )

    final_session = None
    final_messages = None
    for chunk in core.send_request_stream(session, config):
        if chunk.get("type") == "final":
            final_session = chunk.get("session")
            final_messages = chunk.get("messages")

    assert final_session is not None
    assert isinstance(final_messages, list)
    assert final_messages
    final = final_messages[-1]
    assert final.get("role") == "assistant"
    assert isinstance(final.get("content"), str)
    assert "CHATGPT_AUTH_RESPONSES_OK" in final["content"]

    native_history = (final_session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert any(
        isinstance(item, dict) and item.get("type") == "message"
        for item in native_history
    )
    assert any(
        isinstance(item, dict)
        and item.get("role") == "user"
        and item.get("content")
        == [
            {
                "type": "input_text",
                "text": "Reply with exactly: CHATGPT_AUTH_RESPONSES_OK",
            }
        ]
        for item in native_history
    )


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_chatgpt_visible_system_message_round_trip_and_compaction() -> (
    None
):
    load_dotenv(REPO_ROOT / ".env")

    credentials_path = _credentials_path()
    _load_saved_credentials()

    _RecordingChatGPTProvider.recorded_requests = []

    core = AgentCore()
    core.register_provider(
        _RecordingChatGPTProvider,
        [OpenAIResponsesNativeCompactionExtension],
    )
    core.register_feature(OpenAIResponsesChatGPTAuthFeature)
    core.register_feature(SystemMessageFeature)

    config = _chatgpt_visible_system_config(credentials_path)

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly: CHATGPT_VISIBLE_SYSTEM_ONE",
        config=config,
    )

    first_session = None
    first_messages = None
    for chunk in core.send_request_stream(session, config):
        if chunk.get("type") == "final":
            first_session = chunk.get("session")
            first_messages = chunk.get("messages")

    assert first_session is not None
    assert isinstance(first_messages, list)
    final = _last_assistant_message(first_messages)
    assert isinstance(final.get("content"), str)
    assert "CHATGPT_VISIBLE_SYSTEM_ONE" in final["content"]

    assert _RecordingChatGPTProvider.recorded_requests
    first_request = _RecordingChatGPTProvider.recorded_requests[0]
    assert (
        first_request.get("instructions")
        == "You are a precise assistant. Reply exactly with the requested text."
    )
    first_input = first_request.get("input")
    assert isinstance(first_input, list)
    assert first_input
    assert not (
        isinstance(first_input[0], dict)
        and first_input[0].get("role") in {"system", "developer"}
    )

    native_history = (first_session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert native_history
    assert isinstance(native_history[0], dict)
    assert native_history[0].get("role") == "system"

    compacted_session, result = core.execute_session_action(
        first_session,
        config,
        plugin_id="openai_responses_native_compaction",
        action_id="compact_native_history_sync",
        params={},
    )

    assert result["message"] == "Compacted the full visible history."
    compacted_native = (compacted_session.metadata or {}).get("native_messages")
    assert isinstance(compacted_native, list)
    assert compacted_native
    assert isinstance(compacted_native[0], dict)
    assert compacted_native[0].get("role") == "system"
    assert any(
        isinstance(item, dict)
        and item.get("type") in {"compaction", "compaction_summary"}
        for item in compacted_native
    )

    compacted_session = core.add_message(
        compacted_session,
        "user",
        "Reply with exactly: CHATGPT_VISIBLE_SYSTEM_TWO",
        config=config,
    )

    final_session = None
    final_messages = None
    for chunk in core.send_request_stream(compacted_session, config):
        if chunk.get("type") == "final":
            final_session = chunk.get("session")
            final_messages = chunk.get("messages")

    assert final_session is not None
    assert isinstance(final_messages, list)
    final = _last_assistant_message(final_messages)
    assert isinstance(final.get("content"), str)
    assert "CHATGPT_VISIBLE_SYSTEM_TWO" in final["content"]


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_chatgpt_saved_login_fast_mode_round_trip() -> None:
    load_dotenv(REPO_ROOT / ".env")

    credentials_path = _credentials_path()
    _load_saved_credentials()

    for model in _fast_mode_models():
        _RecordingChatGPTProvider.recorded_requests = []

        core = AgentCore()
        core.register_provider(
            _RecordingChatGPTProvider,
            extensions=[
                OpenAIResponsesFastModeExtension,
                OpenAIResponsesUsageExtension,
            ],
        )
        core.register_feature(OpenAIResponsesChatGPTAuthFeature)
        core.register_feature(SystemMessageFeature)

        config = {
            **_chatgpt_config(credentials_path),
            "auth_mode": "auto",
            "model": model,
            "enable_fast_mode": True,
            "show_openai_auth_mode": True,
        }

        session = core.create_session()
        session = core.add_message(
            session,
            "user",
            "Reply with exactly: CHATGPT_FAST_MODE_OK",
            config=config,
        )

        final_session = None
        final_messages = None
        for chunk in core.send_request_stream(session, config):
            if chunk.get("type") == "final":
                final_session = chunk.get("session")
                final_messages = chunk.get("messages")

        assert final_session is not None, f"expected final session for model {model}"
        assert isinstance(
            final_messages, list
        ), f"expected final messages list for model {model}"
        final = _last_assistant_message(final_messages)
        assert isinstance(final.get("content"), str)
        assert "CHATGPT_FAST_MODE_OK" in final["content"]

        service_tier_requests = [
            request
            for request in _RecordingChatGPTProvider.recorded_requests
            if request.get("service_tier") is not None
        ]
        assert (
            service_tier_requests
        ), f"expected at least one recorded request with service_tier for model {model}"
        assert any(
            request.get("service_tier") == "priority"
            for request in service_tier_requests
        ), f"expected a priority-tier request for model {model}, got {service_tier_requests!r}"

        metadata = final.get("metadata") or {}
        assert isinstance(metadata, dict)
        reported_tier = metadata.get("usage_service_tier")

        if reported_tier != "priority":
            pytest.xfail(
                f"ChatGPT backend reported service_tier={reported_tier!r} for model {model}; "
                "some accounts or models may not have Fast mode access."
            )

        assert reported_tier == "priority"
