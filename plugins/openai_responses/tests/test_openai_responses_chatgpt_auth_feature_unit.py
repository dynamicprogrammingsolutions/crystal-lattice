from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from openai_responses_plugins import (
    OpenAIResponsesChatGPTAuthFeature,
    OpenAIResponsesProvider,
)


def _write_credentials(path: Path, *, expires_in_seconds: int = 3600) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "access_token": "chatgpt-access-token",
        "token_type": "Bearer",
        "account_email": "user@example.com",
        "account_id": "acct-123",
        "plan_type": "plus",
        "expires_at": (
            datetime.now(timezone.utc) + timedelta(seconds=expires_in_seconds)
        ).isoformat().replace("+00:00", "Z"),
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_auto_mode_falls_back_to_api_without_saved_login(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))
    feature = OpenAIResponsesChatGPTAuthFeature()
    provider = OpenAIResponsesProvider()
    config = {
        "model": "gpt-5-mini",
        "api_key": "api-key",
        "auth_mode": "auto",
        "api_base_url": "https://api.example.test/v1",
    }

    state = feature.init(config, {"config": dict(config)})
    auth_state = state["_openai_responses_chatgpt_auth"]
    assert auth_state["requested_mode"] == "auto"
    assert auth_state["effective_mode"] == "api"
    assert auth_state["logged_in"] is False
    assert state["config"]["chatgpt_credentials_path"] == str(tmp_path / "auth" / "chatgpt-auth.json")

    _, request_state = provider.initialize_request([], state)
    request = request_state["request"]
    assert request["url"] == "https://api.example.test/v1/responses"
    assert request["headers"]["Authorization"] == "Bearer api-key"


def test_chatgpt_mode_uses_saved_credentials_and_chatgpt_endpoint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    _write_credentials(credentials_path)

    feature = OpenAIResponsesChatGPTAuthFeature()
    provider = OpenAIResponsesProvider()
    config = {
        "model": "gpt-5-mini",
        "auth_mode": "chatgpt",
        "chatgpt_base_url": "https://chatgpt.example.test/backend-api/codex",
        "chatgpt_credentials_path": str(credentials_path),
    }

    state = feature.init(config, {"config": dict(config)})
    auth_state = state["_openai_responses_chatgpt_auth"]
    assert auth_state["effective_mode"] == "chatgpt"
    assert auth_state["logged_in"] is True
    assert state["config"]["chatgpt_access_token"] == "chatgpt-access-token"
    assert state["config"]["chatgpt_account_id"] == "acct-123"

    _, request_state = provider.initialize_request([], state)
    request = request_state["request"]
    assert request["url"] == "https://chatgpt.example.test/backend-api/codex/responses"
    assert request["headers"]["Authorization"] == "Bearer chatgpt-access-token"
    assert request["headers"]["ChatGPT-Account-Id"] == "acct-123"


def test_chatgpt_mode_without_saved_credentials_raises_clear_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))
    feature = OpenAIResponsesChatGPTAuthFeature()
    provider = OpenAIResponsesProvider()
    config = {
        "model": "gpt-5-mini",
        "auth_mode": "chatgpt",
    }

    state = feature.init(config, {"config": dict(config)})

    with pytest.raises(ValueError, match="chatgpt auth_mode requires a valid saved ChatGPT login"):
        provider.initialize_request([], state)


def test_chatgpt_mode_nonstreaming_path_raises_clear_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    _write_credentials(credentials_path)

    feature = OpenAIResponsesChatGPTAuthFeature()
    provider = OpenAIResponsesProvider()
    config = {
        "model": "gpt-5-mini",
        "auth_mode": "chatgpt",
        "chatgpt_credentials_path": str(credentials_path),
    }

    state = feature.init(config, {"config": dict(config)})
    native_messages, request_state = provider.initialize_request([], state)

    with pytest.raises(RuntimeError, match="chatgpt auth_mode requires streaming requests"):
        provider.call_api(native_messages, request_state)


def test_auth_mode_and_endpoint_ui_are_exposed_as_config_elements() -> None:
    provider = OpenAIResponsesProvider()
    feature = OpenAIResponsesChatGPTAuthFeature()

    provider_elements = provider.get_ui_elements(
        config={},
        tags=["provider:openai_responses"],
        models=[{"id": "gpt-5-mini"}],
    )
    feature_elements = feature.get_ui_elements({"model": "gpt-5-mini"})

    auth_config = [element for element in provider_elements if element.get("key") == "auth_mode"]
    assert len(auth_config) == 1
    assert auth_config[0]["ui_type"] == "config"

    endpoint_config = [element for element in feature_elements if element.get("key") == "effective_base_url"]
    assert len(endpoint_config) == 1
    assert endpoint_config[0]["ui_type"] == "config"
    assert endpoint_config[0]["type"] == "readonly"
    assert endpoint_config[0]["default"] == "https://api.openai.com/v1"


def test_endpoint_ui_uses_chatgpt_default_when_auto_mode_has_valid_login(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CONFIG_DIR", str(tmp_path))
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    _write_credentials(credentials_path)

    feature = OpenAIResponsesChatGPTAuthFeature()
    elements = feature.get_ui_elements(
        {
            "auth_mode": "auto",
            "chatgpt_credentials_path": str(credentials_path),
            "chatgpt_base_url": "https://chatgpt.example.test/backend-api/codex",
        }
    )

    assert elements == [
        {
            "ui_type": "config",
            "type": "readonly",
            "key": "effective_base_url",
            "config_path": "chatgpt_base_url",
            "label": "OpenAI endpoint URL",
            "description": "Effective endpoint URL used for ChatGPT-backed OpenAI Responses requests.",
            "default": "https://chatgpt.example.test/backend-api/codex",
        }
    ]