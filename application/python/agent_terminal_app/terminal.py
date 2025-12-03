from __future__ import annotations

import asyncio
from dataclasses import dataclass
from logging import Logger
from typing import Any, Awaitable, Callable, Dict, List, Optional

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout

from .server import append_message_core, create_session_core, get_event_store, run_request_for_session


# ---------------------------------------------------------------------------
# Terminal context and event rendering
# ---------------------------------------------------------------------------


@dataclass
class TerminalContext:
    """Mutable state for the terminal client.

    The application keeps state minimal and focuses on delegating work to
    the shared AgentApplication helpers in :mod:`agent_terminal_app.server`.
    """

    session_id: str
    last_event_id: Optional[str] = None
    running: bool = True
    logger: Optional[Logger] = None

    def write(self, text: str) -> None:
        """Write a line to stdout, flushing immediately, and log if set."""

        print(text, flush=True)
        if self.logger is not None:
            self.logger.info(text)


def _render_event(ctx: TerminalContext, event: Dict[str, Any]) -> None:
    """Render a single event from the shared event store.

    The goal is to keep output simple and readable rather than fully
    covering every possible event type.
    """

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
    """Background task that polls the shared event store.

    Events are rendered as they arrive while the prompt remains active.
    """

    store = get_event_store()

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


# ---------------------------------------------------------------------------
# Decorator-based registries for slash commands and shortcuts
# ---------------------------------------------------------------------------


CommandFn = Callable[[TerminalContext, str], Awaitable[None] | None]


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
    """Register a slash command using a decorator.

    Example::

        @slash_command("help", "Show available commands")
        async def cmd_help(ctx: TerminalContext, arg: str) -> None:
            ...
    """

    cmd_name = name.lstrip("/")

    def decorator(func: CommandFn) -> CommandFn:
        text = description or (func.__doc__ or "").strip() or cmd_name
        _SLASH_COMMANDS[cmd_name] = SlashCommand(name=cmd_name, description=text, handler=func)
        return func

    return decorator


def shortcut(keys: str, description: str = "") -> Callable[[CommandFn], CommandFn]:
    """Register a keyboard shortcut using a decorator.

    The decorated function must accept ``(ctx, arg)`` where ``arg`` is
    a string. When invoked via a shortcut, ``arg`` is the empty string.
    The same function may be decorated as both a slash command and a
    shortcut if desired.
    """

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


# ---------------------------------------------------------------------------
# Concrete commands and shortcuts
# ---------------------------------------------------------------------------


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
    session = create_session_core(agent_id="default")
    ctx.session_id = session.session_id
    ctx.last_event_id = None
    ctx.write(f"[session] switched to {ctx.session_id}")


@slash_command("exit", "Exit the terminal client")
@slash_command("quit")
@shortcut("c-q", "Exit the terminal client")
async def _cmd_exit(ctx: TerminalContext, arg: str) -> None:
    ctx.write("Exiting...")
    ctx.running = False


# ---------------------------------------------------------------------------
# REPL helpers
# ---------------------------------------------------------------------------


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
    try:
        append_message_core(ctx.session_id, role="user", content=text, metadata=None)
    except KeyError:
        ctx.write("[error] session not found; starting a new one")
        session = create_session_core(agent_id="default")
        ctx.session_id = session.session_id
        ctx.last_event_id = None
        append_message_core(ctx.session_id, role="user", content=text, metadata=None)

    async def _run_request() -> None:
        def _worker() -> None:
            # Run in a background thread so that the event loop remains
            # responsive and key bindings stay active while the request
            # is in progress.
            run_request_for_session(ctx.session_id, overrides=None, stream=True)

        await asyncio.to_thread(_worker)

    asyncio.create_task(_run_request())


def _build_key_bindings(ctx: TerminalContext) -> KeyBindings:
    kb = KeyBindings()

    for sc in iter_shortcuts():
        @kb.add(sc.keys)
        def _(event: Any, _shortcut: Shortcut = sc) -> None:  # type: ignore[no-redef]
            result = _shortcut.handler(ctx, "")
            if asyncio.iscoroutine(result):
                asyncio.create_task(result)

    return kb


async def _run_terminal(system_message: Optional[str] = None, logger: Optional[Logger] = None) -> None:
    session = create_session_core(
        agent_id="default",
        system_message=system_message
        or "You are a helpful coding assistant. Respond concisely.",
    )
    ctx = TerminalContext(session_id=session.session_id, logger=logger)

    prompt_session = PromptSession(multiline=True)
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


def run_terminal(system_message: Optional[str] = None, logger: Optional[Logger] = None) -> None:  # pragma: no cover - manual usage
    """Entry point for running the terminal client.

    This function is intended for manual usage, for example::

        python -m agent_terminal_app.terminal
    """

    asyncio.run(_run_terminal(system_message=system_message, logger=logger))
