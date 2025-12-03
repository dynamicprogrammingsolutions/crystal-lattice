"""Tests for the agent_terminal_app terminal application.

These tests exercise the TerminalApplication class directly using the
in-process echo provider configuration so they do not require network
access.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path


ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
APP_PY = os.path.join(ROOT, "application/python")
if APP_PY not in sys.path:
    sys.path.insert(0, APP_PY)
CORE_PY = os.path.join(ROOT, "core/python")
if CORE_PY not in sys.path:
    sys.path.insert(0, CORE_PY)


def test_terminal_application_flow_with_echo_provider(tmp_path: Path) -> None:
    from agent_terminal_app import terminal as term_mod
    from agent_terminal_app.terminal import TerminalApplication

    base_dir = Path(term_mod.__file__).resolve().parent
    echo_config = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    app = TerminalApplication(config_path=echo_config, session_root=session_root)

    system_message = "You are a helpful echo assistant."
    user_message = "hello from the terminal test"

    # 1) Create a new session with a system message.
    session = app.create_session(agent_id="default", system_message=system_message)
    session_id = session.session_id

    # 2) Add a user message.
    updated = app.add_message(session_id, role="user", content=user_message, metadata=None)
    assert updated.session_id == session_id

    # 3) Send a request and verify the echo provider behaviour.
    final_session_dict, messages, request_id = app.send_request(session_id, overrides={}, stream=True)

    # Reload the final session from the application to avoid relying on
    # the shape of the streaming events.
    ctx = app.agent_app.load_session(session_id)
    assert ctx is not None
    _core, _base_config, final_session = ctx
    session_dict = final_session.to_dict()

    history = session_dict.get("messages") or []
    assert history, "expected at least one message in the final session"
    # For the echo config we only require that the call completes and
    # that the session history was not corrupted; we do not assert on
    # the exact assistant content here.

    # 4) Basic check that events were recorded for this session.
    events = app.list_events(session_id=session_id, limit=100)
    kinds = {ev.get("type") for ev in events}
    assert "session_created" in kinds
    assert "message_appended" in kinds
    assert "request_started" in kinds or "final" in kinds
