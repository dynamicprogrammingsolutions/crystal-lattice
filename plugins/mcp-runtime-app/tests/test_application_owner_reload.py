from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from agent_app.application_future import AgentApplication
from agent_app.application_owner import AgentApplicationOwner, ApplicationControl
from agent_app.events import InMemoryEventStore
from mcp_shared.registry import MCPRegistry
from mcp_shared.runtime import MCPRuntimeConfig


class _FakeManager:
    def __init__(self, closed: list[bool], event_store: InMemoryEventStore) -> None:
        self._closed = closed
        self._event_store = event_store

    async def start(self, config: MCPRuntimeConfig) -> None:
        _ = config

    async def list_tools(self) -> list[Any]:
        return []

    def status_snapshot(self) -> list[Any]:
        return []

    async def close(self) -> None:
        events = self._event_store.list(since_id="0", limit=50)["events"]
        assert "application_reload_completed" not in {event["type"] for event in events}
        self._closed.append(True)


def test_application_replacement_closes_mcp_before_completion(tmp_path: Path) -> None:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps({"providers": {}, "agents": {}, "plugins": []}),
        encoding="utf-8",
    )
    event_store = InMemoryEventStore()

    def factory(control: ApplicationControl) -> AgentApplication:
        return AgentApplication(
            config_path,
            tmp_path / "sessions",
            event_store=event_store,
            application_control=control,
        )

    owner = AgentApplicationOwner(factory, event_store=event_store)
    old_application = owner.current
    closed: list[bool] = []
    registry = MCPRegistry(
        app=old_application,
        manager_factory=lambda: _FakeManager(closed, event_store),
    )
    old_application.run_awaitable_blocking(
        registry.ensure_runtime("fixture", MCPRuntimeConfig(servers={}))
    )
    old_application.get_runtime_store().set("mcp_registry", registry)

    result = owner.request_reload(reason="mcp-cleanup-test")

    assert owner.wait_for_reload(result["reload_id"], timeout=5)
    assert closed == [True]
    events = event_store.list(since_id="0", limit=50)["events"]
    event_types = [event["type"] for event in events]
    assert event_types.index("application_reload_completed") > event_types.index(
        "application_reload_ready"
    )
