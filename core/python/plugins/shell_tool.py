"""
ShellTool plugin: execute shell commands in a Codex-style sandboxed environment.

This tool exposes a `shell` function that runs commands via
`["bash", "-lc", command]` with an explicit working directory.
It is inspired by the Codex shell tool semantics described in
SHELL_TOOL_RESEARCH.md.
"""

from __future__ import annotations

import os
import subprocess
from typing import Any, Dict, List, Iterator

from agent_core.types import ToolPlugin


class ShellTool(ToolPlugin):
    name: str = "shell"
    version: str = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "allowed_paths": {
                "type": "array",
                "items": {"type": "string"},
                "default": ["."],
                "description": "Allowed base directories for the working directory",
            },
            "working_directory": {
                "type": "string",
                "default": ".",
                "description": "Base working directory used when a tool call omits workdir",
            },
            "timeout_seconds": {
                "type": "integer",
                "default": 300,
                "description": "Default maximum execution time per command in seconds",
            },
            "max_output_chars": {
                "type": "integer",
                "default": 8000,
                "description": "Maximum number of characters to retain from stdout/stderr",
            },
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return []

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # Tools own their internal state; this implementation only needs configuration.
        return {"config": dict(config)}

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        config = state.get("config", {})
        base_workdir = config.get("working_directory", ".")
        return [
            {
                "type": "function",
                "function": {
                    "name": "shell",
                    "description": (
                        "Execute a shell command using bash -lc in a sandboxed "
                        "working directory. Always prefer setting workdir explicitly."
                    ),
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "command": {
                                "type": "string",
                                "description": (
                                    "The shell command to execute. It will be run as "
                                    "bash -lc '<command>'."
                                ),
                            },
                            "workdir": {
                                "type": "string",
                                "description": (
                                    "Working directory for the command. If omitted, "
                                    f"the tool uses the configured working_directory: {base_workdir}"
                                ),
                            },
                            "timeout_seconds": {
                                "type": "integer",
                                "description": (
                                    "Optional per-call timeout override in seconds. "
                                    "Defaults to the configured timeout_seconds."
                                ),
                            },
                            "env": {
                                "type": "object",
                                "description": (
                                    "Optional additional environment variables as a "
                                    "string-to-string map."
                                ),
                                "additionalProperties": {"type": "string"},
                            },
                        },
                        "required": ["command"],
                    },
                },
            }
        ]

    def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if tool_name != "shell":
            return {"success": False, "error": f"Unknown tool: {tool_name}"}

        config = state.get("config", {})
        raw_command = arguments.get("command", "")

        if not isinstance(raw_command, str) or not raw_command.strip():
            return {"success": False, "error": "command must be a non-empty string"}

        raw_workdir = arguments.get("workdir")
        base_workdir = config.get("working_directory", ".")
        workdir = (
            str(raw_workdir).strip()
            if isinstance(raw_workdir, str) and raw_workdir.strip()
            else str(base_workdir)
        )

        try:
            if not os.path.isabs(workdir):
                workdir = os.path.join(base_workdir, workdir)
            abs_workdir = os.path.abspath(workdir)
        except Exception:
            return {"success": False, "error": f"Invalid workdir: {workdir}"}

        if not os.path.isdir(abs_workdir):
            return {"success": False, "error": f"Working directory does not exist: {abs_workdir}"}

        base_workdir = config.get("working_directory", ".")
        allowed_config = config.get("allowed_paths")
        allowed = allowed_config if allowed_config is not None else [base_workdir]
        abs_allowed = [os.path.abspath(p) for p in allowed]
        if not any(abs_workdir.startswith(p) for p in abs_allowed):
            return {
                "success": False,
                "error": f"Working directory {abs_workdir} is not in allowed paths",
            }

        timeout_default = config.get("timeout_seconds", 300)
        timeout_arg = arguments.get("timeout_seconds")
        try:
            timeout_seconds = int(timeout_arg) if timeout_arg is not None else int(timeout_default)
            if timeout_seconds <= 0:
                timeout_seconds = int(timeout_default) if timeout_default else 300
        except Exception:
            timeout_seconds = 300

        env_arg = arguments.get("env")
        exec_env = os.environ.copy()
        if isinstance(env_arg, dict):
            for key, value in env_arg.items():
                if isinstance(key, str):
                    exec_env[key] = str(value)

        max_output_chars = int(config.get("max_output_chars", 8000) or 8000)

        try:
            completed = subprocess.run(
                ["bash", "-lc", raw_command],
                cwd=abs_workdir,
                env=exec_env,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
                check=False,
            )
        except subprocess.TimeoutExpired as exc:
            raw_stdout = exc.stdout
            raw_stderr = exc.stderr
            stdout = (
                raw_stdout.decode() if isinstance(raw_stdout, bytes) else (raw_stdout or "")
            )
            stderr = (
                raw_stderr.decode() if isinstance(raw_stderr, bytes) else (raw_stderr or "")
            )
            truncated_stdout = self._truncate(stdout, max_output_chars)
            truncated_stderr = self._truncate(stderr, max_output_chars)
            return {
                "success": False,
                "error": f"Command timed out after {timeout_seconds} seconds",
                "returncode": None,
                "stdout": truncated_stdout,
                "stderr": truncated_stderr,
                "workdir": abs_workdir,
                "command": raw_command,
                "timeout_seconds": timeout_seconds,
            }
        except Exception as exc:  # pragma: no cover - defensive
            return {"success": False, "error": f"Failed to execute command: {exc}"}

        raw_stdout = completed.stdout
        raw_stderr = completed.stderr
        stdout = (
            raw_stdout.decode() if isinstance(raw_stdout, bytes) else (raw_stdout or "")
        )
        stderr = (
            raw_stderr.decode() if isinstance(raw_stderr, bytes) else (raw_stderr or "")
        )
        truncated_stdout = self._truncate(stdout, max_output_chars)
        truncated_stderr = self._truncate(stderr, max_output_chars)

        success = completed.returncode == 0
        result: Dict[str, Any] = {
            "success": success,
            "returncode": completed.returncode,
            "stdout": truncated_stdout,
            "stderr": truncated_stderr,
            "workdir": abs_workdir,
            "command": raw_command,
            "timeout_seconds": timeout_seconds,
        }

        if not success and "error" not in result:
            result["error"] = f"Command exited with code {completed.returncode}"

        return result

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        success = bool(result.get("success"))
        returncode = result.get("returncode")
        stdout = str(result.get("stdout", ""))
        stderr = str(result.get("stderr", ""))

        if success:
            prefix = (
                f"Command succeeded (exit code {returncode})."
                if returncode is not None
                else "Command succeeded."
            )
        else:
            error_msg = result.get("error") or (
                f"Command failed with exit code {returncode}"
                if returncode is not None
                else "Command failed."
            )
            prefix = error_msg

        parts: List[str] = [prefix]

        if stdout.strip():
            parts.append(f"STDOUT:\n{stdout}")
        if stderr.strip():
            parts.append(f"STDERR:\n{stderr}")

        return "\n\n".join(parts)

    def stream_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        """Stream shell command output as partials plus a final result.

        This uses the same sandboxing rules as :meth:`execute_tool` but yields
        stdout lines incrementally as ``{"part": {"type": "text", "content": ...}}``
        payloads and finally a RESULT dict containing the full stdout/stderr and
        exit information.
        """
        if tool_name != "shell":
            return

        config = state.get("config", {})
        raw_command = arguments.get("command", "")

        if not isinstance(raw_command, str) or not raw_command.strip():
            # Validation error: yield a final RESULT dict only.
            yield {"success": False, "error": "command must be a non-empty string"}
            return

        raw_workdir = arguments.get("workdir")
        base_workdir = config.get("working_directory", ".")
        workdir = (
            str(raw_workdir).strip()
            if isinstance(raw_workdir, str) and raw_workdir.strip()
            else str(base_workdir)
        )

        try:
            if not os.path.isabs(workdir):
                workdir = os.path.join(base_workdir, workdir)
            abs_workdir = os.path.abspath(workdir)
        except Exception:
            yield {"success": False, "error": f"Invalid workdir: {workdir}"}
            return

        if not os.path.isdir(abs_workdir):
            yield {
                "success": False,
                "error": f"Working directory does not exist: {abs_workdir}",
            }
            return

        allowed_config = config.get("allowed_paths")
        allowed = allowed_config if allowed_config is not None else [base_workdir]
        abs_allowed = [os.path.abspath(p) for p in allowed]
        if not any(abs_workdir.startswith(p) for p in abs_allowed):
            yield {
                "success": False,
                "error": f"Working directory {abs_workdir} is not in allowed paths",
            }
            return

        timeout_default = config.get("timeout_seconds", 300)
        timeout_arg = arguments.get("timeout_seconds")
        try:
            timeout_seconds = int(timeout_arg) if timeout_arg is not None else int(timeout_default)
            if timeout_seconds <= 0:
                timeout_seconds = int(timeout_default) if timeout_default else 300
        except Exception:
            timeout_seconds = 300

        env_arg = arguments.get("env")
        exec_env = os.environ.copy()
        if isinstance(env_arg, dict):
            for key, value in env_arg.items():
                if isinstance(key, str):
                    exec_env[key] = str(value)

        max_output_chars = int(config.get("max_output_chars", 8000) or 8000)

        try:
            proc = subprocess.Popen(
                ["bash", "-lc", raw_command],
                cwd=abs_workdir,
                env=exec_env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except Exception as exc:
            yield {"success": False, "error": f"Failed to execute command: {exc}"}
            return

        stdout_chunks: List[str] = []
        stderr_text = ""
        timed_out = False

        try:
            if proc.stdout is not None:
                for line in proc.stdout:
                    if not line:
                        break
                    stdout_chunks.append(line)
                    chunk = line.rstrip("\n")
                    if chunk:
                        yield {"part": {"type": "text", "content": chunk}}
            try:
                proc.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                proc.kill()
                try:
                    proc.wait(timeout=1)
                except Exception:
                    pass
            except Exception:
                proc.kill()
        finally:
            if proc.stderr is not None:
                try:
                    stderr_text = proc.stderr.read() or ""
                except Exception:
                    stderr_text = ""
            if proc.stdout is not None and not proc.stdout.closed:
                proc.stdout.close()
            if proc.stderr is not None and not proc.stderr.closed:
                proc.stderr.close()

        stdout_text = "".join(stdout_chunks)
        truncated_stdout = self._truncate(stdout_text, max_output_chars)
        truncated_stderr = self._truncate(stderr_text, max_output_chars)

        if timed_out:
            success = False
            return_code = None
            error_msg = f"Command timed out after {timeout_seconds} seconds"
        else:
            return_code = proc.returncode
            success = return_code == 0
            if not success:
                error_msg = f"Command exited with code {return_code}"
            else:
                error_msg = ""

        result: Dict[str, Any] = {
            "success": success,
            "returncode": return_code,
            "stdout": truncated_stdout,
            "stderr": truncated_stderr,
            "workdir": abs_workdir,
            "command": raw_command,
            "timeout_seconds": timeout_seconds,
        }
        if not success:
            result["error"] = error_msg or result.get("error", "Command failed.")

        yield result

    @staticmethod
    def _truncate(text: str, max_chars: int) -> str:
        if max_chars <= 0:
            return ""
        if len(text) <= max_chars:
            return text
        hidden = len(text) - max_chars
        return f"{text[:max_chars]}\n... (truncated, {hidden} more characters)"
