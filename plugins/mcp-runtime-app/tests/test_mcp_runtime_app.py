from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from mcp_runtime_app import MCPRuntimeAppPlugin
from mcp_shared import MCP_OAUTH_PENDING_STORE_KEY, MCP_OAUTH_TOKENS_STORE_KEY


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

    def set(self, key, value):
        self.items[key] = value


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


class _AuthRequiredRegistry:
    def snapshot(self):
        return [
            {
                "runtime_key": "abc",
                "servers": [
                    {
                        "name": "protected",
                        "state": "auth_required",
                        "tool_count": 0,
                        "enabled": True,
                        "transport": "http",
                        "error": "Authentication required for this MCP server. Open MCP status to sign in.",
                    }
                ],
            }
        ]


class _AuthRequiredStoreApp(_DummyApp):
    def __init__(self) -> None:
        self.store = _DummyStore()
        self.store.items = {"mcp_registry": _AuthRequiredRegistry()}


def test_get_ui_elements_hidden_without_mcp_servers() -> None:
    plugin = MCPRuntimeAppPlugin()
    assert plugin.get_ui_elements({}, config={}) == []


def test_get_ui_elements_hidden_when_mcp_disabled() -> None:
    plugin = MCPRuntimeAppPlugin()
    assert (
        plugin.get_ui_elements(
            {}, config={"mcp_enabled": False, "mcp_servers": {"filesystem": {}}}
        )
        == []
    )


def test_show_status_returns_display_payload() -> None:
    plugin = MCPRuntimeAppPlugin()
    result = plugin.execute_action(_DummyApp(), "mcp_show_status", {}, None, {})
    display = result["display"]
    assert display["title"] == "MCP Runtime Status"
    assert "filesystem" in display["body"]


def test_show_status_exposes_auth_required_server() -> None:
    plugin = MCPRuntimeAppPlugin()
    result = plugin.execute_action(
        _AuthRequiredStoreApp(),
        "mcp_show_status",
        {"connection_id": "test-connection"},
        None,
        {},
    )
    body = result["display"]["body"]
    assert "protected" in body
    assert "auth_required" in body
    assert "Open MCP status to sign in" in body
    actions = result["display"]["actions"]
    assert actions == [
        {
            "kind": "run_action",
            "id": "mcp-start-login-protected",
            "label": "Sign in to protected",
            "plugin": "mcp_runtime_app",
            "action_id": "mcp_start_login",
            "fixed_params": {
                "server_name": "protected",
                "connection_id": "test-connection",
            },
            "preserve_display": True,
        }
    ]


def test_start_login_returns_open_and_copy_actions_and_stores_pending() -> None:
    plugin = MCPRuntimeAppPlugin()
    app = _DummyApp()

    result = plugin.execute_action(
        app,
        "mcp_start_login",
        {"server_name": "protected", "connection_id": "test-connection"},
        {
            "session_id": "session-123",
            "base_config": {
                "mcp_servers": {
                    "protected": {
                        "transport": "http",
                        "url": "https://mcp.example.test/mcp",
                        "oauth_authorization_url": "https://auth.example.test/authorize",
                        "oauth_token_endpoint": "https://auth.example.test/token",
                        "oauth_client_id": "client-123",
                    }
                }
            },
        },
        {},
    )

    authorization_url = result["authorization_url"]
    parsed = urlparse(authorization_url)
    query = parse_qs(parsed.query)
    assert parsed.scheme == "https"
    assert parsed.netloc == "auth.example.test"
    assert parsed.path == "/authorize"
    assert query["client_id"] == ["client-123"]
    assert query["response_type"] == ["code"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["redirect_uri"] == [
        "crystal-lattice://action/test-connection/session-123/mcp_runtime_app/mcp_complete_login?server_name=protected"
    ]

    actions = result["display"]["actions"]
    assert [action["kind"] for action in actions] == ["open_url", "copy_text"]
    assert actions[0]["url"] == authorization_url
    assert actions[1]["text"] == authorization_url

    pending = app.store.items[MCP_OAUTH_PENDING_STORE_KEY]
    assert list(pending.keys()) == query["state"]
    login = pending[query["state"][0]]
    assert login["server_name"] == "protected"
    assert login["token_endpoint"] == "https://auth.example.test/token"


class _FakeToken:
    def model_dump(self, *, mode, exclude_none):
        assert mode == "json"
        assert exclude_none is True
        return {
            "access_token": "access-123",
            "token_type": "Bearer",
            "refresh_token": "refresh-123",
        }


def test_complete_login_stores_token_and_clears_runtime(monkeypatch) -> None:
    plugin = MCPRuntimeAppPlugin()
    app = _DummyApp()
    app.store.items[MCP_OAUTH_PENDING_STORE_KEY] = {
        "state-123": {
            "server_name": "protected",
            "server_url": "https://mcp.example.test/mcp",
            "redirect_uri": "crystal-lattice://action/test-connection/session-123/mcp_runtime_app/mcp_complete_login?server_name=protected",
            "token_endpoint": "https://auth.example.test/token",
            "code_verifier": "verifier",
            "client_info": {
                "client_id": "client-123",
                "token_endpoint_auth_method": "none",
                "redirect_uris": [
                    "crystal-lattice://action/test-connection/session-123/mcp_runtime_app/mcp_complete_login?server_name=protected"
                ],
            },
            "resource": "https://mcp.example.test/mcp",
        }
    }

    async def fake_exchange(login, code):
        assert login["server_name"] == "protected"
        assert code == "code-123"
        return _FakeToken()

    monkeypatch.setattr(plugin, "_exchange_code_for_token", fake_exchange)

    result = plugin.execute_action(
        app,
        "mcp_complete_login",
        {
            "server_name": "protected",
            "code": "code-123",
            "state": "state-123",
            "redirect_url": "crystal-lattice://action/test-connection/session-123/mcp_runtime_app/mcp_complete_login?server_name=protected&code=code-123&state=state-123",
        },
        {"session_id": "session-123"},
        {},
    )

    assert result["message"] == "Signed in to protected."
    assert app.store.items[MCP_OAUTH_PENDING_STORE_KEY] == {}
    token = app.store.items[MCP_OAUTH_TOKENS_STORE_KEY]["protected"]
    assert token["access_token"] == "access-123"
    assert token["server_url"] == "https://mcp.example.test/mcp"
    assert app.store.items["mcp_registry"].closed is True


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
