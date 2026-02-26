from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping, Optional
import os
import selectors
import subprocess
import time
import uuid

from agent_core.utils import get_logger


logger = get_logger("NodeToolPlugin")


def _default_node_host_script() -> Path:
    """Return the default tool host runner path (repo checkout)."""

    # core/python/agent_core/tool_hosts/node_tool_plugin.py -> repo root
    root = Path(__file__).resolve().parents[4]
    return root / "packages" / "tool-host-node" / "host.mjs"


class _RpcError(Exception):
    def __init__(self, *, detail: str, stderr: str = "") -> None:
        super().__init__(detail)
        self.detail = detail
        self.stderr = stderr


class NodeToolPlugin:
    """ToolPlugin proxy delegating to a Node.js tool host via NDJSON.

    Subclasses are expected to set:
    - ``name`` / ``version`` (tool plugin identity)
    - ``node_entry`` (absolute path to the JS module)
    - ``node_workdir`` (plugin root directory)
    - optional ``node_export`` (named export selection)
    """

    name = "node_tool"
    version = "unknown"

    node_entry: str = ""
    node_workdir: str = ""
    node_export: Optional[str] = None

    node_timeout_seconds: float = 60.0
    node_command: str = "node"
    node_host_script: Optional[str] = None

    protocol_version: int = 1

    # ---------------------------------------------------------------------
    # BasePlugin optional hooks
    # ---------------------------------------------------------------------

    def get_config_schema(self) -> Dict[str, Any]:
        out = self._rpc_call("get_config_schema", {})
        return out if isinstance(out, dict) else {}

    def get_ui_elements(self) -> List[Dict[str, Any]]:
        out = self._rpc_call("get_ui_elements", {})
        if isinstance(out, list):
            return [i for i in out if isinstance(i, dict)]
        return []

    # ---------------------------------------------------------------------
    # ToolPlugin lifecycle + capability methods
    # ---------------------------------------------------------------------

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        out = self._rpc_call("init", {"config": config})
        return out if isinstance(out, dict) else {"config": config}

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        out = self._rpc_call("get_tags", {"config": config, "models": models})
        if isinstance(out, list):
            return [str(t) for t in out]
        return []

    def required_tags(self) -> List[str]:
        out = self._rpc_call("required_tags", {})
        if isinstance(out, list):
            return [str(t) for t in out]
        return []

    def get_tool_schemas(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        out, new_state = self._rpc_call_with_state("get_tool_schemas", {"state": state})
        self._update_state_in_place(state, new_state)
        if isinstance(out, list):
            return [s for s in out if isinstance(s, dict)]
        return []

    # ---------------------------------------------------------------------
    # ToolPlugin execution + formatting
    # ---------------------------------------------------------------------

    def execute_tool(self, tool_name: str, arguments: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        out, new_state = self._rpc_call_with_state(
            "execute_tool",
            {
                "tool_name": tool_name,
                "arguments": arguments,
                "state": state,
            },
        )
        self._update_state_in_place(state, new_state)
        if isinstance(out, dict) and "success" in out:
            return out
        if isinstance(out, dict):
            return {"success": False, "error": "invalid tool result", "detail": out}
        return {"success": False, "error": "invalid tool result"}

    def stream_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        try:
            yield from self._rpc_stream_execute_tool(tool_name, arguments, state)
        except _RpcError as exc:
            yield {"success": False, "error": exc.detail, "stderr": exc.stderr}
        except Exception as exc:
            yield {"success": False, "error": f"node tool host error: {exc}"}

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> str:
        out, new_state = self._rpc_call_with_state(
            "format_tool_result", {"result": result, "state": state}
        )
        self._update_state_in_place(state, new_state)
        if isinstance(out, str) and out:
            return out
        if result.get("success"):
            return f"Result: {result.get('result')}"
        return f"Error: {result.get('error')}"

    def format_tool_call_preview(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> str:
        out, new_state = self._rpc_call_with_state(
            "format_tool_call_preview",
            {"tool_name": tool_name, "arguments": arguments, "state": state},
        )
        self._update_state_in_place(state, new_state)
        return str(out) if out else ""

    def to_display_format(self, text: str, result: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        out, new_state = self._rpc_call_with_state(
            "to_display_format",
            {"text": text, "result": result, "state": state},
        )
        self._update_state_in_place(state, new_state)
        return out if isinstance(out, dict) else {"type": "text", "content": str(text)}

    # ---------------------------------------------------------------------
    # Internal helpers
    # ---------------------------------------------------------------------

    def _host_script_path(self) -> Path:
        env_override = os.environ.get("AGENT_NODE_TOOL_HOST")
        if env_override:
            return Path(env_override).expanduser().resolve()
        if isinstance(self.node_host_script, str) and self.node_host_script.strip():
            return Path(self.node_host_script).expanduser().resolve()
        return _default_node_host_script().resolve()

    def _base_command(self) -> List[str]:
        host = self._host_script_path()
        return [self.node_command, str(host), "--entry", str(self.node_entry)] + (
            ["--export", str(self.node_export)] if isinstance(self.node_export, str) and self.node_export else []
        )

    def _timeout_seconds(self, params: Mapping[str, Any]) -> float:
        # Allow tools to override timeout via config (common pattern).
        cfg = params.get("config")
        if isinstance(cfg, dict):
            if isinstance(cfg.get("node_timeout_seconds"), (int, float)):
                return float(cfg["node_timeout_seconds"])
            if isinstance(cfg.get("timeout_seconds"), (int, float)):
                return float(cfg["timeout_seconds"])
        return float(self.node_timeout_seconds)

    def _rpc_call(self, method: str, params: Dict[str, Any]) -> Any:
        value, _state = self._rpc_call_with_state(method, params)
        return value

    def _rpc_call_with_state(self, method: str, params: Dict[str, Any]) -> tuple[Any, Optional[Dict[str, Any]]]:
        response = self._run_single_rpc(method, params)
        value = response.get("value")
        new_state = response.get("state")
        return value, new_state if isinstance(new_state, dict) else None

    def _run_single_rpc(self, method: str, params: Dict[str, Any]) -> Dict[str, Any]:
        request_id = str(uuid.uuid4())
        msg = {
            "v": self.protocol_version,
            "id": request_id,
            "method": method,
            "params": params,
        }

        cmd = self._base_command()
        cwd = self.node_workdir or None
        timeout = self._timeout_seconds(params)

        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        stderr_lines: List[str] = []
        try:
            assert proc.stdin is not None
            proc.stdin.write(json.dumps(msg) + "\n")
            proc.stdin.flush()
            proc.stdin.close()

            response = self._read_until_response(proc, request_id, timeout, stderr_lines)
            return response
        finally:
            try:
                if proc.poll() is None:
                    proc.kill()
            except Exception:
                pass

    def _rpc_stream_execute_tool(
        self,
        tool_name: str,
        arguments: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Iterator[Dict[str, Any]]:
        request_id = str(uuid.uuid4())
        params = {
            "tool_name": tool_name,
            "arguments": arguments,
            "state": state,
        }
        msg = {
            "v": self.protocol_version,
            "id": request_id,
            "method": "execute_tool",
            "params": params,
        }

        cmd = self._base_command()
        cwd = self.node_workdir or None
        timeout = self._timeout_seconds({"config": state.get("config") if isinstance(state, dict) else {}})

        proc = subprocess.Popen(
            cmd,
            cwd=cwd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1,
        )

        stderr_lines: List[str] = []
        final_value: Optional[Dict[str, Any]] = None
        new_state: Optional[Dict[str, Any]] = None

        try:
            assert proc.stdin is not None
            proc.stdin.write(json.dumps(msg) + "\n")
            proc.stdin.flush()
            proc.stdin.close()

            sel = selectors.DefaultSelector()
            assert proc.stdout is not None
            assert proc.stderr is not None
            sel.register(proc.stdout, selectors.EVENT_READ)
            sel.register(proc.stderr, selectors.EVENT_READ)

            deadline = time.monotonic() + timeout
            stdout_open = True
            stderr_open = True

            while stdout_open or stderr_open:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    raise _RpcError(detail="timeout", stderr="".join(stderr_lines))

                for key, _mask in sel.select(timeout=min(0.25, remaining)):
                    if key.fileobj is proc.stderr:
                        line = proc.stderr.readline()
                        if not line:
                            stderr_open = False
                            try:
                                sel.unregister(proc.stderr)
                            except Exception:
                                pass
                        else:
                            stderr_lines.append(line)
                        continue

                    if key.fileobj is proc.stdout:
                        line = proc.stdout.readline()
                        if not line:
                            stdout_open = False
                            try:
                                sel.unregister(proc.stdout)
                            except Exception:
                                pass
                            continue

                        parsed = self._parse_host_line(line, stderr_lines)
                        if parsed is None:
                            continue

                        if parsed.get("id") != request_id:
                            continue

                        if "event" in parsed:
                            ev = parsed.get("event")
                            if isinstance(ev, dict) and ev.get("type") == "part":
                                payload = ev.get("payload")
                                yield {"part": payload}
                            continue

                        if parsed.get("ok") is False:
                            err = parsed.get("error") or {}
                            detail = err.get("detail") if isinstance(err, dict) else None
                            raise _RpcError(detail=str(detail or "node tool error"), stderr="".join(stderr_lines))

                        if parsed.get("ok") is True:
                            result = parsed.get("result") or {}
                            if isinstance(result, dict):
                                value = result.get("value")
                                if isinstance(value, dict):
                                    final_value = value
                                if isinstance(result.get("state"), dict):
                                    new_state = result.get("state")
                            stdout_open = False
                            try:
                                sel.unregister(proc.stdout)
                            except Exception:
                                pass
                            continue

                if proc.poll() is not None and not stdout_open and not stderr_open:
                    break

            if final_value is None:
                raise _RpcError(detail="no result", stderr="".join(stderr_lines))

            self._update_state_in_place(state, new_state)
            yield final_value
        finally:
            try:
                if proc.poll() is None:
                    proc.kill()
            except Exception:
                pass

    def _read_until_response(
        self,
        proc: subprocess.Popen[str],
        request_id: str,
        timeout: float,
        stderr_lines: List[str],
    ) -> Dict[str, Any]:
        sel = selectors.DefaultSelector()
        assert proc.stdout is not None
        assert proc.stderr is not None
        sel.register(proc.stdout, selectors.EVENT_READ)
        sel.register(proc.stderr, selectors.EVENT_READ)

        deadline = time.monotonic() + timeout
        stdout_open = True
        stderr_open = True
        response: Optional[Dict[str, Any]] = None

        while stdout_open or stderr_open:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise _RpcError(detail="timeout", stderr="".join(stderr_lines))

            for key, _mask in sel.select(timeout=min(0.25, remaining)):
                if key.fileobj is proc.stderr:
                    line = proc.stderr.readline()
                    if not line:
                        stderr_open = False
                        try:
                            sel.unregister(proc.stderr)
                        except Exception:
                            pass
                    else:
                        stderr_lines.append(line)
                    continue

                if key.fileobj is proc.stdout:
                    line = proc.stdout.readline()
                    if not line:
                        stdout_open = False
                        try:
                            sel.unregister(proc.stdout)
                        except Exception:
                            pass
                        continue

                    parsed = self._parse_host_line(line, stderr_lines)
                    if parsed is None:
                        continue
                    if parsed.get("id") != request_id:
                        continue
                    if "event" in parsed:
                        continue
                    response = parsed
                    stdout_open = False
                    try:
                        sel.unregister(proc.stdout)
                    except Exception:
                        pass

            if response is not None:
                break
            if proc.poll() is not None and not stdout_open and not stderr_open:
                break

        if response is None:
            raise _RpcError(detail="no response", stderr="".join(stderr_lines))

        if response.get("ok") is not True:
            err = response.get("error") or {}
            detail = err.get("detail") if isinstance(err, dict) else None
            raise _RpcError(detail=str(detail or "node tool error"), stderr="".join(stderr_lines))

        result = response.get("result")
        if not isinstance(result, dict):
            return {"value": None}
        return result

    def _parse_host_line(self, line: str, stderr_lines: List[str]) -> Optional[Dict[str, Any]]:
        try:
            parsed = json.loads(line)
        except Exception:
            # Treat non-JSON stdout as a protocol violation.
            stderr_lines.append(f"[stdout] {line}")
            return None
        return parsed if isinstance(parsed, dict) else None

    def _update_state_in_place(self, state: Dict[str, Any], new_state: Optional[Dict[str, Any]]) -> None:
        if not isinstance(new_state, dict):
            return
        try:
            state.clear()
            state.update(new_state)
        except Exception:
            return


__all__ = ["NodeToolPlugin"]
