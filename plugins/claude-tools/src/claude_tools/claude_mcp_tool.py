# Licensing note:
# This file may contain both original code authored for this repository and
# material derived from or adapted from Claude Code or other
# Anthropic-authored materials.
#
# Original code in this file authored for this repository is licensed under
# the Apache License, Version 2.0.
#
# Copyright 2026 Dynamic Programming Solutions Kft.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Anthropic-derived material in this file is not licensed by us under
# Apache-2.0, and are instead subject to Anthropic's terms:
#
# © Anthropic PBC. All rights reserved. Use is subject to Anthropic's
# Commercial Terms of Service:
# https://www.anthropic.com/legal/commercial-terms

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict
from typing import Any, Dict, Iterable, List, Optional

from agent_core.tool_result_payloads import (
    FORMAT_ANTHROPIC_MESSAGES,
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

from .interop import claude_tool_interop_contribution


MCP_PREFIX = "mcp__"
MCP_DELIMITER = "__"
MAX_TOOL_NAME_LENGTH = 64
HASH_LEN = 12


def _sanitize_tool_name_part(value: str) -> str:
    out = []
    for char in value:
        if char.isascii() and (char.isalnum() or char == "_"):
            out.append(char)
        else:
            out.append("_")
    return "".join(out) or "_"


def _unique_name(namespace: str, tool_name: str, identity: str, seen: set[str]) -> str:
    candidate = f"{namespace}{tool_name}"
    if len(candidate) <= MAX_TOOL_NAME_LENGTH and candidate not in seen:
        seen.add(candidate)
        return candidate

    attempt = 0
    while True:
        suffix = (
            "_"
            + hashlib.sha1(f"{identity}\0{attempt}".encode("utf-8")).hexdigest()[
                :HASH_LEN
            ]
        )
        max_tool_len = max(1, MAX_TOOL_NAME_LENGTH - len(namespace) - len(suffix))
        truncated = tool_name[:max_tool_len]
        candidate = f"{namespace}{truncated}{suffix}"
        if len(candidate) > MAX_TOOL_NAME_LENGTH:
            overflow = len(candidate) - MAX_TOOL_NAME_LENGTH
            if overflow > 0:
                namespace_part = (
                    namespace[:-overflow] if overflow < len(namespace) else ""
                )
                candidate = f"{namespace_part}{truncated}{suffix}"
        if candidate not in seen:
            seen.add(candidate)
            return candidate
        attempt += 1


def qualify_claude_mcp_names(
    server_name: str,
    tool_names: Iterable[str],
) -> List[Dict[str, str]]:
    seen: set[str] = set()
    namespace = _sanitize_tool_name_part(f"{MCP_PREFIX}{server_name}{MCP_DELIMITER}")
    qualified: List[Dict[str, str]] = []
    for raw_tool_name in tool_names:
        base_name = _sanitize_tool_name_part(raw_tool_name)
        model_tool_name = _unique_name(
            namespace,
            base_name,
            f"{server_name}\0{raw_tool_name}",
            seen,
        )
        qualified.append(
            {
                "server_name": server_name,
                "raw_tool_name": raw_tool_name,
                "model_tool_name": model_tool_name,
            }
        )
    return qualified


def _default_input_schema() -> Dict[str, Any]:
    return {"type": "object", "properties": {}}


def _coerce_anthropic_input_schema(schema: Any) -> Dict[str, Any]:
    if not isinstance(schema, dict):
        return _default_input_schema()
    out = dict(schema)
    if not isinstance(out.get("type"), str):
        out["type"] = "object"
    if out.get("type") == "object" and not isinstance(out.get("properties"), dict):
        out["properties"] = {}
    return out


def _text_summary_from_content(content: Iterable[Dict[str, Any]]) -> str:
    parts: List[str] = []
    for part in content:
        part_type = part.get("type")
        if part_type == "text":
            text = part.get("text")
            if isinstance(text, str) and text:
                parts.append(text)
            continue
        if part_type in {"image", "audio"}:
            mime_type = part.get("mimeType") or "unknown"
            parts.append(f"[{str(part_type).title()}: {mime_type}]")
            continue
        if part_type == "resource_link":
            parts.append(f"[Resource link: {part.get('uri') or ''}]")
            continue
        if part_type == "resource":
            resource = part.get("resource")
            if isinstance(resource, dict):
                text = resource.get("text")
                if isinstance(text, str) and text:
                    parts.append(text)
                    continue
                mime_type = resource.get("mimeType") or "unknown"
                parts.append(f"[Embedded resource: {mime_type}]")
    return "\n".join(parts)


def _claude_success_content(result: MCPToolCallResult) -> str:
    summary_text = _text_summary_from_content(result.content)
    payload: Dict[str, Any] = {"content": summary_text}
    return json.dumps(payload, separators=(",", ":"))


def _tool_result_block(
    tool_use_id: str,
    content: str,
    *,
    is_error: bool = False,
) -> Dict[str, Any]:
    block: Dict[str, Any] = {
        "type": "tool_result",
        "tool_use_id": tool_use_id,
        "content": content,
        "cache_control": {"type": "ephemeral"},
    }
    if is_error:
        block["is_error"] = True
    return block


class ClaudeMCPTool(ToolPlugin):
    name = "claude_mcp_tool"
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

    def get_tool_interop_contribution(self, state: Dict[str, Any]):
        _ = state
        return claude_tool_interop_contribution()

    async def prepare_async(
        self,
        config: Dict[str, Any],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        _ = state
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
        _ = state
        return [
            dict(item["schema"])
            for item in list((prepared or {}).get("tools") or [])
            if isinstance(item, dict) and isinstance(item.get("schema"), dict)
        ]

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
            state,
            payload_kind,
            payload_format,
            payload_metadata,
            tool_call,
            tool_schema,
        )
        if not isinstance(tool_name, str) or not tool_name:
            return None
        for item in list((prepared or {}).get("tools") or []):
            if isinstance(item, dict) and item.get("model_tool_name") == tool_name:
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
            state,
            payload_kind,
            payload_format,
            payload_metadata,
            cancellation,
        )
        if not isinstance(tool_name, str) or not tool_name:
            return {"success": False, "error": "Missing MCP tool name."}
        if not isinstance(payload, dict):
            return {"success": False, "error": "MCP tool payload must be an object."}

        prepared_catalog = prepared or {}
        tool_entry = self._tool_entry_for_name(tool_name, prepared_catalog)
        if tool_entry is None:
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
        runtime_config = _runtime_config_from_jsonish(
            prepared_catalog.get("runtime_config")
        )
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
            return {
                "success": False,
                "server_name": tool_entry.get("server_name"),
                "raw_tool_name": tool_entry.get("raw_tool_name"),
                "error": f"MCP tool error: {exc}",
                "tool_use_id": self._tool_use_id(tool_call, fallback=tool_name),
            }

        summary_text = _text_summary_from_content(result.content)
        return {
            "success": not result.is_error,
            "server_name": tool_entry.get("server_name"),
            "raw_tool_name": tool_entry.get("raw_tool_name"),
            "content": result.content,
            "structured_content": result.structured_content,
            "meta": result.meta,
            "summary_text": summary_text,
            "error": summary_text if result.is_error else None,
            "tool_use_id": self._tool_use_id(tool_call, fallback=tool_name),
        }

    def format_tool_result(self, result: Dict[str, Any], state: Dict[str, Any]) -> Any:
        _ = state
        tool_use_id = str(result.get("tool_use_id") or "call_mcp")
        if not result.get("success"):
            content = str(result.get("error") or "MCP tool call failed.")
            block = _tool_result_block(tool_use_id, content, is_error=True)
            return make_provider_native_tool_result(
                format=FORMAT_ANTHROPIC_MESSAGES,
                content=[block],
                text=content,
            )

        raw_result = MCPToolCallResult(
            is_error=False,
            content=[
                item
                for item in list(result.get("content") or [])
                if isinstance(item, dict)
            ],
            structured_content=(
                result.get("structured_content")
                if isinstance(result.get("structured_content"), dict)
                else None
            ),
            meta=result.get("meta") if isinstance(result.get("meta"), dict) else None,
        )
        content = _claude_success_content(raw_result)
        block = _tool_result_block(tool_use_id, content)
        return make_provider_native_tool_result(
            format=FORMAT_ANTHROPIC_MESSAGES,
            content=[block],
            text=str(result.get("summary_text") or ""),
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
        transport = raw_spec.get("transport", raw_spec.get("type", "stdio"))
        if transport not in {"stdio", "sse", "http"}:
            return None
        enabled_override = config.get(self._server_enabled_override_key(server_name))
        enabled = (
            enabled_override
            if isinstance(enabled_override, bool)
            else bool(raw_spec.get("enabled", False))
        )
        return MCPServerRuntimeSpec(
            name=server_name,
            enabled=enabled,
            transport=transport,
            command=(
                raw_spec.get("command")
                if isinstance(raw_spec.get("command"), str)
                else None
            ),
            args=(
                [
                    str(item)
                    for item in raw_spec.get("args", [])
                    if isinstance(item, (str, int, float))
                ]
                if isinstance(raw_spec.get("args"), list)
                else []
            ),
            env=(
                {
                    str(key): str(value)
                    for key, value in raw_spec.get("env", {}).items()
                    if isinstance(key, str)
                }
                if isinstance(raw_spec.get("env"), dict)
                else {}
            ),
            cwd=raw_spec.get("cwd") if isinstance(raw_spec.get("cwd"), str) else None,
            url=raw_spec.get("url") if isinstance(raw_spec.get("url"), str) else None,
            headers=(
                {
                    str(key): str(value)
                    for key, value in raw_spec.get("headers", {}).items()
                    if isinstance(key, str)
                }
                if isinstance(raw_spec.get("headers"), dict)
                else {}
            ),
            startup_timeout_seconds=_coerce_positive_int(
                raw_spec.get("startup_timeout_seconds")
            ),
            tool_timeout_seconds=_coerce_positive_int(
                raw_spec.get("tool_timeout_seconds")
            ),
            metadata={},
        )

    def _prepare_tools(
        self,
        discovered: List[MCPDiscoveredTool],
    ) -> List[Dict[str, Any]]:
        by_server: Dict[str, List[MCPDiscoveredTool]] = {}
        for tool in discovered:
            by_server.setdefault(tool.server_name, []).append(tool)

        prepared: List[Dict[str, Any]] = []
        for server_name in sorted(by_server.keys()):
            tools = by_server[server_name]
            qualified = qualify_claude_mcp_names(
                server_name,
                [tool.raw_name for tool in tools],
            )
            qualified_by_raw = {item["raw_tool_name"]: item for item in qualified}
            for tool in tools:
                qualified_name = qualified_by_raw[tool.raw_name]
                schema = {
                    "name": qualified_name["model_tool_name"],
                    "description": tool.description
                    or f"MCP tool {tool.raw_name} from server {server_name}.",
                    "input_schema": _coerce_anthropic_input_schema(tool.input_schema),
                }
                prepared.append(
                    {
                        "model_tool_name": qualified_name["model_tool_name"],
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
            lambda: MCPRegistry(
                app=app,
                manager_factory=self._runtime_manager_factory,
            ),
        )
        return registry if isinstance(registry, MCPRegistry) else None

    def _server_enabled_override_key(self, server_name: str) -> str:
        return f"mcp_server__{server_name}__enabled"

    def _tool_entry_for_name(
        self,
        tool_name: str,
        prepared_catalog: Dict[str, Any],
    ) -> Dict[str, Any] | None:
        for item in list(prepared_catalog.get("tools") or []):
            if isinstance(item, dict) and item.get("model_tool_name") == tool_name:
                return item
        return None

    def _parse_model_tool_name(self, tool_name: str) -> Dict[str, str] | None:
        parts = tool_name.split(MCP_DELIMITER, 2)
        if len(parts) != 3:
            return None
        prefix, server_name, raw_tool_name = parts
        if prefix != "mcp" or not server_name or not raw_tool_name:
            return None
        return {"server_name": server_name, "raw_tool_name": raw_tool_name}

    def _tool_use_id(
        self,
        tool_call: Optional[Dict[str, Any]],
        *,
        fallback: str,
    ) -> str:
        if isinstance(tool_call, dict):
            raw_id = tool_call.get("id")
            if isinstance(raw_id, str) and raw_id:
                return raw_id
        return f"call_{fallback}"


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
                {str(key): str(value) for key, value in spec.get("env", {}).items()}
                if isinstance(spec.get("env"), dict)
                else {}
            ),
            cwd=spec.get("cwd") if isinstance(spec.get("cwd"), str) else None,
            url=spec.get("url") if isinstance(spec.get("url"), str) else None,
            headers=(
                {str(key): str(value) for key, value in spec.get("headers", {}).items()}
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


__all__ = ["ClaudeMCPTool", "qualify_claude_mcp_names"]
