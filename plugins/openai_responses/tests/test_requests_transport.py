from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
from typing import Any

from openai_responses_plugins.requests_transport import RequestsOpenAIClient


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
        self.closed = False

    def request(self, method: str, url: str, **kwargs: Any) -> _Response:
        self.requests.append({"method": method, "url": url, **kwargs})
        return self.responses.pop(0)

    def close(self) -> None:
        self.closed = True


def test_requests_transport_models_and_response_payloads() -> None:
    session = _Session(
        [
            _Response({"data": [{"id": "gpt-test"}]}),
            _Response({"id": "resp_1", "output": []}),
        ]
    )
    client = RequestsOpenAIClient(
        api_key="secret",
        base_url="https://api.test/v1",
        timeout=30,
        session=session,
    )

    assert client.models.list().data == [{"id": "gpt-test"}]
    assert client.responses.create(
        model="gpt-test",
        input=[],
        stream=False,
    ) == {"id": "resp_1", "output": []}
    assert session.requests[0]["url"] == "https://api.test/v1/models"
    assert session.requests[1]["url"] == "https://api.test/v1/responses"
    assert session.requests[1]["headers"]["Authorization"] == "Bearer secret"
    assert session.requests[1]["json"]["model"] == "gpt-test"
    assert session.requests[1]["verify"] is True


def test_requests_transport_uses_configured_ca_bundle() -> None:
    session = _Session([_Response({"data": []})])
    client = RequestsOpenAIClient(
        api_key="secret",
        base_url="https://reviewer.test/v1",
        timeout=30,
        verify="/runtime/reviewer-ca.pem",
        session=session,
    )

    assert client.models.list().data == []
    assert session.requests[0]["verify"] == "/runtime/reviewer-ca.pem"


def test_requests_transport_stream_parses_sse_events() -> None:
    response = _Response(
        {},
        lines=[
            "event: response.output_text.delta",
            'data: {"delta":"hello"}',
            "",
            "event: response.completed",
            'data: {"response":{"output":[]}}',
            "",
        ],
    )
    client = RequestsOpenAIClient(
        api_key="secret",
        base_url="https://api.test/v1",
        timeout=30,
        session=_Session([response]),
    )

    stream = client.responses.create(
        model="gpt-test",
        input=[],
        stream=True,
    )
    assert list(stream) == [
        {"type": "response.output_text.delta", "delta": "hello"},
        {"type": "response.completed", "response": {"output": []}},
    ]


def test_provider_requests_transport_imports_without_openai_sdk() -> None:
    repo_root = Path(__file__).resolve().parents[3]
    script = """
import builtins
real_import = builtins.__import__
def blocked(name, *args, **kwargs):
    if name == "openai" or name.startswith("openai."):
        raise ImportError("blocked for transport test")
    return real_import(name, *args, **kwargs)
builtins.__import__ = blocked
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider
provider = OpenAIResponsesProvider()
state = provider.init({
    "provider_transport": "requests",
    "api_key": "test-key",
    "base_url": "https://api.test/v1",
    "model": "gpt-test",
})
assert state["client"].__class__.__name__ == "RequestsOpenAIClient"
state["client"].close()
"""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [
            str(repo_root / "core/python"),
            str(repo_root / "plugins/openai_responses/src"),
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