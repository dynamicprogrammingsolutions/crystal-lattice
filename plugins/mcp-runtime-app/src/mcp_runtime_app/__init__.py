from __future__ import annotations

from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, quote, urlencode, urlparse

from mcp_shared import (
    MCP_OAUTH_PENDING_STORE_KEY,
    MCP_OAUTH_TOKENS_STORE_KEY,
    MCPRegistry,
    apply_oauth_tokens_to_runtime_config,
    build_oauth_server_config,
    build_mcp_oauth_pending_login,
    build_runtime_config_from_config,
    exchange_mcp_oauth_code_for_token,
    fingerprint_runtime_config,
    get_runtime_store_mapping,
    oauth_string,
    render_oauth_redirect_uri,
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
                "id": "mcp_check_servers",
                "label": "Check MCP servers",
                "icon": "activity",
                "order": 71,
                "action_id": "mcp_check_servers",
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
                "order": 72,
                "action_id": "mcp_reconnect_servers",
                "fixed_params": {},
                "param_map": {
                    "session_id": "$session.session_id",
                    "connection_id": "$context.connectionId",
                },
            },
            {
                "ui_type": "session_action",
                "id": "mcp_clear_runtime",
                "label": "Clear MCP runtime",
                "icon": "trash",
                "order": 73,
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
                    "code": {"type": "string", "required": False},
                    "state": {"type": "string", "required": False},
                    "redirect_url": {"type": "string", "required": False},
                },
            },
            {
                "id": "mcp_show_finish_login",
                "label": "Finish MCP login",
                "description": "Show a form for completing MCP OAuth login from a browser callback URL.",
                "inputs": {
                    "server_name": {"type": "string", "required": True},
                },
            },
            {
                "id": "mcp_reconnect_servers",
                "label": "Reconnect MCP servers",
                "description": "Clear MCP runtimes, reconnect configured servers, and show fresh status.",
                "inputs": {
                    "session_id": {"type": "string", "required": False},
                    "connection_id": {"type": "string", "required": False},
                },
            },
            {
                "id": "mcp_check_servers",
                "label": "Check MCP servers",
                "description": "Connect configured MCP servers if needed and show fresh status.",
                "inputs": {
                    "session_id": {"type": "string", "required": False},
                    "connection_id": {"type": "string", "required": False},
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
        if action_id == "mcp_show_finish_login":
            return self._show_finish_login(params=params)
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
        if action_id == "mcp_check_servers":
            return app.run_awaitable_blocking(
                self._check_servers(app, params=params, context=context, clear=False)
            )
        if action_id == "mcp_reconnect_servers":
            return app.run_awaitable_blocking(
                self._check_servers(app, params=params, context=context, clear=True)
            )
        return {"error": f"Unknown action: {action_id}"}

    async def _check_servers(
        self,
        app: Any,
        *,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        clear: bool,
    ) -> Dict[str, Any]:
        runtime_store = app.get_runtime_store()
        registry = runtime_store.get(self.runtime_store_key)
        cleared = 0
        if clear and registry is not None:
            cleared = await registry.clear_all()

        config = self._effective_config(context)
        if not isinstance(config, dict):
            return self._status_message(
                title="MCP status unavailable",
                body="The session configuration was not available for this action.",
                cleared=cleared,
            )
        if not bool(config.get("mcp_enabled", True)):
            return self._status_message(
                title="MCP servers disabled",
                body="MCP is disabled for this session.",
                cleared=cleared,
            )

        runtime_config = build_runtime_config_from_config(config)
        if not runtime_config.servers:
            return self._status_message(
                title="No MCP servers configured",
                body="This session does not have configured MCP servers.",
                cleared=cleared,
            )

        runtime_config = apply_oauth_tokens_to_runtime_config(
            runtime_config,
            runtime_store,
        )
        runtime_key = fingerprint_runtime_config(runtime_config)
        registry = runtime_store.get_or_create(
            self.runtime_store_key,
            lambda: MCPRegistry(app=app),
        )
        await registry.list_tools(runtime_key, runtime_config)
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
            "cleared": cleared,
            "runtime_key": runtime_key,
        }

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
            raw_spec=raw_spec,
            connection_id=connection_id,
            session_id=session_id,
            server_name=server_name,
        )

        try:
            login = await self._build_pending_login(
                server_name=server_name,
                server_url=server_url,
                raw_spec=raw_spec,
                redirect_uri=redirect_uri,
                connection_id=connection_id,
            )
        except Exception as exc:
            return self._login_error(f"Unable to start MCP login: {exc}")

        runtime_store = app.get_runtime_store()
        pending = get_runtime_store_mapping(runtime_store, MCP_OAUTH_PENDING_STORE_KEY)
        pending[login["state"]] = login["pending"]
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
                    {
                        "kind": "run_action",
                        "id": f"finish-mcp-login-{server_name}",
                        "label": "Finish login",
                        "plugin": self.name,
                        "action_id": "mcp_show_finish_login",
                        "fixed_params": {"server_name": server_name},
                        "preserve_display": True,
                    },
                ],
            },
        }

    def _show_finish_login(self, *, params: Dict[str, Any]) -> Dict[str, Any]:
        server_name = params.get("server_name")
        if not isinstance(server_name, str) or not server_name:
            raise ValueError("server_name must be a non-empty string")

        return {
            "message": f"Paste the MCP callback URL for {server_name}.",
            "display": {
                "format": "markdown",
                "title": f"Finish sign-in to {server_name}",
                "body": (
                    "Paste the full callback URL from the browser after approving "
                    "the MCP login."
                ),
                "variant": "info",
                "presentation": "inline",
                "display_id": f"mcp-login-finish-{server_name}",
                "form": {
                    "kind": "form",
                    "inputs": [
                        {
                            "name": "redirect_url",
                            "type": "multiline",
                            "label": "Callback URL",
                            "placeholder": "http://localhost:41793/oauth/callback?code=...&state=...",
                            "required": True,
                        }
                    ],
                },
                "actions": [
                    {
                        "kind": "run_action",
                        "id": f"submit-mcp-login-callback-{server_name}",
                        "label": "Submit",
                        "plugin": self.name,
                        "action_id": "mcp_complete_login",
                        "fixed_params": {"server_name": server_name},
                        "param_map": {"redirect_url": "$form.redirect_url"},
                        "preserve_display": False,
                    },
                    {
                        "kind": "dismiss",
                        "id": f"cancel-mcp-login-callback-{server_name}",
                        "label": "Cancel",
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

        redirect_url = params.get("redirect_url")
        if isinstance(redirect_url, str) and redirect_url:
            parsed = self._parse_callback_url(redirect_url)
            code = parsed.get("code")
            state = parsed.get("state")

        if not isinstance(code, str) or not code:
            return self._login_error(
                "MCP login callback URL is missing an authorization code."
            )
        if not isinstance(state, str) or not state:
            return self._login_error("MCP login callback URL is missing state.")

        runtime_store = app.get_runtime_store()
        pending = get_runtime_store_mapping(runtime_store, MCP_OAUTH_PENDING_STORE_KEY)
        login = pending.get(state)
        if not isinstance(login, dict):
            tokens = get_runtime_store_mapping(
                runtime_store, MCP_OAUTH_TOKENS_STORE_KEY
            )
            token_entry = tokens.get(server_name)
            if (
                isinstance(token_entry, dict)
                and isinstance(token_entry.get("access_token"), str)
                and token_entry.get("access_token")
            ):
                return self._login_success_result(
                    server_name=server_name,
                    cleared=0,
                    refreshed=None,
                    body="The MCP server is already signed in.",
                )
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
        cleanup_error = None
        if registry is not None:
            try:
                cleared = await registry.clear_all()
            except Exception as exc:
                cleanup_error = str(exc) or type(exc).__name__

        refreshed = None
        if isinstance(self._effective_config(context), dict):
            try:
                check_params: Dict[str, Any] = {}
                connection_id = login.get("connection_id")
                if isinstance(connection_id, str) and connection_id:
                    check_params["connection_id"] = connection_id
                refreshed = await self._check_servers(
                    app,
                    params=check_params,
                    context=context,
                    clear=False,
                )
            except Exception as exc:
                cleanup_error = cleanup_error or (str(exc) or type(exc).__name__)

        body = (
            "MCP runtimes were refreshed with the stored token."
            if refreshed is not None
            else "MCP runtimes will reconnect with the stored token on the next request."
        )
        if cleanup_error:
            body += (
                "\n\nThe token was stored, but runtime refresh will be retried later."
            )

        return self._login_success_result(
            server_name=server_name,
            cleared=cleared,
            refreshed=refreshed,
            body=body,
        )

    def _parse_callback_url(self, redirect_url: str) -> Dict[str, str]:
        parsed = urlparse(redirect_url)
        query = parse_qs(parsed.query)
        values: Dict[str, str] = {}
        for key in ("code", "state"):
            first = query.get(key, [None])[0]
            if isinstance(first, str) and first:
                values[key] = first
        return values

    def _login_success_result(
        self,
        *,
        server_name: str,
        cleared: int,
        refreshed: Optional[Dict[str, Any]],
        body: str,
    ) -> Dict[str, Any]:
        display = {
            "format": "markdown",
            "title": f"Signed in to {server_name}",
            "body": body,
            "variant": "success",
            "presentation": "inline",
            "display_id": f"mcp-login-complete-{server_name}",
        }
        if isinstance(refreshed, dict):
            refreshed_display = refreshed.get("display")
            if isinstance(refreshed_display, dict):
                refreshed_body = refreshed_display.get("body")
                if isinstance(refreshed_body, str) and refreshed_body:
                    display["body"] = f"{body}\n\n{refreshed_body}"
                actions = refreshed_display.get("actions")
                if isinstance(actions, list) and actions:
                    display["actions"] = actions

        result = {
            "message": f"Signed in to {server_name}.",
            "server_name": server_name,
            "cleared": cleared,
            "ui_effects": {"reload_sessions_list": True},
            "display": display,
        }
        if isinstance(refreshed, dict):
            result["runtimes"] = refreshed.get("runtimes", [])
            result["runtime_key"] = refreshed.get("runtime_key")
        return result

    def _server_config(
        self,
        context: Optional[Dict[str, Any]],
        server_name: str,
    ) -> Optional[Dict[str, Any]]:
        config = self._effective_config(context)
        servers = config.get("mcp_servers") if isinstance(config, dict) else None
        raw_spec = servers.get(server_name) if isinstance(servers, dict) else None
        return dict(raw_spec) if isinstance(raw_spec, dict) else None

    def _effective_config(
        self,
        context: Optional[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        if not isinstance(context, dict):
            return None
        config = context.get("config")
        if isinstance(config, dict):
            return config
        base_config = context.get("base_config")
        if isinstance(base_config, dict):
            return base_config
        return None

    async def _build_pending_login(
        self,
        *,
        server_name: str,
        server_url: str,
        raw_spec: Dict[str, Any],
        redirect_uri: str,
        connection_id: str | None = None,
    ) -> Dict[str, Any]:
        return await build_mcp_oauth_pending_login(
            server_name=server_name,
            server_url=server_url,
            raw_spec=raw_spec,
            redirect_uri=redirect_uri,
            connection_id=connection_id,
        )

    async def _exchange_code_for_token(self, login: Dict[str, Any], code: str):
        return await exchange_mcp_oauth_code_for_token(
            pending_login=login,
            code=code,
        )

    def _build_callback_url(
        self,
        *,
        raw_spec: Dict[str, Any],
        connection_id: str,
        session_id: str,
        server_name: str,
    ) -> str:
        oauth_config = build_oauth_server_config(raw_spec)
        template = oauth_string(oauth_config, "redirect_uri")
        if template:
            return render_oauth_redirect_uri(
                template,
                connection_id=connection_id,
                session_id=session_id,
                plugin_id=self.name,
                action_id="mcp_complete_login",
                server_name=server_name,
            )
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

    def _login_error(self, message: str) -> Dict[str, Any]:
        return {
            "message": message,
            "display": {
                "format": "markdown",
                "title": "MCP login unavailable",
                "body": message,
                "variant": "error",
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
