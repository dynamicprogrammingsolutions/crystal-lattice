"""Integration-style tests for a shared InMemoryEventStore.

These tests construct a shared ``AgentApplication`` and event store
used by both the server-style and terminal-style helpers so that both
frontends can observe the same session events.
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


def test_shared_event_store_between_server_and_terminal(tmp_path: Path) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from agent_terminal_app import server as server_mod
    from agent_terminal_app import terminal as term_mod

    # Use the echo configuration for deterministic, offline behaviour.
    base_dir = Path(__file__).resolve().parent.parent / "agent_terminal_app"
    echo_config = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    shared_events = InMemoryEventStore()
    shared_app = AgentApplication(str(echo_config), str(session_root), event_store=shared_events)

    # 1) Create a session via the server helpers.
    create_resp = server_mod.create_session(
        {"agent_id": "default", "system_message": "shared store test"},
        app_instance=shared_app,
    )
    session_dict = create_resp["session"]
    session_id = session_dict["session_id"]

    # 2) Terminal side should see the session_created event via the terminal application helpers.
    term_app = term_mod.TerminalApplication(
        config_path=str(echo_config), session_root=str(session_root), agent_app=shared_app
    )
    t_events = term_app.list_events(session_id=session_id, limit=10)
    kinds = {ev.get("type") for ev in t_events}
    assert "session_created" in kinds

    # 3) Append a user message via the terminal helpers.
    term_app.add_message(session_id, role="user", content="from terminal", metadata=None)

    # 4) Server side should now see a message_appended event for the same session.
    s_events = server_mod.list_events(
        since_id=None,
        request_id=None,
        session_id=session_id,
        limit=20,
        app_instance=shared_app,
    )["events"]
    kinds = {ev.get("type") for ev in s_events}
    assert "message_appended" in kinds
