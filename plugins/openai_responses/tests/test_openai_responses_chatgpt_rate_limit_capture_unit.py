from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider


class _HeaderCarrier:
    def __init__(self, headers: dict[str, str]) -> None:
        self.headers = headers


class _FixtureStream:
    def __init__(self, events: list[dict[str, Any]], headers: dict[str, str]) -> None:
        self._events = events
        self._response = _HeaderCarrier(headers)

    def __enter__(self) -> "_FixtureStream":
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        _ = (exc_type, exc, tb)

    def __iter__(self):
        for event in self._events:
            yield event


class _StreamingClient:
    def __init__(self, stream: _FixtureStream) -> None:
        self.responses = self
        self._stream = stream

    def create(self, **kwargs: Any) -> _FixtureStream:
        _ = kwargs
        return self._stream


def _chatgpt_state(tmp_path: Path) -> dict[str, Any]:
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text(
        json.dumps(
            {
                "access_token": "chatgpt-access-token",
                "refresh_token": "chatgpt-refresh-token",
                "token_type": "Bearer",
                "account_id": "acct-123",
                "account_email": "user@example.com",
                "plan_type": "plus",
            }
        ),
        encoding="utf-8",
    )
    return {
        "config": {
            "model": "gpt-5",
            "auth_mode": "chatgpt",
            "_openai_responses_effective_auth_mode": "chatgpt",
            "chatgpt_access_token": "chatgpt-access-token",
            "chatgpt_token_type": "Bearer",
            "chatgpt_account_id": "acct-123",
            "chatgpt_plan_type": "plus",
            "chatgpt_credentials_path": str(credentials_path),
            "chatgpt_base_url": "https://chatgpt.example.test/backend-api/codex",
        },
        "request": {
            "payload": {"model": "gpt-5"},
            "headers": {},
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


def test_stream_api_captures_codex_rate_limit_headers(tmp_path: Path, monkeypatch) -> None:
    provider = OpenAIResponsesProvider()
    state = _chatgpt_state(tmp_path)
    stream = _FixtureStream(
        [
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
        ],
        headers={
            "x-codex-primary-used-percent": "45",
            "x-codex-primary-window-minutes": "300",
            "x-codex-primary-reset-at": "1704069000",
            "x-codex-secondary-used-percent": "30",
            "x-codex-secondary-window-minutes": "10080",
            "x-codex-secondary-reset-at": "1705000000",
            "x-codex-credits-has-credits": "true",
            "x-codex-credits-unlimited": "false",
            "x-codex-credits-balance": "13",
        },
    )

    monkeypatch.setattr(
        provider,
        "_create_sdk_client_with_options",
        lambda config, *, timeout, max_retries: _StreamingClient(stream),
    )

    chunks = list(provider.stream_api(_native_messages(), state))
    assert [chunk["type"] for chunk in chunks] == ["response.output_text.delta", "response.completed"]

    rate_limits_path = tmp_path / "auth" / "chatgpt-rate-limits.json"
    saved = json.loads(rate_limits_path.read_text(encoding="utf-8"))
    assert saved["plan_type"] == "plus"
    assert saved["snapshots"][0]["primary"]["used_percent"] == 45.0
    assert saved["snapshots"][0]["credits"]["balance"] == "13"


def test_stream_api_stashes_snapshots_in_state_and_journals_them(tmp_path: Path, monkeypatch) -> None:
    provider = OpenAIResponsesProvider()
    state = _chatgpt_state(tmp_path)
    stream = _FixtureStream(
        [
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
        ],
        headers={
            "x-codex-primary-used-percent": "12",
            "x-codex-primary-window-minutes": "300",
            "x-codex-primary-reset-at": "1704069000",
        },
    )

    monkeypatch.setattr(
        provider,
        "_create_sdk_client_with_options",
        lambda config, *, timeout, max_retries: _StreamingClient(stream),
    )

    chunks = list(provider.stream_api(_native_messages(), state))
    assert [chunk["type"] for chunk in chunks] == ["response.completed"]

    stash = state.get("_openai_responses_chatgpt_rate_limit_snapshots")
    assert isinstance(stash, dict)
    assert stash["snapshots"][0]["primary"]["used_percent"] == 12.0
    assert stash["plan_type"] == "plus"
    assert isinstance(stash["captured_at"], str)

    journal_path = tmp_path / "auth" / "chatgpt-usage-journal.ndjson"
    assert journal_path.exists()
    lines = [
        line
        for line in journal_path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    assert len(lines) == 1
    record = json.loads(lines[0])
    assert record["type"] == "rate_limit_snapshot"
    assert record["plan_type"] == "plus"
    assert record["snapshots"][0]["primary"]["used_percent"] == 12.0
    assert isinstance(record["timestamp"], str)


def test_stream_api_does_not_capture_for_api_mode(tmp_path: Path, monkeypatch) -> None:
    provider = OpenAIResponsesProvider()
    state = _chatgpt_state(tmp_path)
    state["config"]["_openai_responses_effective_auth_mode"] = "api"
    state["config"].pop("chatgpt_access_token", None)
    stream = _FixtureStream(
        [
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
        ],
        headers={
            "x-codex-primary-used-percent": "12",
        },
    )

    monkeypatch.setattr(
        provider,
        "_create_sdk_client_with_options",
        lambda config, *, timeout, max_retries: _StreamingClient(stream),
    )

    list(provider.stream_api(_native_messages(), state))

    journal_path = tmp_path / "auth" / "chatgpt-usage-journal.ndjson"
    assert not journal_path.exists()
    assert "_openai_responses_chatgpt_rate_limit_snapshots" not in state