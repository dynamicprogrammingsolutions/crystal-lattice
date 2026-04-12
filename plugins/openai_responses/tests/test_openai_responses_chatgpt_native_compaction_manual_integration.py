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
from openai_responses_plugins.openai_responses_native_compaction_extension import (
    OpenAIResponsesNativeCompactionExtension,
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
        "provider": "openai_responses",
        "model": model,
        "auth_mode": "chatgpt",
        "chatgpt_credentials_path": str(credentials_path),
        "chatgpt_base_url": os.getenv("OPENAI_CHATGPT_BASE_URL")
        or "https://chatgpt.com/backend-api/codex",
        "use_chatgpt_auth_for_compaction": True,
        "system_message_as_instructions": True,
        "strip_leading_system_or_developer_message": True,
        "system_message": "You are a precise assistant. Reply exactly with the requested text.",
        "timeout": 120,
    }


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        OpenAIResponsesProvider,
        [OpenAIResponsesNativeCompactionExtension],
    )
    core.register_feature(OpenAIResponsesChatGPTAuthFeature)
    core.register_feature(SystemMessageFeature)
    return core


def _assert_has_compaction_placeholder(session) -> None:
    assert any(
        (message.metadata or {}).get("openai_responses_compaction")
        for message in session.messages
    )


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_chatgpt_saved_login_native_compaction() -> None:
    load_dotenv(REPO_ROOT / ".env")

    credentials_path = _credentials_path()
    _load_saved_credentials()

    core = _build_core()
    config = _chatgpt_config(credentials_path)

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly CHATGPT_COMPACTION_TURN_ONE",
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
    assert first_messages
    assert "CHATGPT_COMPACTION_TURN_ONE" in str(first_messages[-1].get("content"))

    compacted_session, result = core.execute_session_action(
        first_session,
        config,
        plugin_id="openai_responses_native_compaction",
        action_id="compact_native_history",
        params={},
    )

    assert result["message"] == "Compacted the full visible history."
    _assert_has_compaction_placeholder(compacted_session)

    compacted_session = core.add_message(
        compacted_session,
        "user",
        "Reply with exactly CHATGPT_COMPACTION_TURN_TWO",
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
    assert final_messages
    assert "CHATGPT_COMPACTION_TURN_TWO" in str(final_messages[-1].get("content"))
    _assert_has_compaction_placeholder(final_session)
    native_history = (final_session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert any(
        isinstance(item, dict) and item.get("type") in {"compaction", "compaction_summary"}
        for item in native_history
    )