from __future__ import annotations

from typing import Any


class DummySessionNotificationPlugin:
    name = "dummy_session_notification"
    version = "1.0.0"

    def init(self, app_config: dict[str, Any]) -> dict[str, Any]:
        _ = app_config
        return {}

    def get_config_schema(self) -> dict[str, Any]:
        return {}

    def get_actions(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [
            {
                "id": "emit_session_notification",
                "label": "Show session notification",
                "inputs": {
                    "presentation": {"type": "string", "required": True},
                    "variant": {"type": "string", "required": True},
                },
            },
            {
                "id": "resolve_session_notification",
                "label": "Resolve session notification",
                "inputs": {},
            },
            {
                "id": "expire_session_notification",
                "label": "Expire session notification",
                "inputs": {},
            },
            {
                "id": "notification_followup",
                "label": "Notification follow-up",
                "inputs": {},
            },
        ]

    def get_ui_elements(
        self, state: dict[str, Any], config=None, context=None
    ) -> list[dict[str, Any]]:
        _ = state, config, context
        return [
            {
                "ui_type": "session_action",
                "id": "emit_session_notification",
                "label": "Demo session notification",
                "action_id": "emit_session_notification",
                "dialog": {
                    "kind": "form",
                    "title": "Session notification demo",
                    "inputs": [
                        {
                            "name": "presentation",
                            "type": "select",
                            "label": "Presentation",
                            "required": True,
                            "options": ["banner", "inline", "modal"],
                            "default": "inline",
                        },
                        {
                            "name": "variant",
                            "type": "select",
                            "label": "Variant",
                            "required": True,
                            "options": ["info", "success", "warning", "error"],
                            "default": "info",
                        },
                    ],
                },
                "param_map": {
                    "presentation": "$dialog.presentation",
                    "variant": "$dialog.variant",
                },
            },
            {
                "ui_type": "session_action",
                "id": "expire_session_notification",
                "label": "Expire demo session notification",
                "action_id": "expire_session_notification",
            },
        ]

    def get_commands(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return []

    def execute_action(
        self, app: Any, action_id: str, params: dict[str, Any], context, state
    ) -> dict[str, Any]:
        _ = state
        session_id = (context or {}).get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("A session context is required")
        if action_id == "notification_followup":
            return {
                "status": "ok",
                "display": {
                    "format": "text",
                    "title": "Follow-up completed",
                    "body": "The demo follow-up action ran.",
                    "variant": "success",
                    "presentation": "banner",
                },
            }
        if action_id in {
            "resolve_session_notification",
            "expire_session_notification",
        }:
            items = app.list_session_notifications(session_id)
            items = [
                item
                for item in items
                if item.get("key") == "dummy:session:notification"
            ]
            if items and action_id == "resolve_session_notification":
                app.resolve_session_notification(
                    session_id, items[-1]["id"], {"action_id": action_id}
                )
            if items and action_id == "expire_session_notification":
                app.expire_session_notification(
                    session_id,
                    items[-1]["id"],
                    reason="demo_action",
                )
            return {"status": "ok"}
        if action_id != "emit_session_notification":
            raise KeyError(action_id)
        presentation = str(params.get("presentation") or "inline")
        variant = str(params.get("variant") or "info")
        stored = app.create_session_notification(
            session_id,
            {
                "key": "dummy:session:notification",
                "severity": variant,
                "title": "Session notification demo",
                "body": f"{variant} notification using {presentation} presentation.",
                "source": {"plugin": self.name},
                "display": {
                    "format": "text",
                    "title": "Session notification demo",
                    "body": f"{variant} notification using {presentation} presentation.",
                    "variant": variant,
                    "presentation": presentation,
                    "dismissible": True,
                    "actions": [
                        {
                            "kind": "run_action",
                            "id": "followup",
                            "label": "Run follow-up",
                            "plugin": self.name,
                            "action_id": "notification_followup",
                            "action_owner": "application",
                        }
                    ],
                },
                "model_visibility": "hidden",
            },
        )
        return {"status": "ok", "notification_id": stored["id"]}


__all__ = ["DummySessionNotificationPlugin"]
