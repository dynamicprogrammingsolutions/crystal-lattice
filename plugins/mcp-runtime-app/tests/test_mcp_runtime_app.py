from __future__ import annotations

from mcp_runtime_app import MCPRuntimeAppPlugin


class _DummyRegistry:
    def __init__(self) -> None:
        self.closed = False

    def snapshot(self):
        return [
            {
                "runtime_key": "abc",
                "servers": [
                    {
                        "name": "filesystem",
                        "state": "connected",
                        "tool_count": 2,
                        "enabled": True,
                        "transport": "stdio",
                        "error": None,
                    }
                ],
            }
        ]

    async def clear_all(self):
        self.closed = True
        return 1

    def close(self) -> None:
        self.closed = True


class _DummyStore:
    def __init__(self) -> None:
        self.items = {"mcp_registry": _DummyRegistry()}

    def get(self, key, default=None):
        return self.items.get(key, default)


class _DummyApp:
    def __init__(self) -> None:
        self.store = _DummyStore()

    def get_runtime_store(self):
        return self.store

    def run_awaitable_blocking(self, awaitable):
        import asyncio

        return asyncio.run(awaitable)


class _EmptyStoreApp(_DummyApp):
    def __init__(self) -> None:
        self.store = _DummyStore()
        self.store.items = {}


def test_get_ui_elements_hidden_without_mcp_servers() -> None:
    plugin = MCPRuntimeAppPlugin()
    assert plugin.get_ui_elements({}, config={}) == []


def test_get_ui_elements_hidden_when_mcp_disabled() -> None:
    plugin = MCPRuntimeAppPlugin()
    assert plugin.get_ui_elements({}, config={"mcp_enabled": False, "mcp_servers": {"filesystem": {}}}) == []


def test_show_status_returns_display_payload() -> None:
    plugin = MCPRuntimeAppPlugin()
    result = plugin.execute_action(_DummyApp(), "mcp_show_status", {}, None, {})
    display = result["display"]
    assert display["title"] == "MCP Runtime Status"
    assert "filesystem" in display["body"]


def test_clear_runtime_clears_registry_runtimes() -> None:
    plugin = MCPRuntimeAppPlugin()
    app = _DummyApp()
    result = plugin.execute_action(app, "mcp_clear_runtime", {}, None, {})
    assert result["cleared"] == 1
    assert app.store.items["mcp_registry"].closed is True


def test_show_status_handles_missing_registry() -> None:
    plugin = MCPRuntimeAppPlugin()
    result = plugin.execute_action(_EmptyStoreApp(), "mcp_show_status", {}, None, {})
    assert "No MCP runtimes are currently stored." in result["display"]["body"]