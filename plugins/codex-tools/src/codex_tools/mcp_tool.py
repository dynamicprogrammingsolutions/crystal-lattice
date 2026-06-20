from __future__ import annotations

import json
from dataclasses import asdict
from typing import Any, Dict, Iterable, List, Optional

from agent_core.tool_result_payloads import (
    FORMAT_OPENAI_RESPONSES,
    make_provider_native_tool_result,
)
from agent_core.types import ToolPlugin
from mcp_shared import (
    MCPDiscoveredTool,
    MCPRegistry,
    MCPRuntimeConfig,
    MCPRuntimeManager,
    MCPServerRuntimeSpec,
    MCPToolCallResult,
    apply_oauth_tokens_to_runtime_config,
    fingerprint_runtime_config,
)

from .mcp_names import qualify_codex_mcp_names


def _default_input_schema() -> Dict[str, Any]:
    return {"type": "object", "properties": {}, "additionalProperties": True}


def _coerce_input_schema(schema: Any) -> Dict[str, Any]:
    if not isinstance(schema, dict):
        return _default_input_schema()
    out = dict(schema)
    if not isinstance(out.get("type"), str):
        out["type"] = "object"
    if out.get("type") == "object" and not isinstance(out.get("properties"), dict):
        out["properties"] = {}
    return out


def _mask_file_params(schema: Dict[str, Any], meta: Dict[str, Any]) -> Dict[str, Any]:
    file_params = meta.get("openai/fileParams")
    if not isinstance(file_params, list) or not file_params:
        return schema
    out = dict(schema)
    properties = out.get("properties")
    if not isinstance(properties, dict):
        return out
    new_props = dict(properties)
    for raw_name in file_params:
        if not isinstance(raw_name, str) or not raw_name:
            continue
        existing = new_props.get(raw_name)
        if not isinstance(existing, dict):
            continue
        updated = dict(existing)
        existing_type = updated.get("type")
        if existing_type == "array":
            updated["items"] = {"type": "string"}
            updated["description"] = (
                "This parameter expects an absolute local file path. "
                "If you want to upload a file, provide the absolute path to that file here."
            )
        else:
            description = str(updated.get("description") or "").strip()
            suffix = (
                "This parameter expects an absolute local file path. "
                "If you want to upload a file, provide the absolute path to that file here."
            )
            updated["type"] = "string"
            updated["description"] = f"{description} {suffix}".strip()
        new_props[raw_name] = updated
    out["properties"] = new_props
    return out


def _sanitize_schema_for_codex(
    schema: Dict[str, Any],
    *,
    meta: Dict[str, Any],
) -> Dict[str, Any]:
    return _mask_file_params(_coerce_input_schema(schema), meta)


def _text_summary_from_content(content: Iterable[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for part in content:
        if part.get("type") == "text":
            text = part.get("text")
            if isinstance(text, str) and text:
                parts.append(text)
                continue
        if part.get("type") == "image":
            mime_type = part.get("mimeType") or "unknown"
            parts.append(f"[Image: {mime_type}]")
            continue
        if part.get("type") == "audio":
            mime_type = part.get("mimeType") or "unknown"
            parts.append(f"[Audio: {mime_type}]")
            continue
        if part.get("type") == "resource_link":
            parts.append(f"[Resource link: {part.get('uri') or ''}]")
            continue
        if part.get("type") == "resource":
            resource = part.get("resource")
            if isinstance(resource, dict):
                text = resource.get("text")
                if isinstance(text, str) and text:
                    parts.append(text)
                    continue
                mime_type = resource.get("mimeType") or "unknown"
                parts.append(f"[Embedded resource: {mime_type}]")
    return "\n".join(parts).strip()


def _responses_output_from_result(result: MCPToolCallResult) -> List[Dict[str, Any]]:
    output: List[Dict[str, Any]] = []
    for part in result.content:
        part_type = part.get("type")
        if part_type == "text":
            text = part.get("text")
            if isinstance(text, str) and text:
                output.append({"type": "input_text", "text": text})
            continue
        if part_type in {"image", "audio"}:
            mime_type = str(part.get("mimeType") or "application/octet-stream")
            data = part.get("data")
            if part_type == "image" and isinstance(data, str) and data:
                output.append(
                    {
                        "type": "input_text",
                        "text": f"[Tool provided image data: {mime_type}]",
                    }
                )
                output.append(
                    {
                        "type": "input_image",
                        "image_url": f"data:{mime_type};base64,{data}",
                    }
                )
            else:
                output.append(
                    {
                        "type": "input_text",
                        "text": f"[Tool provided {part_type} data: {mime_type}]",
                    }
                )
            continue
        if part_type == "resource":
            resource = part.get("resource")
            if not isinstance(resource, dict):
                continue
            text = resource.get("text")
            if isinstance(text, str) and text:
                output.append({"type": "input_text", "text": text})
                continue
            mime_type = str(resource.get("mimeType") or "application/octet-stream")
            blob = resource.get("blob")
            if mime_type.startswith("image/") and isinstance(blob, str) and blob:
                output.append(
                    {
                        "type": "input_text",
                        "text": f"[Tool provided embedded image resource: {mime_type}]",
                    }
                )
                output.append(
                    {
                        "type": "input_image",
                        "image_url": f"data:{mime_type};base64,{blob}",
                    }
                )
            else:
                output.append(
                    {
                        "type": "input_text",
                        "text": f"[Tool provided embedded resource: {mime_type}]",
                    }
                )
            continue
        if part_type == "resource_link":
            uri = str(part.get("uri") or "")
            output.append({"type": "input_text", "text": f"Resource Link: {uri}"})
    return output


class CodexMCPTool(ToolPlugin):
    name = "codex_mcp_tool"
    version = "0.1.0"

    runtime_store_key = "mcp_registry"

    def __init__(self) -> None:
        self._runtime_manager_factory = MCPRuntimeManager

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "mcp_enabled": {
                "type": "boolean",
                "default": True,
                "description": "Enable MCP-backed tools for this agent.",
            },
            "mcp_fail_on_startup_error": {
                "type": "boolean",
                "default": False,
                "description": "Fail tool preparation when an enabled MCP server cannot be started.",
            },
            "mcp_reuse_runtime": {
                "type": "boolean",
                "default": True,
                "description": "Reuse live MCP runtime connections across requests when possible.",
            },
            "mcp_servers": {
                "type": "object",
                "default": {},
                "description": "MCP server definitions keyed by server name.",
            },
        }

    def get_ui_elements(
        self,
        config: Dict[str, Any],
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = (tags, models)
        elements: List[Dict[str, Any]] = [
            {
                "type": "checkbox",
                "key": "mcp_enabled",
                "label": "Enable MCP tools",
                "description": "Enable tools discovered from configured MCP servers.",
            }
        ]
        servers = config.get("mcp_servers")
        if not isinstance(servers, dict):
            return elements
        for server_name in sorted(servers.keys()):
            elements.append(
                {
                    "type": "checkbox",
                    "key": self._server_enabled_override_key(server_name),
                    "config_path": f"mcp_servers.{server_name}.enabled",
                    "label": f"Enable MCP server: {server_name}",
                    "description": f"Expose tools from the {server_name} MCP server.",
                }
            )
        return elements

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    async def prepare_async(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        runtime_config = self._build_runtime_config(config)
        if not config.get("mcp_enabled", True):
            return {"runtime_key": None, "tools": []}
        if not runtime_config.servers:
            return {"runtime_key": None, "tools": []}

        store = self._runtime_store(context)
        runtime_config = apply_oauth_tokens_to_runtime_config(runtime_config, store)
        runtime_key = fingerprint_runtime_config(runtime_config)
        registry = self._registry_from_store(store, context=context)
        if registry is not None:
            discovered = await registry.list_tools(runtime_key, runtime_config)
        else:
            manager = self._runtime_manager_factory()
            await manager.start(runtime_config)
            try:
                discovered = await manager.list_tools()
            finally:
                await manager.close()

        prepared_tools = self._prepare_tools(discovered)
        return {
            "runtime_key": runtime_key,
            "runtime_config": _runtime_config_to_jsonish(runtime_config),
            "tools": prepared_tools,
        }

    def get_tool_schemas(
        self,
        state: Dict[str, Any],
        *,
        prepared: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        tools = list((prepared or {}).get("tools") or [])
        schemas: List[Dict[str, Any]] = []
        for tool in tools:
            schema = tool.get("schema")
            if isinstance(schema, dict):
                schemas.append(schema)
        return schemas

    def can_handle_tool_call(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        tool_schema: Optional[Dict[str, Any]] = None,
        prepared: Optional[Dict[str, Any]] = None,
    ) -> Optional[bool]:
        _ = (
            payload,
            payload_kind,
            payload_format,
            payload_metadata,
            tool_call,
            tool_schema,
            state,
        )
        if not isinstance(tool_name, str) or not tool_name:
            return None
        for tool in list((prepared or {}).get("tools") or []):
            if tool.get("model_tool_name") == tool_name:
                return True
        return None

    async def execute_tool_async(
        self,
        tool_name: Optional[str],
        payload: Any,
        state: Dict[str, Any],
        *,
        payload_kind: Optional[str] = None,
        payload_format: Optional[str] = None,
        payload_metadata: Optional[Dict[str, Any]] = None,
        tool_call: Optional[Dict[str, Any]] = None,
        cancellation: Any | None = None,
        context: Optional[Dict[str, Any]] = None,
        prepared: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        _ = (
            payload_kind,
            payload_format,
            payload_metadata,
            tool_call,
            cancellation,
            state,
        )
        if not isinstance(tool_name, str) or not tool_name:
            return {"success": False, "error": "Missing MCP tool name."}
        if not isinstance(payload, dict):
            return {"success": False, "error": "MCP tool payload must be an object."}

        prepared_catalog = prepared or {}
        tool_entry = None
        for item in list(prepared_catalog.get("tools") or []):
            if item.get("model_tool_name") == tool_name:
                tool_entry = item
                break
        if not isinstance(tool_entry, dict):
            parsed = self._parse_model_tool_name(tool_name)
            if parsed is None:
                return {"success": False, "error": f"Unknown MCP tool: {tool_name}"}
            tool_entry = {
                "model_tool_name": tool_name,
                "server_name": parsed["server_name"],
                "raw_tool_name": parsed["raw_tool_name"],
                "tool_timeout_seconds": None,
            }

        runtime_key = prepared_catalog.get("runtime_key")
        if not isinstance(runtime_key, str) or not runtime_key:
            return {"success": False, "error": "MCP runtime is not available."}
        runtime_config_raw = prepared_catalog.get("runtime_config")
        runtime_config = _runtime_config_from_jsonish(runtime_config_raw)
        if runtime_config is None:
            return {"success": False, "error": "MCP runtime is not available."}

        try:
            registry = self._registry_from_store(
                self._runtime_store(context), context=context
            )
            if registry is not None:
                result = await registry.call_tool(
                    runtime_key,
                    runtime_config,
                    server_name=str(tool_entry.get("server_name") or ""),
                    tool_name=str(tool_entry.get("raw_tool_name") or ""),
                    arguments=dict(payload),
                    timeout_seconds=tool_entry.get("tool_timeout_seconds"),
                )
            else:
                manager = self._runtime_manager_factory()
                await manager.start(runtime_config)
                try:
                    result = await manager.call_tool(
                        server_name=str(tool_entry.get("server_name") or ""),
                        tool_name=str(tool_entry.get("raw_tool_name") or ""),
                        arguments=dict(payload),
                        timeout_seconds=tool_entry.get("tool_timeout_seconds"),
                    )
                finally:
                    await manager.close()
        except Exception as exc:
            return {"success": False, "error": f"MCP tool error: {exc}"}

        summary_text = _text_summary_from_content(result.content)
        return {
            "success": not result.is_error,
            "server_name": tool_entry.get("server_name"),
            "raw_tool_name": tool_entry.get("raw_tool_name"),
            "content": result.content,
            "structured_content": result.structured_content,
            "meta": result.meta,
            "summary_text": summary_text,
        }

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> Any:
        _ = state
        if not result.get("success"):
            return f"Error: {result.get('error')}"

        content = result.get("content")
        if not isinstance(content, list):
            content = []
        raw_result = MCPToolCallResult(
            is_error=False,
            content=[item for item in content if isinstance(item, dict)],
            structured_content=(
                result.get("structured_content")
                if isinstance(result.get("structured_content"), dict)
                else None
            ),
            meta=result.get("meta") if isinstance(result.get("meta"), dict) else None,
        )
        output = _responses_output_from_result(raw_result)
        summary_text = str(result.get("summary_text") or "")
        if raw_result.structured_content:
            output.append(
                {
                    "type": "input_text",
                    "text": "Structured content:\n"
                    + json.dumps(
                        raw_result.structured_content, indent=2, sort_keys=True
                    ),
                }
            )
            if not summary_text:
                summary_text = json.dumps(raw_result.structured_content, sort_keys=True)
        if not output:
            output = [
                {
                    "type": "input_text",
                    "text": summary_text or "MCP tool call completed.",
                }
            ]
        return make_provider_native_tool_result(
            format=FORMAT_OPENAI_RESPONSES,
            output=output,
            text=summary_text or "MCP tool call completed.",
        )

    def _build_runtime_config(self, config: Dict[str, Any]) -> MCPRuntimeConfig:
        raw_servers = config.get("mcp_servers")
        server_specs: Dict[str, MCPServerRuntimeSpec] = {}
        if isinstance(raw_servers, dict):
            for server_name, raw_spec in raw_servers.items():
                if not isinstance(server_name, str) or not server_name:
                    continue
                if not isinstance(raw_spec, dict):
                    continue
                spec = self._build_server_spec(server_name, raw_spec, config=config)
                if spec is not None:
                    server_specs[server_name] = spec

        return MCPRuntimeConfig(
            servers=server_specs,
            fail_on_startup_error=bool(config.get("mcp_fail_on_startup_error", False)),
            reuse_runtime=bool(config.get("mcp_reuse_runtime", True)),
        )

    def _build_server_spec(
        self,
        server_name: str,
        raw_spec: Dict[str, Any],
        *,
        config: Dict[str, Any],
    ) -> MCPServerRuntimeSpec | None:
        transport = raw_spec.get("transport", "stdio")
        if transport not in {"stdio", "sse", "http"}:
            return None
        command = raw_spec.get("command")
        if command is not None and not isinstance(command, str):
            command = None
        args = raw_spec.get("args")
        if not isinstance(args, list):
            args = []
        env = raw_spec.get("env")
        if not isinstance(env, dict):
            env = {}
        headers = raw_spec.get("headers")
        if not isinstance(headers, dict):
            headers = {}
        cwd = raw_spec.get("cwd")
        if cwd is not None and not isinstance(cwd, str):
            cwd = None
        url = raw_spec.get("url")
        if url is not None and not isinstance(url, str):
            url = None
        enabled_override = config.get(self._server_enabled_override_key(server_name))
        if isinstance(enabled_override, bool):
            enabled = enabled_override
        else:
            enabled = bool(raw_spec.get("enabled", False))
        return MCPServerRuntimeSpec(
            name=server_name,
            enabled=enabled,
            transport=transport,
            command=command,
            args=[str(item) for item in args if isinstance(item, (str, int, float))],
            env={
                str(key): str(value)
                for key, value in env.items()
                if isinstance(key, str)
            },
            cwd=cwd,
            url=url,
            headers={
                str(key): str(value)
                for key, value in headers.items()
                if isinstance(key, str)
            },
            startup_timeout_seconds=_coerce_positive_int(
                raw_spec.get("startup_timeout_seconds")
            ),
            tool_timeout_seconds=_coerce_positive_int(
                raw_spec.get("tool_timeout_seconds")
            ),
            metadata={},
        )

    def _prepare_tools(
        self, discovered: List[MCPDiscoveredTool]
    ) -> List[Dict[str, Any]]:
        by_server: Dict[str, List[MCPDiscoveredTool]] = {}
        for tool in discovered:
            by_server.setdefault(tool.server_name, []).append(tool)

        prepared: List[Dict[str, Any]] = []
        for server_name in sorted(by_server.keys()):
            tools = by_server[server_name]
            qualified = qualify_codex_mcp_names(
                server_name, [tool.raw_name for tool in tools]
            )
            qualified_by_raw = {item.raw_tool_name: item for item in qualified}
            for tool in tools:
                qualified_name = qualified_by_raw[tool.raw_name]
                schema = {
                    "type": "function",
                    "function": {
                        "name": qualified_name.model_tool_name,
                        "description": tool.description
                        or f"MCP tool {tool.raw_name} from server {server_name}.",
                        "strict": False,
                        "parameters": _sanitize_schema_for_codex(
                            tool.input_schema,
                            meta=tool.meta,
                        ),
                    },
                }
                prepared.append(
                    {
                        "model_tool_name": qualified_name.model_tool_name,
                        "server_name": tool.server_name,
                        "raw_tool_name": tool.raw_name,
                        "tool_timeout_seconds": None,
                        "schema": schema,
                    }
                )
        return prepared

    def _runtime_store(self, context: Optional[Dict[str, Any]]) -> Any | None:
        if not isinstance(context, dict):
            return None
        store = context.get("runtime_store")
        if store is None:
            store = context.get("tool_runtime")
        if store is not None and all(
            hasattr(store, attr) for attr in ("get", "get_or_create")
        ):
            return store
        return None

    def _registry_from_store(
        self,
        store: Any | None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> MCPRegistry | None:
        if store is None:
            return None
        app = None
        if isinstance(context, dict):
            app = context.get("app") or context.get("application")
        if app is None:
            return None
        registry = store.get_or_create(
            self.runtime_store_key,
            lambda: MCPRegistry(app=app, manager_factory=self._runtime_manager_factory),
        )
        return registry if isinstance(registry, MCPRegistry) else None

    def _server_enabled_override_key(self, server_name: str) -> str:
        return f"mcp_server__{server_name}__enabled"

    def _parse_model_tool_name(self, tool_name: str) -> Dict[str, str] | None:
        parts = tool_name.split("__", 2)
        if len(parts) != 3:
            return None
        prefix, server_name, raw_tool_name = parts
        if prefix != "mcp" or not server_name or not raw_tool_name:
            return None
        return {
            "server_name": server_name,
            "raw_tool_name": raw_tool_name,
        }


def _coerce_positive_int(value: Any) -> int | None:
    if isinstance(value, bool):
        return None
    if isinstance(value, int) and value > 0:
        return value
    return None


def _runtime_config_to_jsonish(config: MCPRuntimeConfig) -> Dict[str, Any]:
    return {
        "servers": {
            name: asdict(spec) for name, spec in sorted(config.servers.items())
        },
        "fail_on_startup_error": config.fail_on_startup_error,
        "reuse_runtime": config.reuse_runtime,
    }


def _runtime_config_from_jsonish(raw: Any) -> MCPRuntimeConfig | None:
    if not isinstance(raw, dict):
        return None
    raw_servers = raw.get("servers")
    if not isinstance(raw_servers, dict):
        return None
    servers: Dict[str, MCPServerRuntimeSpec] = {}
    for name, spec in raw_servers.items():
        if not isinstance(name, str) or not isinstance(spec, dict):
            continue
        transport = spec.get("transport")
        if transport not in {"stdio", "sse", "http"}:
            continue
        servers[name] = MCPServerRuntimeSpec(
            name=name,
            enabled=bool(spec.get("enabled", True)),
            transport=transport,
            command=(
                spec.get("command") if isinstance(spec.get("command"), str) else None
            ),
            args=[
                str(item)
                for item in spec.get("args", [])
                if isinstance(item, (str, int, float))
            ],
            env=(
                {str(k): str(v) for k, v in spec.get("env", {}).items()}
                if isinstance(spec.get("env"), dict)
                else {}
            ),
            cwd=spec.get("cwd") if isinstance(spec.get("cwd"), str) else None,
            url=spec.get("url") if isinstance(spec.get("url"), str) else None,
            headers=(
                {str(k): str(v) for k, v in spec.get("headers", {}).items()}
                if isinstance(spec.get("headers"), dict)
                else {}
            ),
            startup_timeout_seconds=_coerce_positive_int(
                spec.get("startup_timeout_seconds")
            ),
            tool_timeout_seconds=_coerce_positive_int(spec.get("tool_timeout_seconds")),
            metadata=(
                dict(spec.get("metadata"))
                if isinstance(spec.get("metadata"), dict)
                else {}
            ),
        )
    return MCPRuntimeConfig(
        servers=servers,
        fail_on_startup_error=bool(raw.get("fail_on_startup_error", False)),
        reuse_runtime=bool(raw.get("reuse_runtime", True)),
    )


__all__ = ["CodexMCPTool"]
