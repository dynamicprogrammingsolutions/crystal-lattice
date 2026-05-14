from __future__ import annotations

import hashlib
import json
from contextlib import AsyncExitStack
from dataclasses import asdict, dataclass, field
from datetime import timedelta
from typing import Any, Dict, Literal


TransportName = Literal["stdio", "sse", "http"]
ServerStateName = Literal["disabled", "connected", "failed"]


@dataclass(frozen=True)
class MCPServerRuntimeSpec:
    name: str
    enabled: bool
    transport: TransportName
    command: str | None = None
    args: list[str] = field(default_factory=list)
    env: dict[str, str] = field(default_factory=dict)
    cwd: str | None = None
    url: str | None = None
    headers: dict[str, str] = field(default_factory=dict)
    startup_timeout_seconds: int | None = None
    tool_timeout_seconds: int | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MCPRuntimeConfig:
    servers: dict[str, MCPServerRuntimeSpec]
    fail_on_startup_error: bool = False
    reuse_runtime: bool = True


@dataclass(frozen=True)
class MCPDiscoveredTool:
    server_name: str
    raw_name: str
    description: str
    input_schema: dict[str, Any]
    annotations: dict[str, Any] = field(default_factory=dict)
    meta: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class MCPToolCallResult:
    is_error: bool
    content: list[dict[str, Any]]
    structured_content: dict[str, Any] | None = None
    meta: dict[str, Any] | None = None


@dataclass(frozen=True)
class MCPServerSnapshot:
    name: str
    enabled: bool
    transport: TransportName
    state: ServerStateName
    tool_count: int = 0
    error: str | None = None


@dataclass
class _RuntimeEntry:
    spec: MCPServerRuntimeSpec
    stack: AsyncExitStack
    session: Any
    tools: list[MCPDiscoveredTool]


def fingerprint_runtime_config(config: MCPRuntimeConfig) -> str:
    payload = {
        "servers": {
            name: asdict(spec) for name, spec in sorted(config.servers.items())
        },
        "fail_on_startup_error": config.fail_on_startup_error,
        "reuse_runtime": config.reuse_runtime,
    }
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha1(encoded.encode("utf-8")).hexdigest()


class MCPRuntimeManager:
    """Vendor-neutral MCP runtime manager.

    The manager keeps MCP client sessions alive across requests when the
    application-owned tool runtime store chooses to reuse it.
    """

    def __init__(self) -> None:
        self._config: MCPRuntimeConfig | None = None
        self._fingerprint: str | None = None
        self._entries: Dict[str, _RuntimeEntry] = {}
        self._snapshots: Dict[str, MCPServerSnapshot] = {}
        self._started = False

    @property
    def runtime_fingerprint(self) -> str | None:
        return self._fingerprint

    async def start(self, config: MCPRuntimeConfig) -> None:
        fingerprint = fingerprint_runtime_config(config)
        if self._started and self._fingerprint == fingerprint:
            return
        if self._started:
            await self.close()

        self._config = config
        self._fingerprint = fingerprint
        self._entries = {}
        self._snapshots = {}

        for server_name, spec in sorted(config.servers.items()):
            if not spec.enabled:
                self._snapshots[server_name] = MCPServerSnapshot(
                    name=server_name,
                    enabled=False,
                    transport=spec.transport,
                    state="disabled",
                )
                continue
            try:
                entry = await self._connect_server(spec)
            except Exception as exc:
                self._snapshots[server_name] = MCPServerSnapshot(
                    name=server_name,
                    enabled=True,
                    transport=spec.transport,
                    state="failed",
                    error=str(exc),
                )
                if config.fail_on_startup_error:
                    await self.close()
                    raise
                continue

            self._entries[server_name] = entry
            self._snapshots[server_name] = MCPServerSnapshot(
                name=server_name,
                enabled=True,
                transport=spec.transport,
                state="connected",
                tool_count=len(entry.tools),
            )

        self._started = True

    async def list_tools(self) -> list[MCPDiscoveredTool]:
        tools: list[MCPDiscoveredTool] = []
        for entry in self._entries.values():
            tools.extend(entry.tools)
        return list(tools)

    def status_snapshot(self) -> list[MCPServerSnapshot]:
        return [self._snapshots[name] for name in sorted(self._snapshots.keys())]

    async def call_tool(
        self,
        *,
        server_name: str,
        tool_name: str,
        arguments: dict[str, Any],
        timeout_seconds: int | None = None,
    ) -> MCPToolCallResult:
        entry = self._entries.get(server_name)
        if entry is None:
            raise RuntimeError(f"MCP server '{server_name}' is not connected")

        kwargs: dict[str, Any] = {}
        if isinstance(timeout_seconds, int) and timeout_seconds > 0:
            kwargs["read_timeout_seconds"] = timedelta(seconds=timeout_seconds)
        result = await entry.session.call_tool(tool_name, arguments, **kwargs)

        content = []
        for part in list(getattr(result, "content", []) or []):
            content.append(_content_block_to_dict(part))

        structured_content = getattr(result, "structuredContent", None)
        if structured_content is None:
            structured_content = getattr(result, "structured_content", None)
        if not isinstance(structured_content, dict):
            structured_content = None

        meta = getattr(result, "meta", None)
        if not isinstance(meta, dict):
            meta = None

        is_error = bool(
            getattr(result, "isError", False) or getattr(result, "is_error", False)
        )
        return MCPToolCallResult(
            is_error=is_error,
            content=content,
            structured_content=structured_content,
            meta=meta,
        )

    async def close(self) -> None:
        entries = list(self._entries.values())
        self._entries = {}
        for entry in entries:
            await entry.stack.aclose()
        self._started = False

    async def _connect_server(self, spec: MCPServerRuntimeSpec) -> _RuntimeEntry:
        stack = AsyncExitStack()
        try:
            session = await self._open_session(spec, stack)
            raw_tools = await session.list_tools()
            tools = _extract_discovered_tools(spec.name, raw_tools)
            return _RuntimeEntry(spec=spec, stack=stack, session=session, tools=tools)
        except Exception:
            await stack.aclose()
            raise

    async def _open_session(self, spec: MCPServerRuntimeSpec, stack: AsyncExitStack) -> Any:
        client_session_cls, transport_factory = _resolve_sdk_primitives(spec.transport)

        if spec.transport == "stdio":
            stdio_params_cls = _resolve_stdio_server_parameters()
            params = stdio_params_cls(
                command=spec.command,
                args=list(spec.args),
                env=dict(spec.env),
                cwd=spec.cwd,
            )
            transport_values = await stack.enter_async_context(
                transport_factory(params)
            )
        else:
            if not isinstance(spec.url, str) or not spec.url:
                raise ValueError(f"MCP server '{spec.name}' is missing url")
            kwargs: dict[str, Any] = {}
            if spec.headers:
                kwargs["headers"] = dict(spec.headers)
            transport_values = await stack.enter_async_context(
                transport_factory(spec.url, **kwargs)
            )
        if not isinstance(transport_values, tuple) or len(transport_values) < 2:
            raise RuntimeError("MCP transport did not return read/write streams")
        read_stream, write_stream = transport_values[:2]

        session = await stack.enter_async_context(
            client_session_cls(read_stream, write_stream)
        )
        await session.initialize()
        return session


def _resolve_sdk_primitives(transport: TransportName) -> tuple[Any, Any]:
    from importlib import import_module

    client_module = import_module("mcp")
    client_session_cls = getattr(client_module, "ClientSession", None)
    if client_session_cls is None:
        client_session_cls = getattr(import_module("mcp.client.session"), "ClientSession")

    if transport == "stdio":
        transport_module = import_module("mcp.client.stdio")
        return client_session_cls, getattr(transport_module, "stdio_client")
    if transport == "sse":
        transport_module = import_module("mcp.client.sse")
        return client_session_cls, getattr(transport_module, "sse_client")

    try:
        transport_module = import_module("mcp.client.streamable_http")
    except ModuleNotFoundError:
        transport_module = import_module("mcp.client.http")

    transport_factory = getattr(transport_module, "streamablehttp_client", None)
    if transport_factory is None:
        transport_factory = getattr(transport_module, "streamable_http_client", None)
    if transport_factory is None:
        transport_factory = getattr(transport_module, "http_client", None)
    if transport_factory is None:
        raise RuntimeError("Could not locate a streamable HTTP MCP client helper")
    return client_session_cls, transport_factory


def _resolve_stdio_server_parameters() -> Any:
    from importlib import import_module

    client_module = import_module("mcp")
    params_cls = getattr(client_module, "StdioServerParameters", None)
    if params_cls is None:
        params_cls = getattr(import_module("mcp.client.stdio"), "StdioServerParameters")
    return params_cls


def _extract_discovered_tools(server_name: str, raw_tools: Any) -> list[MCPDiscoveredTool]:
    tools = getattr(raw_tools, "tools", raw_tools)
    discovered: list[MCPDiscoveredTool] = []
    for tool in list(tools or []):
        dumped = _maybe_model_dump(tool)
        raw_name = str(_get_value(tool, dumped, "name", "") or "")
        if not raw_name:
            continue
        description = str(_get_value(tool, dumped, "description", "") or "")
        input_schema = _get_value(tool, dumped, "inputSchema", None)
        if input_schema is None:
            input_schema = _get_value(tool, dumped, "input_schema", None)
        if not isinstance(input_schema, dict):
            input_schema = {"type": "object", "properties": {}}
        annotations = _get_value(tool, dumped, "annotations", None)
        if not isinstance(annotations, dict):
            annotations = {}
        meta = _get_value(tool, dumped, "meta", None)
        if not isinstance(meta, dict):
            meta = {}
        discovered.append(
            MCPDiscoveredTool(
                server_name=server_name,
                raw_name=raw_name,
                description=description,
                input_schema=dict(input_schema),
                annotations=dict(annotations),
                meta=dict(meta),
            )
        )
    return discovered


def _content_block_to_dict(part: Any) -> dict[str, Any]:
    if isinstance(part, dict):
        return dict(part)
    dumped = _maybe_model_dump(part)
    if isinstance(dumped, dict):
        part_type = dumped.get("type")
        if isinstance(part_type, str):
            return dumped

    part_type = getattr(part, "type", None)
    if part_type == "text":
        return {"type": "text", "text": getattr(part, "text", "")}
    if part_type in {"image", "audio"}:
        return {
            "type": part_type,
            "mimeType": getattr(part, "mimeType", None),
            "data": getattr(part, "data", None),
        }
    if part_type == "resource":
        resource = getattr(part, "resource", None)
        return {"type": "resource", "resource": _resource_to_dict(resource)}
    if part_type == "resource_link":
        return {
            "type": "resource_link",
            "uri": str(getattr(part, "uri", "")),
            "name": getattr(part, "name", None),
            "title": getattr(part, "title", None),
            "mimeType": getattr(part, "mimeType", None),
        }
    return {"type": str(part_type or "unknown"), "repr": repr(part)}


def _resource_to_dict(resource: Any) -> dict[str, Any]:
    if isinstance(resource, dict):
        return dict(resource)
    dumped = _maybe_model_dump(resource)
    if isinstance(dumped, dict):
        return dumped
    return {
        "text": getattr(resource, "text", None),
        "blob": getattr(resource, "blob", None),
        "mimeType": getattr(resource, "mimeType", None),
        "uri": str(getattr(resource, "uri", "")) if getattr(resource, "uri", None) else None,
    }


def _maybe_model_dump(value: Any) -> dict[str, Any] | None:
    fn = getattr(value, "model_dump", None)
    if not callable(fn):
        return None
    try:
        dumped = fn(exclude_none=True)
    except TypeError:
        dumped = fn()
    return dumped if isinstance(dumped, dict) else None


def _get_value(obj: Any, dumped: dict[str, Any] | None, key: str, default: Any) -> Any:
    if isinstance(dumped, dict) and key in dumped:
        return dumped.get(key)
    return getattr(obj, key, default)