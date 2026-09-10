from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Iterator
from urllib.parse import parse_qs, unquote, urlsplit

from agent_app.application_future import AgentApplication
from agent_app.application_notifications import InMemoryApplicationNotificationStore
from agent_app.plugin_sources.dotted import DottedClassSource
from agent_core.types import ProviderPlugin, Session, ToolPlugin


READ_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "Read",
        "description": (
            "Read a UTF-8 text file inside the configured workspace. "
            "Use workspace-relative paths only."
        ),
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Workspace-relative path to read",
                },
                "offset": {
                    "type": "integer",
                    "minimum": 0,
                    "description": "Optional zero-based starting line",
                },
                "limit": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 2000,
                    "description": "Optional maximum number of lines",
                },
            },
            "required": ["file_path"],
        },
    },
}

WRITE_SCHEMA: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "Write",
        "description": (
            "Create or replace a UTF-8 text file inside the configured workspace. "
            "Use workspace-relative paths only."
        ),
        "parameters": {
            "type": "object",
            "additionalProperties": False,
            "properties": {
                "file_path": {
                    "type": "string",
                    "description": "Workspace-relative path to write",
                },
                "content": {
                    "type": "string",
                    "description": "Complete text content",
                },
            },
            "required": ["file_path", "content"],
        },
    },
}

MAX_READ_BYTES = 256 * 1024


def _workspace_root(config: dict[str, Any]) -> Path:
    raw_root = config.get("working_directory")
    if not isinstance(raw_root, str) or not raw_root.strip():
        raise ValueError("working_directory is required")
    root = Path(raw_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    return root


def _workspace_path(root: Path, raw_path: Any) -> tuple[Path, str]:
    if not isinstance(raw_path, str) or not raw_path.strip():
        raise ValueError("file_path must be a non-empty string")
    logical_path = raw_path.strip()
    untrusted = Path(logical_path)
    if untrusted.is_absolute():
        raise ValueError(
            "Absolute paths are not allowed. Remove the leading slash and use "
            "a workspace-relative path such as input.txt."
        )
    resolved = (root / untrusted).resolve()
    try:
        relative = resolved.relative_to(root)
    except ValueError as error:
        raise ValueError("Path escapes the configured workspace") from error
    return resolved, relative.as_posix()


class WorkspaceReadTool(ToolPlugin):
    name = "workspace_read"
    version = "0.1.0"

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {"workspace_root": _workspace_root(config)}

    def get_tool_schemas(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [READ_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> bool | None:
        _ = payload, state
        return tool_name == "Read"

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> dict[str, Any]:
        if tool_name != "Read" or not isinstance(payload, dict):
            return {"success": False, "error": "Read input must be an object"}
        try:
            path, logical_path = _workspace_path(
                state["workspace_root"],
                payload.get("file_path"),
            )
            if not path.is_file():
                raise ValueError(f"File does not exist: {logical_path}")
            if path.stat().st_size > MAX_READ_BYTES:
                raise ValueError("File is larger than the 256 KB read limit")
            text = path.read_text(encoding="utf-8")
            lines = text.splitlines()
            offset = payload.get("offset")
            offset = offset if isinstance(offset, int) and offset >= 0 else 0
            limit = payload.get("limit")
            limit = limit if isinstance(limit, int) and limit > 0 else 2000
            selected = lines[offset : offset + min(limit, 2000)]
            numbered = "\n".join(
                f"{offset + index + 1}\t{line}" for index, line in enumerate(selected)
            )
            return {
                "success": True,
                "result": numbered,
                "path": logical_path,
            }
        except (OSError, UnicodeError, ValueError) as error:
            return {"success": False, "error": str(error)}

    def format_tool_result(
        self,
        result: dict[str, Any],
        state: dict[str, Any],
    ) -> str:
        _ = state
        if result.get("success"):
            return str(result.get("result") or "")
        return f"Error: {result.get('error')}"

    def format_tool_call_preview(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> str:
        _ = tool_name, state
        return (
            f"Read {payload.get('file_path')}"
            if isinstance(payload, dict)
            else "Read workspace file"
        )

    def to_display_format(
        self,
        text: str,
        result: dict[str, Any],
        state: dict[str, Any],
    ) -> dict[str, Any]:
        _ = state
        path = str(result.get("path") or "file")
        return {
            "type": "text",
            "content": text,
            "single_line": f"Read: {path}",
        }


class WorkspaceWriteTool(ToolPlugin):
    name = "workspace_write"
    version = "0.1.0"

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {"workspace_root": _workspace_root(config)}

    def get_tool_schemas(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [WRITE_SCHEMA]

    def can_handle_tool_call(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> bool | None:
        _ = payload, state
        return tool_name == "Write"

    def execute_tool(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> dict[str, Any]:
        if tool_name != "Write" or not isinstance(payload, dict):
            return {"success": False, "error": "Write input must be an object"}
        content = payload.get("content")
        if not isinstance(content, str):
            return {"success": False, "error": "content must be a string"}
        try:
            path, logical_path = _workspace_path(
                state["workspace_root"],
                payload.get("file_path"),
            )
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
            return {
                "success": True,
                "result": f"Wrote {len(content.encode('utf-8'))} bytes to {logical_path}",
                "path": logical_path,
            }
        except (OSError, UnicodeError, ValueError) as error:
            return {"success": False, "error": str(error)}

    def format_tool_result(
        self,
        result: dict[str, Any],
        state: dict[str, Any],
    ) -> str:
        _ = state
        if result.get("success"):
            return str(result.get("result") or "")
        return f"Error: {result.get('error')}"

    def format_tool_call_preview(
        self,
        tool_name: str | None,
        payload: Any,
        state: dict[str, Any],
        **_: Any,
    ) -> str:
        _ = tool_name, state
        return (
            f"Write {payload.get('file_path')}"
            if isinstance(payload, dict)
            else "Write workspace file"
        )

    def to_display_format(
        self,
        text: str,
        result: dict[str, Any],
        state: dict[str, Any],
    ) -> dict[str, Any]:
        _ = state
        path = str(result.get("path") or "file")
        return {
            "type": "text",
            "content": text,
            "single_line": f"Write: {path}",
        }


class EmbeddedSmokeProvider(ProviderPlugin):
    name = "embedded_smoke_provider"
    version = "0.1.0"

    def init(self, config: dict[str, Any]) -> dict[str, Any]:
        return {"config": config}

    def call_api(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> tuple[
        list[dict[str, Any]],
        list[dict[str, Any]],
        list[dict[str, Any]],
        dict[str, Any],
    ]:
        final = {
            "role": "assistant",
            "content": "Embedded runtime smoke response",
            "metadata": {"development_smoke_provider": True},
        }
        return [], [final], [*native_messages, final], state

    def stream_api(
        self,
        native_messages: list[dict[str, Any]],
        state: dict[str, Any],
    ) -> Iterator[dict[str, Any]]:
        _ = native_messages, state
        yield {"content": "Embedded runtime smoke response"}


def _normalized_runtime_configuration(
    runtime_configuration: dict[str, Any] | None,
) -> dict[str, str]:
    source = runtime_configuration if isinstance(runtime_configuration, dict) else {}
    return {
        key: str(source.get(key) or "").strip()
        for key in ("api_key", "model", "proxy_url")
    }


def _config_payload(
    runtime_configuration: dict[str, Any] | None = None,
    workspace_root: Path | None = None,
) -> dict[str, Any]:
    configuration = _normalized_runtime_configuration(runtime_configuration)
    use_openai_compatible = all(configuration.values())
    provider_id = (
        "reference_openai_compatible"
        if use_openai_compatible
        else "embedded_smoke_provider"
    )
    provider_config: dict[str, Any] = {
        "provider": provider_id,
        "model": (
            configuration["model"] if use_openai_compatible else "embedded-smoke"
        ),
    }
    plugins = ["crystal_lattice_mobile_runtime.EmbeddedSmokeProvider"]
    if use_openai_compatible:
        if workspace_root is None:
            raise ValueError("workspace_root is required for the real provider")
        provider_config.update(
            {
                "api_key": configuration["api_key"],
                "base_url": configuration["proxy_url"],
                "timeout": 120,
                "working_directory": str(workspace_root),
                "allowed_paths": [str(workspace_root)],
            }
        )
        plugins = [
            (
                "reference_openai_compatible_provider.provider."
                "OpenAICompatibleProvider"
            ),
            (
                "reference_openai_compatible_provider.tools_extension."
                "OpenAICompatibleToolsExtension"
            ),
            "crystal_lattice_mobile_runtime.WorkspaceReadTool",
            "crystal_lattice_mobile_runtime.WorkspaceWriteTool",
        ]

    return {
        "plugin_policy": {
            "allow_bash_tools": False,
            "allow_dynamic_plugin_install": False,
            "allow_node_tools": False,
            "allow_remote": False,
        },
        "providers": {"embedded": provider_config},
        "plugins": plugins,
        "agents": {
            "local": {
                "provider": "embedded",
            }
        },
    }


class MobileRuntime:
    def __init__(
        self,
        runtime_root: str,
        runtime_configuration: dict[str, Any] | None = None,
    ) -> None:
        self.root = Path(runtime_root)
        self.runtime_configuration = _normalized_runtime_configuration(
            runtime_configuration
        )
        self.config_dir = self.root / "config"
        self.sessions_dir = self.root / "sessions"
        self.workspace_dir = self.root / "workspace"
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.workspace_dir.mkdir(parents=True, exist_ok=True)
        input_path = self.workspace_dir / "input.txt"
        if not input_path.exists():
            input_path.write_text(
                "alpha beta gamma\n",
                encoding="utf-8",
            )

        self.config_path = self.config_dir / "config.json"
        self.config_path.write_text(
            json.dumps(
                _config_payload(
                    self.runtime_configuration,
                    self.workspace_dir,
                ),
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        self.application = AgentApplication(
            self.config_path,
            self.sessions_dir,
            application_notification_store=InMemoryApplicationNotificationStore(),
            plugin_sources=[DottedClassSource()],
        )

    def create_session(
        self,
        *,
        agent_id: str | None = None,
        system_message: str | None = None,
    ) -> Session:
        selected_agent = agent_id or self.application.list_agents()[0]
        core, base_config, session = self.application.create_session(selected_agent)
        if system_message:
            session = core.add_message(
                session,
                "system",
                system_message,
                config=base_config,
            )
            session = self.application.save_session(session)
        stored = self.application.publish_event(
            {
                "type": "session_created",
                "session_id": session.session_id,
                "agent_id": selected_agent,
            }
        )
        self.application.record_checkpoint(
            session.session_id,
            stored.get("request_id"),
        )
        return session

    def append_message(self, session_id: str, message: dict[str, Any]) -> Session:
        loaded = self.application.load_session(session_id)
        if loaded is None:
            raise KeyError(f"Session {session_id!r} not found")
        core, base_config, session = loaded
        metadata = session.metadata if isinstance(session.metadata, dict) else {}
        overrides = metadata.get("overrides")
        effective_config = self.application.resolve_effective_config(
            base_config,
            session,
            overrides if isinstance(overrides, dict) else {},
        )
        next_session = core.add_message(
            session,
            str(message.get("role") or "user"),
            str(message.get("content") or ""),
            (
                message.get("metadata")
                if isinstance(message.get("metadata"), dict)
                else None
            ),
            effective_config,
            multipart_content=(
                message.get("multipartContent")
                if isinstance(message.get("multipartContent"), list)
                else None
            ),
            tool_result=(
                message.get("toolResult")
                if isinstance(message.get("toolResult"), dict)
                else None
            ),
        )
        persisted = self.application.save_session(next_session)
        index = len(persisted.messages) - 1
        stored_message = persisted.messages[index]
        event = self.application.publish_event(
            {
                "type": "message_appended",
                "session_id": session_id,
                "index": index,
                "message": stored_message.to_dict(),
                "role": stored_message.role,
                "content": stored_message.content,
                "metadata": stored_message.metadata or {},
            }
        )
        self.application.record_checkpoint(session_id, event.get("request_id"))
        return persisted


_runtime: MobileRuntime | None = None


def _get_runtime(
    runtime_root: str,
    runtime_configuration: dict[str, Any] | None = None,
) -> MobileRuntime:
    global _runtime
    resolved = str(Path(runtime_root).resolve())
    normalized_configuration = _normalized_runtime_configuration(runtime_configuration)
    if (
        _runtime is None
        or str(_runtime.root.resolve()) != resolved
        or _runtime.runtime_configuration != normalized_configuration
    ):
        if _runtime is not None:
            _runtime.application.close()
        _runtime = MobileRuntime(resolved, normalized_configuration)
    return _runtime


def shutdown_runtime() -> None:
    global _runtime
    if _runtime is None:
        return
    _runtime.application.close()
    _runtime = None


def run_application_smoke(runtime_root: str) -> dict[str, Any]:
    runtime = _get_runtime(runtime_root)
    session = runtime.create_session()
    stored = runtime.append_message(
        session.session_id,
        {
            "role": "user",
            "content": "Embedded application smoke",
        },
    )

    return {
        "status": "ready",
        "pythonVersion": ".".join(map(str, __import__("sys").version_info[:3])),
        "pythonPlatform": __import__("sys").platform,
        "agents": runtime.application.list_agents(),
        "sessionId": stored.session_id,
        "messageCount": len(stored.messages),
    }


def _response(status: int, data: Any) -> dict[str, Any]:
    return {"status": status, "data": data}


def _int_query(
    query: dict[str, list[str]],
    key: str,
) -> int | None:
    values = query.get(key)
    if not values:
        return None
    return int(values[-1])


def _session_parts(path_parts: list[str]) -> tuple[str, list[str]]:
    if len(path_parts) < 2:
        raise ValueError("Session path is missing a session identifier")
    return path_parts[1], path_parts[2:]


def _session_context(runtime: MobileRuntime, session_id: str):
    loaded = runtime.application.load_session(session_id)
    if loaded is None:
        raise KeyError(f"Session {session_id!r} not found")
    return loaded


def _session_overrides(session: Session) -> dict[str, Any]:
    metadata = session.metadata if isinstance(session.metadata, dict) else {}
    overrides = metadata.get("overrides")
    return overrides if isinstance(overrides, dict) else {}


def _update_session_metadata(
    runtime: MobileRuntime,
    session: Session,
    metadata: dict[str, Any],
) -> Session:
    updated = Session(
        session_id=session.session_id,
        messages=session.messages,
        metadata=metadata,
    )
    return runtime.application.save_session(updated)


def _handle_session_request(
    runtime: MobileRuntime,
    method: str,
    path_parts: list[str],
    query: dict[str, list[str]],
    body: dict[str, Any],
) -> dict[str, Any]:
    session_id, tail = _session_parts(path_parts)
    application = runtime.application

    if not tail and method == "GET":
        return _response(200, {"session": application.get_session_summary(session_id)})
    if not tail and method == "DELETE":
        application.delete_session(session_id)
        return _response(200, {"status": "ok"})

    if tail == ["summary"] and method == "GET":
        return _response(200, {"session": application.get_session_summary(session_id)})

    if tail == ["agent"]:
        loaded = _session_context(runtime, session_id)
        core, _base_config, session = loaded
        if method == "GET":
            agent_id = session.metadata.get("agent_id")
            return _response(200, {"agent_id": agent_id})
        if method == "PATCH":
            agent_id = str(body.get("agent_id") or "")
            next_core, next_base_config, next_session = application.update_agent(
                agent_id,
                session,
            )
            _ = core, next_core, next_base_config
            application.save_session(next_session)
            return _response(200, {"status": "ok"})

    if tail == ["messages"]:
        if method == "GET":
            session = application.load_session_record(session_id)
            if session is None:
                raise KeyError(f"Session {session_id!r} not found")
            message_count = len(session.messages)
            start = _int_query(query, "start")
            end = _int_query(query, "end")
            start_index, end_index, _step = slice(start, end).indices(message_count)
            messages = [
                {"index": index, "message": session.messages[index].to_dict()}
                for index in range(start_index, end_index)
            ]
            return _response(
                200,
                {
                    "messages": messages,
                    "cursor_event_id": application.get_session_cursor_event_id(
                        session_id
                    ),
                    "active_request_id": application.get_active_session_request_id(
                        session_id
                    ),
                    "readonly": False,
                    "snapshot_id": None,
                },
            )
        if method == "POST":
            session = runtime.append_message(session_id, body)
            return _response(200, {"session": session.to_dict()})
        if method == "DELETE":
            core, base_config, session = _session_context(runtime, session_id)
            indices = body.get("indices")
            remove_indices: list[int]
            if isinstance(indices, list):
                remove_indices = [value for value in indices if isinstance(value, int)]
            else:
                range_value = body.get("range")
                if not isinstance(range_value, dict):
                    raise ValueError("Message deletion requires indices or range")
                start = range_value.get("start")
                end = range_value.get("end")
                start_index, end_index, _step = slice(start, end).indices(
                    len(session.messages)
                )
                remove_indices = list(range(start_index, end_index))
            effective_config = application.resolve_effective_config(
                base_config,
                session,
                _session_overrides(session),
            )
            next_session = core.slice_session(
                session,
                effective_config,
                remove_indices=remove_indices,
            )
            application.save_session(next_session)
            application.publish_event(
                {
                    "type": "messages_deleted",
                    "session_id": session_id,
                    "indices": remove_indices,
                }
            )
            return _response(
                200,
                {
                    "session": next_session.to_dict(),
                    "deleted_indices": remove_indices,
                },
            )

    if len(tail) == 2 and tail[0] == "messages" and method == "PATCH":
        index = int(tail[1])
        core, base_config, session = _session_context(runtime, session_id)
        effective_config = application.resolve_effective_config(
            base_config,
            session,
            _session_overrides(session),
        )
        next_session = core.modify_message(
            session,
            index,
            str(body.get("content") or ""),
            effective_config,
        )
        application.save_session(next_session)
        application.publish_event(
            {
                "type": "message_modified",
                "session_id": session_id,
                "index": index,
                "message": next_session.messages[index].to_dict(),
            }
        )
        return _response(200, {"status": "ok"})

    if tail == ["send"] and method == "POST":
        started = application.start_session_request(
            session_id,
            (
                body.get("config_overrides")
                if isinstance(body.get("config_overrides"), dict)
                else {}
            ),
            stream=False,
        )
        return _response(
            200,
            {
                "status": started.status,
                "request_id": started.request_id,
            },
        )

    if tail == ["send_message"] and method == "POST":
        message = body.get("message")
        if not isinstance(message, dict):
            raise ValueError("send_message requires a message")
        started = application.start_session_request_with_message(
            session_id,
            role=str(message.get("role") or "user"),
            content=str(message.get("content") or ""),
            metadata=(
                message.get("metadata")
                if isinstance(message.get("metadata"), dict)
                else None
            ),
            multipart_content=(
                message.get("multipartContent")
                if isinstance(message.get("multipartContent"), list)
                else None
            ),
            overrides=(
                body.get("config_overrides")
                if isinstance(body.get("config_overrides"), dict)
                else {}
            ),
            stream=False,
        )
        return _response(
            200,
            {
                "status": started.status,
                "request_id": started.request_id,
                "session_id": session_id,
            },
        )

    if tail == ["plugins"] and method == "GET":
        _core, _base_config, session = _session_context(runtime, session_id)
        agent_id = str(session.metadata.get("agent_id") or "local")
        plugins = application.list_plugins_for_agent(agent_id)
        return _response(200, {"plugins": plugins})
    if tail == ["plugins"] and method in {"PUT", "DELETE"}:
        return _response(200, {"status": "ok"})

    if tail == ["ui-schema"] and method == "GET":
        core, base_config, session = _session_context(runtime, session_id)
        effective_config = application.resolve_effective_config(
            base_config,
            session,
            _session_overrides(session),
        )
        return _response(
            200,
            {"elements": core.get_ui_schema(config=effective_config) or []},
        )

    if tail == ["application", "ui-schema"] and method == "GET":
        return _response(200, {"elements": []})
    if tail == ["config", "schema"] and method == "GET":
        core, _base_config, _session = _session_context(runtime, session_id)
        return _response(200, {"schema": core.get_config_schema() or []})
    if tail == ["config", "base"] and method == "GET":
        _core, base_config, _session = _session_context(runtime, session_id)
        return _response(200, {"config": base_config})

    if tail == ["overrides"]:
        _core, _base_config, session = _session_context(runtime, session_id)
        if method == "GET":
            return _response(200, {"overrides": _session_overrides(session)})
        if method == "PATCH":
            values = body.get("values")
            if not isinstance(values, dict):
                raise ValueError("Override values must be an object")
            metadata = dict(session.metadata)
            metadata["overrides"] = {**_session_overrides(session), **values}
            _update_session_metadata(runtime, session, metadata)
            return _response(200, {"status": "ok"})

    if len(tail) == 2 and tail[0] == "overrides" and method == "DELETE":
        _core, _base_config, session = _session_context(runtime, session_id)
        metadata = dict(session.metadata)
        overrides = dict(_session_overrides(session))
        overrides.pop(tail[1], None)
        metadata["overrides"] = overrides
        _update_session_metadata(runtime, session, metadata)
        return _response(200, {"status": "ok"})

    if tail == ["snapshots"] and method == "GET":
        return _response(200, {"snapshots": []})
    if tail == ["snapshots", "selected"] and method == "GET":
        return _response(200, {"snapshot_id": None})
    if tail == ["notifications"] and method == "GET":
        return _response(
            200,
            {
                "notifications": application.list_session_notifications(
                    session_id,
                    include_terminal=True,
                )
            },
        )

    raise ValueError(f"Unsupported embedded session route: {method} {'/'.join(tail)}")


def _handle_request(
    runtime: MobileRuntime,
    request: dict[str, Any],
) -> dict[str, Any]:
    method = str(request.get("method") or "GET").upper()
    parsed = urlsplit(str(request.get("path") or "/"))
    path_parts = [unquote(part) for part in parsed.path.split("/") if part]
    query = parse_qs(parsed.query)
    body = request.get("body")
    body = body if isinstance(body, dict) else {}
    application = runtime.application

    if path_parts == ["api", "hello"] and method == "GET":
        output_path = runtime.workspace_dir / "output.txt"
        return _response(
            200,
            {
                "message": "Embedded Python runtime is ready",
                "provider_mode": (
                    "openai-compatible"
                    if all(runtime.runtime_configuration.values())
                    else "smoke"
                ),
                "workspace_output": (
                    output_path.read_text(encoding="utf-8")
                    if output_path.is_file()
                    else None
                ),
            },
        )

    if path_parts == ["api", "data"] and method in {"GET", "PUT"}:
        return _response(
            200,
            {
                "message": "Embedded Python runtime",
                "echo": body if method == "PUT" else None,
            },
        )

    if path_parts == ["embedded", "runtime", "status"] and method == "GET":
        return _response(
            200,
            {
                "provider_mode": (
                    "openai-compatible"
                    if all(runtime.runtime_configuration.values())
                    else "smoke"
                ),
                "has_api_key": bool(runtime.runtime_configuration["api_key"]),
                "model": runtime.runtime_configuration["model"],
                "proxy_url": runtime.runtime_configuration["proxy_url"],
            },
        )

    if path_parts == ["embedded", "runtime", "validate"] and method == "POST":
        if not all(runtime.runtime_configuration.values()):
            return _response(400, {"detail": "Runtime configuration is incomplete"})
        from reference_openai_compatible_provider.provider import (
            OpenAICompatibleProvider,
        )

        models = OpenAICompatibleProvider().get_models(
            {
                "api_key": runtime.runtime_configuration["api_key"],
                "base_url": runtime.runtime_configuration["proxy_url"],
                "model": runtime.runtime_configuration["model"],
                "timeout": 15,
            }
        )
        model_ids = {
            model.get("id")
            for model in models
            if isinstance(model, dict) and isinstance(model.get("id"), str)
        }
        configured_model = runtime.runtime_configuration["model"]
        if configured_model not in model_ids:
            return _response(
                401,
                {
                    "detail": (
                        "The proxy credentials were rejected or the configured "
                        "model is unavailable"
                    )
                },
            )
        return _response(
            200,
            {
                "status": "ok",
                "model": configured_model,
            },
        )

    if path_parts == ["embedded", "workspace", "reset"] and method == "POST":
        input_content = body.get("input")
        if not isinstance(input_content, str):
            input_content = "alpha beta gamma\n"
        (runtime.workspace_dir / "input.txt").write_text(
            input_content,
            encoding="utf-8",
        )
        (runtime.workspace_dir / "output.txt").unlink(missing_ok=True)
        return _response(200, {"status": "ok"})

    if path_parts == ["embedded", "workspace", "output"] and method == "GET":
        output_path = runtime.workspace_dir / "output.txt"
        return _response(
            200,
            {
                "exists": output_path.is_file(),
                "content": (
                    output_path.read_text(encoding="utf-8")
                    if output_path.is_file()
                    else ""
                ),
                "provider_mode": (
                    "openai-compatible"
                    if all(runtime.runtime_configuration.values())
                    else "smoke"
                ),
            },
        )

    if path_parts == ["agents"] and method == "GET":
        return _response(200, {"agents": application.list_agents()})

    if path_parts == ["sessions"] and method == "POST":
        session = runtime.create_session(
            agent_id=(
                str(body.get("agent_id"))
                if isinstance(body.get("agent_id"), str)
                else None
            ),
            system_message=(
                str(body.get("system_message"))
                if isinstance(body.get("system_message"), str)
                else None
            ),
        )
        return _response(
            200,
            {
                "session": session.to_dict(),
                "errors": application.get_config_errors(),
            },
        )

    if path_parts == ["sessions"] and method == "GET":
        limit = _int_query(query, "limit")
        return _response(
            200,
            {"sessions": application.list_session_summaries(limit=limit)},
        )

    if path_parts == ["sessions", "request-statuses"] and method == "POST":
        session_ids = body.get("session_ids")
        if not isinstance(session_ids, list):
            session_ids = []
        return _response(
            200,
            application.get_session_request_statuses(
                [value for value in session_ids if isinstance(value, str)]
            ),
        )

    if path_parts and path_parts[0] == "sessions":
        return _handle_session_request(
            runtime,
            method,
            path_parts,
            query,
            body,
        )

    if path_parts == ["events"] and method == "GET":
        result = application.get_event_store().list(
            since_id=(query.get("since_id") or [None])[-1],
            request_id=(query.get("request_id") or [None])[-1],
            session_id=(query.get("session_id") or [None])[-1],
            limit=_int_query(query, "limit") or 100,
        )
        return _response(200, result)

    if len(path_parts) == 3 and path_parts[:1] == ["requests"]:
        if path_parts[2] == "cancel" and method == "POST":
            application.cancel_request(path_parts[1])
            return _response(200, {"status": "ok"})

    if path_parts == ["application", "actions"] and method == "GET":
        return _response(200, {"actions": []})
    if path_parts == ["application", "ui-schema"] and method == "GET":
        return _response(200, {"elements": []})
    if path_parts == ["application", "notifications"] and method == "GET":
        return _response(
            200,
            {
                "notifications": application.list_application_notifications(
                    include_terminal=True,
                )
            },
        )
    if path_parts == ["server", "settings"] and method == "GET":
        return _response(200, {"settings": {}})
    if path_parts == ["server", "settings", "ui-schema"] and method == "GET":
        return _response(200, {"elements": []})

    raise ValueError(f"Unsupported embedded runtime route: {method} {parsed.path}")


def execute_json(command_json: str, runtime_root: str) -> str:
    try:
        request = json.loads(command_json)
        if not isinstance(request, dict):
            raise ValueError("Embedded runtime request must be an object")
        runtime_configuration = request.get("runtimeConfiguration")
        response = _handle_request(
            _get_runtime(
                runtime_root,
                (
                    runtime_configuration
                    if isinstance(runtime_configuration, dict)
                    else None
                ),
            ),
            request,
        )
    except KeyError as error:
        response = _response(404, {"detail": str(error)})
    except ValueError as error:
        response = _response(400, {"detail": str(error)})
    except Exception as error:
        response = _response(
            500,
            {"detail": f"{type(error).__name__}: {error}"},
        )
    return json.dumps(response, separators=(",", ":"))
