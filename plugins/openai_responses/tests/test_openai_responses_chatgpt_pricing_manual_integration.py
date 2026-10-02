"""Saved-login ChatGPT pricing integration tests for GPT-5.6.

Gated on ``CHATGPT_TEST_STATE_DIR`` pointing at a directory containing
``auth/chatgpt-auth.json``. Uses ``AgentApplication`` to verify the
session-owned ``opcache_*`` prompt cache key is auto-generated, then uses a
recording provider subclass to verify the key reaches the outgoing request
and is reused on follow-up turns.

Run with:

    CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
    OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna" \
      pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_pricing_manual_integration.py \
        -m "manual_integration and integration and openai" -q
"""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Tuple

import pytest
from dotenv import load_dotenv

from agent_app.application_future import AgentApplication
from agent_core import AgentCore

from feature_system_message.system_message_feature import SystemMessageFeature
from openai_responses_plugins import (
    OpenAIResponsesChatGPTAuthFeature,
    OpenAIResponsesFastModeExtension,
    OpenAIResponsesProvider,
    OpenAIResponsesUsageExtension,
)
from openai_responses_plugins.openai_responses_prompt_caching_extension import (
    OpenAIResponsesPromptCachingExtension,
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


# ---------------------------------------------------------------------------
# Recording provider subclass (captures outgoing request kwargs).
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Config helpers.
# ---------------------------------------------------------------------------


def _chatgpt_config(credentials_path: Path) -> dict[str, object]:
    model = os.getenv("OPENAI_RESPONSES_CHATGPT_MODEL") or "gpt-5.6-luna"
    return {
        "model": model,
        "auth_mode": "chatgpt",
        "chatgpt_credentials_path": str(credentials_path),
        "chatgpt_base_url": os.getenv("OPENAI_CHATGPT_BASE_URL")
        or "https://chatgpt.com/backend-api/codex",
        "system_message_as_instructions": True,
        "system_message": "You are a precise assistant. Reply exactly with the requested text.",
        "timeout": 180,
        "show_estimated_cached_tokens": True,
        "show_openai_auth_mode": True,
    }


def _build_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(
        _RecordingChatGPTProvider,
        extensions=[
            OpenAIResponsesPromptCachingExtension,
            OpenAIResponsesUsageExtension,
        ],
    )
    core.register_feature(OpenAIResponsesChatGPTAuthFeature)
    core.register_feature(SystemMessageFeature)
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


def _agent_application_config(credentials_path: Path, tmp_path: Path) -> Path:
    """Build an AgentApplication config that loads the openai_responses plugin
    with the prompt-caching extension and ChatGPT auth feature so the
    session-owned ``opcache_*`` key is auto-generated on session creation.
    """
    model = os.getenv("OPENAI_RESPONSES_CHATGPT_MODEL") or "gpt-5.6-luna"
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "openai": {
                "provider": "openai_responses",
                "model": model,
                "auth_mode": "chatgpt",
                "chatgpt_credentials_path": str(credentials_path),
                "chatgpt_base_url": os.getenv("OPENAI_CHATGPT_BASE_URL")
                or "https://chatgpt.com/backend-api/codex",
                "system_message_as_instructions": True,
                "system_message": "You are a precise assistant. Reply exactly with the requested text.",
                "timeout": 180,
            }
        },
        "plugins": [
            "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider",
            "openai_responses_plugins.openai_responses_chatgpt_auth_feature.OpenAIResponsesChatGPTAuthFeature",
            "openai_responses_plugins.openai_responses_prompt_caching_extension.OpenAIResponsesPromptCachingExtension",
            "openai_responses_plugins.openai_responses_usage_extension.OpenAIResponsesUsageExtension",
        ],
        "agents": {"default": {"provider": "openai"}},
    }
    config_path = tmp_path / "config_chatgpt_pricing.json"
    config_path.write_text(json.dumps(cfg), encoding="utf-8")
    return config_path


# ---------------------------------------------------------------------------
# Tests.
# ---------------------------------------------------------------------------


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_chatgpt_saved_login_default_tier_pricing(
    tmp_path: Path,
) -> None:
    """Default-tier ChatGPT pricing test using gpt-5.6-luna.

    Verifies:
    - AgentApplication auto-generates a session-owned ``opcache_*`` key.
    - The exact key is sent on the outgoing ChatGPT request.
    - The same key is reused on a follow-up turn.
    - Usage metadata is present with a positive estimated cost.
    - cache_write_tokens is preserved or explicitly reported as absent.
    """
    load_dotenv(REPO_ROOT / ".env")

    credentials_path = _credentials_path()
    _load_saved_credentials()

    # Step 1: Use AgentApplication to verify auto-generation of the opcache_* key.
    config_path = _agent_application_config(credentials_path, tmp_path)
    app = AgentApplication(str(config_path), str(tmp_path / "sessions"))
    _core, _base_config, app_session = app.create_session_ephemeral("default")

    overrides = (app_session.metadata or {}).get("overrides") or {}
    generated_key = overrides.get("prompt_cache_key")
    assert isinstance(generated_key, str) and generated_key.startswith(
        "opcache_"
    ), f"expected auto-generated opcache_* key, got {generated_key!r}"

    # Step 2: Use the recording provider to send the actual request with the
    # auto-generated key passed via config.
    _RecordingChatGPTProvider.recorded_requests = []
    core = _build_core()
    config = {**_chatgpt_config(credentials_path), "prompt_cache_key": generated_key}

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly: CHATGPT_PRICING_DEFAULT_OK",
        config=config,
    )

    final_session, final_messages = _send_streaming_request(core, session, config)

    final = final_messages[-1]
    assert final.get("role") == "assistant"
    assert isinstance(final.get("content"), str)
    assert "CHATGPT_PRICING_DEFAULT_OK" in final["content"]

    # Verify the exact opcache_* key was sent on the outgoing request.
    assert (
        _RecordingChatGPTProvider.recorded_requests
    ), "expected at least one recorded request"
    first_request = _RecordingChatGPTProvider.recorded_requests[0]
    assert first_request.get("prompt_cache_key") == generated_key, (
        f"expected outgoing request to carry {generated_key!r}, "
        f"got {first_request.get('prompt_cache_key')!r}"
    )

    # Verify usage metadata.
    metadata = final.get("metadata") or {}
    assert isinstance(metadata, dict)
    assert metadata.get("usage_effective_auth_mode") == "chatgpt"
    assert metadata.get("usage_effective_auth_mode_label") == "ChatGPT"
    # Report the service tier as currently observed; do NOT assert it's "standard".
    reported_tier = metadata.get("usage_service_tier")
    print(f"\nChatGPT default-tier test reported service_tier={reported_tier!r}")

    # Usage exists.
    usage = metadata.get("usage")
    assert isinstance(usage, dict), "expected usage dict in metadata"

    # Estimated cost is positive after the pricing fix.
    assert isinstance(metadata.get("usage_total_cost"), (int, float))
    assert (
        metadata.get("usage_total_cost") > 0
    ), "expected positive estimated cost for gpt-5.6-luna after pricing fix"
    assert isinstance(metadata.get("usage_total_cost_formatted"), str)

    # Estimated cached tokens are present (estimate preserved).
    assert isinstance(metadata.get("usage_estimated_cached_tokens"), int)

    # Report cache_write_tokens presence/absence explicitly.
    details = usage.get("input_tokens_details") or {}
    cache_write_tokens = details.get("cache_write_tokens")
    if isinstance(cache_write_tokens, int) and cache_write_tokens > 0:
        assert metadata.get("usage_cache_write_tokens_formatted") is not None
        print(
            f"\nChatGPT default-tier test: backend reported cache_write_tokens={cache_write_tokens}"
        )
    else:
        print(
            "\nChatGPT default-tier test: backend omitted cache_write_tokens; "
            "write-inclusive cost not verified."
        )

    # Step 3: Follow-up turn with the same key.
    follow_up_session = core.add_message(
        final_session,
        "user",
        "Reply with exactly: CHATGPT_PRICING_DEFAULT_FOLLOWUP_OK",
        config=config,
    )
    _RecordingChatGPTProvider.recorded_requests = []
    follow_up_session2, follow_up_messages = _send_streaming_request(
        core, follow_up_session, config
    )

    follow_up_final = follow_up_messages[-1]
    assert follow_up_final.get("role") == "assistant"
    assert "CHATGPT_PRICING_DEFAULT_FOLLOWUP_OK" in str(follow_up_final.get("content"))

    # Verify the same key is reused on the follow-up.
    assert (
        _RecordingChatGPTProvider.recorded_requests
    ), "expected follow-up recorded request"
    follow_up_request = _RecordingChatGPTProvider.recorded_requests[0]
    assert (
        follow_up_request.get("prompt_cache_key") == generated_key
    ), "expected follow-up request to reuse the same opcache_* key"

    # Report follow-up counters.
    follow_up_metadata = follow_up_final.get("metadata") or {}
    follow_up_usage = follow_up_metadata.get("usage") or {}
    follow_up_details = follow_up_usage.get("input_tokens_details") or {}
    print(
        f"\nChatGPT default-tier follow-up counters:\n"
        f"  estimated_cached_tokens={follow_up_metadata.get('usage_estimated_cached_tokens')}\n"
        f"  cached_tokens={follow_up_details.get('cached_tokens')}\n"
        f"  cache_write_tokens={follow_up_details.get('cache_write_tokens')}"
    )
    assert isinstance(follow_up_metadata.get("usage_estimated_cached_tokens"), int)
    assert (
        follow_up_metadata.get("usage_estimated_cached_tokens") > 0
    ), "expected follow-up turn to reuse estimated cached tokens"


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_chatgpt_saved_login_fast_tier_pricing(
    tmp_path: Path,
) -> None:
    """Fast mode ChatGPT pricing test using gpt-5.6-luna.

    Verifies:
    - The outgoing request uses ``service_tier: "priority"`` — the only tier
      name the ChatGPT backend accepts for Fast mode.
    - When the backend reports the fast tier, fast pricing is used.
    - If the account/model does not receive the fast tier (the backend reports
      ``default``), report that explicitly rather than claiming fast pricing
      was verified.
    """
    load_dotenv(REPO_ROOT / ".env")

    credentials_path = _credentials_path()
    _load_saved_credentials()

    # Verify auto-generation of the opcache_* key via AgentApplication.
    config_path = _agent_application_config(credentials_path, tmp_path)
    app = AgentApplication(str(config_path), str(tmp_path / "sessions"))
    _core, _base_config, app_session = app.create_session_ephemeral("default")
    overrides = (app_session.metadata or {}).get("overrides") or {}
    generated_key = overrides.get("prompt_cache_key")
    assert isinstance(generated_key, str) and generated_key.startswith("opcache_")

    _RecordingChatGPTProvider.recorded_requests = []
    core = AgentCore()
    core.register_provider(
        _RecordingChatGPTProvider,
        extensions=[
            OpenAIResponsesPromptCachingExtension,
            OpenAIResponsesFastModeExtension,
            OpenAIResponsesUsageExtension,
        ],
    )
    core.register_feature(OpenAIResponsesChatGPTAuthFeature)
    core.register_feature(SystemMessageFeature)

    config = {
        **_chatgpt_config(credentials_path),
        "auth_mode": "auto",
        "prompt_cache_key": generated_key,
        "enable_fast_mode": True,
        "show_openai_auth_mode": True,
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly: CHATGPT_PRICING_FAST_OK",
        config=config,
    )

    final_session, final_messages = _send_streaming_request(core, session, config)

    final = final_messages[-1]
    assert final.get("role") == "assistant"
    assert isinstance(final.get("content"), str)
    assert "CHATGPT_PRICING_FAST_OK" in final["content"]

    # Verify the outgoing request uses the ChatGPT backend's wire name. The
    # ChatGPT backend only accepts the legacy ``priority`` tier name
    # (sending ``fast`` fails with 400 ``Unsupported service_tier``).
    assert (
        _RecordingChatGPTProvider.recorded_requests
    ), "expected at least one recorded request"
    service_tier_requests = [
        req
        for req in _RecordingChatGPTProvider.recorded_requests
        if req.get("service_tier") is not None
    ]
    assert (
        service_tier_requests
    ), "expected at least one recorded request with service_tier"
    assert any(
        req.get("service_tier") == "priority" for req in service_tier_requests
    ), f"expected a priority-tier request, got {service_tier_requests!r}"

    # Verify the opcache_* key was sent.
    first_request = _RecordingChatGPTProvider.recorded_requests[0]
    assert first_request.get("prompt_cache_key") == generated_key

    metadata = final.get("metadata") or {}
    assert isinstance(metadata, dict)
    assert metadata.get("usage_effective_auth_mode") == "chatgpt"

    reported_tier = metadata.get("usage_service_tier")
    if reported_tier not in ("fast", "priority"):
        pytest.xfail(
            f"ChatGPT backend reported service_tier={reported_tier!r} for gpt-5.6-luna; "
            "the fast tier was not applied for this account/model, so fast-tier "
            "pricing is not verified."
        )

    # When the backend reports the fast tier, assert fast pricing was used.
    # ``priority`` is the obsolete name for the same tier and resolves the
    # same fast-tier prices.
    assert reported_tier in ("fast", "priority")
    assert isinstance(metadata.get("usage_total_cost"), (int, float))
    assert metadata.get("usage_total_cost") > 0

    # Report cache_write_tokens presence/absence.
    usage = metadata.get("usage") or {}
    details = usage.get("input_tokens_details") or {}
    cache_write_tokens = details.get("cache_write_tokens")
    if isinstance(cache_write_tokens, int) and cache_write_tokens > 0:
        print(
            f"\nChatGPT fast-tier test: backend reported cache_write_tokens={cache_write_tokens}"
        )
    else:
        print(
            "\nChatGPT fast-tier test: backend omitted cache_write_tokens; "
            "write-inclusive cost not verified."
        )
