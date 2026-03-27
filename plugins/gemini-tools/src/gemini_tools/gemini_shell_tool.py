"""Gemini shell tool - run_shell_command with Gemini-style output formatting.

Tool name: run_shell_command
Schema matches Gemini CLI shell tool behavior.

Features:
- Command execution with optional description
- Working directory support (dir_path parameter)
- Background mode (is_background parameter)
- 40k character truncation with 20/80 head/tail split
- Temp file saving for truncated output reference
"""

from __future__ import annotations

import sys
import uuid
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


# Gemini defaults
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_MAX_OUTPUT_CHARS = 40_000
DEFAULT_TRUNCATION_HEAD_RATIO = 0.2  # 20% head, 80% tail


class GeminiShellTool(ToolPlugin):
    """Gemini shell tool - run_shell_command.
    
    Tool name: run_shell_command
    
    Command format: string (e.g., "echo hello")
    
    Parameters:
    - command: string (required) - The shell command to execute
    - description: string - Description of the command purpose
    - dir_path: string - Working directory for command execution
    - is_background: boolean - Run command in background mode
    
    Models using this tool:
    - Gemini models via gemini-tools plugin package
    """
    
    name = "gemini_shell_tool"
    version = "1.0.0"
    
    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Initialize tool state with vendor-specific defaults.
        
        Config keys (all optional, vendor defaults applied):
        - shell_timeout_seconds: Default timeout (default: 120)
        - shell_max_output_chars: Max output characters (default: 40000)
        - shell_truncation_head_ratio: Head/tail split ratio (default: 0.2)
        - project_temp_dir: Directory for temp files (default: <working_directory>/.temp)
        """
        import os
        working_directory = str(config.get("working_directory") or os.getcwd())
        workspace_dirs = config.get("allowed_paths") or [working_directory]
        project_temp_dir = str(config.get("project_temp_dir") or (Path(working_directory) / ".temp"))
        
        return {
            "config": config,
            "working_directory": working_directory,
            "workspace_dirs": [str(Path(path).resolve()) for path in workspace_dirs if isinstance(path, str)],
            "project_temp_dir": str(Path(project_temp_dir).resolve()),
            # Shell-specific config with Gemini defaults
            "timeout_seconds": config.get("shell_timeout_seconds", DEFAULT_TIMEOUT_SECONDS),
            "max_output_chars": config.get("shell_max_output_chars", DEFAULT_MAX_OUTPUT_CHARS),
            "truncation_head_ratio": config.get("shell_truncation_head_ratio", DEFAULT_TRUNCATION_HEAD_RATIO),
        }
    
    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return tool schema matching Gemini CLI run_shell_command."""
        return [{
            "type": "function",
            "function": {
                "name": "run_shell_command",
                "description": (
                    "Execute a shell command and return its output.\n\n"
                    "Usage notes:\n"
                    "- Use this tool to execute shell commands. Avoid using this tool for "
                    "commands that may produce very large outputs.\n"
                    "- Always specify the `dir_path` parameter when the command needs to be "
                    "executed in a specific directory. Do not use `cd` in the command string.\n"
                    "- If the command may run for a long time, set `is_background` to true and "
                    "the command will run in the background.\n"
                    "- The output may be truncated if it exceeds the character limit. "
                    "In this case, a reference to the full output file will be provided."
                ),
                "parameters": {
                    "type": "object",
                    "properties": {
                        "command": {
                            "type": "string",
                            "description": "The shell command to execute.",
                        },
                        "description": {
                            "type": "string",
                            "description": "Brief description of the command's purpose.",
                        },
                        "dir_path": {
                            "type": "string",
                            "description": (
                                "The directory in which the command should be executed. "
                                "If not specified, the command runs in the current working directory."
                            ),
                        },
                        "is_background": {
                            "type": "boolean",
                            "description": (
                                "If true, runs the command in the background. "
                                "Useful for long-running commands like dev servers."
                            ),
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
    ) -> Dict[str, Any]:
        """Execute the run_shell_command tool.
        
        Args:
            tool_name: Should be "run_shell_command"
            arguments: Tool call arguments
            state: Tool state from init()
            
        Returns:
            Result dict with success, output, and metadata
        """
        if tool_name != "run_shell_command":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        command = arguments.get("command")
        if not isinstance(command, str) or not command.strip():
            return {"success": False, "error": "Command cannot be empty."}
        
        description = arguments.get("description")
        dir_path = arguments.get("dir_path") or state.get("working_directory")
        is_background = arguments.get("is_background", False)
        
        # Get timeout from state (config-provided or default)
        timeout_seconds = state.get("timeout_seconds", DEFAULT_TIMEOUT_SECONDS)
        
        # Execute via shared engine (sync wrapper around async)
        import asyncio
        import inspect
        
        async def _run():
            return await run_shell_command(
                command,
                workdir=dir_path,
                timeout_seconds=timeout_seconds,
                is_background=is_background,
            )
        
        # Check if we're already in an async context
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context - need to run in a thread
            # since we can't nest asyncio.run()
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as executor:
                future = executor.submit(asyncio.run, _run())
                result = future.result()
        except RuntimeError:
            # No running loop - we can use asyncio.run()
            result = asyncio.run(_run())
        
        # Format output based on result type
        if result.get("background"):
            return self._format_background_result(result, command, dir_path, description)
        
        if result.get("timed_out"):
            return self._format_timeout_result(result, timeout_seconds, command, dir_path)
        
        # Apply truncation to output
        output, trunc_meta = truncate_output(
            result["output"],
            limit_type="chars",
            limit_value=state.get("max_output_chars", DEFAULT_MAX_OUTPUT_CHARS),
            head_ratio=state.get("truncation_head_ratio", DEFAULT_TRUNCATION_HEAD_RATIO),
        )
        
        # Build result
        if result["exit_code"] == 0:
            return self._format_success_result(result, output, trunc_meta, command, dir_path, description, state)
        else:
            return self._format_failure_result(result, output, trunc_meta, command, dir_path, description)
    
    def _format_success_result(
        self,
        result: Dict[str, Any],
        output: str,
        trunc_meta: Dict[str, Any],
        command: str,
        dir_path: str | None,
        description: str | None,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Format successful command result."""
        lines: List[str] = []
        
        # Truncation message if needed
        if trunc_meta.get("truncated"):
            full_path = self._save_full_output(result["output"], state.get("project_temp_dir", ""))
            if full_path:
                lines.append(
                    f"Output too large. Showing first {trunc_meta['head_kept']:,} "
                    f"and last {trunc_meta['tail_kept']:,} characters. "
                    f"For full output see: {full_path}"
                )
            else:
                lines.append(
                    f"Output too large. Showing first {trunc_meta['head_kept']:,} "
                    f"and last {trunc_meta['tail_kept']:,} characters."
                )
            lines.append("")
        
        # Output
        if output.strip():
            lines.append(f"Output:\n{output}")
        else:
            lines.append("Output: (empty)")
        
        return {
            "success": True,
            "output": "\n".join(lines),
            "exit_code": result["exit_code"],
            "duration_seconds": result["duration_seconds"],
            "truncated": trunc_meta.get("truncated", False),
            "command": command,
            "dir_path": dir_path,
            "description": description,
        }
    
    def _format_failure_result(
        self,
        result: Dict[str, Any],
        output: str,
        trunc_meta: Dict[str, Any],
        command: str,
        dir_path: str | None,
        description: str | None,
    ) -> Dict[str, Any]:
        """Format failed command result."""
        lines: List[str] = []
        
        # Truncation message if needed
        if trunc_meta.get("truncated"):
            lines.append(
                f"Output too large. Showing first {trunc_meta['head_kept']:,} "
                f"and last {trunc_meta['tail_kept']:,} characters."
            )
            lines.append("")
        
        # Output
        if output.strip():
            lines.append(f"Output: {output}")
        
        # Error info
        lines.append(f"Error: Command failed with exit code {result['exit_code']}")
        lines.append(f"Exit Code: {result['exit_code']}")
        
        return {
            "success": False,
            "output": "\n".join(lines),
            "exit_code": result["exit_code"],
            "duration_seconds": result["duration_seconds"],
            "truncated": trunc_meta.get("truncated", False),
            "command": command,
            "dir_path": dir_path,
            "description": description,
        }
    
    def _format_timeout_result(
        self,
        result: Dict[str, Any],
        timeout_seconds: float,
        command: str,
        dir_path: str | None,
    ) -> Dict[str, Any]:
        """Format timeout result."""
        lines: List[str] = []
        timeout_minutes = timeout_seconds / 60.0
        
        lines.append(
            f"Command was automatically cancelled because it exceeded the timeout of "
            f"{timeout_minutes:.1f} minutes without output."
        )
        lines.append("Below is the output before it was cancelled:")
        
        if result["output"].strip():
            lines.append(result["output"])
        
        return {
            "success": False,
            "output": "\n".join(lines),
            "exit_code": None,
            "timed_out": True,
            "duration_seconds": result["duration_seconds"],
            "command": command,
            "dir_path": dir_path,
        }
    
    def _format_background_result(
        self,
        result: Dict[str, Any],
        command: str,
        dir_path: str | None,
        description: str | None,
    ) -> Dict[str, Any]:
        """Format background process result."""
        pid = result.get("pid")
        
        lines: List[str] = []
        lines.append(f"Command moved to background (PID: {pid}). Output hidden.")
        
        return {
            "success": True,
            "output": "\n".join(lines),
            "background": True,
            "pid": pid,
            "command": command,
            "dir_path": dir_path,
            "description": description,
        }
    
    def _save_full_output(self, output: str, temp_dir: str) -> str | None:
        """Save full output to temp file and return path.
        
        Args:
            output: Full output string
            temp_dir: Temp directory path from state
            
        Returns:
            File path string, or None on failure
        """
        try:
            temp_path = Path(temp_dir)
            temp_path.mkdir(parents=True, exist_ok=True)
            file_path = temp_path / f"shell_output_{uuid.uuid4().hex[:8]}.txt"
            file_path.write_text(output, encoding="utf-8")
            return str(file_path)
        except Exception:
            return None
    
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
        dir_path = result.get("dir_path")
        
        lines: List[str] = []
        
        if dir_path:
            lines.append(f"Directory: {dir_path}")
        
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


__all__ = ["GeminiShellTool"]