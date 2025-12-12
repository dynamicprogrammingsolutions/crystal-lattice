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
from prompt_toolkit.completion import Completer

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

    # 1) Create a new active session and add a system message.
    session = term_app.start_new_session(agent_id="default")
    term_app.add_message(session.session_id, role="system", content=system_message, metadata=None)
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

    # Subcommand completion for /help.
    help_subs = _collect_completion_texts(completer, "/help ")
    assert "config" in help_subs

    # After a space plus additional text, no completion is offered for
    # unknown subcommands.
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


def test_plugins_completion_subcommands_and_ids() -> None:
    from agent_terminal_app import terminal as term_mod

    class _DummyApp:
        def list_plugins_for_session(self) -> list[dict]:
            return [
                {
                    "kind": "providers",
                    "id": "echo_openai_like",
                    "enabled": True,
                    "source": "implicit",
                },
                {
                    "kind": "extensions",
                    "id": "delay_extension",
                    "enabled": True,
                    "source": "implicit",
                },
            ]

    app = _DummyApp()
    completer = term_mod.SlashCommandCompleter(lambda: app)  # type: ignore[arg-type]

    # Subcommand completion
    sub_texts = _collect_completion_texts(completer, "/plugins o")
    assert "on" in sub_texts
    assert "off" in sub_texts
    assert "reset" not in sub_texts

    # Plugin id completion after a subcommand
    id_texts = _collect_completion_texts(completer, "/plugins on d")
    assert "delay_extension" in id_texts
    assert "echo_openai_like" not in id_texts


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
    session = term_app.start_new_session(agent_id="default")
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
    session = term_app.start_new_session(agent_id="default")
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


def test_delete_messages_by_index_and_range(tmp_path: Path) -> None:
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

    # Create a session with a system message and three user messages.
    session = term_app.start_new_session(agent_id="default")
    term_app.add_message(session.session_id, role="system", content="system", metadata=None)
    term_app.append_user_message("one")
    term_app.append_user_message("two")
    term_app.append_user_message("three")

    contents = [m.content for m in term_app.session.messages]
    assert contents == ["system", "one", "two", "three"]

    # Delete a single message by index (remove "two").
    updated = term_app.delete_messages([2])
    contents_single = [m.content for m in updated.messages]
    assert contents_single == ["system", "one", "three"]

    # Delete a range using positive indices (remove "one" and "three").
    updated_range = term_app.delete_messages([1, 2])
    contents_range = [m.content for m in updated_range.messages]
    assert contents_range == ["system"]

    # Check that a messages_deleted event was recorded.
    events_list = term_app.poll_new_events(limit=100)
    kinds = {ev.get("type") for ev in events_list}
    assert "messages_deleted" in kinds


@pytest.mark.asyncio
async def test_delete_slash_command_negative_range(tmp_path: Path) -> None:
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

    # Session with a system message and three user messages.
    session = term_app.start_new_session(agent_id="default")
    term_app.add_message(session.session_id, role="system", content="system", metadata=None)

    session_id = session.session_id

    term_app.append_user_message("one")

    # Modify the session externally via the shared AgentApplication.
    ctx = agent_app.load_session(session_id)
    assert ctx is not None
    _core, _base_config, loaded_session = ctx
    updated_session = _core.add_message(loaded_session, "user", "external")
    agent_app.save_session(updated_session)

    # Listing should reload the latest session and include the external message.
    items = term_app.list_messages_by_range(0, None)
    contents = [msg.content for _idx, msg in items]
    assert contents[-2:] == ["one", "external"]


@pytest.mark.asyncio
async def test_list_slash_command_shows_thinking_and_tools(tmp_path: Path) -> None:
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

    session = term_app.start_new_session(agent_id="default")
    term_app.add_message(session.session_id, role="system", content="system", metadata=None)
    session_id = session.session_id

    term_app.append_user_message("one")
    term_app.append_user_message("two")
    term_app.append_user_message("three")

    # Add assistant and tool messages with metadata so list formatting can be exercised.
    term_app.add_message(
        session_id,
        role="assistant",
        content="with reasoning",
        metadata={"reasoning": "step1; step2"},
    )
    term_app.add_message(
        session_id,
        role="assistant",
        content="with tools",
        metadata={
            "tool_calls": [
                {
                    "type": "function",
                    "function": {"name": "read_file", "arguments": '{"path": "x"}'},
                }
            ]
        },
    )
    term_app.add_message(
        session_id,
        role="tool",
        content="ok",
        metadata={"tool_call_id": "tc1"},
    )

    outputs: list[str] = []
    ui_state: dict = {}

    # /list 3 should show the last three messages: assistant with reasoning,
    # assistant with tools, and tool result.
    await term_mod._cmd_list(term_app, "3", outputs.append, ui_state)

    joined = "\n".join(outputs)
    assert "thinking: step1; step2" in joined
    assert "tools: 1 call(s): read_file" in joined
    assert "tool_call_id: tc1" in joined

def test_list_sessions_metadata_and_session_completion(tmp_path: Path) -> None:
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

    # Create two sessions with distinct first user messages.
    s1 = term_app.start_new_session(agent_id="default")
    term_app.add_message(s1.session_id, role="system", content="system1", metadata=None)
    term_app.append_user_message("first session message")

    s2 = term_app.start_new_session(agent_id="default")
    term_app.add_message(s2.session_id, role="system", content="system2", metadata=None)
    term_app.append_user_message("second session message that is longer")

    # Force modification times so that s2 is the most recent.
    path1 = session_root / f"{s1.session_id}.json"
    path2 = session_root / f"{s2.session_id}.json"
    assert path1.exists() and path2.exists()

    import os
    import time

    now = time.time()
    os.utime(path1, (now - 10, now - 10))
    os.utime(path2, (now, now))

    # list_sessions_metadata should return sessions ordered by mtime desc.
    meta = term_app.list_sessions_metadata()
    ids = [entry["session_id"] for entry in meta]
    assert ids[0] == s2.session_id
    assert set(ids) == {s1.session_id, s2.session_id}

    # The preview should contain the first user message content.
    previews = {entry["session_id"]: entry["preview"] for entry in meta}
    assert "first session message" in previews[s1.session_id]
    assert "second session message" in previews[s2.session_id]

    # SlashCommandCompleter should suggest sessions without a typed prefix.
    completer = term_mod.SlashCommandCompleter(lambda: term_app)
    doc = Document(text="/session ", cursor_position=len("/session "))
    completions = list(completer.get_completions(doc, None))

    suggested_ids = [c.text for c in completions]
    assert s2.session_id in suggested_ids
    assert s1.session_id in suggested_ids

    # The first completion should correspond to the most recently modified session.
    assert completions[0].text == s2.session_id
    # And its description (display_meta) should contain the first user message.
    assert "second session message" in completions[0].display_meta_text


def test_at_file_completion_uses_core(tmp_path: Path) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore
    from agent_terminal_app import terminal as term_mod

    base_dir = Path(term_mod.__file__).resolve().parent
    # Use the OpenRouter app-layer config which enables FileContextFeature.
    config_path = base_dir / "config_openrouter_app_layer.json"
    session_root = tmp_path / "sessions"

    # Create a small file tree for completions and expansion.
    working_dir = tmp_path / "work"
    working_dir.mkdir(parents=True, exist_ok=True)
    target_file = working_dir / "foo" / "bar.js"
    target_file.parent.mkdir(parents=True, exist_ok=True)
    target_file.write_text("console.log('hello');\n", encoding="utf-8")

    events = InMemoryEventStore()
    agent_app = AgentApplication(str(config_path), str(session_root), event_store=events)
    term_app = term_mod.TerminalApplication(
        config_path=str(config_path),
        session_root=str(session_root),
        agent_app=agent_app,
    )

    # Override working_directory via overrides so the feature searches our temp tree.
    session = term_app.start_new_session(agent_id="default")
    md = session.metadata or {}
    overrides = md.get("overrides") or {}
    overrides["working_directory"] = str(working_dir)
    new_metadata = {**md, "overrides": overrides}
    term_app._session = type(session)(
        session_id=session.session_id,
        messages=session.messages,
        metadata=new_metadata,
    )

    completer = term_mod.SlashCommandCompleter(lambda: term_app)
    # Simulate typing an @file prefix.
    doc = Document(text="@file:bar", cursor_position=len("@file:bar"))
    completions = list(completer.get_completions(doc, None))

    # At least one completion should be offered and display the relative path.
    assert completions
    assert any("foo/bar.js" in c.display_text for c in completions)

def test_modify_message_application_emits_event(tmp_path: Path) -> None:
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

    session = term_app.start_new_session(agent_id="default")
    term_app.add_message(session.session_id, role="system", content="system", metadata=None)
    term_app.append_user_message("one")
    term_app.append_user_message("two")

    updated = term_app.modify_message(1, "one-edited")
    contents = [m.content for m in updated.messages]
    assert contents == ["system", "one-edited", "two"]

    events_list = term_app.list_events(session_id=session.session_id, limit=50)
    kinds = {ev.get("type") for ev in events_list}
    assert "message_modified" in kinds
    modified_events = [ev for ev in events_list if ev.get("type") == "message_modified"]
    assert any(ev.get("index") == 1 and ev.get("content") == "one-edited" for ev in modified_events)


@pytest.mark.asyncio
async def test_append_slash_command_appends_with_roles(tmp_path: Path) -> None:
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

    session = term_app.start_new_session(agent_id="default")
    term_app.add_message(session.session_id, role="system", content="system", metadata=None)

    outputs: list[str] = []
    ui_state: dict = {}

    # Explicit user, system, assistant roles plus default user role.
    await term_mod._cmd_append(term_app, "user first", outputs.append, ui_state)
    await term_mod._cmd_append(term_app, "system sys-msg", outputs.append, ui_state)
    await term_mod._cmd_append(term_app, "assistant reply", outputs.append, ui_state)
    await term_mod._cmd_append(term_app, "plain-user", outputs.append, ui_state)

    contents = [m.content for m in term_app.session.messages]
    roles = [m.role for m in term_app.session.messages]

    assert contents == ["system", "first", "sys-msg", "reply", "plain-user"]
    assert roles == ["system", "user", "system", "assistant", "user"]

    events_list = term_app.list_events(session_id=session.session_id, limit=50)
    kinds = {ev.get("type") for ev in events_list}
    assert "message_appended" in kinds


@pytest.mark.asyncio
async def test_append_shortcut_appends_user_message(tmp_path: Path) -> None:
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

    session = term_app.start_new_session(agent_id="default")
    term_app.add_message(session.session_id, role="system", content="system", metadata=None)

    outputs: list[str] = []
    ui_state: dict = {}

    await term_mod._shortcut_append_current_input(
        term_app,
        "shortcut message",
        outputs.append,
        ui_state,
    )

    contents = [m.content for m in term_app.session.messages]
    roles = [m.role for m in term_app.session.messages]

    assert contents == ["system", "shortcut message"]
    assert roles == ["system", "user"]


@pytest.mark.asyncio
async def test_send_slash_command_resends_with_current_history(tmp_path: Path) -> None:
    import asyncio

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

    session = term_app.start_new_session(agent_id="default")
    term_app.add_message(session.session_id, role="system", content="system", metadata=None)
    term_app.append_user_message("hello")

    outputs: list[str] = []
    ui_state: dict = {}

    await term_mod._cmd_send(term_app, "", outputs.append, ui_state)

    # Allow background request to run.
    await asyncio.sleep(0.1)

    events_list = term_app.list_events(session_id=session.session_id, limit=100)
    kinds = {ev.get("type") for ev in events_list}
    assert "request_started" in kinds or "final" in kinds

    joined = "\n".join(outputs)
    assert "[send] request started for current session" in joined


def test_list_plugins_for_session_implicit_defaults(tmp_path: Path) -> None:
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

    session = term_app.start_new_session(agent_id="default")

    plugins = term_app.list_plugins_for_session()
    ids_by_kind: dict[str, list[str]] = {}
    sources: set[str] = set()
    for entry in plugins:
        kind = entry["kind"]
        pid = entry["id"]
        ids_by_kind.setdefault(kind, []).append(pid)
        assert entry["enabled"] is True
        sources.add(entry["source"])

    # config_echo_app.json registers one provider and two extensions.
    assert ids_by_kind["providers"] == ["echo_openai_like"]
    assert ids_by_kind["extensions"] == [
        "delay_extension",
        "random_failure_extension",
    ]
    assert "features" not in ids_by_kind or ids_by_kind["features"] == []
    assert "tools" not in ids_by_kind or ids_by_kind["tools"] == []

    # With no explicit agent or session plugin list, the effective
    # enabled set is implicit and all plugins are enabled.
    assert sources == {"implicit"}
    assert "plugins" not in (session.metadata or {})


def test_set_session_plugins_persists_and_reloads_core(tmp_path: Path) -> None:
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

    session = term_app.start_new_session(agent_id="default")
    session_id = session.session_id

    # Restrict the session to the provider plugin only.
    updated = term_app.set_session_plugins(["echo_openai_like"])
    assert updated.session_id == session_id
    md = updated.metadata or {}
    assert md.get("plugins") == ["echo_openai_like"]

    # Persisted session in the AgentApplication should see the same list.
    ctx = agent_app.load_session(session_id)
    assert ctx is not None
    _core2, _base_config2, persisted = ctx
    assert (persisted.metadata or {}).get("plugins") == ["echo_openai_like"]

    # The core attached to the terminal application should now have a
    # provider with no extensions attached.
    core, _base_config, active_session = term_app.require_session()
    assert active_session.session_id == session_id

    providers = getattr(core, "_providers")
    assert len(providers) == 1
    provider_wrapper = providers[0]
    assert provider_wrapper.name == "echo_openai_like"
    assert provider_wrapper.extensions == []

    # list_plugins_for_session should now report only the provider as
    # enabled, with a "session" source; extensions are disabled.
    entries = term_app.list_plugins_for_session()
    by_id = {entry["id"]: entry for entry in entries}
    assert by_id["echo_openai_like"]["enabled"] is True
    assert by_id["echo_openai_like"]["source"] == "session"
    assert by_id["delay_extension"]["enabled"] is False
    assert by_id["delay_extension"]["source"] == "session"
    assert by_id["random_failure_extension"]["enabled"] is False
    assert by_id["random_failure_extension"]["source"] == "session"


def test_clear_session_plugins_reverts_to_implicit_defaults(tmp_path: Path) -> None:
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

    session = term_app.start_new_session(agent_id="default")
    session_id = session.session_id

    # First, set an explicit plugin list so metadata contains "plugins".
    _ = term_app.set_session_plugins(["echo_openai_like"])

    cleared = term_app.clear_session_plugins()
    assert cleared.session_id == session_id
    md_cleared = cleared.metadata or {}
    assert "plugins" not in md_cleared

    # The persisted session should no longer have a "plugins" key.
    ctx = agent_app.load_session(session_id)
    assert ctx is not None
    _core2, _base_config2, persisted = ctx
    assert "plugins" not in (persisted.metadata or {})

    # The reloaded core should again have both extensions attached to
    # the single provider.
    core, _base_config, active_session = term_app.require_session()
    assert active_session.session_id == session_id

    providers = getattr(core, "_providers")
    assert len(providers) == 1
    provider_wrapper = providers[0]
    ext_names = [ext.name for ext in provider_wrapper.extensions]
    assert sorted(ext_names) == ["delay_extension", "random_failure_extension"]

    # list_plugins_for_session should report all plugins enabled with an
    # implicit source, matching the initial default behaviour.
    entries = term_app.list_plugins_for_session()
    assert all(entry["enabled"] for entry in entries)
    assert {entry["source"] for entry in entries} == {"implicit"}


@pytest.mark.asyncio
async def test_plugins_slash_command_lists_and_toggles(tmp_path: Path) -> None:
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

    session = term_app.start_new_session(agent_id="default")
    session_id = session.session_id

    outputs: list[str] = []
    ui_state: dict = {}

    # Initial listing should show provider and both extensions and
    # populate plugins_last_list in ui_state.
    await term_mod._cmd_plugins(term_app, "", outputs.append, ui_state)
    joined = "\n".join(outputs)
    assert "echo_openai_like" in joined
    assert "delay_extension" in joined
    assert "random_failure_extension" in joined

    last_list = ui_state.get("plugins_last_list")
    assert isinstance(last_list, list)
    assert [entry["id"] for entry in last_list] == [
        "echo_openai_like",
        "delay_extension",
        "random_failure_extension",
    ]

    # Disable the first extension by index.
    outputs.clear()
    await term_mod._cmd_plugins(term_app, "off 2", outputs.append, ui_state)

    # Session metadata should now contain a plugins list with the
    # provider and the remaining extension enabled.
    md = term_app.session.metadata or {}
    assert md.get("plugins") == ["echo_openai_like", "random_failure_extension"]

    core, _base_config, active_session = term_app.require_session()
    assert active_session.session_id == session_id

    providers = getattr(core, "_providers")
    assert len(providers) == 1
    provider_wrapper = providers[0]
    assert provider_wrapper.name == "echo_openai_like"
    ext_names = [ext.name for ext in provider_wrapper.extensions]
    assert ext_names == ["random_failure_extension"]

    # Disable the remaining extension by id.
    outputs.clear()
    await term_mod._cmd_plugins(
        term_app,
        "off random_failure_extension",
        outputs.append,
        ui_state,
    )

    md2 = term_app.session.metadata or {}
    assert md2.get("plugins") == ["echo_openai_like"]

    core_after_off, _base_config_after_off, active_session_after_off = term_app.require_session()
    assert active_session_after_off.session_id == session_id
    providers_after_off = getattr(core_after_off, "_providers")
    assert len(providers_after_off) == 1
    provider_wrapper_after_off = providers_after_off[0]
    assert provider_wrapper_after_off.extensions == []

    # Reset should clear session-specific overrides and restore
    # extensions.
    outputs.clear()
    await term_mod._cmd_plugins(term_app, "reset", outputs.append, ui_state)

    md_cleared = term_app.session.metadata or {}
    assert "plugins" not in md_cleared

    core2, _base_config2, active_session2 = term_app.require_session()
    assert active_session2.session_id == session_id
    providers2 = getattr(core2, "_providers")
    assert len(providers2) == 1
    provider_wrapper2 = providers2[0]
    ext_names2 = [ext.name for ext in provider_wrapper2.extensions]
    assert sorted(ext_names2) == ["delay_extension", "random_failure_extension"]
