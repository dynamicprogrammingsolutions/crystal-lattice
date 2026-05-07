from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest

import openai_responses_plugins.openai_responses_provider as provider_module
from openai_responses_plugins.chatgpt_credentials import ChatGPTRefreshPermanentError
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider


class _UnauthorizedError(RuntimeError):
    def __init__(self) -> None:
        super().__init__("Error code: 401 - {'detail': 'Could not parse your authentication token.'}")
        self.status_code = 401


class _FixtureStreamEvent:
    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = payload

    def model_dump(self, mode: str = "python") -> dict[str, Any]:
        _ = mode
        return self._payload


class _FixtureStream:
    def __init__(self, events: list[dict[str, Any]]) -> None:
        self._events = events

    def __enter__(self) -> "_FixtureStream":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        _ = (exc_type, exc, tb)

    def __iter__(self):
        for index, event in enumerate(self._events):
            if index % 2 == 0:
                yield _FixtureStreamEvent(event)
            else:
                yield event


class _UnauthorizedResponsesResource:
    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _FixtureStream:
        self.calls.append(kwargs)
        raise _UnauthorizedError()


class _SuccessfulResponsesResource:
    def __init__(self, events: list[dict[str, Any]]) -> None:
        self.calls: list[dict[str, Any]] = []
        self._events = events

    def create(self, **kwargs: Any) -> _FixtureStream:
        self.calls.append(kwargs)
        return _FixtureStream(self._events)


class _StreamingClient:
    def __init__(self, responses: Any) -> None:
        self.responses = responses
        self.option_calls: list[dict[str, Any]] = []

    def with_options(self, **kwargs: Any) -> "_StreamingClient":
        self.option_calls.append(kwargs)
        return self


def _stream_events() -> list[dict[str, Any]]:
    return [
        {"type": "response.output_text.delta", "delta": "ok"},
        {
            "type": "response.completed",
            "response": {
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "ok"}],
                    }
                ]
            },
        },
    ]


def _write_credentials(path: Path, *, access_token: str, refresh_token: str = "refresh-1") -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "Bearer",
                "account_id": "acct-123",
                "account_email": "user@example.com",
                "plan_type": "plus",
            }
        ),
        encoding="utf-8",
    )


def _chatgpt_state(credentials_path: Path) -> dict[str, Any]:
    return {
        "config": {
            "model": "gpt-5-mini",
            "auth_mode": "chatgpt",
            "_openai_responses_effective_auth_mode": "chatgpt",
            "chatgpt_access_token": "old-access",
            "chatgpt_token_type": "Bearer",
            "chatgpt_account_id": "acct-123",
            "chatgpt_credentials_path": str(credentials_path),
            "chatgpt_base_url": "https://chatgpt.example.test/backend-api/codex",
            "timeout": 30,
        },
        "request": {
            "payload": {"model": "gpt-5-mini"},
            "headers": {"Content-Type": "application/json"},
            "timeout": 30,
        },
    }


def _native_messages() -> list[dict[str, Any]]:
    return [
        {
            "type": "message",
            "role": "user",
            "content": [{"type": "input_text", "text": "hello"}],
        }
    ]


def test_stream_api_reloads_changed_chatgpt_credentials_before_refresh(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    _write_credentials(credentials_path, access_token="new-access")
    provider = OpenAIResponsesProvider()
    tokens_seen: list[str] = []
    success_responses = _SuccessfulResponsesResource(_stream_events())

    def _fake_create_client(config: dict[str, Any], *, timeout: float, max_retries: Any) -> _StreamingClient:
        _ = (timeout, max_retries)
        token = str(config.get("chatgpt_access_token"))
        tokens_seen.append(token)
        if token == "old-access":
            return _StreamingClient(_UnauthorizedResponsesResource())
        if token == "new-access":
            return _StreamingClient(success_responses)
        raise AssertionError(f"unexpected token {token!r}")

    def _unexpected_refresh(*args: Any, **kwargs: Any) -> dict[str, Any]:
        raise AssertionError("refresh should not be called when credentials already changed on disk")

    monkeypatch.setattr(provider, "_create_sdk_client_with_options", _fake_create_client)
    monkeypatch.setattr(provider_module, "refresh_chatgpt_credentials", _unexpected_refresh)

    chunks = list(provider.stream_api(_native_messages(), _chatgpt_state(credentials_path)))

    assert [chunk["type"] for chunk in chunks] == ["response.output_text.delta", "response.completed"]
    assert tokens_seen == ["old-access", "new-access"]
    assert len(success_responses.calls) == 1


def test_stream_api_refreshes_chatgpt_credentials_and_retries_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    _write_credentials(credentials_path, access_token="old-access", refresh_token="refresh-1")
    provider = OpenAIResponsesProvider()
    tokens_seen: list[str] = []
    success_responses = _SuccessfulResponsesResource(_stream_events())

    def _fake_create_client(config: dict[str, Any], *, timeout: float, max_retries: Any) -> _StreamingClient:
        _ = (timeout, max_retries)
        token = str(config.get("chatgpt_access_token"))
        tokens_seen.append(token)
        if token == "old-access":
            return _StreamingClient(_UnauthorizedResponsesResource())
        if token == "refreshed-access":
            return _StreamingClient(success_responses)
        raise AssertionError(f"unexpected token {token!r}")

    def _refresh_credentials(path: Path, *, timeout: float) -> dict[str, Any]:
        _ = timeout
        _write_credentials(path, access_token="refreshed-access", refresh_token="refresh-2")
        return {
            "access_token": "refreshed-access",
            "refresh_token": "refresh-2",
            "token_type": "Bearer",
            "account_id": "acct-123",
            "account_email": "user@example.com",
            "plan_type": "plus",
        }

    monkeypatch.setattr(provider, "_create_sdk_client_with_options", _fake_create_client)
    monkeypatch.setattr(provider_module, "refresh_chatgpt_credentials", _refresh_credentials)

    chunks = list(provider.stream_api(_native_messages(), _chatgpt_state(credentials_path)))
    saved = json.loads(credentials_path.read_text(encoding="utf-8"))

    assert [chunk["type"] for chunk in chunks] == ["response.output_text.delta", "response.completed"]
    assert tokens_seen == ["old-access", "refreshed-access"]
    assert saved["access_token"] == "refreshed-access"
    assert saved["refresh_token"] == "refresh-2"
    assert len(success_responses.calls) == 1


def test_stream_api_surfaces_clear_error_when_chatgpt_refresh_fails_permanently(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    _write_credentials(credentials_path, access_token="old-access", refresh_token="refresh-1")
    provider = OpenAIResponsesProvider()

    def _fake_create_client(config: dict[str, Any], *, timeout: float, max_retries: Any) -> _StreamingClient:
        _ = (config, timeout, max_retries)
        return _StreamingClient(_UnauthorizedResponsesResource())

    def _refresh_credentials(path: Path, *, timeout: float) -> dict[str, Any]:
        _ = (path, timeout)
        raise ChatGPTRefreshPermanentError(
            "Saved ChatGPT login expired or was revoked. Please sign in again."
        )

    monkeypatch.setattr(provider, "_create_sdk_client_with_options", _fake_create_client)
    monkeypatch.setattr(provider_module, "refresh_chatgpt_credentials", _refresh_credentials)

    with pytest.raises(RuntimeError, match="Saved ChatGPT login expired or was revoked"):
        list(provider.stream_api(_native_messages(), _chatgpt_state(credentials_path)))