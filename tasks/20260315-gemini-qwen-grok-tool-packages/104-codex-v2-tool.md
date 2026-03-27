# 140 - Codex V2 Shell Tool

Short description: Create the Codex V2 `shell_command` tool using the shared shell engine.

Parent Task: `tasks/20260315-gemini-qwen-grok-tool-packages/000-main.md`

Depends On: 
- `tasks/20260315-gemini-qwen-grok-tool-packages/101-shell-engine-core.md`
- `tasks/20260315-gemini-qwen-grok-tool-packages/102-shell-engine-truncation.md`

## Requirements checklist

- [ ] Create `plugins/codex-tools/src/codex_tools/shell_command_tool.py`
- [ ] Tool name: `shell_command`
- [ ] Schema matches `docs/codex-tools/shell_command/schema.without_request_permissions.json`
- [ ] Output formatting matches Codex CLI freeform style
- [ ] Token-based truncation with `max_output_tokens` parameter
- [ ] Duration tracking in output
- [ ] Non-zero exit code returned as tool error

## Goal

Create the first vendor tool using the shared shell engine. This serves as the proof-of-concept and establishes the pattern for other vendor tools.

## Tool Schema

From `docs/codex-tools/shell_command/schema.without_request_permissions.json`:

```python
{
    "type": "function",
    "function": {
        "name": "shell_command",
        "description": (
            "Runs a shell command and returns its output.\n"
            "- Always set the `workdir` param when using the shell_command function. "
            "Do not use `cd` unless absolutely necessary."
        ),
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
                "max_output_tokens": {
                    "type": "number",
                    "description": "Maximum output tokens before truncation"
                },
            },
            "required": ["command"],
        },
    },
}
```

**Note:** The schema has additional params (`login`, `sandbox_permissions`, `justification`, `prefix_rule`) that are **out of scope** for this implementation (host-side security features).

## Output Formatting (Freeform Text)

From `docs/codex-tools/shared/README.md`:

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
Output:
<truncated output>
... truncated, 3000 more tokens
```

**Failure (non-zero exit code):**
- Returned as **tool error** with formatted output inline

## Tool Implementation Pattern

```python
from typing import Any, Dict
from agent_core.types import ToolPlugin
from tool_compat_shared.shell_engine import run_shell_command

class ShellCommandTool(ToolPlugin):
    name: str = "shell_command"
    version: str = "1.0.0"
    
    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{
            "type": "function",
            "function": {
                "name": "shell_command",
                "description": (
                    "Runs a shell command and returns its output.\n"
                    "- Always set the `workdir` param when using the shell_command function. "
                    "Do not use `cd` unless absolutely necessary."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {"type": "string", "description": "..."},
                        "workdir": {"type": "string", "description": "..."},
                        "timeout_ms": {"type": "number", "description": "..."},
                        "max_output_tokens": {"type": "number", "description": "..."},
                    },
                    "required": ["command"],
                },
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
        max_output_tokens = arguments.get("max_output_tokens")
        
        # Convert timeout from ms to seconds
        timeout_seconds = timeout_ms / 1000 if timeout_ms else None
        
        # Call shared engine with token-based truncation
        result = await run_shell_command(
            command,
            workdir=workdir,
            timeout_seconds=timeout_seconds,
            limit_type="tokens" if max_output_tokens else None,
            limit_value=max_output_tokens,
            head_ratio=1.0,  # All from beginning
        )
        
        return self._build_result(result)
    
    def _build_result(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Build result dict with Codex formatting."""
        lines = []
        
        # Exit code
        exit_code = result.get("exit_code")
        lines.append(f"Exit code: {exit_code if exit_code is not None else 'none'}")
        
        # Duration
        lines.append(f"Wall time: {result['duration_seconds']:.1f} seconds")
        
        # Truncation info
        if result.get("truncated"):
            lines.append(f"Total output lines: {result['total_lines']}")
        
        # Output
        lines.append("Output:")
        lines.append(result["output"])
        
        # Truncation marker
        if result.get("truncated"):
            lines.append(f"... truncated, {result['omitted_tokens']} more tokens")
        
        output = "\n".join(lines)
        
        # Non-zero exit = tool error
        success = exit_code == 0
        
        return {
            "success": success,
            "output": output,
            "exit_code": exit_code,
            "timed_out": result.get("timed_out", False),
        }
    
    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Format result for LLM consumption."""
        if not result.get("success"):
            # Return as error with output inline
            return result["output"]
        return result["output"]
```

## Key Design Decisions

1. **Token-based truncation only** - Codex V2 uses tokens, not chars or lines
2. **No background support** - Codex schema doesn't have `is_background`
3. **Timeout in milliseconds** - Convert to seconds for shared engine
4. **Non-zero exit = tool error** - Matches Codex CLI behavior

## Tests

Port relevant tests from `plugins/codex-tools/tests/test_shell_tool.py`:

1. Basic execution: `echo hello` → output contains "hello"
2. Exit code 0: success=True
3. Exit code non-zero: success=False, output returned as error
4. Timeout: `timed_out=True`, message indicates timeout
5. Truncation: long output truncated at `max_output_tokens`
6. Working directory: command runs in specified directory

## Deliverables

1. `plugins/codex-tools/src/codex_tools/shell_command_tool.py`
2. `plugins/codex-tools/tests/test_shell_command_tool.py`
3. Updated `plugins/codex-tools/src/codex_tools/__init__.py` - export `ShellCommandTool`

## Notes for completing agent

- Finalize whether to use `async def execute_tool` or sync wrapper
- Verify output formatting matches Codex CLI exactly
- Check if `to_display_format` method is needed
- This tool establishes the pattern for vendor wrappers

## Completion notes

(To be filled during implementation)