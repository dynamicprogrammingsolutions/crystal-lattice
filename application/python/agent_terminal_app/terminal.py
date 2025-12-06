from __future__ import annotations

import asyncio
from dataclasses import dataclass
from logging import Logger
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout

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
    agent = app.current_agent_id()
    return f"Agent: {agent}  Session: {session_id}"


def _render_event(event: Dict[str, Any], write: Callable[[str], None]) -> None:
    etype = event.get("type")

    if etype == "session_created":
        write(f"[session] created {event.get('session_id')}")
        return
    if etype == "message_appended":
        role = event.get("role")
        content = event.get("content", "") or ""
        if role == "user":
            write(f"You: {content}")
        elif role == "assistant":
            write(f"Assistant: {content}")
        return
    if etype == "messages_deleted":
        indices = event.get("indices")
        if isinstance(indices, list):
            try:
                text_indices = ", ".join(str(i) for i in indices)
            except Exception:
                text_indices = str(indices)
        else:
            text_indices = str(indices)
        write(f"[session] deleted messages at indices: {text_indices}")
        return
    if etype == "request_started":
        write(f"[request] started ({event.get('request_id')})")
        return
    if etype == "partial":
        message = event.get("message") or {}
        content = message.get("content", "") or ""
        if content:
            write(f"Assistant (partial): {content}")
        return
    if etype == "final":
        messages = event.get("messages") or []
        text = ""
        if messages:
            text = messages[-1].get("content", "") or ""
        write(f"Assistant: {text}")
        return
    if etype == "tool_calls":
        write("[tools] tool calls requested")
        return
    if etype == "tool_results":
        write("[tools] tool results applied")
        return
    if etype == "error":
        write(f"[error] {event.get('detail')}")
        return
    if etype == "request_completed":
        write("[request] completed")
        return


def _format_message_for_list(index: int, message: Any) -> List[str]:
    """Return display lines for a session message.

    Shows the role, content/result, thinking, and a minimal summary of any
    tool calls or tool results attached to the message.
    """

    role = getattr(message, "role", None)
    if role is None and isinstance(message, dict):
        role = message.get("role")

    content = getattr(message, "content", None)
    if content is None and isinstance(message, dict):
        content = message.get("content")

    metadata = getattr(message, "metadata", None)
    if metadata is None and isinstance(message, dict):
        metadata = message.get("metadata")

    lines: List[str] = []
    role_text = str(role) if role is not None else "unknown"
    lines.append(f"[{index}] {role_text}")

    def _shorten(text: str, limit: int = 200) -> str:
        single = " ".join((text or "").split())
        if len(single) <= limit:
            return single
        return single[: limit - 3] + "..."

    if isinstance(content, str) and content:
        label = "result" if role_text == "tool" else "content"
        lines.append(f"  {label}: {_shorten(content)}")

    md = metadata if isinstance(metadata, dict) else {}

    reasoning = md.get("reasoning")
    if isinstance(reasoning, str) and reasoning:
        lines.append(f"  thinking: {_shorten(reasoning)}")
    else:
        thinking_blocks = md.get("thinking_blocks")
        if thinking_blocks:
            lines.append(f"  thinking: {_shorten(str(thinking_blocks))}")

    tool_calls = md.get("tool_calls")
    if isinstance(tool_calls, list) and tool_calls:
        names: List[str] = []
        for tc in tool_calls:
            if not isinstance(tc, dict):
                continue
            func = tc.get("function") or {}
            name = func.get("name") if isinstance(func, dict) else None
            if not isinstance(name, str) or not name:
                name = str(tc.get("type") or "tool")
            names.append(name)
        if names:
            summary = ", ".join(names)
            summary = _shorten(summary, limit=80)
            lines.append(f"  tools: {len(names)} call(s): {summary}")

    tool_call_id = md.get("tool_call_id")
    if tool_call_id:
        lines.append(f"  tool_call_id: {tool_call_id}")

    return lines


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


@slash_command("help", "Show commands and shortcuts")
async def _cmd_help(
    app: TerminalApplication,
    arg: str,
    write: Callable[[str], None],
    ui_state: Dict[str, Any],
) -> None:
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
    session = app.start_new_session(system_message=None, agent_id=None)
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
        app.start_new_session(system_message=None, agent_id="default")
        app.append_user_message(text)

    async def _run_request() -> None:
        def _worker() -> None:
            try:
                app.send_request(stream=True)
            except Exception:
                # Background errors are logged via events; keep UI responsive.
                pass

        await asyncio.to_thread(_worker)

    asyncio.create_task(_run_request())


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

        @kb.add(sc.keys)
        def _(event: Any, _shortcut: Shortcut = sc) -> None:  # type: ignore[no-redef]
            result = _shortcut.handler(app, "", write, ui_state)
            if asyncio.iscoroutine(result):
                asyncio.create_task(result)

    return kb


async def _run_terminal(
    app: TerminalApplication,
    system_message: Optional[str] = None,
    logger: Optional[Logger] = None,
) -> None:
    session = app.start_new_session(
        system_message=system_message
        or "You are a helpful coding assistant. Respond concisely.",
        agent_id="default",
    )

    ui_state: Dict[str, Any] = {
        "running": True,
        "pending_agent_choices": None,
        "pending_session_choices": None,
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

    with patch_stdout():
        while ui_state.get("running", True):
            try:
                user_input = await prompt_session.prompt_async(
                    "You> ",
                    key_bindings=key_bindings,
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
    system_message: Optional[str] = None,
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

    asyncio.run(_run_terminal(app, system_message=system_message, logger=logger))
