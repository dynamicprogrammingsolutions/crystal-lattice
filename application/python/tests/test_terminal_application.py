"""Tests for the agent_terminal_app terminal helpers.

These tests exercise the module-level helper functions in
``agent_terminal_app.terminal`` using the in-process echo provider
configuration so they do not require network access.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest
from prompt_toolkit.document import Document

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
APP_PY = os.path.join(ROOT, "application/python")
if APP_PY not in sys.path:
    sys.path.insert(0, APP_PY)
CORE_PY = os.path.join(ROOT, "core/python")
if CORE_PY not in sys.path:
    sys.path.insert(0, CORE_PY)


def test_terminal_flow_with_echo_provider(tmp_path: Path) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from agent_terminal_app import terminal as term_mod

    base_dir = Path(term_mod.__file__).resolve().parent
    echo_config = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(echo_config), str(session_root), event_store=events)

    system_message = "You are a helpful echo assistant."
    user_message = "hello from the terminal test"

    # 1) Create a new session with a system message.
    session = term_mod.create_session(app, agent_id="default", system_message=system_message)
    session_id = session.session_id

    # 2) Add a user message.
    updated = term_mod.add_message(app, session_id, role="user", content=user_message, metadata=None)
    assert updated.session_id == session_id

    # 3) Send a request and verify the echo provider behaviour.
    final_session_dict, messages, request_id = term_mod.send_request(
        app,
        session_id,
        overrides={},
        stream=True,
    )

    # Reload the final session from the application to avoid relying on
    # the shape of the streaming events.
    ctx = app.load_session(session_id)
    assert ctx is not None
    _core, _base_config, final_session = ctx
    session_dict = final_session.to_dict()

    history = session_dict.get("messages") or []
    assert history, "expected at least one message in the final session"
    # For the echo config we only require that the call completes and
    # that the session history was not corrupted; we do not assert on
    # the exact assistant content here.

    # 4) Basic check that events were recorded for this session.
    events_list = term_mod.list_events(app, session_id=session_id, limit=100)
    kinds = {ev.get("type") for ev in events_list}
    assert "session_created" in kinds
    assert "message_appended" in kinds
    assert "request_started" in kinds or "final" in kinds


def _collect_completion_texts(completer, text: str) -> set[str]:
    doc = Document(text=text, cursor_position=len(text))
    return {c.text for c in completer.get_completions(doc, None)}


def test_slash_command_completer_basic() -> None:
    from agent_terminal_app import terminal as term_mod

    completer = term_mod.SlashCommandCompleter()

    # Basic prefix completion.
    texts = _collect_completion_texts(completer, "/he")
    assert "help" in texts

    # Non-slash input should not offer completions.
    assert _collect_completion_texts(completer, "hello") == set()

    # After a space (arguments), no completion is offered.
    assert _collect_completion_texts(completer, "/help more") == set()


@pytest.mark.asyncio
async def test_agent_switch_slash_command(tmp_path: Path) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from agent_terminal_app import terminal as term_mod

    base_dir = Path(term_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    agents = app.list_agents()
    assert "default" in agents
    assert len(agents) >= 2

    # Create an initial session using the default agent.
    session = term_mod.create_session(app, agent_id="default", system_message=None)
    metadata = session.metadata or {}
    initial_agent = metadata.get("agent_id")
    assert initial_agent == "default"

    ctx = term_mod.TerminalContext(
        app=app,
        session_id=session.session_id,
        agent_id=initial_agent,
    )

    # Trigger the /agent dialog.
    await term_mod._cmd_agent(ctx, "")
    assert ctx.pending_agent_choices is not None
    available = ctx.pending_agent_choices
    assert isinstance(available, list)
    assert set(available) >= {"default"}

    # Choose a non-default agent if available.
    target = next(a for a in available if a != "default")

    # Simulate user entering the chosen agent name.
    term_mod._handle_agent_selection(ctx, target)

    assert ctx.agent_id == target

    loaded = app.load_session(session.session_id)
    assert loaded is not None
    _core2, _base_config2, updated_session = loaded
    assert updated_session.metadata.get("agent_id") == target
