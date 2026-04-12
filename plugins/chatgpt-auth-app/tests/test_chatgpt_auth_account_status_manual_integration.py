from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

import pytest
from dotenv import load_dotenv

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


REPO_ROOT = Path(__file__).resolve().parents[3]
_DEFAULT_MANUAL_STATE_DIR = Path(__file__).resolve().parent / ".manual-state"


def _plugin_entry(repo_name: str, entry: str) -> Dict[str, str]:
    return {"path": str(REPO_ROOT / "plugins" / repo_name), "entry": entry}


def _manual_state_dir() -> Path:
    raw = os.getenv("CHATGPT_TEST_STATE_DIR")
    if isinstance(raw, str) and raw.strip():
        return Path(raw).expanduser()
    return _DEFAULT_MANUAL_STATE_DIR


def _credentials_path() -> Path:
    return _manual_state_dir() / "auth" / "chatgpt-auth.json"


def _rate_limits_path() -> Path:
    return _manual_state_dir() / "auth" / "chatgpt-rate-limits.json"


def _load_saved_credentials() -> dict[str, object]:
    path = _credentials_path()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        pytest.skip(f"saved ChatGPT login not found at {path}")
    if not isinstance(payload, dict):
        pytest.skip(f"saved ChatGPT login at {path} is not a JSON object")
    return payload


def _write_config(state_dir: Path) -> Path:
    model = os.getenv("OPENAI_RESPONSES_CHATGPT_MODEL") or "gpt-5"
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(state_dir / ".plugin_cache"),
        "providers": {
            "chatgpt": {
                "provider": "openai_responses",
                "model": model,
                "auth_mode": "chatgpt",
                "chatgpt_credentials_path": "${env:CONFIG_DIR}/auth/chatgpt-auth.json",
                "chatgpt_rate_limits_path": "${env:CONFIG_DIR}/auth/chatgpt-rate-limits.json",
                "chatgpt_base_url": os.getenv("OPENAI_CHATGPT_BASE_URL")
                or "https://chatgpt.com/backend-api/codex",
                "system_message_as_instructions": True,
                "strip_leading_system_or_developer_message": True,
                "system_message": "You are a precise assistant. Reply exactly with the requested text.",
                "timeout": 120,
            }
        },
        "plugins": [
            _plugin_entry("chatgpt-auth-app", "chatgpt_auth_app.ChatGPTAuthAppPlugin"),
            _plugin_entry("openai_responses", "openai_responses_plugins.OpenAIResponsesProvider"),
            _plugin_entry(
                "openai_responses",
                "openai_responses_plugins.OpenAIResponsesChatGPTAuthFeature",
            ),
            _plugin_entry(
                "feature-system-message",
                "feature_system_message.system_message_feature.SystemMessageFeature",
            ),
        ],
        "agents": {
            "default": {"provider": "chatgpt"},
        },
        "application": {
            "chatgpt_auth": {
                "credentials_path": "${env:CONFIG_DIR}/auth/chatgpt-auth.json",
                "rate_limits_path": "${env:CONFIG_DIR}/auth/chatgpt-rate-limits.json",
            }
        },
    }
    path = state_dir / "config_chatgpt_account_status_manual.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_chatgpt_account_status_after_real_request() -> None:
    load_dotenv(REPO_ROOT / ".env")

    state_dir = _manual_state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    _load_saved_credentials()

    rate_limits_path = _rate_limits_path()
    rate_limits_path.unlink(missing_ok=True)

    config_path = _write_config(state_dir)
    app = AgentApplication(
        str(config_path),
        str(state_dir / "sessions"),
        event_store=InMemoryEventStore(),
        env_overrides={"CONFIG_DIR": str(state_dir)},
    )

    core, base_config, session = app.create_session("default")
    session = core.add_message(
        session,
        "user",
        "Reply with exactly: CHATGPT_ACCOUNT_STATUS_OK",
        config=base_config,
    )
    app.save_session(session)

    final_seen = False
    for event in app.send_request(core, session, base_config, stream=True):
        if event.get("type") == "final":
            final_seen = True

    assert final_seen, "expected final event from real ChatGPT-backed request"
    assert rate_limits_path.exists(), "expected ChatGPT rate-limit sidecar to be captured"

    saved_limits = json.loads(rate_limits_path.read_text(encoding="utf-8"))
    snapshots = saved_limits.get("snapshots")
    assert isinstance(snapshots, list) and snapshots, "expected non-empty rate-limit snapshots"

    result = app.execute_application_action(
        "chatgpt_auth",
        "show_account_status",
        {"session_id": session.session_id},
    )
    body = result["display"]["body"]
    assert "Effective auth mode: `chatgpt`" in body
    assert "Usage limits:" in body
    assert (
        "5h limit:" in body
        or "Weekly limit:" in body
        or "Monthly limit:" in body
        or "Credits:" in body
    )