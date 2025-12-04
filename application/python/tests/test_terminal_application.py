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

    # After a space (arguments), no completion is offered for commands
    # without argument completers.
    assert _collect_completion_texts(completer, "/help more") == set()


def test_agent_id_completion() -> None:
    from agent_terminal_app import terminal as term_mod

    def _get_agents() -> list[str]:
        return ["default", "alt"]

    completer = term_mod.SlashCommandCompleter(get_agent_ids=_get_agents)

    # Completing agent id after "/agent ".
    texts = _collect_completion_texts(completer, "/agent a")
    assert "alt" in texts
    assert "default" not in texts

    # With no prefix, all agents are suggested.
    texts_all = _collect_completion_texts(completer, "/agent ")
    assert "default" in texts_all
    assert "alt" in texts_all


def test_set_completion() -> None:
    from agent_terminal_app import terminal as term_mod

    def _get_elements() -> list[dict]:
        return [
            {"key": "enable_reasoning", "type": "checkbox", "options": []},
            {
                "key": "reasoning_effort",
                "type": "select",
                "options": ["low", "medium", "high"],
            },
        ]

    completer = term_mod.SlashCommandCompleter(get_ui_elements=_get_elements)

    # Key completion after /set
    key_texts = _collect_completion_texts(completer, "/set r")
    assert "reasoning_effort" in key_texts
    assert "enable_reasoning" not in key_texts

    # Value completion after specific key
    val_texts = _collect_completion_texts(completer, "/set reasoning_effort h")
    assert "high" in val_texts
    assert "low" not in val_texts


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

    # Decide on a non-default target agent and switch via /agent {agent_id}.
    target = next(a for a in agents if a != "default")

    await term_mod._cmd_agent(ctx, target)

    assert ctx.agent_id == target

    loaded = app.load_session(session.session_id)
    assert loaded is not None
    _core2, _base_config2, updated_session = loaded
    assert updated_session.metadata.get("agent_id") == target


@pytest.mark.asyncio
async def test_set_overrides_and_send_request_uses_them(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from agent_core import AgentCore
    from agent_terminal_app import terminal as term_mod

    base_dir = Path(term_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    app = AgentApplication(str(config_path), str(session_root), event_store=events)

    # Monkeypatch AgentCore.get_ui_schema to expose a reasoning_effort select.
    def _fake_get_ui_schema(self) -> dict:  # type: ignore[override]
        return {
            "openrouter_reasoning": [
                {
                    "type": "select",
                    "key": "reasoning_effort",
                    "options": [
                        {"value": "low", "label": "Low"},
                        {"value": "high", "label": "High"},
                    ],
                }
            ]
        }

    monkeypatch.setattr(AgentCore, "get_ui_schema", _fake_get_ui_schema, raising=False)

    # Create a session and context.
    session = term_mod.create_session(app, agent_id="default", system_message=None)
    ctx = term_mod.TerminalContext(app=app, session_id=session.session_id, agent_id="default")

    # Use /set to update an override in session metadata.
    await term_mod._cmd_set(ctx, "reasoning_effort high")

    loaded = app.load_session(session.session_id)
    assert loaded is not None
    _core2, _base_config2, updated_session = loaded
    overrides = updated_session.metadata.get("overrides") or {}
    assert overrides.get("reasoning_effort") == "high"

    # Patch AgentApplication.send_request to capture overrides passed in.
    captured: dict = {}

    def _fake_send_request(self, core, session_obj, base_cfg, overrides_arg, *, stream=False, request_id=None):  # type: ignore[override]
        captured["overrides"] = overrides_arg
        # Minimal final event structure for terminal.send_request.
        yield {
            "type": "final",
            "session": session_obj.to_dict(),
            "messages": [],
            "request_id": "req-1",
        }

    monkeypatch.setattr(AgentApplication, "send_request", _fake_send_request, raising=True)

    # Invoke terminal.send_request without explicit overrides; it should
    # pull from session.metadata["overrides"].
    final_session_dict, messages, request_id = term_mod.send_request(
        app,
        session.session_id,
        overrides=None,
        stream=True,
    )

    assert captured["overrides"] == {"reasoning_effort": "high"}
    assert final_session_dict is not None
