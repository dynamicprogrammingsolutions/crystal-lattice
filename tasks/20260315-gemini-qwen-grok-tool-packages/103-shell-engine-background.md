# 130 - Shell Engine Background Process Support

Short description: Add background process support to the shared shell engine for Gemini and Qwen tools.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/101-shell-engine-core.md`

## Requirements checklist

- [ ] Add `is_background` parameter to `run_shell_command()`
- [ ] Skip timeout when `is_background=True`
- [ ] Append `&` to command on Unix (not Windows)
- [ ] Return early after ~200ms with PID
- [ ] Capture initial output for startup error detection
- [ ] Include kill hint in result message

## Goal

Add support for running shell commands in background mode. This allows long-running processes (development servers, watchers) to continue while the agent proceeds with other work.

## Background Process Capability (Tier 1 - Plugin Level)

| Feature | Status | Notes |
|---------|--------|-------|
| `is_background` param | ✅ Implement | For Gemini and Qwen tools |
| Skip timeout | ✅ Implement | No timeout when `is_background: true` |
| Append `&` on Unix | ✅ Implement | Simple string manipulation |
| Return early with PID | ✅ Implement | Don't wait for completion |
| Initial output capture | ✅ Implement | Small delay to capture startup errors |
| Kill hint | ✅ Implement | "Use kill <pid> to stop" |

**Postponed (Tier 2 - Application level):** Registry, streaming after return, UI toggle, process lifecycle management.

## Interface Extension (for approval)

```python
async def run_shell_command(
    command: str,
    *,
    workdir: str | None = None,
    timeout_seconds: float | None = None,
    env: dict[str, str] | None = None,
    shell_path: str | None = None,
    is_background: bool = False,  # NEW
    ...
) -> dict[str, Any]:
    """
    Execute a shell command, optionally in background mode.
    
    Background mode behavior:
    - No timeout applied (timeout_seconds ignored)
    - On Unix: '&' appended to command if not present
    - Returns early after BACKGROUND_DELAY_MS with PID
    - Initial output captured for startup error detection
    """
```

## Return Data Structure (Extended for Background)

```python
{
    # Standard fields
    "exit_code": int | None,     # None for background processes
    "output": str,               # Initial output (~200ms)
    "stdout": str,
    "stderr": str,
    "duration_seconds": float,   # ~0.2 for background
    "timed_out": bool,           # Always False for background
    
    # Background-specific
    "background": bool,          # True if background mode
    "pid": int | None,           # Process ID
    "message": str,              # Human-readable message with kill hint
}
```

## Implementation Pattern

```python
import sys

BACKGROUND_DELAY_MS = 0.2  # 200ms, matches Gemini CLI

async def run_shell_command(
    command: str,
    *,
    is_background: bool = False,
    ...
) -> dict[str, Any]:
    
    is_windows = sys.platform == "win32"
    
    if is_background:
        # Skip timeout for background processes
        timeout_seconds = None
        
        # Append & on Unix for shell backgrounding
        if not is_windows and not command.rstrip().endswith('&'):
            command = command.rstrip() + ' &'
    
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
    
    pid = process.pid
    
    if is_background:
        # Small delay to capture initial output / startup errors
        await asyncio.sleep(BACKGROUND_DELAY_MS)
        
        # Non-blocking read of available output
        # Note: This is tricky with asyncio streams
        # Option: Use readline with timeout, or check if data available
        
        initial_output = await _capture_initial_output(process)
        
        kill_hint = (
            f" (Use taskkill /F /T /PID {pid} to stop)"
            if is_windows
            else f" (Use kill {pid} to stop)"
        )
        
        return {
            "exit_code": None,
            "output": initial_output["combined"],
            "stdout": initial_output["stdout"],
            "stderr": initial_output["stderr"],
            "duration_seconds": time.monotonic() - start_time,
            "timed_out": False,
            "background": True,
            "pid": pid,
            "message": f"Background command started. PID: {pid}{kill_hint}",
        }
    
    # ... standard foreground execution ...
```

## Platform Differences

### Unix
- Append `&` to command for shell backgrounding
- Process continues after tool returns
- Kill hint: `Use kill <pid> to stop`

### Windows
- Do NOT append `&` (Windows shell doesn't support it the same way)
- Process stays attached (not detached) so it dies when parent dies
- Kill hint: `Use taskkill /F /T /PID <pid> to stop`

## Research Findings (from Qwen source)

From `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/shell.ts:163-170`:

```typescript
// On non-Windows, use & to run in background.
// On Windows, we don't use start /B because it creates a detached process that
// doesn't die when the parent dies. Instead, we rely on the race logic below
// to return early while keeping the process attached (detached: false).
if (!isWindows && shouldRunInBackground && !finalCommand.trim().endsWith('&')) {
    finalCommand = finalCommand.trim() + ' &';
}

// On Windows, we rely on the race logic below to handle background tasks.
// We just ensure the command string is clean.
if (isWindows && shouldRunInBackground) {
    finalCommand = finalCommand.trim().replace(/&+$/, '').trim();
}
```

## Vendor Output Formatting

**Gemini background response:**
```
Command moved to background (PID: 12345). Output hidden.
```

**Qwen background response:**
```
Background command started. PID: 12345 (Use kill 12345 to stop)
```

**On Windows:**
```
Background command started. PID: 12345 (Use taskkill /F /T /PID 12345 to stop)
```

## Tests

- Background Unix: `is_background=True` → `&` appended, returns with PID
- Background Windows: `is_background=True` → no `&` appended, returns with PID
- No timeout applied: background process runs beyond timeout_seconds
- Initial output: startup error (e.g., `command not found`) captured in initial output
- Kill hint present: result["message"] contains correct platform-specific hint

## Deliverables

1. Updated `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`
   - `is_background` parameter
   - Background execution logic
   - Platform-specific handling
2. Updated `plugins/tool-compat-shared/tests/test_shell_engine.py`
   - Background mode tests

## Notes for completing agent

- Finalize the initial output capture approach for asyncio
- Consider whether to use `asyncio.wait_for` with timeout on readline, or another approach
- The background process continues running after return - no lifecycle management in this chunk
- This is Tier 1 only; Tier 2 (registry, streaming) is future work

## Completion notes

(To be filled during implementation)