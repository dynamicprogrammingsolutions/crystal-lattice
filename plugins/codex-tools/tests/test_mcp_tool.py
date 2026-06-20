from __future__ import annotations

import asyncio

from codex_tools.mcp_tool import CodexMCPTool
from mcp_shared import MCPDiscoveredTool, MCPToolCallResult


class _DummyStore:
    def __init__(self) -> None:
        self.items = {}

    def get(self, namespace: str, key: str):
        return self.items.get((namespace, key))

    def set(self, namespace: str, key: str, value):
        self.items[(namespace, key)] = value


class _FakeRuntimeManager:
    def __init__(self) -> None:
        self.started = 0

    async def start(self, config) -> None:
        self.started += 1
        self.config = config

    async def list_tools(self):
        if not self.config.servers["filesystem"].enabled:
            return []
        return [
            MCPDiscoveredTool(
                server_name="filesystem",
                raw_name="read-file",
                description="Read a file",
                input_schema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                },
            ),
            MCPDiscoveredTool(
                server_name="filesystem",
                raw_name="read_file",
                description="Read a file via alias",
                input_schema={
                    "type": "object",
                    "properties": {"path": {"type": "string"}},
                },
            ),
        ]

    def status_snapshot(self):
        return [
            {
                "name": "filesystem",
                "state": "connected",
                "tool_count": 2,
                "enabled": True,
                "transport": "stdio",
                "error": None,
            }
        ]

    async def close(self):
        return None

    async def call_tool(
        self, *, server_name: str, tool_name: str, arguments: dict, timeout_seconds=None
    ):
        assert server_name == "filesystem"
        assert tool_name in {"read-file", "read_file"}
        assert arguments == {"path": "/tmp/notes.txt"}
        return MCPToolCallResult(
            is_error=False,
            content=[{"type": "text", "text": "notes"}],
            structured_content={"bytes": 5},
        )


def _config():
    return {
        "mcp_enabled": True,
        "mcp_servers": {
            "filesystem": {
                "enabled": True,
                "transport": "stdio",
                "command": "node",
                "args": ["server.js"],
            }
        },
    }


def test_codex_mcp_ui_elements_show_global_and_per_server_toggle() -> None:
    tool = CodexMCPTool()
    elements = tool.get_ui_elements(_config())
    keys = [item["key"] for item in elements]
    assert keys == ["mcp_enabled", "mcp_server__filesystem__enabled"]


def test_codex_mcp_prepare_builds_unique_tool_names_and_schemas() -> None:
    tool = CodexMCPTool()
    tool._runtime_manager_factory = _FakeRuntimeManager
    prepared = asyncio.run(
        tool.prepare_async(
            _config(),
            {"config": _config()},
            context={"tool_runtime": _DummyStore()},
        )
    )
    schemas = tool.get_tool_schemas({"config": _config()}, prepared=prepared)
    names = [schema["function"]["name"] for schema in schemas]
    assert len(names) == 2
    assert names[0].startswith("mcp__filesystem__")
    assert names[1].startswith("mcp__filesystem__")
    assert len(set(names)) == 2


def test_codex_mcp_prepare_treats_missing_server_enabled_as_disabled() -> None:
    tool = CodexMCPTool()
    tool._runtime_manager_factory = _FakeRuntimeManager
    config = _config()
    config["mcp_servers"]["filesystem"].pop("enabled")

    prepared = asyncio.run(
        tool.prepare_async(
            config,
            {"config": config},
            context={"tool_runtime": _DummyStore()},
        )
    )

    assert prepared["tools"] == []


def test_codex_mcp_prepare_server_enabled_override_can_enable_missing_enabled() -> None:
    tool = CodexMCPTool()
    tool._runtime_manager_factory = _FakeRuntimeManager
    config = _config()
    config["mcp_servers"]["filesystem"].pop("enabled")
    config["mcp_server__filesystem__enabled"] = True

    prepared = asyncio.run(
        tool.prepare_async(
            config,
            {"config": config},
            context={"tool_runtime": _DummyStore()},
        )
    )

    assert prepared["tools"]


def test_codex_mcp_execute_and_format_returns_provider_native_tool_result() -> None:
    tool = CodexMCPTool()
    tool._runtime_manager_factory = _FakeRuntimeManager
    prepared = {
        "runtime_key": "runtime-1",
        "runtime_config": {
            "servers": {
                "filesystem": {
                    "name": "filesystem",
                    "enabled": True,
                    "transport": "stdio",
                    "command": "node",
                    "args": ["server.js"],
                    "env": {},
                    "headers": {},
                    "metadata": {},
                    "startup_timeout_seconds": None,
                    "tool_timeout_seconds": None,
                    "cwd": None,
                    "url": None,
                }
            },
            "fail_on_startup_error": False,
            "reuse_runtime": True,
        },
        "tools": [
            {
                "model_tool_name": "mcp__filesystem__read_file",
                "server_name": "filesystem",
                "raw_tool_name": "read_file",
                "tool_timeout_seconds": None,
                "schema": {
                    "type": "function",
                    "function": {
                        "name": "mcp__filesystem__read_file",
                        "description": "Read a file",
                        "parameters": {"type": "object", "properties": {}},
                    },
                },
            }
        ],
    }
    store = _DummyStore()
    result = asyncio.run(
        tool.execute_tool_async(
            "mcp__filesystem__read_file",
            {"path": "/tmp/notes.txt"},
            {"config": _config()},
            context={"tool_runtime": store},
            prepared=prepared,
        )
    )
    assert result["success"] is True
    formatted = tool.format_tool_result(result, {"config": _config()})
    assert formatted["type"] == "provider_native_tool_result"
    assert formatted["format"] == "openai.responses"
    assert formatted["output"][0]["text"] == "notes"
