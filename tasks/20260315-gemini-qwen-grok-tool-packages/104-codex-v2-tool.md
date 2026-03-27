# 104 - Codex V2 Shell Tool

Short description: Create the Codex V2 `shell_command` tool using the shared shell engine.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/100-shell-tools.md`

Depends On: 
- `tasks/20260315-gemini-qwen-grok-tool-packages/101-shell-engine-core.md`
- `tasks/20260315-gemini-qwen-grok-tool-packages/102-shell-engine-truncation.md`

## Related tasks (completion)

Upon completion, mark the following tasks as completed:

- `tasks/20260225-codex-tools-parity/020-bash-tool-round-1-schema.md` — COMPLETED VIA this task
- `tasks/20260225-codex-tools-parity/030-bash-tool-round-2-output-and-limits.md` — COMPLETED VIA this task

## Requirements checklist

- [ ] Create `plugins/codex-tools/src/codex_tools/shell_command_tool.py`
- [ ] Tool name: `shell_command`
- [ ] Schema matches `docs/codex-tools/shell_command/schema.without_request_permissions.json`
- [ ] Output formatting matches Codex CLI freeform style
- [ ] Token-based truncation using approximation (`len // 4`), NOT tiktoken
- [ ] Default `max_output_tokens = 10_000` (from models.json)
- [ ] Truncation split: 50/50 (head_ratio=0.5) — matches Codex implementation
- [ ] Duration tracking in output
- [ ] Non-zero exit code returned as tool error
- [ ] Mark `tasks/20260225-codex-tools-parity/020-bash-tool-round-1-schema.md` as completed
- [ ] Mark `tasks/20260225-codex-tools-parity/030-bash-tool-round-2-output-and-limits.md` as completed
- [ ] **Shared helper update:** Add support for array-based commands to `run_shell_command()` for `shell` tool compatibility

## Goal

Create the first vendor tool using the shared shell engine. This serves as the proof-of-concept and establishes the pattern for other vendor tools.

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

## Tool Schema

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

**Note:** The schema has additional params (`sandbox_permissions`, `justification`, `prefix_rule`) that are **out of scope** for this implementation (host-side security features). The `max_output_tokens` parameter is NOT in the schema — it's configured via model `truncation_policy` in models.json.

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

```python
from typing import Any, Dict, List
from agent_core.types import ToolPlugin
from tool_compat_shared.shell_engine import run_shell_command, truncate_output

DEFAULT_MAX_OUTPUT_TOKENS = 10_000  # From Codex models.json

class ShellCommandTool(ToolPlugin):
    name: str = "shell_command"
    version: str = "1.0.0"
    
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
        if tool_name != "shell_command":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        command = arguments.get("command", "")
        workdir = arguments.get("workdir")
        timeout_ms = arguments.get("timeout_ms")
        
        # Convert timeout from ms to seconds
        timeout_seconds = timeout_ms / 1000 if timeout_ms else None
        
        # Call shared engine (no truncation params - apply separately)
        result = await run_shell_command(
            command,
            workdir=workdir,
            timeout_seconds=timeout_seconds,
        )
        
        # Apply Codex-style truncation (50/50 split, token approximation)
        output, trunc_meta = truncate_output(
            result["output"],
            limit_type="tokens",
            limit_value=DEFAULT_MAX_OUTPUT_TOKENS,
            head_ratio=0.5,  # Codex uses 50/50 split
        )
        
        return self._build_result(result, output, trunc_meta)
    
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
    
    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Format result for LLM consumption."""
        return result["output"]
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

Port relevant tests from `plugins/codex-tools/tests/test_shell_tool.py`:

1. Basic execution: `echo hello` → output contains "hello"
2. Exit code 0: success=True
3. Exit code non-zero: success=False, output returned as error
4. Timeout: `timed_out=True`, message indicates timeout
5. Truncation: long output truncated at 10K tokens with 50/50 split
6. Truncation marker: verify `…N tokens truncated…` in output
7. Working directory: command runs in specified directory

## Deliverables

1. `plugins/codex-tools/src/codex_tools/shell_command_tool.py`
2. `plugins/codex-tools/tests/test_shell_command_tool.py`
3. Updated `plugins/codex-tools/src/codex_tools/__init__.py` - export `ShellCommandTool`

## Notes for completing agent

- Token approximation is always cheap (`len(text) // 4`)
- Truncation marker is Unicode ellipsis (`…`), not ASCII
- Output format matches `formatted_truncate_text` from Codex truncate.rs
- This tool establishes the pattern for vendor wrappers

## Completion notes

(To be filled during implementation)