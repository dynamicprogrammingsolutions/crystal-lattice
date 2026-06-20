from __future__ import annotations

from urllib.parse import parse_qs, urlparse

import mcp_runtime_app as mcp_runtime_app_mod
from mcp_runtime_app import MCPRuntimeAppPlugin
from mcp_shared import (
    MCP_OAUTH_PENDING_STORE_KEY,
    MCP_OAUTH_TOKENS_STORE_KEY,
)


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


class _FailingClearRegistry(_DummyRegistry):
    async def clear_all(self):
        self.closed = True
        raise RuntimeError("Attempted to exit cancel scope in a different task")


class _DummyStore:
    def __init__(self) -> None:
        self.items = {"mcp_registry": _DummyRegistry()}

    def get(self, key, default=None):
        return self.items.get(key, default)

    def set(self, key, value):
        self.items[key] = value

    def get_or_create(self, key, factory):
        if key not in self.items:
            self.items[key] = factory()
        return self.items[key]


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


class _CheckingRegistry:
    instances = []

    def __init__(self, *, app) -> None:
        self.app = app
        self.cleared = 0
        self.started = []
        _CheckingRegistry.instances.append(self)

    async def list_tools(self, runtime_key, runtime_config):
        self.started.append((runtime_key, runtime_config))
        return []

    async def clear_all(self):
        self.cleared += 1
        return 1

    def snapshot(self):
        return [
            {
                "runtime_key": self.started[-1][0] if self.started else "missing",
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


def test_check_servers_starts_runtime_from_session_config(monkeypatch) -> None:
    monkeypatch.setattr(mcp_runtime_app_mod, "MCPRegistry", _CheckingRegistry)
    _CheckingRegistry.instances = []
    plugin = MCPRuntimeAppPlugin()
    app = _DummyApp()
    app.store.items = {}

    result = plugin.execute_action(
        app,
        "mcp_check_servers",
        {"connection_id": "test-connection"},
        {
            "session_id": "session-123",
            "base_config": {
                "mcp_enabled": True,
                "mcp_servers": {
                    "protected": {
                        "transport": "http",
                        "url": "https://mcp.example.test/mcp",
                    }
                },
            },
        },
        {},
    )

    assert result["cleared"] == 0
    assert _CheckingRegistry.instances
    registry = _CheckingRegistry.instances[0]
    assert len(registry.started) == 1
    runtime_config = registry.started[0][1]
    assert runtime_config.servers["protected"].url == "https://mcp.example.test/mcp"
    assert "protected" in result["display"]["body"]
    assert result["display"]["actions"][0]["action_id"] == "mcp_start_login"


def test_check_servers_prefers_effective_config_over_base_config(monkeypatch) -> None:
    monkeypatch.setattr(mcp_runtime_app_mod, "MCPRegistry", _CheckingRegistry)
    _CheckingRegistry.instances = []
    plugin = MCPRuntimeAppPlugin()
    app = _DummyApp()
    app.store.items = {}

    result = plugin.execute_action(
        app,
        "mcp_check_servers",
        {"connection_id": "test-connection"},
        {
            "session_id": "session-123",
            "base_config": {
                "mcp_enabled": False,
                "mcp_servers": {},
            },
            "config": {
                "mcp_enabled": True,
                "mcp_servers": {
                    "protected": {
                        "transport": "http",
                        "url": "https://mcp.example.test/mcp",
                    }
                },
            },
        },
        {},
    )

    assert result["cleared"] == 0
    assert _CheckingRegistry.instances
    runtime_config = _CheckingRegistry.instances[0].started[0][1]
    assert runtime_config.servers["protected"].url == "https://mcp.example.test/mcp"
    assert "MCP is disabled for this session" not in result["display"]["body"]


def test_reconnect_servers_clears_then_starts_runtime_from_session_config(
    monkeypatch,
) -> None:
    monkeypatch.setattr(mcp_runtime_app_mod, "MCPRegistry", _CheckingRegistry)
    _CheckingRegistry.instances = []
    plugin = MCPRuntimeAppPlugin()
    app = _DummyApp()
    existing = _CheckingRegistry(app=app)
    app.store.items = {"mcp_registry": existing}

    result = plugin.execute_action(
        app,
        "mcp_reconnect_servers",
        {"connection_id": "test-connection"},
        {
            "session_id": "session-123",
            "base_config": {
                "mcp_enabled": True,
                "mcp_servers": {
                    "protected": {
                        "transport": "http",
                        "url": "https://mcp.example.test/mcp",
                    }
                },
            },
        },
        {},
    )

    assert result["cleared"] == 1
    assert existing.cleared == 1
    assert len(existing.started) == 1
    assert "protected" in result["display"]["body"]


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
    assert login["client_info"]["token_endpoint_auth_method"] == "none"


def test_start_login_uses_nested_oauth_config_and_redirect_template() -> None:
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
                        "oauth": {
                            "authorization_url": "https://auth.example.test/authorize",
                            "token_endpoint": "https://auth.example.test/token",
                            "client_id": "client-123",
                            "client_secret": "secret-123",
                            "token_endpoint_auth_method": "client_secret_post",
                            "scope": "mcp:connect",
                            "redirect_uri": "https://crystallattice.dev/oauth/{connection_id}/{session_id}/{server_name}/callback",
                        },
                    }
                }
            },
        },
        {},
    )

    authorization_url = result["authorization_url"]
    query = parse_qs(urlparse(authorization_url).query)
    assert query["redirect_uri"] == [
        "https://crystallattice.dev/oauth/test-connection/session-123/protected/callback"
    ]
    assert query["scope"] == ["mcp:connect"]

    pending = app.store.items[MCP_OAUTH_PENDING_STORE_KEY]
    login = pending[query["state"][0]]
    assert login["redirect_uri"] == (
        "https://crystallattice.dev/oauth/test-connection/session-123/protected/callback"
    )
    assert login["client_info"]["client_id"] == "client-123"
    assert login["client_info"]["client_secret"] == "secret-123"
    assert login["client_info"]["redirect_uris"] == [
        "https://crystallattice.dev/oauth/test-connection/session-123/protected/callback"
    ]
    assert login["client_info"]["token_endpoint_auth_method"] == "client_secret_post"


class _FakeToken:
    def model_dump(self, *, mode, exclude_none):
        assert mode == "json"
        assert exclude_none is True
        return {
            "access_token": "access-123",
            "token_type": "Bearer",
            "refresh_token": "refresh-123",
        }


def _pending_login(server_name: str = "protected") -> dict:
    return {
        "server_name": server_name,
        "server_url": "https://mcp.example.test/mcp",
        "redirect_uri": f"crystal-lattice://action/test-connection/session-123/mcp_runtime_app/mcp_complete_login?server_name={server_name}",
        "connection_id": "test-connection",
        "token_endpoint": "https://auth.example.test/token",
        "code_verifier": "verifier",
        "client_info": {
            "client_id": "client-123",
            "token_endpoint_auth_method": "none",
            "redirect_uris": [
                f"crystal-lattice://action/test-connection/session-123/mcp_runtime_app/mcp_complete_login?server_name={server_name}"
            ],
        },
        "resource": "https://mcp.example.test/mcp",
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


def test_complete_login_succeeds_when_runtime_cleanup_fails(monkeypatch) -> None:
    plugin = MCPRuntimeAppPlugin()
    app = _DummyApp()
    app.store.items["mcp_registry"] = _FailingClearRegistry()
    app.store.items[MCP_OAUTH_PENDING_STORE_KEY] = {
        "state-123": _pending_login(),
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
    assert app.store.items[MCP_OAUTH_TOKENS_STORE_KEY]["protected"]["access_token"] == (
        "access-123"
    )
    assert "runtime refresh will be retried" in result["display"]["body"]


def test_complete_login_replayed_callback_is_idempotent_after_token_stored() -> None:
    plugin = MCPRuntimeAppPlugin()
    app = _DummyApp()
    app.store.items[MCP_OAUTH_PENDING_STORE_KEY] = {}
    app.store.items[MCP_OAUTH_TOKENS_STORE_KEY] = {
        "protected": {
            "access_token": "access-123",
            "token_type": "Bearer",
            "server_url": "https://mcp.example.test/mcp",
        }
    }

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
    assert result["display"]["variant"] == "success"
    assert "already signed in" in result["display"]["body"]


def test_complete_login_refreshes_runtime_when_session_config_available(
    monkeypatch,
) -> None:
    monkeypatch.setattr(mcp_runtime_app_mod, "MCPRegistry", _CheckingRegistry)
    plugin = MCPRuntimeAppPlugin()
    app = _DummyApp()
    existing = _CheckingRegistry(app=app)
    app.store.items["mcp_registry"] = existing
    app.store.items[MCP_OAUTH_PENDING_STORE_KEY] = {
        "state-123": {
            "server_name": "protected",
            "server_url": "https://mcp.example.test/mcp",
            "redirect_uri": "crystal-lattice://action/test-connection/session-123/mcp_runtime_app/mcp_complete_login?server_name=protected",
            "connection_id": "test-connection",
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
        {
            "session_id": "session-123",
            "base_config": {
                "mcp_enabled": True,
                "mcp_servers": {
                    "protected": {
                        "transport": "http",
                        "url": "https://mcp.example.test/mcp",
                    }
                },
            },
        },
        {},
    )

    assert result["message"] == "Signed in to protected."
    assert result["cleared"] == 1
    assert existing.cleared == 1
    assert len(existing.started) == 1
    assert result["runtimes"][0]["servers"][0]["name"] == "protected"
    assert "MCP runtimes were refreshed" in result["display"]["body"]


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
