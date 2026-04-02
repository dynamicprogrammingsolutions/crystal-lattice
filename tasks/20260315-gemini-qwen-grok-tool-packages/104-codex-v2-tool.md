# 104 - Codex Shell Tools (shell + shell_command)

Short description: Create both Codex shell tools (`shell` for array commands, `shell_command` for string commands) using the shared shell engine.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/100-shell-tools.md`

Depends On: 
- `tasks/20260315-gemini-qwen-grok-tool-packages/101-shell-engine-core.md`
- `tasks/20260315-gemini-qwen-grok-tool-packages/102-shell-engine-truncation.md`

## Related tasks (completion)

Upon completion, mark the following tasks as completed:

- `tasks/20260225-codex-tools-parity/020-bash-tool-round-1-schema.md` — COMPLETED VIA this task
- `tasks/20260225-codex-tools-parity/030-bash-tool-round-2-output-and-limits.md` — COMPLETED VIA this task

## Requirements checklist

### Shared Engine Update
- [x] Add support for array-based commands to `run_shell_command()` (accepts `str | list[str]`)
- [x] Add tests for array command execution

### shell_command Tool (string-based, for Codex-variant models)
- [x] Create `plugins/codex-tools/src/codex_tools/shell_command_tool.py`
- [x] Tool name: `shell_command`
- [x] Schema matches `docs/codex-tools/shell_command/schema.without_request_permissions.json`
- [x] `command` parameter is a string
- [x] Support `login` parameter (affects shell args: `-lc` vs `-c`)
- [x] Implement `stream_tool()` for real-time output streaming

### shell Tool (array-based, for non-Codex-variant models)
- [x] Create `plugins/codex-tools/src/codex_tools/shell_array_tool.py`
- [x] Tool name: `shell`
- [x] Schema matches `docs/codex-tools/shell/schema.without_request_permissions.json`
- [x] `command` parameter is an array of strings
- [x] Implement `stream_tool()` for real-time output streaming

### Common Features (both tools)
- [x] Output formatting matches Codex CLI freeform style
- [x] Token-based truncation using approximation (`len // 4`), NOT tiktoken
- [x] Default `max_output_tokens = 10_000` (from models.json)
- [x] Truncation split: 50/50 (head_ratio=0.5) — matches Codex implementation
- [x] Duration tracking in output ("Wall time: X seconds")
- [x] Non-zero exit code returned as tool error
- [x] Support `workdir` and `timeout_ms` parameters

### Task Completion
- [x] Mark `tasks/20260225-codex-tools-parity/020-bash-tool-round-1-schema.md` as completed
- [x] Mark `tasks/20260225-codex-tools-parity/030-bash-tool-round-2-output-and-limits.md` as completed

## Goal

Create both Codex CLI shell tools using the shared shell engine. Codex CLI has two shell tools selected by `shell_type` in models.json:

| `shell_type` | Tool Name | Command Format | Models |
|--------------|-----------|----------------|--------|
| `"default"` | `shell` | **Array**: `["bash", "-lc", "echo hello"]` | gpt-5, gpt-5.1, gpt-5.2 (non-Codex variants) |
| `"shell_command"` | `shell_command` | **String**: `"echo hello"` | gpt-5.2-codex, gpt-5.3-codex, gpt-5.4 (Codex variants) |

Both tools belong in `plugins/codex-tools/` and share the same execution engine and output formatting.

## Codex Research Findings (CRITICAL)

### Source References in Codex Repo

1. **Tool schema definition:**
   - `/Users/ferenci84/Dev/Mine/codex/codex-rs/core/src/tools/spec.rs` — `create_shell_command_tool()` function (lines ~570-630)
   - This defines the `shell_command` tool schema including all parameters

2. **Model-to-tool mapping:**
   - `/Users/ferenci84/Dev/Mine/codex/codex-rs/core/models.json` — `shell_type` field per model
   - Models with `"shell_type": "shell_command"`: gpt-5.2-codex, gpt-5.3-codex, gpt-5.4, gpt-5.1-codex, gpt-5-codex, etc.
   - Non-Codex models (gpt-5, gpt-5.1, gpt-5.2) use `"shell_type": "default"`

3. **Truncation implementation:**
   - `/Users/ferenci84/Dev/Mine/codex/codex-rs/core/src/truncate.rs` — token approximation and truncation logic

### Two Shell Tool Variants in Codex

Codex has **two different shell tools** selected by `shell_type` in models.json:

| `shell_type` | Tool Name | Command Format | Models |
|--------------|-----------|----------------|--------|
| `"default"` | `shell` | **Array**: `["bash", "-lc", "echo hello"]` | gpt-5, gpt-5.1, gpt-5.2 (non-Codex) |
| `"shell_command"` | `shell_command` | **String**: `"echo hello"` | gpt-5.2-codex, gpt-5.3-codex, gpt-5.4 (Codex) |

**Tool selection logic (from spec.rs):**
```rust
fn shell_tool_name(config: &ToolsConfig) -> Option<&'static str> {
    match config.shell_type {
        ConfigShellToolType::Default => Some("shell"),
        ConfigShellToolType::ShellCommand => Some("shell_command"),
        // ...
    }
}
```

**`shell` schema (array-based):**
```json
{
  "name": "shell",
  "parameters": {
    "properties": {
      "command": {
        "type": "array",
        "items": { "type": "string" },
        "description": "The command to execute (passed to execvp)"
      }
    }
  }
}
```

**`shell_command` schema (string-based):**
```json
{
  "name": "shell_command",
  "parameters": {
    "properties": {
      "command": {
        "type": "string",
        "description": "The shell script to execute in the user's default shell"
      }
    }
  }
}
```

**Why the difference:**
- `shell` (array) — Explicit control, model specifies shell binary and flags. Closer to raw `execvp()` semantics.
- `shell_command` (string) — More ergonomic for LLMs, CLI handles shell detection. Model writes natural shell commands.

### Shared Helper Requirement

The shared `run_shell_command()` helper currently accepts `command: str`. To support both tool types:

```python
async def run_shell_command(
    command: str | list[str],  # NEW: accept array or string
    *,
    workdir: str | None = None,
    timeout_seconds: float | None = None,
    env: dict[str, str] | None = None,
    shell: ShellInfo | None = None,
) -> dict[str, Any]:
    """
    Execute a shell command.
    
    Args:
        command: Either a string (executed via shell -c) or a list of strings
                  (first element is executable, rest are args, passed to exec).
    """
```

**Implementation:**
- If `command` is a string: use current behavior (shell -c wrapper)
- If `command` is a list: pass directly to `asyncio.create_subprocess_exec(*command, ...)`

This allows vendor wrappers to use the same shared engine for both `shell` and `shell_command` tools.

From examining the actual Codex CLI implementation (`/Users/ferenci84/Dev/Mine/codex/codex-rs/core/src/truncate.rs`):

### Token Approximation (NOT tiktoken!)

Codex uses a simple heuristic, NOT real tokenization:
```rust
const APPROX_BYTES_PER_TOKEN: usize = 4;

pub(crate) fn approx_token_count(text: &str) -> usize {
    len(text) / 4  // Essentially this
}
```

### Truncation Split: 50/50 (NOT head-only!)

```rust
fn split_budget(budget: usize) -> (usize, usize) {
    let left = budget / 2;
    (left, budget - left)  // 50% head, 50% tail
}
```

### Truncation Marker Format

The marker is embedded IN the output text:
```
{head}…{N} tokens truncated…{tail}
```

NOT appended after the output.

### Default Limits (from models.json)

For GPT-5.2-codex, GPT-5.3-codex, GPT-5.4:
```json
"truncation_policy": {
    "mode": "tokens",
    "limit": 10000
}
```

### Shell Type

All Codex models use `"shell_type": "shell_command"` (not "default" or "bash").

## Tool Schemas

### shell_command (string-based)

From `docs/codex-tools/shell_command/schema.without_request_permissions.json`:

```json
{
  "type": "function",
  "name": "shell_command",
  "description": "Runs a shell command and returns its output.\n- Always set the `workdir` param when using the shell_command function. Do not use `cd` unless absolutely necessary.",
  "strict": false,
  "parameters": {
    "type": "object",
    "properties": {
      "command": {
        "type": "string",
        "description": "The shell script to execute in the user's default shell"
      },
      "workdir": {
        "type": "string",
        "description": "The working directory to execute the command in"
      },
      "timeout_ms": {
        "type": "number",
        "description": "The timeout for the command in milliseconds"
      },
      "login": {
        "type": "boolean",
        "description": "Whether to run the shell with login shell semantics. Defaults to true."
      }
    },
    "required": ["command"],
    "additionalProperties": false
  }
}
```

### shell (array-based)

From `docs/codex-tools/shell/schema.without_request_permissions.json`:

```json
{
  "type": "function",
  "name": "shell",
  "description": "Runs a shell command and returns its output.\n- The arguments to `shell` will be passed to execvp(). Most terminal commands should be prefixed with [\"bash\", \"-lc\"].\n- Always set the `workdir` param when using the shell function. Do not use `cd` unless absolutely necessary.",
  "strict": false,
  "parameters": {
    "type": "object",
    "properties": {
      "command": {
        "type": "array",
        "description": "The command to execute",
        "items": { "type": "string" }
      },
      "workdir": {
        "type": "string",
        "description": "The working directory to execute the command in"
      },
      "timeout_ms": {
        "type": "number",
        "description": "The timeout for the command in milliseconds"
      }
    },
    "required": ["command"],
    "additionalProperties": false
  }
}
```

**Note:** Both schemas have additional params (`sandbox_permissions`, `justification`, `prefix_rule`) that are **out of scope** for this implementation (host-side security features). The `max_output_tokens` parameter is NOT in the schema — it's configured via model `truncation_policy` in models.json.

## Output Formatting (Codex CLI Style)

From examining `formatted_truncate_text` in truncate.rs:

**Success (exit code 0, no truncation):**
```
Exit code: 0
Wall time: 1.5 seconds
Output:
<combined output>
```

**Success with truncation:**
```
Exit code: 0
Wall time: 1.5 seconds
Total output lines: 5000

<head>…3000 tokens truncated…<tail>
```

**Note:** The truncation marker `…N tokens truncated…` is embedded IN the output, between head and tail.

**Failure (non-zero exit code):**
- Returned as **tool error** with formatted output inline

## Tool Implementation Pattern

Both tools share a base class for common formatting and truncation logic.

### Shared Base Class

```python
# plugins/codex-tools/src/codex_tools/base_shell_tool.py

from typing import Any, Dict, Iterator
from agent_core.types import ToolPlugin
from tool_compat_shared.shell_engine import run_shell_command, truncate_output

DEFAULT_MAX_OUTPUT_TOKENS = 10_000  # From Codex models.json


class BaseCodexShellTool(ToolPlugin):
    """Base class for Codex shell tools with shared formatting logic."""
    
    version: str = "1.0.0"
    
    def _build_result(
        self, 
        result: Dict[str, Any], 
        output: str, 
        trunc_meta: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build result dict with Codex formatting."""
        lines = []
        
        # Exit code
        exit_code = result.get("exit_code")
        lines.append(f"Exit code: {exit_code if exit_code is not None else 'none'}")
        
        # Duration
        lines.append(f"Wall time: {result['duration_seconds']:.1f} seconds")
        
        # Truncation header
        if trunc_meta.get("truncated"):
            lines.append(f"Total output lines: {trunc_meta['total_lines']}")
            lines.append("")  # Blank line before output
        
        # Output (already contains truncation marker if truncated)
        lines.append(output)
        
        output_text = "\n".join(lines)
        
        # Non-zero exit = tool error
        success = exit_code == 0 and not result.get("timed_out")
        
        return {
            "success": success,
            "output": output_text,
            "exit_code": exit_code,
            "timed_out": result.get("timed_out", False),
            "truncated": trunc_meta.get("truncated", False),
        }
    
    def _apply_truncation(self, output: str) -> tuple[str, Dict[str, Any]]:
        """Apply Codex-style truncation (50/50 split, token approximation)."""
        return truncate_output(
            output,
            limit_type="tokens",
            limit_value=DEFAULT_MAX_OUTPUT_TOKENS,
            head_ratio=0.5,  # Codex uses 50/50 split
        )
    
    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Format result for LLM consumption."""
        return result["output"]
```

### shell_command Tool (string-based)

```python
# plugins/codex-tools/src/codex_tools/shell_command_tool.py

from typing import Any, Dict, Iterator, List
from tool_compat_shared.shell_engine import ShellInfo, detect_shell, run_shell_command
from .base_shell_tool import BaseCodexShellTool


class ShellCommandTool(BaseCodexShellTool):
    """Codex shell_command tool - string-based command for Codex-variant models."""
    
    name: str = "shell_command"
    
    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{
            "type": "function",
            "name": "shell_command",
            "description": (
                "Runs a shell command and returns its output.\n"
                "- Always set the `workdir` param when using the shell_command function. "
                "Do not use `cd` unless absolutely necessary."
            ),
            "strict": False,
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The shell script to execute in the user's default shell",
                    },
                    "workdir": {
                        "type": "string",
                        "description": "The working directory to execute the command in",
                    },
                    "timeout_ms": {
                        "type": "number",
                        "description": "The timeout for the command in milliseconds",
                    },
                    "login": {
                        "type": "boolean",
                        "description": "Whether to run the shell with login shell semantics. Defaults to true.",
                    },
                },
                "required": ["command"],
                "additionalProperties": False,
            },
        }]
    
    def _get_shell(self, login: bool) -> ShellInfo:
        """Get shell config, adjusting for login flag."""
        shell = detect_shell()
        if login and shell.name == "bash":
            # Use -lc for login shell
            return ShellInfo(name=shell.name, path=shell.path, args=("-lc",))
        return shell
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if tool_name != "shell_command":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        command = arguments.get("command", "")
        workdir = arguments.get("workdir")
        timeout_ms = arguments.get("timeout_ms")
        login = arguments.get("login", True)  # Default true
        
        # Convert timeout from ms to seconds
        timeout_seconds = timeout_ms / 1000 if timeout_ms else None
        
        # Get shell with login flag
        shell = self._get_shell(login)
        
        # Call shared engine
        result = await run_shell_command(
            command,
            workdir=workdir,
            timeout_seconds=timeout_seconds,
            shell=shell,
        )
        
        # Apply truncation
        output, trunc_meta = self._apply_truncation(result["output"])
        
        return self._build_result(result, output, trunc_meta)
    
    def stream_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        """Stream shell command output in real-time."""
        # Implementation for streaming - see below
        ...
```

### shell Tool (array-based)

```python
# plugins/codex-tools/src/codex_tools/shell_array_tool.py

from typing import Any, Dict, Iterator, List
from tool_compat_shared.shell_engine import run_shell_command
from .base_shell_tool import BaseCodexShellTool


class ShellArrayTool(BaseCodexShellTool):
    """Codex shell tool - array-based command for non-Codex-variant models."""
    
    name: str = "shell"
    
    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{
            "type": "function",
            "name": "shell",
            "description": (
                "Runs a shell command and returns its output.\n"
                "- The arguments to `shell` will be passed to execvp(). "
                "Most terminal commands should be prefixed with [\"bash\", \"-lc\"].\n"
                "- Always set the `workdir` param when using the shell function. "
                "Do not use `cd` unless absolutely necessary."
            ),
            "strict": False,
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "array",
                        "description": "The command to execute",
                        "items": {"type": "string"},
                    },
                    "workdir": {
                        "type": "string",
                        "description": "The working directory to execute the command in",
                    },
                    "timeout_ms": {
                        "type": "number",
                        "description": "The timeout for the command in milliseconds",
                    },
                },
                "required": ["command"],
                "additionalProperties": False,
            },
        }]
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if tool_name != "shell":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        command = arguments.get("command", [])
        workdir = arguments.get("workdir")
        timeout_ms = arguments.get("timeout_ms")
        
        # Validate command is a list
        if not isinstance(command, list):
            return {"success": False, "error": "command must be an array of strings"}
        
        # Convert timeout from ms to seconds
        timeout_seconds = timeout_ms / 1000 if timeout_ms else None
        
        # Call shared engine with array command
        result = await run_shell_command(
            command,  # list[str] - passed directly to exec
            workdir=workdir,
            timeout_seconds=timeout_seconds,
        )
        
        # Apply truncation
        output, trunc_meta = self._apply_truncation(result["output"])
        
        return self._build_result(result, output, trunc_meta)
    
    def stream_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        """Stream shell command output in real-time."""
        # Implementation for streaming - see below
        ...
```

### Streaming Implementation

Both tools share the same streaming pattern:

```python
async def _stream_execute(
    self,
    command: str | list[str],
    workdir: str | None,
    timeout_seconds: float | None,
    shell: ShellInfo | None = None,
) -> Iterator[Dict[str, Any]]:
    """Stream output in real-time, yield partials then final result."""
    # Use asyncio subprocess with real-time line reading
    # Yield {"part": {"type": "text", "content": line}} for each line
    # Yield final result dict at the end
```
```

## Key Design Decisions

1. **Token approximation (`len // 4`)** - Matches Codex CLI, no tiktoken needed
2. **50/50 truncation split** - `head_ratio=0.5`, matches Codex `split_budget`
3. **Truncation marker in output** - `…N tokens truncated…` between head and tail
4. **Default 10K tokens** - From models.json truncation_policy
5. **No background support** - Codex schema doesn't have `is_background`
6. **Timeout in milliseconds** - Convert to seconds for shared engine
7. **Non-zero exit = tool error** - Matches Codex CLI behavior

## Tests

### Shared Engine Tests (update to `test_shell_engine.py`)

1. Array command execution: `["echo", "hello"]` → output contains "hello"
2. Array command with shell wrapper: `["bash", "-lc", "echo hello"]` → output contains "hello"
3. Array command exit code: `["sh", "-c", "exit 1"]` → exit_code=1

### shell_command Tool Tests (`test_shell_command_tool.py`)

1. Basic execution: `"echo hello"` → output contains "hello"
2. Exit code 0: success=True
3. Exit code non-zero: success=False, formatted as error
4. Timeout: `timed_out=True`, message indicates timeout
5. Truncation: long output truncated at 10K tokens with 50/50 split
6. Truncation marker format: verify Codex-style formatting
7. Working directory: command runs in specified directory
8. Login shell: `login=True` uses `-lc`, `login=False` uses `-c`
9. Streaming: real-time output chunks + final result

### shell Tool Tests (`test_shell_array_tool.py`)

1. Basic execution: `["echo", "hello"]` → output contains "hello"
2. Shell wrapper: `["bash", "-lc", "echo hello"]` → output contains "hello"
3. Exit code 0: success=True
4. Exit code non-zero: success=False, formatted as error
5. Timeout: `timed_out=True`, message indicates timeout
6. Truncation: long output truncated at 10K tokens with 50/50 split
7. Working directory: command runs in specified directory
8. Streaming: real-time output chunks + final result
9. Invalid command type: string instead of array → error

## Deliverables

### Shared Engine
1. Updated `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`
   - `run_shell_command()` accepts `str | list[str]`
   - Array commands passed directly to `asyncio.create_subprocess_exec(*command)`
2. Updated `plugins/tool-compat-shared/tests/test_shell_engine.py`
   - Tests for array command execution

### Codex Tools
3. `plugins/codex-tools/src/codex_tools/base_shell_tool.py`
   - `BaseCodexShellTool` with shared formatting/truncation logic
4. `plugins/codex-tools/src/codex_tools/shell_command_tool.py`
   - `ShellCommandTool` (string-based)
5. `plugins/codex-tools/src/codex_tools/shell_array_tool.py`
   - `ShellArrayTool` (array-based)
6. Updated `plugins/codex-tools/src/codex_tools/__init__.py`
   - Export `ShellCommandTool`, `ShellArrayTool`
7. `plugins/codex-tools/tests/test_shell_command_tool.py`
8. `plugins/codex-tools/tests/test_shell_array_tool.py`

## Notes for completing agent

- Token approximation is always cheap (`len(text) // 4`)
- Truncation marker is Unicode ellipsis (`…`), not ASCII
- Output format matches `formatted_truncate_text` from Codex truncate.rs
- Both tools share the same formatting logic via `BaseCodexShellTool`
- The existing `shell_tool.py` in codex-tools uses a STRING command (old implementation) - this task creates NEW tools that match Codex CLI schemas
- `shell_command` has a `login` parameter (defaults to true) affecting shell args
- `shell` tool uses array commands passed directly to exec (no shell wrapper)
- Streaming should use asyncio subprocess with real-time line reading

## Completion notes

**Implementation completed successfully.**

### Files created/modified:

1. **Shared Engine:**
   - Updated `plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`
     - `run_shell_command()` now accepts `str | list[str]`
     - Array commands passed directly to `asyncio.create_subprocess_exec(*command)`
     - Returns `direct_exec: True` for array commands
   - Updated `plugins/tool-compat-shared/tests/test_shell_engine.py`
     - Added `TestRunShellCommandArray` class with 10 tests for array command execution

2. **Codex Tools:**
   - Created `plugins/codex-tools/src/codex_tools/base_shell_tool.py`
     - `BaseCodexShellTool` with shared formatting and truncation logic
     - `_build_result()` for Codex-style output formatting
     - `_apply_truncation()` with 10K tokens, 50/50 split
     - `_insert_truncation_marker()` for `…N tokens truncated…` format
   - Created `plugins/codex-tools/src/codex_tools/shell_command_tool.py`
     - `ShellCommandTool` (string-based, tool name: `shell_command`)
     - Supports `login` parameter for `-lc` vs `-c` shell args
     - Implements `stream_tool()` for real-time streaming
   - Created `plugins/codex-tools/src/codex_tools/shell_array_tool.py`
     - `ShellArrayTool` (array-based, tool name: `shell`)
     - Direct exec via `asyncio.create_subprocess_exec(*command)`
     - Handles `FileNotFoundError` and `PermissionError` gracefully
   - Updated `plugins/codex-tools/src/codex_tools/__init__.py`
     - Exports `ShellCommandTool`, `ShellArrayTool`, `BaseCodexShellTool`
   - Created `plugins/codex-tools/tests/test_shell_command_tool.py` (26 tests)
   - Created `plugins/codex-tools/tests/test_shell_array_tool.py` (27 tests)

3. **Core Framework:**
   - Updated `core/python/agent_core/plugin/tool.py`
     - Added `execute_tool_async()` method to `ToolWrapper`
     - Properly handles async `execute_tool` implementations

### Test results:

- All 70 tests in `plugins/codex-tools/tests/` pass
- All 70 tests in `plugins/tool-compat-shared/tests/test_shell_engine.py` pass

### Key design decisions implemented:

- **Token approximation**: `len(text) // 4` (no tiktoken)
- **Truncation split**: 50/50 head/tail (Codex-style)
- **Default limit**: 10,000 tokens
- **Output format**: "Exit code: X\nWall time: Y seconds\n..." (Codex-style)
- **Non-zero exit**: `success=False` (tool error)
- **Login shell**: `login=True` → `-lc`, `login=False` → `-c`
- **Array exec**: Direct `asyncio.create_subprocess_exec(*command)` (no shell wrapper)
- **Error handling**: `FileNotFoundError` returns exit code 127, `PermissionError` returns 126