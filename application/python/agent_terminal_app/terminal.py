from __future__ import annotations

import asyncio
from dataclasses import dataclass
from logging import Logger
from pathlib import Path
import sys
from typing import Any, Awaitable, Callable, Dict, List, Optional, cast, Tuple

from prompt_toolkit import PromptSession, print_formatted_text
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import FormattedText
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout

from .event_rendering import TerminalRenderContext, _render_terminal_exception
from .terminal_app import TerminalApplication, TerminalUserError
from agent_app.config import resolve_request_config

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
        if not isinstance(text, str) or not text:
            return

        # Slash-command completion
        if text.startswith("/"):
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
            return

        # Non-slash input: delegate to feature-driven completions when
        # appropriate (for example, @file: path expansion).
        if "@" not in text:
            return

        app = self._get_app()
        try:
            items = app.get_feature_completions(text) or []
        except Exception:
            items = []

        cursor_pos = len(text)
        for item in items:
            if not isinstance(item, dict):
                continue
            replacement = item.get("replacement")
            start = item.get("start")
            if not isinstance(replacement, str) or not isinstance(start, int):
                continue

            display = item.get("display") or replacement
            display_meta = item.get("display_meta") or ""
            start_position = start - cursor_pos

            comp = Completion(
                replacement,
                start_position=start_position,
                display=display,
                display_meta=display_meta,
            )
            # Attach the original completion descriptor so that accept
            # handlers can delegate to feature-specific logic.
            setattr(comp, "_feature_completion", item)
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


def _parse_range_or_index_arg(
    text: str,
    *,
    command: str,
    write: Callable[[str], None],
) -> Optional[Tuple[Optional[int], Optional[int]]]:
    """Parse a ``start:end``-style range argument.

    ``text`` must contain a colon and may omit either bound, following
    Python slice conventions (e.g. ``":3"``, ``"1:"``). Each side is
    parsed as an optional integer.

    Returns ``(start, end)`` where each element may be ``None``. On
    parse errors, prints a user-facing message using ``command`` as the
    prefix (e.g. ``"[list] ..."``) and returns ``None``.
    """

    start_str, _, end_str = text.partition(":")
    try:
        start_val = int(start_str) if start_str.strip() else None
    except ValueError:
        write(f"[{command}] invalid start index; expected an integer")
        return None
    try:
        end_val = int(end_str) if end_str.strip() else None
    except ValueError:
        write(f"[{command}] invalid end index; expected an integer")
        return None
    return start_val, end_val


def _normalize_setting_options(options: Any) -> List[tuple[str, str]]:
    """Normalize a UI element's options into ``(value, display)`` pairs.

    Supports both simple string options and objects like
    ``{"value": "low", "label": "Low"}``.
    """

    normalized: List[tuple[str, str]] = []
    if not isinstance(options, list):
        return normalized

    for opt in options:
        if isinstance(opt, str):
            if opt:
                normalized.append((opt, opt))
            continue

        if isinstance(opt, dict):
            val = opt.get("value")
            label = opt.get("label")
            if isinstance(val, str) and val:
                if isinstance(label, str) and label:
                    normalized.append((val, label))
                else:
                    normalized.append((val, val))

    return normalized




async def _poll_events(
    app: TerminalApplication,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
    poll_interval: float = 0.1,
) -> None:
    while ui_state.get("running", True):
        events = app.poll_new_events(limit=50)
        renderer = ui_state.get("renderer")
        for ev in events:
            # Prefer the shared TerminalRenderContext when available so that
            # streaming events and history listing share the same visuals.
            if isinstance(renderer, TerminalRenderContext):
                renderer.render_event(ev, write)

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
    # Debug helper: rely on the centralized error handler. Reuse the
    # current session/core via TerminalApplication.require_session so
    # that any missing-session issues are surfaced consistently.

    core, base_config, session = app.require_session()
    schema = core.get_ui_schema()

    # Print directly so that the raw schema is visible for debugging.
    print(schema)


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
        raise TerminalUserError("no agents configured")

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
            raise TerminalUserError(f"unknown agent: {selection!r}")

        if target == current_agent:
            raise TerminalUserError(f"already using agent {target!r}")

        app.switch_agent(target)
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
        raise TerminalUserError("no saved sessions found")

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
            raise TerminalUserError(f"unknown session: {selection!r}")

        session = app.switch_session(target)
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
        core, base_config, session = app.require_session()

        schema = core.get_config_schema()

        if not isinstance(schema, dict) or not schema:
            write("[help config] no config keys available for current plugins")
        else:
            # Sort config keys by plugin name, then key.
            items: List[Tuple[str, str, Dict[str, Any]]] = []
            for key, raw_entry in schema.items():
                if not isinstance(key, str) or not key:
                    continue
                if not isinstance(raw_entry, dict):
                    continue
                plugin_name_val = raw_entry.get("plugin")
                plugin_name = (
                    plugin_name_val
                    if isinstance(plugin_name_val, str) and plugin_name_val
                    else "unknown"
                )
                items.append((plugin_name, key, raw_entry))

            items.sort(key=lambda item: (item[0], item[1]))

            write("\n[help] Config keys for enabled plugins:")
            for plugin_name, key, entry in items:
                type_name = entry.get("type", "?")
                default_val = entry.get("default")
                description = entry.get("description") or ""
                current_val = base_config.get(key, default_val)

                key_str = f"\x1b[1;33m{key}\x1b[0m"
                plugin_str = f"\x1b[34m[{plugin_name}]\x1b[0m"
                type_str = f"\x1b[34m{type_name}\x1b[0m"
                # If the key is not explicitly set in the base config,
                # the default is in effect; in that case omit the
                # "current" marker and show only the default.
                if isinstance(base_config, dict) and key in base_config:
                    values_body = f"default={default_val!r}, current={current_val!r}"
                else:
                    values_body = f"default={default_val!r}"
                values_str = f"\x1b[90m{values_body}\x1b[0m"

                if description:
                    desc_str = f"\x1b[90m{description}\x1b[0m"
                    write(f"  {key_str} ({type_str}) {plugin_str} {values_str} - {desc_str}")
                else:
                    write(f"  {key_str} ({type_str}) {plugin_str} {values_str}")

        # List available plugins for this session with their enabled
        # status, mirroring the style of /plugins.
        try:
            plugin_entries = app.list_plugins_for_session()
        except Exception:
            plugin_entries = []

        if plugin_entries:
            write("\n[help] Plugins for this session:")
            kind_labels = {
                "providers": "provider",
                "extensions": "extension",
                "features": "feature",
                "tools": "tool",
            }
            for index, entry in enumerate(plugin_entries, 1):
                enabled = bool(entry.get("enabled"))
                status = "on " if enabled else "off"
                raw_kind = entry.get("kind")
                kind = raw_kind if isinstance(raw_kind, str) else ""
                display_kind = kind_labels.get(kind, kind or "-")
                pid = entry.get("id") if isinstance(entry.get("id"), str) else ""
                write(f"  {index}. [{status:3s}] {display_kind:<9s} {pid}")

        # Load any per-session configuration overrides stored in the
        # session metadata so that we can display current vs. override
        # values for configurable settings.
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides_val = metadata.get("overrides")
        overrides: Dict[str, Any] = (
            overrides_val if isinstance(overrides_val, dict) else {}
        )

        # Also show configurable settings exposed via /set (UI schema).
        ui_elements = app.session_ui_elements()

        if ui_elements:
            # Sort configurable settings by plugin name, then key.
            cfg_items: List[Tuple[str, str, Dict[str, Any]]] = []
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
                cfg_items.append((plugin_name, key_val, el))

            cfg_items.sort(key=lambda item: (item[0], item[1]))

            write("\n[help] Configurable settings (via /set):")
            for plugin_name, key_val, el in cfg_items:
                schema_entry = schema.get(key_val) if isinstance(schema, dict) else None
                type_name = (
                    schema_entry.get("type", "?")
                    if isinstance(schema_entry, dict)
                    else "?"
                )
                label_val = el.get("label")
                desc_val = el.get("description")
                info = (
                    label_val
                    if isinstance(label_val, str) and label_val
                    else (desc_val if isinstance(desc_val, str) else "")
                )

                # Determine the effective current value for this key.
                # Preference order:
                #   1. Value from the base agent config (if present)
                #   2. Default from the plugin config schema (if present)
                #   3. "none" if neither is defined.
                has_current = False
                current_value: Any = None
                if isinstance(base_config, dict) and key_val in base_config:
                    current_value = base_config[key_val]
                    has_current = True
                elif isinstance(schema_entry, dict) and "default" in schema_entry:
                    current_value = schema_entry.get("default")
                    has_current = True
                current_str = repr(current_value) if has_current else "none"

                # Override value comes from per-session overrides. If
                # no override exists for this key, we omit it from the
                # display instead of showing a placeholder.
                has_override = key_val in overrides
                override_str = repr(overrides[key_val]) if has_override else "none"

                key_str = f"\x1b[1;33m{key_val}\x1b[0m"
                plugin_str = f"\x1b[34m[{plugin_name}]\x1b[0m"
                type_str = f"\x1b[34m{type_name}\x1b[0m"
                if has_override:
                    values_body = f"current={current_str}, override={override_str}"
                else:
                    values_body = f"current={current_str}"
                values_str = f"\x1b[90m{values_body}\x1b[0m"
                if info:
                    info_str = f"\x1b[90m{info}\x1b[0m"
                    write(
                        f"  {key_str} ({type_str}) {plugin_str} {values_str} - {info_str}"
                    )
                else:
                    write(f"  {key_str} ({type_str}) {plugin_str} {values_str}")
        else:
            write("\n[help] No configurable settings available via /set for this session")

        # Finally, show application-level config options from the
        # top-level "application" section (used by the terminal app
        # itself for things like tool output limits). This is driven by
        # a static schema so that all options are visible even when they
        # are not explicitly set in the config file.
        app_cfg_schema = app.get_application_config_schema()
        app_cfg = app.agent_app.get_application_config()

        if app_cfg_schema:
            write("\n[help] Application-level config options (config[\"application\"]):")
            for key in sorted(app_cfg_schema.keys()):
                meta = app_cfg_schema.get(key) or {}
                type_name = meta.get("type", "?")
                default_val = meta.get("default")
                desc = meta.get("description") or ""
                current_val = app_cfg.get(key, default_val)

                key_str = f"\x1b[1;33m{key}\x1b[0m"
                type_str = f"\x1b[34m{type_name}\x1b[0m"
                values_str = f"\x1b[90mdefault={default_val!r}, current={current_val!r}\x1b[0m"
                if desc:
                    desc_str = f"\x1b[90m{desc}\x1b[0m"
                    write(f"  {key_str} ({type_str}) {values_str} - {desc_str}")
                else:
                    write(f"  {key_str} ({type_str}) {values_str}")
        else:
            write("\n[help] No application-level config options defined (schema is empty)")

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
    session = app.start_new_session(agent_id=None, persist=False)
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
        _render_terminal_exception("agent", exc, write)
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
        _render_terminal_exception("session", exc, write)
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
    raw_prefix = value_prefix

    target_el: Optional[Dict[str, Any]] = None
    for el in elements:
        if el.get("key") == key_token:
            target_el = el
            break

    if target_el is None:
        return completions

    options = target_el.get("options") or []
    el_type = target_el.get("type")

    # Special-case boolean / checkbox settings: suggest "true" / "false"
    # without any extra meta information.
    if el_type == "checkbox":
        bool_options = ["true", "false"]
        lower_prefix = value_prefix.lower()
        for opt in bool_options:
            if not value_prefix or opt.startswith(lower_prefix):
                completions.append(
                    Completion(
                        opt,
                        start_position=-len(raw_prefix),
                        display=opt,
                    )
                )
        return completions

    # For non-boolean options, support both plain strings and
    # {"value", "label"} objects. Show the underlying value as the
    # primary suggestion and the human-friendly label as meta.
    normalized = _normalize_setting_options(options)
    for opt_value, opt_display in normalized:
        if not value_prefix or opt_value.startswith(value_prefix):
            completions.append(
                Completion(
                    opt_value,
                    start_position=-len(value_prefix),
                    display=opt_value,
                    display_meta=opt_display,
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
        raise TerminalUserError("no configurable UI elements available")

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
            normalized = _normalize_setting_options(options)
            if normalized:
                display_opts = [opt_display for _, opt_display in normalized]
                write(f"  {key} (options: {', '.join(display_opts)})")
            else:
                write(f"  {key}")
        return

    name_and_val = text.split(" ", 1)
    key = name_and_val[0]
    value = name_and_val[1].strip() if len(name_and_val) > 1 else ""

    el = by_key.get(key)
    if el is None:
        raise TerminalUserError(f"unknown key: {key!r}")

    if not value:
        raise TerminalUserError(f"missing value for {key!r}")

    options = el.get("options") or []
    normalized = _normalize_setting_options(options)

    coerced: Any = value
    if normalized:
        lowered = value.lower()
        canonical: Optional[str] = None
        for opt_value, opt_display in normalized:
            # Accept either the underlying value or the human label,
            # matching case-sensitively or case-insensitively.
            if (
                value == opt_value
                or value == opt_display
                or lowered == opt_value.lower()
                or lowered == opt_display.lower()
            ):
                canonical = opt_value
                break

        if canonical is None:
            allowed_labels = [opt_display for _, opt_display in normalized]
            raise TerminalUserError(
                f"invalid value for {key!r}. Allowed: {', '.join(allowed_labels)}"
            )

        coerced = canonical

    el_type = el.get("type")
    if el_type == "checkbox":
        lowered = value.lower()
        if lowered in {"true", "1", "yes", "on"}:
            coerced = True
        elif lowered in {"false", "0", "no", "off"}:
            coerced = False
        else:
            raise TerminalUserError(f"invalid boolean for {key!r}: {value!r}")

    try:
        app.update_override(key, coerced)
    except Exception as exc:  # pragma: no cover - defensive
        # Surface configuration update failures as application errors so
        # that they include a stack trace but keep the UI responsive.
        raise TerminalApplicationError(f"failed to update overrides: {exc}")

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
        entries = app.list_plugins_for_session()

        if not entries:
            raise TerminalUserError("no plugins configured")

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
        app.clear_session_plugins()
        write("[plugins] cleared session-specific plugin overrides; using defaults again")
        try:
            ui_state["plugins_last_list"] = app.list_plugins_for_session()
        except Exception:
            ui_state["plugins_last_list"] = []
        return

    if sub not in {"on", "off"}:
        raise TerminalUserError("usage: /plugins [on|off|reset] <id-or-index>")

    target = rest.strip()
    if not target:
        raise TerminalUserError(f"usage: /plugins {sub} <id-or-index>")

    entries = ui_state.get("plugins_last_list")
    if not isinstance(entries, list) or not entries:
        entries = app.list_plugins_for_session()
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
        raise TerminalUserError(f"unknown plugin: {target!r}")

    try:
        session = app.session
    except RuntimeError as exc:
        # Treat a missing active session as an application-level
        # invariant violation for this command.
        raise TerminalApplicationError(f"no active session: {exc}")

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
        raise TerminalApplicationError(f"failed to update plugins: {exc}")

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
    # Ensure there is an active session; any missing-session issues are
    # treated as application errors and handled by the central wrapper.
    _ = app.session

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
            raise TerminalUserError("missing content for message")

    # Let TerminalApplication manage session/core state and surface
    # any issues via the central error handler.
    session_id = app.session_id
    app.add_message(session_id, role=role, content=content, metadata=None)

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
        # Let TerminalApplication manage session/core state and surface
        # any issues via the shared error renderer.
        session_id = app.session_id
        app.add_message(session_id, role="user", content=message, metadata=None)
    except Exception as exc:  # pragma: no cover - defensive
        _render_terminal_exception("append", exc, write)
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
        # Delegate cancellation to the application layer and render any
        # errors (including provider/tool issues) through the shared
        # exception renderer so that behaviour matches slash commands.
        app.agent_app.cancel_request(request_id)
    except Exception as exc:  # pragma: no cover - defensive
        _render_terminal_exception("cancel", exc, write)
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
        raise TerminalUserError("usage: /delete <index> or /delete <start>:<end>")

    # Parse arguments; ranges use slice semantics while a single integer
    # is interpreted as a Python-style index.
    if ":" in text:
        bounds = _parse_range_or_index_arg(text, command="delete", write=write)
        if bounds is None:
            return

        start_val, end_val = bounds

        _session, deleted = app.delete_messages_by_range(start_val, end_val)
    else:
        try:
            raw_index = int(text)
        except ValueError:
            raise TerminalUserError("invalid value; expected an integer or range")

        # Reuse the application's delete_messages helper so that
        # native-history semantics and events remain consistent.
        _session = app.delete_messages([raw_index])
        deleted = [raw_index]

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
        raise TerminalUserError("usage: /modify <index>")

    try:
        raw_index = int(text)
    except ValueError:
        raise TerminalUserError("invalid index; expected an integer")

    # Let TerminalApplication handle index normalization and session
    # state via show_message so that single-index semantics match other
    # history operations (including support for negative indices).
    target_index, message = app.show_message(raw_index)
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
    use_short = False

    # Optional "short" prefix switches renderers into compact mode.
    if text.startswith("short"):
        first, _, rest = text.partition(" ")
        if first == "short":
            use_short = True
            text = rest.strip()

    items: List[Tuple[int, Any]]

    # For listing, we either:
    # - list all messages when no bounds are provided,
    # - list a slice when a ``start:end`` range is supplied, or
    # - list a single message when given a Python-style index.

    if not text:
        items = app.list_messages_by_range(None, None)
    elif ":" in text:
        bounds = _parse_range_or_index_arg(text, command="list", write=write)
        if bounds is None:
            return
        start_val, end_val = bounds

        items = app.list_messages_by_range(start_val, end_val)
    else:
        # Single integer: interpret as a Python-style index selecting a
        # single message.
        try:
            raw_index = int(text)
        except ValueError:
            raise TerminalUserError("invalid value; expected an integer or range")

        # Delegate index normalization and session validation to the
        # application by selecting a single-element slice.
        items = app.list_messages_by_range(raw_index, raw_index + 1)

    if not items:
        write("[list] no messages to show")
        return

    renderer = ui_state.get("renderer")

    # When no renderer is present in ui_state (for example in tests
    # calling this command directly), create a fresh TerminalRenderContext
    # so that listing uses the same visuals as the interactive UI.
    if not isinstance(renderer, TerminalRenderContext):
        renderer = TerminalRenderContext(
            app=app,
            footer_elements_supplier=lambda: app.message_footer_elements(),
        )
        ui_state["renderer"] = renderer

    for idx, message in items:
        renderer.render_message(idx, message, write, short=use_short)


@slash_command("fork", "Fork the current session (optionally up to an index)")
async def _cmd_fork(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
    text = (arg or "").strip()
    # When no index is provided, default to ``-1`` so that ``/fork``
    # with no arguments copies the entire session (up to the last
    # message) by following Python-style negative index semantics.
    if not text:
        index = -1
    else:
        try:
            index = int(text)
        except ValueError:
            raise TerminalUserError("invalid index; expected an integer")

    source_session_id = app.session_id

    # Let TerminalApplication handle index validation and forking
    # semantics. Errors surface as TerminalUserError or
    # TerminalApplicationError.
    new_session = app.fork_session(index)

    write(f"[fork] forked {source_session_id!r} -> {new_session.session_id!r}")


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

    try:
        result = cmd.handler(app, arg, write, ui_state)
        if asyncio.iscoroutine(result):
            await result
    except Exception as exc:  # pragma: no cover - defensive
        # Delegate representation of user vs application errors to the
        # shared rendering helper so that behavior stays consistent
        # across all terminal entry points.
        _render_terminal_exception(cmd.name, exc, write)


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
    except RuntimeError:
        # Auto-recover when no active session is present by starting a
        # new ephemeral session and retrying the append.
        write("[error] session not found; starting a new one")
        app.start_new_session(agent_id=None, persist=False)
        app.append_user_message(text)
    except Exception as exc:  # pragma: no cover - defensive
        # For user-caused errors (``TerminalUserError``) render a
        # simple message; for application errors, include a traceback.
        _render_terminal_exception("input", exc, write)
        return

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
        _render_terminal_exception("modify", exc, write)
        return

    write(f"[modify] updated message at index {index}")


def _build_key_bindings(
    app: TerminalApplication,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> KeyBindings:
    kb = KeyBindings()

    def _accept_completion(event: Any) -> None:
        """Accept the current or first completion without submitting.

        - If a completion menu is active and a completion is selected,
          apply that completion.
        - If no completion is selected, start completion and apply the
          first suggestion when available.
        - For file-context completions (identified by an ``@file:`` text
          and ``display_meta`` containing ``"file"``), log acceptance so
          that a later change can attach richer behavior.
        """

        buf = event.current_buffer
        state = buf.complete_state

        # Ensure we have a completion list. When none is active yet,
        # start completion and let the completer populate suggestions.
        if state is None or not getattr(state, "completions", None):
            buf.start_completion(select_first=True)
            state = buf.complete_state

        if state is None or not getattr(state, "completions", None):
            return

        # Prefer the currently selected completion when available;
        # otherwise fall back to the first suggestion.
        current = state.current_completion
        if current is not None:
            comp = current
        else:
            comps = list(state.completions)
            if not comps:
                return
            comp = comps[0]

        text = comp.text
        meta = getattr(comp, "display_meta_text", "") or ""

        # Apply the selected completion; fall back to inserting its text
        # directly if apply_completion is not available.
        apply = getattr(buf, "apply_completion", None)
        if callable(apply):
            apply(comp)
        else:  # pragma: no cover - defensive fallback
            buf.insert_text(comp.text)

        # After the completion is applied, give feature plugins a chance to
        # transform the accepted completion into a richer snippet. This is
        # used by FileContextFeature to turn "@file:path" into a multi-line
        # template snippet.
        completion_dict = getattr(comp, "_feature_completion", None)
        if not isinstance(completion_dict, dict):
            return

        try:
            core, base_config, session = app.require_session()
            metadata = session.metadata if isinstance(session.metadata, dict) else {}
            overrides_val = metadata.get("overrides")
            overrides: Dict[str, Any] = (
                overrides_val if isinstance(overrides_val, dict) else {}
            )
            config = resolve_request_config(base_config, overrides)
            buffer_text = buf.text
            snippet = core.apply_feature_completion(config, buffer_text, completion_dict)
        except Exception as exc:
            # Display a user-friendly error message while allowing
            # structlog-based logging inside the core/plugins to capture
            # details for debugging.
            if isinstance(text, str) and text.startswith("@file:") and "file" in meta:
                write(f"[file-context] {exc}")
            else:
                write(f"[completion] {exc}")
            return

        if not isinstance(snippet, str) or not snippet:
            return

        # Replace the just-applied completion text with the snippet. We
        # assume the completion was inserted contiguously before the
        # cursor.
        cursor_pos = buf.cursor_position
        if isinstance(text, str) and cursor_pos >= len(text):
            buf.cursor_position = cursor_pos
            buf.delete_before_cursor(len(text))
            buf.insert_text(snippet)

    # Ctrl-J inserts a newline without submitting the buffer.
    @kb.add("c-j")
    def _insert_newline(event: Any) -> None:  # type: ignore[no-redef]
        event.current_buffer.insert_text("\n")

    # Alt-Enter (Meta-Enter / Esc, Enter) also inserts a newline.
    @kb.add("escape", "enter")
    def _meta_enter_newline(event: Any) -> None:  # type: ignore[no-redef]
        event.current_buffer.insert_text("\n")

    # Esc alone: cancel the current completion menu (if any) without
    # modifying the buffer content.
    @kb.add("escape")
    def _escape_cancel_completion(event: Any) -> None:  # type: ignore[no-redef]
        buf = event.current_buffer
        state = buf.complete_state
        if state is None:
            return
        cancel = getattr(buf, "cancel_completion", None)
        if callable(cancel):
            cancel()
        else:  # pragma: no cover - defensive fallback
            buf.complete_state = None

    # Space: when a completion menu is open and a completion is already
    # selected, accept that completion and then insert a space. When no
    # completion menu is active, behave like a normal space key.
    @kb.add(" ")
    def _space_accept_or_insert(event: Any) -> None:  # type: ignore[no-redef]
        buf = event.current_buffer
        state = buf.complete_state
        if state is not None and getattr(state, "completions", None):
            _accept_completion(event)
        buf.insert_text(" ")

    # Tab: accept the selected completion (or the first one when none is
    # selected) without submitting the buffer.
    @kb.add("tab")
    def _tab_accept_completion(event: Any) -> None:  # type: ignore[no-redef]
        _accept_completion(event)

    # Enter: accept current completion (if any) or submit the buffer.
    # For file-context completions (identified by @file: prefix and
    # display metadata), we currently just log acceptance; later this
    # hook can apply a richer template.
    @kb.add("enter")
    def _enter_accept(event: Any) -> None:  # type: ignore[no-redef]
        _accept_completion(event)
        event.current_buffer.validate_and_handle()

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
    app.start_new_session(agent_id=app.available_agents()[0], persist=False)

    ui_state: Dict[str, Any] = {
        "running": True,
        "pending_agent_choices": None,
        "pending_session_choices": None,
        "pending_modify_index": None,
        "input_prefill": "",
        "renderer": None,
    }

    # Shared renderer context used for both streaming events and history
    # listing so that visuals stay consistent.
    renderer_ctx = TerminalRenderContext(
        app=app,
        footer_elements_supplier=lambda: app.message_footer_elements(),
    )
    ui_state["renderer"] = renderer_ctx

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
