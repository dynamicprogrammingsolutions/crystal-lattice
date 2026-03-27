"""Codex shell tool - array-based command execution.

This tool accepts an array of strings representing the command and its arguments,
passed directly to execvp (no shell wrapper). Used by non-Codex-variant models
(gpt-5, gpt-5.1, gpt-5.2).

Schema matches docs/codex-tools/shell/schema.without_request_permissions.json
"""

from __future__ import annotations

import asyncio
import os
import subprocess
import threading
import time
from queue import Queue
from typing import Any, Dict, Iterator, List

from tool_compat_shared.shell_engine import run_shell_command

from .base_shell_tool import BaseCodexShellTool


class ShellArrayTool(BaseCodexShellTool):
    """Codex shell tool - array-based command for non-Codex-variant models.
    
    Tool name: shell
    
    Command format: array (e.g., ["bash", "-lc", "echo hello"])
    Execution: Direct execvp (no shell wrapper)
    
    Parameters:
    - command: array of strings (required) - Command to execute
    - workdir: string - Working directory
    - timeout_ms: number - Timeout in milliseconds
    
    Note: Unlike shell_command, this tool does NOT have a 'login' parameter.
    The caller specifies the exact command including shell flags.
    
    Models using this tool:
    - gpt-5
    - gpt-5.1
    - gpt-5.2 (non-codex variant)
    
    The command is passed directly to execvp, so callers should typically
    prefix with ["bash", "-lc", "..."] for shell-like behavior.
    """
    
    name: str = "shell"
    
    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return tool schema matching Codex CLI shell (array-based)."""
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
        """Execute the shell tool (array-based).
        
        Args:
            tool_name: Should be "shell"
            arguments: Tool call arguments
            state: Tool state (not used)
            
        Returns:
            Result dict with success, output, exit_code, etc.
        """
        if tool_name != "shell":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        command = arguments.get("command", [])
        
        # Validate command is a list
        if not isinstance(command, list):
            return {"success": False, "error": "command must be an array of strings"}
        
        if not command:
            return {"success": False, "error": "command array cannot be empty"}
        
        # Validate all elements are strings
        if not all(isinstance(c, str) for c in command):
            return {"success": False, "error": "command array must contain only strings"}
        
        workdir = arguments.get("workdir")
        timeout_ms = arguments.get("timeout_ms")
        
        # Convert timeout from ms to seconds
        timeout_seconds = None
        if timeout_ms is not None:
            try:
                timeout_seconds = float(timeout_ms) / 1000.0
            except (TypeError, ValueError):
                pass
        
        # Call shared engine with array command (direct exec)
        try:
            result = await run_shell_command(
                command,  # list[str] - passed directly to exec
                workdir=workdir,
                timeout_seconds=timeout_seconds,
            )
        except FileNotFoundError:
            return {
                "success": False,
                "error": f"Command not found: {command[0]}",
                "exit_code": 127,  # Standard "command not found" exit code
                "command": command,
                "workdir": workdir,
            }
        except PermissionError:
            return {
                "success": False,
                "error": f"Permission denied: {command[0]}",
                "exit_code": 126,  # Standard "permission denied" exit code
                "command": command,
                "workdir": workdir,
            }
        
        # Apply truncation
        output, trunc_meta = self._apply_truncation(result["output"])
        
        # Insert truncation marker if truncated
        if trunc_meta.get("truncated"):
            output = self._insert_truncation_marker(output, trunc_meta)
        
        # Build formatted result
        formatted = self._build_result(result, output, trunc_meta)
        
        # Add additional metadata
        formatted["command"] = command
        formatted["workdir"] = workdir
        
        return formatted
    
    def stream_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        """Stream shell command output in real-time.
        
        Yields partial output chunks followed by a final result dict.
        
        Args:
            tool_name: Should be "shell"
            arguments: Tool call arguments
            state: Tool state
            
        Yields:
            Partial dicts with {"part": {"type": "text", "content": line}}
            Final dict with full result
        """
        if tool_name != "shell":
            return
        
        command = arguments.get("command", [])
        
        # Validate command is a list
        if not isinstance(command, list):
            yield {"success": False, "error": "command must be an array of strings"}
            return
        
        if not command:
            yield {"success": False, "error": "command array cannot be empty"}
            return
        
        if not all(isinstance(c, str) for c in command):
            yield {"success": False, "error": "command array must contain only strings"}
            return
        
        workdir = arguments.get("workdir")
        timeout_ms = arguments.get("timeout_ms")
        
        # Convert timeout
        timeout_seconds = None
        if timeout_ms is not None:
            try:
                timeout_seconds = float(timeout_ms) / 1000.0
            except (TypeError, ValueError):
                pass
        
        # Use synchronous streaming (same pattern as shell_command)
        yield from self._sync_execute(
            command=command,
            workdir=workdir,
            timeout_seconds=timeout_seconds,
        )
    
    def _sync_execute(
        self,
        command: List[str],
        workdir: str | None,
        timeout_seconds: float | None,
    ) -> Iterator[Dict[str, Any]]:
        """Synchronous execution with line-by-line streaming.
        
        Uses subprocess.Popen for streaming output.
        """
        start_time = time.monotonic()
        
        try:
            proc = subprocess.Popen(
                command,  # Direct exec (no shell wrapper)
                cwd=workdir,
                env=os.environ,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except FileNotFoundError:
            yield {"success": False, "error": f"Command not found: {command[0]}"}
            return
        except Exception as exc:
            yield {"success": False, "error": f"Failed to execute command: {exc}"}
            return
        
        stdout_queue: Queue[str] = Queue()
        stderr_chunks: List[str] = []
        
        def read_stdout():
            if proc.stdout is None:
                return
            for line in proc.stdout:
                stdout_queue.put(line)
        
        def read_stderr():
            if proc.stderr is None:
                return
            for line in proc.stderr:
                stderr_chunks.append(line)
        
        stdout_thread = threading.Thread(target=read_stdout, daemon=True)
        stderr_thread = threading.Thread(target=read_stderr, daemon=True)
        stdout_thread.start()
        stderr_thread.start()
        
        stdout_chunks: List[str] = []
        timed_out = False
        
        try:
            while True:
                elapsed = time.monotonic() - start_time
                if timeout_seconds is not None and elapsed >= timeout_seconds:
                    timed_out = True
                    proc.kill()
                    break
                
                try:
                    line = stdout_queue.get(timeout=0.1)
                    stdout_chunks.append(line)
                    yield {
                        "part": {"type": "text", "content": line},
                        "command": command,
                        "workdir": workdir,
                    }
                except:  # queue.Empty
                    if proc.poll() is not None:
                        break
        finally:
            stdout_thread.join(timeout=1)
            stderr_thread.join(timeout=1)
        
        exit_code = proc.returncode
        duration = time.monotonic() - start_time
        
        # Combine output
        output = "".join(stdout_chunks) + "".join(stderr_chunks)
        truncated_output, trunc_meta = self._apply_truncation(output)
        
        if trunc_meta.get("truncated"):
            truncated_output = self._insert_truncation_marker(truncated_output, trunc_meta)
        
        result = self._build_result(
            {
                "exit_code": exit_code,
                "output": truncated_output,
                "stdout": "".join(stdout_chunks),
                "stderr": "".join(stderr_chunks),
                "duration_seconds": duration,
                "timed_out": timed_out,
            },
            truncated_output,
            trunc_meta,
        )
        
        result["command"] = command
        result["workdir"] = workdir
        
        yield result


__all__ = ["ShellArrayTool"]