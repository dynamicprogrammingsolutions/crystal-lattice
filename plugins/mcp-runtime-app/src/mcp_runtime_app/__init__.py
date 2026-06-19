from __future__ import annotations

import secrets
from typing import Any, Dict, List, Optional
from urllib.parse import quote, urlencode, urljoin

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
from mcp.shared.auth import OAuthClientInformationFull, OAuthClientMetadata
from mcp_shared import (
    MCP_OAUTH_PENDING_STORE_KEY,
    MCP_OAUTH_TOKENS_STORE_KEY,
    get_runtime_store_mapping,
    set_runtime_store_mapping,
)


class MCPRuntimeAppPlugin:
    name = "mcp_runtime_app"
    version = "0.1.0"

    runtime_store_key = "mcp_registry"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = (state, tags, models)
        if isinstance(config, dict):
            servers = config.get("mcp_servers")
            if not bool(config.get("mcp_enabled")):
                return []
            if not isinstance(servers, dict) or not servers:
                return []
        return [
            {
                "ui_type": "session_action",
                "id": "mcp_show_status",
                "label": "MCP status",
                "icon": "plug",
                "order": 70,
                "action_id": "mcp_show_status",
                "fixed_params": {},
                "param_map": {
                    "session_id": "$session.session_id",
                    "connection_id": "$context.connectionId",
                },
            },
            {
                "ui_type": "session_action",
                "id": "mcp_reconnect_servers",
                "label": "Reconnect MCP servers",
                "icon": "refresh",
                "order": 71,
                "action_id": "mcp_reconnect_servers",
                "fixed_params": {},
                "param_map": {"session_id": "$session.session_id"},
            },
            {
                "ui_type": "session_action",
                "id": "mcp_clear_runtime",
                "label": "Clear MCP runtime",
                "icon": "trash",
                "order": 72,
                "action_id": "mcp_clear_runtime",
                "fixed_params": {},
                "param_map": {"session_id": "$session.session_id"},
            },
        ]

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        _ = app_config
        return {}

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "mcp_show_status",
                "label": "MCP status",
                "description": "Show the current MCP runtime status snapshot.",
                "inputs": {
                    "session_id": {"type": "string", "required": False},
                    "connection_id": {"type": "string", "required": False},
                },
            },
            {
                "id": "mcp_start_login",
                "label": "Sign in to MCP server",
                "description": "Start OAuth login for an MCP server.",
                "inputs": {
                    "server_name": {"type": "string", "required": True},
                    "connection_id": {"type": "string", "required": True},
                },
            },
            {
                "id": "mcp_complete_login",
                "label": "Complete MCP login",
                "description": "Complete OAuth login for an MCP server.",
                "inputs": {
                    "server_name": {"type": "string", "required": True},
                    "code": {"type": "string", "required": True},
                    "state": {"type": "string", "required": True},
                    "redirect_url": {"type": "string", "required": True},
                },
            },
            {
                "id": "mcp_reconnect_servers",
                "label": "Reconnect MCP servers",
                "description": "Clear MCP runtimes so they reconnect on the next request.",
                "inputs": {
                    "session_id": {"type": "string", "required": False},
                },
            },
            {
                "id": "mcp_clear_runtime",
                "label": "Clear MCP runtime",
                "description": "Clear all stored MCP runtimes immediately.",
                "inputs": {
                    "session_id": {"type": "string", "required": False},
                },
            },
        ]

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = (params, context, state)
        store = app.get_runtime_store()
        registry = store.get(self.runtime_store_key)
        if action_id == "mcp_show_status":
            runtimes = self._collect_runtime_rows(registry)
            display: Dict[str, Any] = {
                "format": "markdown",
                "title": "MCP Runtime Status",
                "body": self._format_status_body(runtimes),
                "variant": "info",
                "presentation": "inline",
                "display_id": "mcp-runtime-status",
            }
            actions = self._status_followup_actions(runtimes, params)
            if actions:
                display["actions"] = actions
            return {
                "display": display,
                "runtimes": runtimes,
            }
        if action_id == "mcp_start_login":
            return app.run_awaitable_blocking(
                self._start_login(app, params=params, context=context)
            )
        if action_id == "mcp_complete_login":
            return app.run_awaitable_blocking(
                self._complete_login(app, params=params, context=context)
            )
        if action_id == "mcp_clear_runtime":
            if registry is None:
                cleared = 0
            else:
                cleared = app.run_awaitable_blocking(registry.clear_all())
            return self._status_message(
                title="MCP runtime cleared",
                body=f"Cleared {cleared} stored MCP runtime(s).",
                cleared=cleared,
            )
        if action_id == "mcp_reconnect_servers":
            if registry is None:
                cleared = 0
            else:
                cleared = app.run_awaitable_blocking(registry.clear_all())
            return self._status_message(
                title="MCP reconnect scheduled",
                body=(
                    f"Cleared {cleared} stored MCP runtime(s). "
                    "The next request will reconnect configured MCP servers."
                ),
                cleared=cleared,
            )
        return {"error": f"Unknown action: {action_id}"}

    def _collect_runtime_rows(self, registry: Any) -> List[Dict[str, Any]]:
        if registry is None:
            return []
        snapshot = getattr(registry, "snapshot", None)
        if not callable(snapshot):
            return []
        rows = snapshot()
        return [dict(row) for row in rows if isinstance(row, dict)]

    def _status_followup_actions(
        self,
        runtimes: List[Dict[str, Any]],
        params: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        connection_id = params.get("connection_id")
        actions: List[Dict[str, Any]] = []
        for runtime in runtimes:
            for server in runtime.get("servers") or []:
                if not isinstance(server, dict):
                    continue
                if server.get("state") != "auth_required":
                    continue
                server_name = server.get("name")
                if not isinstance(server_name, str) or not server_name:
                    continue
                fixed_params: Dict[str, Any] = {"server_name": server_name}
                if isinstance(connection_id, str) and connection_id:
                    fixed_params["connection_id"] = connection_id
                actions.append(
                    {
                        "kind": "run_action",
                        "id": f"mcp-start-login-{server_name}",
                        "label": f"Sign in to {server_name}",
                        "plugin": self.name,
                        "action_id": "mcp_start_login",
                        "fixed_params": fixed_params,
                        "preserve_display": True,
                    }
                )
        return actions

    def _format_status_body(self, runtimes: List[Dict[str, Any]]) -> str:
        if not runtimes:
            return "No MCP runtimes are currently stored."
        lines: List[str] = []
        for runtime in runtimes:
            runtime_key = runtime.get("runtime_key") or "unknown"
            lines.append(f"Runtime `{runtime_key}`")
            for server in runtime.get("servers") or []:
                if not isinstance(server, dict):
                    continue
                name = str(server.get("name") or "unknown")
                state = str(server.get("state") or "unknown")
                tool_count = int(server.get("tool_count") or 0)
                error = server.get("error")
                suffix = f" ({tool_count} tools)"
                if error:
                    suffix += f" - {error}"
                lines.append(f"- `{name}`: {state}{suffix}")
        return "\n".join(lines)

    async def _start_login(
        self,
        app: Any,
        *,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        server_name = params.get("server_name")
        connection_id = params.get("connection_id")
        session_id = context.get("session_id") if isinstance(context, dict) else None
        if not isinstance(server_name, str) or not server_name:
            raise ValueError("server_name must be a non-empty string")
        if not isinstance(connection_id, str) or not connection_id:
            raise ValueError("connection_id must be a non-empty string")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be available in action context")

        raw_spec = self._server_config(context, server_name)
        if raw_spec is None:
            return self._login_error(
                f"MCP server `{server_name}` is not present in the session config."
            )
        server_url = raw_spec.get("url")
        if not isinstance(server_url, str) or not server_url:
            return self._login_error(
                f"MCP server `{server_name}` does not have an HTTP URL."
            )

        redirect_uri = self._build_callback_url(
            connection_id=connection_id,
            session_id=session_id,
            server_name=server_name,
        )

        try:
            login = await self._build_login_request(
                server_name=server_name,
                server_url=server_url,
                raw_spec=raw_spec,
                redirect_uri=redirect_uri,
            )
        except Exception as exc:
            return self._login_error(f"Unable to start MCP login: {exc}")

        runtime_store = app.get_runtime_store()
        pending = get_runtime_store_mapping(runtime_store, MCP_OAUTH_PENDING_STORE_KEY)
        pending[login["state"]] = {
            "server_name": server_name,
            "server_url": server_url,
            "redirect_uri": redirect_uri,
            "token_endpoint": login["token_endpoint"],
            "code_verifier": login["code_verifier"],
            "client_info": login["client_info"],
            "resource": login.get("resource"),
        }
        set_runtime_store_mapping(runtime_store, MCP_OAUTH_PENDING_STORE_KEY, pending)

        authorization_url = login["authorization_url"]
        return {
            "message": f"Open the sign-in link for {server_name}.",
            "authorization_url": authorization_url,
            "display": {
                "format": "markdown",
                "title": f"Sign in to {server_name}",
                "body": "Open the authorization link, then return to Crystal Lattice when the browser redirects back.",
                "variant": "info",
                "presentation": "inline",
                "display_id": f"mcp-login-{server_name}",
                "actions": [
                    {
                        "kind": "open_url",
                        "id": f"open-mcp-login-{server_name}",
                        "label": "Open sign-in",
                        "url": authorization_url,
                    },
                    {
                        "kind": "copy_text",
                        "id": f"copy-mcp-login-{server_name}",
                        "label": "Copy sign-in link",
                        "text": authorization_url,
                        "copied_label": "Copied",
                    },
                ],
            },
        }

    async def _complete_login(
        self,
        app: Any,
        *,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        _ = context
        server_name = params.get("server_name")
        code = params.get("code")
        state = params.get("state")
        if not isinstance(server_name, str) or not server_name:
            raise ValueError("server_name must be a non-empty string")
        if not isinstance(code, str) or not code:
            raise ValueError("code must be a non-empty string")
        if not isinstance(state, str) or not state:
            raise ValueError("state must be a non-empty string")

        runtime_store = app.get_runtime_store()
        pending = get_runtime_store_mapping(runtime_store, MCP_OAUTH_PENDING_STORE_KEY)
        login = pending.get(state)
        if not isinstance(login, dict):
            return self._login_error("No pending MCP login matches this callback.")
        if login.get("server_name") != server_name:
            return self._login_error("MCP login callback server mismatch.")

        try:
            token = await self._exchange_code_for_token(login, code)
        except Exception as exc:
            return self._login_error(f"MCP login failed: {exc}")

        tokens = get_runtime_store_mapping(runtime_store, MCP_OAUTH_TOKENS_STORE_KEY)
        token_payload = token.model_dump(mode="json", exclude_none=True)
        token_payload["server_url"] = login.get("server_url")
        tokens[server_name] = token_payload
        pending.pop(state, None)
        set_runtime_store_mapping(runtime_store, MCP_OAUTH_TOKENS_STORE_KEY, tokens)
        set_runtime_store_mapping(runtime_store, MCP_OAUTH_PENDING_STORE_KEY, pending)

        registry = runtime_store.get(self.runtime_store_key)
        cleared = 0
        if registry is not None:
            cleared = await registry.clear_all()

        return {
            "message": f"Signed in to {server_name}.",
            "server_name": server_name,
            "cleared": cleared,
            "ui_effects": {"reload_sessions_list": True},
            "display": {
                "format": "markdown",
                "title": f"Signed in to {server_name}",
                "body": "MCP runtimes were cleared and will reconnect with the stored token on the next request.",
                "variant": "success",
                "presentation": "inline",
                "display_id": f"mcp-login-complete-{server_name}",
            },
        }

    def _server_config(
        self,
        context: Optional[Dict[str, Any]],
        server_name: str,
    ) -> Optional[Dict[str, Any]]:
        base_config = context.get("base_config") if isinstance(context, dict) else None
        servers = (
            base_config.get("mcp_servers") if isinstance(base_config, dict) else None
        )
        raw_spec = servers.get(server_name) if isinstance(servers, dict) else None
        return dict(raw_spec) if isinstance(raw_spec, dict) else None

    async def _build_login_request(
        self,
        *,
        server_name: str,
        server_url: str,
        raw_spec: Dict[str, Any],
        redirect_uri: str,
    ) -> Dict[str, Any]:
        client_metadata = OAuthClientMetadata(
            redirect_uris=[redirect_uri],
            client_name="Crystal Lattice Control",
        )

        auth_url = raw_spec.get("oauth_authorization_url") or raw_spec.get(
            "authorization_url"
        )
        token_endpoint = raw_spec.get("oauth_token_endpoint") or raw_spec.get(
            "token_endpoint"
        )
        client_id = raw_spec.get("oauth_client_id") or raw_spec.get("client_id")
        if (
            isinstance(auth_url, str)
            and auth_url
            and isinstance(token_endpoint, str)
            and token_endpoint
            and isinstance(client_id, str)
            and client_id
        ):
            client_info = OAuthClientInformationFull(
                client_id=client_id,
                client_secret=(
                    raw_spec.get("oauth_client_secret")
                    if isinstance(raw_spec.get("oauth_client_secret"), str)
                    else None
                ),
                token_endpoint_auth_method=(
                    raw_spec.get("oauth_token_endpoint_auth_method")
                    if raw_spec.get("oauth_token_endpoint_auth_method")
                    in {"none", "client_secret_post", "client_secret_basic"}
                    else "none"
                ),
                redirect_uris=[redirect_uri],
            )
            return self._authorization_payload(
                auth_endpoint=auth_url,
                token_endpoint=token_endpoint,
                client_info=client_info,
                redirect_uri=redirect_uri,
                resource=resource_url_from_server_url(server_url),
                scope=(
                    raw_spec.get("oauth_scope")
                    if isinstance(raw_spec.get("oauth_scope"), str)
                    else None
                ),
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
            if (
                protected_metadata is None
                or not protected_metadata.authorization_servers
            ):
                raise RuntimeError("MCP protected resource metadata was not available")

            auth_server_url = str(protected_metadata.authorization_servers[0])
            oauth_metadata = None
            for url in build_oauth_authorization_server_metadata_discovery_urls(
                auth_server_url,
                server_url,
            ):
                response = await client.send(create_oauth_metadata_request(url))
                should_continue, metadata = await handle_auth_metadata_response(
                    response
                )
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

            client_metadata_url = (
                raw_spec.get("oauth_client_metadata_url")
                if isinstance(raw_spec.get("oauth_client_metadata_url"), str)
                else None
            )
            if should_use_client_metadata_url(oauth_metadata, client_metadata_url):
                client_info = create_client_info_from_metadata_url(
                    client_metadata_url,
                    redirect_uris=client_metadata.redirect_uris,
                )
            else:
                registration_request = create_client_registration_request(
                    oauth_metadata,
                    client_metadata,
                    self._authorization_base_url(auth_server_url or server_url),
                )
                registration_response = await client.send(registration_request)
                client_info = await handle_registration_response(registration_response)

        auth_endpoint = (
            str(oauth_metadata.authorization_endpoint)
            if oauth_metadata is not None and oauth_metadata.authorization_endpoint
            else urljoin(self._authorization_base_url(auth_server_url), "/authorize")
        )
        token_endpoint = (
            str(oauth_metadata.token_endpoint)
            if oauth_metadata is not None and oauth_metadata.token_endpoint
            else urljoin(self._authorization_base_url(auth_server_url), "/token")
        )
        return self._authorization_payload(
            auth_endpoint=auth_endpoint,
            token_endpoint=token_endpoint,
            client_info=client_info,
            redirect_uri=redirect_uri,
            resource=resource_url_from_server_url(server_url),
            scope=client_metadata.scope,
        )

    def _authorization_payload(
        self,
        *,
        auth_endpoint: str,
        token_endpoint: str,
        client_info: OAuthClientInformationFull,
        redirect_uri: str,
        resource: str,
        scope: Optional[str],
    ) -> Dict[str, Any]:
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

    async def _exchange_code_for_token(self, login: Dict[str, Any], code: str):
        client_info_raw = login.get("client_info")
        if not isinstance(client_info_raw, dict):
            raise RuntimeError("pending login is missing client info")
        client_info = OAuthClientInformationFull.model_validate(client_info_raw)
        token_endpoint = login.get("token_endpoint")
        code_verifier = login.get("code_verifier")
        redirect_uri = login.get("redirect_uri")
        if not isinstance(token_endpoint, str) or not token_endpoint:
            raise RuntimeError("pending login is missing token endpoint")
        if not isinstance(code_verifier, str) or not code_verifier:
            raise RuntimeError("pending login is missing PKCE verifier")
        if not isinstance(redirect_uri, str) or not redirect_uri:
            raise RuntimeError("pending login is missing redirect URI")

        token_data: Dict[str, Any] = {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": client_info.client_id,
            "code_verifier": code_verifier,
        }
        resource = login.get("resource")
        if isinstance(resource, str) and resource:
            token_data["resource"] = resource

        method = client_info.token_endpoint_auth_method or "none"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        auth = None
        if method == "client_secret_post" and client_info.client_secret:
            token_data["client_secret"] = client_info.client_secret
        elif method == "client_secret_basic" and client_info.client_secret:
            auth = (client_info.client_id, client_info.client_secret)

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

    def _build_callback_url(
        self,
        *,
        connection_id: str,
        session_id: str,
        server_name: str,
    ) -> str:
        base = "/".join(
            [
                "crystal-lattice://action",
                quote(connection_id, safe=""),
                quote(session_id, safe=""),
                quote(self.name, safe=""),
                "mcp_complete_login",
            ]
        )
        return f"{base}?{urlencode({'server_name': server_name})}"

    def _authorization_base_url(self, url: str) -> str:
        parsed = httpx.URL(url)
        return (
            f"{parsed.scheme}://{parsed.host}{f':{parsed.port}' if parsed.port else ''}"
        )

    def _login_error(self, message: str) -> Dict[str, Any]:
        return {
            "message": message,
            "display": {
                "format": "markdown",
                "title": "MCP login unavailable",
                "body": message,
                "variant": "danger",
                "presentation": "inline",
            },
        }

    def _status_message(self, *, title: str, body: str, cleared: int) -> Dict[str, Any]:
        return {
            "display": {
                "format": "markdown",
                "title": title,
                "body": body,
                "variant": "info",
                "presentation": "inline",
            },
            "cleared": cleared,
        }


__all__ = ["MCPRuntimeAppPlugin"]
