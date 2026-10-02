from __future__ import annotations

import asyncio
import json
from typing import Any, AsyncIterator, Dict, Optional

import pytest

from agent_terminal_app import bridge_client as bridge_mod


class _DummyWs:
    def __init__(self) -> None:
        self.sent: list[Dict[str, Any]] = []
        self.closed = False

    async def send(self, data: str) -> None:
        self.sent.append(json.loads(data))

    async def close(self) -> None:
        self.closed = True


class _FakeResponse:
    def __init__(
        self,
        *,
        status_code: int = 200,
        headers: Optional[Dict[str, str]] = None,
        chunks: Optional[list[bytes]] = None,
    ) -> None:
        self.status_code = status_code
        self.headers = headers or {}
        self._chunks = chunks or []

    async def aiter_raw(self) -> AsyncIterator[bytes]:
        for chunk in self._chunks:
            yield chunk

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")


async def _consume_content(content: Any) -> bytes:
    if content is None:
        return b""
    if isinstance(content, bytes):
        return content
    chunks: list[bytes] = []
    async for chunk in content:
        chunks.append(chunk)
    return b"".join(chunks)


class _ResponseContext:
    def __init__(
        self,
        response: _FakeResponse,
        *,
        content: Any = None,
        consumed: Optional[list[bytes]] = None,
    ) -> None:
        self.response = response
        self.content = content
        self.consumed = consumed

    async def __aenter__(self) -> _FakeResponse:
        if self.consumed is not None:
            self.consumed.append(await _consume_content(self.content))
        return self.response

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class _FakeBridgeHttpClient:
    def __init__(
        self,
        *,
        request_chunks: Optional[list[bytes]] = None,
    ) -> None:
        self.request_chunks = request_chunks or []
        self.uploaded: list[bytes] = []
        self.download_headers: Optional[Dict[str, str]] = None
        self.upload_headers: Optional[Dict[str, str]] = None

    async def __aenter__(self) -> "_FakeBridgeHttpClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    def stream(self, method: str, url: str, headers=None) -> _ResponseContext:
        assert method == "GET"
        assert url.endswith("/bridge/v1/transfers/request-1/request-body")
        self.download_headers = headers
        return _ResponseContext(_FakeResponse(chunks=self.request_chunks))

    async def put(self, url: str, headers=None, content=None) -> _FakeResponse:
        assert url.endswith("/bridge/v1/transfers/request-1/response-body")
        self.upload_headers = headers
        self.uploaded.append(await _consume_content(content))
        return _FakeResponse(status_code=204)


class _FakeLocalHttpClient:
    def __init__(self, response_chunks: list[bytes]) -> None:
        self.response_chunks = response_chunks
        self.request_bodies: list[bytes] = []
        self.request_headers: Optional[Dict[str, str]] = None
        self.request_url: Optional[str] = None

    async def __aenter__(self) -> "_FakeLocalHttpClient":
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None

    def stream(
        self,
        method: str,
        url: str,
        *,
        headers=None,
        content=None,
    ) -> _ResponseContext:
        assert method == "POST"
        self.request_url = url
        self.request_headers = headers
        return _ResponseContext(
            _FakeResponse(
                status_code=201,
                headers={
                    "content-type": "application/octet-stream",
                    "content-length": "999",
                    "content-encoding": "gzip",
                },
                chunks=self.response_chunks,
            ),
            content=content,
            consumed=self.request_bodies,
        )


class _BlockingResponse(_FakeResponse):
    def __init__(self, entered: asyncio.Event) -> None:
        super().__init__()
        self.entered = entered

    async def aiter_raw(self) -> AsyncIterator[bytes]:
        self.entered.set()
        await asyncio.Future()
        if False:  # pragma: no cover - keeps this an async iterator
            yield b""


class _BlockingResponseContext:
    def __init__(self, entered: asyncio.Event) -> None:
        self.entered = entered

    async def __aenter__(self) -> _FakeResponse:
        self.entered.set()
        await asyncio.Future()
        raise AssertionError("unreachable")

    async def __aexit__(self, exc_type, exc, tb) -> None:
        return None


class _PhaseBridgeHttpClient(_FakeBridgeHttpClient):
    def __init__(self, phase: str, entered: asyncio.Event) -> None:
        super().__init__()
        self.phase = phase
        self.entered = entered

    def stream(self, method: str, url: str, headers=None) -> _ResponseContext:
        if self.phase == "request_download":
            assert method == "GET"
            return _ResponseContext(_BlockingResponse(self.entered))
        return super().stream(method, url, headers=headers)

    async def put(self, url: str, headers=None, content=None) -> _FakeResponse:
        if self.phase == "response_upload":
            self.entered.set()
            await asyncio.Future()
        return await super().put(url, headers=headers, content=content)


class _PhaseLocalHttpClient(_FakeLocalHttpClient):
    def __init__(self, phase: str, entered: asyncio.Event) -> None:
        super().__init__([b"response"])
        self.phase = phase
        self.entered = entered

    def stream(
        self,
        method: str,
        url: str,
        *,
        headers=None,
        content=None,
    ) -> _ResponseContext | _BlockingResponseContext:
        if self.phase == "local_stream":
            return _BlockingResponseContext(self.entered)
        return super().stream(
            method,
            url,
            headers=headers,
            content=content,
        )


def _make_client(**overrides: Any) -> bridge_mod.BridgeClient:
    config = bridge_mod.BridgeConfig(
        bridge_url="wss://bridge.example/ws/websocket",
        bridge_http_base=None,
        server_id="server-1",
        display_name="Test Server",
        computer_name="test-host",
        location=None,
        local_http_base="http://127.0.0.1:9000",
        **overrides,
    )
    return bridge_mod.BridgeClient(config, test_mode=True)


def test_bridge_http_base_is_derived_without_the_websocket_path() -> None:
    assert (
        bridge_mod._derive_bridge_http_base(
            "wss://bridge.example/prefix/ws/websocket?type=server"
        )
        == "https://bridge.example/prefix"
    )
    assert (
        bridge_mod._derive_bridge_http_base("ws://127.0.0.1:4000/ws")
        == "http://127.0.0.1:4000"
    )


def test_v2_request_streams_raw_request_and_response_bytes(monkeypatch) -> None:
    bridge_http = _FakeBridgeHttpClient(request_chunks=[b"\x00\xff", b"request"])
    local_http = _FakeLocalHttpClient(response_chunks=[b"\xff\x00", b"response"])
    clients = iter([bridge_http, local_http])
    monkeypatch.setattr(bridge_mod.httpx, "AsyncClient", lambda *a, **k: next(clients))

    client = _make_client()
    websocket = _DummyWs()
    client._ws = websocket  # type: ignore[assignment]

    async def _run() -> None:
        await client._handle_http_request_v2(
            {
                "request_id": "request-1",
                "method": "POST",
                "path": "/requests/request-1/soft-cancel",
                "headers": {
                    "content-type": "application/octet-stream",
                    "accept-encoding": "br",
                    "authorization": "Bearer backend-token",
                },
                "request_body_present": True,
                "request_body_path": "/bridge/v1/transfers/request-1/request-body",
                "request_body_token": "request-token",
                "response_body_path": "/bridge/v1/transfers/request-1/response-body",
                "response_body_token": "response-token",
            }
        )

    asyncio.run(_run())

    assert local_http.request_bodies == [b"\x00\xffrequest"]
    assert (
        local_http.request_url
        == "http://127.0.0.1:9000/requests/request-1/soft-cancel"
    )
    assert local_http.request_headers is not None
    assert local_http.request_headers["Accept-Encoding"] == "identity"
    assert local_http.request_headers["authorization"] == "Bearer backend-token"
    assert bridge_http.download_headers == {"Authorization": "Bearer request-token"}
    assert bridge_http.upload_headers == {"Authorization": "Bearer response-token"}
    assert bridge_http.uploaded == [b"\xff\x00response"]

    assert len(websocket.sent) == 1
    message = websocket.sent[0]
    assert message["event"] == "http_response_v2_init"
    assert message["payload"]["request_id"] == "request-1"
    assert message["payload"]["status"] == 201
    assert message["payload"]["headers"] == {"content-type": "application/octet-stream"}
    assert "body" not in message["payload"]
    assert "chunk" not in message["payload"]


def test_v2_cancel_cancels_the_matching_task() -> None:
    client = _make_client()

    async def _run() -> None:
        task = asyncio.create_task(asyncio.sleep(60))
        client._inflight_v2_tasks["request-1"] = task
        client._inflight_http_tasks.add(task)
        client._handle_http_request_v2_cancel({"request_id": "request-1"})
        try:
            await task
        except asyncio.CancelledError:
            pass
        assert task.cancelled()

    asyncio.run(_run())


@pytest.mark.parametrize(
    ("phase", "trigger"),
    [
        ("request_download", "cancel"),
        ("local_stream", "bridge_close"),
        ("response_upload", "stop"),
        ("response_upload", "superseded"),
    ],
)
def test_v2_phase_cancellation_cleans_task_registries(
    monkeypatch,
    phase: str,
    trigger: str,
) -> None:
    async def _run() -> None:
        entered = asyncio.Event()
        bridge_http = _PhaseBridgeHttpClient(phase, entered)
        local_http = _PhaseLocalHttpClient(phase, entered)
        clients = iter([bridge_http, local_http])
        monkeypatch.setattr(
            bridge_mod.httpx,
            "AsyncClient",
            lambda *args, **kwargs: next(clients),
        )

        client = _make_client()
        websocket = _DummyWs()
        client._ws = websocket  # type: ignore[assignment]
        payload = {
            "request_id": "request-1",
            "method": "POST",
            "path": "/phase-cancellation",
            "headers": {"content-type": "application/octet-stream"},
            "request_body_present": phase == "request_download",
            "request_body_path": "/bridge/v1/transfers/request-1/request-body",
            "request_body_token": "request-token",
            "response_body_path": "/bridge/v1/transfers/request-1/response-body",
            "response_body_token": "response-token",
        }

        client._track_v2_http_task(payload)
        await asyncio.wait_for(entered.wait(), timeout=1)
        task = client._inflight_v2_tasks["request-1"]

        if trigger == "cancel":
            client._handle_http_request_v2_cancel({"request_id": "request-1"})
            await asyncio.gather(task, return_exceptions=True)
        elif trigger == "bridge_close":
            await client._close_ws()
        elif trigger == "stop":
            await client.stop()
        elif trigger == "superseded":
            await client._handle_superseded({"reason": "new_connection"})
        else:  # pragma: no cover - parameter guard
            raise AssertionError(f"Unexpected trigger {trigger}")

        await asyncio.sleep(0)

        assert task.cancelled()
        assert "request-1" not in client._inflight_v2_tasks
        assert task not in client._inflight_http_tasks
        if trigger in {"bridge_close", "stop", "superseded"}:
            assert websocket.closed is True

    asyncio.run(_run())
