from __future__ import annotations

"""Unit tests for the bridge client's local HTTP proxying.

These tests exercise :meth:`BridgeClient.execute_local_request` in
isolation by mocking :mod:`httpx` so no real network calls are made.
"""

import asyncio
import types
from typing import Any, Dict, Optional

from agent_terminal_app import bridge_client as bridge_mod


class _DummyResponse:
    def __init__(self) -> None:
        self.status_code = 200
        self.headers: Dict[str, str] = {"X-Test": "1"}
        self.text = "ok"


class _DummyAsyncClient:
    last_request: Optional[tuple[Any, ...]] = None

    def __init__(self, *args: Any, **kwargs: Any) -> None:  # pragma: no cover - trivial
        self.args = args
        self.kwargs = kwargs

    async def __aenter__(self) -> "_DummyAsyncClient":  # pragma: no cover - trivial
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - trivial
        return None

    async def request(self, method: str, url: str, headers=None, content=None) -> _DummyResponse:
        _DummyAsyncClient.last_request = (method, url, headers, content)
        return _DummyResponse()


def test_execute_local_request_builds_url_and_invokes_httpx(monkeypatch) -> None:
    """BridgeClient should compose URL from base + path and call httpx."""

    # Patch the module-level httpx reference used by BridgeClient.
    monkeypatch.setattr(
        bridge_mod,
        "httpx",
        types.SimpleNamespace(AsyncClient=_DummyAsyncClient),
    )

    cfg = bridge_mod.BridgeConfig(
        bridge_url="ws://example.test/ws/websocket",
        server_id="server-1",
        display_name="Test Server",
        computer_name="test-host",
        location=None,
        local_http_base="http://127.0.0.1:9000/",  # trailing slash should be handled
    )

    client = bridge_mod.BridgeClient(cfg, test_mode=True)

    async def _run() -> Dict[str, Any]:
        return await client.execute_local_request("GET", "/api/data", None)

    result = asyncio.run(_run())

    # Response comes from our dummy client.
    assert result["status"] == 200
    assert result["body"] == "ok"
    assert result["headers"]["X-Test"] == "1"

    # Verify that the composed URL and method match expectations.
    assert _DummyAsyncClient.last_request is not None
    method, url, headers, content = _DummyAsyncClient.last_request
    assert method == "GET"
    assert url == "http://127.0.0.1:9000/api/data"
    assert headers == {}  # No body -> no Content-Type header
    assert content is None
