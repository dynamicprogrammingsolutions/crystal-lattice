from __future__ import annotations

import json
import os
from pathlib import Path

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from feature_system_message.system_message_feature import SystemMessageFeature
from openai_responses_plugins import (
    OpenAIResponsesChatGPTAuthFeature,
    OpenAIResponsesProvider,
)


REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CHATGPT_AUTH_STATE_DIR = (
    REPO_ROOT / "plugins" / "chatgpt-auth-app" / "tests" / ".manual-state"
)


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
    model = os.getenv("OPENAI_RESPONSES_CHATGPT_MODEL") or "gpt-5"
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


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_chatgpt_saved_login_real_request() -> None:
    load_dotenv(REPO_ROOT / ".env")

    credentials_path = _credentials_path()
    credentials = _load_saved_credentials()

    core = AgentCore()
    core.register_provider(OpenAIResponsesProvider)
    core.register_feature(OpenAIResponsesChatGPTAuthFeature)
    core.register_feature(SystemMessageFeature)

    config = _chatgpt_config(credentials_path)

    auth_feature = OpenAIResponsesChatGPTAuthFeature()
    system_feature = SystemMessageFeature()
    provider = OpenAIResponsesProvider()
    provider_state = auth_feature.init(config, {"config": dict(config)})
    provider_state = system_feature.init(config, provider_state)
    _, request_state = provider.initialize_request([], provider_state)
    _, request_state = system_feature.initialize_request([], request_state)
    request = request_state["request"]

    assert request["url"] == f"{str(config['chatgpt_base_url']).rstrip('/')}/responses"
    assert request["headers"]["Authorization"].endswith(str(credentials["access_token"]))
    assert request["headers"]["ChatGPT-Account-Id"] == credentials.get("account_id")
    assert request["instructions"] == "You are a precise assistant. Reply exactly with the requested text."

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
    assert any(isinstance(item, dict) and item.get("type") == "message" for item in native_history)