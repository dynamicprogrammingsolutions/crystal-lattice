from __future__ import annotations

import asyncio
from dataclasses import dataclass
from logging import Logger
from pathlib import Path
import sys
from typing import Any, Awaitable, Callable, Dict, List, Optional, cast

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout

from .event_rendering import _format_message_for_list, _render_event
from .terminal_app import TerminalApplication

_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config_openrouter_app_layer.json"
_DEFAULT_SESSION_ROOT = Path(__file__).resolve().parent / "sessions"


# ---------------------------------------------------------------------------
# Terminal UI wiring (prompt_toolkit)
# ---------------------------------------------------------------------------


CommandFn = Callable[[TerminalApplication, str, Callable[[str], None], Dict[str, Any]], Awaitable[None] | None]
SlashCompletionFn = Callable[[TerminalApplication, str], List[Completion]]


@dataclass(frozen=True)
class SlashCommand:
    name: str
    description: str
    handler: CommandFn
    completer: Optional[SlashCompletionFn] = None


@dataclass(frozen=True)
class Shortcut:
    keys: str
    description: str
    handler: CommandFn


_SLASH_COMMANDS: Dict[str, SlashCommand] = {}
_SHORTCUTS: Dict[str, Shortcut] = {}


def slash_command(
    name: str,
    description: str = "",
    completer: Optional[SlashCompletionFn] = None,
) -> Callable[[CommandFn], CommandFn]:
    cmd_name = name.lstrip("/")

    def decorator(func: CommandFn) -> CommandFn:
        text = description or (func.__doc__ or "").strip() or cmd_name
        _SLASH_COMMANDS[cmd_name] = SlashCommand(
            name=cmd_name,
            description=text,
            handler=func,
            completer=completer,
        )
        return func

    return decorator


def shortcut(keys: str, description: str = "") -> Callable[[CommandFn], CommandFn]:
    def decorator(func: CommandFn) -> CommandFn:
        text = description or (func.__doc__ or "").strip() or keys
        _SHORTCUTS[keys] = Shortcut(keys=keys, description=text, handler=func)
        return func

    return decorator


def get_slash_command(name: str) -> Optional[SlashCommand]:
    return _SLASH_COMMANDS.get(name.lstrip("/"))


def iter_slash_commands() -> List[SlashCommand]:
    return sorted(_SLASH_COMMANDS.values(), key=lambda c: c.name)


def iter_shortcuts() -> List[Shortcut]:
    return sorted(_SHORTCUTS.values(), key=lambda s: s.keys)


class SlashCommandCompleter(Completer):
    """Autocomplete for slash commands and their arguments.

    This completer is generic: it knows how to complete command names
    and delegates per-command argument completion to the ``completer``
    callback registered with each :class:`SlashCommand` via the
    :func:`slash_command` decorator.
    """

    def __init__(self, get_app: Callable[[], TerminalApplication]) -> None:
        self._get_app = get_app

    def get_completions(self, document, complete_event):  # type: ignore[override]
        text = document.text_before_cursor
        if not isinstance(text, str) or not text.startswith("/"):
            return

        body = text[1:]

        # No space yet: complete command names.
        if " " not in body:
            prefix = body
            for cmd in iter_slash_commands():
                if not prefix or cmd.name.startswith(prefix):
                    yield Completion(
                        cmd.name,
                        start_position=-len(prefix),
                        display=f"/{cmd.name}",
                        display_meta=cmd.description,
                    )
            return

        cmd_name, _, rest = body.partition(" ")
        rest = rest.lstrip()

        cmd = get_slash_command(cmd_name)
        if cmd is None or cmd.completer is None:
            return

        app = self._get_app()
        try:
            completions = cmd.completer(app, rest) or []
        except Exception:
            completions = []

        for comp in completions:
            yield comp


def _status_bar_text(app: TerminalApplication) -> str:
    try:
        session_id = app.session_id
    except RuntimeError:
        session_id = "-"
    try:
        agent = app.current_agent_id()
    except RuntimeError:
        agent = "default"
    return f"Agent: {agent}  Session: {session_id}"




async def _poll_events(
    app: TerminalApplication,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
    poll_interval: float = 0.1,
) -> None:
    while ui_state.get("running", True):
        events = app.poll_new_events(limit=50)
        for ev in events:
            _render_event(ev, write)

            etype = ev.get("type")
            if etype == "request_started":
                rid = ev.get("request_id")
                if isinstance(rid, str):
                    ui_state["active_request_id"] = rid
            elif etype in {"request_completed", "request_cancelled"}:
                rid = ev.get("request_id")
                active = ui_state.get("active_request_id")
                if active is None or active == rid:
                    ui_state["active_request_id"] = None

        await asyncio.sleep(poll_interval)


@slash_command("ui_schema", "Get schema for UI configuration")
async def _cmd_ui_schema(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    try:
        core, base_config, session = app.agent_app.load_session(app.session_id)
        print(core.get_ui_schema())
    except Exception as exc:
        write(f"[ui_schema] failed to get schema: {exc}")


def _agent_completion(app: TerminalApplication, text: str) -> List[Completion]:
    agents = app.list_agents()

    prefix = text
    # Only complete a single token after /agent
    if " " in prefix:
        return []

    completions: List[Completion] = []
    for agent in agents:
        if not prefix or agent.startswith(prefix):
            completions.append(
                Completion(
                    agent,
                    start_position=-len(prefix),
                    display=agent,
                    display_meta="agent",
                )
            )
    return completions


def _session_completion(app: TerminalApplication, text: str) -> List[Completion]:
    sessions = app.list_sessions_metadata()

    prefix = text
    # Only complete a single token after /session
    if " " in prefix:
        return []

    completions: List[Completion] = []
    for entry in sessions:
        sid = entry.get("session_id")
        if not isinstance(sid, str) or not sid:
            continue
        if prefix and not sid.startswith(prefix):
            continue
        preview = entry.get("preview")
        meta = preview if isinstance(preview, str) else ""
        completions.append(
            Completion(
                sid,
                start_position=-len(prefix),
                display=sid,
                display_meta=meta,
            )
        )
    return completions


def _plugins_completion(app: TerminalApplication, text: str) -> List[Completion]:
    rest = text.lstrip()
    completions: List[Completion] = []

    # First token: subcommand
    if " " not in rest:
        prefix = rest
        for sub in ["on", "off", "reset"]:
            if not prefix or sub.startswith(prefix):
                completions.append(
                    Completion(
                        sub,
                        start_position=-len(prefix),
                        display=sub,
                        display_meta="subcommand",
                    )
                )
        return completions

    sub, _, tail = rest.partition(" ")
    tail = tail.lstrip()
    if sub not in {"on", "off"}:
        return completions

    prefix = tail
    try:
        plugins = app.list_plugins_for_session()
    except Exception:
        return completions

    for entry in plugins:
        pid = entry.get("id")
        if not isinstance(pid, str) or not pid:
            continue
        if prefix and not pid.startswith(prefix):
            continue
        kind = entry.get("kind")
        enabled = bool(entry.get("enabled"))
        status = "on" if enabled else "off"
        meta_parts: List[str] = []
        if isinstance(kind, str) and kind:
            meta_parts.append(kind)
        meta_parts.append(status)
        meta = " ".join(meta_parts)
        completions.append(
            Completion(
                pid,
                start_position=-len(prefix),
                display=pid,
                display_meta=meta,
            )
        )
    return completions


@slash_command("agent", "Switch the active agent for this session", completer=_agent_completion)
async def _cmd_agent(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    agents = app.list_agents()
    if not agents:
        write("[agent] no agents configured")
        return

    selection = (arg or "").strip()
    current_agent = app.current_agent_id()

    # If an agent identifier (or index) is provided, switch immediately.
    if selection:
        target: Optional[str] = None
        if selection.isdigit():
            index = int(selection)
            if 1 <= index <= len(agents):
                target = agents[index - 1]
        if target is None and selection in agents:
            target = selection

        if target is None:
            write(f"[agent] unknown agent: {selection!r}")
            return

        if target == current_agent:
            write(f"[agent] already using agent {target!r}")
            return

        try:
            app.switch_agent(target)
        except Exception as exc:  # pragma: no cover - defensive
            write(f"[agent] failed to switch agent: {exc}")
            return

        write(f"[agent] switched to {target!r}")
        return

    # No argument: fall back to a simple text-based selection.
    ui_state["pending_agent_choices"] = agents

    write("\n[agent] Available agents:")
    for index, agent in enumerate(agents, 1):
        marker = "*" if agent == current_agent else " "
        write(f"  {index}. [{marker}] {agent}")
    write("[agent] Enter agent name or number (empty to cancel):")


@slash_command("session", "Switch to an existing session", completer=_session_completion)
async def _cmd_session(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    sessions = app.list_sessions_metadata()
    if not sessions:
        write("[session] no saved sessions found")
        return

    selection = (arg or "").strip()

    # If a session identifier (or index) is provided, switch immediately.
    if selection:
        target: Optional[str] = None
        ids = [entry.get("session_id") for entry in sessions]
        ids = [sid for sid in ids if isinstance(sid, str) and sid]
        if selection.isdigit():
            index = int(selection)
            if 1 <= index <= len(ids):
                target = ids[index - 1]
        if target is None and selection in ids:
            target = selection

        if target is None:
            write(f"[session] unknown session: {selection!r}")
            return

        try:
            session = app.switch_session(target)
        except Exception as exc:  # pragma: no cover - defensive
            write(f"[session] failed to switch session: {exc}")
            return

        write(f"[session] switched to {session.session_id!r}")
        return

    # No argument: show a simple text-based selection.
    ui_state["pending_session_choices"] = [
        entry.get("session_id") for entry in sessions if isinstance(entry.get("session_id"), str) and entry.get("session_id")
    ]

    try:
        current_session_id = app.session_id
    except RuntimeError:
        current_session_id = None

    write("\n[session] Available sessions (most recent first):")
    for index, entry in enumerate(sessions, 1):
        sid = entry.get("session_id")
        if not isinstance(sid, str) or not sid:
            continue
        marker = "*" if sid == current_session_id else " "
        preview = entry.get("preview") if isinstance(entry.get("preview"), str) else ""
        if preview:
            write(f"  {index}. [{marker}] {sid} - {preview}")
        else:
            write(f"  {index}. [{marker}] {sid}")
    write("[session] Enter session id or number (empty to cancel):")


def _help_completion(app: TerminalApplication, text: str) -> List[Completion]:
    rest = text.lstrip()
    prefix = rest
    # Only complete a single token after /help
    if " " in rest:
        return []

    completions: List[Completion] = []
    sub = "config"
    if not prefix or sub.startswith(prefix):
        completions.append(
            Completion(
                sub,
                start_position=-len(prefix),
                display=sub,
                display_meta="subcommand",
            )
        )
    return completions


@slash_command("help", "Show commands and shortcuts", completer=_help_completion)
async def _cmd_help(

    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    text = (arg or "").strip()

    if text == "config":
        # Show top-level config keys for the currently enabled plugins.
        try:
            core, _base_config, _session = app.require_session()
        except Exception as exc:
            write(f"[help config] no active session: {exc}")
            return

        try:
            schema = core.get_config_schema()
        except Exception as exc:
            write(f"[help config] failed to get config schema: {exc}")
            return

        if not isinstance(schema, dict) or not schema:
            write("[help config] no config keys available for current plugins")
        else:
            write("\n[help] Config keys for enabled plugins:")
            for key in sorted(schema.keys()):
                entry = schema.get(key) or {}
                if not isinstance(entry, dict):
                    continue
                plugin_name_val = entry.get("plugin")
                plugin_name = (
                    plugin_name_val
                    if isinstance(plugin_name_val, str) and plugin_name_val
                    else "unknown"
                )
                desc_val = entry.get("description")
                description = desc_val if isinstance(desc_val, str) else ""
 
                # Formatting: key in bold yellow, [plugin] in blue, description in gray.
                key_str = f"\x1b[1;33m{key}\x1b[0m"
                plugin_str = f"\x1b[34m[{plugin_name}]\x1b[0m"
                if description:
                    desc_str = f"\x1b[90m{description}\x1b[0m"
                    write(f"  {key_str} {plugin_str} {desc_str}")
                else:
                    write(f"  {key_str} {plugin_str}")
 
        # Also show configurable settings exposed via /set (UI schema).
        try:
            ui_elements = app.session_ui_elements()
        except Exception as exc:  # pragma: no cover - defensive
            write(f"[help config] failed to get UI schema: {exc}")
            write("")
            return
 
        if not ui_elements:
            write("\n[help] No configurable settings available via /set for this session")
            write("")
            return
 
        write("\n[help] Configurable settings (via /set):")
        for el in ui_elements:
            key_val = el.get("key")
            if not isinstance(key_val, str) or not key_val:
                continue
            plugin_name_val = el.get("plugin")
            plugin_name = (
                plugin_name_val
                if isinstance(plugin_name_val, str) and plugin_name_val
                else "unknown"
            )
            label_val = el.get("label")
            desc_val = el.get("description")
            info = (
                label_val
                if isinstance(label_val, str) and label_val
                else (desc_val if isinstance(desc_val, str) else "")
            )
 
            key_str = f"\x1b[1;33m{key_val}\x1b[0m"
            plugin_str = f"\x1b[34m[{plugin_name}]\x1b[0m"
            if info:
                info_str = f"\x1b[90m{info}\x1b[0m"
                write(f"  {key_str} {plugin_str} {info_str}")
            else:
                write(f"  {key_str} {plugin_str}")
        write("")
        return


    write("\nCommands:")
    for cmd in iter_slash_commands():
        write(f"  /{cmd.name:10s} - {cmd.description}")

    write("\nShortcuts (while typing):")
    for sc in iter_shortcuts():
        write(f"  {sc.keys:10s} - {sc.description}")
    write("")


@slash_command("new", "Start a new session")
@shortcut("c-n", "Start a new session")
async def _cmd_new_session(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    session = app.start_new_session(agent_id=None)
    app.reset_event_cursor()
    write(f"[session] switched to {session.session_id}")


@slash_command("exit", "Exit the terminal client")
@slash_command("quit")
@shortcut("c-q", "Exit the terminal client")
async def _cmd_exit(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    write("Exiting...")
    ui_state["running"] = False


def _handle_agent_selection(
    app: TerminalApplication,
    text: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    choices = ui_state.get("pending_agent_choices") or []
    ui_state["pending_agent_choices"] = None

    selection = text.strip()
    if not selection:
        write("[agent] selection cancelled")
        return

    target: Optional[str] = None
    if selection.isdigit():
        index = int(selection)
        if 1 <= index <= len(choices):
            target = choices[index - 1]
    if target is None and selection in choices:
        target = selection

    if target is None:
        write(f"[agent] invalid selection: {selection!r}")
        return

    current_agent = app.current_agent_id()
    if target == current_agent:
        write(f"[agent] already using agent {target!r}")
        return

    try:
        app.switch_agent(target)
    except Exception as exc:  # pragma: no cover - defensive
        write(f"[agent] failed to switch agent: {exc}")
        return

    write(f"[agent] switched to {target!r}")


def _handle_session_selection(
    app: TerminalApplication,
    text: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    choices = ui_state.get("pending_session_choices") or []
    ui_state["pending_session_choices"] = None

    selection = text.strip()
    if not selection:
        write("[session] selection cancelled")
        return

    target: Optional[str] = None
    if selection.isdigit():
        index = int(selection)
        if 1 <= index <= len(choices):
            target = choices[index - 1]
    if target is None and selection in choices:
        target = selection

    if target is None:
        write(f"[session] invalid selection: {selection!r}")
        return

    try:
        session = app.switch_session(target)
    except Exception as exc:  # pragma: no cover - defensive
        write(f"[session] failed to switch session: {exc}")
        return

    write(f"[session] switched to {session.session_id!r}")


def _set_completion(app: TerminalApplication, text: str) -> List[Completion]:
    elements = app.session_ui_elements()
    rest = text.lstrip()
    completions: List[Completion] = []

    # No or single token after /set: complete keys.
    if " " not in rest:
        key_prefix = rest
        seen: set[str] = set()
        for el in elements:
            key = el.get("key")
            if not isinstance(key, str) or not key or key in seen:
                continue
            if not key_prefix or key.startswith(key_prefix):
                seen.add(key)
                completions.append(
                    Completion(
                        key,
                        start_position=-len(key_prefix),
                        display=key,
                        display_meta="setting",
                    )
                )
        return completions

    # Complete option values for a specific key.
    key_token, _, value_prefix = rest.partition(" ")
    value_prefix = value_prefix.lstrip()

    target_el: Optional[Dict[str, Any]] = None
    for el in elements:
        if el.get("key") == key_token:
            target_el = el
            break

    if target_el is None:
        return completions

    options = target_el.get("options") or []
    for opt in options:
        if not isinstance(opt, str) or not opt:
            continue
        if not value_prefix or opt.startswith(value_prefix):
            completions.append(
                Completion(
                    opt,
                    start_position=-len(value_prefix),
                    display=opt,
                    display_meta=key_token,
                )
            )
    return completions


@slash_command("set", "Set a configuration override for this session", completer=_set_completion)
async def _cmd_set(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    elements = app.session_ui_elements()
    if not elements:
        write("[set] no configurable UI elements available")
        return

    by_key: Dict[str, Dict[str, Any]] = {}
    for el in elements:
        key = el.get("key")
        if isinstance(key, str) and key:
            by_key[key] = el

    text = (arg or "").strip()
    if not text:
        write("[set] usage: /set <key> <value>")
        write("[set] Available keys:")
        for key in sorted(by_key.keys()):
            options = by_key[key].get("options") or []
            if options:
                write(f"  {key} (options: {', '.join(options)})")
            else:
                write(f"  {key}")
        return

    name_and_val = text.split(" ", 1)
    key = name_and_val[0]
    value = name_and_val[1].strip() if len(name_and_val) > 1 else ""

    el = by_key.get(key)
    if el is None:
        write(f"[set] unknown key: {key!r}")
        return

    if not value:
        write(f"[set] missing value for {key!r}")
        return

    options = el.get("options") or []
    if options and value not in options:
        write(f"[set] invalid value for {key!r}. Allowed: {', '.join(options)}")
        return

    el_type = el.get("type")
    coerced: Any = value
    if el_type == "checkbox":
        lowered = value.lower()
        if lowered in {"true", "1", "yes", "on"}:
            coerced = True
        elif lowered in {"false", "0", "no", "off"}:
            coerced = False
        else:
            write(f"[set] invalid boolean for {key!r}: {value!r}")
            return

    try:
        app.update_override(key, coerced)
    except Exception as exc:  # pragma: no cover - defensive
        write(f"[set] failed to update overrides: {exc}")
        return

    write(f"[set] {key}={coerced!r} saved for this session")


@slash_command("plugins", "List or toggle plugins for this session", completer=_plugins_completion)
async def _cmd_plugins(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    text = (arg or "").strip()

    if not text:
        try:
            entries = app.list_plugins_for_session()
        except Exception as exc:  # pragma: no cover - defensive
            write(f"[plugins] failed to list plugins: {exc}")
            return

        if not entries:
            write("[plugins] no plugins configured")
            ui_state["plugins_last_list"] = []
            return

        ui_state["plugins_last_list"] = entries

        write("[plugins] Active plugin configuration for this session:")
        kind_labels = {
            "providers": "provider",
            "extensions": "extension",
            "features": "feature",
            "tools": "tool",
        }
        for index, entry in enumerate(entries, 1):
            enabled = bool(entry.get("enabled"))
            status = "on " if enabled else "off"
            raw_kind = entry.get("kind")
            kind = raw_kind if isinstance(raw_kind, str) else ""
            display_kind = kind_labels.get(kind, kind or "-")
            pid = entry.get("id") if isinstance(entry.get("id"), str) else ""
            write(f"  {index}. [{status:3s}] {display_kind:<9s} {pid}")
        return

    # Subcommands: on, off, reset
    parts = text.split(None, 1)
    sub = parts[0]
    rest = parts[1] if len(parts) > 1 else ""

    if sub == "reset":
        try:
            app.clear_session_plugins()
        except Exception as exc:  # pragma: no cover - defensive
            write(f"[plugins] failed to clear plugin overrides: {exc}")
            return
        write("[plugins] cleared session-specific plugin overrides; using defaults again")
        try:
            ui_state["plugins_last_list"] = app.list_plugins_for_session()
        except Exception:
            ui_state["plugins_last_list"] = []
        return

    if sub not in {"on", "off"}:
        write("[plugins] usage: /plugins [on|off|reset] <id-or-index>")
        return

    target = rest.strip()
    if not target:
        write(f"[plugins] usage: /plugins {sub} <id-or-index>")
        return

    entries = ui_state.get("plugins_last_list")
    if not isinstance(entries, list) or not entries:
        try:
            entries = app.list_plugins_for_session()
        except Exception as exc:  # pragma: no cover - defensive
            write(f"[plugins] failed to list plugins: {exc}")
            return
    ui_state["plugins_last_list"] = entries

    def _resolve_plugin_id(token: str, items: List[Dict[str, Any]]) -> Optional[str]:
        if token.isdigit():
            index = int(token)
            if 1 <= index <= len(items):
                pid = items[index - 1].get("id")
                if isinstance(pid, str) and pid:
                    return pid
        for entry in items:
            pid = entry.get("id")
            if isinstance(pid, str) and pid == token:
                return pid
        name_matches: List[Dict[str, Any]] = [
            entry
            for entry in items
            if isinstance(entry.get("name"), str) and entry["name"] == token
        ]
        if len(name_matches) == 1:
            pid = name_matches[0].get("id")
            if isinstance(pid, str) and pid:
                return pid
        return None

    plugin_id = _resolve_plugin_id(target, entries)
    if plugin_id is None:
        write(f"[plugins] unknown plugin: {target!r}")
        return

    try:
        session = app.session
    except RuntimeError as exc:
        write(f"[plugins] no active session: {exc}")
        return

    metadata = session.metadata or {}
    plugins_from_session = metadata.get("plugins")
    if isinstance(plugins_from_session, list):
        enabled_ids = [p for p in plugins_from_session if isinstance(p, str)]
    else:
        agent_val = metadata.get("agent_id")
        agent_id = agent_val if isinstance(agent_val, str) and agent_val else "default"
        try:
            default_ids = app.agent_app.get_agent_plugins(agent_id)
        except Exception:  # pragma: no cover - defensive
            default_ids = None
        if default_ids is None:
            enabled_ids = [
                pid
                for pid in (entry.get("id") for entry in entries)
                if isinstance(pid, str) and pid
            ]
        else:
            enabled_ids = [p for p in default_ids if isinstance(p, str)]

    if sub == "on":
        if plugin_id not in enabled_ids:
            enabled_ids.append(plugin_id)
    else:
        enabled_ids = [p for p in enabled_ids if p != plugin_id]

    provider_ids = [
        entry.get("id")
        for entry in entries
        if entry.get("kind") == "providers" and isinstance(entry.get("id"), str) and entry.get("id")
    ]
    if sub == "off" and not any(pid in enabled_ids for pid in provider_ids):
        write("[plugins] warning: no providers will remain enabled after this change")

    try:
        app.set_session_plugins(cast(List[str], enabled_ids))
    except Exception as exc:  # pragma: no cover - defensive
        write(f"[plugins] failed to update plugins: {exc}")
        return

    action = "enabled" if sub == "on" else "disabled"
    write(f"[plugins] {action} plugin {plugin_id!r} for this session")
    try:
        ui_state["plugins_last_list"] = app.list_plugins_for_session()
    except Exception:
        ui_state["plugins_last_list"] = entries


@slash_command("send", "Send a request with the current history")
@shortcut("c-x s", "Send a request with the current history")
async def _cmd_send(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    try:
        _ = app.session
    except RuntimeError as exc:
        write(f"[send] no active session: {exc}")
        return

    await _start_background_request(app)
    write("[send] request started for current session")


@slash_command("append", "Append a message without sending")
async def _cmd_append(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    text = (arg or "").strip()
    if not text:
        write("[append] usage: /append [user|system|assistant] <content>")
        return

    role = "user"
    content = text

    first, sep, rest = text.partition(" ")
    if first in {"user", "system", "assistant"} and sep:
        role = first
        content = rest.strip()
        if not content:
            write("[append] missing content for message")
            return

    try:
        session_id = app.session_id
    except RuntimeError as exc:
        write(f"[append] no active session: {exc}")
        return

    try:
        app.add_message(session_id, role=role, content=content, metadata=None)
    except Exception as exc:  # pragma: no cover - defensive
        write(f"[append] failed to append message: {exc}")
        return

    write(f"[append] appended {role} message without sending")


@shortcut("c-x a", "Append current input as user message without sending")
async def _shortcut_append_current_input(
    app: TerminalApplication,
    text: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    message = (text or "").strip()
    if not message:
        return

    try:
        session_id = app.session_id
    except RuntimeError as exc:
        write(f"[append] no active session: {exc}")
        return

    try:
        app.add_message(session_id, role="user", content=message, metadata=None)
    except Exception as exc:  # pragma: no cover - defensive
        write(f"[append] failed to append message: {exc}")
        return

    write("[append] appended user message without sending")


@shortcut("c-x c", "Cancel the active request (if any)")
@slash_command("cancel", "Cancel the active request (if any)")
async def _shortcut_cancel_request(
    app: TerminalApplication,
    text: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    request_id = ui_state.get("active_request_id")
    if not isinstance(request_id, str) or not request_id:
        write("[cancel] no active request to cancel")
        return

    try:
        app.agent_app.cancel_request(request_id)
    except Exception as exc:  # pragma: no cover - defensive
        write(f"[cancel] failed to cancel request: {exc}")
        return

    write("[cancel] cancellation requested for active request")


@slash_command("delete", "Delete messages by index or range")
async def _cmd_delete(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    text = (arg or "").strip()
    if not text:
        write("[delete] usage: /delete <count> or /delete <start>:<end>")
        return

    # Parse arguments; delegate deletion semantics to TerminalApplication.
    if ":" in text:
        start_str, _, end_str = text.partition(":")
        try:
            start_val = int(start_str) if start_str.strip() else None
        except ValueError:
            write("[delete] invalid start index; expected an integer")
            return
        try:
            end_val = int(end_str) if end_str.strip() else None
        except ValueError:
            write("[delete] invalid end index; expected an integer")
            return

        try:
            _session, deleted = app.delete_messages_by_range(start_val, end_val)
        except RuntimeError as exc:
            write(f"[delete] no active session: {exc}")
            return
        except ValueError as exc:
            write(f"[delete] {exc}")
            return
        except Exception as exc:  # pragma: no cover - defensive
            write(f"[delete] failed to delete messages: {exc}")
            return
    else:
        try:
            count = int(text)
        except ValueError:
            write("[delete] invalid value; expected an integer or range")
            return

        try:
            _session, deleted = app.delete_last_messages(count)
        except RuntimeError as exc:
            write(f"[delete] no active session: {exc}")
            return
        except ValueError as exc:
            write(f"[delete] {exc}")
            return
        except Exception as exc:  # pragma: no cover - defensive
            write(f"[delete] failed to delete messages: {exc}")
            return

    if deleted:
        write("[delete] deleted messages at indices: " + ", ".join(str(i) for i in deleted))
    else:
        write("[delete] no messages deleted")


@slash_command("modify", "Load a message by index for editing")
async def _cmd_modify(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    text = (arg or "").strip()
    if not text:
        write("[modify] usage: /modify <index>")
        return

    try:
        raw_index = int(text)
    except ValueError:
        write("[modify] invalid index; expected an integer")
        return

    try:
        session = app.session
    except RuntimeError as exc:
        write(f"[modify] no active session: {exc}")
        return

    message_count = len(session.messages)
    if message_count == 0:
        write("[modify] no messages to modify")
        return

    target_index = raw_index
    if target_index < 0:
        target_index = message_count + target_index
    if target_index < 0 or target_index >= message_count:
        write("[modify] index out of range")
        return

    try:
        items = app.list_messages_by_range(target_index, target_index + 1)
    except Exception as exc:  # pragma: no cover - defensive
        write(f"[modify] failed to load message: {exc}")
        return

    if not items:
        write("[modify] no message found at that index")
        return

    _idx, message = items[0]
    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")
    if not isinstance(content, str):
        write("[modify] target message has no string content")
        return

    ui_state["pending_modify_index"] = target_index
    ui_state["input_prefill"] = content
    write(f"[modify] loaded message at index {target_index} for editing")


@slash_command("list", "List messages by count or range")
async def _cmd_list(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    text = (arg or "").strip()
    if not text:
        write("[list] usage: /list <count> or /list <start>:<end>")
        return

    # Parse arguments; delegate bounds validation and session handling to
    # TerminalApplication.list_messages_by_range.
    start_val: Optional[int]
    end_val: Optional[int]

    if ":" in text:
        start_str, _, end_str = text.partition(":")
        try:
            start_val = int(start_str) if start_str.strip() else None
        except ValueError:
            write("[list] invalid start index; expected an integer")
            return
        try:
            end_val = int(end_str) if end_str.strip() else None
        except ValueError:
            write("[list] invalid end index; expected an integer")
            return
    else:
        try:
            count = int(text)
        except ValueError:
            write("[list] invalid value; expected an integer or range")
            return
        if count <= 0:
            write("[list] count must be a positive integer")
            return
        start_val = -count
        end_val = None

    try:
        items = app.list_messages_by_range(start_val, end_val)
    except RuntimeError as exc:
        write(f"[list] no active session: {exc}")
        return
    except ValueError as exc:
        write(f"[list] {exc}")
        return
    except Exception as exc:  # pragma: no cover - defensive
        write(f"[list] failed to list messages: {exc}")
        return

    if not items:
        write("[list] no messages to show")
        return

    for idx, message in items:
        for line in _format_message_for_list(idx, message):
            write(line)


async def _handle_slash_command(

    app: TerminalApplication,
    raw: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    name_and_arg = raw[1:].strip().split(" ", 1)
    name = name_and_arg[0] if name_and_arg else ""
    arg = name_and_arg[1] if len(name_and_arg) > 1 else ""

    if not name:
        write("[commands] empty command")
        return

    cmd = get_slash_command(name)
    if cmd is None:
        write(f"[commands] unknown command: /{name}")
        return

    result = cmd.handler(app, arg, write, ui_state)
    if asyncio.iscoroutine(result):
        await result


async def _start_background_request(app: TerminalApplication) -> None:
    async def _run_request() -> None:
        def _worker() -> None:
            try:
                app.send_request(stream=True)
            except Exception:
                # Background errors are logged via events; keep UI responsive.
                pass

        await asyncio.to_thread(_worker)

    asyncio.create_task(_run_request())


async def _handle_user_message(
    app: TerminalApplication,
    text: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    try:
        app.append_user_message(text)
    except Exception:
        write("[error] session not found; starting a new one")
        app.start_new_session(agent_id="default")
        app.append_user_message(text)

    await _start_background_request(app)


async def _handle_modify_message(
    app: TerminalApplication,
    text: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    index = ui_state.get("pending_modify_index")
    ui_state["pending_modify_index"] = None
    ui_state["input_prefill"] = ""

    if index is None:
        await _handle_user_message(app, text, write, ui_state)
        return

    try:
        app.modify_message(index, text)
    except Exception as exc:  # pragma: no cover - defensive
        write(f"[modify] failed to update message at index {index}: {exc}")
        return

    write(f"[modify] updated message at index {index}")


def _build_key_bindings(
    app: TerminalApplication,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> KeyBindings:
    kb = KeyBindings()

    # Ctrl-J inserts a newline without submitting the buffer.
    @kb.add("c-j")
    def _insert_newline(event: Any) -> None:  # type: ignore[no-redef]
        event.current_buffer.insert_text("\n")

    for sc in iter_shortcuts():
        key_parts = tuple(sc.keys.split()) if sc.keys else ()
        if not key_parts:
            continue

        @kb.add(*key_parts)
        def _(event: Any, _shortcut: Shortcut = sc) -> None:  # type: ignore[no-redef]
            buffer_text = event.current_buffer.text
            event.current_buffer.reset()
            result = _shortcut.handler(app, buffer_text, write, ui_state)
            if asyncio.iscoroutine(result):
                asyncio.create_task(result)

    return kb

def _set_terminal_title(title: str) -> None:
    """Best-effort update of the terminal window title.

    On POSIX terminals, use a standard ANSI escape sequence.
    On Windows, fall back to the ``title`` console command.
    Failures are silently ignored so that unsupported terminals
    are unaffected.
    """
    print(f"Setting terminal title to: {title}")
    try:
        # Windows consoles (cmd/PowerShell) don't reliably support the
        # xterm title escape, but they do support the "title" command.
        if sys.platform.startswith("win"):
            import os

            os.system(f"title {title}")
        else:
            sys.stdout.write(f"\x1B]0;{title}\x07")
            sys.stdout.flush()
    except Exception:
        # Never let title handling break startup.
        pass

async def _run_terminal(
    app: TerminalApplication,
    logger: Optional[Logger] = None,
) -> None:
    # Create an initial in-memory session so that the UI has a
    # session context from startup, but avoid persisting it until
    # the user sends the first message or otherwise modifies it.
    app.start_new_session(agent_id="default", persist=False)

    ui_state: Dict[str, Any] = {
        "running": True,
        "pending_agent_choices": None,
        "pending_session_choices": None,
        "pending_modify_index": None,
        "input_prefill": "",
    }

    def write(text: str) -> None:
        print(text, flush=True)
        if logger is not None:
            logger.info(text)

    completer = SlashCommandCompleter(lambda: app)
    prompt_session = PromptSession(
        multiline=False,
        completer=completer,
        complete_while_typing=True,
        bottom_toolbar=lambda: _status_bar_text(app),
    )
    key_bindings = _build_key_bindings(app, write, ui_state)

    event_task = asyncio.create_task(_poll_events(app, write, ui_state))

    write("Session started. Type /help for commands. Press Ctrl-Q to exit.")

    with patch_stdout(True):
        _set_terminal_title("Crystal Lattice")
        while ui_state.get("running", True):
            try:
                default_text = ui_state.get("input_prefill") or ""
                ui_state["input_prefill"] = ""
                user_input = await prompt_session.prompt_async(
                    "You> ",
                    key_bindings=key_bindings,
                    default=default_text,
                )
            except (EOFError, KeyboardInterrupt):  # pragma: no cover - console UX
                write("")
                break

            text = user_input.strip()
            if not text:
                continue

            if ui_state.get("pending_agent_choices") is not None:
                _handle_agent_selection(app, text, write, ui_state)
                continue

            if ui_state.get("pending_session_choices") is not None:
                _handle_session_selection(app, text, write, ui_state)
                continue

            if ui_state.get("pending_modify_index") is not None and not text.startswith("/"):
                await _handle_modify_message(app, text, write, ui_state)
                continue

            if text.startswith("/"):
                await _handle_slash_command(app, text, write, ui_state)
            else:
                await _handle_user_message(app, text, write, ui_state)

    ui_state["running"] = False
    event_task.cancel()
    try:
        await event_task
    except asyncio.CancelledError:  # pragma: no cover - shutdown path
        pass


def run_terminal(
    logger: Optional[Logger] = None,
    app_instance: Optional[TerminalApplication] = None,
) -> None:  # pragma: no cover - manual usage

    """Entry point for running the terminal client.

    If ``app_instance`` is provided, it is used; otherwise a default
    :class:`TerminalApplication` is constructed with the package's
    config and session root.
    """

    app = app_instance or TerminalApplication(
        config_path=_DEFAULT_CONFIG_PATH,
        session_root=_DEFAULT_SESSION_ROOT,
    )

    asyncio.run(_run_terminal(app, logger=logger))
