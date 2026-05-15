from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Dict, List

from .runtime import (
    MCPDiscoveredTool,
    MCPRuntimeConfig,
    MCPRuntimeManager,
    MCPServerSnapshot,
    MCPToolCallResult,
)


@dataclass
class _RuntimeRecord:
    runtime_key: str
    runtime_config: MCPRuntimeConfig
    manager: MCPRuntimeManager
    discovered_tools: List[MCPDiscoveredTool]
    snapshots: List[MCPServerSnapshot]


class MCPRegistry:
    """Application-scoped registry of live MCP runtimes."""

    def __init__(self, *, app: Any, manager_factory: Any = MCPRuntimeManager) -> None:
        self._app = app
        self._manager_factory = manager_factory
        self._lock = threading.RLock()
        self._records: Dict[str, _RuntimeRecord] = {}

    async def ensure_runtime(
        self,
        runtime_key: str,
        runtime_config: MCPRuntimeConfig,
    ) -> _RuntimeRecord:
        with self._lock:
            existing = self._records.get(runtime_key)
        if existing is not None:
            return existing

        manager = self._manager_factory()
        await manager.start(runtime_config)
        discovered = await manager.list_tools()
        record = _RuntimeRecord(
            runtime_key=runtime_key,
            runtime_config=runtime_config,
            manager=manager,
            discovered_tools=list(discovered),
            snapshots=list(manager.status_snapshot()),
        )
        with self._lock:
            current = self._records.get(runtime_key)
            if current is not None:
                await manager.close()
                return current
            self._records[runtime_key] = record
        return record

    async def list_tools(
        self,
        runtime_key: str,
        runtime_config: MCPRuntimeConfig,
    ) -> List[MCPDiscoveredTool]:
        record = await self.ensure_runtime(runtime_key, runtime_config)
        tools = await record.manager.list_tools()
        with self._lock:
            record.discovered_tools = list(tools)
            record.snapshots = list(record.manager.status_snapshot())
            return list(record.discovered_tools)

    async def call_tool(
        self,
        runtime_key: str,
        runtime_config: MCPRuntimeConfig,
        *,
        server_name: str,
        tool_name: str,
        arguments: Dict[str, Any],
        timeout_seconds: int | None = None,
    ) -> MCPToolCallResult:
        record = await self.ensure_runtime(runtime_key, runtime_config)
        result = await record.manager.call_tool(
            server_name=server_name,
            tool_name=tool_name,
            arguments=arguments,
            timeout_seconds=timeout_seconds,
        )
        with self._lock:
            record.snapshots = list(record.manager.status_snapshot())
        return result

    def snapshot(self) -> List[Dict[str, Any]]:
        with self._lock:
            rows: List[Dict[str, Any]] = []
            for runtime_key, record in sorted(self._records.items()):
                rows.append(
                    {
                        "runtime_key": runtime_key,
                        "servers": [
                            {
                                "name": snapshot.name,
                                "enabled": snapshot.enabled,
                                "transport": snapshot.transport,
                                "state": snapshot.state,
                                "tool_count": snapshot.tool_count,
                                "error": snapshot.error,
                            }
                            for snapshot in record.snapshots
                        ],
                    }
                )
            return rows

    async def clear_runtime(self, runtime_key: str) -> bool:
        with self._lock:
            record = self._records.pop(runtime_key, None)
        if record is None:
            return False
        await record.manager.close()
        return True

    async def clear_all(self) -> int:
        with self._lock:
            records = list(self._records.values())
            self._records.clear()
        for record in records:
            await record.manager.close()
        return len(records)

    def close(self) -> None:
        runner = getattr(self._app, "run_awaitable_blocking", None)
        if callable(runner):
            runner(self.clear_all())
            return
        with self._lock:
            self._records.clear()


__all__ = ["MCPRegistry"]