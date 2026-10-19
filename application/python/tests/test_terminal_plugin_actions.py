from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
from types import SimpleNamespace

import pytest
from prompt_toolkit.completion import CompleteEvent
from prompt_toolkit.document import Document

from agent_app.application_future import AgentApplication
from agent_app.application_notifications import InMemoryApplicationNotificationStore
from agent_app.command_ui import CommandCatalogError, build_command_catalog
from agent_app.events import InMemoryEventStore
from agent_terminal_app import terminal
from agent_terminal_app.terminal_app import TerminalApplication, TerminalUserError


def _config(
    tmp_path: Path,
    *,
    slash_path: list[str] | None = None,
) -> Path:
    path = tmp_path / "config.json"
    path.write_text(
        json.dumps(
            {
                "providers": {
                    "echo": {
                        "provider": "echo_openai_like",
                        "model": "test-model",
                    }
                },
                "plugins": [
                    "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
                    "fixtures.terminal_action_app_plugin.TerminalActionAppPlugin",
                ],
                "agents": {"default": {"provider": "echo"}},
                "application": {
                    "terminal_action_fixture": {
                        "slash_path": slash_path or ["fixture", "record"],
                    }
                },
            }
        ),
        encoding="utf-8",
    )
    return path


def _terminal(
    tmp_path: Path,
    *,
    event_store: InMemoryEventStore | None = None,
    notification_store: InMemoryApplicationNotificationStore | None = None,
) -> tuple[TerminalApplication, AgentApplication]:
    config = _config(tmp_path)
    app = AgentApplication(
        config,
        tmp_path / "sessions",
        event_store=event_store or InMemoryEventStore(),
        application_notification_store=(
            notification_store or InMemoryApplicationNotificationStore()
        ),
    )
    frontend = TerminalApplication(
        config_path=config,
        session_root=tmp_path / "sessions",
        agent_app=app,
    )
    frontend.start_new_session("default")
    return frontend, app


def _calls(app: AgentApplication) -> list[dict]:
    return app._app_plugins["terminal_action_fixture"].state["calls"]


def test_public_cli_resolves_nested_command_path(tmp_path: Path) -> None:
    config = _config(tmp_path)
    env = os.environ.copy()
    python_paths = [
        str(Path(__file__).resolve().parents[1]),
        str(Path(__file__).resolve().parents[3] / "core" / "python"),
        str(Path(__file__).resolve().parent),
    ]
    if env.get("PYTHONPATH"):
        python_paths.append(env["PYTHONPATH"])
    env["PYTHONPATH"] = os.pathsep.join(python_paths)

    completed = subprocess.run(
        [
            sys.executable,
            "-m",
            "agent_terminal_app",
            "--config",
            str(config),
            "--sessions-dir",
            str(tmp_path / "cli-sessions"),
            "fixture",
            "record",
            "--value",
            "cli",
            "--count",
            "7",
        ],
        cwd=tmp_path,
        env=env,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )

    assert completed.returncode == 0, completed.stderr
    assert "Recorded cli" in completed.stdout
    assert "[success] Recorded" in completed.stdout


def test_standalone_foreground_interrupt_cancels_once_and_exits_130(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    calls: list[tuple[str, dict]] = []

    class _App:
        def execute_action_with_metadata(
            self,
            _plugin: str,
            action_id: str,
            params: dict,
            **_kwargs: object,
        ) -> SimpleNamespace:
            calls.append((action_id, dict(params)))
            states = {
                "start": "pending",
                "status": "pending",
                "cancel": "canceled",
            }
            return SimpleNamespace(
                result={
                    "auth_status": {
                        "login_id": "attempt-1",
                        "state": states[action_id],
                    }
                }
            )

    command = {
        "plugin": "fixture",
        "action_id": "start",
        "foreground": {
            "attempt_id_path": "auth_status.login_id",
            "state_path": "auth_status.state",
            "pending_states": ["pending"],
            "success_states": ["authenticated"],
            "failure_states": ["failed"],
            "cancelled_states": ["canceled"],
            "expired_states": ["expired"],
            "poll_interval_seconds": 0.1,
            "status": {"action_id": "status", "attempt_param": "login_id"},
            "cancel": {"action_id": "cancel", "attempt_param": "login_id"},
        },
    }
    monkeypatch.setattr(
        "agent_terminal_app.__main__.time.sleep",
        lambda _interval: (_ for _ in ()).throw(KeyboardInterrupt()),
    )

    from agent_terminal_app.__main__ import _run_standalone_command_element

    with pytest.raises(SystemExit) as exc_info:
        _run_standalone_command_element(_App(), command, {})

    assert exc_info.value.code == 130
    assert calls == [
        ("start", {}),
        ("cancel", {"login_id": "attempt-1"}),
    ]


def test_standalone_help_never_exposes_sensitive_form_flags(
    capsys: pytest.CaptureFixture[str],
) -> None:
    from agent_terminal_app.__main__ import _parse_command_ui_args

    command = {
        "path": ["fixture", "sensitive"],
        "dialog": {
            "kind": "form",
            "inputs": [
                {"name": "visible", "type": "text"},
                {"name": "token", "type": "secret", "required": True},
                {"name": "password", "type": "password"},
            ],
        },
    }
    with pytest.raises(SystemExit) as help_exit:
        _parse_command_ui_args(command, {}, ["--help"])

    assert help_exit.value.code == 0
    output = capsys.readouterr().out
    assert "--visible" in output
    assert "--token" not in output
    assert "--password" not in output


def test_command_catalog_separates_frontends_and_reports_collisions() -> None:
    elements = [
        {
            "ui_type": "cli_command",
            "plugin": "one",
            "id": "one",
            "path": ["same"],
            "action_id": "run",
        },
        {
            "ui_type": "slash_command",
            "plugin": "one",
            "id": "slash",
            "path": ["same"],
            "action_id": "run",
        },
    ]
    assert len(build_command_catalog(elements, ui_type="cli_command")) == 1
    assert len(build_command_catalog(elements, ui_type="slash_command")) == 1

    with pytest.raises(CommandCatalogError, match="same: built-in, one.one"):
        build_command_catalog(
            elements,
            ui_type="cli_command",
            reserved_paths=[("same",)],
        )
    nested = [{**elements[0], "path": ["same", "nested"]}]
    with pytest.raises(
        CommandCatalogError,
        match="same nested: built-in, one.one",
    ):
        build_command_catalog(
            nested,
            ui_type="cli_command",
            reserved_paths=[("same",)],
        )


@pytest.mark.asyncio
async def test_dynamic_slash_help_and_completion_use_current_catalog(
    tmp_path: Path,
) -> None:
    frontend, _app = _terminal(tmp_path)
    output: list[str] = []

    await terminal._cmd_help(frontend, "", output.append, {})
    assert any("/fixture record" in line for line in output)
    assert any("aliases: /record fixture" in line for line in output)
    argument_help = next(line for line in output if "arguments:" in line)
    assert "text=VALUE" in argument_help
    assert "secret" not in argument_help
    assert "password" not in argument_help

    completer = terminal.SlashCommandCompleter(lambda: frontend)
    first = list(completer.get_completions(Document("/fi"), CompleteEvent()))
    second = list(completer.get_completions(Document("/fixture r"), CompleteEvent()))
    alias = list(completer.get_completions(Document("/rec"), CompleteEvent()))
    argument = list(
        completer.get_completions(
            Document("/fixture record te"),
            CompleteEvent(),
        )
    )
    sensitive_argument = list(
        completer.get_completions(
            Document("/fixture record se"),
            CompleteEvent(),
        )
    )
    assert [item.text for item in first] == ["fixture"]
    assert [item.text for item in second] == ["record"]
    assert [item.text for item in alias] == ["record"]
    assert [item.text for item in argument] == ["text="]
    assert sensitive_argument == []


@pytest.mark.asyncio
async def test_form_context_prefill_beats_default_and_secret_is_never_prefilled() -> (
    None
):
    values = await terminal._collect_action_form(
        {
            "kind": "form",
            "inputs": [
                {
                    "name": "value",
                    "type": "text",
                    "prefill_from": "$session.metadata.value",
                    "default": "default",
                },
                {
                    "name": "password",
                    "type": "password",
                    "default": "must-not-prefill",
                },
            ],
        },
        context={"session": {"metadata": {"value": "prefilled"}}},
        inline_values=None,
        ui_state={"action_responses": ["", "typed-password"]},
    )

    assert values == {
        "value": "prefilled",
        "password": "typed-password",
    }


@pytest.mark.asyncio
async def test_dynamic_slash_and_action_use_same_action_and_ordered_form(
    tmp_path: Path,
) -> None:
    frontend, app = _terminal(tmp_path)
    output: list[str] = []

    await terminal._handle_slash_command(
        frontend,
        (
            "/fixture record text=slash count=3 enabled=yes note=hello "
            "ratio=2.5 choice=beta"
        ),
        output.append,
        {"action_responses": ["slash-secret", "slash-password"]},
    )
    await terminal._cmd_action(
        frontend,
        (
            "--scope session --plugin terminal_action_fixture fixture_session "
            "text=action count=5 enabled=false note=:skip ratio=3 choice=alpha"
        ),
        output.append,
        {"action_responses": ["action-secret", "action-password"]},
    )

    calls = _calls(app)
    assert [call["action_id"] for call in calls] == ["record", "record"]
    assert calls[0]["params"] == {
        "text": "slash",
        "count": 3,
        "enabled": True,
        "ratio": 2.5,
        "choice": "beta",
        "note": "hello",
        "secret": "slash-secret",
        "password": "slash-password",
        "session_id": frontend.session_id,
    }
    assert calls[1]["params"] == {
        "text": "action",
        "count": 5,
        "enabled": False,
        "ratio": 3.0,
        "choice": "alpha",
        "note": "",
        "secret": "action-secret",
        "password": "action-password",
        "session_id": frontend.session_id,
    }
    assert "slash-secret" not in "\n".join(output)
    assert "slash-password" not in "\n".join(output)
    assert "action-secret" not in "\n".join(output)
    assert "action-password" not in "\n".join(output)


@pytest.mark.asyncio
async def test_sensitive_values_are_redacted_from_action_errors(
    tmp_path: Path,
) -> None:
    frontend, app = _terminal(tmp_path)
    output: list[str] = []

    await terminal._handle_slash_command(
        frontend,
        (
            "/fixture record text=raise-sensitive-error count=3 enabled=yes "
            "note=hello ratio=2.5 choice=beta"
        ),
        output.append,
        {"action_responses": ["error-secret-canary", "error-password-canary"]},
    )

    rendered = "\n".join(output)
    assert "error-secret-canary" not in rendered
    assert "error-password-canary" not in rendered
    assert "[redacted]" in rendered
    assert _calls(app) == []


@pytest.mark.asyncio
async def test_action_cancellation_and_disabled_reason_prevent_invocation(
    tmp_path: Path,
) -> None:
    frontend, app = _terminal(tmp_path)
    with pytest.raises(TerminalUserError, match="disabled.*fixture is unavailable"):
        frontend.resolve_action_element(
            "fixture_disabled",
            plugin="terminal_action_fixture",
            scope="session",
        )

    with pytest.raises(TerminalUserError, match="action cancelled"):
        await terminal._cmd_action(
            frontend,
            "--plugin terminal_action_fixture fixture_session",
            lambda _line: None,
            {"action_responses": [None]},
        )
    assert _calls(app) == []


@pytest.mark.parametrize("cancel_position", range(8))
@pytest.mark.asyncio
async def test_form_cancellation_at_each_prompt_prevents_invocation(
    tmp_path: Path,
    cancel_position: int,
) -> None:
    frontend, app = _terminal(tmp_path)
    valid_responses = [
        "text",
        "2",
        "yes",
        "note",
        "secret-canary",
        "password-canary",
        "1.5",
        "alpha",
    ]

    with pytest.raises(TerminalUserError, match="action cancelled"):
        await terminal._cmd_action(
            frontend,
            "--plugin terminal_action_fixture fixture_session",
            lambda _line: None,
            {"action_responses": [*valid_responses[:cancel_position], None]},
        )

    assert _calls(app) == []


@pytest.mark.asyncio
async def test_confirm_cancellation_prevents_invocation(tmp_path: Path) -> None:
    frontend, app = _terminal(tmp_path)

    with pytest.raises(TerminalUserError, match="action cancelled"):
        await terminal._cmd_action(
            frontend,
            "--plugin terminal_action_fixture fixture_confirm",
            lambda _line: None,
            {"action_responses": ["no"]},
        )

    assert _calls(app) == []


@pytest.mark.asyncio
async def test_message_action_uses_list_index_and_condition(tmp_path: Path) -> None:
    frontend, app = _terminal(tmp_path)
    frontend.append_user_message("user")
    frontend.add_message(
        frontend.session_id,
        role="assistant",
        content="assistant",
        metadata=None,
    )

    user_elements = frontend.action_elements(message_index=-2)
    assert [element["id"] for element in user_elements] == [
        "fixture_message",
        "fixture_message_followup",
    ]
    assert frontend.action_elements(message_index=-1) == []

    await terminal._cmd_action(
        frontend,
        "--message -2 --plugin terminal_action_fixture fixture_message",
        lambda _line: None,
        {},
    )
    assert _calls(app)[0]["params"]["message_index"] == 0


def test_action_inventory_excludes_bare_procedures_and_orders_ui_elements(
    tmp_path: Path,
) -> None:
    frontend, _app = _terminal(tmp_path)

    elements = frontend.action_elements()
    assert "bare" not in {element["id"] for element in elements}
    assert [element["id"] for element in elements[:4]] == [
        "fixture_session",
        "fixture_session_list",
        "fixture_application",
        "fixture_disabled",
    ]
    with pytest.raises(TerminalUserError, match="no applicable action element"):
        frontend.resolve_action_element("bare")


@pytest.mark.asyncio
async def test_direct_followup_reference_executes_after_rendering(
    tmp_path: Path,
) -> None:
    frontend, app = _terminal(tmp_path)
    context = frontend.action_context()
    result = frontend.execute_ui_element(
        frontend.resolve_action_element(
            "fixture_show_followup",
            plugin="terminal_action_fixture",
        ),
        context=context,
    )
    output: list[str] = []
    terminal._render_action_result(
        frontend,
        result,
        output.append,
        context=context,
    )
    command_line = next(line for line in output if "/action --ref" in line)
    reference = command_line.rsplit(" ", 1)[-1]

    await terminal._cmd_action(
        frontend,
        f"--ref {reference}",
        output.append,
        {"action_responses": ["later", "6"]},
    )
    assert _calls(app)[0]["params"] == {
        "text": "later",
        "count": 6,
        "enabled": True,
        "ratio": 1.5,
        "choice": "alpha",
        "session_id": frontend.session_id,
    }
    assert frontend.get_action_reference(reference)

    replacement_output: list[str] = []
    terminal._render_action_result(
        frontend,
        result,
        replacement_output.append,
        context=context,
    )
    with pytest.raises(TerminalUserError, match="unknown or expired"):
        frontend.get_action_reference(reference)


@pytest.mark.asyncio
async def test_direct_followup_preserves_message_context_and_nonpreserving_lifetime(
    tmp_path: Path,
) -> None:
    frontend, app = _terminal(tmp_path)
    frontend.append_user_message("user")
    element = frontend.resolve_action_element(
        "fixture_message_followup",
        plugin="terminal_action_fixture",
        message_index=-1,
    )
    context = frontend.action_context(message_index=-1)
    result = frontend.execute_ui_element(element, context=context)
    action = result["display"]["actions"][0]
    action["preserve_display"] = False
    output: list[str] = []
    terminal._render_action_result(
        frontend,
        result,
        output.append,
        context=context,
    )
    reference = next(line for line in output if "/action --ref" in line).rsplit(" ", 1)[
        -1
    ]

    await terminal._cmd_action(
        frontend,
        f"--ref {reference}",
        output.append,
        {"action_responses": ["message", "7"]},
    )

    assert _calls(app)[0]["params"]["message_index"] == 0
    with pytest.raises(TerminalUserError, match="unknown or expired"):
        frontend.get_action_reference(reference)


def test_application_session_and_session_list_scopes_map_only_valid_context(
    tmp_path: Path,
) -> None:
    frontend, app = _terminal(tmp_path)
    context = frontend.action_context()

    session_list = frontend.resolve_action_element(
        "fixture_session_list",
        plugin="terminal_action_fixture",
        scope="session-list",
    )
    frontend.execute_ui_element(session_list, context=context)
    assert _calls(app)[0]["params"] == {
        "text": "session-list",
        "session_id": frontend.session_id,
        "count": 2,
        "enabled": False,
        "ratio": 1.5,
        "choice": "alpha",
    }
    assert _calls(app)[0]["context"]["session_id"] == frontend.session_id

    application = frontend.resolve_action_element(
        "fixture_application",
        plugin="terminal_action_fixture",
        scope="application",
    )
    frontend.execute_ui_element(
        application,
        context=context,
        dialog_values={
            "text": "application",
            "count": 2,
            "enabled": False,
            "note": "",
            "ratio": 1.5,
            "choice": "alpha",
        },
    )
    assert "session_id" not in _calls(app)[1]["params"]
    assert _calls(app)[1]["context"] == {"application_generation": 1}


def test_invalid_followup_binding_is_not_registered(tmp_path: Path) -> None:
    frontend, _app = _terminal(tmp_path)
    output: list[str] = []

    terminal._render_action_result(
        frontend,
        {
            "display": {
                "title": "Invalid",
                "actions": [
                    {
                        "kind": "run_action",
                        "id": "invalid",
                        "plugin": "terminal_action_fixture",
                        "action_id": "missing",
                    }
                ],
            }
        },
        output.append,
        context=frontend.action_context(),
    )

    assert any("unavailable" in line for line in output)
    assert not any("/action --ref" in line for line in output)


def _notification(
    *,
    key: str,
    text: str,
) -> dict:
    return {
        "key": key,
        "severity": "info",
        "title": "Fixture notification",
        "body": text,
        "source": {"plugin": "terminal_action_fixture"},
        "display": {
            "format": "text",
            "title": "Fixture notification",
            "body": text,
            "presentation": "banner",
            "actions": [
                {
                    "kind": "run_action",
                    "id": "notification-record",
                    "label": "Record",
                    "plugin": "terminal_action_fixture",
                    "action_id": "record",
                    "fixed_params": {"text": text},
                }
            ],
        },
        "model_visibility": "hidden",
    }


def test_notification_hydration_dedup_and_authoritative_followup(
    tmp_path: Path,
) -> None:
    frontend, app = _terminal(tmp_path)
    stored = app.create_application_notification(
        _notification(key="fixture:app", text="first")
    )

    updates = frontend.poll_notification_updates()
    assert [item["notification"]["revision"] for item in updates] == [1]
    assert frontend.poll_notification_updates() == []

    context = frontend.action_context()
    output: list[str] = []
    terminal._render_action_result(
        frontend,
        {"display": stored["display"]},
        output.append,
        context=context,
        notification={
            "scope": "application",
            "session_id": None,
            "notification_id": stored["id"],
            "revision": stored["revision"],
        },
    )
    reference = next(line for line in output if "/action --ref" in line).rsplit(" ", 1)[
        -1
    ]

    updated = app.update_application_notification(
        stored["id"],
        {"body": "second", "display": _notification(key="x", text="second")["display"]},
        expected_revision=stored["revision"],
    )
    assert [
        item["notification"]["revision"]
        for item in frontend.poll_notification_updates()
    ] == [updated["revision"]]

    result, _element, _context = frontend.execute_action_reference(reference)
    assert result["record"]["params"]["text"] == "second"

    app.resolve_application_notification(
        stored["id"],
        expected_revision=updated["revision"],
    )
    frontend.poll_notification_updates()
    with pytest.raises(TerminalUserError, match="unknown or expired"):
        frontend.get_action_reference(reference)


@pytest.mark.asyncio
async def test_notification_poll_loop_renders_without_listing_command(
    tmp_path: Path,
) -> None:
    frontend, app = _terminal(tmp_path)
    app.create_application_notification(
        _notification(key="fixture:auto", text="automatic")
    )
    output: list[str] = []
    ui_state = {"running": True}
    task = asyncio.create_task(
        terminal._poll_events(
            frontend,
            output.append,
            ui_state,
            poll_interval=0.001,
        )
    )
    await asyncio.sleep(0.01)
    ui_state["running"] = False
    await task

    assert any("Fixture notification" in line for line in output)
    assert any("/action --ref notification-" in line for line in output)
    assert "notifications" not in terminal._static_slash_names()


def test_inactive_session_notification_is_ignored_until_switch(tmp_path: Path) -> None:
    frontend, app = _terminal(tmp_path)
    first_session_id = frontend.session_id
    _core, _config, second = app.create_session("default")
    frontend.poll_notification_updates()

    app.create_session_notification(
        second.session_id,
        _notification(key="fixture:session", text="second session"),
    )
    assert frontend.poll_notification_updates() == []

    frontend.switch_session(second.session_id)
    updates = frontend.poll_notification_updates()
    assert [item["session_id"] for item in updates] == [second.session_id]

    frontend.switch_session(first_session_id)
    assert frontend.poll_notification_updates() == []


def test_notification_cursor_recovery_hydrates_authoritative_revision(
    tmp_path: Path,
) -> None:
    events = InMemoryEventStore(max_events_global=1)
    frontend, app = _terminal(tmp_path, event_store=events)
    events.publish({"type": "fixture_marker"})
    assert frontend.poll_notification_updates() == []

    stored = app.create_application_notification(
        _notification(key="fixture:cursor", text="first")
    )
    updated = app.update_application_notification(
        stored["id"],
        {
            "body": "authoritative",
            "display": _notification(
                key="fixture:cursor",
                text="authoritative",
            )["display"],
        },
        expected_revision=stored["revision"],
    )

    updates = frontend.poll_notification_updates()
    assert [
        (
            item["notification"]["revision"],
            item["notification"]["display"]["body"],
        )
        for item in updates
    ] == [(updated["revision"], "authoritative")]
    assert frontend.poll_notification_updates() == []


def test_notification_cursor_recovery_retires_pruned_terminal_revision(
    tmp_path: Path,
) -> None:
    events = InMemoryEventStore(max_events_global=1)
    frontend, app = _terminal(tmp_path, event_store=events)
    events.publish({"type": "fixture_marker"})
    frontend.poll_notification_updates()

    stored = app.create_application_notification(
        _notification(key="fixture:terminal-cursor", text="pending")
    )
    update = frontend.poll_notification_updates()[0]
    output: list[str] = []
    terminal._render_action_result(
        frontend,
        {"display": stored["display"]},
        output.append,
        context=frontend.action_context(),
        notification={
            "scope": update["scope"],
            "session_id": update["session_id"],
            "notification_id": stored["id"],
            "revision": stored["revision"],
        },
    )
    reference = next(line for line in output if "/action --ref" in line).rsplit(" ", 1)[
        -1
    ]

    app.resolve_application_notification(
        stored["id"],
        expected_revision=stored["revision"],
    )
    events.publish({"type": "fixture_marker_after_resolution"})
    assert frontend.poll_notification_updates() == []

    with pytest.raises(TerminalUserError, match="unknown or expired"):
        frontend.get_action_reference(reference)


def test_application_replacement_invalidates_refs_and_rehydrates_notifications(
    tmp_path: Path,
) -> None:
    events = InMemoryEventStore()
    notifications = InMemoryApplicationNotificationStore()
    frontend, first_app = _terminal(
        tmp_path,
        event_store=events,
        notification_store=notifications,
    )
    stored = first_app.create_application_notification(
        _notification(key="fixture:replacement", text="replacement")
    )
    assert frontend.poll_notification_updates()

    context = frontend.action_context()
    result = frontend.execute_ui_element(
        frontend.resolve_action_element(
            "fixture_show_followup",
            plugin="terminal_action_fixture",
        ),
        context=context,
    )
    output: list[str] = []
    terminal._render_action_result(
        frontend,
        result,
        output.append,
        context=context,
    )
    reference = next(line for line in output if "/action --ref" in line).rsplit(" ", 1)[
        -1
    ]

    config = _config(tmp_path, slash_path=["replacement", "record"])
    replacement = AgentApplication(
        config,
        tmp_path / "sessions",
        event_store=events,
        application_notification_store=notifications,
    )
    frontend.replace_agent_app(replacement)

    with pytest.raises(TerminalUserError, match="unknown or expired"):
        frontend.get_action_reference(reference)
    updates = frontend.poll_notification_updates()
    assert [
        (item["notification"]["id"], item["notification"]["revision"])
        for item in updates
    ] == [(stored["id"], stored["revision"])]
    assert [element["path"] for element in frontend.slash_command_elements()] == [
        ["replacement", "record"]
    ]
    assert frontend.match_slash_command(["fixture", "record"])[0] is None
