from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pytest
from dotenv import load_dotenv

from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider


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


@pytest.mark.manual_integration
@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_chatgpt_model_discovery_includes_gpt_5_6_family() -> None:
    load_dotenv(REPO_ROOT / ".env")

    credentials_path = _credentials_path()
    _load_saved_credentials()

    provider = OpenAIResponsesProvider()
    config = {
        "auth_mode": "chatgpt",
        "chatgpt_credentials_path": str(credentials_path),
        "chatgpt_base_url": os.getenv("OPENAI_CHATGPT_BASE_URL")
        or "https://chatgpt.com/backend-api/codex",
        "timeout": 120,
    }

    models = provider.get_models(config)

    assert isinstance(models, list)
    assert models, "ChatGPT model discovery returned an empty model list"
    model_ids = {
        model["id"] for model in models if isinstance(model, dict) and model.get("id")
    }
    expected = {"gpt-5.6-sol", "gpt-5.6-terra", "gpt-5.6-luna"}
    missing = expected - model_ids
    assert (
        not missing
    ), f"expected GPT-5.6 family IDs missing from ChatGPT discovery: {sorted(missing)}"
