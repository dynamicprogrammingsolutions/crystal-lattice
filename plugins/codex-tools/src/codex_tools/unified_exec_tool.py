"""Codex unified exec tools - exec_command and write_stdin.

Implements the current upstream Codex CLI "unified exec" shell surface:

- ``exec_command`` runs a command (optionally in a PTY), waits up to
  ``yield_time_ms``, and returns either the finished output with its exit
  code or a ``session_id`` for a still-running process.
- ``write_stdin`` polls an existing session or writes characters to its
  stdin (PTY sessions) and returns recent output.

Schema matches:
plugins/codex-tools/reference/codex-cli-tools/exec_command/schema.json
plugins/codex-tools/reference/codex-cli-tools/write_stdin/schema.json

Platform divergence (documented in the reference READMEs): the upstream
approval parameters (``sandbox_permissions``, ``justification``,
``prefix_rule``, ``additional_permissions``) are not served because the
platform has no per-command sandbox or approval flow.
"""

from __future__ import annotations

import asyncio
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Tuple

from tool_compat_shared.interactive_process_engine import (
    DEFAULT_MAX_SESSIONS,
    DEFAULT_SESSION_TTL_SECONDS,
    InteractiveProcessManager,
    InteractiveProcessSession,
    InteractiveSpawnSpec,
    SessionLimitError,
    StdinClosedError,
)
from tool_compat_shared.shell_engine import ShellInfo, approx_token_count, detect_shell

from .base_shell_tool import DEFAULT_MAX_OUTPUT_TOKENS, BaseCodexShellTool
from .workdir import resolve_tool_workdir


# --- Upstream tool schema texts (codex-rs/core/src/tools/handlers/shell_spec.rs) ---

EXEC_COMMAND_DESCRIPTION = (
    "Runs a command in a PTY, returning output or a session ID for ongoing "
    "interaction."
)
CMD_DESCRIPTION = "Shell command to execute."
WORKDIR_DESCRIPTION = "Working directory for the command. Defaults to the turn cwd."
TTY_DESCRIPTION = (
    "True allocates a PTY for the command; false or omitted uses plain pipes."
)
YIELD_TIME_DESCRIPTION = (
    "Wait before yielding output. Defaults to 10000 ms; effective range is "
    "250-30000 ms."
)
MAX_OUTPUT_TOKENS_DESCRIPTION = (
    "Output token budget. Defaults to 10000 tokens; larger requests may be "
    "capped by policy."
)
SHELL_PARAM_DESCRIPTION = "Shell binary to launch. Defaults to the user's default shell."
LOGIN_DESCRIPTION = (
    "True runs the shell with -l/-i semantics; false disables them. "
    "Defaults to true."
)

WRITE_STDIN_DESCRIPTION = (
    "Writes characters to an existing unified exec session and returns "
    "recent output."
)
SESSION_ID_DESCRIPTION = "Identifier of the running unified exec session."
CHARS_DESCRIPTION = (
    "Bytes to write to stdin. Defaults to empty, which polls without writing."
)
WRITE_STDIN_YIELD_DESCRIPTION = (
    "Wait before yielding output. Non-empty writes default to 250 ms and cap "
    "at 30000 ms; empty polls wait 5000-300000 ms by default."
)

# --- Upstream timing bounds (codex-rs/core/src/unified_exec/mod.rs) ---

MIN_YIELD_TIME_MS = 250
MAX_YIELD_TIME_MS = 30_000
DEFAULT_EXEC_YIELD_TIME_MS = 10_000
MIN_EMPTY_YIELD_TIME_MS = 5_000
MAX_EMPTY_YIELD_TIME_MS = 300_000
DEFAULT_WRITE_YIELD_TIME_MS = 250

INTERRUPT_CHARS = "\x03"

RUNTIME_STORE_KEY = "codex_tools.unified_exec"

_POLL_INTERVAL_SECONDS = 0.05


def clamp_exec_yield_time_ms(raw: Any) -> int:
    """Clamp exec_command yield time to the upstream 250-30000 ms range."""

    value = DEFAULT_EXEC_YIELD_TIME_MS
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        value = int(raw)
    return max(MIN_YIELD_TIME_MS, min(MAX_YIELD_TIME_MS, value))


def resolve_write_stdin_yield_time_ms(raw: Any, *, has_input: bool) -> int:
    """Resolve write_stdin yield time with upstream write/poll bounds."""

    value = DEFAULT_WRITE_YIELD_TIME_MS
    if isinstance(raw, (int, float)) and not isinstance(raw, bool):
        value = int(raw)
    value = max(MIN_YIELD_TIME_MS, value)
    if has_input:
        return min(MAX_YIELD_TIME_MS, value)
    return max(MIN_EMPTY_YIELD_TIME_MS, min(MAX_EMPTY_YIELD_TIME_MS, value))


def _resolve_max_output_tokens(raw: Any, config: Dict[str, Any]) -> int:
    if isinstance(raw, (int, float)) and not isinstance(raw, bool) and raw > 0:
        return int(raw)
    configured = config.get("unified_exec_max_output_tokens")
    if isinstance(configured, (int, float)) and not isinstance(configured, bool):
        if configured > 0:
            return int(configured)
    return DEFAULT_MAX_OUTPUT_TOKENS


def _resolve_shell(login: bool, shell_arg: Any) -> ShellInfo:
    """Resolve the shell, honoring an explicit shell path and login flag."""

    if isinstance(shell_arg, str) and shell_arg.strip():
        path = shell_arg.strip()
        name = Path(path).name or "sh"
        args: Tuple[str, ...] = ("-lc",) if login and name in ("bash", "sh") else ("-c",)
        return ShellInfo(name=name, path=path, args=args)

    shell = detect_shell()
    if login and shell.name in ("bash", "sh"):
        return ShellInfo(name=shell.name, path=shell.path, args=("-lc",))
    return shell


def _parse_session_id(raw: Any) -> Optional[int]:
    if isinstance(raw, bool):
        return None
    if isinstance(raw, int):
        return raw
    if isinstance(raw, float) and raw.is_integer():
        return int(raw)
    return None


def _format_response_text(
    *,
    wall_time_seconds: float,
    exit_code: Optional[int],
    session_id: Optional[int],
    truncated: bool,
    original_token_count: Optional[int],
    output_body: str,
) -> str:
    """Format the model-facing text using the upstream unified exec layout."""

    lines: List[str] = [f"Wall time: {wall_time_seconds:.4f} seconds"]
    if exit_code is not None:
        lines.append(f"Process exited with code {exit_code}")
    if session_id is not None:
        lines.append(f"Process running with session ID {session_id}")
    if truncated and original_token_count is not None:
        lines.append(f"Original token count: {original_token_count}")
    lines.append("Output:")
    return "\n".join(lines) + "\n" + output_body


def _manager_max_sessions(config: Dict[str, Any]) -> int:
    raw = config.get("unified_exec_max_sessions")
    if isinstance(raw, (int, float)) and not isinstance(raw, bool) and raw > 0:
        return int(raw)
    return DEFAULT_MAX_SESSIONS


def _manager_ttl_seconds(config: Dict[str, Any]) -> float:
    raw = config.get("unified_exec_session_ttl_seconds")
    if isinstance(raw, (int, float)) and not isinstance(raw, bool) and raw >= 0:
        return float(raw)
    return DEFAULT_SESSION_TTL_SECONDS


def _manager_settings(config: Dict[str, Any]) -> Tuple[int, float]:
    """Effective manager settings for a tool config."""

    return _manager_max_sessions(config), _manager_ttl_seconds(config)


def _manager_store_key(config: Dict[str, Any]) -> str:
    """Runtime-store key for the manager matching this config.

    Managers are keyed by their settings (MCP runtime-key precedent) so
    agents with different session caps or TTLs get separate managers while
    session ids stay unique within the manager a tool addresses.
    """

    max_sessions, ttl_seconds = _manager_settings(config)
    return f"{RUNTIME_STORE_KEY}.{max_sessions}.{ttl_seconds}"


# Process-wide fallback managers for contexts without a runtime store,
# keyed by the same settings fingerprint as the store key.
_module_managers: Dict[Tuple[int, float], InteractiveProcessManager] = {}
_module_managers_lock = threading.Lock()


def _get_module_manager(
    settings: Tuple[int, float],
) -> InteractiveProcessManager:
    with _module_managers_lock:
        manager = _module_managers.get(settings)
        if manager is None:
            manager = InteractiveProcessManager(
                max_sessions=settings[0], session_ttl_seconds=settings[1]
            )
            _module_managers[settings] = manager
        return manager


class _UnifiedExecToolBase(BaseCodexShellTool):
    """Shared manager resolution, wait loops, and result building."""

    version: str = "1.0.0"

    # -- manager -----------------------------------------------------------

    def _resolve_manager(
        self,
        state: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> InteractiveProcessManager:
        config = state.get("config", {})
        settings = _manager_settings(config)
        store = None
        if isinstance(context, dict):
            raw = context.get("runtime_store") or context.get("tool_runtime")
            if raw is not None and hasattr(raw, "get_or_create"):
                store = raw
        if store is not None:
            manager = store.get_or_create(
                _manager_store_key(config),
                lambda: InteractiveProcessManager(
                    max_sessions=settings[0],
                    session_ttl_seconds=settings[1],
                ),
            )
            if isinstance(manager, InteractiveProcessManager):
                return manager
        return _get_module_manager(settings)

    # -- result building ----------------------------------------------------

    def _truncate_output_body(
        self, output: str, max_output_tokens: int
    ) -> Tuple[str, Dict[str, Any]]:
        """Apply Codex-style truncation with the upstream warning header."""

        truncated_text, meta = self._apply_truncation(output, max_output_tokens)
        if not meta.get("truncated"):
            return output, meta
        truncated_text = self._insert_truncation_marker(truncated_text, meta)
        original_token_count = approx_token_count(output)
        body = (
            "Warning: truncated output "
            f"(original token count: {original_token_count})\n"
            f"Total output lines: {meta.get('total_lines', 0)}\n"
            f"\n{truncated_text}"
        )
        return body, {**meta, "original_token_count": original_token_count}

    def _build_unified_result(
        self,
        *,
        session: InteractiveProcessSession,
        output: str,
        max_output_tokens: int,
        wall_time_seconds: float,
        finished: bool,
        cancelled: bool = False,
        extra: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        body, meta = self._truncate_output_body(output, max_output_tokens)
        exit_code = session.exit_code if finished else None
        session_id = session.session_id if not finished else None
        original_token_count = (
            meta.get("original_token_count") if meta.get("truncated") else None
        )
        text = _format_response_text(
            wall_time_seconds=wall_time_seconds,
            exit_code=exit_code,
            session_id=session_id,
            truncated=bool(meta.get("truncated")),
            original_token_count=original_token_count,
            output_body=body,
        )
        success = ((exit_code == 0) if finished else True) and not cancelled
        result: Dict[str, Any] = {
            "success": success,
            "output": text,
            "wall_time_seconds": wall_time_seconds,
            "exit_code": exit_code,
            "session_id": session_id,
            "truncated": bool(meta.get("truncated")),
            "original_token_count": original_token_count,
            "timed_out": False,
            "cancelled": cancelled,
            "duration_seconds": wall_time_seconds,
            "command": session.command,
            "workdir": session.workdir,
        }
        if extra:
            result.update(extra)
        return result

    # -- wait loops ----------------------------------------------------------

    def _finalize_finished_session(
        self, session: InteractiveProcessSession
    ) -> str:
        """Collect the output tail of a finished session and close it."""

        tail = session.collect_final_output()
        session.terminate()
        return tail

    async def _wait_for_output_async(
        self,
        session: InteractiveProcessSession,
        *,
        yield_seconds: float,
        cancellation: Any = None,
    ) -> Tuple[str, bool, bool]:
        """Wait up to the yield window collecting output (async path).

        Returns (output, finished, cancelled). Never terminates a live
        session; a finished session is closed here and must be dropped from
        the manager by the caller.
        """

        deadline = time.monotonic() + yield_seconds
        collected: List[str] = []
        cancel_requested, cancel_token = self._register_cancellation(cancellation)
        try:
            while True:
                chunk = session.drain()
                if chunk:
                    collected.append(chunk)
                if not session.alive:
                    break
                if cancel_requested is not None and cancel_requested.is_set():
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                await asyncio.sleep(min(_POLL_INTERVAL_SECONDS, remaining))
            finished = not session.alive
            if finished:
                tail = self._finalize_finished_session(session)
                if tail:
                    collected.append(tail)
            cancelled = bool(
                cancel_requested is not None
                and cancel_requested.is_set()
                and not finished
            )
            return "".join(collected), finished, cancelled
        finally:
            self._unregister_cancellation(cancellation, cancel_token)

    def _stream_wait(
        self,
        session: InteractiveProcessSession,
        *,
        yield_seconds: float,
        cancellation: Any = None,
    ) -> Iterator[Dict[str, Any]]:
        """Wait up to the yield window, yielding output parts as they arrive.

        Yields partial display payloads; the generator's return value is
        ``(output, finished, cancelled)`` (consumed via ``yield from``).
        """

        deadline = time.monotonic() + yield_seconds
        collected: List[str] = []
        cancel_requested, cancel_token = self._register_cancellation(cancellation)
        try:
            while True:
                chunk = session.drain()
                if chunk:
                    collected.append(chunk)
                    yield {
                        "part": {"type": "text", "content": chunk},
                        "command": session.command,
                        "workdir": session.workdir,
                    }
                if not session.alive:
                    break
                if cancel_requested is not None and cancel_requested.is_set():
                    break
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    break
                time.sleep(min(_POLL_INTERVAL_SECONDS, remaining))
            finished = not session.alive
            if finished:
                tail = self._finalize_finished_session(session)
                if tail:
                    collected.append(tail)
                    yield {
                        "part": {"type": "text", "content": tail},
                        "command": session.command,
                        "workdir": session.workdir,
                    }
            cancelled = bool(
                cancel_requested is not None
                and cancel_requested.is_set()
                and not finished
            )
            return "".join(collected), finished, cancelled
        finally:
            self._unregister_cancellation(cancellation, cancel_token)

    def _register_cancellation(
        self, cancellation: Any
    ) -> Tuple[Optional[threading.Event], Any]:
        cancel_requested: Optional[threading.Event] = None
        cancel_token = None
        if cancellation is not None and hasattr(cancellation, "add_callback"):
            cancel_requested = threading.Event()

            def _request_cancel() -> None:
                cancel_requested.set()

            try:
                cancel_token = cancellation.add_callback(_request_cancel)
            except Exception:
                cancel_token = None
        return cancel_requested, cancel_token

    def _unregister_cancellation(self, cancellation: Any, cancel_token: Any) -> None:
        if (
            cancellation is not None
            and cancel_token is not None
            and hasattr(cancellation, "remove_callback")
        ):
            try:
                cancellation.remove_callback(cancel_token)
            except Exception:
                pass

    # -- selection -----------------------------------------------------------

    def _is_unified_exec_enabled(
        self,
        config: Dict[str, Any],
        tags: List[str],
    ) -> bool:
        mode = config.get("shell_tool_mode", "auto")
        if mode == "exec_command":
            return True
        if mode == "auto":
            return "codex-variant" in tags
        return False


class ExecCommandTool(_UnifiedExecToolBase):
    """Codex unified exec tool - start a command and yield output or a session.

    Tool name: exec_command

    Selected for the shell-command model family (gpt-5.1+, gpt-6.x, codex
    variants) via ``shell_tool_mode: "auto"`` and for any agent via the
    explicit ``shell_tool_mode: "exec_command"``.
    """

    name: str = "exec_command"
    default_enabled: bool = True

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        """Advertise this tool's presence for mutual awareness."""
        return ["shell:exec"]

    def is_enabled(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> bool:
        """Enable under ``exec_command`` mode; under ``auto`` for the
        shell-command family (codex-variant tag)."""
        return self._is_unified_exec_enabled(config, tags)

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return tool schema matching Codex CLI exec_command."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "exec_command",
                    "description": EXEC_COMMAND_DESCRIPTION,
                    "strict": False,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "cmd": {
                                "type": "string",
                                "description": CMD_DESCRIPTION,
                            },
                            "workdir": {
                                "type": "string",
                                "description": WORKDIR_DESCRIPTION,
                            },
                            "tty": {
                                "type": "boolean",
                                "description": TTY_DESCRIPTION,
                            },
                            "yield_time_ms": {
                                "type": "number",
                                "description": YIELD_TIME_DESCRIPTION,
                            },
                            "max_output_tokens": {
                                "type": "number",
                                "description": MAX_OUTPUT_TOKENS_DESCRIPTION,
                            },
                            "shell": {
                                "type": "string",
                                "description": SHELL_PARAM_DESCRIPTION,
                            },
                            "login": {
                                "type": "boolean",
                                "description": LOGIN_DESCRIPTION,
                            },
                        },
                        "required": ["cmd"],
                        "additionalProperties": False,
                    },
                },
            }
        ]

    def _prepare_execution(
        self,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """Validate arguments; returns an error result dict when invalid."""

        cmd = arguments.get("cmd", "")
        if not isinstance(cmd, str) or not cmd.strip():
            return {"success": False, "error": "cmd must be a non-empty string"}
        return None

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute the exec_command tool."""
        if tool_name != "exec_command":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        invalid = self._prepare_execution(arguments, state)
        if invalid is not None:
            return invalid

        context = kwargs.get("context") or state.get("_last_tool_context")
        state["_last_tool_context"] = context
        prepared = self._resolve_spawn(arguments, state)
        if isinstance(prepared, dict):
            return prepared
        cmd, workdir, tty, yield_ms, max_output_tokens, shell = prepared

        manager = self._resolve_manager(state, context)
        try:
            session = manager.spawn(
                InteractiveSpawnSpec(
                    command=cmd, workdir=workdir, tty=tty, shell=shell
                )
            )
        except SessionLimitError as exc:
            return {
                "success": False,
                "error": str(exc),
                "command": cmd,
                "workdir": workdir,
            }
        except Exception as exc:
            return self._spawn_error_result(
                command=cmd, workdir=workdir, exc=exc, state=state
            )

        start = time.monotonic()
        output, finished, _ = await self._wait_for_output_async(
            session,
            yield_seconds=yield_ms / 1000.0,
            cancellation=kwargs.get("cancellation"),
        )
        wall_time = time.monotonic() - start
        if finished:
            manager.remove(session.session_id)
        return self._build_unified_result(
            session=session,
            output=output,
            max_output_tokens=max_output_tokens,
            wall_time_seconds=wall_time,
            finished=finished,
            extra={"tty": tty},
        )

    async def execute_tool_async(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return await self.execute_tool(tool_name, arguments, state, **kwargs)

    def stream_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        *,
        cancellation: Any | None = None,
        context: Any | None = None,
        **_: Any,
    ) -> Iterator[Dict[str, Any]]:
        """Stream session output in real-time, then yield the final result."""
        if tool_name != "exec_command":
            return

        invalid = self._prepare_execution(arguments, state)
        if invalid is not None:
            yield invalid
            return

        state["_last_tool_context"] = context
        prepared = self._resolve_spawn(arguments, state)
        if isinstance(prepared, dict):
            yield prepared
            return
        cmd, workdir, tty, yield_ms, max_output_tokens, shell = prepared

        manager = self._resolve_manager(state, context)
        try:
            session = manager.spawn(
                InteractiveSpawnSpec(
                    command=cmd, workdir=workdir, tty=tty, shell=shell
                )
            )
        except SessionLimitError as exc:
            yield {
                "success": False,
                "error": str(exc),
                "command": cmd,
                "workdir": workdir,
            }
            return
        except Exception as exc:
            yield self._spawn_error_result(
                command=cmd, workdir=workdir, exc=exc, state=state
            )
            return

        start = time.monotonic()
        output, finished, _cancelled = yield from self._stream_wait(
            session,
            yield_seconds=yield_ms / 1000.0,
            cancellation=cancellation,
        )
        wall_time = time.monotonic() - start
        if finished:
            manager.remove(session.session_id)
        yield self._build_unified_result(
            session=session,
            output=output,
            max_output_tokens=max_output_tokens,
            wall_time_seconds=wall_time,
            finished=finished,
            extra={"tty": tty},
        )

    def _resolve_spawn(
        self, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Any:
        """Resolve spawn parameters shared by execute and stream paths."""

        cmd = arguments.get("cmd", "")
        config = state.get("config", {})
        workdir = resolve_tool_workdir(config, arguments.get("workdir"))

        intercepted = self._maybe_intercept_apply_patch(
            command=cmd,
            workdir=workdir,
            state=state,
        )
        if intercepted is not None:
            return intercepted

        tty = arguments.get("tty", False)
        if not isinstance(tty, bool):
            tty = bool(tty)
        yield_ms = clamp_exec_yield_time_ms(arguments.get("yield_time_ms"))
        max_output_tokens = _resolve_max_output_tokens(
            arguments.get("max_output_tokens"), config
        )
        login = arguments.get("login", True)
        if not isinstance(login, bool):
            login = True
        shell = _resolve_shell(login, arguments.get("shell"))
        return cmd, workdir, tty, yield_ms, max_output_tokens, shell


class WriteStdinTool(_UnifiedExecToolBase):
    """Codex unified exec tool - poll or feed an existing session.

    Tool name: write_stdin
    """

    name: str = "write_stdin"
    default_enabled: bool = True

    def get_tags(
        self, config: Dict[str, Any], models: List[Dict[str, Any]]
    ) -> List[str]:
        """Advertise this tool's presence for mutual awareness."""
        return ["shell:exec"]

    def is_enabled(
        self,
        config: Dict[str, Any],
        tags: List[str],
        models: List[Dict[str, Any]],
        context: Dict[str, Any],
    ) -> bool:
        """Enabled together with exec_command."""
        return self._is_unified_exec_enabled(config, tags)

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return tool schema matching Codex CLI write_stdin."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "write_stdin",
                    "description": WRITE_STDIN_DESCRIPTION,
                    "strict": False,
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "session_id": {
                                "type": "number",
                                "description": SESSION_ID_DESCRIPTION,
                            },
                            "chars": {
                                "type": "string",
                                "description": CHARS_DESCRIPTION,
                            },
                            "yield_time_ms": {
                                "type": "number",
                                "description": WRITE_STDIN_YIELD_DESCRIPTION,
                            },
                            "max_output_tokens": {
                                "type": "number",
                                "description": MAX_OUTPUT_TOKENS_DESCRIPTION,
                            },
                        },
                        "required": ["session_id"],
                        "additionalProperties": False,
                    },
                },
            }
        ]

    def _prepare_write(
        self,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        context: Any,
    ) -> Any:
        """Validate and apply the write; returns an error dict or a tuple."""

        session_id = _parse_session_id(arguments.get("session_id"))
        if session_id is None:
            return {"success": False, "error": "session_id must be a number"}

        chars = arguments.get("chars", "")
        if not isinstance(chars, str):
            chars = str(chars)

        manager = self._resolve_manager(state, context)
        session = manager.get(session_id)
        if session is None:
            return {"success": False, "error": f"Unknown process id {session_id}"}

        has_input = bool(chars)
        if has_input and not session.tty and chars != INTERRUPT_CHARS:
            return {
                "success": False,
                "error": (
                    "stdin is closed for this session; rerun exec_command "
                    "with tty=true to keep stdin open"
                ),
            }

        try:
            if chars == INTERRUPT_CHARS:
                session.interrupt()
            elif has_input:
                session.write(chars)
        except StdinClosedError:
            return {
                "success": False,
                "error": (
                    "stdin is closed for this session; rerun exec_command "
                    "with tty=true to keep stdin open"
                ),
            }
        except Exception as exc:
            return {"success": False, "error": f"failed to write to stdin: {exc}"}

        config = state.get("config", {})
        yield_ms = resolve_write_stdin_yield_time_ms(
            arguments.get("yield_time_ms"), has_input=has_input
        )
        max_output_tokens = _resolve_max_output_tokens(
            arguments.get("max_output_tokens"), config
        )
        return session, yield_ms, max_output_tokens

    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        """Execute the write_stdin tool."""
        if tool_name != "write_stdin":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        context = kwargs.get("context") or state.get("_last_tool_context")
        state["_last_tool_context"] = context
        outcome = self._prepare_write(arguments, state, context)
        if isinstance(outcome, dict):
            return outcome
        session, yield_ms, max_output_tokens = outcome

        start = time.monotonic()
        output, finished, _ = await self._wait_for_output_async(
            session,
            yield_seconds=yield_ms / 1000.0,
            cancellation=kwargs.get("cancellation"),
        )
        wall_time = time.monotonic() - start
        if finished:
            # Match upstream: an exited process leaves the store once observed.
            self._resolve_manager(state, context).remove(session.session_id)
        return self._build_unified_result(
            session=session,
            output=output,
            max_output_tokens=max_output_tokens,
            wall_time_seconds=wall_time,
            finished=finished,
        )

    async def execute_tool_async(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        **kwargs: Any,
    ) -> Dict[str, Any]:
        return await self.execute_tool(tool_name, arguments, state, **kwargs)

    def stream_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        *,
        cancellation: Any | None = None,
        context: Any | None = None,
        **_: Any,
    ) -> Iterator[Dict[str, Any]]:
        """Stream polled output, then yield the final result."""
        if tool_name != "write_stdin":
            return

        state["_last_tool_context"] = context
        outcome = self._prepare_write(arguments, state, context)
        if isinstance(outcome, dict):
            yield outcome
            return
        session, yield_ms, max_output_tokens = outcome

        start = time.monotonic()
        output, finished, _cancelled = yield from self._stream_wait(
            session,
            yield_seconds=yield_ms / 1000.0,
            cancellation=cancellation,
        )
        wall_time = time.monotonic() - start
        if finished:
            self._resolve_manager(state, context).remove(session.session_id)
        yield self._build_unified_result(
            session=session,
            output=output,
            max_output_tokens=max_output_tokens,
            wall_time_seconds=wall_time,
            finished=finished,
        )


__all__ = [
    "ExecCommandTool",
    "WriteStdinTool",
]
