"""Tests for the agent_terminal_app server application.

These tests mirror the style of the example application tests under
``core/python/examples/tests`` but exercise the ServerApplication class
instead of the FastAPI routes.
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


def test_server_application_flow_with_echo_provider(tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod
    from agent_terminal_app.server import ServerApplication

    base_dir = Path(server_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    app = ServerApplication(config_path=config_path, session_root=session_root)

    system_message = "You are a helpful echo assistant."
    user_message = "hello from the agent_terminal_app test"

    # 1) Create a new session with a system message.
    session = app.create_session(agent_id="default", system_message=system_message)
    session_id = session.session_id
    assert isinstance(session_id, str) and session_id

    # 2) Add a user message.
    updated = app.add_message(session_id, role="user", content=user_message, metadata=None)
    assert updated.session_id == session_id

    # 3) Send a request and verify the echo provider behaviour.
    final_session_dict, messages, request_id = app.send_request(session_id, overrides={}, stream=True)

    assert messages, "expected at least one final message"
    last = messages[-1]
    content = last.get("content", "")
    assert isinstance(content, str)

    # EchoOpenAILikeProvider returns "SYS=<system> | USER=<user>".
    assert "SYS=" in content and "USER=" in content
    assert system_message in content
    assert user_message in content

    # 4) Basic check that events were recorded for this session.
    events = app.list_events(session_id=session_id, limit=100)
    kinds = {ev.get("type") for ev in events}
    assert "session_created" in kinds
    assert "message_appended" in kinds
    assert "request_started" in kinds or "final" in kinds
