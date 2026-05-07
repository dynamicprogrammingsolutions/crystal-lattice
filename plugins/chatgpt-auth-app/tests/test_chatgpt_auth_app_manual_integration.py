from __future__ import annotations

import json
import os
import time
from pathlib import Path
from typing import Any, Dict

import pytest

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


@pytest.mark.manual_integration
def test_manual_device_login_flow() -> None:
    state_dir = _manual_state_dir()
    state_dir.mkdir(parents=True, exist_ok=True)
    issuer = os.getenv("CHATGPT_ISSUER", "https://auth.openai.com").rstrip("/")
    device_code_endpoint = os.getenv(
        "CHATGPT_DEVICE_CODE_ENDPOINT",
        f"{issuer}/api/accounts/deviceauth/usercode",
    )
    token_endpoint = os.getenv(
        "CHATGPT_TOKEN_ENDPOINT",
        f"{issuer}/api/accounts/deviceauth/token",
    )
    token_exchange_endpoint = os.getenv(
        "CHATGPT_TOKEN_EXCHANGE_ENDPOINT",
        f"{issuer}/oauth/token",
    )
    client_id = os.getenv("CHATGPT_CLIENT_ID", "app_EMoamEEZ73f0CkXaXp7hrann")
    client_secret = os.getenv("CHATGPT_CLIENT_SECRET")
    if not client_id:
        pytest.skip("CHATGPT_CLIENT_ID must be set when overriding the default")

    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(state_dir / ".plugin_cache"),
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "test-model"}
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            _plugin_entry(
                "chatgpt-auth-app",
                "chatgpt_auth_app.ChatGPTAuthAppPlugin",
            ),
        ],
        "agents": {
            "default": {"provider": "echo"},
        },
        "application": {
            "chatgpt_auth": {
                "issuer": issuer,
                "credentials_path": "${env:CONFIG_DIR}/auth/chatgpt-auth.json",
                "device_code_endpoint": device_code_endpoint,
                "token_endpoint": token_endpoint,
                "token_exchange_endpoint": token_exchange_endpoint,
                "client_id": client_id,
                "client_secret": client_secret,
                "request_encoding": os.getenv("CHATGPT_REQUEST_ENCODING", "json"),
                "device_code_poll_interval_seconds": 5,
                "login_timeout_seconds": 300,
                "http_timeout_seconds": 20,
            }
        },
    }

    config_path = state_dir / "config_chatgpt_auth_manual.json"
    config_path.write_text(json.dumps(cfg), encoding="utf-8")

    app = AgentApplication(
        str(config_path),
        str(state_dir / "sessions"),
        event_store=InMemoryEventStore(),
    )

    result = app.execute_application_action("chatgpt_auth", "login_start", {})
    auth_status = result["auth_status"]
    print("Open this URL in a browser:", auth_status["verification_url"])
    print("Enter this code:", auth_status["user_code"])

    deadline = time.time() + 300
    last_status = auth_status
    while time.time() < deadline:
        last_status = app.execute_application_action("chatgpt_auth", "check_status", {})[
            "auth_status"
        ]
        if last_status["state"] == "authenticated":
            break
        time.sleep(5)

    assert last_status["state"] == "authenticated"
    credentials_path = state_dir / "auth" / "chatgpt-auth.json"
    assert credentials_path.exists()
    print("Saved credentials to:", credentials_path)