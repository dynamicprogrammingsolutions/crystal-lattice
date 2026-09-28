from __future__ import annotations

import json
import os
import runpy
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
OPENAI_RESPONSES_SRC = ROOT / "plugins/openai_responses/src"
if str(OPENAI_RESPONSES_SRC) not in sys.path:
    sys.path.insert(0, str(OPENAI_RESPONSES_SRC))
FEATURE_SYSTEM_MESSAGE_SRC = ROOT / "plugins/feature-system-message/src"
if str(FEATURE_SYSTEM_MESSAGE_SRC) not in sys.path:
    sys.path.insert(0, str(FEATURE_SYSTEM_MESSAGE_SRC))

from agent_app.config import (  # noqa: E402
    build_config_resolution_env,
    resolve_placeholders,
)
from agent_core import AgentCore  # noqa: E402
from plugin_provision import module_importable, provision_plugin  # noqa: E402

CONFIG_PATH = (
    ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "default_config"
    / "config.json"
)
HELPER_PATH = (
    CONFIG_PATH.parent
    / "system_messages"
    / "helpers"
    / "select_codex_developer_message.py"
)

_DEFAULT_CHATGPT_AUTH_STATE_DIR = (
    ROOT / "plugins" / "chatgpt-auth-app" / "tests" / ".manual-state"
)
GPT_6_DISTINCTIVE_SUBSTRING = "You are Codex, an agent based on GPT-6"
GPT_6_CONNECTOR_PLACEHOLDER = "app://{{connector_id}}"
EXPECTED_REPLY_MARKER = "CHATGPT_GPT6SOL_INSTRUCTIONS_OK"

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


def _compiled_codex_developer_message(model: str) -> str:
    raw_config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    resolution_env = build_config_resolution_env(CONFIG_PATH)
    resolution_env["CONFIG_DIR"] = str(CONFIG_PATH.parent.resolve())
    resolved_config, _errors = resolve_placeholders(raw_config, env=resolution_env)
    rows = resolved_config["mixins"]["codex_developer_message"][
        "codex_developer_messages"
    ]
    config = {"codex_developer_messages": rows, "model": model}
    namespace = runpy.run_path(str(HELPER_PATH), init_globals={"CONFIG": config})
    return namespace["select_codex_developer_message"]()


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


@pytest.fixture(scope="session")
def openai_responses_plugin(tmp_path_factory: pytest.TempPathFactory) -> None:
    """Provision the openai_responses plugin on the fly when it is not installed.

    The application default config loads this plugin dynamically, so the
    application test environment never installs it or its ``openai`` SDK
    dependency. This test drives the provider directly, so it installs the
    plugin hermetically (``pip install --target``) only when needed.
    """
    if module_importable("openai_responses_plugins"):
        return
    target_dir = tmp_path_factory.mktemp("openai_responses_plugin")
    provision_plugin(ROOT / "plugins" / "openai_responses", target_dir)
    sys.path.insert(0, str(target_dir))


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


def _chatgpt_config(
    credentials_path: Path, model: str, compiled_system_message: str
) -> dict[str, object]:
    return {
        "model": model,
        "auth_mode": "chatgpt",
        "chatgpt_credentials_path": str(credentials_path),
        "chatgpt_base_url": os.getenv("OPENAI_CHATGPT_BASE_URL")
        or "https://chatgpt.com/backend-api/codex",
        "system_message_as_instructions": True,
        "system_message": compiled_system_message,
        "timeout": 240,
        "reasoning_effort": "low",
        "reasoning_summary": "concise",
        "show_openai_auth_mode": True,
    }


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_chatgpt_gpt6_sol_system_instructions_round_trip(
    openai_responses_plugin: None,
) -> None:
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

    def _build_recording_core() -> AgentCore:
        core = AgentCore()
        core.register_provider(
            _RecordingChatGPTProvider,
            extensions=[
                OpenAIResponsesReasoningExtension,
                OpenAIResponsesUsageExtension,
            ],
        )
        core.register_feature(OpenAIResponsesChatGPTAuthFeature)
        core.register_feature(SystemMessageFeature)
        core.register_feature(RequestOptionsFeature)
        return core

    load_dotenv(ROOT / ".env")

    credentials_path = _credentials_path()
    _load_saved_credentials()

    model = os.getenv("OPENAI_RESPONSES_CHATGPT_GPT6_MODEL") or "gpt-6-sol"
    compiled_system_message = _compiled_codex_developer_message(model)
    assert (
        GPT_6_DISTINCTIVE_SUBSTRING in compiled_system_message
    ), "compiled system message should contain the GPT-6 distinctive substring"
    assert (
        GPT_6_CONNECTOR_PLACEHOLDER in compiled_system_message
    ), "the literal {{connector_id}} app-trigger syntax should be kept verbatim"

    _RecordingChatGPTProvider.recorded_requests = []
    core = _build_recording_core()
    config = _chatgpt_config(credentials_path, model, compiled_system_message)

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        f"Reply with exactly: {EXPECTED_REPLY_MARKER}",
        config=config,
    )

    final_session, final_messages = _send_streaming_request(core, session, config)

    final = final_messages[-1]
    assert final.get("role") == "assistant"
    assert isinstance(final.get("content"), str)
    assert EXPECTED_REPLY_MARKER in final["content"]

    assert (
        _RecordingChatGPTProvider.recorded_requests
    ), "expected at least one recorded request"
    instructions = _RecordingChatGPTProvider.recorded_requests[0].get("instructions")
    assert isinstance(instructions, str)
    assert (
        GPT_6_DISTINCTIVE_SUBSTRING in instructions
    ), "recorded request instructions should contain the GPT-6 distinctive substring"

    metadata = final.get("metadata") or {}
    assert isinstance(metadata, dict)
    assert metadata.get("usage_effective_auth_mode") == "chatgpt"


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_chatgpt_gpt6_sol_selection_only() -> None:
    load_dotenv(ROOT / ".env")

    _credentials_path()
    _load_saved_credentials()

    compiled = _compiled_codex_developer_message("gpt-6-sol")
    assert GPT_6_DISTINCTIVE_SUBSTRING in compiled, (
        "compiled system message for gpt-6-sol should contain the GPT-6 "
        "distinctive substring"
    )
    # The GPT-6 family members have pairwise-distinct templates, and each is
    # distinct from every GPT-5.6 family member.
    astra = _compiled_codex_developer_message("gpt-6-astra")
    luna6 = _compiled_codex_developer_message("gpt-6-luna")
    assert len({compiled, astra, luna6}) == 3
    for model in ("gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"):
        family_compiled = _compiled_codex_developer_message(model)
        assert compiled != family_compiled, f"gpt-6-sol should be distinct from {model}"
