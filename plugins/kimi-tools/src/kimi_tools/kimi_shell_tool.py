"""Kimi shell tool - Shell with clean environment support.

Tool name: Shell
Schema matches Kimi CLI shell tool behavior.

Features:
- Clean environment (strips PyInstaller/frozen-executable variables)
- Timeout in seconds (default: 60, max: 300)
- Kimi-style output truncation
- Success/failure message formatting
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import Any, Dict, List

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    accumulate_truncated_lines,
    run_shell_command,
)


# Kimi defaults
DEFAULT_TIMEOUT_SECONDS = 60
DEFAULT_MAX_TIMEOUT_SECONDS = 300
DEFAULT_MAX_OUTPUT_CHARS = 50_000
DEFAULT_MAX_OUTPUT_LINE_LENGTH = 2_000
TRUNCATION_MARKER = "[...truncated]"
TRUNCATION_NOTICE = "Output is truncated to fit in the message."


def get_clean_env() -> Dict[str, str]:
    """Return a clean environment for subprocess execution.
    
    Strips PyInstaller/frozen-executable modified environment variables
    that could interfere with subprocess execution:
    - _MEIPASS, _MEIPASS2 (PyInstaller temp paths)
    - PYINSTALLER_* variables
    - LD_LIBRARY_PATH modifications from frozen apps
    
    Returns:
        Cleaned environment dict
    """
    env = dict(os.environ)
    
    # Remove PyInstaller variables if running as frozen executable
    if getattr(sys, 'frozen', False):
        keys_to_remove = [k for k in env if k.startswith('_MEI') or k.startswith('PYINSTALLER')]
        for k in keys_to_remove:
            env.pop(k, None)
        # Also clean LD_LIBRARY_PATH that might point to frozen app libs
        env.pop('LD_LIBRARY_PATH', None)
    
    return env


class KimiShellTool(ToolPlugin):
    """Kimi shell tool - Shell.
    
    Tool name: Shell
    
    Command format: string (e.g., "echo hello")
    
    Parameters:
    - command: string (required) - The shell command to execute
    - timeout: integer - Timeout in seconds (default: 60, max: 300)
    
    Models using this tool:
    - Kimi models via kimi-tools plugin package
    """
    
    name = "kimi_shell_tool"
    version = "1.0.0"
    
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize tool state with vendor-specific defaults.
        
        Config keys (all optional, vendor defaults applied):
        - shell_timeout_seconds: Default timeout in seconds (default: 60)
        - shell_max_timeout_seconds: Maximum allowed timeout (default: 300)
        - shell_clean_env: Use clean environment for subprocess (default: true)
        - project_temp_dir: Directory for temp files (default: <working_directory>/.temp)
        """
        import os
        working_directory = str(config.get("working_directory") or os.getcwd())
        workspace_dirs = config.get("allowed_paths") or [working_directory]
        project_temp_dir = str(config.get("project_temp_dir") or (Path(working_directory) / ".temp"))
        
        return {
            "working_directory": working_directory,
            "workspace_dirs": [str(Path(path).resolve()) for path in workspace_dirs if isinstance(path, str)],
            "project_temp_dir": str(Path(project_temp_dir).resolve()),
            # Shell-specific config with Kimi defaults
            "timeout_seconds": config.get("shell_timeout_seconds", DEFAULT_TIMEOUT_SECONDS),
            "max_timeout_seconds": config.get("shell_max_timeout_seconds", DEFAULT_MAX_TIMEOUT_SECONDS),
            "clean_env": config.get("shell_clean_env", True),
        }
    
    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return tool schema matching Kimi CLI Shell tool."""
        return [{
            "type": "function",
            "function": {
                "name": "Shell",
                "description": (
                    "Execute a shell command and return its output.\n\n"
                    "Usage notes:\n"
                    "- Use this tool to execute shell commands.\n"
                    "- The `timeout` parameter is in seconds. Default: 60, Max: 300.\n"
                    "- Commands run with a clean environment (PyInstaller variables removed).\n"
                    "- Output is truncated to fit in the message when needed."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The shell command to execute.",
                        },
                        "timeout": {
                            "type": "integer",
                            "description": "Timeout in seconds. Default: 60, Max: 300",
                            "default": DEFAULT_TIMEOUT_SECONDS,
                        },
                    },
                    "required": ["command"],
                },
            },
        }]
    
    def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        *,
        cancellation: Any | None = None,
    ) -> Dict[str, Any]:
        """Execute the Shell tool.
        
        Args:
            tool_name: Should be "Shell"
            arguments: Tool call arguments
            state: Tool state from init()
            
        Returns:
            Result dict with success, output, and metadata
        """
        if tool_name != "Shell":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        command = arguments.get("command")
        if not isinstance(command, str) or not command.strip():
            return {"success": False, "error": "Command cannot be empty."}
        
        # Parse timeout (in seconds)
        timeout = arguments.get("timeout")
        if timeout is not None:
            try:
                timeout = int(timeout)
            except (TypeError, ValueError):
                timeout = None
        
        # Apply timeout limits
        max_timeout = state.get("max_timeout_seconds", DEFAULT_MAX_TIMEOUT_SECONDS)
        if timeout is None:
            timeout = state.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
        else:
            timeout = min(timeout, max_timeout)
        
        # Get working directory from state
        workdir = state.get("working_directory")
        
        # Get environment (clean or inherit)
        env = get_clean_env() if state.get("clean_env", True) else None
        
        # Execute via shared engine (sync wrapper around async)
        import asyncio
        
        async def _run():
            return await run_shell_command(
                command,
                workdir=workdir,
                timeout_seconds=timeout,
                env=env,
                cancellation=cancellation,
            )
        
        # Check if we're already in an async context
        try:
            asyncio.get_running_loop()
            # We're in an async context - need to run in a thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _run())
                result = future.result()
        except RuntimeError:
            # No running loop - we can use asyncio.run()
            result = asyncio.run(_run())
        
        output, trunc_meta = accumulate_truncated_lines(
            result["output"].splitlines(keepends=True),
            max_chars=DEFAULT_MAX_OUTPUT_CHARS,
            max_line_length=DEFAULT_MAX_OUTPUT_LINE_LENGTH,
            marker=TRUNCATION_MARKER,
        )
        result = {
            **result,
            "output": output,
            "truncated": trunc_meta.get("truncated", False),
        }

        # Format output based on result type
        if result.get("timed_out"):
            return self._format_timeout_result(result, timeout, command)

        if result.get("cancelled"):
            output = str(result.get("output") or "").rstrip()
            lines = [output] if output else []
            lines.append("Command cancelled.")
            return {
                "success": False,
                "output": "\n".join(lines),
                "exit_code": None,
                "cancelled": True,
                "duration_seconds": result["duration_seconds"],
                "command": command,
                "truncated": bool(result.get("truncated")),
            }
        
        # Build result based on exit code
        if result["exit_code"] == 0:
            return self._format_success_result(result, command)
        else:
            return self._format_failure_result(result, command)
    
    def _format_success_result(
        self,
        result: Dict[str, Any],
        command: str,
    ) -> Dict[str, Any]:
        """Format successful command result.
        
        Kimi success format:
        <combined output>
        Command executed successfully.
        """
        lines: List[str] = []
        
        # Output
        if result["output"].strip():
            lines.append(result["output"])
        
        # Success message
        message = "Command executed successfully."
        if result.get("truncated"):
            message += f" {TRUNCATION_NOTICE}"
        lines.append(message)
        
        return {
            "success": True,
            "output": "\n".join(lines),
            "exit_code": result["exit_code"],
            "duration_seconds": result["duration_seconds"],
            "command": command,
            "truncated": bool(result.get("truncated")),
        }
    
    def _format_failure_result(
        self,
        result: Dict[str, Any],
        command: str,
    ) -> Dict[str, Any]:
        """Format failed command result.
        
        Kimi failure format:
        <combined output>
        Command failed with exit code: N.
        """
        lines: List[str] = []
        
        # Output
        if result["output"].strip():
            lines.append(result["output"])
        
        # Failure message
        message = f"Command failed with exit code: {result['exit_code']}."
        if result.get("truncated"):
            message += f" {TRUNCATION_NOTICE}"
        lines.append(message)
        
        return {
            "success": False,
            "output": "\n".join(lines),
            "exit_code": result["exit_code"],
            "duration_seconds": result["duration_seconds"],
            "command": command,
            "truncated": bool(result.get("truncated")),
        }
    
    def _format_timeout_result(
        self,
        result: Dict[str, Any],
        timeout: int,
        command: str,
    ) -> Dict[str, Any]:
        """Format timeout result.
        
        Kimi timeout format:
        <partial output>
        Command killed by timeout (Ns)
        """
        lines: List[str] = []
        
        # Partial output
        if result["output"].strip():
            lines.append(result["output"])
        
        # Timeout message
        message = f"Command killed by timeout ({timeout}s)"
        if result.get("truncated"):
            message += f" {TRUNCATION_NOTICE}"
        lines.append(message)
        
        return {
            "success": False,
            "output": "\n".join(lines),
            "exit_code": None,
            "timed_out": True,
            "duration_seconds": result["duration_seconds"],
            "command": command,
            "truncated": bool(result.get("truncated")),
        }
    
    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        """Format result for LLM consumption."""
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


__all__ = ["KimiShellTool", "get_clean_env"]