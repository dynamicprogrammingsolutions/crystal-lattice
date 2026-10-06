from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv

from agent_app.application_future import AsyncRuntimeHost
from agent_core import AgentCore
from feature_system_message.system_message_feature import SystemMessageFeature
from openai_responses_plugins import (
    OpenAIResponsesChatGPTAuthFeature,
    OpenAIResponsesProvider,
)
from openai_responses_plugins.openai_responses_native_compaction import (
    COMPACTION_TRANSPORT_CONTEXT_KEY,
    CancellableAsyncOpenAIResponsesCompactionTransport,
)
from openai_responses_plugins.openai_responses_native_compaction_extension import (
    OpenAIResponsesNativeCompactionExtension,
)
from openai_responses_plugins.openai_responses_websearch_extension import (
    OpenAIResponsesWebSearchExtension,
)
from plugins.request_options_feature import RequestOptionsFeature


REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_CHATGPT_AUTH_STATE_DIR = (
    REPO_ROOT / "plugins" / "chatgpt-auth-app" / "tests" / ".manual-state"
)
_DEFAULT_CRYSTAL_CREDENTIALS_PATH = (
    Path.home() / ".crystal" / "auth" / "chatgpt-auth.json"
)
pytestmark = pytest.mark.api


def _manual_state_dir() -> Path:
    raw = os.getenv("CHATGPT_TEST_STATE_DIR")
    if isinstance(raw, str) and raw.strip():
        return Path(raw).expanduser()
    return _DEFAULT_CHATGPT_AUTH_STATE_DIR


def _credentials_path() -> Path:
    configured_state_dir = os.getenv("CHATGPT_TEST_STATE_DIR")
    if isinstance(configured_state_dir, str) and configured_state_dir.strip():
        return Path(configured_state_dir).expanduser() / "auth" / "chatgpt-auth.json"
    if _DEFAULT_CRYSTAL_CREDENTIALS_PATH.is_file():
        return _DEFAULT_CRYSTAL_CREDENTIALS_PATH
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
    model = os.getenv("OPENAI_RESPONSES_CHATGPT_MODEL") or "gpt-6-luna"
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
        [OpenAIResponsesNativeCompactionExtension, OpenAIResponsesWebSearchExtension],
    )
    core.register_feature(OpenAIResponsesChatGPTAuthFeature)
    core.register_feature(SystemMessageFeature)
    core.register_feature(RequestOptionsFeature)
    return core


def _assert_has_compaction_native_items(session) -> None:
    native_history = (session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert any(
        isinstance(item, dict)
        and item.get("type") in {"compaction", "compaction_summary"}
        for item in native_history
    )


class _RecordedCompactionTransport(CancellableAsyncOpenAIResponsesCompactionTransport):
    input_items: list[dict[str, Any]] | None = None

    def compact(
        self,
        *,
        model: str,
        input_items: list[dict[str, Any]],
        instructions: str | None,
        request_options: dict[str, Any] | None = None,
        timeout: float,
    ) -> Any:
        self.input_items = input_items
        return super().compact(
            model=model,
            input_items=input_items,
            instructions=instructions,
            request_options=request_options,
            timeout=timeout,
        )


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
@pytest.mark.parametrize(
    "with_web_search", [False, True], ids=["plain-history", "web-search-history"]
)
def test_openai_responses_chatgpt_saved_login_native_compaction(
    with_web_search: bool,
) -> None:
    load_dotenv(REPO_ROOT / ".env")

    credentials_path = _credentials_path()
    _load_saved_credentials()

    core = _build_core()
    config = _chatgpt_config(credentials_path)
    first_config = config
    prompt = "Reply with exactly CHATGPT_COMPACTION_TURN_ONE"
    if with_web_search:
        config = {**config, "enable_web_search": True}
        first_config = {
            **config,
            "request_options": {"tool_choice": {"type": "web_search"}},
        }
        prompt = (
            "Search the web for the official OpenAI Responses API documentation. "
            "Then reply with exactly CHATGPT_COMPACTION_TURN_ONE"
        )

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        prompt,
        config=first_config,
    )

    first_session = None
    first_messages = None
    for chunk in core.send_request_stream(session, first_config):
        if chunk.get("type") == "final":
            first_session = chunk.get("session")
            first_messages = chunk.get("messages")

    assert first_session is not None
    assert isinstance(first_messages, list)
    assert first_messages
    assert "CHATGPT_COMPACTION_TURN_ONE" in str(first_messages[-1].get("content"))
    searches: list[dict[str, Any]] = []
    if with_web_search:
        native_history = (first_session.metadata or {}).get("native_messages")
        assert isinstance(native_history, list)
        searches = [
            item for item in native_history if item.get("type") == "web_search_call"
        ]
        assert searches
        assert all(item.get("status") == "completed" for item in searches)

    runtime = AsyncRuntimeHost()
    transport = _RecordedCompactionTransport(
        run_awaitable_blocking=runtime.run_blocking,
    )
    try:
        compacted_session, result = core.execute_session_action(
            first_session,
            config,
            plugin_id="openai_responses_native_compaction",
            action_id="compact_native_history_sync",
            params={},
            context={COMPACTION_TRANSPORT_CONTEXT_KEY: transport},
        )
    finally:
        runtime.close()

    assert result["message"] == "Compacted the full visible history."
    _assert_has_compaction_native_items(compacted_session)
    if with_web_search:
        assert transport.input_items is not None
        compact_searches = [
            item
            for item in transport.input_items
            if item.get("type") == "web_search_call"
        ]
        assert compact_searches
        assert [(item["id"], item["status"]) for item in compact_searches] == [
            (item["id"], item["status"]) for item in searches
        ]
        assert all("_metadata" not in item for item in compact_searches)

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
    _assert_has_compaction_native_items(final_session)
    native_history = (final_session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert any(
        isinstance(item, dict)
        and item.get("type") in {"compaction", "compaction_summary"}
        for item in native_history
    )


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_chatgpt_automatic_compaction() -> None:
    credentials_path = _credentials_path()
    _load_saved_credentials()

    core = _build_core()
    config = {
        **_chatgpt_config(credentials_path),
        "enable_openai_automatic_compaction": True,
        "openai_compaction_trigger_tokens": 1000,
    }
    filler = ("compactible context line. " * 600).strip()
    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        f"{filler}\nReply with exactly CHATGPT_AUTOMATIC_COMPACTION_ONE.",
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
    assert "CHATGPT_AUTOMATIC_COMPACTION_ONE" in str(first_messages[-1].get("content"))
    _assert_has_compaction_native_items(first_session)

    first_session = core.add_message(
        first_session,
        "user",
        "Reply with exactly CHATGPT_AUTOMATIC_COMPACTION_TWO.",
        config=config,
    )
    final_session = None
    final_messages = None
    for chunk in core.send_request_stream(first_session, config):
        if chunk.get("type") == "final":
            final_session = chunk.get("session")
            final_messages = chunk.get("messages")

    assert final_session is not None
    assert isinstance(final_messages, list)
    assert final_messages
    assert "CHATGPT_AUTOMATIC_COMPACTION_TWO" in str(final_messages[-1].get("content"))
    _assert_has_compaction_native_items(final_session)
