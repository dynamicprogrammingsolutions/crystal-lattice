"""Streaming tests for the application layer wrapper."""

from __future__ import annotations

import time
from pathlib import Path

from agent_app import AgentApplication
from agent_core import AgentCore


def _make_config(tmp_path: Path) -> Path:
    cfg = {
        "providers": {
            "dummy": {"provider": "dummy_provider", "model": "test-model"}
        },
        "plugins": {
            "providers": ["tests.dummy_provider.DummyProvider"],
        },
        "agents": {
            "default": {"provider": "dummy"},
        },
    }
    path = tmp_path / "config.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


def _poll_events(app: AgentApplication, request_id: str, timeout: float = 5.0):
    """Poll events until request_completed or timeout."""

    since_id = None
    start = time.time()
    final_events = []
    while time.time() - start < timeout:
        batch = app.get_events(
            {
                "since_id": since_id,
                "request_id": request_id,
            }
        )["events"]
        if not batch:
            time.sleep(0.01)
            continue
        since_id = batch[-1]["event_id"]
        final_events.extend(batch)
        if any(ev["type"] == "request_completed" for ev in batch):
            break
    return final_events


def test_send_request_streaming_emits_events(tmp_path):
    config_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    created = app.create_session({"agent_id": "default"})
    session_id = created["session"]["session_id"]
    app.add_message(
        {"session_id": session_id, "message": {"role": "user", "content": "Hello"}}
    )

    started = app.send_request({"session_id": session_id, "stream": True})
    request_id = started["request_id"]

    events = _poll_events(app, request_id)

    assert any(ev["type"] == "partial" for ev in events)
    assert any(ev["type"] == "final" for ev in events)
    assert any(ev["type"] == "request_completed" for ev in events)
