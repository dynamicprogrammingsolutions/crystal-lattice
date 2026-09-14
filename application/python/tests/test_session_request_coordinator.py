from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, Dict

from fastapi import HTTPException
import pytest

from agent_app.application_future import AgentApplication
from agent_app.application_notifications import InMemoryApplicationNotificationStore
from agent_app.application_owner import AgentApplicationOwner, ApplicationControl
from agent_app.events import InMemoryEventStore
from agent_app.operations import (
    get_application_operation_service,
    session_operation_exclusivity_key,
)
from agent_terminal_app import server as server_mod
from agent_terminal_app.terminal_app import TerminalApplication


def _echo_config_path() -> Path:
    return Path(server_mod.__file__).resolve().parent / "config_echo_app.json"


def _blocking_send(
    *,
    session_id: str,
    started: threading.Event,
    release: threading.Event,
):
    def _send_request(
        core_arg: Any,
        session_arg: Any,
        base_config_arg: Any,
        overrides_arg: Dict[str, Any] | None,
        *,
        stream: bool = True,
        request_id: str | None = None,
        baseline_file_state: Any = None,
    ):
        _ = (
            core_arg,
            session_arg,
            base_config_arg,
            overrides_arg,
            baseline_file_state,
        )
        started.set()
        yield {
            "type": "request_started",
            "session_id": session_id,
            "request_id": request_id,
            "stream": stream,
        }
        release.wait(timeout=5)
        yield {
            "type": "final",
            "session_id": session_id,
            "request_id": request_id,
            "messages": [],
        }
        yield {
            "type": "request_completed",
            "session_id": session_id,
            "request_id": request_id,
        }

    return _send_request


def _wait_for_request_cleanup(app: AgentApplication, session_id: str) -> None:
    deadline = time.time() + 5
    while time.time() < deadline:
        if app.get_active_session_request_id(session_id) is None:
            return
        time.sleep(0.02)
    raise AssertionError("timed out waiting for request admission cleanup")


def test_terminal_and_http_share_one_active_request_authority(tmp_path: Path) -> None:
    config_path = _echo_config_path()
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    app = AgentApplication(config_path, session_root, event_store=events)
    terminal = TerminalApplication(
        config_path=config_path,
        session_root=session_root,
        agent_app=app,
    )
    session = terminal.start_new_session(agent_id="default")
    terminal.append_user_message("hello")

    started = threading.Event()
    release = threading.Event()
    app.send_request = _blocking_send(  # type: ignore[assignment]
        session_id=session.session_id,
        started=started,
        release=release,
    )

    terminal_start = terminal.start_request()
    assert terminal_start.status == "started"
    assert started.wait(timeout=2)
    operations = get_application_operation_service(app.get_runtime_store())
    active_operation = operations.get(terminal_start.request_id)
    assert active_operation is not None
    assert active_operation.owner_id == "agent_app.session_request"
    assert active_operation.session_id == session.session_id

    http_start = server_mod.send_request(
        session.session_id,
        {"config_overrides": {}},
        app_instance=app,
    )
    assert http_start == {
        "status": "already_running",
        "request_id": terminal_start.request_id,
    }

    before = app.load_live_session_record(session.session_id)
    assert before is not None
    duplicate_append = terminal.append_user_message_and_start_request("must not append")
    assert duplicate_append.status == "already_running"
    assert duplicate_append.request_id == terminal_start.request_id
    after = app.load_live_session_record(session.session_id)
    assert after is not None
    assert after.messages == before.messages

    release.set()
    _wait_for_request_cleanup(app, session.session_id)
    assert operations.get(terminal_start.request_id) is None


def test_background_request_retains_application_generation_during_reload(
    tmp_path: Path,
) -> None:
    config_path = _echo_config_path()
    session_root = tmp_path / "sessions"
    events = InMemoryEventStore()
    notification_store = InMemoryApplicationNotificationStore()

    def factory(control: ApplicationControl) -> AgentApplication:
        return AgentApplication(
            config_path,
            session_root,
            event_store=events,
            application_notification_store=notification_store,
            application_control=control,
        )

    owner = AgentApplicationOwner(factory, event_store=events)
    old_application = owner.current
    core, base_config, session = old_application.create_session("default")
    session = core.add_message(
        session,
        "user",
        "hold reload",
        metadata=None,
        config=base_config,
    )
    old_application.save_session(session)

    started = threading.Event()
    release = threading.Event()
    old_application.send_request = _blocking_send(  # type: ignore[assignment]
        session_id=session.session_id,
        started=started,
        release=release,
    )

    request = old_application.start_session_request(session.session_id)
    assert request.status == "started"
    assert started.wait(timeout=2)

    reload_result = owner.request_reload(reason="request-coordinator-test")
    assert owner.wait_for_reload(reload_result["reload_id"], timeout=0.1) is False
    assert owner.current is old_application

    release.set()
    assert owner.wait_for_reload(reload_result["reload_id"], timeout=5)
    assert owner.current is not old_application


def test_http_send_reports_session_busy_for_non_request_operation(
    tmp_path: Path,
) -> None:
    config_path = _echo_config_path()
    app = AgentApplication(config_path, tmp_path / "sessions")
    _core, _base_config, session = app.create_session("default")
    operations = get_application_operation_service(app.get_runtime_store())
    lease = operations.reserve(
        operation_id="test-compaction",
        owner_id="test_compaction",
        session_id=session.session_id,
        exclusivity_keys=(session_operation_exclusivity_key(session.session_id),),
    )

    with pytest.raises(HTTPException) as exc_info:
        server_mod.send_request(
            session.session_id,
            {"config_overrides": {}},
            app_instance=app,
        )

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail["status"] == "session_busy"
    assert exc_info.value.detail["operation"]["owner_id"] == "test_compaction"
    lease.release()
    app.close()


def test_synchronous_message_run_is_atomic_and_returns_success(
    tmp_path: Path,
) -> None:
    app = AgentApplication(
        _echo_config_path(),
        tmp_path / "sessions",
        application_notification_store=InMemoryApplicationNotificationStore(),
    )
    _core, _base_config, session = app.create_session("default")
    observed: list[dict[str, Any]] = []

    result = app.run_session_request_with_message(
        session.session_id,
        role="user",
        content="coordinated task",
        stream=False,
        on_event=observed.append,
    )

    stored = app.load_session_record(session.session_id)
    assert stored is not None
    assert [message.role for message in stored.messages] == ["user", "assistant"]
    assert stored.messages[0].content == "coordinated task"
    assert result.status == "succeeded"
    assert result.error is None
    assert result.final_messages[-1]["role"] == "assistant"
    assert [event["type"] for event in observed] == [
        "request_started",
        "final",
        "request_completed",
    ]
    app.close()


def test_synchronous_result_classifies_and_redacts_request_error(
    tmp_path: Path,
) -> None:
    app = AgentApplication(
        _echo_config_path(),
        tmp_path / "sessions",
        application_notification_store=InMemoryApplicationNotificationStore(),
    )
    _core, _base_config, session = app.create_session("default")

    def _failing_send(*_args: Any, request_id: str, **_kwargs: Any):
        yield {
            "type": "request_started",
            "session_id": session.session_id,
            "request_id": request_id,
        }
        yield {
            "type": "error",
            "session_id": session.session_id,
            "request_id": request_id,
            "detail": "provider failed token=do-not-return Bearer also-secret",
        }
        yield {
            "type": "request_completed",
            "session_id": session.session_id,
            "request_id": request_id,
        }

    app.send_request = _failing_send  # type: ignore[assignment]
    result = app.run_session_request_with_message(
        session.session_id,
        role="user",
        content="fail safely",
        stream=False,
    )

    assert result.status == "failed"
    assert result.error is not None
    assert result.error.category == "request_failed"
    assert "do-not-return" not in result.error.message
    assert "also-secret" not in result.error.message
    assert result.error.message.count("[redacted]") == 2
    stored = app.load_session_record(session.session_id)
    assert stored is not None
    assert [message.content for message in stored.messages] == ["fail safely"]
    app.close()


def test_synchronous_result_classifies_missing_final_as_interrupted(
    tmp_path: Path,
) -> None:
    app = AgentApplication(
        _echo_config_path(),
        tmp_path / "sessions",
        application_notification_store=InMemoryApplicationNotificationStore(),
    )
    _core, _base_config, session = app.create_session("default")

    def _interrupted_send(*_args: Any, request_id: str, **_kwargs: Any):
        yield {
            "type": "request_started",
            "session_id": session.session_id,
            "request_id": request_id,
        }
        yield {
            "type": "request_completed",
            "session_id": session.session_id,
            "request_id": request_id,
        }

    app.send_request = _interrupted_send  # type: ignore[assignment]
    result = app.run_session_request_with_message(
        session.session_id,
        role="user",
        content="interrupted",
        stream=False,
    )

    assert result.status == "interrupted"
    assert result.error is None
    assert result.final_messages == []
    app.close()


def test_synchronous_timeout_uses_request_cancellation_result(
    tmp_path: Path,
) -> None:
    app = AgentApplication(
        _echo_config_path(),
        tmp_path / "sessions",
        application_notification_store=InMemoryApplicationNotificationStore(),
    )
    _core, _base_config, session = app.create_session("default")

    def _slow_send(*_args: Any, request_id: str, **_kwargs: Any):
        yield {
            "type": "request_started",
            "session_id": session.session_id,
            "request_id": request_id,
        }
        time.sleep(0.05)
        yield {
            "type": "request_cancelled",
            "session_id": session.session_id,
            "request_id": request_id,
        }
        yield {
            "type": "request_completed",
            "session_id": session.session_id,
            "request_id": request_id,
        }

    app.send_request = _slow_send  # type: ignore[assignment]
    result = app.run_session_request_with_message(
        session.session_id,
        role="user",
        content="time out",
        stream=False,
        timeout=0.01,
    )

    assert result.status == "cancelled"
    assert result.error is not None
    assert result.error.category == "timeout"
    assert app.get_active_session_request_id(session.session_id) is None
    app.close()


def test_synchronous_observer_failure_cancels_and_cleans_up(
    tmp_path: Path,
) -> None:
    app = AgentApplication(
        _echo_config_path(),
        tmp_path / "sessions",
        application_notification_store=InMemoryApplicationNotificationStore(),
    )
    _core, _base_config, session = app.create_session("default")

    def _cancellable_send(*_args: Any, request_id: str, **_kwargs: Any):
        yield {
            "type": "request_started",
            "session_id": session.session_id,
            "request_id": request_id,
        }
        yield {
            "type": "request_cancelled",
            "session_id": session.session_id,
            "request_id": request_id,
        }
        yield {
            "type": "request_completed",
            "session_id": session.session_id,
            "request_id": request_id,
        }

    def _raise_from_observer(_event: dict[str, Any]) -> None:
        raise RuntimeError("observer failed")

    app.send_request = _cancellable_send  # type: ignore[assignment]
    with pytest.raises(RuntimeError, match="observer failed"):
        app.run_session_request_with_message(
            session.session_id,
            role="user",
            content="observer task",
            stream=False,
            on_event=_raise_from_observer,
        )

    assert app.get_active_session_request_id(session.session_id) is None
    stored = app.load_session_record(session.session_id)
    assert stored is not None
    assert [message.content for message in stored.messages] == ["observer task"]
    app.close()


@pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan"), True])
def test_synchronous_run_rejects_invalid_timeout(
    tmp_path: Path,
    timeout: Any,
) -> None:
    app = AgentApplication(
        _echo_config_path(),
        tmp_path / "sessions",
        application_notification_store=InMemoryApplicationNotificationStore(),
    )
    _core, _base_config, session = app.create_session("default")

    with pytest.raises(ValueError, match="finite positive"):
        app.run_session_request(session.session_id, timeout=timeout)

    app.close()
