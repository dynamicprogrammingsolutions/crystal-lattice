"""Grok shell tool - bash with minimal schema and raw output.

Tool name: bash
Schema matches Grok CLI shell tool behavior.

Features:
- Minimal schema: just command parameter (no timeout, no workdir, no background)
- No truncation
- Raw output format (no special formatting)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Iterator, List

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    ShellInfo,
    detect_shell,
    run_shell_command,
)


class GrokShellTool(ToolPlugin):
    """Grok shell tool - bash.
    
    Tool name: bash
    
    Command format: string (e.g., "echo hello")
    
    Parameters:
    - command: string (required) - The bash command to execute
    
    Note: Grok has minimal schema - no timeout, no working directory,
    no background mode, no truncation.
    
    Models using this tool:
    - Grok models via grok-tools plugin package
    """
    
    name = "grok_shell_tool"
    version = "1.0.0"
    
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize tool state.
        
        Grok shell tool has no configurable options.
        """
        import os
        working_directory = str(config.get("working_directory") or os.getcwd())
        workspace_dirs = config.get("allowed_paths") or [working_directory]
        project_temp_dir = str(config.get("project_temp_dir") or (Path(working_directory) / ".temp"))
        
        return {
            "working_directory": working_directory,
            "workspace_dirs": [str(Path(path).resolve()) for path in workspace_dirs if isinstance(path, str)],
            "project_temp_dir": str(Path(project_temp_dir).resolve()),
        }
    
    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return tool schema matching Grok CLI bash tool (minimal)."""
        return [{
            "type": "function",
            "function": {
                "name": "bash",
                "description": "Execute a bash command and return its output.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute.",
                        },
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
        """Execute the bash tool.
        
        Args:
            tool_name: Should be "bash"
            arguments: Tool call arguments
            state: Tool state from init()
            
        Returns:
            Result dict with success and output
        """
        if tool_name != "bash":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        command = arguments.get("command")
        if not isinstance(command, str) or not command.strip():
            return {"success": False, "error": "Command cannot be empty."}
        
        # Execute via shared engine (no timeout, no background)
        result = await run_shell_command(command)
        
        # Grok returns raw output - no special formatting
        success = result["exit_code"] == 0
        
        return {
            "success": success,
            "output": result["output"],
            "exit_code": result["exit_code"],
            "duration_seconds": result["duration_seconds"],
            "command": command,
        }
    
    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Format result for LLM consumption - raw output."""
        return result.get("output", "")
    
    def format_tool_call_preview(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> str:
        """Generate a preview for tool call display."""
        command = arguments.get("command", "")
        if isinstance(command, str):
            cmd = command.strip()
            return cmd.splitlines()[0] if "\n" in cmd else cmd
        return ""
    
    def to_display_format(
        self,
        text: str,
        result: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Format result for display."""
        command = result.get("command")
        
        if command:
            cmd_preview = command.splitlines()[0] if "\n" in command else command
            content = f"Command: {cmd_preview}\nOutput:\n{text}"
        else:
            content = text
        
        return {"type": "text", "content": content}


__all__ = ["GrokShellTool"]