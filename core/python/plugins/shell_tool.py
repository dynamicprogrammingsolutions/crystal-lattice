"""
ShellTool plugin: execute shell commands in a Codex-style sandboxed environment.

This tool exposes a `shell` function that runs commands via
`["bash", "-lc", command]` with an explicit working directory.
It is inspired by the Codex shell tool semantics described in
SHELL_TOOL_RESEARCH.md.
"""

from __future__ import annotations

import os
import queue
import subprocess
import threading
import time
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
                "default": 60,
                "description": "Default maximum execution time per command in seconds",
            },
            "max_output_chars": {
                "type": "integer",
                "default": 8000,
                "description": "Maximum number of characters to retain from stdout/stderr",
            },
            "max_output_lines": {
                "type": "integer",
                "default": 2000,
                "description": "Maximum number of lines of stdout/stderr to retain before truncation.",
            },
        }

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        return []

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        # Tools own their internal state; this implementation only needs configuration.
        return {"config": config}

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

        timeout_default = config.get("timeout_seconds", 60)
        timeout_arg = arguments.get("timeout_seconds")
        try:
            timeout_seconds = int(timeout_arg) if timeout_arg is not None else int(timeout_default)
            if timeout_seconds <= 0:
                timeout_seconds = int(timeout_default) if timeout_default else 300
        except Exception:
            timeout_seconds = 60

        env_arg = arguments.get("env")
        exec_env = os.environ.copy()
        if isinstance(env_arg, dict):
            for key, value in env_arg.items():
                if isinstance(key, str):
                    exec_env[key] = str(value)

        max_output_lines = int(config.get("max_output_lines", 2000) or 2000)
        configured_chars = int(config.get("max_output_chars", 8000) or 8000)
        # Guard against extremely long lines by capping total characters
        # to approximately ``80 * max_output_lines``.
        hard_char_cap = max_output_lines * 80
        max_output_chars = min(configured_chars, hard_char_cap)

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
            truncated_stdout = self._truncate(stdout, max_output_lines, max_output_chars)
            truncated_stderr = self._truncate(stderr, max_output_lines, max_output_chars)
            return {
                "success": False,
                "error": f"Command timed out after {timeout_seconds} seconds",
                "returncode": None,
                "stdout": truncated_stdout,
                "stderr": truncated_stderr,
                "stdout_truncated": truncated_stdout != stdout,
                "stderr_truncated": truncated_stderr != stderr,
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
        truncated_stdout = self._truncate(stdout, max_output_lines, max_output_chars)
        truncated_stderr = self._truncate(stderr, max_output_lines, max_output_chars)

        success = completed.returncode == 0
        result: Dict[str, Any] = {
            "success": success,
            "returncode": completed.returncode,
            "stdout": truncated_stdout,
            "stderr": truncated_stderr,
            "stdout_truncated": truncated_stdout != stdout,
            "stderr_truncated": truncated_stderr != stderr,
            "workdir": abs_workdir,
            "command": raw_command,
            "timeout_seconds": timeout_seconds,
            "explicit_workdir": bool(isinstance(raw_workdir, str) and raw_workdir.strip()),
        }

        if not success and "error" not in result:
            result["error"] = f"Command exited with code {completed.returncode}"

        return result

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        success = bool(result.get("success"))
        returncode = result.get("returncode")
        stdout = str(result.get("stdout", "") or "")
        stderr = str(result.get("stderr", "") or "")
        stdout_truncated = bool(result.get("stdout_truncated"))
        stderr_truncated = bool(result.get("stderr_truncated"))

        stdout_has = bool(stdout.strip())
        stderr_has = bool(stderr.strip())
        exitcode_is_zero = isinstance(returncode, int) and returncode == 0

        # Simple success path: no stderr, zero exit code.
        #
        # - When output is not truncated, return stdout only so that
        #   LLMs see the raw command output without extra framing.
        # - When output is truncated, prepend a minimal header so the
        #   truncation is visible: "STDOUT (truncated):".
        if success and exitcode_is_zero and not stderr_has:
            if stdout_truncated and stdout_has:
                return f"STDOUT (truncated):\n{stdout}"
            if stdout_has:
                return stdout
            # No stdout at all; fall back to a simple success prefix.
            return "Command succeeded (exit code 0)."

        # General case: non-zero exit code, stderr present, or
        # non-success. Always include a prefix plus STDOUT/STDERR
        # sections, marking truncated stdout when applicable.
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

        if stdout_has:
            if stdout_truncated:
                parts.append(f"STDOUT (truncated):\n{stdout}")
            else:
                parts.append(f"STDOUT:\n{stdout}")
        if stderr_has:
            parts.append(f"STDERR:\n{stderr}")

        return "\n\n".join(parts)

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        """Add the executed command to the top of the display content.

        Workdir is only shown when explicitly overridden via the
        ``workdir`` tool argument so that default working-directory
        behaviour remains compact.
        """

        command = result.get("command")
        if isinstance(command, str) and command.strip():
            cmd = command.strip()
            # Detect whether the caller explicitly changed workdir for
            # this invocation. This flag is injected by execute_tool /
            # stream_tool.
            explicit = bool(result.get("explicit_workdir"))
            workdir = result.get("workdir") if explicit else None
            if isinstance(workdir, str) and workdir.strip():
                header = self._build_header(cmd, workdir.strip())
            else:
                header = self._build_header(cmd, None)
            content = f"{header}\n{text}" if text else header
        else:
            content = text

        return {"type": "text", "content": content}

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

        timeout_default = config.get("timeout_seconds", 60)
        timeout_arg = arguments.get("timeout_seconds")
        try:
            timeout_seconds = int(timeout_arg) if timeout_arg is not None else int(timeout_default)
            if timeout_seconds <= 0:
                timeout_seconds = int(timeout_default) if timeout_default else 300
        except Exception:
            timeout_seconds = 60

        env_arg = arguments.get("env")
        exec_env = os.environ.copy()
        if isinstance(env_arg, dict):
            for key, value in env_arg.items():
                if isinstance(key, str):
                    exec_env[key] = str(value)

        max_output_lines = int(config.get("max_output_lines", 2000) or 2000)
        configured_chars = int(config.get("max_output_chars", 8000) or 8000)
        hard_char_cap = max_output_lines * 80
        max_output_chars = min(configured_chars, hard_char_cap)

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

        # Use a background thread to read stdout so we can enforce a real
        # wall-clock timeout even when the subprocess isn't producing output.
        stdout_queue: "queue.Queue[str]" = queue.Queue()

        def _stdout_reader() -> None:
            try:
                if proc.stdout is None:
                    return
                for line in proc.stdout:
                    if not line:
                        break
                    stdout_queue.put(line)
            finally:
                try:
                    if proc.stdout is not None and not proc.stdout.closed:
                        proc.stdout.close()
                except Exception:
                    pass

        reader_thread = threading.Thread(target=_stdout_reader, daemon=True)
        reader_thread.start()

        start_time = time.monotonic()
        sent_header = False

        try:
            while True:
                # Check for timeout first so we don't block forever on queue.get.
                elapsed = time.monotonic() - start_time
                if timeout_seconds and elapsed >= timeout_seconds:
                    timed_out = True
                    proc.kill()
                    try:
                        proc.wait(timeout=1)
                    except Exception:
                        pass
                    break

                # Drain any available stdout lines, but don't block too long.
                try:
                    line = stdout_queue.get(timeout=0.1)
                except queue.Empty:
                    # If the process has exited and there's nothing left in the
                    # queue, we're done.
                    if proc.poll() is not None and stdout_queue.empty():
                        break
                    continue

                stdout_chunks.append(line)
                if line:
                    # Attach the executed command header at the top of
                    # the first streamed chunk so that incremental
                    # output matches the header used in
                    # ``to_display_format``.
                    if not sent_header:
                        cmd = str(raw_command).strip()
                        explicit = bool(isinstance(raw_workdir, str) and raw_workdir.strip())
                        workdir_for_header = abs_workdir if explicit else None
                        header = self._build_header(cmd, workdir_for_header) if cmd else ""
                        content = f"{header}\n{line}" if header else line
                        sent_header = True
                    else:
                        content = line

                    yield {
                        "part": {"type": "text", "content": content},
                        "command": raw_command,
                        "workdir": abs_workdir,
                    }

            # Ensure the process has fully exited (or been killed) before
            # collecting stderr, but don't let this hang the generator.
            if proc.poll() is None:
                try:
                    proc.wait(timeout=1)
                except Exception:
                    pass
        finally:
            try:
                reader_thread.join(timeout=1)
            except Exception:
                pass

            if proc.stderr is not None:
                try:
                    stderr_text = proc.stderr.read() or ""
                except Exception:
                    stderr_text = ""
                finally:
                    try:
                        proc.stderr.close()
                    except Exception:
                        pass

        stdout_text = "".join(stdout_chunks)
        truncated_stdout = self._truncate(stdout_text, max_output_lines, max_output_chars)
        truncated_stderr = self._truncate(stderr_text, max_output_lines, max_output_chars)

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
            "stdout_truncated": truncated_stdout != stdout_text,
            "stderr_truncated": truncated_stderr != stderr_text,
            "workdir": abs_workdir,
            "command": raw_command,
            "timeout_seconds": timeout_seconds,
            "explicit_workdir": bool(isinstance(raw_workdir, str) and raw_workdir.strip()),
        }
        if not success:
            result["error"] = error_msg or result.get("error", "Command failed.")

        # For streaming, append a compact summary at the end of the
        # output so that exit codes and stderr are visible without
        # duplicating stdout. This mirrors the semantics of
        # ``format_tool_result``:
        #
        # - When there is stderr or a non-zero exit code, append an
        #   exit-code line plus STDERR (and a STDOUT header so users
        #   can disambiguate streams).
        # - When stdout is truncated but the command otherwise
        #   succeeded cleanly, append only a ``STDOUT (truncated):``
        #   header.
        stdout_has = bool(truncated_stdout.strip())
        stderr_has = bool(truncated_stderr.strip())
        stdout_truncated = truncated_stdout != stdout_text
        exitcode_is_zero = isinstance(return_code, int) and return_code == 0

        summary_lines: List[str] = []

        if success and exitcode_is_zero and not stderr_has:
            # Simple success path; only emit a marker when stdout has
            # been truncated so callers can distinguish complete vs
            # partial output.
            if stdout_truncated and stdout_has:
                summary_lines.append("STDOUT was truncated")
        else:
            # Non-zero exit code, stderr present, or explicit failure.
            # Always include an exit-code/error prefix and stderr,
            # plus a STDOUT header when any stdout was produced.
            if success:
                if return_code is not None:
                    prefix = f"Command succeeded (exit code {return_code})."
                else:
                    prefix = "Command succeeded."
            else:
                if result.get("error"):
                    prefix = str(result["error"])
                elif return_code is not None:
                    prefix = f"Command failed with exit code {return_code}"
                else:
                    prefix = "Command failed."

            summary_lines.append(prefix)

            if stdout_has:
                if stdout_truncated:
                    summary_lines.append("STDOUT was truncated")
            if stderr_has:
                summary_lines.append("STDERR:")
                summary_lines.append(truncated_stderr)

        if summary_lines:
            # Emit the summary as a distinct part type so that
            # renderers can treat it separately from the main stdout
            # stream (for example, always showing it even when the
            # bulk output is truncated).
            yield {
                "part": {"type": "summary", "content": "\n".join(summary_lines) + "\n"},
                "command": raw_command,
                "workdir": abs_workdir,
            }

        yield result

    @staticmethod
    def _build_header(command: str, workdir: str | None) -> str:
        """Return a standard multi-line header for shell output.

        Format:

        - Workdir: <path>      (only when ``workdir`` is not None)
        - Command executed: ...
        - Output:
        """

        lines: List[str] = []
        if workdir:
            lines.append(f"Workdir: {workdir}")
        lines.append(f"Command executed: {command}")
        lines.append("Output:")
        return "\n".join(lines)

    @staticmethod
    def _truncate(text: str, max_lines: int, max_chars: int) -> str:
        """Truncate text by line and character limits.

        ``max_lines`` controls the number of newline-terminated lines
        retained; ``max_chars`` caps total characters kept. When either
        limit is non-positive, it is ignored.
        """

        original_len = len(text)

        if max_lines > 0:
            lines = text.splitlines(keepends=True)
            if len(lines) > max_lines:
                text = "".join(lines[:max_lines])

        if max_chars > 0 and len(text) > max_chars:
            text = text[:max_chars]

        if len(text) == original_len:
            return text

        hidden = original_len - len(text)
        return f"{text}\n... (truncated, {hidden} more characters)"
