from __future__ import annotations

import asyncio
from dataclasses import dataclass
from logging import Logger
from pathlib import Path
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from prompt_toolkit import PromptSession
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.patch_stdout import patch_stdout

from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore
from agent_core import Session


_DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent / "config_echo_app.json"
_DEFAULT_SESSION_ROOT = Path(__file__).resolve().parent / "sessions"


class TerminalApplication:
    """Terminal-side application wrapping AgentApplication and event store.

    This class owns its own :class:`AgentApplication` and
    :class:`InMemoryEventStore`. The prompt_toolkit UI calls methods on
    this class; behaviour is separate from the HTTP server.
    """

    def __init__(
        self,
        *,
        config_path: str | Path,
        session_root: str | Path,
        agent_app: Optional[AgentApplication] = None,
        event_store: Optional[InMemoryEventStore] = None,
    ) -> None:
        cfg = Path(config_path)
        root = Path(session_root)
        root.mkdir(parents=True, exist_ok=True)

        self._agent_app = agent_app or AgentApplication(str(cfg), str(root))
        self._events = event_store or InMemoryEventStore()

    @property
    def agent_app(self) -> AgentApplication:
        return self._agent_app

    @property
    def event_store(self) -> InMemoryEventStore:
        return self._events

    def create_session(self, agent_id: str, system_message: Optional[str]) -> Session:
        core, base_config, base_session = self._agent_app.create_session(agent_id)
        session = base_session

        if isinstance(system_message, str) and system_message:
            session = core.add_message(session, "system", system_message)
            self._agent_app.save_session(session)

        self._events.publish(
            {
                "type": "session_created",
                "session_id": session.session_id,
                "agent_id": agent_id,
                "session": session.to_dict(),
            }
        )

        return session

    def add_message(
        self,
        session_id: str,
        *,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Session:
        ctx = self._agent_app.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")

        core, base_config, session = ctx

        normalized_role = role if role in {"system", "user", "assistant", "tool"} else "user"

        new_session = core.add_message(session, normalized_role, content, metadata)
        self._agent_app.save_session(new_session)

        last_message = new_session.messages[-1] if new_session.messages else None

        self._events.publish(
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
        self,
        session_id: str,
        *,
        overrides: Optional[Dict[str, Any]] = None,
        stream: bool = True,
    ) -> Tuple[Optional[Dict[str, Any]], List[Dict[str, Any]], Optional[str]]:
        if overrides is not None and not isinstance(overrides, dict):
            raise ValueError("config_overrides must be a mapping if provided")

        ctx = self._agent_app.load_session(session_id)
        if ctx is None:
            raise KeyError(f"Session {session_id!r} not found")

        core, base_config, session = ctx

        final_session_dict: Optional[Dict[str, Any]] = session.to_dict()
        final_messages: List[Dict[str, Any]] = []
        request_id: Optional[str] = None

        for ev in self._agent_app.send_request(core, session, base_config, overrides, stream=stream):
            stored = self._events.publish(ev)

            if stored.get("type") == "final":
                final_session_dict = stored.get("session") or final_session_dict
                final_messages = list(stored.get("messages") or [])
                request_id = stored.get("request_id")
            elif "session" in stored and isinstance(stored.get("session"), dict):
                final_session_dict = stored["session"]

        if final_session_dict is not None:
            try:
                final_session = Session.from_dict(final_session_dict)
                self._agent_app.save_session(final_session)
            except Exception:
                pass

        return final_session_dict, final_messages, request_id

    def list_events(
        self,
        *,
        since_id: Optional[str] = None,
        session_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        return self._events.list(
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
    app: TerminalApplication
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
    store = ctx.app.event_store

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
    session = ctx.app.create_session(agent_id="default", system_message=None)
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
        app.add_message(ctx.session_id, role="user", content=text, metadata=None)
    except KeyError:
        ctx.write("[error] session not found; starting a new one")
        session = app.create_session(agent_id="default", system_message=None)
        ctx.session_id = session.session_id
        ctx.last_event_id = None
        app.add_message(ctx.session_id, role="user", content=text, metadata=None)

    async def _run_request() -> None:
        def _worker() -> None:
            try:
                app.send_request(ctx.session_id, overrides=None, stream=True)
            except Exception:
                # Background errors are logged via events; keep UI responsive.
                pass

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


async def _run_terminal(
    app: TerminalApplication,
    system_message: Optional[str] = None,
    logger: Optional[Logger] = None,
) -> None:
    session = app.create_session(
        agent_id="default",
        system_message=system_message
        or "You are a helpful coding assistant. Respond concisely.",
    )
    ctx = TerminalContext(app=app, session_id=session.session_id, logger=logger)

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
