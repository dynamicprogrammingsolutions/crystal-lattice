from __future__ import annotations

import asyncio
import shutil
import time
from contextlib import asynccontextmanager

import pytest
import mcp_shared.runtime as runtime_mod

from mcp_shared import (
    MCPDiscoveredTool,
    MCPRuntimeConfig,
    MCPRegistry,
    MCPRuntimeManager,
    MCPServerRuntimeSpec,
    MCPServerSnapshot,
    MCPToolCallResult,
    fingerprint_runtime_config,
)


def test_fingerprint_runtime_config_changes_with_content() -> None:
    config_a = MCPRuntimeConfig(
        servers={
            "filesystem": MCPServerRuntimeSpec(
                name="filesystem",
                enabled=True,
                transport="stdio",
                command="node",
                args=["server.js"],
            )
        }
    )
    config_b = MCPRuntimeConfig(
        servers={
            "filesystem": MCPServerRuntimeSpec(
                name="filesystem",
                enabled=True,
                transport="stdio",
                command="node",
                args=["server-other.js"],
            )
        }
    )

    assert fingerprint_runtime_config(config_a)
    assert fingerprint_runtime_config(config_a) != fingerprint_runtime_config(config_b)


def test_runtime_manager_status_snapshot_defaults_empty() -> None:
    manager = MCPRuntimeManager()
    assert manager.status_snapshot() == []


def test_discovered_tool_dataclass_fields() -> None:
    tool = MCPDiscoveredTool(
        server_name="filesystem",
        raw_name="read_file",
        description="Read a file",
        input_schema={"type": "object", "properties": {}},
    )
    assert tool.server_name == "filesystem"
    assert tool.raw_name == "read_file"


class _StallingClientSession:
    def __init__(self, read_stream, write_stream) -> None:
        _ = read_stream, write_stream

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = exc_type, exc, tb

    async def initialize(self) -> None:
        await asyncio.sleep(60)

    async def list_tools(self):
        raise AssertionError("list_tools should not run after startup timeout")


class _StallingListToolsClientSession:
    def __init__(self, read_stream, write_stream) -> None:
        _ = read_stream, write_stream

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = exc_type, exc, tb

    async def initialize(self) -> None:
        return None

    async def list_tools(self):
        await asyncio.sleep(60)


class _UnauthorizedResponse:
    status_code = 401


class _UnauthorizedMCPError(Exception):
    response = _UnauthorizedResponse()


class _UnauthorizedClientSession:
    def __init__(self, read_stream, write_stream) -> None:
        _ = read_stream, write_stream

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = exc_type, exc, tb

    async def initialize(self) -> None:
        raise _UnauthorizedMCPError(
            "401 Unauthorized: WWW-Authenticate Bearer resource_metadata"
        )

    async def list_tools(self):
        raise AssertionError("list_tools should not run after unauthorized startup")


@asynccontextmanager
async def _fake_http_transport(url: str, **kwargs):
    _ = url, kwargs
    yield "read-stream", "write-stream"


@pytest.mark.asyncio
async def test_http_mcp_auth_required_does_not_hang_startup(monkeypatch) -> None:
    monkeypatch.setattr(
        runtime_mod,
        "_resolve_sdk_primitives",
        lambda transport: (_StallingClientSession, _fake_http_transport),
    )

    manager = MCPRuntimeManager()
    config = MCPRuntimeConfig(
        servers={
            "protected": MCPServerRuntimeSpec(
                name="protected",
                enabled=True,
                transport="http",
                url="http://127.0.0.1:1/mcp",
                startup_timeout_seconds=0.1,
            )
        },
        fail_on_startup_error=False,
    )

    started_at = time.monotonic()
    await asyncio.wait_for(manager.start(config), timeout=1)
    elapsed = time.monotonic() - started_at

    assert elapsed < 0.8
    assert await manager.list_tools() == []
    snapshots = manager.status_snapshot()
    assert len(snapshots) == 1
    snapshot = snapshots[0]
    assert snapshot.name == "protected"
    assert snapshot.state in {"failed", "auth_required"}
    assert snapshot.error
    assert "timed out" in snapshot.error.lower()


@pytest.mark.asyncio
async def test_runtime_manager_startup_timeout_covers_initial_list_tools(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runtime_mod,
        "_resolve_sdk_primitives",
        lambda transport: (_StallingListToolsClientSession, _fake_http_transport),
    )

    manager = MCPRuntimeManager()
    config = MCPRuntimeConfig(
        servers={
            "protected": MCPServerRuntimeSpec(
                name="protected",
                enabled=True,
                transport="http",
                url="http://127.0.0.1:1/mcp",
                startup_timeout_seconds=0.1,
            )
        },
        fail_on_startup_error=False,
    )

    await asyncio.wait_for(manager.start(config), timeout=1)

    snapshot = manager.status_snapshot()[0]
    assert snapshot.state == "failed"
    assert snapshot.error
    assert "timed out" in snapshot.error.lower()


@pytest.mark.asyncio
async def test_runtime_manager_marks_unauthorized_startup_as_auth_required(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runtime_mod,
        "_resolve_sdk_primitives",
        lambda transport: (_UnauthorizedClientSession, _fake_http_transport),
    )

    manager = MCPRuntimeManager()
    config = MCPRuntimeConfig(
        servers={
            "protected": MCPServerRuntimeSpec(
                name="protected",
                enabled=True,
                transport="http",
                url="http://127.0.0.1:1/mcp",
                startup_timeout_seconds=1,
            )
        },
        fail_on_startup_error=False,
    )

    await manager.start(config)

    assert await manager.list_tools() == []
    snapshot = manager.status_snapshot()[0]
    assert snapshot.state == "auth_required"
    assert snapshot.error
    assert "unauthorized" in snapshot.error.lower()


class _FakeApp:
    def run_awaitable_blocking(self, awaitable):
        import asyncio

        return asyncio.run(awaitable)


class _FakeRuntimeManager:
    instances = []

    def __init__(self) -> None:
        self.started = 0
        self.closed = 0
        _FakeRuntimeManager.instances.append(self)

    async def start(self, config) -> None:
        self.started += 1
        self.config = config

    async def list_tools(self):
        return [
            MCPDiscoveredTool(
                server_name="filesystem",
                raw_name="read_file",
                description="Read file",
                input_schema={"type": "object", "properties": {}},
            )
        ]

    async def call_tool(
        self, *, server_name: str, tool_name: str, arguments: dict, timeout_seconds=None
    ):
        return MCPToolCallResult(
            is_error=False,
            content=[
                {
                    "type": "text",
                    "text": f"{server_name}:{tool_name}:{arguments['path']}",
                }
            ],
            structured_content=None,
        )

    def status_snapshot(self):
        return [
            MCPServerSnapshot(
                name="filesystem",
                enabled=True,
                transport="stdio",
                state="connected",
                tool_count=1,
                error=None,
            )
        ]

    async def close(self):
        self.closed += 1


@pytest.mark.asyncio
async def test_registry_reuses_runtime_for_same_key() -> None:
    _FakeRuntimeManager.instances = []
    registry = MCPRegistry(app=_FakeApp(), manager_factory=_FakeRuntimeManager)
    config = MCPRuntimeConfig(
        servers={
            "filesystem": MCPServerRuntimeSpec(
                name="filesystem",
                enabled=True,
                transport="stdio",
                command="node",
                args=["server.js"],
            )
        }
    )

    tools_a = await registry.list_tools("same-key", config)
    tools_b = await registry.list_tools("same-key", config)

    assert [tool.raw_name for tool in tools_a] == ["read_file"]
    assert [tool.raw_name for tool in tools_b] == ["read_file"]
    assert len(_FakeRuntimeManager.instances) == 1


def test_registry_close_closes_all_runtimes() -> None:
    _FakeRuntimeManager.instances = []
    registry = MCPRegistry(app=_FakeApp(), manager_factory=_FakeRuntimeManager)
    config = MCPRuntimeConfig(
        servers={
            "filesystem": MCPServerRuntimeSpec(
                name="filesystem",
                enabled=True,
                transport="stdio",
                command="node",
                args=["server.js"],
            )
        }
    )

    import asyncio

    asyncio.run(registry.ensure_runtime("close-key", config))
    registry.close()

    assert len(_FakeRuntimeManager.instances) == 1
    assert _FakeRuntimeManager.instances[0].closed == 1


@pytest.mark.integration
@pytest.mark.asyncio
async def test_runtime_manager_can_connect_to_real_filesystem_mcp_server(
    tmp_path,
) -> None:
    if shutil.which("npx") is None:
        pytest.skip("npx not available")

    note = tmp_path / "note.txt"
    note.write_text("hello from runtime test\n", encoding="utf-8")

    manager = MCPRuntimeManager()
    config = MCPRuntimeConfig(
        servers={
            "filesystem": MCPServerRuntimeSpec(
                name="filesystem",
                enabled=True,
                transport="stdio",
                command="npx",
                args=[
                    "-y",
                    "@modelcontextprotocol/server-filesystem",
                    str(tmp_path.resolve()),
                ],
                cwd=str(tmp_path.resolve()),
                startup_timeout_seconds=30,
                tool_timeout_seconds=30,
            )
        },
        fail_on_startup_error=True,
    )

    try:
        await manager.start(config)
        tools = await manager.list_tools()
        assert any(tool.raw_name == "read_file" for tool in tools)

        result = await manager.call_tool(
            server_name="filesystem",
            tool_name="read_file",
            arguments={"path": str(note.resolve())},
            timeout_seconds=30,
        )

        assert result.is_error is False
        assert result.content
        assert result.content[0]["type"] == "text"
        assert "hello from runtime test" in result.content[0]["text"]
    finally:
        await manager.close()
