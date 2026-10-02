from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from urllib.error import HTTPError, URLError

import pytest

import openai_responses_plugins.chatgpt_credentials as credentials_module
from openai_responses_plugins.chatgpt_credentials import (
    ChatGPTRefreshPermanentError,
    ChatGPTRefreshTransientError,
    refresh_chatgpt_credentials,
)


def _jwt(payload: dict[str, object]) -> str:
    encoded = base64.urlsafe_b64encode(json.dumps(payload).encode("utf-8")).decode("ascii").rstrip("=")
    return f"header.{encoded}.signature"


def _write_credentials(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(
            {
                "access_token": "old-access",
                "refresh_token": "old-refresh",
                "id_token": _jwt(
                    {
                        "email": "old@example.com",
                        "chatgpt_account_id": "acct-old",
                        "chatgpt_plan_type": "free",
                    }
                ),
                "plan_type": "free",
                "account_id": "acct-old",
                "account_email": "old@example.com",
            }
        ),
        encoding="utf-8",
    )


class _StubHTTPResponse:
    def __init__(self, body: str) -> None:
        self._body = body.encode("utf-8")

    def read(self) -> bytes:
        return self._body

    def __enter__(self) -> "_StubHTTPResponse":
        return self

    def __exit__(self, exc_type: object, exc: object, tb: object) -> None:
        _ = (exc_type, exc, tb)


def test_refresh_chatgpt_credentials_rotates_tokens_and_persists(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    _write_credentials(credentials_path)

    captured: dict[str, object] = {}

    def _fake_urlopen(
        request: object,
        timeout: float,
        context: object,
    ) -> _StubHTTPResponse:
        assert context is not None
        captured["timeout"] = timeout
        captured["url"] = request.full_url
        captured["payload"] = json.loads(request.data.decode("utf-8"))
        return _StubHTTPResponse(
            json.dumps(
                {
                    "access_token": "new-access",
                    "refresh_token": "new-refresh",
                    "id_token": _jwt(
                        {
                            "email": "new@example.com",
                            "chatgpt_account_id": "acct-new",
                            "chatgpt_plan_type": "plus",
                        }
                    ),
                    "token_type": "bearer",
                    "expires_in": 3600,
                }
            )
        )

    monkeypatch.setattr(credentials_module, "urlopen", _fake_urlopen)

    refreshed = refresh_chatgpt_credentials(credentials_path, timeout=12.5)

    saved = json.loads(credentials_path.read_text(encoding="utf-8"))
    assert captured == {
        "timeout": 12.5,
        "url": "https://auth.openai.com/oauth/token",
        "payload": {
            "client_id": "app_EMoamEEZ73f0CkXaXp7hrann",
            "grant_type": "refresh_token",
            "refresh_token": "old-refresh",
        },
    }
    assert refreshed["access_token"] == "new-access"
    assert refreshed["refresh_token"] == "new-refresh"
    assert refreshed["token_type"] == "Bearer"
    assert refreshed["account_email"] == "new@example.com"
    assert refreshed["account_id"] == "acct-new"
    assert refreshed["plan_type"] == "plus"
    assert saved["access_token"] == "new-access"
    assert saved["refresh_token"] == "new-refresh"
    assert saved["account_email"] == "new@example.com"
    assert saved["account_id"] == "acct-new"
    assert saved["plan_type"] == "plus"
    assert isinstance(saved.get("obtained_at"), str)
    assert isinstance(saved.get("expires_at"), str)


def test_refresh_chatgpt_credentials_without_refresh_token_raises_permanent_error(
    tmp_path: Path,
) -> None:
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    credentials_path.parent.mkdir(parents=True, exist_ok=True)
    credentials_path.write_text(json.dumps({"access_token": "old-access"}), encoding="utf-8")

    with pytest.raises(ChatGPTRefreshPermanentError, match="cannot be refreshed"):
        refresh_chatgpt_credentials(credentials_path, timeout=5.0)


def test_refresh_chatgpt_credentials_maps_revoked_token_to_sign_in_again(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    _write_credentials(credentials_path)

    def _fake_urlopen(
        request: object,
        timeout: float,
        context: object,
    ) -> _StubHTTPResponse:
        assert context is not None
        _ = (request, timeout)
        raise HTTPError(
            "https://auth.openai.com/oauth/token",
            401,
            "Unauthorized",
            hdrs=None,
            fp=io.BytesIO(json.dumps({"error": {"code": "refresh_token_invalidated"}}).encode("utf-8")),
        )

    monkeypatch.setattr(credentials_module, "urlopen", _fake_urlopen)

    with pytest.raises(ChatGPTRefreshPermanentError, match="Please sign in again"):
        refresh_chatgpt_credentials(credentials_path, timeout=5.0)


def test_refresh_chatgpt_credentials_surfaces_transient_network_failures(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    credentials_path = tmp_path / "auth" / "chatgpt-auth.json"
    _write_credentials(credentials_path)

    def _fake_urlopen(
        request: object,
        timeout: float,
        context: object,
    ) -> _StubHTTPResponse:
        assert context is not None
        _ = (request, timeout)
        raise URLError("network down")

    monkeypatch.setattr(credentials_module, "urlopen", _fake_urlopen)

    with pytest.raises(ChatGPTRefreshTransientError, match="network down"):
        refresh_chatgpt_credentials(credentials_path, timeout=5.0)