from __future__ import annotations

import secrets
from typing import Any
from urllib.parse import urlencode, urljoin

import httpx
from mcp.client.auth.oauth2 import (
    PKCEParameters,
    build_oauth_authorization_server_metadata_discovery_urls,
    build_protected_resource_metadata_discovery_urls,
    create_client_info_from_metadata_url,
    create_client_registration_request,
    create_oauth_metadata_request,
    extract_resource_metadata_from_www_auth,
    extract_scope_from_www_auth,
    get_client_metadata_scopes,
    handle_auth_metadata_response,
    handle_protected_resource_response,
    handle_registration_response,
    handle_token_response_scopes,
    resource_url_from_server_url,
    should_use_client_metadata_url,
)
from mcp.shared.auth import OAuthClientInformationFull

from .oauth import (
    build_oauth_client_metadata,
    build_oauth_server_config,
    oauth_string,
)


async def build_mcp_oauth_login_request(
    *,
    server_url: str,
    raw_spec: dict[str, Any],
    redirect_uri: str,
) -> dict[str, Any]:
    oauth_config = build_oauth_server_config(raw_spec)
    client_metadata = build_oauth_client_metadata(
        oauth_config,
        redirect_uri=redirect_uri,
    )

    auth_url = oauth_string(oauth_config, "authorization_url")
    token_endpoint = oauth_string(oauth_config, "token_endpoint")
    client_id = oauth_string(oauth_config, "client_id")
    if auth_url and token_endpoint and client_id:
        client_info = OAuthClientInformationFull(
            client_id=client_id,
            client_secret=oauth_string(oauth_config, "client_secret"),
            token_endpoint_auth_method=(
                oauth_string(
                    oauth_config,
                    "token_endpoint_auth_method",
                    allowed_values={
                        "none",
                        "client_secret_post",
                        "client_secret_basic",
                    },
                )
                or "none"
            ),
            redirect_uris=[redirect_uri],
        )
        return _authorization_payload(
            auth_endpoint=auth_url,
            token_endpoint=token_endpoint,
            client_info=client_info,
            redirect_uri=redirect_uri,
            resource=resource_url_from_server_url(server_url),
            scope=oauth_string(oauth_config, "scope"),
        )

    async with httpx.AsyncClient(timeout=15.0) as client:
        challenge = await client.post(
            server_url,
            headers={
                "Accept": "application/json, text/event-stream",
                "Content-Type": "application/json",
            },
            json={
                "jsonrpc": "2.0",
                "id": "mcp-login-probe",
                "method": "initialize",
                "params": {
                    "protocolVersion": "2025-06-18",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "crystal-lattice-control",
                        "version": "0.1.0",
                    },
                },
            },
        )
        if challenge.status_code != 401:
            raise RuntimeError(
                f"MCP server did not request OAuth login (status {challenge.status_code})"
            )

        protected_metadata = None
        prm_urls = build_protected_resource_metadata_discovery_urls(
            extract_resource_metadata_from_www_auth(challenge),
            server_url,
        )
        for url in prm_urls:
            response = await client.send(create_oauth_metadata_request(url))
            protected_metadata = await handle_protected_resource_response(response)
            if protected_metadata is not None:
                break
        if protected_metadata is None or not protected_metadata.authorization_servers:
            raise RuntimeError("MCP protected resource metadata was not available")

        auth_server_url = str(protected_metadata.authorization_servers[0])
        oauth_metadata = None
        for url in build_oauth_authorization_server_metadata_discovery_urls(
            auth_server_url,
            server_url,
        ):
            response = await client.send(create_oauth_metadata_request(url))
            should_continue, metadata = await handle_auth_metadata_response(response)
            if metadata is not None:
                oauth_metadata = metadata
                break
            if not should_continue:
                break

        client_metadata.scope = get_client_metadata_scopes(
            extract_scope_from_www_auth(challenge),
            protected_metadata,
            oauth_metadata,
        )

        client_metadata_url = oauth_string(oauth_config, "client_metadata_url")
        if should_use_client_metadata_url(oauth_metadata, client_metadata_url):
            client_info = create_client_info_from_metadata_url(
                client_metadata_url,
                redirect_uris=client_metadata.redirect_uris,
            )
        else:
            registration_request = create_client_registration_request(
                oauth_metadata,
                client_metadata,
                _authorization_base_url(auth_server_url or server_url),
            )
            registration_response = await client.send(registration_request)
            client_info = await handle_registration_response(registration_response)

    auth_endpoint = (
        str(oauth_metadata.authorization_endpoint)
        if oauth_metadata is not None and oauth_metadata.authorization_endpoint
        else urljoin(_authorization_base_url(auth_server_url), "/authorize")
    )
    token_endpoint = (
        str(oauth_metadata.token_endpoint)
        if oauth_metadata is not None and oauth_metadata.token_endpoint
        else urljoin(_authorization_base_url(auth_server_url), "/token")
    )
    return _authorization_payload(
        auth_endpoint=auth_endpoint,
        token_endpoint=token_endpoint,
        client_info=client_info,
        redirect_uri=redirect_uri,
        resource=resource_url_from_server_url(server_url),
        scope=client_metadata.scope,
    )


async def build_mcp_oauth_pending_login(
    *,
    server_name: str,
    server_url: str,
    raw_spec: dict[str, Any],
    redirect_uri: str,
    connection_id: str | None = None,
) -> dict[str, Any]:
    login = await build_mcp_oauth_login_request(
        server_url=server_url,
        raw_spec=raw_spec,
        redirect_uri=redirect_uri,
    )
    pending = {
        "server_name": server_name,
        "server_url": server_url,
        "redirect_uri": redirect_uri,
        "token_endpoint": login["token_endpoint"],
        "code_verifier": login["code_verifier"],
        "client_info": login["client_info"],
        "resource": login.get("resource"),
        "oauth_config": build_oauth_server_config(raw_spec),
    }
    if connection_id:
        pending["connection_id"] = connection_id
    return {
        "authorization_url": login["authorization_url"],
        "state": login["state"],
        "pending": pending,
    }


def build_mcp_oauth_token_request(
    *,
    pending_login: dict[str, Any],
    code: str,
) -> tuple[dict[str, Any], dict[str, str], tuple[str, str] | None]:
    client_info_raw = pending_login.get("client_info")
    if not isinstance(client_info_raw, dict):
        raise RuntimeError("pending login is missing client info")
    client_info = OAuthClientInformationFull.model_validate(client_info_raw)
    token_endpoint = pending_login.get("token_endpoint")
    code_verifier = pending_login.get("code_verifier")
    redirect_uri = pending_login.get("redirect_uri")
    if not isinstance(token_endpoint, str) or not token_endpoint:
        raise RuntimeError("pending login is missing token endpoint")
    if not isinstance(code_verifier, str) or not code_verifier:
        raise RuntimeError("pending login is missing PKCE verifier")
    if not isinstance(redirect_uri, str) or not redirect_uri:
        raise RuntimeError("pending login is missing redirect URI")

    token_data: dict[str, Any] = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_info.client_id,
        "code_verifier": code_verifier,
    }
    oauth_config = pending_login.get("oauth_config")
    oauth_config = oauth_config if isinstance(oauth_config, dict) else {}
    token_exchange = oauth_config.get("token_exchange")
    token_exchange = token_exchange if isinstance(token_exchange, dict) else {}

    resource = pending_login.get("resource")
    if token_exchange.get("include_resource") is not False and isinstance(resource, str) and resource:
        token_data["resource"] = resource

    method = client_info.token_endpoint_auth_method or "none"
    headers = {
        "Accept": "application/json, application/x-www-form-urlencoded",
        "Content-Type": "application/x-www-form-urlencoded",
    }
    auth = None
    if method == "client_secret_basic" and client_info.client_secret:
        auth = (client_info.client_id, client_info.client_secret)
    elif (
        method == "client_secret_post"
        or token_exchange.get("include_client_secret") is True
    ) and client_info.client_secret:
        token_data["client_secret"] = client_info.client_secret

    return token_data, headers, auth


async def exchange_mcp_oauth_code_for_token(
    *,
    pending_login: dict[str, Any],
    code: str,
):
    token_endpoint = pending_login.get("token_endpoint")
    if not isinstance(token_endpoint, str) or not token_endpoint:
        raise RuntimeError("pending login is missing token endpoint")
    token_data, headers, auth = build_mcp_oauth_token_request(
        pending_login=pending_login,
        code=code,
    )
    async with httpx.AsyncClient(timeout=15.0) as client:
        response = await client.post(
            token_endpoint,
            data=token_data,
            headers=headers,
            auth=auth,
        )
        if response.status_code != 200:
            body = response.text
            raise RuntimeError(
                f"token exchange failed ({response.status_code}): {body}"
            )
        return await handle_token_response_scopes(response)


def _authorization_payload(
    *,
    auth_endpoint: str,
    token_endpoint: str,
    client_info: OAuthClientInformationFull,
    redirect_uri: str,
    resource: str,
    scope: str | None,
) -> dict[str, Any]:
    pkce = PKCEParameters.generate()
    state = secrets.token_urlsafe(32)
    if not isinstance(client_info.client_id, str) or not client_info.client_id:
        raise RuntimeError("OAuth client registration did not return a client id")
    params = {
        "response_type": "code",
        "client_id": client_info.client_id,
        "redirect_uri": redirect_uri,
        "state": state,
        "code_challenge": pkce.code_challenge,
        "code_challenge_method": "S256",
        "resource": resource,
    }
    if scope:
        params["scope"] = scope
    return {
        "authorization_url": f"{auth_endpoint}?{urlencode(params)}",
        "token_endpoint": token_endpoint,
        "code_verifier": pkce.code_verifier,
        "state": state,
        "client_info": client_info.model_dump(mode="json", exclude_none=True),
        "resource": resource,
    }


def _authorization_base_url(url: str) -> str:
    parsed = httpx.URL(url)
    return f"{parsed.scheme}://{parsed.host}{f':{parsed.port}' if parsed.port else ''}"