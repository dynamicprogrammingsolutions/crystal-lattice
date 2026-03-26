# 100 - Shell Tools (All Vendors)

Short description: Add vendor-compatible shell/command execution tools to `gemini-tools`, `qwen-tools`, `grok-tools`, and `kimi-tools`, sharing subprocess execution internals from `tool-compat-shared`, with Kimi's Python-native implementation as the first seed for the shared helper layer.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: `tasks/20260315-gemini-qwen-grok-tool-packages/090-kimi-tools.md`

## Requirements checklist

- [ ] Create shared shell engine in `tool-compat-shared`
- [ ] Shared engine uses combined stdout/stderr (interleaved at capture time)
- [ ] Shared engine implements token-aware truncation with tiktoken (optional dependency)
- [ ] Shared engine tracks `duration_seconds`, `timed_out`, `exit_code`
- [ ] Shared engine supports background process mode (return early with PID)
- [ ] Create Codex V2 shell tool using shared engine
- [ ] Codex V2 tool matches Codex CLI formatting requirements
- [ ] Port existing codex shell tests to Codex V2 tool
- [ ] Create Gemini shell tool (`run_shell_command`) with `is_background` param
- [ ] Create Qwen shell tool (`bash`) with `is_background` param
- [ ] Create Grok shell tool (`bash`)
- [ ] Create Kimi shell tool (`Shell`)
- [ ] All tools achieve model-facing behavior parity with original CLI implementations
- [ ] Update package exports and READMEs

## Goal

Add one tool type (shell command execution) across all four vendor packages. Each vendor exposes its own tool name, parameter names, timeout defaults, working directory handling, and result message formatting. The shared internal package provides the common subprocess execution, streaming, timeout, and clean-environment mechanics.

## Public package outcome

1. `plugins/gemini-tools/`
- `GeminiShellTool` (tool name: `run_shell_command`)
2. `plugins/qwen-tools/`
- `QwenShellTool` (tool name: `bash`)
3. `plugins/grok-tools/`
- `GrokShellTool` (tool name: `bash`)
4. `plugins/kimi-tools/`
- `KimiShellTool` (tool name: `Shell`)

## Related tasks

### Codex parity task (will be completed by this task)

**Task:** `tasks/20260225-codex-tools-parity/030-bash-tool-round-2-output-and-limits.md`

This task's completion will satisfy the Codex parity task requirements. Upon completion, update the codex parity task with:
- Status: COMPLETED VIA `tasks/20260315-gemini-qwen-grok-tool-packages/100-shell-tools.md`

### Requirements from codex parity task (must verify during implementation)

From `tasks/20260225-codex-tools-parity/030-bash-tool-round-2-output-and-limits.md`:

1. **Token-aware truncation:**
   - `max_output_tokens` parameter (tool arg where applicable)
   - Tool-level defaults in config
   - Fast heuristic: `len(text) / 4` as default token estimate
   - Optionally use `tiktoken` if available (feature-detect, do not require)
   - Remove "line limit" concept if Codex CLI doesn't have it
   - Truncation notes: `"Total output lines: …"` and/or `"... truncated …"`

2. **Result shape standardization:**
   - Add to result dict: `duration_seconds`, `timed_out: bool`
   - `truncation: { stdout: {reason, ...}, stderr: {reason, ...} }` (optional, for internal metadata only)
   - **Do not preserve output conventions that diverge from Codex CLI**

3. **Streaming consistency:**
   - First chunk includes same header as `to_display_format`
   - Final summary emitted even when stdout truncated
   - Final `result` dict always includes `success`

4. **Acceptance criteria:**
   - Deterministic truncation policy aligned with Codex CLI
   - Users/models can reliably detect truncation
   - `max_output_tokens` cap works with long lines

5. **Open questions (resolved):**
   - Structured JSON string output mode: defer
   - Separate stderr token caps: **shared budget** (single combined output)

## Key source references

### Gemini

- Shell tool implementation:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/shell.ts:456` (`class ShellTool`)
- Schema/declaration helpers:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/dynamic-declaration-helpers.ts` (`getShellDeclaration`, `getCommandDescription`)
- Config/definition wiring:
  - `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/coreTools.ts:176` (`getShellDefinition`)

### Qwen

- Shell tool implementation:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/shell.ts:527` (`class ShellTool`)
- Tool names:
  - `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/tool-names.ts:8`

### Grok

- Shell schema:
  - `/Users/ferenci84/Dev/Mine/grok-cli/src/grok/tools.ts:102` (`bash` tool definition)
- Agent guidance:
  - `/Users/ferenci84/Dev/Mine/grok-cli/src/agent/grok-agent.ts` (usage patterns)

### Kimi

- Shell tool implementation:
  - `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/shell/__init__.py` (`class Shell`)
- Bash description template:
  - `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/shell/bash.md`
- PowerShell description template:
  - `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/shell/powershell.md`
- Clean environment helper:
  - `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/utils/subprocess_env.py` (`get_clean_env`)

### Codex CLI (source of truth for Codex V2 tool)

- Shell tool schema:
  - `docs/codex-tools/shell_command/schema.without_request_permissions.json`
- Shared formatting behavior:
  - `docs/codex-tools/shared/README.md`
- Shell_command behavior:
  - `docs/codex-tools/shell_command/README.md`
- Current implementation (for reference, not to be modified):
  - `plugins/codex-tools/src/codex_tools/shell_tool.py`
- Current tests (to be ported):
  - `plugins/codex-tools/tests/test_shell_tool.py`

## Model-facing behavior parity requirement

**All vendor shell tools must achieve model-facing behavior parity with their original CLI implementations.** This means:

1. **Tool schema parity:** Tool name, parameter names, types, required fields, and descriptions must match the original CLI's tool schema exactly.

2. **Output formatting parity:** The formatted tool result (what the LLM sees) must match the original CLI's output format, including:
   - Success/failure message wording
   - Exit code reporting format
   - Timeout message format
   - Output structure (combined vs separate streams)
   - Truncation banners and markers

3. **Behavior parity:** Core behavior must match:
   - Timeout handling (default values, max limits)
   - Working directory handling
   - Environment variable handling
   - Empty command rejection

### Known limitations (explicitly out of scope)

The following are host-side UX features that should NOT be implemented in the tool plugins:

1. **Command allowlisting/permission checks** (Qwen) - host-side approval flow
2. **Interactive shell sessions** - no vendor supports this in tool scope
3. **Sandbox permissions** (Codex `sandbox_permissions`, `justification`, `prefix_rule`) - host-side security
4. **Apply_patch interception** (Codex) - host-side routing

### Background process capability (partial implementation)

**Implemented in this task (Tier 1 - Plugin level):**

| Feature | Status | Notes |
|---------|--------|-------|
| `is_background` schema param | ✅ Implement | For Gemini and Qwen tools |
| Skip timeout for background | ✅ Implement | No timeout enforcement when `is_background: true` |
| Append `&` on Unix | ✅ Implement | Simple string manipulation |
| Return early with PID | ✅ Implement | Don't wait for process completion |
| Initial output capture | ✅ Implement | Small delay (200ms) to capture startup errors |
| Kill hint in response | ✅ Implement | "Use kill <pid> to stop" |

**Postponed for future task (Tier 2 - Application level):**

| Feature | Status | Notes |
|---------|--------|-------|
| Background shell registry | ❌ Postponed | Requires application-layer state management |
| Streaming output after return | ❌ Postponed | Requires subscription mechanism |
| UI toggle (Ctrl+B, /shells) | ❌ Postponed | Requires terminal/HTTP app support |
| Process lifecycle management | ❌ Postponed | Kill/restart background processes |

**Future task reference:** `tasks/20260315-gemini-qwen-grok-tool-packages/135-background-process-management.md`

See the "Background Process Capability" section below for full implementation details.

### Source of truth for implementation

During implementation planning, **inspect and use the original CLI implementations as the source of truth:**

1. For Gemini: Read `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/shell.ts`
2. For Qwen: Read `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/shell.ts`
3. For Grok: Read `/Users/ferenci84/Dev/Mine/grok-cli/src/grok/tools.ts`
4. For Kimi: Read `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/shell/__init__.py`
5. For Codex: Read `docs/codex-tools/shell_command/*.json` and `docs/codex-tools/shared/README.md`

## Compatibility findings

### Shared internals are realistic

All four vendors share the same core mechanics:

1. Spawning a subprocess with a shell command.
2. **Combined stdout/stderr capture (interleaved at source)** - timing must be preserved.
3. Timeout enforcement (different defaults per vendor).
4. Working directory override (where supported).
5. Exit code interpretation and result message formatting.
6. Environment variable handling.

These should become shared helpers in `tool-compat-shared`.

### Stdout/stderr handling (critical design decision)

**All original CLI tools combine stdout and stderr into a single output stream:**

| Vendor | Handling | Evidence |
|--------|----------|----------|
| Gemini | Combined | `output: string` - "Combined stdout/stderr" in description |
| Qwen | Combined | `cumulativeOutput` - single stream via ShellExecutionService |
| Kimi | Combined | `builder.write()` for both callbacks - same builder |
| Grok | Combined | Minimal schema, implied combined |
| Codex CLI | Combined | `output` field in structured format |

**Design requirement:** The shared engine MUST interleave stdout and stderr at capture time. If captured separately, the relative timing of output lines is lost and cannot be reconstructed.

### Public schemas differ meaningfully

| Aspect | Gemini | Qwen | Grok | Kimi |
|--------|--------|------|------|------|
| Tool name | `run_shell_command` | `bash` | `bash` | `Shell` |
| Command param | `command` | `command` | `command` | `command` |
| Working dir param | `dir_path` | `directory` | (none) | (none — uses CWD) |
| Timeout param | (config) | `timeout` (milliseconds) | (none) | `timeout` (seconds) |
| Timeout default | 120s | 120000ms | — | 60s |
| Max timeout | (configurable) | 600000ms (10 min) | — | 300s (5 min) |
| Env param | (none) | (none) | (none) | (none — clean env) |
| Description param | `description` | `description` | (none) | (none) |
| Background param | `is_background` | `is_background` | (none) | (none) |
| PowerShell support | (none) | (none) | (none) | Yes (auto-detects) |

## Proposed shared internals in `tool-compat-shared`

Add a new module `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`:

1. **Subprocess execution**:
   - `run_shell_command(command, *, workdir, timeout_seconds, max_output_tokens, env, shell_path) -> dict`
   - Interleave stdout/stderr at capture time (preserve timing)
   - Timeout enforcement with process kill
   - Duration tracking

2. **Token-aware truncation**:
   - Use `tiktoken` if available (optional dependency)
   - Fallback to heuristic: `len(text) / 4`
   - Track `total_lines` for truncation header

3. **Shell detection**:
   - `detect_shell() -> (shell_path, shell_name, shell_args_func)`
   - PowerShell auto-detection on Windows

4. **Clean environment**:
   - `get_clean_env() -> dict` — safe environment construction (port Kimi's pattern)

## Response formatting requirement

Every vendor shell tool must match its CLI's LLM-visible output:

### Output Limits by Vendor

| Vendor | Limit Type | Value | Notes |
|--------|------------|-------|-------|
| **Gemini** | Execution buffer | 16 MB | Internal `MAX_CHILD_PROCESS_BUFFER_SIZE` |
| **Gemini** | Execution scrollback | 300,000 lines | Internal `SCROLLBACK_LIMIT` for PTY |
| **Gemini** | **LLM output threshold** | **40,000 chars** | `DEFAULT_TRUNCATE_TOOL_OUTPUT_THRESHOLD` - what's sent to model |
| **Qwen** | Truncation chars | 25,000 | `DEFAULT_TRUNCATE_TOOL_OUTPUT_THRESHOLD` |
| **Qwen** | Truncation lines | 1,000 | `DEFAULT_TRUNCATE_TOOL_OUTPUT_LINES` |
| **Grok** | None | N/A | Minimal schema, no limits visible |
| **Kimi** | Timeout | 60s default, 300s max | Seconds only |
| **Codex CLI** | Tokens | `max_output_tokens` param | Token-based, with heuristic fallback |

**Key insights:**
- Only Codex CLI uses token-based limits
- Gemini has **two levels of limits**: execution limits (16MB/300k lines) AND a separate LLM output threshold (40k chars)
- Gemini's LLM truncation shows first 20% + last 80% with file reference

### Important: Stdout/Stderr Tracking

**Qwen requires separate stdout/stderr tracking** for its failure output format:
```
Stdout: <stdout or (empty)>
Stderr: <stderr or (empty)>
```

**Design decision:** The shared engine should:
1. **Capture stdout and stderr separately** during execution
2. **Interleave them for combined output** (timing preserved)
3. **Return both combined output AND separate streams** in result dict:
   ```python
   {
       "output": str,      # combined interleaved
       "stdout": str,      # separate (for Qwen formatting)
       "stderr": str,      # separate (for Qwen formatting)
   }
   ```

This allows:
- Gemini, Kimi, Codex, Grok: Use `output` (combined)
- Qwen: Use `stdout` and `stderr` for failure formatting

### Gemini Output Formatting (verified from source)

**Success (exit code 0, no error):**
```
Output: <combined output>
```

**Failure (exit code != 0 or error):**
```
Output: <combined output>
Error: <error message>
Exit Code: <n>
Signal: <signal>   (if terminated by signal)
Background PIDs: <pids>   (if background processes started)
Process Group PGID: <pid>   (if available)
```

**Background mode:**
```
Command moved to background (PID: 12345). Output hidden. Press Ctrl+B to view.
```

**Timeout/aborted:**
```
Command was automatically cancelled because it exceeded the timeout of X.X minutes without output.
Below is the output before it was cancelled:
<output>
```

**Truncation (output > 40k chars):**
```
Output too large. Showing first 8,000 and last 32,000 characters. For full output see: /path/to/tool-outputs/shell_xxx.txt
<head content>

... [omitted chars] ...

<tail content>
```
Note: Shows first 20% + last 80% of threshold, saves full output to temp file.

### Qwen Output Formatting (verified from source)

**Success (exit code 0, no stderr):**
```
<combined stdout output>
```

**Failure (exit code != 0, error, signal, or stderr):**
```
Stdout: <stdout or (empty)>
Stderr: <stderr or (empty)>
Error: <error or (none)>
Exit Code: <code or (none)>
Signal: <signal or (none)>
```

**Background mode:**
```
Background command started. PID: 12345 (Use kill 12345 to stop)
```

**On Windows:**
```
Background command started. PID: 12345 (Use taskkill /F /T /PID 12345 to stop)
```

### Grok Output Formatting

**Minimal schema** - appears to return raw output without special formatting headers. No timeout, no workdir, no env params.

### Kimi Output Formatting (verified from source)

**Success (exit code 0):**
```
<combined output>
Command executed successfully.
```
Note: Status message comes **after** the output.

**Failure (exit code != 0):**
```
<combined output>
Command failed with exit code: N.
```

**Timeout:**
```
<partial output>
Command killed by timeout (Ns)
```

**Empty command:**
```
Command cannot be empty.
```

### Codex CLI Output Formatting (for Codex V2 tool)

**Freeform format (used for `shell_command`):**

**Success:**
```
Exit code: 0
Wall time: 1.5 seconds
Output:
<combined output>
```

**Truncated:**
```
Exit code: 0
Wall time: 1.5 seconds
Total output lines: 5000

<output prefix>
... truncated, 3000 more tokens
```

**Failure (exit code != 0):**
- Returned as **tool error** with formatted output inline

**Structured JSON format** (default for other exec tools):
```json
{
  "metadata": {
    "exit_code": 0,
    "duration_seconds": 1.5
  },
  "output": "<combined output>"
}
```

### Summary Comparison

| Aspect | Gemini | Qwen | Grok | Kimi | Codex CLI |
|--------|--------|------|------|------|-----------|
| **Limit type** | Lines (300k) | Chars (25k) + Lines (1k) | None | Timeout only | **Tokens** |
| **Token-aware** | No | No | No | No | **Yes** |
| **Combined output** | Yes | Yes | Yes | Yes | Yes |
| **Status message position** | Before output | Headers before | N/A | **After output** | Headers before |
| **Duration tracking** | No | No | No | No | **Yes** |
| **Truncation marker** | `[GEMINI_CLI_WARNING: ...]` | `[N files truncated]` | N/A | N/A | `Total output lines: N` |

5. **Output content**: stdout and stderr **combined and interleaved** as produced by the subprocess.

Implementation pattern: shared helper produces vendor-neutral result `{exit_code, output, duration_seconds, timed_out, truncated, total_lines}`; vendor wrapper applies vendor-specific message formatting.

## Behavior requirements

### Gemini (`run_shell_command`)

1. Params: `command` (required), `description`, `dir_path`, `is_background`.
2. `dir_path` sets working directory for command execution.
3. Verify timeout default (120s) and max from source during implementation.
4. Schema description should match Gemini CLI's shell tool description.
5. Output: combined stdout/stderr.

### Qwen (`bash`)

1. Params: `command` (required), `timeout` (milliseconds), `description`, `directory`, `is_background`.
2. `timeout` in milliseconds, max 600000 (10 min), default 120000ms (2 min).
3. `directory` must be absolute and within workspace.
4. `description` is a brief user-facing description of the command.
5. `is_background` for long-running processes (schema only, no actual background management).
6. Command allowlist validation: out of scope (host-side UX).
7. Output: combined stdout/stderr.

### Grok (`bash`)

1. Params: `command` (required). Minimal schema.
2. No timeout, no workdir, no env params.
3. Schema description matches Grok CLI's `"Execute a bash command"`.
4. Output: combined stdout/stderr.

### Kimi (`Shell`)

1. Params: `command` (required), `timeout` (seconds, default 60, max 300).
2. Uses clean environment (no inheritance of potentially unsafe vars).
3. Auto-detects PowerShell on Windows with different description template.
4. Shell invocation: `(shell_path, "-c", command)` for bash, `(shell_path, "-command", command)` for PowerShell.
5. Output: combined stdout/stderr (already implemented this way).
6. Timeout kills process via `asyncio.wait_for` + `process.kill()`.

### Codex V2 (`shell_command`)

1. Params: `command` (required), `workdir`, `timeout_ms`, `max_output_tokens`.
2. Output formatting (freeform text per Codex CLI):
   ```
   Exit code: <n>
   Wall time: <sec> seconds
   Total output lines: <N>   (only if truncated)
   Output:
   <combined output>
   ```
3. Non-zero exit code → return as tool error with formatted output inline.
4. Token-aware truncation with single budget for combined output.
5. Sandbox permissions params: out of scope for this implementation.

## Background Process Capability

### Overview

Gemini and Qwen CLIs support running shell commands in the background via the `is_background` parameter. This allows long-running processes (development servers, watchers, daemons) to continue while the agent proceeds with other work.

### Vendor Implementation Analysis

#### Gemini CLI Background Implementation

**Source:** `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/shell.ts`

**Behavior when `is_background: true`:**
1. After 200ms delay, calls `ShellExecutionService.background(pid)` to resolve the promise
2. Process continues running; PTY/child process stays alive
3. Returns immediately with:
   ```
   Command moved to background (PID: 12345). Output hidden. Press Ctrl+B to view.
   ```
4. Host-side registry (`backgroundShells: Map<number, BackgroundShell>`) tracks process
5. UI supports `Ctrl+B` or `/shells` to view background process output
6. Streaming continues to the registered shell entry

**Key code pattern:**
```typescript
if (this.params.is_background) {
  setTimeout(() => {
    ShellExecutionService.background(pid);  // Resolve promise, keep PTY alive
  }, BACKGROUND_DELAY_MS);  // 200ms
}

// Return data includes PID for registry
data = { pid: result.pid, command: this.params.command, initialOutput: result.output };
```

#### Qwen CLI Background Implementation

**Source:** `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/shell.ts`

**Behavior when `is_background: true`:**
1. No timeout applied (`effectiveTimeout = undefined`)
2. On Unix: appends `&` to command if not already present
3. On Windows: uses race logic (returns early without detaching)
4. Returns immediately with:
   ```
   Background command started. PID: 12345 (Use kill 12345 to stop)
   ```
5. **No host-side registry** - user must manually manage with `kill <pid>`

**Key code pattern:**
```typescript
const effectiveTimeout = this.params.is_background
  ? undefined
  : (this.params.timeout ?? DEFAULT_FOREGROUND_TIMEOUT_MS);

// Append & on Unix
if (!isWindows && shouldRunInBackground && !finalCommand.trim().endsWith('&')) {
  finalCommand = finalCommand.trim() + ' &';
}

// Return early
return {
  llmContent: `Background command started.${pidMsg}${killHint}`,
  returnDisplay: `Background command started.${pidMsg}${killHint}`,
};
```

### Implementation Tiers

#### Tier 1: Plugin-Level (IMPLEMENTED IN THIS TASK)

The shared shell engine and vendor tools will implement:

| Feature | Implementation |
|---------|----------------|
| Schema param | Add `is_background: boolean` to Gemini and Qwen tools |
| Timeout skip | When `is_background: true`, set `timeout_seconds = None` |
| Unix backgrounding | Append `&` to command if not already present |
| Windows handling | No `&` append (Windows doesn't support shell backgrounding the same way) |
| Early return | Don't wait for process completion |
| Initial output | Capture ~200ms of output to detect startup errors |
| PID in response | Return `pid` field for user reference |
| Kill hint | Include "Use kill <pid> to stop" or Windows equivalent |

**Shared engine function signature:**
```python
def run_shell_command(
    command: str,
    *,
    is_background: bool = False,
    # ... other params
) -> dict:
    """
    Returns for background:
    {
        "exit_code": None,  # Not known yet
        "output": str,      # Initial output (~200ms)
        "pid": int,         # Process ID
        "background": True,
        "duration_seconds": float,
        "message": "Background command started. PID: 12345 (Use kill 12345 to stop)",
    }
    """
```

**Gemini tool response:**
```
Command moved to background (PID: 12345). Output hidden.
```

**Qwen tool response:**
```
Background command started. PID: 12345 (Use kill 12345 to stop)
```

#### Tier 2: Application-Level (POSTPONED)

**Future task:** `tasks/20260315-gemini-qwen-grok-tool-packages/140-background-process-management.md`

The following features require application-layer support and are NOT implemented in this task:

| Feature | Description | Why Postponed |
|---------|-------------|---------------|
| Background shell registry | `Map<number, BackgroundShell>` in application state | Requires app-layer state management |
| Output streaming after return | Continue capturing output after tool returns | Requires subscription mechanism |
| UI toggle (Ctrl+B) | Toggle visibility of background shells panel | Requires terminal app support |
| `/shells` command | View/manage background processes | Requires terminal app command system |
| Process lifecycle | Kill/restart background processes via UI | Requires persistent state + UI actions |

### Plugin Implementation Details

**Shared engine changes:**
```python
# In shell_engine.py

def run_shell_command(
    command: str,
    *,
    is_background: bool = False,
    workdir: str | None = None,
    timeout_seconds: float | None = None,
    max_output_tokens: int | None = None,
    env: dict[str, str] | None = None,
    shell_path: str | None = None,
) -> dict:
    
    is_windows = sys.platform == "win32"
    
    if is_background:
        # Skip timeout for background processes
        timeout_seconds = None
        
        # Append & on Unix for shell backgrounding
        if not is_windows and not command.rstrip().endswith('&'):
            command = command.rstrip() + ' &'
    
    # Spawn process
    process = subprocess.Popen(
        build_shell_args(command, shell_path),
        cwd=workdir,
        env=env or os.environ.copy(),
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        # Don't use subprocess' built-in timeout for background
    )
    
    pid = process.pid
    
    if is_background:
        # Small delay to capture initial output / startup errors
        import time
        time.sleep(0.2)  # 200ms like Gemini CLI
        
        # Capture whatever output is available
        initial_output = capture_available_output(process)
        
        return {
            "exit_code": None,
            "output": initial_output,
            "pid": pid,
            "background": True,
            "duration_seconds": 0.2,
            "timed_out": False,
            "truncated": False,
        }
    
    # Normal foreground execution...
```

**Gemini vendor wrapper:**
```python
def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
    if result.get("background"):
        pid = result.get("pid")
        return f"Command moved to background (PID: {pid}). Output hidden."
    # ... normal formatting
```

**Qwen vendor wrapper:**
```python
def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
    if result.get("background"):
        pid = result.get("pid")
        is_windows = sys.platform == "win32"
        kill_hint = " (Use taskkill /F /T /PID {pid} to stop)" if is_windows else f" (Use kill {pid} to stop)"
        return f"Background command started. PID: {pid}{kill_hint}"
    # ... normal formatting
```

### Tests for Background Process

1. **Gemini background:**
   - `is_background: true` → returns immediately with PID
   - Response contains "moved to background"
   - Timeout is NOT applied
   - `&` is appended on Unix

2. **Qwen background:**
   - `is_background: true` → returns immediately with PID
   - Response contains kill hint
   - Timeout is NOT applied
   - `&` is appended on Unix (not Windows)

3. **Initial output capture:**
   - Startup error (e.g., `command not found`) appears in initial output
   - Process continues running after return

## Test plan

### Shared engine tests

1. Token truncation: verify `max_output_tokens` cap works with long lines.
2. Combined output: verify stdout and stderr are interleaved correctly.
3. Duration tracking: verify `duration_seconds` is accurate.
4. Timeout: verify process is killed and `timed_out` is set.
5. Shell detection: verify bash and PowerShell detection.

### Schema tests (all vendors)

1. Assert exact tool names per vendor.
2. Assert parameter names, types, required fields, defaults.
3. Assert description text matches vendor.

### Shell execution tests (all vendors)

1. Simple command: `echo hello` → output contains `"hello"`, success message.
2. Non-zero exit code: `false` or `exit 1` → failure message with exit code.
3. Timeout: long-running command killed by timeout → timeout message.
4. Stderr capture: command that writes to stderr → stderr in combined output.
5. Empty command → rejection error.
6. Combined output: command writing to both stdout and stderr → verify interleaving.

### Vendor-specific tests

1. Gemini: `dir_path` parameter sets working directory.
2. Gemini: `is_background: true` → returns immediately with PID, "moved to background" message.
3. Qwen: `timeout` in milliseconds, `directory` validation, max 600000 enforcement.
4. Qwen: `is_background: true` → returns immediately with PID, kill hint in message.
5. Kimi: clean environment (e.g. `env` or `printenv` output differs from full environment), PowerShell detection helper.
6. Grok: minimal schema (no timeout/workdir/env).
7. Codex V2: verify output formatting matches Codex CLI freeform style.

### Background process tests

1. **Gemini background:**
   - `is_background: true` → response contains PID and "moved to background"
   - No timeout applied
   - `&` appended on Unix

2. **Qwen background:**
   - `is_background: true` → response contains PID and kill hint
   - No timeout applied
   - `&` appended on Unix (not Windows)

3. **Initial output capture:**
   - Startup error appears in initial output (within 200ms window)
   - Valid long-running process continues after return

### Integration tests

1. Each package loads through application plugin manager with shell tool exposed.
2. Real subprocess calls succeed.
3. OpenRouter integration tests (one per vendor package with cheap model).

### Ported tests from codex shell tool

Port relevant tests from `plugins/codex-tools/tests/test_shell_tool.py` to `plugins/codex-tools/tests/test_shell_command_tool.py`:

1. Basic command execution
2. Exit code handling (adapted for new formatting)
3. Timeout handling (adapted for new formatting)
4. Truncation (adapted for token-based)
5. Streaming tests (adapted for new combined output format)

## Deliverables

1. **Shared shell engine:** `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`
2. **Shared engine tests:** `plugins/tool-compat-shared/tests/test_shell_engine.py`
3. **Codex V2 shell tool:** `plugins/codex-tools/src/codex_tools/shell_command_tool.py`
4. **Codex V2 tests:** `plugins/codex-tools/tests/test_shell_command_tool.py`
5. **Four vendor-specific shell tool classes:**
   - `plugins/gemini-tools/src/gemini_tools/gemini_shell_tool.py`
   - `plugins/qwen-tools/src/qwen_tools/qwen_shell_tool.py`
   - `plugins/grok-tools/src/grok_tools/grok_shell_tool.py`
   - `plugins/kimi-tools/src/kimi_tools/kimi_shell_tool.py`
6. **Vendor shell tool tests**
7. **Package exports and READMEs updated**

## Documentation follow-up

After implementation, update each vendor package README with:

1. Exposed shell tool name and parameters.
2. Vendor-specific behavior notes (timeout units, workdir handling, env handling).
3. Known limitations (no allowlist, no background management, no interactive sessions).

---

## Execution plan

### Phase 1: Create shared shell engine

**File:** `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`

**Core function signature:**
```python
def run_shell_command(
    command: str,
    *,
    workdir: str | None = None,
    timeout_seconds: float | None = None,
    max_output_tokens: int | None = None,
    max_output_chars: int | None = None,  # for Gemini/Qwen char limits
    env: dict[str, str] | None = None,
    shell_path: str | None = None,  # auto-detect if None
) -> dict:
    """
    Execute a shell command and return combined and separate outputs.

    Returns:
    {
        "exit_code": int,
        "output": str,           # combined stdout+stderr interleaved (timing preserved)
        "stdout": str,           # separate stdout (for Qwen formatting)
        "stderr": str,           # separate stderr (for Qwen formatting)
        "duration_seconds": float,
        "timed_out": bool,
        "truncated": bool,
        "total_lines": int,
    }
    """
```

**Features to implement:**

1. **Subprocess execution:**
   - Use `subprocess.Popen` with stdout and stderr as pipes
   - **Track stdout and stderr separately** while capturing
   - **Interleave them for combined `output`** (preserve timing)
   - Track duration with `time.monotonic()`

2. **Truncation (multiple modes):**
   - **Token-based:** for Codex V2 (`max_output_tokens`) using `tiktoken` or heuristic
   - **Char-based:** for Gemini (40k default) and Qwen (25k default)
   - Track `total_lines` for truncation header
   - Add `tiktoken` as optional dependency in `pyproject.toml`

3. **Timeout enforcement:**
   - Use wall-clock timeout with process kill
   - Set `timed_out: bool` in result

4. **Shell detection:**
   - `detect_shell()` returns `(shell_path, shell_name, is_powershell)`
   - Auto-detect PowerShell on Windows via `os.name` and environment

5. **Clean environment helper:**
   - Port from `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/utils/subprocess_env.py`
   - `get_clean_env() -> dict[str, str]`

**Dependency update:**
- `plugins/tool-compat-shared/pyproject.toml`: add `tiktoken` as optional dependency

**Tests:**
- `plugins/tool-compat-shared/tests/test_shell_engine.py`

### Phase 2: Create Codex V2 shell tool

**File:** `plugins/codex-tools/src/codex_tools/shell_command_tool.py`

**Tool name:** `shell_command`

**Schema (from `docs/codex-tools/shell_command/schema.without_request_permissions.json`):**
```python
{
    "type": "function",
    "function": {
        "name": "shell_command",
        "description": "Runs a shell command and returns its output.\n- Always set the `workdir` param when using the shell_command function. Do not use `cd` unless absolutely necessary.",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The shell script to execute in the user's default shell"},
                "workdir": {"type": "string", "description": "The working directory to execute the command in"},
                "timeout_ms": {"type": "number", "description": "The timeout for the command in milliseconds"},
                "max_output_tokens": {"type": "number", "description": "Maximum output tokens before truncation"},
            },
            "required": ["command"],
        },
    },
}
```

**Output formatting (freeform text per `docs/codex-tools/shared/README.md`):**

Success case (exit code 0):
```
Exit code: 0
Wall time: 1.5 seconds
Output:
<combined output>
```

Truncated output:
```
Exit code: 0
Wall time: 1.5 seconds
Total output lines: 5000
Output:
<truncated output>
... truncated, 3000 more tokens
```

Error case (non-zero exit):
- Return as tool error with formatted output inline

**Tests (ported from existing):**
- `plugins/codex-tools/tests/test_shell_command_tool.py`
- Port relevant tests, adapt for:
  - Combined output format
  - Token-based truncation
  - Duration tracking
  - New formatting

### Phase 3: Create vendor shell tools

#### Gemini shell tool

**File:** `plugins/gemini-tools/src/gemini_tools/gemini_shell_tool.py`

- Inspect source: `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/shell.ts`
- Tool name: `run_shell_command`
- Params: `command`, `description`, `dir_path`, `is_background`
- Default timeout: 120s (verify from source)
- Output: combined

#### Qwen shell tool

**File:** `plugins/qwen-tools/src/qwen_tools/qwen_shell_tool.py`

- Inspect source: `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/shell.ts`
- Tool name: `bash`
- Params: `command`, `timeout` (ms), `description`, `directory`, `is_background`
- Max timeout: 600000ms
- Default timeout: 120000ms
- Output: combined

#### Grok shell tool

**File:** `plugins/grok-tools/src/grok_tools/grok_shell_tool.py`

- Inspect source: `/Users/ferenci84/Dev/Mine/grok-cli/src/grok/tools.ts`
- Tool name: `bash`
- Params: `command` only
- Minimal schema
- Output: combined

#### Kimi shell tool

**File:** `plugins/kimi-tools/src/kimi_tools/kimi_shell_tool.py`

- Inspect source: `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/shell/__init__.py`
- Tool name: `Shell`
- Params: `command`, `timeout` (s, default 60, max 300)
- Clean environment by default
- PowerShell auto-detection
- Output: combined

### Phase 4: Update exports

1. `plugins/tool-compat-shared/src/tool_compat_shared/__init__.py` - export shell engine functions
2. `plugins/codex-tools/src/codex_tools/__init__.py` - export `ShellCommandTool`
3. `plugins/gemini-tools/src/gemini_tools/__init__.py` - export `GeminiShellTool`
4. `plugins/qwen-tools/src/qwen_tools/__init__.py` - export `QwenShellTool`
5. `plugins/grok-tools/src/grok_tools/__init__.py` - export `GrokShellTool`
6. `plugins/kimi-tools/src/kimi_tools/__init__.py` - export `KimiShellTool`

### Phase 5: Verify codex parity requirements

After implementation, verify all requirements from `tasks/20260225-codex-tools-parity/030-bash-tool-round-2-output-and-limits.md`:

- [ ] Token-aware truncation with `max_output_tokens`
- [ ] Fast heuristic fallback (`len(text) / 4`)
- [ ] `tiktoken` optional, feature-detected
- [ ] `duration_seconds` tracked
- [ ] `timed_out: bool` tracked
- [ ] Combined output (single budget)
- [ ] Deterministic truncation policy
- [ ] Truncation reliably detectable
- [ ] Streaming consistency (first chunk header, final summary, result dict)

### Phase 6: Mark codex task as completed

Update `tasks/20260225-codex-tools-parity/030-bash-tool-round-2-output-and-limits.md`:

```markdown
## Status

COMPLETED VIA `tasks/20260315-gemini-qwen-grok-tool-packages/100-shell-tools.md`
```

---

## Outdated concepts removed

The following concepts from the original task exploration are now obsolete:

- ❌ Separate STDOUT/STDERR sections in **combined** output (all vendors use combined for normal output)
- ❌ `truncation: { stdout: {...}, stderr: {...} }` as separate token budgets (combined output has single budget)

### Concepts clarified (NOT obsolete)

- ✅ **Separate `stdout`/`stderr` tracking IS needed** for Qwen's failure formatting
- ✅ **Combined interleaved `output`** is the primary output field
- ✅ **Line/char-based truncation** is used by Gemini (40k chars) and Qwen (25k chars, 1k lines)
- ✅ **Token-based truncation** is used by Codex CLI only
- ✅ `max_output_tokens` is for Codex V2; other vendors use their native limits

---

## Remaining planning items (for next planning round)

The following items need detailed planning before implementation:

### 1. Streaming/Interleaving Implementation Strategy (High Priority)

**Question:** How exactly do we capture stdout and stderr separately while preserving timing for interleaving?

**Options:**
- A) Use `select` on Unix, threading on Windows
- B) Use threading for both (simpler, works cross-platform) - current codex shell_tool uses this
- C) Read from both streams into separate buffers with timestamps, then merge

**Decision needed:** Which approach? Reference existing `codex-tools/shell_tool.py` streaming implementation.

**Source reference:** `plugins/codex-tools/src/codex_tools/shell_tool.py:stream_tool` (lines 350-500)

---

### 2. Truncation Implementation Details (High Priority)

**Questions to resolve:**

**Gemini truncation (40k chars):**
- Implement 20%/80% split (head=8k, tail=32k)?
- Save full output to temp file? (Gemini does: `For full output see: /path/to/file.txt`)
- Where to save? Project temp dir? Session-scoped?

**Qwen truncation (25k chars OR 1k lines):**
- Which limit takes precedence?
- Apply to combined output or separately to stdout/stderr?
- Truncation marker format?

**Codex token truncation:**
- Exact tiktoken integration: `tiktoken.get_encoding("cl100k_base")`?
- Heuristic fallback: `len(text) / 4` - is this accurate enough?
- Truncation marker: `Total output lines: N` + `... truncated, X more tokens`

**Source references:**
- Gemini: `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/utils/fileUtils.ts:596` (`formatTruncatedToolOutput`)
- Qwen: `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/config/config.ts:227` (constants)

---

### 3. Platform-Specific Behavior (High Priority)

**Shell detection:**
- How to detect shell on Unix: Check `SHELL` env var, fallback to `/bin/bash`
- How to detect PowerShell on Windows: Check `PSModulePath`, `$PSHOME`, or `os.name == 'nt'`
- Shell args: `-c` for bash, `-command` for PowerShell

**Background process on Windows:**
- Qwen uses "race logic" - what is it exactly?
- Windows can't use `&` for backgrounding the same way
- Need to research from source: `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/shell.ts`

**Source references:**
- Kimi shell detection: `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/utils/environment.py`
- Qwen Windows handling: `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/shell.ts:163-170`

---

### 4. Configuration Wiring (Medium Priority)

**Questions:**
- How do users set `max_output_chars`, `max_output_tokens`, timeout defaults?
- Per-agent config in `agents.yaml`? Global config?
- Integration with existing `agent_app` config system?

**Existing patterns:**
- Vendor tools already use `config.get("working_directory")` etc.
- See existing vendor tools in `plugins/gemini-tools/` for config patterns

---

### 5. Integration Points (Medium Priority)

**Verify existing plugin loading works:**
- How do vendor tools register with the plugin system?
- Check `plugins/gemini-tools/pyproject.toml` for entry points
- Check how `TerminalApplication` loads plugin packages

**Source references:**
- Existing tool exports: `plugins/gemini-tools/src/gemini_tools/__init__.py`
- Plugin loading: `core/python/agent_core/plugin/`

---

### 6. Clean Environment Implementation (Low Priority)

**Simple port from Kimi:**
- Source: `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/utils/subprocess_env.py`
- Purpose: Strip PyInstaller-modified environment variables
- Usage: Kimi uses it always; other vendors may not need it

**Decision:** Make it optional/configurable per vendor.

---

## Completion notes

(To be filled during implementation)