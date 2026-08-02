from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Any, Dict

from agent_app.application_future import AgentApplication
from agent_app.application_notifications import InMemoryApplicationNotificationStore
from agent_app.application_owner import AgentApplicationOwner, ApplicationControl
from agent_app.events import InMemoryEventStore
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
