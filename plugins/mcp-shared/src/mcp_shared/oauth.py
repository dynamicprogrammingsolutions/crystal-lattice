from __future__ import annotations

from dataclasses import replace
from typing import Any

from .runtime import MCPRuntimeConfig, MCPServerRuntimeSpec


MCP_OAUTH_PENDING_STORE_KEY = "mcp_oauth_pending"
MCP_OAUTH_TOKENS_STORE_KEY = "mcp_oauth_tokens"


def get_runtime_store_mapping(runtime_store: Any, key: str) -> dict[str, Any]:
    if runtime_store is None:
        return {}
    getter = getattr(runtime_store, "get", None)
    if not callable(getter):
        return {}
    value = getter(key, {})
    return value if isinstance(value, dict) else {}


def set_runtime_store_mapping(
    runtime_store: Any, key: str, value: dict[str, Any]
) -> None:
    if isinstance(runtime_store, dict):
        runtime_store[key] = dict(value)
        return
    setter = getattr(runtime_store, "set", None)
    if callable(setter):
        setter(key, dict(value))
        return
    if hasattr(runtime_store, "items") and isinstance(runtime_store.items, dict):
        runtime_store.items[key] = dict(value)


def apply_oauth_tokens_to_runtime_config(
    config: MCPRuntimeConfig,
    runtime_store: Any,
) -> MCPRuntimeConfig:
    tokens = get_runtime_store_mapping(runtime_store, MCP_OAUTH_TOKENS_STORE_KEY)
    if not tokens:
        return config

    updated_servers: dict[str, MCPServerRuntimeSpec] = {}
    changed = False
    for server_name, spec in config.servers.items():
        token_entry = tokens.get(server_name)
        access_token = (
            token_entry.get("access_token") if isinstance(token_entry, dict) else None
        )
        if not isinstance(access_token, str) or not access_token:
            updated_servers[server_name] = spec
            continue

        headers = dict(spec.headers)
        headers["Authorization"] = f"Bearer {access_token}"
        updated_servers[server_name] = replace(spec, headers=headers)
        changed = True

    if not changed:
        return config
    return replace(config, servers=updated_servers)
