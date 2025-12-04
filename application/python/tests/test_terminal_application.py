"""Tests for the agent_terminal_app terminal helpers.

These tests exercise the terminal application's helper logic and the
prompt_toolkit-based completion helpers using the in-process echo
provider configuration so they do not require network access.
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
    agent_app = AgentApplication(str(echo_config), str(session_root), event_store=events)
    term_app = term_mod.TerminalApplication(
        config_path=str(echo_config),
        session_root=str(session_root),
        agent_app=agent_app,
    )

    system_message = "You are a helpful echo assistant."
    user_message = "hello from the terminal test"

    # 1) Create a new active session with a system message.
    session = term_app.start_new_session(system_message=system_message, agent_id="default")
    session_id = session.session_id

    # 2) Add a user message to the active session.
    updated = term_app.append_user_message(user_message)
    assert updated.session_id == session_id

    # 3) Send a request and verify the echo provider behaviour.
    final_session_dict, messages, request_id = term_app.send_request(
        stream=True,
    )

    # Reload the final session from the application to avoid relying on
    # the shape of the streaming events.
    ctx = agent_app.load_session(session_id)
    assert ctx is not None
    _core, _base_config, final_session = ctx
    session_dict = final_session.to_dict()

    history = session_dict.get("messages") or []
    assert history, "expected at least one message in the final session"
    # For the echo config we only require that the call completes and
    # that the session history was not corrupted; we do not assert on
    # the exact assistant content here.

    # 4) Basic check that events were recorded for this session.
    events_list = term_app.poll_new_events(limit=100)
    kinds = {ev.get("type") for ev in events_list}
    assert "session_created" in kinds
    assert "message_appended" in kinds
    assert "request_started" in kinds or "final" in kinds


def _collect_completion_texts(completer, text: str) -> set[str]:
    doc = Document(text=text, cursor_position=len(text))
    return {c.text for c in completer.get_completions(doc, None)}


def test_slash_command_completer_basic() -> None:
    from agent_terminal_app import terminal as term_mod

    # Simple context stub; not used for basic command-name completion.
    class _Ctx:
        pass

    completer = term_mod.SlashCommandCompleter(lambda: _Ctx())

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

    class _DummyApp:
        def list_agents(self) -> list[str]:
            return ["default", "alt"]

    class _DummyTerminalApp:
        def list_agents(self) -> list[str]:
            return ["default", "alt"]

    completer = term_mod.SlashCommandCompleter(lambda: _DummyTerminalApp())

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

    class _DummyTerminalApp:
        def __init__(self, elements: list[dict]) -> None:
            self._elements = elements

        def list_agents(self) -> list[str]:  # unused here
            return []

        def session_ui_elements(self) -> list[dict]:
            return self._elements

    elements = [
        {"key": "enable_reasoning", "type": "checkbox", "options": []},
        {
            "key": "reasoning_effort",
            "type": "select",
            "options": ["low", "medium", "high"],
        },
    ]

    app = _DummyTerminalApp(elements)
    completer = term_mod.SlashCommandCompleter(lambda: app)

    # Key completion after /set
    key_texts = _collect_completion_texts(completer, "/set r")
    assert "reasoning_effort" in key_texts
    assert "enable_reasoning" not in key_texts

    # Value completion after specific key
    val_texts = _collect_completion_texts(completer, "/set reasoning_effort h")
    assert "high" in val_texts
    assert "low" not in val_texts


def test_switch_session_agent_application_logic(tmp_path: Path) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from agent_terminal_app import terminal as term_mod

    base_dir = Path(term_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    agent_app = AgentApplication(str(config_path), str(session_root), event_store=events)
    term_app = term_mod.TerminalApplication(
        config_path=str(config_path),
        session_root=str(session_root),
        agent_app=agent_app,
    )

    agents = term_app.list_agents()
    assert "default" in agents
    assert len(agents) >= 2

    # Create an initial session using the default agent.
    session = term_app.start_new_session(system_message=None, agent_id="default")
    metadata = session.metadata or {}
    initial_agent = metadata.get("agent_id")
    assert initial_agent == "default"

    # Decide on a non-default target agent and switch via the application.
    target = next(a for a in agents if a != "default")

    updated_session = term_app.switch_agent(target)
    assert updated_session.metadata.get("agent_id") == target

    loaded = agent_app.load_session(session.session_id)
    assert loaded is not None
    _core2, _base_config2, persisted_session = loaded
    assert persisted_session.metadata.get("agent_id") == target


def test_set_overrides_and_send_request_uses_them(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from agent_terminal_app import terminal as term_mod

    base_dir = Path(term_mod.__file__).resolve().parent
    config_path = base_dir / "config_echo_app.json"
    session_root = tmp_path / "sessions"

    events = InMemoryEventStore()
    agent_app = AgentApplication(str(config_path), str(session_root), event_store=events)
    term_app = term_mod.TerminalApplication(
        config_path=str(config_path),
        session_root=str(session_root),
        agent_app=agent_app,
    )

    # Create a session and update an override via the application.
    session = term_app.start_new_session(system_message=None, agent_id="default")
    updated = term_app.update_override("reasoning_effort", "high")

    overrides = updated.metadata.get("overrides") or {}
    assert overrides.get("reasoning_effort") == "high"

    # Patch AgentApplication.send_request to capture overrides passed in.
    captured: dict = {}

    def _fake_send_request(self, core, session_obj, base_cfg, overrides_arg, *, stream=False, request_id=None):  # type: ignore[override]
        captured["overrides"] = overrides_arg
        # Minimal final event structure for TerminalApplication.send_request.
        yield {
            "type": "final",
            "session": session_obj.to_dict(),
            "messages": [],
            "request_id": "req-1",
        }

    monkeypatch.setattr(AgentApplication, "send_request", _fake_send_request, raising=True)

    # Invoke TerminalApplication.send_request; it should
    # pull overrides from session.metadata["overrides"].
    final_session_dict, messages, request_id = term_app.send_request(
        stream=True,
    )

    assert captured["overrides"] == {"reasoning_effort": "high"}
    assert final_session_dict is not None
