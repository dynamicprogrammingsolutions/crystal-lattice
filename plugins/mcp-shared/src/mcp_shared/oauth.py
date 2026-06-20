from __future__ import annotations

from dataclasses import replace
from typing import Any

from mcp.shared.auth import OAuthClientMetadata

from .runtime import MCPRuntimeConfig, MCPServerRuntimeSpec


MCP_OAUTH_PENDING_STORE_KEY = "mcp_oauth_pending"
MCP_OAUTH_TOKENS_STORE_KEY = "mcp_oauth_tokens"
DEFAULT_OAUTH_CLIENT_NAME = "Crystal Lattice Control"
DEFAULT_OAUTH_CLIENT_URI = "https://crystallattice.dev"
DEFAULT_OAUTH_SOFTWARE_ID = "crystal-lattice-control"
DEFAULT_OAUTH_SOFTWARE_VERSION = "0.1.0"
DEFAULT_OAUTH_TOKEN_ENDPOINT_AUTH_METHOD = "none"


_CLIENT_METADATA_FIELDS = {
    "client_name",
    "client_uri",
    "logo_uri",
    "contacts",
    "tos_uri",
    "policy_uri",
    "jwks_uri",
    "software_id",
    "software_version",
    "token_endpoint_auth_method",
    "grant_types",
    "response_types",
}


_ENDPOINT_FIELDS = {
    "authorization_url",
    "token_endpoint",
    "registration_endpoint",
    "client_id",
    "client_secret",
    "client_metadata_url",
    "scope",
    "redirect_uri",
}


_LEGACY_OAUTH_KEYS = {
    "oauth_authorization_url": "authorization_url",
    "oauth_token_endpoint": "token_endpoint",
    "oauth_registration_endpoint": "registration_endpoint",
    "oauth_client_id": "client_id",
    "oauth_client_secret": "client_secret",
    "oauth_client_metadata_url": "client_metadata_url",
    "oauth_scope": "scope",
    "oauth_redirect_uri": "redirect_uri",
    "authorization_url": "authorization_url",
    "token_endpoint": "token_endpoint",
    "client_id": "client_id",
    "client_secret": "client_secret",
}


def build_oauth_server_config(raw_spec: dict[str, Any]) -> dict[str, Any]:
    """Return normalized MCP OAuth config for one server.

    The nested ``oauth`` object is the canonical shape. Legacy flat keys are
    still accepted so existing local configs keep working while the new shape is
    adopted by docs and tests.
    """

    config: dict[str, Any] = {
        "client_name": DEFAULT_OAUTH_CLIENT_NAME,
        "client_uri": DEFAULT_OAUTH_CLIENT_URI,
        "software_id": DEFAULT_OAUTH_SOFTWARE_ID,
        "software_version": DEFAULT_OAUTH_SOFTWARE_VERSION,
        "token_endpoint_auth_method": DEFAULT_OAUTH_TOKEN_ENDPOINT_AUTH_METHOD,
    }
    for legacy_key, normalized_key in _LEGACY_OAUTH_KEYS.items():
        value = raw_spec.get(legacy_key)
        if value is not None:
            config[normalized_key] = value

    nested = raw_spec.get("oauth")
    if isinstance(nested, dict):
        for key in _CLIENT_METADATA_FIELDS | _ENDPOINT_FIELDS:
            if key in nested:
                value = nested.get(key)
                if value is None:
                    config.pop(key, None)
                else:
                    config[key] = value

    return config


def build_oauth_client_metadata(
    oauth_config: dict[str, Any],
    *,
    redirect_uri: str,
) -> OAuthClientMetadata:
    kwargs: dict[str, Any] = {"redirect_uris": [redirect_uri]}
    for key in _CLIENT_METADATA_FIELDS:
        value = oauth_config.get(key)
        if value is not None:
            kwargs[key] = value
    return OAuthClientMetadata(**kwargs)


def oauth_string(
    oauth_config: dict[str, Any],
    key: str,
    *,
    allowed_values: set[str] | None = None,
) -> str | None:
    value = oauth_config.get(key)
    if not isinstance(value, str) or not value:
        return None
    if allowed_values is not None and value not in allowed_values:
        return None
    return value


def render_oauth_redirect_uri(
    template: str,
    *,
    connection_id: str,
    session_id: str,
    plugin_id: str,
    action_id: str,
    server_name: str,
) -> str:
    values = {
        "connection_id": connection_id,
        "session_id": session_id,
        "plugin_id": plugin_id,
        "action_id": action_id,
        "server_name": server_name,
    }
    try:
        return template.format(**values)
    except KeyError as exc:
        missing = str(exc).strip("'")
        raise ValueError(f"unknown OAuth redirect URI placeholder: {missing}") from exc


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
