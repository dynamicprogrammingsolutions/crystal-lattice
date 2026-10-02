from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from anthropic_plugins.requests_transport import RequestsAnthropicClient


class _Response:
    def __init__(
        self,
        payload: dict[str, Any],
        *,
        status_code: int = 200,
        lines: list[str] | None = None,
    ) -> None:
        self._payload = payload
        self.status_code = status_code
        self.headers = {"Content-Type": "application/json"}
        self.text = str(payload)
        self._lines = lines or []
        self.closed = False

    def json(self) -> dict[str, Any]:
        return self._payload

    def iter_lines(self, *, decode_unicode: bool):
        _ = decode_unicode
        yield from self._lines

    def close(self) -> None:
        self.closed = True


class _Session:
    def __init__(self, responses: list[_Response]) -> None:
        self.responses = list(responses)
        self.requests: list[dict[str, Any]] = []

    def request(self, method: str, url: str, **kwargs: Any) -> _Response:
        self.requests.append({"method": method, "url": url, **kwargs})
        return self.responses.pop(0)

    def close(self) -> None:
        return None


def test_requests_transport_models_and_message_payloads() -> None:
    session = _Session(
        [
            _Response({"data": [{"id": "claude-test"}]}),
            _Response(
                {
                    "id": "msg_1",
                    "content": [{"type": "text", "text": "hello"}],
                    "usage": {},
                }
            ),
        ]
    )
    client = RequestsAnthropicClient(
        api_key="secret",
        base_url="https://api.test",
        timeout=30,
        default_headers={"anthropic-version": "2023-06-01"},
        session=session,
    )

    assert client.models.list(limit=25) == [{"id": "claude-test"}]
    response = client.messages.create(
        model="claude-test",
        max_tokens=100,
        messages=[{"role": "user", "content": "hello"}],
        stream=False,
    )
    assert response["id"] == "msg_1"
    assert session.requests[0]["url"] == "https://api.test/v1/models"
    assert session.requests[0]["params"] == {"limit": 25}
    assert session.requests[1]["url"] == "https://api.test/v1/messages"
    assert session.requests[1]["headers"]["x-api-key"] == "secret"


def test_requests_transport_stream_parses_anthropic_sse() -> None:
    response = _Response(
        {},
        lines=[
            "event: message_start",
            'data: {"message":{"content":[]}}',
            "",
            "event: message_stop",
            "data: {}",
            "",
        ],
    )
    client = RequestsAnthropicClient(
        api_key="secret",
        base_url="https://api.test",
        timeout=30,
        session=_Session([response]),
    )

    stream = client.messages.create(
        model="claude-test",
        max_tokens=100,
        messages=[],
        stream=True,
    )
    assert list(stream) == [
        {"type": "message_start", "message": {"content": []}},
        {"type": "message_stop"},
    ]


def test_provider_requests_transport_imports_without_anthropic_sdk() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    script = """
import builtins
real_import = builtins.__import__
def blocked(name, *args, **kwargs):
    if name == "anthropic" or name.startswith("anthropic."):
        raise ImportError("blocked for transport test")
    return real_import(name, *args, **kwargs)
builtins.__import__ = blocked
from anthropic_plugins.provider import AnthropicProvider
provider = AnthropicProvider()
client = provider._client({
    "provider_transport": "requests",
    "api_key": "test-key",
    "base_url": "https://api.test",
})
assert client.__class__.__name__ == "RequestsAnthropicClient"
client.close()
"""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(repo_root / "core/python"),
            str(repo_root / "plugins/anthropic-compatible/src"),
        ]
    )
    completed = subprocess.run(
        [sys.executable, "-c", script],
        check=False,
        capture_output=True,
        text=True,
        env=env,
    )
    assert completed.returncode == 0, completed.stderr