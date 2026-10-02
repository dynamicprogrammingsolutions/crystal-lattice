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
from types import SimpleNamespace

from agent_app.app_context import ApplicationContext
from agent_app.application_future import AgentApplication
from agent_app.tool_loop import RequestCancellation, ToolLoopRunner
from agent_core import AgentCore


def _make_config(tmp_path: Path) -> Path:
    cfg = {
        "providers": {"dummy": {"provider": "dummy_provider", "model": "test-model"}},
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


def test_soft_cancel_interrupts_provider_signal_but_not_tool_signal() -> None:
    cancellation = RequestCancellation()
    provider_interrupted = threading.Event()
    tool_interrupted = threading.Event()
    cancellation.add_callback(provider_interrupted.set)
    cancellation.tool_cancellation.add_callback(tool_interrupted.set)

    cancellation.soft_cancel()

    assert cancellation.is_cancelled()
    assert cancellation.cancellation_mode() == "soft"
    assert provider_interrupted.is_set()
    assert not tool_interrupted.is_set()

    cancellation.cancel()

    assert cancellation.cancellation_mode() == "hard"
    assert tool_interrupted.is_set()


def test_streaming_assistant_lifecycle_carries_reserved_message_index(
    tmp_path: Path,
) -> None:
    config_path = _make_config(tmp_path)
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
    )
    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "Hello")
    app.save_session(session)
    expected_index = len(session.messages)

    events = list(app.send_request(core, session, base_config, overrides=None, stream=True))

    lifecycle = [event for event in events if event.get("type") == "assistant_message"]
    assert [event.get("phase") for event in lifecycle] == ["start", "end"]
    assert all(event.get("message_index") == expected_index for event in lifecycle)

    final_event = next(event for event in events if event.get("type") == "final")
    assert final_event["start_index"] == expected_index


def test_final_without_partials_emits_indexed_synthetic_assistant_start() -> None:
    session_core = AgentCore()
    session = session_core.create_session()
    session = session_core.add_message(session, "user", "Hello")
    expected_index = len(session.messages)
    final_message = {"role": "assistant", "content": "Done", "metadata": {}}
    final_session = session_core.add_message(session, "assistant", "Done")

    class _FinalOnlyCore:
        def send_request_stream(self, *args, **kwargs):
            _ = args, kwargs
            yield {
                "type": "final",
                "session": final_session,
                "messages": [final_message],
            }

    runner = ToolLoopRunner(
        core=_FinalOnlyCore(),  # type: ignore[arg-type]
        config={},
        request_id="request-final-only",
        tool_loop_cfg=SimpleNamespace(max_loops=8),
        app_context=ApplicationContext(app=None),
        base_config={},
    )

    events = list(runner._run_llm_phase(session, stream=True))
    lifecycle = [event for event in events if event.get("type") == "assistant_message"]

    assert [event.get("phase") for event in lifecycle] == ["start", "end"]
    assert all(event.get("message_index") == expected_index for event in lifecycle)


def test_send_request_completion_expires_request_scoped_notification(
    tmp_path: Path,
) -> None:
    config_path = _make_config(tmp_path)
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
    )
    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "Hello")
    app.save_session(session)
    request_id = "request-with-notification"
    created = app.create_session_notification(
        session.session_id,
        {
            "key": "request:notification",
            "severity": "info",
            "title": "Request notification",
            "body": "Visible until request completion",
            "source": {"plugin": "test"},
            "display": {
                "format": "text",
                "body": "Visible until request completion",
                "presentation": "inline",
            },
            "retention": {"policy": "until_request_complete"},
        },
        request_id=request_id,
    )

    events = list(
        app.send_request(
            core,
            session,
            base_config,
            stream=True,
            request_id=request_id,
        )
    )

    assert events[-1]["type"] == "request_completed"
    retained = app.list_session_notifications(
        session.session_id,
        include_terminal=True,
    )
    expired = next(item for item in retained if item["id"] == created["id"])
    assert expired["status"] == "expired"
    assert expired["expiration"]["reason"] == "request_completed"


def test_send_request_completes_when_tool_preparation_fails(tmp_path: Path) -> None:
    config_path = _make_failing_prepare_tool_config(tmp_path)
    session_root = tmp_path / "sessions"

    app = AgentApplication(str(config_path), str(session_root), core_factory=AgentCore)

    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "Hello")
    app.save_session(session)

    events = list(app.send_request(core, session, base_config, overrides=None, stream=True))

    assert [event.get("type") for event in events] == [
        "request_started",
        "error",
        "request_completed",
    ]
    assert "Tool preparation failed" in str(events[1].get("detail"))


def test_prepare_failure_still_expires_request_scoped_notification(
    tmp_path: Path,
) -> None:
    config_path = _make_failing_prepare_tool_config(tmp_path)
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
    )
    core, base_config, session = app.create_session("default")
    session = core.add_message(session, "user", "Hello")
    app.save_session(session)
    request_id = "prepare-failure-request"
    created = app.create_session_notification(
        session.session_id,
        {
            "key": "prepare:notification",
            "severity": "warning",
            "title": "Preparation notification",
            "body": "Expires even when preparation fails",
            "source": {"plugin": "test"},
            "display": {
                "format": "text",
                "body": "Expires even when preparation fails",
                "presentation": "inline",
            },
            "retention": {"policy": "until_request_complete"},
        },
        request_id=request_id,
    )

    events = list(
        app.send_request(
            core,
            session,
            base_config,
            stream=True,
            request_id=request_id,
        )
    )

    assert events[-1]["type"] == "request_completed"
    retained = app.list_session_notifications(
        session.session_id,
        include_terminal=True,
    )
    expired = next(item for item in retained if item["id"] == created["id"])
    assert expired["status"] == "expired"
    assert expired["expiration"]["reason"] == "request_completed"


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
        "providers": {"dummy": {"provider": "failing_dummy_provider", "model": "test-model"}},
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
        "providers": {"dummy": {"provider": "dummy_provider", "model": "test-model"}},
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


def _make_finite_blocking_tool_config(tmp_path: Path) -> Path:
    cfg = {
        "providers": {"dummy": {"provider": "dummy_provider", "model": "test-model"}},
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.dummy_tool.FiniteBlockingTool",
        ],
        "agents": {
            "default": {"provider": "dummy"},
        },
    }
    path = tmp_path / "config_finite_blocking_tool.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _make_failing_prepare_tool_config(tmp_path: Path) -> Path:
    cfg = {
        "providers": {"dummy": {"provider": "dummy_provider", "model": "test-model"}},
        "plugins": [
            "tests.dummy_provider.DummyProvider",
            "tests.dummy_tool.FailingPrepareTool",
        ],
        "agents": {
            "default": {"provider": "dummy"},
        },
    }
    path = tmp_path / "config_failing_prepare_tool.json"
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


def test_cancel_request_during_registration_is_not_lost(
    tmp_path: Path,
    monkeypatch,
) -> None:
    import agent_app.application_future as application_future

    config_path = _make_config(tmp_path)
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
    )
    request_id = "registration-race"
    constructor_entered = threading.Event()
    allow_constructor = threading.Event()
    registered: dict[str, object] = {}
    original_cancellation = application_future.RequestCancellation

    class BlockingRequestCancellation(original_cancellation):
        def __init__(self, *, cancelled: bool = False) -> None:
            constructor_entered.set()
            assert allow_constructor.wait(timeout=5)
            super().__init__(cancelled=cancelled)

    monkeypatch.setattr(
        application_future,
        "RequestCancellation",
        BlockingRequestCancellation,
    )

    register_thread = threading.Thread(
        target=lambda: registered.setdefault(
            "cancellation",
            app._register_request_cancellation(request_id),
        )
    )
    register_thread.start()
    assert constructor_entered.wait(timeout=5)

    cancel_thread = threading.Thread(target=lambda: app.cancel_request(request_id))
    cancel_thread.start()
    time.sleep(0.05)
    assert cancel_thread.is_alive()

    allow_constructor.set()
    register_thread.join(timeout=5)
    cancel_thread.join(timeout=5)
    assert not register_thread.is_alive()
    assert not cancel_thread.is_alive()

    cancellation = registered["cancellation"]
    assert isinstance(cancellation, original_cancellation)
    assert cancellation.is_cancelled()
    app._clear_request_cancellation(request_id)


def test_pre_registered_soft_cancel_preserves_tool_until_hard_escalation(
    tmp_path: Path,
) -> None:
    config_path = _make_config(tmp_path)
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
    )
    request_id = "pre-registered-soft-cancel"

    app.soft_cancel_request(request_id)
    cancellation = app._register_request_cancellation(request_id)

    assert cancellation.is_cancelled()
    assert cancellation.cancellation_mode() == "soft"
    assert cancellation.tool_cancellation.is_cancelled() is False

    app.cancel_request(request_id)

    assert cancellation.cancellation_mode() == "hard"
    assert cancellation.tool_cancellation.is_cancelled() is True
    app._clear_request_cancellation(request_id)


def test_early_hard_cancel_cannot_be_downgraded_by_soft_cancel(
    tmp_path: Path,
) -> None:
    config_path = _make_config(tmp_path)
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
    )
    request_id = "pre-registered-hard-cancel"

    app.cancel_request(request_id)
    app.soft_cancel_request(request_id)
    cancellation = app._register_request_cancellation(request_id)

    assert cancellation.cancellation_mode() == "hard"
    assert cancellation.tool_cancellation.is_cancelled() is True
    app._clear_request_cancellation(request_id)


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
    cancelled_event = next(
        event for event in events if event.get("type") == "request_cancelled"
    )
    assert cancelled_event["cancellation_mode"] == "hard"

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


def test_soft_cancel_waits_for_active_tool_and_persists_result(tmp_path: Path) -> None:
    from tests.dummy_tool import (
        get_finite_blocking_tool_state,
        release_finite_blocking_tool,
        reset_finite_blocking_tool_state,
    )

    reset_finite_blocking_tool_state()
    config_path = _make_finite_blocking_tool_config(tmp_path)
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
    )
    core, base_config, session = app.create_session("default")
    tool_call = {
        "id": "call_finish",
        "type": "function",
        "function": {
            "name": "finish_when_released",
            "arguments": json.dumps({}),
        },
    }
    second_tool_call = {
        **tool_call,
        "id": "call_must_not_start",
    }
    session = core.add_message(
        session,
        "assistant",
        "",
        {"tool_calls": [tool_call, second_tool_call]},
    )
    app.save_session(session)
    events: list[dict] = []
    request_id = "req_tool_soft_cancel"

    worker = threading.Thread(
        target=lambda: events.extend(
            app.send_request(
                core,
                session,
                base_config,
                stream=True,
                request_id=request_id,
            )
        )
    )
    worker.start()

    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if get_finite_blocking_tool_state()["entered"]:
            break
        time.sleep(0.02)
    else:
        raise AssertionError("finite tool did not start")

    app.soft_cancel_request(request_id)
    time.sleep(0.1)
    assert worker.is_alive()
    assert get_finite_blocking_tool_state()["interrupted"] is False

    release_finite_blocking_tool()
    worker.join(timeout=5)
    assert not worker.is_alive()

    cancelled = next(event for event in events if event.get("type") == "request_cancelled")
    assert cancelled["cancellation_mode"] == "soft"
    assert any(event.get("type") == "tool_results" for event in events)
    checkpoints = [
        event for event in events if event.get("type") == "session_checkpoint"
    ]
    assert checkpoints
    assert checkpoints[-1]["session"].messages[-1].content == "finished normally"
    assert get_finite_blocking_tool_state()["call_count"] == 1
    assert not any(event.get("type") == "final" for event in events)


def test_hard_cancel_escalates_soft_cancel_during_active_tool(tmp_path: Path) -> None:
    from tests.dummy_tool import (
        get_finite_blocking_tool_state,
        reset_finite_blocking_tool_state,
    )

    reset_finite_blocking_tool_state()
    config_path = _make_finite_blocking_tool_config(tmp_path)
    app = AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        core_factory=AgentCore,
    )
    core, base_config, session = app.create_session("default")
    tool_call = {
        "id": "call_escalate",
        "type": "function",
        "function": {
            "name": "finish_when_released",
            "arguments": json.dumps({}),
        },
    }
    session = core.add_message(session, "assistant", "", {"tool_calls": [tool_call]})
    app.save_session(session)
    request_id = "req_tool_soft_then_hard"
    events: list[dict] = []
    worker = threading.Thread(
        target=lambda: events.extend(
            app.send_request(
                core,
                session,
                base_config,
                stream=True,
                request_id=request_id,
            )
        )
    )
    worker.start()

    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        if get_finite_blocking_tool_state()["entered"]:
            break
        time.sleep(0.02)
    else:
        raise AssertionError("finite tool did not start")

    app.soft_cancel_request(request_id)
    app.cancel_request(request_id)
    worker.join(timeout=5)
    assert not worker.is_alive()
    assert get_finite_blocking_tool_state()["interrupted"] is True
    cancelled = next(event for event in events if event.get("type") == "request_cancelled")
    assert cancelled["cancellation_mode"] == "hard"


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
        provider_state = get_cancellable_blocking_provider_state()
        if request_id in provider_state["active"]:
            break
        time.sleep(0.05)
    else:
        raise AssertionError("provider was not active before cancellation")

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


def test_cancel_request_interrupts_provider_after_partial_output(
    tmp_path: Path,
) -> None:
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
    assistant_starts = [
        event
        for event in events
        if event.get("type") == "assistant_message" and event.get("phase") == "start"
    ]
    assert assistant_starts
    assert assistant_starts[0].get("message_index") == len(session.messages)

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
        provider_state = get_cancellable_blocking_provider_state()
        if request_id in provider_state["active"]:
            break
        time.sleep(0.05)
    else:
        raise AssertionError("provider was not active before cancellation")

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

    try:
        # Wait until both provider calls are in flight and their cancel events
        # are registered; request_started alone does not guarantee the
        # provider was reached, and cancelling before the call would abort
        # the request without invoking the provider.
        deadline = time.monotonic() + 5.0
        while time.monotonic() < deadline:
            active_ids = set(get_cancellable_blocking_provider_state()["active"])
            if {"req_provider_one", "req_provider_two"} <= active_ids:
                break
            time.sleep(0.05)
        else:
            raise AssertionError("both requests did not reach the provider before cancellation")

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
    finally:
        # Unblock the workers on any failure path so the process can exit.
        if worker1.is_alive() or worker2.is_alive():
            app.cancel_request("req_provider_one")
            app.cancel_request("req_provider_two")
        worker1.join(timeout=5)
        worker2.join(timeout=5)
