"""Generic callback application plugin for deep-link integration tests."""

from __future__ import annotations

from typing import Any
from urllib.parse import quote, urlencode


class GenericCallbackAppPlugin:
    name = "generic_callback_app"
    version = "1.0.0"

    def __init__(self) -> None:
        self.executed: list[dict[str, Any]] = []

    def init(self, app_config: dict[str, Any]) -> dict[str, Any]:
        _ = app_config
        return {}

    def get_config_schema(self) -> dict[str, Any]:
        return {}

    def get_actions(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [
            {
                "id": "start_external_flow",
                "label": "Create callback link",
                "description": "Create a generic external callback link.",
                "inputs": {
                    "connection_id": {"type": "string", "required": True},
                    "result": {"type": "string", "required": False},
                    "nonce": {"type": "string", "required": False},
                    "include_plugin_id": {"type": "boolean", "required": False},
                },
            },
            {
                "id": "complete_external_flow",
                "label": "Complete external flow",
                "description": "Completes a generic external callback flow.",
                "inputs": {
                    "result": {"type": "string", "required": True},
                    "nonce": {"type": "string", "required": False},
                    "redirect_url": {"type": "string", "required": True},
                },
            },
        ]

    def get_ui_elements(
        self,
        state: dict[str, Any],
        config: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        models: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        _ = state, config, tags, models
        return [
            {
                "ui_type": "session_action",
                "id": "generic_callback_start_external_flow",
                "label": "Create callback link",
                "action_id": "start_external_flow",
                "param_map": {
                    "connection_id": "$context.connectionId",
                },
            },
            {
                "ui_type": "session_action_callback",
                "id": "generic_callback_complete_external_flow",
                "label": "Complete generic external flow",
                "action_id": "complete_external_flow",
                "param_map": {
                    "result": "$callback.query.result",
                    "nonce": "$callback.query.nonce",
                    "redirect_url": "$callback.redirect_url",
                },
            },
        ]

    def get_commands(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return []

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: dict[str, Any],
        context: dict[str, Any] | None,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        _ = app, state
        if action_id == "start_external_flow":
            return self._start_external_flow(params, context)
        if action_id == "complete_external_flow":
            return self._complete_external_flow(action_id, params, context)
        raise KeyError(f"Unknown action_id {action_id!r}")

    def _start_external_flow(
        self,
        params: dict[str, Any],
        context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        connection_id = params.get("connection_id")
        if not isinstance(connection_id, str) or not connection_id:
            raise ValueError("connection_id must be a non-empty string")

        session_id = context.get("session_id") if isinstance(context, dict) else None
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be available in action context")

        result = (
            params.get("result")
            if isinstance(params.get("result"), str)
            else "approved"
        )
        nonce = params.get("nonce") if isinstance(params.get("nonce"), str) else "n-123"
        include_plugin_id = params.get("include_plugin_id") is True
        callback_url = self._build_callback_url(
            connection_id=connection_id,
            session_id=session_id,
            result=result,
            nonce=nonce,
            include_plugin_id=include_plugin_id,
        )

        record = {
            "action_id": "start_external_flow",
            "params": dict(params),
            "session_id": session_id,
            "callback_url": callback_url,
        }
        self.executed.append(record)

        return {
            "message": "Generic callback link created",
            "callback_url": callback_url,
            "display": self._link_display_payload(callback_url),
        }

    def _complete_external_flow(
        self,
        action_id: str,
        params: dict[str, Any],
        context: dict[str, Any] | None,
    ) -> dict[str, Any]:
        session_id = context.get("session_id") if isinstance(context, dict) else None
        record = {
            "action_id": action_id,
            "params": dict(params),
            "session_id": session_id,
        }
        self.executed.append(record)
        return {
            "message": "Generic action complete",
            "handled": True,
            "action": action_id,
            "inputs": dict(params),
            "context": {"session_id": session_id},
        }

    def _build_callback_url(
        self,
        *,
        connection_id: str,
        session_id: str,
        result: str,
        nonce: str,
        include_plugin_id: bool,
    ) -> str:
        segments = [
            "crystal-lattice://action",
            quote(connection_id, safe=""),
            quote(session_id, safe=""),
        ]
        if include_plugin_id:
            segments.append(quote(self.name, safe=""))
        segments.append("generic_callback_complete_external_flow")
        return f"{'/'.join(segments)}?{urlencode({'result': result, 'nonce': nonce})}"

    def _link_display_payload(self, callback_url: str) -> dict[str, Any]:
        return {
            "format": "markdown",
            "title": "Generic Callback Link",
            "body": "Copy the generated callback link and route it back to Crystal Lattice.",
            "variant": "info",
            "presentation": "inline",
            "dismissible": True,
            "display_id": "generic-callback-flow",
            "actions": [
                {
                    "kind": "open_url",
                    "id": "open-generic-callback-link",
                    "label": "Open link",
                    "url": callback_url,
                },
                {
                    "kind": "copy_text",
                    "id": "copy-generic-callback-link",
                    "label": "Copy link",
                    "text": callback_url,
                    "copied_label": "Copied",
                },
            ],
        }


__all__ = ["GenericCallbackAppPlugin"]
