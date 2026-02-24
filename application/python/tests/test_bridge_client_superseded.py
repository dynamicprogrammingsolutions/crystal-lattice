from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path

import pytest

from agent_terminal_app import bridge_client as bridge_mod


class _DummyWs:
    def __init__(self, messages: list[dict]) -> None:
        self._messages = [json.dumps(m) for m in messages]
        self.closed = False

    def __aiter__(self) -> "_DummyWs":
        return self

    async def __anext__(self) -> str:
        if not self._messages:
            raise StopAsyncIteration
        return self._messages.pop(0)

    async def close(self) -> None:
        self.closed = True


def _make_client(**overrides) -> bridge_mod.BridgeClient:
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


def test_bridge_client_superseded_stops_message_loop() -> None:
    client = _make_client()
    dummy_ws = _DummyWs(
        [
            {
                "event": "superseded",
                "payload": {"server_id": "server-1", "reason": "new_connection"},
            }
        ]
    )
    client._ws = dummy_ws  # type: ignore[assignment]

    asyncio.run(client._handle_messages())

    assert client._stopped is True
    assert dummy_ws.closed is True


def test_bridge_local_guard_blocks_second_instance(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    client = _make_client(local_guard=True)
    lock_path = tmp_path / ".crystal" / "bridge_locks" / "server-1.lock"
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    lock_path.write_text(json.dumps({"pid": os.getpid()}) + "\n", encoding="utf-8")

    with pytest.raises(RuntimeError, match=r"already running"):
        asyncio.run(client._acquire_local_lock())
