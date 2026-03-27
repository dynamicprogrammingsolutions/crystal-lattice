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
from typing import Any


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


__all__ = [
    "ShellInfo",
    "build_shell_args",
    "detect_shell",
    "run_shell_command",
]