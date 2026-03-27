"""Qwen shell tool - bash with Qwen-style output formatting.

Tool name: bash
Schema matches Qwen CLI shell tool behavior.

Features:
- Command execution with optional description
- Working directory support (directory parameter)
- Background mode (is_background parameter)
- Line-first truncation (1k lines), then char truncation (25k chars)
- Platform-specific kill hints for background processes
- Timeout in milliseconds
"""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any, Dict, Iterator, List

from agent_core.types import ToolPlugin
from tool_compat_shared import (
    BACKGROUND_DELAY_SECONDS,
    ShellInfo,
    detect_shell,
    run_shell_command,
    truncate_output,
)


# Qwen defaults
DEFAULT_TIMEOUT_MS = 120_000  # 120 seconds in milliseconds
DEFAULT_MAX_TIMEOUT_MS = 600_000  # 600 seconds max
DEFAULT_MAX_OUTPUT_LINES = 1_000
DEFAULT_MAX_OUTPUT_CHARS = 25_000


class QwenShellTool(ToolPlugin):
    """Qwen shell tool - bash.
    
    Tool name: bash
    
    Command format: string (e.g., "echo hello")
    
    Parameters:
    - command: string (required) - The shell command to execute
    - timeout: number - Timeout in milliseconds (default: 120000, max: 600000)
    - description: string - Description of the command purpose
    - directory: string - Working directory for command execution
    - is_background: boolean - Run command in background mode
    
    Models using this tool:
    - Qwen models via qwen-tools plugin package
    """
    
    name = "qwen_shell_tool"
    version = "1.0.0"
    
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize tool state with vendor-specific defaults.
        
        Config keys (all optional, vendor defaults applied):
        - shell_timeout_seconds: Default timeout in seconds (default: 120)
        - shell_max_timeout_seconds: Maximum allowed timeout (default: 600)
        - shell_max_output_lines: Max output lines (default: 1000)
        - shell_max_output_chars: Max output characters (default: 25000)
        - project_temp_dir: Directory for temp files (default: <working_directory>/.temp)
        """
        import os
        working_directory = str(config.get("working_directory") or os.getcwd())
        workspace_dirs = config.get("allowed_paths") or [working_directory]
        project_temp_dir = str(config.get("project_temp_dir") or (Path(working_directory) / ".temp"))
        global_temp_dir = str(config.get("global_temp_dir") or tempfile.gettempdir())
        user_skills_dir = str(config.get("user_skills_dir") or tempfile.gettempdir())
        
        return {
            "working_directory": working_directory,
            "workspace_dirs": [str(Path(path).resolve()) for path in workspace_dirs if isinstance(path, str)],
            "project_temp_dir": str(Path(project_temp_dir).resolve()),
            "global_temp_dir": str(Path(global_temp_dir).resolve()),
            "user_skills_dir": str(Path(user_skills_dir).resolve()),
            # Shell-specific config with Qwen defaults
            "timeout_seconds": config.get("shell_timeout_seconds", DEFAULT_TIMEOUT_MS // 1000),
            "max_timeout_seconds": config.get("shell_max_timeout_seconds", DEFAULT_MAX_TIMEOUT_MS // 1000),
            "max_output_lines": config.get("shell_max_output_lines", DEFAULT_MAX_OUTPUT_LINES),
            "max_output_chars": config.get("shell_max_output_chars", DEFAULT_MAX_OUTPUT_CHARS),
        }
    
    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return tool schema matching Qwen CLI bash tool."""
        return [{
            "type": "function",
            "function": {
                "name": "bash",
                "description": (
                    "Execute a bash command and return its output.\n\n"
                    "Usage notes:\n"
                    "- Use this tool to execute shell commands.\n"
                    "- Always specify the `directory` parameter when the command needs to be "
                    "executed in a specific directory. Do not use `cd` in the command string.\n"
                    "- The `timeout` parameter is in milliseconds. Maximum allowed is 600000ms (10 minutes).\n"
                    "- If the command may run for a long time, set `is_background` to true."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The bash command to execute.",
                        },
                        "timeout": {
                            "type": "number",
                            "description": "Timeout in milliseconds. Default: 120000, Max: 600000",
                        },
                        "description": {
                            "type": "string",
                            "description": "Brief description of the command's purpose.",
                        },
                        "directory": {
                            "type": "string",
                            "description": "The directory in which to execute the command.",
                        },
                        "is_background": {
                            "type": "boolean",
                            "description": "If true, runs the command in the background.",
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
            Result dict with success, output, and metadata
        """
        if tool_name != "bash":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        command = arguments.get("command")
        if not isinstance(command, str) or not command.strip():
            return {"success": False, "error": "Command cannot be empty."}
        
        description = arguments.get("description")
        directory = arguments.get("directory")
        is_background = arguments.get("is_background", False)
        
        # Parse timeout (in milliseconds)
        timeout_ms = arguments.get("timeout")
        if timeout_ms is not None:
            try:
                timeout_ms = float(timeout_ms)
            except (TypeError, ValueError):
                timeout_ms = None
        
        # Apply timeout limits
        max_timeout_ms = state.get("max_timeout_seconds", DEFAULT_MAX_TIMEOUT_MS // 1000) * 1000
        if timeout_ms is None:
            timeout_seconds = state.get("timeout_seconds", DEFAULT_TIMEOUT_MS // 1000)
        else:
            timeout_ms = min(timeout_ms, max_timeout_ms)
            timeout_seconds = timeout_ms / 1000.0
        
        # Execute via shared engine
        result = await run_shell_command(
            command,
            workdir=directory,
            timeout_seconds=timeout_seconds,
            is_background=is_background,
        )
        
        # Format output based on result type
        if result.get("background"):
            return self._format_background_result(result, command, directory, description)
        
        if result.get("timed_out"):
            return self._format_timeout_result(result, timeout_seconds, command, directory)
        
        # Apply Qwen-style truncation (line-first, then char)
        output, trunc_meta = self._apply_qwen_truncation(
            result["output"],
            state.get("max_output_lines", DEFAULT_MAX_OUTPUT_LINES),
            state.get("max_output_chars", DEFAULT_MAX_OUTPUT_CHARS),
        )
        
        # Build result based on exit code and stderr
        if result["exit_code"] == 0 and not result["stderr"].strip():
            return self._format_success_result(result, output, trunc_meta, command, directory, description)
        else:
            return self._format_failure_result(result, output, trunc_meta, command, directory, description)
    
    def _apply_qwen_truncation(
        self,
        output: str,
        line_limit: int,
        char_limit: int,
    ) -> tuple[str, Dict[str, Any]]:
        """Apply Qwen-style line-first, then char truncation.
        
        Qwen truncates by lines first (1k lines), then by chars (25k chars).
        Both use head-only truncation (head_ratio=1.0).
        
        Args:
            output: Raw output string
            line_limit: Maximum lines to keep
            char_limit: Maximum characters to keep
            
        Returns:
            Tuple of (truncated_output, metadata_dict)
        """
        # First pass: check line count
        output, meta = truncate_output(
            output,
            limit_type="lines",
            limit_value=line_limit,
            head_ratio=1.0,  # Qwen uses head-only
        )
        
        if meta["truncated"]:
            return output, meta
        
        # Second pass: check char count (only if lines didn't trigger)
        output, meta = truncate_output(
            output,
            limit_type="chars",
            limit_value=char_limit,
            head_ratio=1.0,  # Qwen uses head-only
        )
        
        return output, meta
    
    def _format_success_result(
        self,
        result: Dict[str, Any],
        output: str,
        trunc_meta: Dict[str, Any],
        command: str,
        directory: str | None,
        description: str | None,
    ) -> Dict[str, Any]:
        """Format successful command result (exit 0, no stderr).
        
        Qwen success format: just the stdout output, no prefix.
        """
        lines: List[str] = []
        
        # Output (no prefix for success)
        if output.strip():
            lines.append(output)
        
        # Truncation message if needed
        if trunc_meta.get("truncated"):
            lines.append("")
            if trunc_meta.get("omitted_lines", 0) > 0:
                lines.append(f"[{trunc_meta['omitted_lines']} lines truncated]")
            else:
                lines.append(f"[{trunc_meta.get('omitted_chars', 0)} characters truncated]")
        
        return {
            "success": True,
            "output": "\n".join(lines) if lines else "",
            "exit_code": result["exit_code"],
            "duration_seconds": result["duration_seconds"],
            "truncated": trunc_meta.get("truncated", False),
            "command": command,
            "directory": directory,
            "description": description,
        }
    
    def _format_failure_result(
        self,
        result: Dict[str, Any],
        output: str,
        trunc_meta: Dict[str, Any],
        command: str,
        directory: str | None,
        description: str | None,
    ) -> Dict[str, Any]:
        """Format failed command result (non-zero exit or stderr).
        
        Qwen failure format:
        Stdout: <stdout or (empty)>
        Stderr: <stderr or (empty)>
        Error: <error or (none)>
        Exit Code: <code or (none)>
        Signal: <signal or (none)>
        """
        lines: List[str] = []
        
        # Stdout
        stdout = result.get("stdout", "")
        if stdout.strip():
            lines.append(f"Stdout: {stdout.strip()}")
        else:
            lines.append("Stdout: (empty)")
        
        # Stderr
        stderr = result.get("stderr", "")
        if stderr.strip():
            lines.append(f"Stderr: {stderr.strip()}")
        else:
            lines.append("Stderr: (empty)")
        
        # Error (if any)
        if result.get("error"):
            lines.append(f"Error: {result['error']}")
        else:
            lines.append("Error: (none)")
        
        # Exit code
        exit_code = result.get("exit_code")
        if exit_code is not None:
            lines.append(f"Exit Code: {exit_code}")
        else:
            lines.append("Exit Code: (none)")
        
        # Signal (if terminated by signal)
        # Note: We don't have signal info from the shared engine yet
        lines.append("Signal: (none)")
        
        # Truncation message if needed
        if trunc_meta.get("truncated"):
            lines.append("")
            if trunc_meta.get("omitted_lines", 0) > 0:
                lines.append(f"[{trunc_meta['omitted_lines']} lines truncated]")
            else:
                lines.append(f"[{trunc_meta.get('omitted_chars', 0)} characters truncated]")
        
        return {
            "success": False,
            "output": "\n".join(lines),
            "exit_code": result["exit_code"],
            "duration_seconds": result["duration_seconds"],
            "truncated": trunc_meta.get("truncated", False),
            "command": command,
            "directory": directory,
            "description": description,
        }
    
    def _format_timeout_result(
        self,
        result: Dict[str, Any],
        timeout_seconds: float,
        command: str,
        directory: str | None,
    ) -> Dict[str, Any]:
        """Format timeout result."""
        lines: List[str] = []
        
        lines.append("Stdout: (empty)")
        lines.append("Stderr: (empty)")
        lines.append(f"Error: Command timed out after {timeout_seconds:.1f} seconds")
        lines.append("Exit Code: (none)")
        lines.append("Signal: (none)")
        
        # Include partial output if any
        if result["output"].strip():
            lines.append("")
            lines.append("Partial output before timeout:")
            lines.append(result["output"])
        
        return {
            "success": False,
            "output": "\n".join(lines),
            "exit_code": None,
            "timed_out": True,
            "duration_seconds": result["duration_seconds"],
            "command": command,
            "directory": directory,
        }
    
    def _format_background_result(
        self,
        result: Dict[str, Any],
        command: str,
        directory: str | None,
        description: str | None,
    ) -> Dict[str, Any]:
        """Format background process result with platform-specific kill hint."""
        pid = result.get("pid")
        is_windows = sys.platform == "win32"
        
        lines: List[str] = []
        
        if is_windows:
            lines.append(f"Background command started. PID: {pid} (Use taskkill /F /T /PID {pid} to stop)")
        else:
            lines.append(f"Background command started. PID: {pid} (Use kill {pid} to stop)")
        
        return {
            "success": True,
            "output": "\n".join(lines),
            "background": True,
            "pid": pid,
            "command": command,
            "directory": directory,
            "description": description,
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
        directory = result.get("directory")
        
        lines: List[str] = []
        
        if directory:
            lines.append(f"Directory: {directory}")
        
        if command:
            cmd_preview = command.splitlines()[0] if "\n" in command else command
            lines.append(f"Command: {cmd_preview}")
        
        if lines:
            lines.append("Output:")
            header = "\n".join(lines)
            content = f"{header}\n{text}" if text else header
        else:
            content = text
        
        return {"type": "text", "content": content}


__all__ = ["QwenShellTool"]