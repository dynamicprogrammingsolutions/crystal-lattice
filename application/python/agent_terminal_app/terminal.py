from __future__ import annotations

import asyncio
from dataclasses import dataclass
from logging import Logger
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout

from agent_app.application_future import AgentApplication
from agent_core import Session


_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config_openrouter_app_layer.json"
_DEFAULT_SESSION_ROOT = Path(__file__).resolve().parent / "sessions"


# ---------------------------------------------------------------------------
# Application helpers built on AgentApplication + event store
# ---------------------------------------------------------------------------


def _build_default_agent_app() -> AgentApplication:
    cfg = _DEFAULT_CONFIG_PATH
    root = _DEFAULT_SESSION_ROOT
    root.mkdir(parents=True, exist_ok=True)
    return AgentApplication(str(cfg), str(root))


def create_session(app: AgentApplication, agent_id: str, system_message: Optional[str]) -> Session:
    """Create and persist a session, publishing ``session_created``."""

    core, _base_config, base_session = app.create_session(agent_id)
    session = base_session

    if isinstance(system_message, str) and system_message:
        session = core.add_message(session, "system", system_message)
        app.save_session(session)

    store = app.get_event_store()
    store.publish(
        {
            "type": "session_created",
            "session_id": session.session_id,
            "agent_id": agent_id,
            "session": session.to_dict(),
        }
    )

    return session


def add_message(
    app: AgentApplication,
    session_id: str,
    *,
    role: str,
    content: str,
    metadata: Optional[Dict[str, Any]] = None,
) -> Session:
    """Append a message and publish ``message_appended``."""

    ctx = app.load_session(session_id)
    if ctx is None:
        raise KeyError(f"Session {session_id!r} not found")

    core, _base_config, session = ctx

    normalized_role = role if role in {"system", "user", "assistant", "tool"} else "user"

    new_session = core.add_message(session, normalized_role, content, metadata)
    app.save_session(new_session)

    last_message = new_session.messages[-1] if new_session.messages else None

    store = app.get_event_store()
    store.publish(
        {
            "type": "message_appended",
            "session_id": new_session.session_id,
            "role": normalized_role,
            "content": content,
            "metadata": metadata or {},
            "message": last_message.to_dict() if last_message is not None else None,
            "session": new_session.to_dict(),
        }
    )

    return new_session


def send_request(
    app: AgentApplication,
    session_id: str,
    *,
    overrides: Optional[Dict[str, Any]] = None,
    stream: bool = True,
) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], Optional[str]]:
    """Run ``AgentApplication.send_request`` and publish all events.

    Configuration overrides are loaded from the session's metadata under
    ``overrides`` and merged with any explicit ``overrides`` mapping
    provided to this function (explicit values winning).
    """

    if overrides is not None and not isinstance(overrides, dict):
        raise ValueError("config_overrides must be a mapping if provided")

    ctx = app.load_session(session_id)
    if ctx is None:
        raise KeyError(f"Session {session_id!r} not found")

    core, base_config, session = ctx

    # Merge stored overrides from session.metadata with explicit overrides.
    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    stored_overrides = metadata.get("overrides") if isinstance(metadata.get("overrides"), dict) else {}

    effective_overrides: Optional[Dict[str, Any]]
    if overrides is None:
        effective_overrides = dict(stored_overrides) if stored_overrides else None
    else:
        base = dict(stored_overrides) if stored_overrides else {}
        effective_overrides = {**base, **overrides}


    final_session_dict: Optional[Dict[str, Any]] = session.to_dict()
    final_messages: List[Dict[str, Any]] = []
    request_id: Optional[str] = None

    store = app.get_event_store()

    for ev in app.send_request(core, session, base_config, effective_overrides, stream=stream):

        stored = store.publish(ev)

        if stored.get("type") == "final":
            final_session_dict = stored.get("session") or final_session_dict
            final_messages = list(stored.get("messages") or [])
            request_id = stored.get("request_id")
        elif "session" in stored and isinstance(stored.get("session"), dict):
            final_session_dict = stored["session"]

    if final_session_dict is not None:
        try:
            final_session = Session.from_dict(final_session_dict)
            app.save_session(final_session)
        except Exception:  # pragma: no cover - defensive
            pass

    return final_session_dict, final_messages, request_id


def list_events(
    app: AgentApplication,
    *,
    since_id: Optional[str] = None,
    session_id: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """List events for a given session from the application's store."""

    store = app.get_event_store()
    return store.list(
        since_id=since_id,
        request_id=None,
        session_id=session_id,
        limit=limit,
    )


# ---------------------------------------------------------------------------
# Terminal UI wiring (prompt_toolkit)
# ---------------------------------------------------------------------------


CommandFn = Callable[["TerminalContext", str], Awaitable[None] | None]
SlashCompletionFn = Callable[["TerminalContext", str], List[Completion]]


@dataclass
class TerminalContext:

    app: AgentApplication
    session_id: str
    agent_id: str
    last_event_id: Optional[str] = None
    running: bool = True
    logger: Optional[Logger] = None
    pending_agent_choices: Optional[List[str]] = None

    def write(self, text: str) -> None:
        print(text, flush=True)
        if self.logger is not None:
            self.logger.info(text)


def _status_bar_text(ctx: TerminalContext) -> str:
    agent = ctx.agent_id or "default"
    return f"Agent: {agent}  Session: {ctx.session_id}"


def _render_event(ctx: TerminalContext, event: Dict[str, Any]) -> None:
    etype = event.get("type")

    if etype == "session_created":
        ctx.write(f"[session] created {event.get('session_id')}")
        return
    if etype == "message_appended":
        role = event.get("role")
        content = event.get("content", "") or ""
        if role == "user":
            ctx.write(f"You: {content}")
        elif role == "assistant":
            ctx.write(f"Assistant: {content}")
        return
    if etype == "request_started":
        ctx.write(f"[request] started ({event.get('request_id')})")
        return
    if etype == "partial":
        message = event.get("message") or {}
        content = message.get("content", "") or ""
        if content:
            ctx.write(f"Assistant (partial): {content}")
        return
    if etype == "final":
        messages = event.get("messages") or []
        text = ""
        if messages:
            text = messages[-1].get("content", "") or ""
        ctx.write(f"Assistant: {text}")
        return
    if etype == "tool_calls":
        ctx.write("[tools] tool calls requested")
        return
    if etype == "tool_results":
        ctx.write("[tools] tool results applied")
        return
    if etype == "error":
        ctx.write(f"[error] {event.get('detail')}")
        return
    if etype == "request_completed":
        ctx.write("[request] completed")
        return


async def _poll_events(ctx: TerminalContext, poll_interval: float = 0.1) -> None:
    store = ctx.app.get_event_store()

    while ctx.running:
        events = store.list(
            since_id=ctx.last_event_id,
            session_id=ctx.session_id,
            limit=50,
        )
        if events:
            last = events[-1].get("event_id")
            if isinstance(last, str):
                ctx.last_event_id = last
            for ev in events:
                _render_event(ctx, ev)
        await asyncio.sleep(poll_interval)


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

    def __init__(self, get_context: Callable[[], "TerminalContext"]) -> None:
        self._get_context = get_context

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

        ctx = self._get_context()
        try:
            completions = cmd.completer(ctx, rest) or []
        except Exception:
            completions = []

        for comp in completions:
            yield comp

@slash_command("ui_schema", "Get schema for UI configuration")
async def _cmd_ui_schema(ctx: TerminalContext, arg: str) -> None:
    app = ctx.app

    try:
        core, base_config, session = app.load_session(ctx.session_id)
        print(core.get_ui_schema())
    except Exception as exc:
        ctx.write(f"[ui_schema] failed to get schema: {exc}")
        return


def _flatten_ui_schema(ui_schema: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize UI schema elements for configuration-focused usage.

    The core returns a flattened list of UI elements from all plugins.
    This helper filters to elements with ``ui_type == "config"`` (or
    unset), de-duplicates by key, and normalizes options to a list of
    string values for convenience in the terminal UI.
    """

    flat: Dict[str, Dict[str, Any]] = {}

    for el in ui_schema or []:
        if not isinstance(el, dict):
            continue
        key = el.get("key")
        if not isinstance(key, str) or not key:
            continue

        ui_type = el.get("ui_type", "config")
        if ui_type != "config":
            continue

        entry = flat.get(key)
        if entry is None:
            entry = {"key": key, "type": el.get("type"), "options": []}
            flat[key] = entry

        opts = el.get("options") or []
        if isinstance(opts, list):
            for opt in opts:
                # Core UI elements typically store options as
                # {"value": <str>, "label": <str>}. We only need the
                # value for completion and /set overrides.
                if isinstance(opt, dict):
                    val = opt.get("value")
                    if isinstance(val, str) and val not in entry["options"]:
                        entry["options"].append(val)
                elif isinstance(opt, str) and opt not in entry["options"]:
                    entry["options"].append(opt)

    return sorted(flat.values(), key=lambda e: e["key"])


def _get_session_ui_elements(ctx: TerminalContext) -> List[Dict[str, Any]]:
    app = ctx.app
    loaded = app.load_session(ctx.session_id)
    if loaded is None:
        return []
    core, _base_config, _session = loaded
    try:
        ui_schema = core.get_ui_schema()
    except Exception:
        return []
    return _flatten_ui_schema(ui_schema)


def _agent_completion(ctx: TerminalContext, text: str) -> List[Completion]:
    app = ctx.app
    try:
        agents = app.list_agents()
    except Exception:
        agents = ["default"]

    agents = [a for a in agents if isinstance(a, str) and a]
    agents = sorted(dict.fromkeys(agents))

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


@slash_command("agent", "Switch the active agent for this session", completer=_agent_completion)
async def _cmd_agent(ctx: TerminalContext, arg: str) -> None:

    app = ctx.app
    try:
        agents = app.list_agents()
    except Exception:
        agents = ["default"]

    agents = [a for a in agents if isinstance(a, str) and a]
    if not agents:
        ctx.write("[agent] no agents configured")
        return

    agents = sorted(dict.fromkeys(agents))

    selection = (arg or "").strip()

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
            ctx.write(f"[agent] unknown agent: {selection!r}")
            return

        if target == ctx.agent_id:
            ctx.write(f"[agent] already using agent {target!r}")
            return

        try:
            _switch_session_agent(ctx, target)
        except Exception as exc:  # pragma: no cover - defensive
            ctx.write(f"[agent] failed to switch agent: {exc}")
        return

    # No argument: fall back to a simple text-based selection.
    ctx.pending_agent_choices = agents

    ctx.write("\n[agent] Available agents:")
    for index, agent in enumerate(agents, 1):
        marker = "*" if agent == ctx.agent_id else " "
        ctx.write(f"  {index}. [{marker}] {agent}")
    ctx.write("[agent] Enter agent name or number (empty to cancel):")


@slash_command("help", "Show commands and shortcuts")
async def _cmd_help(ctx: TerminalContext, arg: str) -> None:

    ctx.write("\nCommands:")
    for cmd in iter_slash_commands():
        ctx.write(f"  /{cmd.name:10s} - {cmd.description}")

    ctx.write("\nShortcuts (while typing):")
    for sc in iter_shortcuts():
        ctx.write(f"  {sc.keys:10s} - {sc.description}")
    ctx.write("")


@slash_command("new", "Start a new session")
@shortcut("c-n", "Start a new session")
async def _cmd_new_session(ctx: TerminalContext, arg: str) -> None:
    session = create_session(ctx.app, agent_id=ctx.agent_id, system_message=None)
    ctx.session_id = session.session_id
    ctx.last_event_id = None
    metadata = session.metadata or {}
    agent = metadata.get("agent_id")
    if isinstance(agent, str) and agent:
        ctx.agent_id = agent
    ctx.write(f"[session] switched to {ctx.session_id}")


@slash_command("exit", "Exit the terminal client")
@slash_command("quit")
@shortcut("c-q", "Exit the terminal client")
async def _cmd_exit(ctx: TerminalContext, arg: str) -> None:
    ctx.write("Exiting...")
    ctx.running = False


def _switch_session_agent(ctx: TerminalContext, agent_id: str) -> None:
    app = ctx.app
    loaded = app.load_session(ctx.session_id)
    if loaded is None:
        raise KeyError(f"Session {ctx.session_id!r} not found")
    _core, _base_config, session = loaded

    metadata = session.metadata or {}
    new_metadata = {**metadata, "agent_id": agent_id}
    new_session = Session(
        session_id=session.session_id,
        messages=list(session.messages),
        metadata=new_metadata,
    )
    app.save_session(new_session)

    ctx.agent_id = agent_id
    ctx.last_event_id = None
    ctx.write(f"[agent] switched to {agent_id!r}")


def _update_session_overrides(ctx: TerminalContext, key: str, value: Any) -> None:
    app = ctx.app
    loaded = app.load_session(ctx.session_id)
    if loaded is None:
        raise KeyError(f"Session {ctx.session_id!r} not found")
    _core, _base_config, session = loaded

    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    overrides = metadata.get("overrides") if isinstance(metadata.get("overrides"), dict) else {}

    new_overrides = {**overrides, key: value}
    new_metadata = {**metadata, "overrides": new_overrides}

    new_session = Session(
        session_id=session.session_id,
        messages=list(session.messages),
        metadata=new_metadata,
    )
    app.save_session(new_session)

    ctx.write(f"[set] {key}={value!r} saved for this session")
 
 
def _handle_agent_selection(ctx: TerminalContext, text: str) -> None:

    choices = ctx.pending_agent_choices or []
    ctx.pending_agent_choices = None

    selection = text.strip()
    if not selection:
        ctx.write("[agent] selection cancelled")
        return

    target: Optional[str] = None
    if selection.isdigit():
        index = int(selection)
        if 1 <= index <= len(choices):
            target = choices[index - 1]
    if target is None and selection in choices:
        target = selection

    if target is None:
        ctx.write(f"[agent] invalid selection: {selection!r}")
        return

    if target == ctx.agent_id:
        ctx.write(f"[agent] already using agent {target!r}")
        return

    try:
        _switch_session_agent(ctx, target)
    except Exception as exc:  # pragma: no cover - defensive
        ctx.write(f"[agent] failed to switch agent: {exc}")


def _set_completion(ctx: TerminalContext, text: str) -> List[Completion]:
    elements = _get_session_ui_elements(ctx)
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
async def _cmd_set(ctx: TerminalContext, arg: str) -> None:
    elements = _get_session_ui_elements(ctx)
    if not elements:
        ctx.write("[set] no configurable UI elements available")
        return

    by_key: Dict[str, Dict[str, Any]] = {}
    for el in elements:
        key = el.get("key")
        if isinstance(key, str) and key:
            by_key[key] = el

    text = (arg or "").strip()
    if not text:
        ctx.write("[set] usage: /set <key> <value>")
        ctx.write("[set] Available keys:")
        for key in sorted(by_key.keys()):
            options = by_key[key].get("options") or []
            if options:
                ctx.write(f"  {key} (options: {', '.join(options)})")
            else:
                ctx.write(f"  {key}")
        return

    name_and_val = text.split(" ", 1)
    key = name_and_val[0]
    value = name_and_val[1].strip() if len(name_and_val) > 1 else ""

    el = by_key.get(key)
    if el is None:
        ctx.write(f"[set] unknown key: {key!r}")
        return

    if not value:
        ctx.write(f"[set] missing value for {key!r}")
        return

    options = el.get("options") or []
    if options and value not in options:
        ctx.write(f"[set] invalid value for {key!r}. Allowed: {', '.join(options)}")
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
            ctx.write(f"[set] invalid boolean for {key!r}: {value!r}")
            return

    try:
        _update_session_overrides(ctx, key, coerced)
    except Exception as exc:  # pragma: no cover - defensive
        ctx.write(f"[set] failed to update overrides: {exc}")


async def _handle_slash_command(ctx: TerminalContext, raw: str) -> None:
    name_and_arg = raw[1:].strip().split(" ", 1)
    name = name_and_arg[0] if name_and_arg else ""
    arg = name_and_arg[1] if len(name_and_arg) > 1 else ""

    if not name:
        ctx.write("[commands] empty command")
        return

    cmd = get_slash_command(name)
    if cmd is None:
        ctx.write(f"[commands] unknown command: /{name}")
        return

    result = cmd.handler(ctx, arg)
    if asyncio.iscoroutine(result):
        await result



async def _handle_user_message(ctx: TerminalContext, text: str) -> None:
    app = ctx.app

    try:
        add_message(app, ctx.session_id, role="user", content=text, metadata=None)
    except KeyError:
        ctx.write("[error] session not found; starting a new one")
        session = create_session(app, agent_id=ctx.agent_id, system_message=None)
        ctx.session_id = session.session_id
        ctx.last_event_id = None
        metadata = session.metadata or {}
        agent = metadata.get("agent_id")
        if isinstance(agent, str) and agent:
            ctx.agent_id = agent
        add_message(app, ctx.session_id, role="user", content=text, metadata=None)

    async def _run_request() -> None:
        def _worker() -> None:
            try:
                send_request(app, ctx.session_id, overrides=None, stream=True)
            except Exception:
                # Background errors are logged via events; keep UI responsive.
                pass

        await asyncio.to_thread(_worker)

    asyncio.create_task(_run_request())


def _build_key_bindings(ctx: TerminalContext) -> KeyBindings:
    kb = KeyBindings()

    # Ctrl-J inserts a newline without submitting the buffer.
    @kb.add("c-j")
    def _insert_newline(event: Any) -> None:  # type: ignore[no-redef]
        event.current_buffer.insert_text("\n")

    for sc in iter_shortcuts():

        @kb.add(sc.keys)
        def _(event: Any, _shortcut: Shortcut = sc) -> None:  # type: ignore[no-redef]
            result = _shortcut.handler(ctx, "")
            if asyncio.iscoroutine(result):
                asyncio.create_task(result)

    return kb


async def _run_terminal(
    app: AgentApplication,
    system_message: Optional[str] = None,
    logger: Optional[Logger] = None,
) -> None:
    session = create_session(
        app,
        agent_id="default",
        system_message=system_message
        or "You are a helpful coding assistant. Respond concisely.",
    )
    metadata = session.metadata or {}
    agent = metadata.get("agent_id") if isinstance(metadata, dict) else None
    agent_id = agent if isinstance(agent, str) and agent else "default"
    ctx = TerminalContext(app=app, session_id=session.session_id, agent_id=agent_id, logger=logger)

    completer = SlashCommandCompleter(lambda: ctx)
    prompt_session = PromptSession(
        multiline=False,
        completer=completer,
        complete_while_typing=True,
        bottom_toolbar=lambda: _status_bar_text(ctx),
    )
    key_bindings = _build_key_bindings(ctx)

    event_task = asyncio.create_task(_poll_events(ctx))


    ctx.write("Session started. Type /help for commands. Press Ctrl-Q to exit.")

    with patch_stdout():
        while ctx.running:
            try:
                user_input = await prompt_session.prompt_async(
                    "You> ",
                    key_bindings=key_bindings,
                )
            except (EOFError, KeyboardInterrupt):  # pragma: no cover - console UX
                ctx.write("")
                break

            text = user_input.strip()
            if not text:
                continue

            if ctx.pending_agent_choices is not None:
                _handle_agent_selection(ctx, text)
                continue

            if text.startswith("/"):
                await _handle_slash_command(ctx, text)
            else:
                await _handle_user_message(ctx, text)

    ctx.running = False
    event_task.cancel()
    try:
        await event_task
    except asyncio.CancelledError:  # pragma: no cover - shutdown path
        pass


def run_terminal(
    system_message: Optional[str] = None,
    logger: Optional[Logger] = None,
    app_instance: Optional[AgentApplication] = None,
) -> None:  # pragma: no cover - manual usage
    """Entry point for running the terminal client.

    If ``app_instance`` is provided, it is used; otherwise a default
    :class:`AgentApplication` is constructed with the package's config
    and session root.
    """

    app = app_instance or _build_default_agent_app()

    asyncio.run(_run_terminal(app, system_message=system_message, logger=logger))
