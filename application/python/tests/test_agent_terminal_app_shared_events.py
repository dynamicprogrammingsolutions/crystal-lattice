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

    term_app.switch_session(session_id)

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


def test_cursor_after_terminal_request_avoids_replay_for_mobile(tmp_path: Path) -> None:
    """Cursor from /sessions/{id}/messages should not replay last request.

    This test mirrors the mobile scenario where a session is created and a
    request is sent via the terminal, then the mobile app loads messages via
    the HTTP server and starts polling /events from the returned
    ``cursor_event_id``. The cursor should be positioned so that polling
    does not replay the already-completed request.
    """

    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from agent_terminal_app import server as server_mod
    from agent_terminal_app import terminal as term_mod

    base_dir = Path(__file__).resolve().parent.parent / "agent_terminal_app"
    echo_config = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    shared_events = InMemoryEventStore()

    # Two AgentApplication instances sharing a single event store, as in
    # --server --console mode.
    server_app = AgentApplication(
        str(echo_config), str(session_root), event_store=shared_events
    )
    terminal_agent_app = AgentApplication(
        str(echo_config), str(session_root), event_store=shared_events
    )

    term_app = term_mod.TerminalApplication(
        config_path=str(echo_config),
        session_root=str(session_root),
        agent_app=terminal_agent_app,
    )

    # 1) Create a session and run a request entirely via the terminal.
    session = term_app.start_new_session(agent_id="default")
    session_id = session.session_id

    term_app.append_user_message("hello from terminal")
    _final_session_dict, final_messages, request_id = term_app.send_request(stream=False)
    assert final_messages, "expected terminal request to produce final messages"

    # 2) Server side: emulate the mobile app loading messages.
    messages_resp = server_mod.list_session_messages(
        session_id,
        start=-50,
        app_instance=server_app,
    )
    cursor_event_id = messages_resp["cursor_event_id"]

    # 3) Emulate the mobile app's first /events poll using that cursor.
    events_resp = server_mod.list_events(
        since_id=cursor_event_id,
        request_id=None,
        session_id=session_id,
        limit=5000,
        app_instance=server_app,
    )
    events_payload = events_resp.get("events") or []

    # Under the desired semantics, there should be no replay of the last
    # completed request when polling from the cursor returned by
    # /sessions/{id}/messages. In particular, no streaming or final
    # assistant/tool events for this request should appear after the
    # cursor. A request_completed marker is acceptable.
    blocked_types = {
        "assistant_message",
        "partial",
        "final",
        "tool_calls",
        "tool_partial",
        "tool_results",
    }

    replayed_types = {
        ev.get("type")
        for ev in events_payload
        if ev.get("session_id") == session_id and ev.get("request_id") == request_id
    }

    assert not (replayed_types & blocked_types)
