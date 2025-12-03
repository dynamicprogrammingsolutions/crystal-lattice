"""Integration-style tests for shared InMemoryEventStore.

These tests construct ServerApplication and TerminalApplication instances
that share the same event store and (optionally) the same AgentApplication
so that both frontends can observe the same session events.
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
    from agent_terminal_app.server import ServerApplication
    from agent_terminal_app.terminal import TerminalApplication

    # Use the echo configuration for deterministic, offline behaviour.
    base_dir = Path(__file__).resolve().parent.parent / "agent_terminal_app"
    echo_config = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    shared_app = AgentApplication(str(echo_config), str(session_root))
    shared_events = InMemoryEventStore()

    server_app = ServerApplication(
        config_path=echo_config,
        session_root=session_root,
        agent_app=shared_app,
        event_store=shared_events,
    )
    terminal_app = TerminalApplication(
        config_path=echo_config,
        session_root=session_root,
        agent_app=shared_app,
        event_store=shared_events,
    )

    # 1) Create a session via the server application.
    session = server_app.create_session(agent_id="default", system_message="shared store test")
    session_id = session.session_id

    # 2) Terminal side should see the session_created event.
    t_events = terminal_app.list_events(session_id=session_id, limit=10)
    kinds = {ev.get("type") for ev in t_events}
    assert "session_created" in kinds

    # 3) Append a user message via the terminal application.
    terminal_app.add_message(session_id, role="user", content="from terminal", metadata=None)

    # 4) Server side should now see a message_appended event for the same session.
    s_events = server_app.list_events(session_id=session_id, limit=20)
    kinds = {ev.get("type") for ev in s_events}
    assert "message_appended" in kinds
