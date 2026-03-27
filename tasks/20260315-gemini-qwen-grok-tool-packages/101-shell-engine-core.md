# 101 - Shell Engine Core

Short description: Create the shared shell engine with asyncio subprocess execution, three-buffer output accumulation, shell detection, and basic timeout handling.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/100-shell-tools.md`

Depends On: None (first subtask)

## Requirements checklist

- [x] Create `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`
- [x] Implement `async def run_shell_command()` with asyncio subprocess
- [x] Three-buffer accumulation: combined (interleaved), stdout, stderr
- [x] Shell detection: `detect_shell()` returns shell path and args
- [x] Timeout handling with `asyncio.wait_for()`
- [x] Duration tracking with `time.monotonic()`
- [x] Return dict with: `exit_code`, `output`, `stdout`, `stderr`, `duration_seconds`, `timed_out`

## Goal

Implement the core shell execution engine that all vendor tools will use. This is the foundation - no truncation, no background mode, just execution and output capture.

## Interface (for approval)

```python
import asyncio
import time
from typing import Any, Literal

async def run_shell_command(
    command: str,
    *,
    workdir: str | None = None,
    timeout_seconds: float | None = None,
    env: dict[str, str] | None = None,
    shell_path: str | None = None,  # auto-detect if None
) -> dict[str, Any]:
    """
    Execute a shell command with interleaved output capture.
    
    Args:
        command: The shell command to execute
        workdir: Working directory (None = current directory)
        timeout_seconds: Timeout in seconds (None = no timeout)
        env: Environment variables (None = inherit current)
        shell_path: Shell executable path (None = auto-detect)
    
    Returns:
        {
            "exit_code": int | None,
            "output": str,           # Combined interleaved output
            "stdout": str,           # Separate stdout
            "stderr": str,           # Separate stderr
            "duration_seconds": float,
            "timed_out": bool,
        }
    """
```

## Implementation Pattern (from parent task research)

**Optimized asyncio approach with three buffers accumulated in real-time:**

```python
async def run_shell_command(
    command: str,
    *,
    workdir: str | None = None,
    timeout_seconds: float | None = None,
    env: dict[str, str] | None = None,
    shell_path: str | None = None,
) -> dict[str, Any]:
    shell = shell_path or detect_shell()
    args = build_shell_args(command, shell)
    
    start_time = time.monotonic()
    
    process = await asyncio.create_subprocess_exec(
        *args,
        cwd=workdir,
        env=env or {},
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    
    # Three buffers - all accumulated in real-time
    combined_chunks: list[str] = []   # Interleaved order
    stdout_chunks: list[str] = []     # Separate for Qwen
    stderr_chunks: list[str] = []     # Separate for Qwen
    
    async def read_stdout() -> None:
        if process.stdout is None:
            return
        async for line in process.stdout:
            decoded = line.decode(errors="replace")
            combined_chunks.append(decoded)
            stdout_chunks.append(decoded)
    
    async def read_stderr() -> None:
        if process.stderr is None:
            return
        async for line in process.stderr:
            decoded = line.decode(errors="replace")
            combined_chunks.append(decoded)
            stderr_chunks.append(decoded)
    
    try:
        if timeout_seconds:
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
        "exit_code": exit_code,
        "output": "".join(combined_chunks),
        "stdout": "".join(stdout_chunks),
        "stderr": "".join(stderr_chunks),
        "duration_seconds": duration,
        "timed_out": timed_out,
    }
```

**Why this is efficient:**
1. No polling - `async for` wakes immediately when data arrives
2. Single thread - asyncio event loop, no context switching
3. O(n) memory/compute - list append is O(1), join is O(n)
4. No per-chunk conditionals - just append to two lists per chunk
5. True interleaving - chunks appended in arrival order

## Shell Detection

```python
import os
import platform
import shutil
from dataclasses import dataclass

@dataclass(frozen=True)
class ShellInfo:
    name: str  # "bash", "sh", "powershell", "cmd"
    path: str
    args: tuple[str, ...]  # ("-c",) for bash, ("-command",) for powershell

def detect_shell() -> ShellInfo:
    """Detect the appropriate shell for the current platform."""
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
    if shell_path and os.path.exists(shell_path):
        name = os.path.basename(shell_path)
        return ShellInfo(name=name, path=shell_path, args=("-c",))

    # Fallback: check common bash locations
    for candidate in ["/bin/bash", "/usr/bin/bash", "/usr/local/bin/bash"]:
        if os.path.exists(candidate):
            return ShellInfo(name="bash", path=candidate, args=("-c",))

    # Final fallback to sh
    return ShellInfo(name="sh", path="/bin/sh", args=("-c",))

def build_shell_args(command: str, shell: ShellInfo | None = None) -> list[str]:
    """Build subprocess args for shell command execution."""
    if shell is None:
        shell = detect_shell()
    return [shell.path, *shell.args, command]
```

## Research Findings (from parent task)

| Vendor | Approach | Interleaving Quality |
|--------|----------|----------------------|
| **Gemini** | PTY (preferred), child_process fallback | Best (PTY), Approximate (fallback) |
| **Qwen** | PTY (preferred), child_process fallback | Best (PTY), **Broken** (fallback appends stderr at end) |
| **Kimi** | asyncio.gather, same builder | Good (matches our approach) |
| **Grok** | Unknown | Unknown |

Our asyncio approach matches Kimi's implementation and is **better than Qwen's child_process fallback**.

## Tests

- `plugins/tool-compat-shared/tests/test_shell_engine.py`
  - Basic execution: `echo hello` → output contains "hello"
  - Exit code: `exit 1` → exit_code=1
  - Timeout: long command killed → timed_out=True
  - Stderr capture: command writing to stderr → stderr in result
  - Combined output: both stdout and stderr → interleaved in `output`
  - Shell detection: verify correct shell on current platform
  - Working directory: verify command runs in specified directory

## Deliverables

1. `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`
   - `run_shell_command()` async function
   - `detect_shell()` function
   - `build_shell_args()` function
   - `ShellInfo` dataclass
2. `plugins/tool-compat-shared/tests/test_shell_engine.py`

## Notes for completing agent

- Finalize the interface before implementation and send for approval
- Consider whether to use line-by-line reading (`readline()`) or chunk reading (`read(n)`)
- Consider encoding handling (currently using `errors="replace"`)
- This chunk does NOT include truncation or background support

## Completion notes

**Implementation completed successfully.**

### Files created/modified:

1. **Created:** `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`
   - `ShellInfo` frozen dataclass with `name`, `path`, `args`
   - `detect_shell()` - platform-aware shell detection (Unix: SHELL env → /bin/bash → /bin/sh; Windows: PowerShell → cmd)
   - `build_shell_args()` - constructs subprocess argument list
   - `run_shell_command()` - async subprocess execution with three-buffer accumulation

2. **Modified:** `plugins/tool-compat-shared/src/tool_compat_shared/__init__.py`
   - Added exports: `ShellInfo`, `build_shell_args`, `detect_shell`, `run_shell_command`

3. **Created:** `plugins/tool-compat-shared/tests/test_shell_engine.py`
   - 21 tests covering shell detection, argument building, and command execution
   - Tests for: basic echo, exit codes, timeout, stderr capture, combined output, working directory, env override, duration tracking

### Test results:

All 21 tests passed:
- `TestDetectShell`: 5 tests for shell detection
- `TestBuildShellArgs`: 3 tests for argument building
- `TestRunShellCommand`: 13 tests for command execution

### Design decisions implemented:

- **Line-by-line reading**: Using `async for line in process.stdout` (matches Kimi pattern)
- **Encoding**: `errors="replace"` for graceful degradation
- **Return structure**: Uses `"ok": bool` consistent with other engines
- **Process termination on timeout**: `process.kill()` then `await process.wait()`
- **Environment**: Inherits `os.environ` by default; caller can override via `env` parameter