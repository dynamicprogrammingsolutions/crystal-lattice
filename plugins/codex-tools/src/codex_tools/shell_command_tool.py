"""Codex shell_command tool - string-based command execution.

This tool accepts a string command which is executed via the user's default
shell. Used by Codex-variant models (gpt-5.2-codex, gpt-5.3-codex, gpt-5.4).

Schema matches docs/codex-tools/shell_command/schema.without_request_permissions.json
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Dict, Iterator, List

from tool_compat_shared.shell_engine import (
    ShellInfo,
    detect_shell,
    run_shell_command,
)

from .base_shell_tool import BaseCodexShellTool, DEFAULT_MAX_OUTPUT_TOKENS


class ShellCommandTool(BaseCodexShellTool):
    """Codex shell_command tool - string-based command for Codex-variant models.
    
    Tool name: shell_command
    
    Command format: string (e.g., "echo hello")
    Execution: Wrapped via shell (e.g., bash -c "echo hello")
    
    Parameters:
    - command: string (required) - Shell script to execute
    - workdir: string - Working directory
    - timeout_ms: number - Timeout in milliseconds
    - login: boolean - Use login shell semantics (default: true)
    
    Models using this tool:
    - gpt-5.2-codex
    - gpt-5.3-codex
    - gpt-5.4
    - gpt-5.1-codex
    - gpt-5-codex
    """
    
    name: str = "shell_command"
    
    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return tool schema matching Codex CLI shell_command."""
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
        """Get shell config, adjusting for login flag.
        
        Login shell:
        - bash: uses -lc flag (loads ~/.bash_profile, ~/.bashrc, etc.)
        
        Non-login shell:
        - bash: uses -c flag (minimal environment)
        
        Args:
            login: Whether to use login shell semantics
            
        Returns:
            ShellInfo with appropriate args
        """
        shell = detect_shell()
        
        # Adjust args for login shell on bash
        if login and shell.name in ("bash", "sh"):
            # Use -lc for login shell
            return ShellInfo(name=shell.name, path=shell.path, args=("-lc",))
        
        # Default behavior (non-login or other shells)
        return shell
    
    async def execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute the shell_command tool.
        
        Args:
            tool_name: Should be "shell_command"
            arguments: Tool call arguments
            state: Tool state (not used)
            
        Returns:
            Result dict with success, output, exit_code, etc.
        """
        if tool_name != "shell_command":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        
        command = arguments.get("command", "")
        if not isinstance(command, str) or not command.strip():
            return {"success": False, "error": "command must be a non-empty string"}
        
        workdir = arguments.get("workdir")
        timeout_ms = arguments.get("timeout_ms")
        login = arguments.get("login", True)  # Default true
        
        # Convert timeout from ms to seconds
        timeout_seconds = None
        if timeout_ms is not None:
            try:
                timeout_seconds = float(timeout_ms) / 1000.0
            except (TypeError, ValueError):
                pass
        
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
        
        # Insert truncation marker if truncated
        if trunc_meta.get("truncated"):
            output = self._insert_truncation_marker(output, trunc_meta)
        
        # Build formatted result
        formatted = self._build_result(result, output, trunc_meta)
        
        # Add additional metadata
        formatted["command"] = command
        formatted["workdir"] = workdir
        formatted["login"] = login
        
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
            tool_name: Should be "shell_command"
            arguments: Tool call arguments
            state: Tool state
            
        Yields:
            Partial dicts with {"part": {"type": "text", "content": line}}
            Final dict with full result
        """
        if tool_name != "shell_command":
            return
        
        command = arguments.get("command", "")
        if not isinstance(command, str) or not command.strip():
            yield {"success": False, "error": "command must be a non-empty string"}
            return
        
        workdir = arguments.get("workdir")
        timeout_ms = arguments.get("timeout_ms")
        login = arguments.get("login", True)
        
        # Convert timeout
        timeout_seconds = None
        if timeout_ms is not None:
            try:
                timeout_seconds = float(timeout_ms) / 1000.0
            except (TypeError, ValueError):
                pass
        
        # Get shell with login flag
        shell = self._get_shell(login)
        
        # Build args
        from tool_compat_shared.shell_engine import build_shell_args
        args = build_shell_args(command, shell)
        
        # Run streaming subprocess
        yield from self._stream_subprocess(
            args=args,
            command=command,
            workdir=workdir,
            timeout_seconds=timeout_seconds,
            login=login,
        )
    
    def _stream_subprocess(
        self,
        args: List[str],
        command: str,
        workdir: str | None,
        timeout_seconds: float | None,
        login: bool,
    ) -> Iterator[Dict[str, Any]]:
        """Run subprocess and stream output.
        
        This is a sync generator that runs an async subprocess internally.
        Uses asyncio.run() to create a new event loop.
        """
        import os
        import sys
        
        async def _async_stream() -> Iterator[Dict[str, Any]]:
            start_time = time.monotonic()
            
            try:
                process = await asyncio.create_subprocess_exec(
                    *args,
                    cwd=workdir,
                    env=os.environ,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                )
            except Exception as exc:
                yield {"success": False, "error": f"Failed to execute command: {exc}"}
                return
            
            combined_chunks: List[str] = []
            stdout_chunks: List[str] = []
            stderr_chunks: List[str] = []
            
            async def read_streams():
                """Read stdout and stderr concurrently."""
                async def read_stdout():
                    if process.stdout is None:
                        return
                    async for line in process.stdout:
                        decoded = line.decode(errors="replace")
                        combined_chunks.append(decoded)
                        stdout_chunks.append(decoded)
                
                async def read_stderr():
                    if process.stderr is None:
                        return
                    async for line in process.stderr:
                        decoded = line.decode(errors="replace")
                        combined_chunks.append(decoded)
                        stderr_chunks.append(decoded)
                
                if timeout_seconds is not None:
                    try:
                        await asyncio.wait_for(
                            asyncio.gather(read_stdout(), read_stderr()),
                            timeout=timeout_seconds,
                        )
                    except asyncio.TimeoutError:
                        process.kill()
                        await process.wait()
                        return True  # timed_out
                else:
                    await asyncio.gather(read_stdout(), read_stderr())
                
                return False  # not timed_out
            
            # Run streaming with timeout handling
            timed_out = await read_streams()
            exit_code = process.returncode
            duration = time.monotonic() - start_time
            
            # Yield each stdout line as a partial
            for chunk in stdout_chunks:
                yield {
                    "part": {"type": "text", "content": chunk},
                    "command": command,
                    "workdir": workdir,
                }
            
            # Apply truncation to combined output
            output = "".join(combined_chunks)
            truncated_output, trunc_meta = self._apply_truncation(output)
            
            if trunc_meta.get("truncated"):
                truncated_output = self._insert_truncation_marker(truncated_output, trunc_meta)
            
            # Build result
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
            result["login"] = login
            
            yield result
        
        # Run the async generator in an event loop
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None
        
        if loop is not None:
            # Already in async context - create task
            from collections.abc import AsyncIterator
            
            async def collect():
                results = []
                async for item in _async_stream():
                    results.append(item)
                return results
            
            # We can't easily yield from async in a sync generator
            # For now, fall back to synchronous execution
            for item in self._sync_execute(command, workdir, timeout_seconds, login):
                yield item
        else:
            # No running loop - safe to use asyncio.run
            results = asyncio.run(self._collect_async_stream(_async_stream()))
            for item in results:
                yield item
    
    async def _collect_async_stream(self, async_gen) -> List[Dict[str, Any]]:
        """Collect all items from an async generator."""
        results = []
        async for item in async_gen:
            results.append(item)
        return results
    
    def _sync_execute(
        self,
        command: str,
        workdir: str | None,
        timeout_seconds: float | None,
        login: bool,
    ) -> Iterator[Dict[str, Any]]:
        """Fallback synchronous execution for streaming.
        
        Uses subprocess.Popen for line-by-line streaming.
        """
        import os
        import subprocess
        import threading
        import queue
        
        shell = self._get_shell(login)
        from tool_compat_shared.shell_engine import build_shell_args
        args = build_shell_args(command, shell)
        
        start_time = time.monotonic()
        
        try:
            proc = subprocess.Popen(
                args,
                cwd=workdir,
                env=os.environ,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except Exception as exc:
            yield {"success": False, "error": f"Failed to execute command: {exc}"}
            return
        
        stdout_queue: queue.Queue[str] = queue.Queue()
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
            import time
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
                except queue.Empty:
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
        result["login"] = login
        
        yield result


__all__ = ["ShellCommandTool"]