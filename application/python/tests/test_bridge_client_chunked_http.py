from __future__ import annotations

import asyncio
import json
from typing import Any, Dict, List, Optional

from agent_terminal_app import bridge_client as bridge_mod


class _DummyWs:
    def __init__(self) -> None:
        self.sent: List[Dict[str, Any]] = []

    async def send(self, data: str) -> None:
        self.sent.append(json.loads(data))


def _make_client(**overrides: Any) -> bridge_mod.BridgeClient:
    cfg = bridge_mod.BridgeConfig(
        bridge_url="ws://example.test/ws/websocket",
        server_id="server-1",
        display_name="Test Server",
        computer_name="test-host",
        location=None,
        local_http_base="http://127.0.0.1:9000",
        **overrides,
    )
    return bridge_mod.BridgeClient(cfg, test_mode=True)


def test_chunked_request_reassembles_body_and_sends_legacy_response(monkeypatch) -> None:
    client = _make_client(response_chunking_threshold_bytes=1024 * 1024)
    dummy_ws = _DummyWs()
    client._ws = dummy_ws  # type: ignore[assignment]

    captured: Dict[str, Any] = {}

    async def _fake_execute(method: str, path: str, body: Optional[str], *, headers=None) -> Dict[str, Any]:
        captured.update({"method": method, "path": path, "body": body, "headers": headers})
        return {
            "status": 200,
            "headers": {"content-type": "application/json"},
            "body": json.dumps({"ok": True}),
        }

    monkeypatch.setattr(client, "execute_local_request", _fake_execute)

    async def _run() -> None:
        await client._handle_http_request_init(
            {
                "request_id": "req-1",
                "method": "PUT",
                "path": "/api/data",
                "headers": {"content-type": "application/json"},
            }
        )
        await client._handle_http_request_chunk({"request_id": "req-1", "seq": 0, "chunk": "{\"a\":"})
        await client._handle_http_request_chunk({"request_id": "req-1", "seq": 1, "chunk": "1}"})
        await client._handle_http_request_end({"request_id": "req-1", "final_seq": 1})

    asyncio.run(_run())

    assert captured["method"] == "PUT"
    assert captured["path"] == "/api/data"
    assert captured["body"] == '{"a":1}'

    assert len(dummy_ws.sent) == 1
    assert dummy_ws.sent[0]["event"] == "http_response"
    assert dummy_ws.sent[0]["payload"]["request_id"] == "req-1"


def test_large_response_is_sent_as_chunks(monkeypatch) -> None:
    client = _make_client(response_chunking_threshold_bytes=100)
    dummy_ws = _DummyWs()
    client._ws = dummy_ws  # type: ignore[assignment]

    big_body = "x" * 500

    async def _fake_execute(method: str, path: str, body: Optional[str], *, headers=None) -> Dict[str, Any]:
        return {
            "status": 200,
            "headers": {"content-type": "text/plain"},
            "body": big_body,
        }

    monkeypatch.setattr(client, "execute_local_request", _fake_execute)

    async def _run() -> None:
        await client._handle_http_request(
            {
                "request_id": "req-2",
                "method": "GET",
                "path": "/api/data",
                "headers": {},
                "body": None,
            }
        )

    asyncio.run(_run())

    events = [m["event"] for m in dummy_ws.sent]
    assert events[0] == "http_response_init"
    assert "http_response_chunk" in events
    assert events[-1] == "http_response_end"
