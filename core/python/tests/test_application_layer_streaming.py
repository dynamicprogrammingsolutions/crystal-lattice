"""Streaming tests for the future application layer wrapper.

These tests exercise :mod:`agent_app.application_future` using the
``send_request_v2`` streaming event iterator instead of the original
background-thread + event-store architecture.
"""

from __future__ import annotations

import time
from pathlib import Path

from agent_app.application_future import AgentApplication
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


def test_send_request_streaming_emits_events(tmp_path: Path) -> None:
    config_path = _make_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_agent_session("default")
    session = core.add_message(session, "user", "Hello")

    events = list(app.send_request_v2(core, session, base_config, overrides=None, stream=True))

    assert any(ev["type"] == "partial" for ev in events)
    assert any(ev["type"] == "final" for ev in events)
    assert any(ev["type"] == "request_completed" for ev in events)
