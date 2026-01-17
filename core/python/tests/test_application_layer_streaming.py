"""Streaming tests for the future application layer wrapper.

These tests exercise :mod:`agent_app.application_future` using the
``send_request`` streaming event iterator instead of the original
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
        "plugins": ["tests.dummy_provider.DummyProvider"],
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

    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "Hello")

    events = list(app.send_request(core, session, base_config, overrides=None, stream=True))

    assert any(ev["type"] == "partial" for ev in events)
    assert any(ev["type"] == "final" for ev in events)
    assert any(ev["type"] == "request_completed" for ev in events)


def _make_slow_config(tmp_path: Path, *, sleep_per_char: float = 0.05) -> Path:
    cfg = {
        "providers": {
            "dummy": {
                "provider": "dummy_provider",
                "model": "test-model",
                "sleep_per_char": sleep_per_char,
            }
        },
        "plugins": ["tests.dummy_provider.DummyProvider"],
        "agents": {
            "default": {"provider": "dummy"},
        },
    }
    path = tmp_path / "config_slow.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


def _make_failing_config(tmp_path: Path) -> Path:
    cfg = {
        "providers": {
            "dummy": {"provider": "failing_dummy_provider", "model": "test-model"}
        },
        "plugins": ["tests.dummy_provider.FailingOnceDummyProvider"],
        "agents": {
            "default": {"provider": "dummy"},
        },
    }
    path = tmp_path / "config_failing.json"
    path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    return path


def test_cancel_request_and_resume(tmp_path: Path) -> None:
    import threading
    import time

    from tests.dummy_provider import reset_failing_dummy_provider_state  # noqa: F401

    config_path = _make_slow_config(tmp_path, sleep_per_char=0.05)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "Hello slow world")

    events: list[dict] = []

    def _consume() -> None:
        for ev in app.send_request(core, session, base_config, overrides=None, stream=True):
            events.append(ev)

    t = threading.Thread(target=_consume)
    t.start()

    # Wait briefly for request_started and some partials.
    time.sleep(0.1)

    request_id = None
    for ev in events:
        if ev.get("type") == "request_started":
            request_id = ev.get("request_id")
            break

    assert isinstance(request_id, str) and request_id

    app.cancel_request(request_id)

    t.join(timeout=5)
    assert not t.is_alive()

    kinds = {ev.get("type") for ev in events}
    assert "request_cancelled" in kinds
    assert "request_completed" in kinds

    # A fresh request after cancellation should still complete normally.
    events2 = list(app.send_request(core, session, base_config, overrides=None, stream=True))
    kinds2 = {ev.get("type") for ev in events2}
    assert "final" in kinds2
    assert "request_completed" in kinds2
    assert "request_cancelled" not in kinds2


def test_failure_then_resume(tmp_path: Path) -> None:
    from tests.dummy_provider import reset_failing_dummy_provider_state

    reset_failing_dummy_provider_state()

    config_path = _make_failing_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "Hi failing provider")

    events1 = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    kinds1 = {ev.get("type") for ev in events1}
    assert "error" in kinds1
    assert "request_completed" in kinds1

    # Second request should succeed now that the provider has failed once.
    events2 = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    kinds2 = {ev.get("type") for ev in events2}
    assert "final" in kinds2
    assert "request_completed" in kinds2
