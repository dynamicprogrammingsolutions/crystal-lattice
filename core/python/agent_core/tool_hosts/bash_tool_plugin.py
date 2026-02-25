from __future__ import annotations

import json
import os
import queue
import shutil
import subprocess
import threading
import time
from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping, Optional, Tuple

from agent_core.utils import get_logger


logger = get_logger("BashToolPlugin")


_SCALAR_TYPES = (str, int, float, bool)


def _to_cli_scalar(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


class BashToolPlugin:
    """ToolPlugin proxy delegating to a single bash script.

    Subclasses are expected to set:

    - ``name`` / ``version`` (tool plugin identity)
    - ``bash_entry`` (absolute path to the ``.bash`` tool file)
    - ``bash_schema`` (parsed schema returned by ``schema``)
    - ``bash_tools`` (OpenAI tool schemas; typically one function)
    - ``bash_args_mode`` ("flags" | "positional" | "json")
    - optional ``bash_positional`` (positional mapping when args_mode=="positional")
    """

    name: str = "bash_tool"
    version: str = "unknown"

    bash_entry: str = ""
    bash_schema: Dict[str, Any] = {}
    bash_tools: List[Dict[str, Any]] = []

    bash_args_mode: str = "flags"
    bash_positional: List[Dict[str, Any]] = []

    bash_timeout_seconds: float = 60.0
    bash_error_timeout_seconds: float = 5.0
    bash_stream_stderr: bool = False
    bash_command: str = "bash"

    # ---------------------------------------------------------------------
    # ToolPlugin lifecycle + capability methods
    # ---------------------------------------------------------------------

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return self.bash_tools

    # ---------------------------------------------------------------------
    # ToolPlugin execution + formatting
    # ---------------------------------------------------------------------

    def execute_tool(
        self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Dict[str, Any]:
        if not self._handles_tool_name(tool_name):
            return {"success": False, "error": f"Unknown tool: {tool_name}"}
        return self._execute_run_tool(arguments, state)

    def stream_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        if not self._handles_tool_name(tool_name):
            return

        yield from self._stream_run_tool(arguments, state)

    def format_tool_call_preview(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> str:
        if not self._handles_tool_name(tool_name):
            return ""

        stdout, _stderr, code = self._call_subcommand(
            "preview",
            arguments,
            state,
            timeout=self.bash_timeout_seconds,
        )
        if code != 0:
            return ""
        line = (stdout or "").strip().splitlines()[0] if (stdout or "").strip() else ""
        return line

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        success = bool(result.get("success"))
        if success:
            return self._format_success(result)

        custom = self._try_format_error_with_script(result, state)
        if isinstance(custom, str) and custom.strip():
            return custom.strip()
        return self._format_failure_fallback(result)

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    def _handles_tool_name(self, tool_name: str) -> bool:
        # v1: one tool per bash file; enforce id == function.name at load time.
        return tool_name == self.name

    def _call_subcommand(
        self,
        subcommand: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
        *,
        timeout: float,
        exit_code: Optional[int] = None,
        extra_env: Optional[Mapping[str, str]] = None,
    ) -> Tuple[str, str, int]:
        if not shutil.which(self.bash_command):
            return "", f"Missing required executable: {self.bash_command}", 127

        try:
            cmd, stdin_data = self._build_invocation(subcommand, arguments, exit_code=exit_code)
        except ValueError as exc:
            return "", str(exc), 2
        cwd = self._resolve_cwd(state)
        env = dict(os.environ)
        if extra_env:
            env.update({k: str(v) for k, v in extra_env.items() if isinstance(k, str)})

        try:
            cp = subprocess.run(
                cmd,
                input=stdin_data,
                cwd=cwd,
                env=env,
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            return cp.stdout or "", cp.stderr or "", int(cp.returncode)
        except subprocess.TimeoutExpired as exc:
            stdout = exc.stdout or ""
            stderr = exc.stderr or ""
            return stdout, stderr, 124
        except Exception as exc:
            return "", str(exc), 1

    def _resolve_cwd(self, state: Dict[str, Any]) -> Optional[str]:
        cfg = state.get("config")
        if not isinstance(cfg, dict):
            return None
        wd = cfg.get("working_directory")
        if not isinstance(wd, str) or not wd.strip():
            return None
        try:
            return os.path.abspath(os.path.expanduser(wd.strip()))
        except Exception:
            return wd.strip()

    def _build_invocation(
        self,
        subcommand: str,
        arguments: Dict[str, Any],
        *,
        exit_code: Optional[int] = None,
    ) -> Tuple[List[str], Optional[str]]:
        entry = str(Path(self.bash_entry).expanduser().resolve())
        base: List[str] = [self.bash_command, entry, subcommand]
        stdin_data: Optional[str] = None

        if subcommand == "error":
            base.append(str(int(exit_code) if isinstance(exit_code, int) else 1))

        mode = self.bash_args_mode
        if mode == "json":
            base.append("--args-json")
            stdin_data = json.dumps(
                arguments if isinstance(arguments, dict) else {}, ensure_ascii=False
            )
            return base, stdin_data

        if mode == "positional":
            argv, err = self._positional_argv(arguments)
            if err is not None:
                raise ValueError(err)
            return base + argv, stdin_data

        argv, err = self._flags_argv(arguments)
        if err is not None:
            raise ValueError(err)
        return base + argv, stdin_data

    def _flags_argv(self, arguments: Dict[str, Any]) -> Tuple[List[str], Optional[str]]:
        if not isinstance(arguments, dict):
            return [], "arguments must be an object"

        argv: List[str] = []
        for key, value in arguments.items():
            if not isinstance(key, str) or not key.strip():
                continue
            name = key.strip()
            if value is None:
                continue
            if isinstance(value, bool):
                argv.append(f"--{name}" if value else f"--no-{name}")
                continue
            if not isinstance(value, _SCALAR_TYPES):
                return [], f"unsupported value type for {name}: {type(value).__name__}"
            argv.extend([f"--{name}", _to_cli_scalar(value)])
        return argv, None

    def _positional_argv(self, arguments: Dict[str, Any]) -> Tuple[List[str], Optional[str]]:
        if not isinstance(arguments, dict):
            return [], "arguments must be an object"

        entries = self.bash_positional or []
        if not entries:
            return [], "positional mapping missing"

        values: List[str] = []
        present: List[bool] = []

        for entry in entries:
            if not isinstance(entry, dict):
                return [], "invalid positional mapping"
            name = entry.get("name")
            if not isinstance(name, str) or not name.strip():
                return [], "invalid positional mapping"
            key = name.strip()

            required_val = entry.get("required")
            if isinstance(required_val, bool):
                required = required_val
            else:
                required = "default" not in entry

            if key in arguments and arguments[key] is not None:
                val = arguments[key]
                if not isinstance(val, _SCALAR_TYPES):
                    return [], f"unsupported value type for {key}: {type(val).__name__}"
                values.append(_to_cli_scalar(val))
                present.append(True)
                continue

            if "default" in entry:
                default = entry.get("default")
                if default is None:
                    values.append("")
                elif isinstance(default, _SCALAR_TYPES):
                    values.append(_to_cli_scalar(default))
                else:
                    return [], f"unsupported default type for {key}: {type(default).__name__}"
                present.append(False)
                continue

            if required:
                return [], f"missing required argument: {key}"

            values.append("")
            present.append(False)

        # Omit trailing defaulted args.
        while values and not present[-1]:
            values.pop()
            present.pop()
        return values, None

    def _execute_run_tool(self, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        if not shutil.which(self.bash_command):
            return {
                "success": False,
                "error": f"Missing required executable: {self.bash_command}",
                "exit_code": 127,
                "stdout": "",
                "stderr": "",
                "tool_name": self.name,
                "arguments": arguments,
            }

        try:
            cmd, stdin_data = self._build_invocation("run", arguments)
        except ValueError as exc:
            return {
                "success": False,
                "error": str(exc),
                "exit_code": 2,
                "stdout": "",
                "stderr": "",
                "tool_name": self.name,
                "arguments": arguments,
            }

        cwd = self._resolve_cwd(state)
        timeout_seconds = float(self.bash_timeout_seconds)

        try:
            cp = subprocess.run(
                cmd,
                input=stdin_data,
                cwd=cwd,
                capture_output=True,
                text=True,
                timeout=timeout_seconds,
            )
            exit_code = int(cp.returncode)
            stdout_text = cp.stdout or ""
            stderr_text = cp.stderr or ""
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            exit_code = 124
            stdout_text = exc.stdout or ""
            stderr_text = exc.stderr or ""
            timed_out = True
        except Exception as exc:
            return {
                "success": False,
                "error": f"Failed to start tool: {exc}",
                "exit_code": 1,
                "stdout": "",
                "stderr": "",
                "tool_name": self.name,
                "arguments": arguments,
            }

        success = not timed_out and exit_code == 0
        result: Dict[str, Any] = {
            "success": bool(success),
            "exit_code": exit_code,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "timed_out": timed_out,
            "timeout_seconds": timeout_seconds,
            "tool_name": self.name,
            "arguments": arguments,
        }
        if not success:
            result["error"] = "timeout" if timed_out else "exit_code_nonzero"
            result["detail"] = (
                f"Tool timed out after {timeout_seconds} seconds"
                if timed_out
                else f"Tool exited with code {exit_code}"
            )

        return result

    def _stream_run_tool(
        self, arguments: Dict[str, Any], state: Dict[str, Any]
    ) -> Iterator[Dict[str, Any]]:
        if not shutil.which(self.bash_command):
            yield {
                "success": False,
                "error": f"Missing required executable: {self.bash_command}",
                "exit_code": 127,
                "stdout": "",
                "stderr": "",
                "tool_name": self.name,
                "arguments": arguments,
            }
            return

        try:
            cmd, stdin_data = self._build_invocation("run", arguments)
        except ValueError as exc:
            yield {
                "success": False,
                "error": str(exc),
                "exit_code": 2,
                "stdout": "",
                "stderr": "",
                "tool_name": self.name,
                "arguments": arguments,
            }
            return

        cwd = self._resolve_cwd(state)
        timeout_seconds = float(self.bash_timeout_seconds)
        stream_stderr = bool(self.bash_stream_stderr)

        try:
            proc = subprocess.Popen(
                cmd,
                cwd=cwd,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
            )
        except Exception as exc:
            yield {
                "success": False,
                "error": f"Failed to start tool: {exc}",
                "exit_code": 1,
                "stdout": "",
                "stderr": "",
                "tool_name": self.name,
                "arguments": arguments,
            }
            return

        if stdin_data is not None:
            try:
                assert proc.stdin is not None
                proc.stdin.write(stdin_data)
                proc.stdin.flush()
            except Exception:
                pass
            finally:
                try:
                    if proc.stdin is not None:
                        proc.stdin.close()
                except Exception:
                    pass

        stdout_chunks: List[str] = []
        stderr_chunks: List[str] = []
        timed_out = False

        stdout_queue: "queue.Queue[str]" = queue.Queue()
        stderr_queue: "queue.Queue[str]" = queue.Queue()

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

        def _stderr_reader() -> None:
            try:
                if proc.stderr is None:
                    return
                for line in proc.stderr:
                    if not line:
                        break
                    stderr_queue.put(line)
            finally:
                try:
                    if proc.stderr is not None and not proc.stderr.closed:
                        proc.stderr.close()
                except Exception:
                    pass

        out_thread = threading.Thread(target=_stdout_reader, daemon=True)
        err_thread = threading.Thread(target=_stderr_reader, daemon=True)
        out_thread.start()
        err_thread.start()

        start_time = time.monotonic()
        try:
            while True:
                elapsed = time.monotonic() - start_time
                if timeout_seconds and elapsed >= timeout_seconds:
                    timed_out = True
                    try:
                        proc.kill()
                        proc.wait(timeout=1)
                    except Exception:
                        pass
                    break

                drained_any = False

                try:
                    line = stdout_queue.get(timeout=0.05)
                except queue.Empty:
                    line = None

                if isinstance(line, str):
                    drained_any = True
                    stdout_chunks.append(line)
                    if line:
                        yield {
                            "part": {
                                "type": "text",
                                "content": line,
                                "stream": "stdout",
                            }
                        }

                while True:
                    try:
                        err_line = stderr_queue.get_nowait()
                    except queue.Empty:
                        break
                    drained_any = True
                    stderr_chunks.append(err_line)
                    if stream_stderr and err_line:
                        yield {
                            "part": {
                                "type": "text",
                                "content": err_line,
                                "stream": "stderr",
                            }
                        }

                if proc.poll() is not None and stdout_queue.empty() and stderr_queue.empty():
                    break

                if not drained_any:
                    time.sleep(0.01)
        finally:
            try:
                out_thread.join(timeout=1)
            except Exception:
                pass
            try:
                err_thread.join(timeout=1)
            except Exception:
                pass

            while True:
                try:
                    line = stdout_queue.get_nowait()
                except queue.Empty:
                    break
                stdout_chunks.append(line)
                if line:
                    yield {"part": {"type": "text", "content": line, "stream": "stdout"}}

            while True:
                try:
                    err_line = stderr_queue.get_nowait()
                except queue.Empty:
                    break
                stderr_chunks.append(err_line)
                if stream_stderr and err_line:
                    yield {"part": {"type": "text", "content": err_line, "stream": "stderr"}}

        stdout_text = "".join(stdout_chunks)
        stderr_text = "".join(stderr_chunks)

        if timed_out:
            exit_code: int | None = 124
            success = False
            err = f"Tool timed out after {timeout_seconds} seconds"
        else:
            exit_code = proc.returncode
            success = isinstance(exit_code, int) and exit_code == 0
            err = "" if success else f"Tool exited with code {exit_code}"

        result: Dict[str, Any] = {
            "success": bool(success),
            "exit_code": exit_code,
            "stdout": stdout_text,
            "stderr": stderr_text,
            "timed_out": timed_out,
            "timeout_seconds": timeout_seconds,
            "tool_name": self.name,
            "arguments": arguments,
        }
        if not success:
            result["error"] = "timeout" if timed_out else "exit_code_nonzero"
            result["detail"] = err

        summary = self._stream_summary(result, stderr_streamed=stream_stderr)
        if summary:
            yield {"part": {"type": "summary", "content": summary}}

        yield result

    def _stream_summary(self, result: Mapping[str, Any], *, stderr_streamed: bool) -> str:
        success = bool(result.get("success"))
        exit_code = result.get("exit_code")
        stderr = str(result.get("stderr") or "")
        timed_out = bool(result.get("timed_out"))

        if success:
            if stderr.strip() and not stderr_streamed:
                return f"STDERR:\n{stderr.rstrip()}\n"
            return ""

        lines: List[str] = []
        if timed_out:
            timeout_seconds = result.get("timeout_seconds")
            lines.append(f"Timed out after {timeout_seconds} seconds.")
        elif isinstance(exit_code, int):
            lines.append(f"Exit code: {exit_code}.")
        else:
            lines.append("Exit code: unknown.")

        if stderr.strip() and not stderr_streamed:
            lines.append("STDERR:")
            lines.append(stderr.rstrip("\n"))

        return "\n".join(lines) + "\n"

    def _try_format_error_with_script(
        self, result: Dict[str, Any], state: Dict[str, Any]
    ) -> str | None:
        exit_code = result.get("exit_code")
        if not isinstance(exit_code, int):
            exit_code = 1

        args = result.get("arguments")
        arguments = args if isinstance(args, dict) else {}

        extra_env: Dict[str, str] = {}
        if bool(result.get("timed_out")):
            extra_env["AGENT_TOOL_TIMED_OUT"] = "1"
            timeout_val = result.get("timeout_seconds")
            if isinstance(timeout_val, (int, float)):
                extra_env["AGENT_TOOL_TIMEOUT_SECONDS"] = str(timeout_val)

        stdout, _stderr, code = self._call_subcommand(
            "error",
            arguments,
            state,
            timeout=float(self.bash_error_timeout_seconds),
            exit_code=int(exit_code),
            extra_env=extra_env,
        )
        if code != 0:
            return None
        formatted = (stdout or "").strip()
        return formatted or None

    def _format_success(self, result: Mapping[str, Any]) -> str:
        stdout = str(result.get("stdout") or "")
        stderr = str(result.get("stderr") or "")

        if stdout.strip() and not stderr.strip():
            return stdout.rstrip("\n")
        if not stdout.strip() and stderr.strip():
            return f"STDERR:\n{stderr.rstrip()}"
        if stdout.strip() and stderr.strip():
            return f"STDOUT:\n{stdout.rstrip()}\n\nSTDERR:\n{stderr.rstrip()}"
        return "OK"

    def _format_failure_fallback(self, result: Mapping[str, Any]) -> str:
        exit_code = result.get("exit_code")
        stdout = str(result.get("stdout") or "")
        stderr = str(result.get("stderr") or "")
        timed_out = bool(result.get("timed_out"))
        timeout_seconds = result.get("timeout_seconds")

        if timed_out:
            prefix = f"Error: tool timed out after {timeout_seconds} seconds"
        elif isinstance(exit_code, int):
            prefix = f"Error: tool exited with code {exit_code}"
        else:
            prefix = "Error: tool failed"

        parts: List[str] = [prefix]
        if stdout.strip():
            parts.append(f"STDOUT:\n{stdout.rstrip()}")
        if stderr.strip():
            parts.append(f"STDERR:\n{stderr.rstrip()}")
        return "\n\n".join(parts)


__all__ = ["BashToolPlugin"]
