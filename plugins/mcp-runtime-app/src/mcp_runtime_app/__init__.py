from __future__ import annotations

from typing import Any, Dict, List, Optional


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
                "param_map": {"session_id": "$session.session_id"},
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
            return {
                "display": {
                    "format": "markdown",
                    "title": "MCP Runtime Status",
                    "body": self._format_status_body(runtimes),
                    "variant": "info",
                    "presentation": "inline",
                    "display_id": "mcp-runtime-status",
                },
                "runtimes": runtimes,
            }
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