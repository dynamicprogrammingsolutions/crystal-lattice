from __future__ import annotations

import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional

import pytest
from prompt_toolkit.document import Document

from agent_app.application_future import AgentApplication
from agent_core import Message, Session
from agent_terminal_app import terminal as terminal_mod
from agent_terminal_app.terminal_app import TerminalApplication, TerminalUserError

from plugins.echo_openai_like_provider import EchoOpenAILikeProvider  # noqa: F401


ROOT = Path(__file__).resolve().parents[3]


class TerminalFiltersPlugin:
    name = "terminal_filters"
    version = "1.0.0"

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        _ = app_config
        return {}

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return []

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = state, config, context
        return [
            {
                "ui_type": "session_list_field",
                "id": "title",
                "role": "title",
                "data": "metadata.title",
                "order": 0,
            },
            {
                "ui_type": "session_list_filter",
                "id": "session_search",
                "label": "Search",
                "data": [
                    "session_id",
                    "preview",
                    "presentation.title",
                ],
                "type": "text",
                "match": "contains",
                "main_search": True,
                "order": 0,
            },
            {
                "ui_type": "session_list_filter",
                "id": "archived",
                "label": "Archived",
                "data": "metadata.archived",
                "type": "boolean",
                "match": "equals",
                "missing_value": False,
                "default": False,
                "order": 10,
            },
            {
                "ui_type": "session_list_filter",
                "id": "owner",
                "label": "Owner",
                "data": "metadata.owner",
                "type": "select",
                "match": "equals",
                "options": [
                    {"value": "alice", "label": "Alice"},
                    {"value": "bob", "label": "Bob"},
                ],
                "order": 20,
            },
            {
                "ui_type": "session_list_filter",
                "id": "status",
                "label": "Status",
                "data": "metadata.status",
                "type": "select",
                "match": "one_of",
                "multiple": True,
                "options": [
                    {"value": "todo", "label": "To do"},
                    {"value": "blocked", "label": "Blocked"},
                    {"value": "done", "label": "Done"},
                    {"value": "needs,review", "label": "Needs review"},
                ],
                "order": 30,
            },
            {
                "ui_type": "session_list_filter",
                "id": "note",
                "label": "Note",
                "data": "metadata.note",
                "type": "text",
                "match": "equals",
                "order": 40,
            },
        ]

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = app, params, context, state
        raise ValueError(action_id)


def _make_terminal(
    tmp_path: Path,
    *,
    with_filters: bool = True,
) -> tuple[TerminalApplication, AgentApplication, Path]:
    plugins = ["plugins.echo_openai_like_provider.EchoOpenAILikeProvider"]
    if with_filters:
        plugins.append("test_terminal_session_filters.TerminalFiltersPlugin")
    config = {
        "providers": {
            "echo": {
                "provider": "echo_openai_like",
                "model": "test-model",
            }
        },
        "plugins": plugins,
        "agents": {"default": {"provider": "echo"}},
    }
    config_path = tmp_path / "config.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    session_root = tmp_path / "sessions"
    application = AgentApplication(config_path, session_root)
    terminal = TerminalApplication(
        config_path=config_path,
        session_root=session_root,
        agent_app=application,
    )
    return terminal, application, session_root


def _make_builtin_filter_terminal(
    tmp_path: Path,
) -> tuple[TerminalApplication, AgentApplication, Path]:
    config = {
        "providers": {
            "echo": {
                "provider": "echo_openai_like",
                "model": "test-model",
            }
        },
        "plugins": [
            "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
            f"path:{ROOT / 'plugins' / 'session-main-search-app'}",
            f"path:{ROOT / 'plugins' / 'session-pinned-app'}",
            f"path:{ROOT / 'plugins' / 'session-status-app'}",
        ],
        "agents": {"default": {"provider": "echo"}},
    }
    config_path = tmp_path / "config-built-in-filters.json"
    config_path.write_text(json.dumps(config), encoding="utf-8")
    session_root = tmp_path / "sessions-built-in-filters"
    application = AgentApplication(config_path, session_root)
    terminal = TerminalApplication(
        config_path=config_path,
        session_root=session_root,
        agent_app=application,
    )
    return terminal, application, session_root


def _save(
    application: AgentApplication,
    *,
    session_id: str,
    preview: str,
    metadata: Dict[str, Any],
) -> None:
    application.save_session(
        Session(
            session_id=session_id,
            messages=(
                Message(role="system", content="system"),
                Message(role="user", content=preview),
            ),
            metadata={"agent_id": "default", **metadata},
        )
    )


def _seed(
    application: AgentApplication,
    session_root: Path,
) -> None:
    _save(
        application,
        session_id="visible-alpha",
        preview="ordinary preview",
        metadata={
            "title": "Alpha planning",
            "owner": "alice",
            "status": "todo",
            "note": "one",
        },
    )
    _save(
        application,
        session_id="visible-beta",
        preview="Beta blocked work",
        metadata={
            "owner": "bob",
            "status": "blocked",
            "note": "two",
        },
    )
    _save(
        application,
        session_id="hidden-archived",
        preview="Alpha archive",
        metadata={
            "archived": True,
            "owner": "alice",
            "status": "done",
            "note": "one",
        },
    )
    now = time.time()
    for index, session_id in enumerate(
        ["visible-alpha", "visible-beta", "hidden-archived"],
        1,
    ):
        os.utime(
            session_root / f"{session_id}.json",
            (now + index, now + index),
        )


@pytest.mark.asyncio
async def test_session_command_defaults_search_filters_and_exact_id(
    tmp_path: Path,
) -> None:
    terminal, application, session_root = _make_terminal(tmp_path)
    try:
        _seed(application, session_root)
        command = terminal_mod.get_slash_command("session")
        assert command is not None

        output: List[str] = []
        ui_state: Dict[str, Any] = {}
        await command.handler(terminal, "", output.append, ui_state)
        assert ui_state["pending_session_choices"] == [
            "visible-beta",
            "visible-alpha",
        ]

        output.clear()
        await command.handler(terminal, "ALPHA", output.append, ui_state)
        assert ui_state["pending_session_choices"] == ["visible-alpha"]

        output.clear()
        await command.handler(
            terminal,
            "--filter archived=any --filter owner=alice "
            "--filter status=todo,done --filter note=one Alpha",
            output.append,
            ui_state,
        )
        assert ui_state["pending_session_choices"] == [
            "hidden-archived",
            "visible-alpha",
        ]
        terminal_mod._handle_session_selection(
            terminal,
            "2",
            output.append,
            ui_state,
        )
        assert terminal.session_id == "visible-alpha"

        with pytest.raises(
            TerminalUserError,
            match="no sessions match",
        ):
            await command.handler(terminal, "does-not-match", output.append, ui_state)

        output.clear()
        await command.handler(
            terminal,
            "--filter archived=false hidden-archived",
            output.append,
            ui_state,
        )
        assert terminal.session_id == "hidden-archived"
        assert "switched" in "\n".join(output)
    finally:
        terminal.close()


def test_terminal_filter_values_are_command_local_and_invalid_values_error(
    tmp_path: Path,
) -> None:
    terminal, application, session_root = _make_terminal(tmp_path)
    try:
        _seed(application, session_root)
        archived = terminal.query_sessions_metadata(filter_inputs={"archived": "true"})
        assert [item["session_id"] for item in archived] == ["hidden-archived"]

        defaults = terminal.query_sessions_metadata()
        assert [item["session_id"] for item in defaults] == [
            "visible-beta",
            "visible-alpha",
        ]

        csv_quoted = terminal.query_sessions_metadata(
            filter_inputs={"status": '"needs,review",todo'}
        )
        assert [item["session_id"] for item in csv_quoted] == ["visible-alpha"]

        with pytest.raises(TerminalUserError, match="unknown session filter"):
            terminal.query_sessions_metadata(filter_inputs={"unknown": "value"})
        with pytest.raises(TerminalUserError, match="any, true, or false"):
            terminal.query_sessions_metadata(filter_inputs={"archived": "maybe"})
        with pytest.raises(TerminalUserError, match="invalid value"):
            terminal.query_sessions_metadata(filter_inputs={"owner": "nobody"})
    finally:
        terminal.close()


def test_session_completion_includes_filter_ids_values_and_matching_ids(
    tmp_path: Path,
) -> None:
    terminal, application, session_root = _make_terminal(tmp_path)
    try:
        _seed(application, session_root)
        completer = terminal_mod.SlashCommandCompleter(lambda: terminal)

        filter_ids = list(
            completer.get_completions(
                Document(
                    text="/session --filter ",
                    cursor_position=len("/session --filter "),
                ),
                None,
            )
        )
        assert "archived=" in {completion.text for completion in filter_ids}
        assert "session_search=" not in {completion.text for completion in filter_ids}

        boolean_values = list(
            completer.get_completions(
                Document(
                    text="/session --filter archived=",
                    cursor_position=len("/session --filter archived="),
                ),
                None,
            )
        )
        assert {completion.text for completion in boolean_values} == {
            "any",
            "true",
            "false",
        }

        matching_ids = list(
            completer.get_completions(
                Document(
                    text="/session Alpha",
                    cursor_position=len("/session Alpha"),
                ),
                None,
            )
        )
        assert [completion.text for completion in matching_ids] == ["visible-alpha"]
    finally:
        terminal.close()


def test_terminal_uses_real_pin_and_status_plugin_declarations(
    tmp_path: Path,
) -> None:
    terminal, application, _session_root = _make_builtin_filter_terminal(tmp_path)
    try:
        _save(
            application,
            session_id="ordinary-todo",
            preview="ordinary",
            metadata={},
        )
        _save(
            application,
            session_id="pinned-blocked",
            preview="blocked",
            metadata={},
        )
        application.execute_application_action(
            plugin_id="session_pinned",
            action_id="toggle_session_pinned",
            params={"session_id": "pinned-blocked"},
        )
        application.execute_application_action(
            plugin_id="session_status",
            action_id="set_session_status",
            params={
                "session_id": "pinned-blocked",
                "status": "blocked",
            },
        )

        pinned = terminal.query_sessions_metadata(
            filter_inputs={"pinned_state": "true"}
        )
        assert [item["session_id"] for item in pinned] == ["pinned-blocked"]

        not_pinned = terminal.query_sessions_metadata(
            filter_inputs={"pinned_state": "false"}
        )
        assert [item["session_id"] for item in not_pinned] == ["ordinary-todo"]

        todo = terminal.query_sessions_metadata(
            filter_inputs={"session_status": "todo"}
        )
        assert [item["session_id"] for item in todo] == ["ordinary-todo"]

        both_statuses = terminal.query_sessions_metadata(
            filter_inputs={"session_status": "todo,blocked"}
        )
        assert {item["session_id"] for item in both_statuses} == {
            "ordinary-todo",
            "pinned-blocked",
        }

        assert terminal.session_filter_completion_values("pinned_state") == [
            "any",
            "true",
            "false",
        ]
        assert terminal.session_filter_completion_values("session_status") == [
            "any",
            "todo",
            "in_progress",
            "blocked",
            "done",
        ]
    finally:
        terminal.close()


@pytest.mark.asyncio
async def test_terminal_without_main_search_still_allows_exact_id(
    tmp_path: Path,
) -> None:
    terminal, application, session_root = _make_terminal(tmp_path, with_filters=False)
    try:
        _save(
            application,
            session_id="exact-only",
            preview="preview",
            metadata={},
        )
        command = terminal_mod.get_slash_command("session")
        assert command is not None

        with pytest.raises(
            TerminalUserError,
            match="requires a main-search plugin",
        ):
            await command.handler(terminal, "preview", lambda _: None, {})

        output: List[str] = []
        await command.handler(terminal, "exact-only", output.append, {})
        assert terminal.session_id == "exact-only"
    finally:
        terminal.close()
