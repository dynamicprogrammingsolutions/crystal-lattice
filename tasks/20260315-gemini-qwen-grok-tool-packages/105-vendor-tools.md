# 105 - Vendor Shell Tools (Gemini, Qwen, Grok, Kimi)

Short description: Create vendor-specific shell tool wrappers for Gemini, Qwen, Grok, and Kimi using the shared shell engine.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/100-shell-tools.md`

Depends On:
- `tasks/20260315-gemini-qwen-grok-tool-packages/101-shell-engine-core.md`
- `tasks/20260315-gemini-qwen-grok-tool-packages/102-shell-engine-truncation.md`
- `tasks/20260315-gemini-qwen-grok-tool-packages/103-shell-engine-background.md`

## Requirements checklist

- [x] Create `plugins/gemini-tools/src/gemini_tools/gemini_shell_tool.py`
- [x] Create `plugins/qwen-tools/src/qwen_tools/qwen_shell_tool.py`
- [x] Create `plugins/grok-tools/src/grok_tools/grok_shell_tool.py`
- [x] Create `plugins/kimi-tools/src/kimi_tools/kimi_shell_tool.py`
- [x] All tools achieve model-facing behavior parity with original CLI implementations
- [x] Update package exports and READMEs

## Goal

Create thin vendor-specific wrappers that call the shared shell engine with appropriate parameters and format output according to each vendor's conventions.

## Vendor Comparison Table

| Aspect | Gemini | Qwen | Grok | Kimi |
|--------|--------|------|------|------|
| Tool name | `run_shell_command` | `bash` | `bash` | `Shell` |
| Command param | `command` | `command` | `command` | `command` |
| Working dir param | `dir_path` | `directory` | (none) | (none) |
| Timeout param | (config) | `timeout` (ms) | (none) | `timeout` (s) |
| Timeout default | 120s | 120000ms | — | 60s |
| Max timeout | (configurable) | 600000ms | — | 300s |
| Description param | `description` | `description` | (none) | (none) |
| Background param | `is_background` | `is_background` | (none) | (none) |
| Truncation | 40k chars, 20/80 | 25k chars OR 1k lines | None | None |
| Clean env | No | No | No | Yes |

---

## Gemini Shell Tool

### Schema

```python
{
    "type": "function",
    "function": {
        "name": "run_shell_command",
        "description": "...",  # From Gemini CLI
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "..."},
                "description": {"type": "string", "description": "..."},
                "dir_path": {"type": "string", "description": "..."},
                "is_background": {"type": "boolean", "description": "..."},
            },
            "required": ["command"],
        },
    },
}
```

### Output Formatting

**Success:**
```
Output: <combined output>
```

**Failure:**
```
Output: <combined output>
Error: <error message>
Exit Code: <n>
```

**Background:**
```
Command moved to background (PID: 12345). Output hidden.
```

**Timeout:**
```
Command was automatically cancelled because it exceeded the timeout of X.X minutes without output.
Below is the output before it was cancelled:
<output>
```

**Truncation:**
```
Output too large. Showing first 8,000 and last 32,000 characters. For full output see: /path/to/file.txt
<head content>

... [omitted chars] ...

<tail content>
```

### Truncation Parameters

```python
result = await run_shell_command(
    command,
    workdir=dir_path,
    timeout_seconds=timeout,
    limit_type="chars",
    limit_value=40_000,
    head_ratio=0.2,  # 20% head, 80% tail
    is_background=is_background,
)
```

### Source Reference

- `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/shell.ts`
- `/Users/ferenci84/Dev/Mine/gemini-cli/packages/core/src/tools/definitions/coreTools.ts`

---

## Qwen Shell Tool

### Schema

```python
{
    "type": "function",
    "function": {
        "name": "bash",
        "description": "...",  # From Qwen CLI
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "..."},
                "timeout": {"type": "number", "description": "Timeout in milliseconds"},
                "description": {"type": "string", "description": "..."},
                "directory": {"type": "string", "description": "..."},
                "is_background": {"type": "boolean", "description": "..."},
            },
            "required": ["command"],
        },
    },
}
```

### Output Formatting

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

**Background:**
```
Background command started. PID: 12345 (Use kill 12345 to stop)
```

**On Windows:**
```
Background command started. PID: 12345 (Use taskkill /F /T /PID 12345 to stop)
```

### Truncation Parameters

Qwen uses **line-first, then char** truncation. Two calls to shared engine:

```python
# First: line limit
result = await run_shell_command(
    command,
    workdir=directory,
    timeout_seconds=timeout_ms / 1000,
    limit_type="lines",
    limit_value=1_000,
    head_ratio=1.0,
    is_background=is_background,
)

# Note: Char limit (25k) is handled separately if needed
# Or could be a second pass if lines don't trigger truncation
```

### Source Reference

- `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/shell.ts`
- `/Users/ferenci84/Dev/Mine/qwen-code/packages/core/src/tools/tool-names.ts`

---

## Grok Shell Tool

### Schema

```python
{
    "type": "function",
    "function": {
        "name": "bash",
        "description": "Execute a bash command",
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "The bash command to execute"},
            },
            "required": ["command"],
        },
    },
}
```

### Output Formatting

Grok has **minimal schema** - appears to return raw output without special formatting headers. No timeout, no workdir, no env params.

### Truncation

None - Grok CLI has no visible output limits.

### Parameters

```python
result = await run_shell_command(
    command,
    # No special parameters - minimal configuration
)
```

### Source Reference

- `/Users/ferenci84/Dev/Mine/grok-cli/src/grok/tools.ts`

---

## Kimi Shell Tool

### Schema

```python
{
    "type": "function",
    "function": {
        "name": "Shell",
        "description": "...",  # Loaded from bash.md or powershell.md
        "parameters": {
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "..."},
                "timeout": {"type": "integer", "description": "...", "default": 60},
            },
            "required": ["command"],
        },
    },
}
```

### Output Formatting

**Success:**
```
<combined output>
Command executed successfully.
```

**Failure:**
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

### Special Features

1. **Clean environment** - Uses `get_clean_env()` to strip PyInstaller-modified variables
2. **PowerShell detection** - Auto-detects PowerShell on Windows with different description template

### Parameters

```python
from tool_compat_shared.shell_engine import get_clean_env

result = await run_shell_command(
    command,
    timeout_seconds=timeout,
    env=get_clean_env(),  # Clean environment
)
```

### Source Reference

- `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/shell/__init__.py`
- `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/utils/subprocess_env.py`
- `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/shell/bash.md`
- `/Users/ferenci84/Dev/Mine/kimi-cli/src/kimi_cli/tools/shell/powershell.md`

---

## Out of Scope Features

The following are host-side UX features that should NOT be implemented in the tool plugins:

1. **Command allowlisting/permission checks** (Qwen) - host-side approval flow
2. **Interactive shell sessions** - no vendor supports this in tool scope
3. **Sandbox permissions** (Codex `sandbox_permissions`, `justification`, `prefix_rule`) - host-side security
4. **Apply_patch interception** (Codex) - host-side routing

---

## Tests

Each vendor tool should have tests for:

1. Schema validation: tool name, parameter names, types, required fields
2. Success case: `echo hello` → correct output format
3. Failure case: `exit 1` → correct error format
4. Timeout: long command → correct timeout message
5. Background (Gemini, Qwen only): `is_background=True` → correct background message
6. Working directory (Gemini, Qwen only): verify execution in specified directory
7. Clean environment (Kimi only): verify environment differs from full

---

## Deliverables

1. `plugins/gemini-tools/src/gemini_tools/gemini_shell_tool.py`
2. `plugins/qwen-tools/src/qwen_tools/qwen_shell_tool.py`
3. `plugins/grok-tools/src/grok_tools/grok_shell_tool.py`
4. `plugins/kimi-tools/src/kimi_tools/kimi_shell_tool.py`
5. Updated `__init__.py` files for each package
6. Tests for each vendor tool
7. Updated READMEs

---

## Notes for completing agent

- Finalize each vendor's output formatting by reading original CLI source
- Verify timeout units: Gemini (seconds), Qwen (milliseconds), Kimi (seconds)
- For Kimi, implement `get_clean_env()` integration
- For Gemini truncation, implement temp file saving for full output reference
- This task can be split further if needed (one vendor per pass)

## Completion notes

**Implementation completed successfully.**

### Files created:

1. **`plugins/gemini-tools/src/gemini_tools/gemini_shell_tool.py`**
   - Tool name: `run_shell_command`
   - Parameters: `command`, `description`, `dir_path`, `is_background`
   - Timeout: 120s default (configurable via `shell_timeout_seconds`)
   - Truncation: 40k chars with 20/80 head/tail split
   - Temp file saving for truncated output in `project_temp_dir`

2. **`plugins/qwen-tools/src/qwen_tools/qwen_shell_tool.py`**
   - Tool name: `bash`
   - Parameters: `command`, `timeout` (ms), `description`, `directory`, `is_background`
   - Timeout: 120s default, 600s max (configurable)
   - Truncation: Line-first (1k lines), then char (25k chars), head-only
   - Platform-specific kill hints for background processes

3. **`plugins/grok-tools/src/grok_tools/grok_shell_tool.py`**
   - Tool name: `bash`
   - Minimal schema: only `command` parameter
   - No timeout, no working directory, no background, no truncation
   - Raw output format

4. **`plugins/kimi-tools/src/kimi_tools/kimi_shell_tool.py`**
   - Tool name: `Shell`
   - Parameters: `command`, `timeout` (seconds)
   - Timeout: 60s default, 300s max
   - Clean environment via `get_clean_env()` (removes PyInstaller variables)
   - No truncation

### Files modified:

1. **`plugins/gemini-tools/src/gemini_tools/__init__.py`** - Added `GeminiShellTool` export
2. **`plugins/qwen-tools/src/qwen_tools/__init__.py`** - Added `QwenShellTool` export
3. **`plugins/grok-tools/src/grok_tools/__init__.py`** - Added `GrokShellTool` export
4. **`plugins/kimi-tools/src/kimi_tools/__init__.py`** - Added `KimiShellTool` export

5. **`plugins/gemini-tools/README.md`** - Added shell tool documentation and config keys
6. **`plugins/qwen-tools/README.md`** - Added shell tool documentation and config keys
7. **`plugins/grok-tools/README.md`** - Added shell tool documentation
8. **`plugins/kimi-tools/README.md`** - Added shell tool documentation and config keys

### Test files created:

1. **`plugins/gemini-tools/tests/test_gemini_shell_tool.py`** - 31 tests
2. **`plugins/qwen-tools/tests/test_qwen_shell_tool.py`** - 32 tests
3. **`plugins/grok-tools/tests/test_grok_shell_tool.py`** - 17 tests
4. **`plugins/kimi-tools/tests/test_kimi_shell_tool.py`** - 27 tests

### Test results:

All 107 tests passed.

### Config keys documented:

| Config Key | Gemini | Qwen | Kimi | Description |
|------------|--------|------|------|-------------|
| `shell_timeout_seconds` | 120 | 120 | 60 | Default timeout |
| `shell_max_timeout_seconds` | - | 600 | 300 | Maximum allowed timeout |
| `shell_max_output_chars` | 40000 | 25000 | - | Character limit |
| `shell_max_output_lines` | - | 1000 | - | Line limit |
| `shell_truncation_head_ratio` | 0.2 | 1.0 | - | Head/tail split ratio |
| `shell_clean_env` | - | - | true | Use clean environment |
| `project_temp_dir` | ✓ | ✓ | ✓ | Temp file storage |

### Design decisions:

1. **Kimi clean environment**: Implemented `get_clean_env()` inline in the Kimi tool - removes PyInstaller/frozen-executable variables when running as frozen.

2. **Qwen dual truncation**: Two-pass truncation in the Qwen tool - first checks line count (1k lines), then char count (25k chars).

3. **Gemini temp file**: Truncated output saved to `project_temp_dir` with UUID-based filename.

4. **Config defaults**: Each vendor tool applies its own defaults to shared config keys (e.g., `shell_timeout_seconds` = 120 for Gemini, 60 for Kimi).