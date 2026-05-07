"""Streaming tests for the future application layer wrapper.

These tests exercise :mod:`agent_app.application_future` using the
``send_request`` streaming event iterator instead of the original
background-thread + event-store architecture.
"""

from __future__ import annotations

import time
import json
import threading
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
    app.save_session(session)

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


def _make_blocking_tool_config(tmp_path: Path) -> Path:
    cfg = {
        "providers": {
            "dummy": {"provider": "dummy_provider", "model": "test-model"}
        },
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.dummy_tool.CancellableBlockingTool",
        ],
        "agents": {
            "default": {"provider": "dummy"},
        },
    }
    path = tmp_path / "config_blocking_tool.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _make_blocking_provider_config(
    tmp_path: Path,
    *,
    emit_partial_before_cancel: bool = False,
) -> Path:
    cfg = {
        "providers": {
            "dummy": {
                "provider": "cancellable_blocking_provider",
                "model": "test-model",
                "emit_partial_before_cancel": emit_partial_before_cancel,
            }
        },
        "plugins": ["tests.dummy_provider.CancellableBlockingProvider"],
        "agents": {
            "default": {"provider": "dummy"},
        },
    }
    path = tmp_path / (
        "config_blocking_provider_partial.json"
        if emit_partial_before_cancel
        else "config_blocking_provider.json"
    )
    path.write_text(json.dumps(cfg), encoding="utf-8")
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
    app.save_session(session)

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
    app.save_session(session)

    events1 = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    kinds1 = {ev.get("type") for ev in events1}
    assert "error" in kinds1
    assert "request_completed" in kinds1

    # Second request should succeed now that the provider has failed once.
    events2 = list(app.send_request(core, session, base_config, overrides=None, stream=False))
    kinds2 = {ev.get("type") for ev in events2}
    assert "final" in kinds2
    assert "request_completed" in kinds2


def test_cancel_request_interrupts_silent_running_tool(tmp_path: Path) -> None:
    config_path = _make_blocking_tool_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")
    tool_call = {
        "id": "call_block",
        "type": "function",
        "function": {"name": "block_until_cancel", "arguments": json.dumps({})},
    }
    session = core.add_message(session, "assistant", "", {"tool_calls": [tool_call]})
    app.save_session(session)

    events: list[dict] = []
    request_id = "req_tool_cancel_silent"

    def _consume() -> None:
        for ev in app.send_request(
            core,
            session,
            base_config,
            overrides=None,
            stream=True,
            request_id=request_id,
        ):
            events.append(ev)

    worker = threading.Thread(target=_consume)
    worker.start()

    time.sleep(0.2)
    app.cancel_request(request_id)
    app.cancel_request(request_id)

    worker.join(timeout=5)
    assert not worker.is_alive()

    kinds = [ev.get("type") for ev in events]
    assert "request_cancelled" in kinds
    assert "request_completed" in kinds
    assert "tool_results" in kinds

    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    assert checkpoints
    final_session = checkpoints[-1]["session"]
    tool_messages = [m for m in final_session.messages if getattr(m, "role", None) == "tool"]
    assert tool_messages
    assert "Cancelled" in str(tool_messages[-1].content)

    _core2, _base2, session2 = app.create_session("default")
    session2 = core.add_message(session2, "user", "Hello after cancel")
    app.save_session(session2)
    events2 = list(
        app.send_request(
            core,
            session2,
            base_config,
            overrides=None,
            stream=True,
            request_id="req_tool_cancel_followup",
        )
    )
    kinds2 = {ev.get("type") for ev in events2}
    assert "final" in kinds2
    assert "request_completed" in kinds2
    assert "request_cancelled" not in kinds2


def test_cancel_request_interrupts_tool_after_partial_output(tmp_path: Path) -> None:
    config_path = _make_blocking_tool_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")
    tool_call = {
        "id": "call_block_partial",
        "type": "function",
        "function": {
            "name": "block_until_cancel",
            "arguments": json.dumps({"emit_partial": True}),
        },
    }
    session = core.add_message(session, "assistant", "", {"tool_calls": [tool_call]})
    app.save_session(session)

    events: list[dict] = []
    request_id = "req_tool_cancel_partial"

    def _consume() -> None:
        for ev in app.send_request(
            core,
            session,
            base_config,
            overrides=None,
            stream=True,
            request_id=request_id,
        ):
            events.append(ev)

    worker = threading.Thread(target=_consume)
    worker.start()

    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if any(ev.get("type") == "tool_partial" for ev in events):
            break
        time.sleep(0.05)
    else:
        raise AssertionError("tool_partial was not emitted before cancellation")

    app.cancel_request(request_id)

    worker.join(timeout=5)
    assert not worker.is_alive()

    kinds = [ev.get("type") for ev in events]
    assert "tool_partial" in kinds
    assert "request_cancelled" in kinds
    assert "request_completed" in kinds


def test_cancel_request_interrupts_silent_running_provider(tmp_path: Path) -> None:
    from tests.dummy_provider import (
        get_cancellable_blocking_provider_state,
        reset_cancellable_blocking_provider_state,
    )

    reset_cancellable_blocking_provider_state()
    config_path = _make_blocking_provider_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "Cancel provider call")
    app.save_session(session)

    request_id = "req_provider_cancel_silent"
    events: list[dict] = []

    def _consume() -> None:
        for ev in app.send_request(
            core,
            session,
            base_config,
            overrides=None,
            stream=True,
            request_id=request_id,
        ):
            events.append(ev)

    worker = threading.Thread(target=_consume)
    worker.start()

    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if any(ev.get("type") == "request_started" for ev in events):
            break
        time.sleep(0.05)
    else:
        raise AssertionError("request_started was not emitted before cancellation")

    app.cancel_request(request_id)

    worker.join(timeout=5)
    assert not worker.is_alive()

    kinds = [ev.get("type") for ev in events]
    assert "request_cancelled" in kinds
    assert "request_completed" in kinds
    assert "final" not in kinds

    provider_state = get_cancellable_blocking_provider_state()
    assert request_id in provider_state["stream_request_ids"]
    assert request_id in provider_state["cancel_request_ids"]
    assert request_id not in provider_state["active"]


def test_cancel_request_interrupts_provider_after_partial_output(tmp_path: Path) -> None:
    from tests.dummy_provider import (
        get_cancellable_blocking_provider_state,
        reset_cancellable_blocking_provider_state,
    )

    reset_cancellable_blocking_provider_state()
    config_path = _make_blocking_provider_config(
        tmp_path,
        emit_partial_before_cancel=True,
    )
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "Cancel provider stream after partial")
    app.save_session(session)

    request_id = "req_provider_cancel_partial"
    events: list[dict] = []

    def _consume() -> None:
        for ev in app.send_request(
            core,
            session,
            base_config,
            overrides=None,
            stream=True,
            request_id=request_id,
        ):
            events.append(ev)

    worker = threading.Thread(target=_consume)
    worker.start()

    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if any(ev.get("type") == "partial" for ev in events):
            break
        time.sleep(0.05)
    else:
        raise AssertionError("provider partial was not emitted before cancellation")

    app.cancel_request(request_id)

    worker.join(timeout=5)
    assert not worker.is_alive()

    kinds = [ev.get("type") for ev in events]
    assert "partial" in kinds
    assert "request_cancelled" in kinds
    assert "request_completed" in kinds
    assert "final" not in kinds

    provider_state = get_cancellable_blocking_provider_state()
    assert request_id in provider_state["stream_request_ids"]
    assert request_id in provider_state["cancel_request_ids"]
    assert request_id not in provider_state["active"]


def test_cancel_request_interrupts_non_streaming_provider_call(tmp_path: Path) -> None:
    from tests.dummy_provider import (
        get_cancellable_blocking_provider_state,
        reset_cancellable_blocking_provider_state,
    )

    reset_cancellable_blocking_provider_state()
    config_path = _make_blocking_provider_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "Cancel blocking non-stream provider")
    app.save_session(session)

    request_id = "req_provider_cancel_nonstream"
    events: list[dict] = []

    def _consume() -> None:
        for ev in app.send_request(
            core,
            session,
            base_config,
            overrides=None,
            stream=False,
            request_id=request_id,
        ):
            events.append(ev)

    worker = threading.Thread(target=_consume)
    worker.start()

    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        if any(ev.get("type") == "request_started" for ev in events):
            break
        time.sleep(0.05)
    else:
        raise AssertionError("request_started was not emitted before cancellation")

    app.cancel_request(request_id)

    worker.join(timeout=5)
    assert not worker.is_alive()

    kinds = [ev.get("type") for ev in events]
    assert "request_cancelled" in kinds
    assert "request_completed" in kinds
    assert "final" not in kinds

    provider_state = get_cancellable_blocking_provider_state()
    assert request_id in provider_state["call_request_ids"]
    assert request_id in provider_state["cancel_request_ids"]
    assert request_id not in provider_state["active"]


def test_provider_cancellation_is_request_scoped(tmp_path: Path) -> None:
    from tests.dummy_provider import (
        get_cancellable_blocking_provider_state,
        reset_cancellable_blocking_provider_state,
    )

    reset_cancellable_blocking_provider_state()
    config_path = _make_blocking_provider_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session1 = app.create_session("default")
    session1 = core.add_message(session1, "user", "first request")
    app.save_session(session1)
    _core2, _base2, session2 = app.create_session("default")
    session2 = core.add_message(session2, "user", "second request")
    app.save_session(session2)

    events1: list[dict] = []
    events2: list[dict] = []

    def _consume(session, rid, sink) -> None:
        for ev in app.send_request(
            core,
            session,
            base_config,
            overrides=None,
            stream=False,
            request_id=rid,
        ):
            sink.append(ev)

    worker1 = threading.Thread(target=_consume, args=(session1, "req_provider_one", events1))
    worker2 = threading.Thread(target=_consume, args=(session2, "req_provider_two", events2))
    worker1.start()
    worker2.start()

    deadline = time.monotonic() + 5.0
    while time.monotonic() < deadline:
        started1 = any(ev.get("type") == "request_started" for ev in events1)
        started2 = any(ev.get("type") == "request_started" for ev in events2)
        if started1 and started2:
            break
        time.sleep(0.05)
    else:
        raise AssertionError("both requests did not start before cancellation")

    app.cancel_request("req_provider_one")

    worker1.join(timeout=5)
    assert not worker1.is_alive()
    time.sleep(0.2)
    assert worker2.is_alive()

    app.cancel_request("req_provider_two")
    worker2.join(timeout=5)
    assert not worker2.is_alive()

    kinds1 = {ev.get("type") for ev in events1}
    kinds2 = {ev.get("type") for ev in events2}
    assert "request_cancelled" in kinds1
    assert "request_cancelled" in kinds2

    provider_state = get_cancellable_blocking_provider_state()
    assert provider_state["call_request_ids"].count("req_provider_one") == 1
    assert provider_state["call_request_ids"].count("req_provider_two") == 1
    assert provider_state["cancel_request_ids"].count("req_provider_one") >= 1
    assert provider_state["cancel_request_ids"].count("req_provider_two") >= 1
