"""Shell command execution engine with asyncio subprocess support.

This module provides the core shell execution functionality used by all vendor
shell tools. It uses asyncio subprocess for efficient, non-blocking execution
with three-buffer output accumulation (combined/interleaved, stdout, stderr).

The implementation matches Kimi's approach and is more efficient than Qwen's
child_process fallback for output interleaving.
"""

from __future__ import annotations

import asyncio
import os
import platform
import shutil
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Literal


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


async def run_shell_command(
    command: str,
    *,
    workdir: str | None = None,
    timeout_seconds: float | None = None,
    env: dict[str, str] | None = None,
    shell: ShellInfo | None = None,
) -> dict[str, Any]:
    """Execute a shell command with interleaved output capture.

    Uses asyncio subprocess for efficient, non-blocking execution with
    three-buffer output accumulation:
    - combined: interleaved output in arrival order
    - stdout: separate stdout capture
    - stderr: separate stderr capture

    Args:
        command: The shell command to execute.
        workdir: Working directory. None means current directory.
        timeout_seconds: Timeout in seconds. None means no timeout.
        env: Environment variables. None means inherit os.environ.
        shell: Shell configuration. None means auto-detect via detect_shell().

    Returns:
        Dict with:
            - ok: bool (True if exit_code == 0 and not timed out)
            - exit_code: int | None (None if timed out)
            - output: str (combined interleaved output)
            - stdout: str (separate stdout)
            - stderr: str (separate stderr)
            - duration_seconds: float
            - timed_out: bool
            - shell: ShellInfo (shell used for execution)
    """
    shell = shell or detect_shell()
    args = build_shell_args(command, shell)

    start_time = time.monotonic()

    process = await asyncio.create_subprocess_exec(
        *args,
        cwd=workdir,
        env=env if env is not None else os.environ,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )

    # Three buffers - all accumulated in real-time
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
        process.kill()
        await process.wait()
        exit_code = None
        timed_out = True

    duration = time.monotonic() - start_time

    return {
        "ok": not timed_out and exit_code == 0,
        "exit_code": exit_code,
        "output": "".join(combined_chunks),
        "stdout": "".join(stdout_chunks),
        "stderr": "".join(stderr_chunks),
        "duration_seconds": duration,
        "timed_out": timed_out,
        "shell": shell,
    }


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
    "ShellInfo",
    "approx_token_count",
    "build_shell_args",
    "detect_shell",
    "run_shell_command",
    "truncate_output",
]