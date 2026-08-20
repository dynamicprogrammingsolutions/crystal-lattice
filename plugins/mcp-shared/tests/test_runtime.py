from __future__ import annotations

import asyncio
import builtins
import shutil
import time
from contextlib import AsyncExitStack, asynccontextmanager
from pathlib import Path
from typing import Any

import pytest
import mcp_shared.runtime as runtime_mod

from mcp_shared import (
    DEFAULT_OAUTH_CLIENT_NAME,
    DEFAULT_OAUTH_CLIENT_URI,
    DEFAULT_OAUTH_SOFTWARE_ID,
    DEFAULT_OAUTH_SOFTWARE_VERSION,
    DEFAULT_OAUTH_TOKEN_ENDPOINT_AUTH_METHOD,
    MCP_OAUTH_TOKENS_STORE_KEY,
    MCPDiscoveredTool,
    MCPRuntimeConfig,
    MCPRegistry,
    MCPRuntimeManager,
    MCPServerRuntimeSpec,
    MCPServerSnapshot,
    MCPToolCallResult,
    apply_oauth_tokens_to_runtime_config,
    build_oauth_client_metadata,
    build_oauth_server_config,
    build_mcp_oauth_token_request,
    fingerprint_runtime_config,
    load_oauth_tokens_into_runtime_store,
    load_persisted_oauth_tokens,
    mcp_oauth_tokens_path,
    render_oauth_redirect_uri,
    save_persisted_oauth_tokens,
)


class _FakeTool:
    """Minimal stand-in for an MCP SDK ``Tool`` pydantic model.

    ``_extract_discovered_tools`` reads fields via ``model_dump()`` (preferred)
    or ``getattr``, so a plain dict does not work. This fake exposes the same
    ``model_dump`` surface as the real model.
    """

    def __init__(self, **fields: Any) -> None:
        self._fields = dict(fields)

    def model_dump(self, exclude_none: bool = False) -> dict[str, Any]:
        if exclude_none:
            return {k: v for k, v in self._fields.items() if v is not None}
        return dict(self._fields)


class _FakeListToolsResult:
    """Stand-in for the MCP SDK ``ListToolsResult`` object."""

    def __init__(self, tools: list[Any]) -> None:
        self.tools = tools


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


def test_extract_discovered_tools_sanitizes_non_standard_input_schema() -> None:
    """MCP servers (e.g. mcp-gsheets) may return inputSchema in a TypeScript
    schema-library format (Effect/Schema-style) instead of JSON Schema. The
    runtime must sanitize it before exposing it to the rest of the platform,
    otherwise LLM providers reject the request with a 400."""
    raw_tools = _FakeListToolsResult(
        tools=[
            _FakeTool(
                name="sheets_merge_cells",
                description="Merge cells in a range",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "spreadsheetId": {
                            "def": {"type": "string"},
                            "type": "string",
                            "format": None,
                            "minLength": None,
                            "maxLength": None,
                        },
                        "range": {
                            "def": {"type": "string"},
                            "type": "string",
                            "format": None,
                            "minLength": None,
                            "maxLength": None,
                        },
                        "mergeType": {
                            "def": {
                                "type": "enum",
                                "entries": {
                                    "MERGE_ALL": "MERGE_ALL",
                                    "MERGE_COLUMNS": "MERGE_COLUMNS",
                                    "MERGE_ROWS": "MERGE_ROWS",
                                },
                            },
                            "type": "enum",
                            "enum": {
                                "MERGE_ALL": "MERGE_ALL",
                                "MERGE_COLUMNS": "MERGE_COLUMNS",
                                "MERGE_ROWS": "MERGE_ROWS",
                            },
                            "options": [
                                "MERGE_ALL",
                                "MERGE_COLUMNS",
                                "MERGE_ROWS",
                            ],
                        },
                    },
                    "required": ["spreadsheetId", "range", "mergeType"],
                },
            )
        ]
    )

    discovered = runtime_mod._extract_discovered_tools("mcp-gsheets", raw_tools)
    assert len(discovered) == 1
    tool = discovered[0]
    assert tool.raw_name == "sheets_merge_cells"
    schema = tool.input_schema

    # Top-level shape preserved.
    assert schema["type"] == "object"
    assert schema["required"] == ["spreadsheetId", "range", "mergeType"]

    # Null-valued optional fields dropped from string properties.
    spreadsheet_id = schema["properties"]["spreadsheetId"]
    assert spreadsheet_id == {"type": "string"}

    # Enum converted to type=string + enum list (from ``options``).
    merge_type = schema["properties"]["mergeType"]
    assert merge_type["type"] == "string"
    assert merge_type["enum"] == ["MERGE_ALL", "MERGE_COLUMNS", "MERGE_ROWS"]

    # No non-standard fields anywhere in the sanitized schema.
    _assert_no_non_standard_fields(schema)


def test_sanitize_input_schema_converts_enum_with_entries_only() -> None:
    """When an enum has ``entries`` (dict) but no ``options`` list, the enum
    values are taken from the dict keys."""
    schema = {
        "type": "object",
        "properties": {
            "color": {
                "type": "enum",
                "entries": {"RED": "RED", "GREEN": "GREEN", "BLUE": "BLUE"},
            }
        },
    }
    sanitized = runtime_mod._sanitize_input_schema(schema)
    color = sanitized["properties"]["color"]
    assert color["type"] == "string"
    assert color["enum"] == ["RED", "GREEN", "BLUE"]


def test_sanitize_input_schema_unwraps_optional_inner_type() -> None:
    """``type: "optional"`` with ``innerType`` is unwrapped to the inner schema,
    preserving non-schema siblings like ``description``."""
    schema = {
        "type": "object",
        "properties": {
            "nickname": {
                "type": "optional",
                "innerType": {"type": "string"},
                "description": "Optional nickname",
            }
        },
    }
    sanitized = runtime_mod._sanitize_input_schema(schema)
    nickname = sanitized["properties"]["nickname"]
    assert nickname["type"] == "string"
    assert nickname["description"] == "Optional nickname"
    assert "innerType" not in nickname
    assert "type" not in nickname or nickname["type"] == "string"


def test_sanitize_input_schema_maps_shape_to_properties_and_element_to_items() -> None:
    """``shape`` becomes ``properties`` and ``element`` becomes ``items``."""
    schema = {
        "type": "object",
        "shape": {
            "tags": {
                "type": "array",
                "element": {"type": "string"},
            }
        },
    }
    sanitized = runtime_mod._sanitize_input_schema(schema)
    assert "shape" not in sanitized
    assert "properties" in sanitized
    tags = sanitized["properties"]["tags"]
    assert tags["type"] == "array"
    assert tags["items"] == {"type": "string"}
    assert "element" not in tags


def test_sanitize_input_schema_drops_non_standard_metadata() -> None:
    """Effect/Schema numeric metadata (``checks``, ``isInt``, ``isFinite``,
    ``minValue``, ``maxValue``) has no safe JSON Schema equivalent and is
    dropped."""
    schema = {
        "type": "object",
        "properties": {
            "ratio": {
                "type": "number",
                "checks": [{}, {}],
                "isInt": False,
                "isFinite": True,
                "minValue": 0,
                "maxValue": 1,
            }
        },
    }
    sanitized = runtime_mod._sanitize_input_schema(schema)
    ratio = sanitized["properties"]["ratio"]
    assert ratio == {"type": "number"}


def test_sanitize_input_schema_preserves_already_valid_json_schema() -> None:
    """A schema that is already valid JSON Schema draft 2020-12 passes through
    unchanged (no regression)."""
    schema = {
        "type": "object",
        "title": "Person",
        "properties": {
            "name": {"type": "string", "minLength": 1, "description": "Full name"},
            "age": {"type": "integer", "minimum": 0, "maximum": 150},
            "tags": {
                "type": "array",
                "items": {"type": "string"},
                "uniqueItems": True,
            },
            "address": {
                "type": "object",
                "properties": {
                    "city": {"type": "string"},
                    "zip": {"type": "string", "pattern": "^[0-9]{5}$"},
                },
                "required": ["city"],
            },
        },
        "required": ["name", "age"],
        "additionalProperties": False,
    }
    sanitized = runtime_mod._sanitize_input_schema(schema)
    assert sanitized == schema


def test_sanitize_input_schema_handles_non_dict_input() -> None:
    """A non-dict inputSchema falls back to a permissive object schema."""
    sanitized = runtime_mod._sanitize_input_schema("not a schema")
    assert sanitized == {"type": "object", "properties": {}}


def test_sanitize_input_schema_guards_against_cycles() -> None:
    """A self-referential schema (malformed) does not blow the stack."""
    cyclic: dict[str, Any] = {"type": "object", "properties": {}}
    cyclic["properties"]["self"] = cyclic
    sanitized = runtime_mod._sanitize_input_schema(cyclic)
    # The cycle target becomes a permissive object schema instead of recursing
    # forever.
    assert sanitized["type"] == "object"
    assert "properties" in sanitized


def _assert_no_non_standard_fields(schema: Any) -> None:
    """Recursively assert that no non-standard JSON Schema fields remain."""
    forbidden_keys = {
        "def",
        "innerType",
        "shape",
        "element",
        "entries",
        "checks",
        "isInt",
        "isFinite",
        "minValue",
        "maxValue",
        "options",
    }
    forbidden_types = {"enum", "optional"}

    def visit(node: Any) -> None:
        if isinstance(node, dict):
            for key, value in node.items():
                assert (
                    key not in forbidden_keys
                ), f"non-standard field {key!r} remains: {node}"
                if key == "type":
                    assert (
                        value not in forbidden_types
                    ), f"non-standard type {value!r} remains: {node}"
                if key == "enum":
                    assert isinstance(
                        value, list
                    ), f"enum must be a list, got {type(value).__name__}: {node}"
                if key in ("format", "minLength", "maxLength") and value is None:
                    assert False, f"null-valued optional field {key!r} remains: {node}"
                visit(value)
        elif isinstance(node, list):
            for item in node:
                visit(item)

    visit(schema)


def test_apply_oauth_tokens_to_runtime_config_adds_authorization_header() -> None:
    config = MCPRuntimeConfig(
        servers={
            "protected": MCPServerRuntimeSpec(
                name="protected",
                enabled=True,
                transport="http",
                url="https://mcp.example.test/mcp",
                headers={"X-Test": "yes"},
            ),
            "public": MCPServerRuntimeSpec(
                name="public",
                enabled=True,
                transport="http",
                url="https://public.example.test/mcp",
            ),
        }
    )
    runtime_store = {
        MCP_OAUTH_TOKENS_STORE_KEY: {
            "protected": {"access_token": "access-123"},
        }
    }

    updated = apply_oauth_tokens_to_runtime_config(config, runtime_store)

    assert updated.servers["protected"].headers == {
        "X-Test": "yes",
        "Authorization": "Bearer access-123",
    }
    assert updated.servers["public"].headers == {}


def test_persisted_oauth_tokens_round_trip_and_apply(tmp_path: Path) -> None:
    tokens = {
        "figma": {
            "access_token": "persisted-access",
            "token_type": "Bearer",
            "server_url": "https://mcp.figma.com/mcp",
        }
    }

    save_persisted_oauth_tokens(tmp_path, tokens)

    assert mcp_oauth_tokens_path(tmp_path) == tmp_path / "mcp" / "oauth-tokens.json"
    assert load_persisted_oauth_tokens(tmp_path) == tokens

    runtime_store: dict[str, Any] = {}
    loaded = load_oauth_tokens_into_runtime_store(runtime_store, tmp_path)
    assert loaded == tokens
    assert runtime_store[MCP_OAUTH_TOKENS_STORE_KEY] == tokens

    config = MCPRuntimeConfig(
        servers={
            "figma": MCPServerRuntimeSpec(
                name="figma",
                enabled=True,
                transport="http",
                url="https://mcp.figma.com/mcp",
            )
        }
    )
    updated = apply_oauth_tokens_to_runtime_config(config, runtime_store)
    assert updated.servers["figma"].headers["Authorization"] == (
        "Bearer persisted-access"
    )


def test_build_oauth_server_config_defaults_and_nested_overrides() -> None:
    config = build_oauth_server_config(
        {
            "oauth_client_id": "legacy-client",
            "oauth_scope": "legacy-scope",
            "oauth": {
                "client_name": "Custom Client",
                "client_uri": "https://client.example.test",
                "client_id": "nested-client",
                "scope": "nested-scope",
                "token_endpoint_auth_method": "client_secret_post",
                "token_exchange": {
                    "include_client_secret": True,
                    "include_resource": False,
                },
            },
        }
    )

    assert config["client_name"] == "Custom Client"
    assert config["client_uri"] == "https://client.example.test"
    assert config["client_id"] == "nested-client"
    assert config["scope"] == "nested-scope"
    assert config["software_id"] == DEFAULT_OAUTH_SOFTWARE_ID
    assert config["software_version"] == DEFAULT_OAUTH_SOFTWARE_VERSION
    assert config["token_endpoint_auth_method"] == "client_secret_post"
    assert config["token_exchange"] == {
        "include_client_secret": True,
        "include_resource": False,
    }


def test_build_oauth_client_metadata_uses_crystal_lattice_defaults() -> None:
    config = build_oauth_server_config({})

    metadata = build_oauth_client_metadata(
        config,
        redirect_uri="crystal-lattice://action/connection/session/plugin/action",
    )

    assert metadata.client_name == DEFAULT_OAUTH_CLIENT_NAME
    assert str(metadata.client_uri).rstrip("/") == DEFAULT_OAUTH_CLIENT_URI
    assert metadata.software_id == DEFAULT_OAUTH_SOFTWARE_ID
    assert metadata.software_version == DEFAULT_OAUTH_SOFTWARE_VERSION
    assert (
        metadata.token_endpoint_auth_method == DEFAULT_OAUTH_TOKEN_ENDPOINT_AUTH_METHOD
    )
    assert [str(uri) for uri in metadata.redirect_uris] == [
        "crystal-lattice://action/connection/session/plugin/action"
    ]


def test_build_oauth_server_config_nested_null_omits_default_metadata() -> None:
    config = build_oauth_server_config(
        {
            "oauth": {
                "client_name": "Codex",
                "client_uri": None,
                "software_id": None,
                "software_version": None,
            }
        }
    )

    metadata = build_oauth_client_metadata(
        config,
        redirect_uri="http://127.0.0.1:41793/callback",
    )

    assert metadata.model_dump(mode="json", exclude_none=True) == {
        "redirect_uris": ["http://127.0.0.1:41793/callback"],
        "token_endpoint_auth_method": "none",
        "grant_types": ["authorization_code", "refresh_token"],
        "response_types": ["code"],
        "client_name": "Codex",
    }


def test_render_oauth_redirect_uri_substitutes_supported_placeholders() -> None:
    rendered = render_oauth_redirect_uri(
        "https://crystallattice.dev/{connection_id}/{session_id}/{plugin_id}/{action_id}/{server_name}",
        connection_id="connection-123",
        session_id="session-123",
        plugin_id="mcp_runtime_app",
        action_id="mcp_complete_login",
        server_name="protected",
    )

    assert rendered == (
        "https://crystallattice.dev/connection-123/session-123/"
        "mcp_runtime_app/mcp_complete_login/protected"
    )


def _oauth_pending(
    *,
    token_endpoint_auth_method: str = "none",
    client_secret: str | None = "secret-123",
    token_exchange: dict | None = None,
) -> dict:
    client_info = {
        "client_id": "client-123",
        "token_endpoint_auth_method": token_endpoint_auth_method,
        "redirect_uris": ["http://localhost:41793/oauth/callback"],
    }
    if client_secret is not None:
        client_info["client_secret"] = client_secret
    return {
        "server_name": "protected",
        "server_url": "https://mcp.example.test/mcp",
        "redirect_uri": "http://localhost:41793/oauth/callback",
        "token_endpoint": "https://auth.example.test/token",
        "code_verifier": "verifier-123",
        "client_info": client_info,
        "resource": "https://mcp.example.test/mcp",
        "oauth_config": {"token_exchange": token_exchange or {}},
    }


def test_build_mcp_oauth_token_request_includes_public_client_secret_when_configured() -> (
    None
):
    token_data, headers, auth = build_mcp_oauth_token_request(
        pending_login=_oauth_pending(
            token_endpoint_auth_method="none",
            token_exchange={"include_client_secret": True},
        ),
        code="code-123",
    )

    assert token_data["client_secret"] == "secret-123"
    assert token_data["resource"] == "https://mcp.example.test/mcp"
    assert headers["Accept"] == "application/json, application/x-www-form-urlencoded"
    assert auth is None


def test_build_mcp_oauth_token_request_can_omit_resource() -> None:
    token_data, _, _ = build_mcp_oauth_token_request(
        pending_login=_oauth_pending(token_exchange={"include_resource": False}),
        code="code-123",
    )

    assert "resource" not in token_data


def test_build_mcp_oauth_token_request_preserves_secret_auth_methods() -> None:
    post_data, _, post_auth = build_mcp_oauth_token_request(
        pending_login=_oauth_pending(token_endpoint_auth_method="client_secret_post"),
        code="code-123",
    )
    basic_data, _, basic_auth = build_mcp_oauth_token_request(
        pending_login=_oauth_pending(token_endpoint_auth_method="client_secret_basic"),
        code="code-123",
    )

    assert post_data["client_secret"] == "secret-123"
    assert post_auth is None
    assert "client_secret" not in basic_data
    assert basic_auth == ("client-123", "secret-123")


def test_build_runtime_config_treats_missing_server_enabled_as_disabled() -> None:
    config = runtime_mod.build_runtime_config_from_config(
        {
            "mcp_servers": {
                "implicit": {
                    "transport": "http",
                    "url": "https://implicit.example.test/mcp",
                },
                "explicit": {
                    "enabled": True,
                    "transport": "http",
                    "url": "https://explicit.example.test/mcp",
                },
            }
        }
    )

    assert config.servers["implicit"].enabled is False
    assert config.servers["explicit"].enabled is True


def test_build_runtime_config_server_enabled_override_can_enable_missing_enabled() -> (
    None
):
    config = runtime_mod.build_runtime_config_from_config(
        {
            "mcp_server__implicit__enabled": True,
            "mcp_servers": {
                "implicit": {
                    "transport": "http",
                    "url": "https://implicit.example.test/mcp",
                },
            },
        }
    )

    assert config.servers["implicit"].enabled is True


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


class _StallingExitClientSession(_StallingClientSession):
    async def __aexit__(self, exc_type, exc, tb) -> None:
        _ = exc_type, exc, tb
        await asyncio.sleep(60)


class _FailingStallingExitClientSession(_StallingExitClientSession):
    async def initialize(self) -> None:
        raise RuntimeError("startup failed")


class _CancelledClientSession(_StallingClientSession):
    async def initialize(self) -> None:
        raise asyncio.CancelledError()


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


class _GroupedUnauthorizedClientSession(_UnauthorizedClientSession):
    async def initialize(self) -> None:
        exception_group_cls = getattr(builtins, "ExceptionGroup", None)
        if exception_group_cls is None:
            raise _UnauthorizedMCPError(
                "401 Unauthorized: WWW-Authenticate Bearer resource_metadata"
            )
        raise exception_group_cls(
            "unhandled errors in a TaskGroup",
            [
                _UnauthorizedMCPError(
                    "401 Unauthorized: WWW-Authenticate Bearer resource_metadata"
                )
            ],
        )


@asynccontextmanager
async def _fake_http_transport(url: str, **kwargs):
    _ = url, kwargs
    yield "read-stream", "write-stream"


@asynccontextmanager
async def _stalling_exit_transport(url: str, **kwargs):
    _ = url, kwargs
    try:
        yield "read-stream", "write-stream"
    finally:
        await asyncio.sleep(60)


@asynccontextmanager
async def _failing_exit_transport(url: str, **kwargs):
    _ = url, kwargs
    try:
        yield "read-stream", "write-stream"
    finally:
        raise RuntimeError("Attempted to exit cancel scope in a different task")


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
async def test_runtime_manager_startup_timeout_does_not_wait_forever_for_cleanup(
    monkeypatch,
) -> None:
    monkeypatch.setattr(runtime_mod, "DEFAULT_CLEANUP_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(
        runtime_mod,
        "_resolve_sdk_primitives",
        lambda transport: (_StallingExitClientSession, _stalling_exit_transport),
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
    snapshot = manager.status_snapshot()[0]
    assert snapshot.state == "failed"
    assert snapshot.error
    assert "timed out" in snapshot.error.lower()


@pytest.mark.asyncio
async def test_runtime_manager_startup_error_does_not_wait_forever_for_cleanup(
    monkeypatch,
) -> None:
    monkeypatch.setattr(runtime_mod, "DEFAULT_CLEANUP_TIMEOUT_SECONDS", 0.05)
    monkeypatch.setattr(
        runtime_mod,
        "_resolve_sdk_primitives",
        lambda transport: (_FailingStallingExitClientSession, _stalling_exit_transport),
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

    started_at = time.monotonic()
    await asyncio.wait_for(manager.start(config), timeout=1)
    elapsed = time.monotonic() - started_at

    assert elapsed < 0.8
    snapshot = manager.status_snapshot()[0]
    assert snapshot.state == "failed"
    assert snapshot.error == "startup failed"


@pytest.mark.asyncio
async def test_runtime_manager_contains_cancelled_startup_when_not_fatal(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runtime_mod,
        "_resolve_sdk_primitives",
        lambda transport: (_CancelledClientSession, _fake_http_transport),
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

    await asyncio.wait_for(manager.start(config), timeout=1)

    assert await manager.list_tools() == []
    snapshot = manager.status_snapshot()[0]
    assert snapshot.state == "failed"
    assert snapshot.error == "MCP server startup was cancelled."


@pytest.mark.asyncio
async def test_runtime_manager_marks_cancelled_http_auth_challenge_as_auth_required(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runtime_mod,
        "_resolve_sdk_primitives",
        lambda transport: (_CancelledClientSession, _fake_http_transport),
    )

    async def fake_requires_auth(spec):
        assert spec.name == "protected"
        return True

    monkeypatch.setattr(runtime_mod, "_http_server_requires_auth", fake_requires_auth)

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

    await asyncio.wait_for(manager.start(config), timeout=1)

    assert await manager.list_tools() == []
    snapshot = manager.status_snapshot()[0]
    assert snapshot.state == "auth_required"
    assert snapshot.error
    assert "Authentication required" in snapshot.error


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


@pytest.mark.asyncio
async def test_runtime_manager_marks_grouped_unauthorized_startup_as_auth_required(
    monkeypatch,
) -> None:
    monkeypatch.setattr(
        runtime_mod,
        "_resolve_sdk_primitives",
        lambda transport: (_GroupedUnauthorizedClientSession, _fake_http_transport),
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
    assert "authentication required" in snapshot.error.lower()


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


@pytest.mark.asyncio
async def test_runtime_manager_close_does_not_wait_forever_for_cleanup(
    monkeypatch,
) -> None:
    monkeypatch.setattr(runtime_mod, "DEFAULT_CLEANUP_TIMEOUT_SECONDS", 0.05)

    spec = MCPServerRuntimeSpec(
        name="protected",
        enabled=True,
        transport="http",
        url="http://127.0.0.1:1/mcp",
    )
    stack = AsyncExitStack()
    await stack.enter_async_context(_stalling_exit_transport("http://127.0.0.1:1/mcp"))
    manager = MCPRuntimeManager()
    manager._entries["protected"] = runtime_mod._RuntimeEntry(  # noqa: SLF001
        spec=spec,
        stack=stack,
        session=object(),
        tools=[],
    )

    started_at = time.monotonic()
    await asyncio.wait_for(manager.close(), timeout=1)
    elapsed = time.monotonic() - started_at

    assert elapsed < 0.8
    assert manager.status_snapshot() == []


@pytest.mark.asyncio
async def test_runtime_manager_close_suppresses_cleanup_errors() -> None:
    spec = MCPServerRuntimeSpec(
        name="protected",
        enabled=True,
        transport="http",
        url="http://127.0.0.1:1/mcp",
    )
    stack = AsyncExitStack()
    await stack.enter_async_context(_failing_exit_transport("http://127.0.0.1:1/mcp"))
    manager = MCPRuntimeManager()
    manager._entries["protected"] = runtime_mod._RuntimeEntry(  # noqa: SLF001
        spec=spec,
        stack=stack,
        session=object(),
        tools=[],
    )

    await asyncio.wait_for(manager.close(), timeout=1)

    assert manager.status_snapshot() == []


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
