"""Shell command execution engine with asyncio subprocess support.

This module provides the core shell execution functionality used by all vendor
shell tools. It uses asyncio subprocess for efficient, non-blocking execution
with three-buffer output accumulation (combined/interleaved, stdout, stderr).

The implementation matches Kimi's approach and is more efficient than Qwen's
child_process fallback for output interleaving.

Background process support allows long-running commands (development servers,
watchers) to continue while the agent proceeds with other work. The shared
engine returns only structured data; vendor wrappers handle formatting.
"""

from __future__ import annotations

import asyncio
import os
import platform
import shutil
import signal
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal

# =============================================================================
# Background Process Defaults
# =============================================================================

BACKGROUND_DELAY_SECONDS = 0.2
"""Delay before returning from background command, to capture initial output."""

BACKGROUND_MAX_LINES = 100
"""Maximum lines to capture per stream for background process initial output."""

BACKGROUND_READ_TIMEOUT = 0.01
"""Per-line read timeout in seconds for background process initial output capture."""

TERMINATE_GRACE_SECONDS = 0.2
"""Grace period between soft terminate and hard kill for foreground processes."""


@dataclass(frozen=True)
class ShellInfo:
    """Detected shell configuration.

    Attributes:
        name: Shell name (e.g., "bash", "sh", "powershell", "cmd").
        path: Absolute path to the shell executable.
        args: Argument tuple for passing commands to the shell.
    """

    name: str
    path: str
    args: tuple[str, ...]


def detect_shell() -> ShellInfo:
    """Detect the appropriate shell for the current platform.

    On Windows, prefers PowerShell if available, falls back to cmd.exe.
    On Unix, respects the SHELL environment variable, falls back to
    /bin/bash, then /bin/sh.

    Returns:
        ShellInfo with detected shell configuration.
    """
    system = platform.system()

    if system == "Windows":
        # Check for PowerShell first
        ps_path = shutil.which("powershell.exe") or shutil.which("pwsh.exe")
        if ps_path:
            return ShellInfo(name="powershell", path=ps_path, args=("-command",))
        # Fallback to cmd.exe
        cmd_path = shutil.which("cmd.exe") or "cmd.exe"
        return ShellInfo(name="cmd", path=cmd_path, args=("/c",))

    # Unix: Check SHELL env var, then common paths
    shell_path = os.environ.get("SHELL", "")
    if shell_path and Path(shell_path).exists():
        name = Path(shell_path).name
        return ShellInfo(name=name, path=shell_path, args=("-c",))

    # Fallback: check common bash locations
    for candidate in ["/bin/bash", "/usr/bin/bash", "/usr/local/bin/bash"]:
        if Path(candidate).exists():
            return ShellInfo(name="bash", path=candidate, args=("-c",))

    # Final fallback to sh
    return ShellInfo(name="sh", path="/bin/sh", args=("-c",))


def build_shell_args(command: str, shell: ShellInfo | None = None) -> list[str]:
    """Build subprocess argument list for shell command execution.

    Args:
        command: The shell command to execute.
        shell: Shell configuration. If None, auto-detects via detect_shell().

    Returns:
        List of arguments suitable for asyncio.create_subprocess_exec().
    """
    if shell is None:
        shell = detect_shell()
    return [shell.path, *shell.args, command]


def _launch_process_kwargs() -> dict[str, Any]:
    """Return subprocess kwargs that isolate the child into its own killable group."""
    if os.name == "nt":
        return {}
    return {"start_new_session": True}


def build_async_subprocess_kwargs() -> dict[str, Any]:
    """Return standard async subprocess kwargs for noninteractive shell execution."""
    launch_kwargs = dict(_launch_process_kwargs())
    launch_kwargs["stdin"] = asyncio.subprocess.DEVNULL
    return launch_kwargs


def build_sync_subprocess_kwargs() -> dict[str, Any]:
    """Return standard sync subprocess kwargs for noninteractive shell execution."""
    launch_kwargs = dict(_launch_process_kwargs())
    launch_kwargs["stdin"] = subprocess.DEVNULL
    return launch_kwargs


def _get_process_group_id(pid: int | None) -> int | None:
    if pid is None or os.name == "nt":
        return None
    try:
        return os.getpgid(pid)
    except ProcessLookupError:
        return None


async def terminate_async_process_tree(
    process: asyncio.subprocess.Process,
    *,
    grace_seconds: float = TERMINATE_GRACE_SECONDS,
) -> None:
    """Terminate the entire process tree for an asyncio subprocess."""
    if process.returncode is not None:
        return

    pgid = _get_process_group_id(process.pid)
    if pgid is not None:
        try:
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            return

        try:
            await asyncio.wait_for(process.wait(), timeout=grace_seconds)
            return
        except asyncio.TimeoutError:
            pgid = _get_process_group_id(process.pid)
            if pgid is not None:
                try:
                    os.killpg(pgid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            await process.wait()
            return

    process.terminate()
    try:
        await asyncio.wait_for(process.wait(), timeout=grace_seconds)
    except asyncio.TimeoutError:
        process.kill()
        await process.wait()


def terminate_process_tree(
    process: subprocess.Popen[Any],
    *,
    grace_seconds: float = TERMINATE_GRACE_SECONDS,
) -> None:
    """Terminate the entire process tree for a synchronous subprocess."""
    if process.poll() is not None:
        return

    pgid = _get_process_group_id(process.pid)
    if pgid is not None:
        try:
            os.killpg(pgid, signal.SIGTERM)
        except ProcessLookupError:
            return

        try:
            process.wait(timeout=grace_seconds)
            return
        except subprocess.TimeoutExpired:
            pgid = _get_process_group_id(process.pid)
            if pgid is not None:
                try:
                    os.killpg(pgid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            try:
                process.wait(timeout=grace_seconds)
            except subprocess.TimeoutExpired:
                pass
            return

    process.terminate()
    try:
        process.wait(timeout=grace_seconds)
    except subprocess.TimeoutExpired:
        process.kill()
        try:
            process.wait(timeout=grace_seconds)
        except subprocess.TimeoutExpired:
            pass


async def _capture_initial_output(
    process: asyncio.subprocess.Process,
    *,
    delay_seconds: float = BACKGROUND_DELAY_SECONDS,
    max_lines: int = BACKGROUND_MAX_LINES,
    read_timeout: float = BACKGROUND_READ_TIMEOUT,
) -> dict[str, str]:
    """Capture initial output from a background process.

    Waits for a delay to let output accumulate, then reads available lines
    with short timeouts. This allows capturing startup errors like
    "command not found" while not blocking on long-running processes.

    Args:
        process: The subprocess to capture output from.
        delay_seconds: Initial delay before reading. Default BACKGROUND_DELAY_SECONDS.
        max_lines: Maximum lines to read per stream. Default BACKGROUND_MAX_LINES.
        read_timeout: Per-line read timeout in seconds. Default BACKGROUND_READ_TIMEOUT.

    Returns:
        Dict with:
            - stdout: captured stdout lines
            - stderr: captured stderr lines
            - combined: interleaved output (stdout lines followed by stderr lines)
    """
    stdout_chunks: list[str] = []
    stderr_chunks: list[str] = []

    # Sleep to let output accumulate
    await asyncio.sleep(delay_seconds)

    async def read_some_lines(
        stream: asyncio.StreamReader | None,
        chunks: list[str],
    ) -> None:
        """Read up to max_lines lines from stream with per-line timeout."""
        if stream is None:
            return
        try:
            for _ in range(max_lines):
                line = await asyncio.wait_for(stream.readline(), timeout=read_timeout)
                if not line:
                    break
                chunks.append(line.decode(errors="replace"))
        except asyncio.TimeoutError:
            # Expected - stream is still open, no more data available right now
            pass

    await asyncio.gather(
        read_some_lines(process.stdout, stdout_chunks),
        read_some_lines(process.stderr, stderr_chunks),
    )

    return {
        "stdout": "".join(stdout_chunks),
        "stderr": "".join(stderr_chunks),
        # Combined is stdout followed by stderr (not truly interleaved due to
        # sequential reads, but captures both for error detection)
        "combined": "".join(stdout_chunks) + "".join(stderr_chunks),
    }


async def run_shell_command(
    command: str | list[str],
    *,
    workdir: str | None = None,
    timeout_seconds: float | None = None,
    env: dict[str, str] | None = None,
    shell: ShellInfo | None = None,
    is_background: bool = False,
    background_delay_seconds: float | None = None,
    background_max_lines: int | None = None,
    background_read_timeout: float | None = None,
) -> dict[str, Any]:
    """Execute a shell command with interleaved output capture.

    Uses asyncio subprocess for efficient, non-blocking execution with
    three-buffer output accumulation:
    - combined: interleaved output in arrival order
    - stdout: separate stdout capture
    - stderr: separate stderr capture

    Command formats:
    - String: "echo hello" → wrapped via shell (e.g., ["/bin/bash", "-c", "echo hello"])
    - Array: ["echo", "hello"] → passed directly to execvp (no shell wrapper)

    Background mode (is_background=True):
    - Only supported for string commands (shell-based execution)
    - Timeout is ignored (process runs indefinitely)
    - On Unix, '&' is appended to command for shell backgrounding
    - On Windows, no '&' is appended (process stays attached)
    - Returns early after capturing initial output (~200ms by default)
    - For array commands, is_background is ignored

    Args:
        command: The shell command to execute. Either a string (wrapped via shell)
                 or a list of strings (passed directly to execvp).
        workdir: Working directory. None means current directory.
        timeout_seconds: Timeout in seconds. None means no timeout. Ignored for background.
        env: Environment variables. None means inherit os.environ.
        shell: Shell configuration. None means auto-detect via detect_shell().
               Only used when command is a string.
        is_background: If True, run in background mode and return early.
                       Only supported for string commands.
        background_delay_seconds: Delay before returning for background. Default BACKGROUND_DELAY_SECONDS.
        background_max_lines: Max lines to capture per stream for background. Default BACKGROUND_MAX_LINES.
        background_read_timeout: Per-line read timeout for background. Default BACKGROUND_READ_TIMEOUT.

    Returns:
        Dict with:
            - ok: bool (True if exit_code == 0 and not timed out; True for background if started)
            - exit_code: int | None (None if timed out or background)
            - output: str (combined interleaved output)
            - stdout: str (separate stdout)
            - stderr: str (separate stderr)
            - duration_seconds: float
            - timed_out: bool (always False for background)
            - shell: ShellInfo (shell used for execution, only for string commands)
            - background: bool (True if background mode, only present when True)
            - pid: int (process ID, only present for background mode)
            - direct_exec: bool (True if command was array/list, only present when True)
    """
    is_windows = sys.platform == "win32"
    is_array_command = isinstance(command, list)

    # Determine execution args based on command type
    if is_array_command:
        # Array command: pass directly to execvp
        args = list(command)
        used_shell = None
        # Background mode not supported for direct exec
        effective_background = False
    else:
        # String command: wrap via shell
        used_shell = shell or detect_shell()

        # Background mode: modify command for Unix
        if is_background:
            # Skip timeout for background processes
            timeout_seconds = None

            # On Unix, append '&' for shell backgrounding if not already present
            if not is_windows and not command.rstrip().endswith("&"):
                command = command.rstrip() + " &"

        args = build_shell_args(command, used_shell)
        effective_background = is_background

    start_time = time.monotonic()

    process = await asyncio.create_subprocess_exec(
        *args,
        cwd=workdir,
        env=env if env is not None else os.environ,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        **build_async_subprocess_kwargs(),
    )

    pid = process.pid

    # Background mode: capture initial output and return early
    if effective_background:
        initial_output = await _capture_initial_output(
            process,
            delay_seconds=background_delay_seconds or BACKGROUND_DELAY_SECONDS,
            max_lines=background_max_lines or BACKGROUND_MAX_LINES,
            read_timeout=background_read_timeout or BACKGROUND_READ_TIMEOUT,
        )

        duration = time.monotonic() - start_time

        result: dict[str, Any] = {
            "ok": True,  # Process started successfully
            "exit_code": None,  # Process still running
            "output": initial_output["combined"],
            "stdout": initial_output["stdout"],
            "stderr": initial_output["stderr"],
            "duration_seconds": duration,
            "timed_out": False,
            "background": True,
            "pid": pid,
        }
        if used_shell is not None:
            result["shell"] = used_shell
        return result

    # Foreground mode: wait for completion with three-buffer accumulation
    combined_chunks: list[str] = []  # Interleaved order
    stdout_chunks: list[str] = []  # Separate for vendor formatting
    stderr_chunks: list[str] = []  # Separate for vendor formatting

    async def read_stdout() -> None:
        """Read stdout line-by-line, appending to both combined and stdout buffers."""
        if process.stdout is None:
            return
        async for line in process.stdout:
            decoded = line.decode(errors="replace")
            combined_chunks.append(decoded)
            stdout_chunks.append(decoded)

    async def read_stderr() -> None:
        """Read stderr line-by-line, appending to both combined and stderr buffers."""
        if process.stderr is None:
            return
        async for line in process.stderr:
            decoded = line.decode(errors="replace")
            combined_chunks.append(decoded)
            stderr_chunks.append(decoded)

    try:
        if timeout_seconds is not None:
            await asyncio.wait_for(
                asyncio.gather(read_stdout(), read_stderr()),
                timeout=timeout_seconds,
            )
        else:
            await asyncio.gather(read_stdout(), read_stderr())

        exit_code = await process.wait()
        timed_out = False

    except asyncio.TimeoutError:
        await terminate_async_process_tree(process)
        exit_code = None
        timed_out = True

    duration = time.monotonic() - start_time

    result = {
        "ok": not timed_out and exit_code == 0,
        "exit_code": exit_code,
        "output": "".join(combined_chunks),
        "stdout": "".join(stdout_chunks),
        "stderr": "".join(stderr_chunks),
        "duration_seconds": duration,
        "timed_out": timed_out,
    }
    if used_shell is not None:
        result["shell"] = used_shell
    if is_array_command:
        result["direct_exec"] = True
    return result


# =============================================================================
# Truncation Support
# =============================================================================

APPROX_BYTES_PER_TOKEN = 4
"""Approximate bytes per token for Codex-style token estimation."""


def approx_token_count(text: str) -> int:
    """Approximate token count using Codex's heuristic: len(text) // 4.

    This matches the Codex CLI implementation in truncate.rs:
    const APPROX_BYTES_PER_TOKEN: usize = 4;

    Args:
        text: The text to estimate token count for.

    Returns:
        Approximate number of tokens.
    """
    return len(text) // APPROX_BYTES_PER_TOKEN


def _build_metadata(
    *,
    truncated: bool,
    total_chars: int,
    total_lines: int,
    total_tokens: int,
    omitted_chars: int,
    omitted_lines: int,
    omitted_tokens: int,
    head_kept: int,
    tail_kept: int,
    limit_type: str,
    limit_value: int,
    head_ratio: float,
) -> dict[str, Any]:
    """Build the metadata dict returned by truncate_output."""
    return {
        "truncated": truncated,
        "total_chars": total_chars,
        "total_lines": total_lines,
        "total_tokens": total_tokens,
        "omitted_chars": omitted_chars,
        "omitted_lines": omitted_lines,
        "omitted_tokens": omitted_tokens,
        "head_kept": head_kept,
        "tail_kept": tail_kept,
        "limit_type": limit_type,
        "limit_value": limit_value,
        "head_ratio": head_ratio,
    }


def _truncate_chars(
    content: str,
    max_chars: int,
    head_ratio: float,
    total_chars: int,
    total_lines: int,
    total_tokens: int,
    limit_type: str,
    limit_value: int,
) -> tuple[str, dict[str, Any]]:
    """Truncate by character count."""
    head_chars = int(max_chars * head_ratio)
    tail_chars = max_chars - head_chars

    if head_ratio >= 1.0:
        # All from beginning (Qwen-style)
        truncated = content[:max_chars]
        return truncated, _build_metadata(
            truncated=True,
            total_chars=total_chars,
            total_lines=total_lines,
            total_tokens=total_tokens,
            omitted_chars=total_chars - max_chars,
            omitted_lines=0,  # Unknown without re-counting
            omitted_tokens=0,  # Unknown without re-counting
            head_kept=max_chars,
            tail_kept=0,
            limit_type=limit_type,
            limit_value=limit_value,
            head_ratio=head_ratio,
        )

    # Split: head + tail
    head = content[:head_chars]
    tail = content[-tail_chars:] if tail_chars > 0 else ""
    truncated = head + tail
    return truncated, _build_metadata(
        truncated=True,
        total_chars=total_chars,
        total_lines=total_lines,
        total_tokens=total_tokens,
        omitted_chars=total_chars - max_chars,
        omitted_lines=0,  # Unknown without re-counting
        omitted_tokens=0,  # Unknown without re-counting
        head_kept=head_chars,
        tail_kept=tail_chars,
        limit_type=limit_type,
        limit_value=limit_value,
        head_ratio=head_ratio,
    )


def _truncate_lines(
    content: str,
    max_lines: int,
    head_ratio: float,
    total_chars: int,
    total_lines: int,
    total_tokens: int,
    limit_type: str,
    limit_value: int,
) -> tuple[str, dict[str, Any]]:
    """Truncate by line count, preserving line breaks."""
    lines = content.splitlines(keepends=True)
    head_lines = int(max_lines * head_ratio)
    tail_lines = max_lines - head_lines

    if head_ratio >= 1.0:
        # All from beginning (Qwen-style)
        truncated = "".join(lines[:max_lines])
        omitted_lines = len(lines) - max_lines
        return truncated, _build_metadata(
            truncated=True,
            total_chars=total_chars,
            total_lines=total_lines,
            total_tokens=total_tokens,
            omitted_chars=0,  # Unknown without re-counting
            omitted_lines=omitted_lines,
            omitted_tokens=0,  # Unknown without re-counting
            head_kept=max_lines,
            tail_kept=0,
            limit_type=limit_type,
            limit_value=limit_value,
            head_ratio=head_ratio,
        )

    # Split: head + tail
    head = "".join(lines[:head_lines])
    tail = "".join(lines[-tail_lines:]) if tail_lines > 0 else ""
    truncated = head + tail
    omitted_lines = len(lines) - max_lines
    return truncated, _build_metadata(
        truncated=True,
        total_chars=total_chars,
        total_lines=total_lines,
        total_tokens=total_tokens,
        omitted_chars=0,  # Unknown without re-counting
        omitted_lines=omitted_lines,
        omitted_tokens=0,  # Unknown without re-counting
        head_kept=head_lines,
        tail_kept=tail_lines,
        limit_type=limit_type,
        limit_value=limit_value,
        head_ratio=head_ratio,
    )


def _truncate_tokens(
    content: str,
    max_tokens: int,
    head_ratio: float,
    total_chars: int,
    total_lines: int,
    total_tokens: int,
    limit_type: str,
    limit_value: int,
) -> tuple[str, dict[str, Any]]:
    """Token-aware truncation using Codex's approximation (len//4).

    This converts the token budget to a character budget and delegates
    to _truncate_chars, exactly matching Codex CLI behavior.
    """
    # Convert token budget to char budget
    max_chars = max_tokens * APPROX_BYTES_PER_TOKEN
    omitted_tokens = total_tokens - max_tokens

    truncated, metadata = _truncate_chars(
        content,
        max_chars,
        head_ratio,
        total_chars,
        total_lines,
        total_tokens,
        limit_type,
        limit_value,
    )
    # Update the omitted_tokens which _truncate_chars can't compute
    metadata = {**metadata, "omitted_tokens": omitted_tokens}
    return truncated, metadata


def truncate_output(
    content: str,
    *,
    limit_type: Literal["chars"] | Literal["lines"] | Literal["tokens"],
    limit_value: int,
    head_ratio: float = 0.5,
) -> tuple[str, dict[str, Any]]:
    """Truncate content and return (truncated_content, metadata).

    Truncation behavior:
    - limit_type="chars": truncate by character count
    - limit_type="lines": truncate by line count
    - limit_type="tokens": truncate by token count (using Codex approximation: len//4)

    head_ratio controls distribution:
    - head_ratio=1.0: keep first N chars/lines/tokens (standard head truncation, Qwen-style)
    - head_ratio=0.5: keep first 50% + last 50% (Codex-style split, DEFAULT)
    - head_ratio=0.2: keep first 20% + last 80% (Gemini-style split)

    Args:
        content: The text to potentially truncate.
        limit_type: Type of limit - "chars", "lines", or "tokens".
        limit_value: Maximum number of units to keep.
        head_ratio: How to split the budget between head and tail. Default 0.5 (50/50).

    Returns:
        Tuple of (truncated_content, metadata_dict) where metadata contains:
            - truncated: bool - whether truncation was applied
            - total_chars: int - original character count
            - total_lines: int - original line count
            - total_tokens: int - approximate original token count
            - omitted_chars: int - characters removed (0 if limit_type != "chars")
            - omitted_lines: int - lines removed (0 if limit_type != "lines")
            - omitted_tokens: int - tokens removed (0 if limit_type != "tokens")
            - head_kept: int - units kept from beginning
            - tail_kept: int - units kept from end
            - limit_type: str - the limit type used
            - limit_value: int - the limit value used
            - head_ratio: float - the head ratio used
    """
    # Calculate totals (always cheap)
    total_chars = len(content)
    total_lines = len(content.splitlines())
    total_tokens = approx_token_count(content)

    # Check if truncation needed
    current_value = {
        "chars": total_chars,
        "lines": total_lines,
        "tokens": total_tokens,
    }[limit_type]

    if current_value <= limit_value:
        return content, _build_metadata(
            truncated=False,
            total_chars=total_chars,
            total_lines=total_lines,
            total_tokens=total_tokens,
            omitted_chars=0,
            omitted_lines=0,
            omitted_tokens=0,
            head_kept=current_value,
            tail_kept=0,
            limit_type=limit_type,
            limit_value=limit_value,
            head_ratio=head_ratio,
        )

    # Apply truncation based on limit_type
    if limit_type == "tokens":
        return _truncate_tokens(
            content,
            limit_value,
            head_ratio,
            total_chars,
            total_lines,
            total_tokens,
            limit_type,
            limit_value,
        )
    elif limit_type == "lines":
        return _truncate_lines(
            content,
            limit_value,
            head_ratio,
            total_chars,
            total_lines,
            total_tokens,
            limit_type,
            limit_value,
        )
    else:  # chars
        return _truncate_chars(
            content,
            limit_value,
            head_ratio,
            total_chars,
            total_lines,
            total_tokens,
            limit_type,
            limit_value,
        )


__all__ = [
    "BACKGROUND_DELAY_SECONDS",
    "BACKGROUND_MAX_LINES",
    "BACKGROUND_READ_TIMEOUT",
    "ShellInfo",
    "approx_token_count",
    "build_shell_args",
    "detect_shell",
    "run_shell_command",
    "truncate_output",
]