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
    """Run ``AgentApplication.send_request`` and publish all events."""

    if overrides is not None and not isinstance(overrides, dict):
        raise ValueError("config_overrides must be a mapping if provided")

    ctx = app.load_session(session_id)
    if ctx is None:
        raise KeyError(f"Session {session_id!r} not found")

    core, base_config, session = ctx

    final_session_dict: Optional[Dict[str, Any]] = session.to_dict()
    final_messages: List[Dict[str, Any]] = []
    request_id: Optional[str] = None

    store = app.get_event_store()

    for ev in app.send_request(core, session, base_config, overrides, stream=stream):
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


@dataclass
class TerminalContext:
    app: AgentApplication
    session_id: str
    last_event_id: Optional[str] = None
    running: bool = True
    logger: Optional[Logger] = None

    def write(self, text: str) -> None:
        print(text, flush=True)
        if self.logger is not None:
            self.logger.info(text)


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


@dataclass(frozen=True)
class Shortcut:
    keys: str
    description: str
    handler: CommandFn


_SLASH_COMMANDS: Dict[str, SlashCommand] = {}
_SHORTCUTS: Dict[str, Shortcut] = {}


def slash_command(name: str, description: str = "") -> Callable[[CommandFn], CommandFn]:
    cmd_name = name.lstrip("/")

    def decorator(func: CommandFn) -> CommandFn:
        text = description or (func.__doc__ or "").strip() or cmd_name
        _SLASH_COMMANDS[cmd_name] = SlashCommand(name=cmd_name, description=text, handler=func)
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
    """Autocomplete for registered slash commands.

    This completer activates when the input starts with ``/`` and the
    cursor is still within the command name (before any space). It
    suggests the registered slash commands by name.
    """

    def get_completions(self, document, complete_event):  # type: ignore[override]
        text = document.text_before_cursor
        if not isinstance(text, str) or not text.startswith("/"):
            return

        # Only complete the command name (before the first space).
        name_part = text[1:]
        if " " in name_part:
            return

        prefix = name_part
        for cmd in iter_slash_commands():
            if not prefix or cmd.name.startswith(prefix):
                yield Completion(
                    cmd.name,
                    start_position=-len(prefix),
                    display=f"/{cmd.name}",
                    display_meta=cmd.description,
                )


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
    session = create_session(ctx.app, agent_id="default", system_message=None)
    ctx.session_id = session.session_id
    ctx.last_event_id = None
    ctx.write(f"[session] switched to {ctx.session_id}")


@slash_command("exit", "Exit the terminal client")
@slash_command("quit")
@shortcut("c-q", "Exit the terminal client")
async def _cmd_exit(ctx: TerminalContext, arg: str) -> None:
    ctx.write("Exiting...")
    ctx.running = False


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
        session = create_session(app, agent_id="default", system_message=None)
        ctx.session_id = session.session_id
        ctx.last_event_id = None
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
    ctx = TerminalContext(app=app, session_id=session.session_id, logger=logger)

    completer = SlashCommandCompleter()
    prompt_session = PromptSession(
        multiline=False,
        completer=completer,
        complete_while_typing=True,
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
