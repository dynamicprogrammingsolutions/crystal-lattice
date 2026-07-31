from __future__ import annotations

from typing import Any


_PRESENTATIONS = ["banner", "modal"]
_VARIANTS = ["info", "success", "warning", "error"]


def _dialog() -> dict[str, Any]:
    return {
        "kind": "form",
        "title": "Application notification demo",
        "inputs": [
            {
                "name": "presentation",
                "type": "select",
                "label": "Presentation",
                "required": True,
                "options": _PRESENTATIONS,
                "default": "banner",
            },
            {
                "name": "variant",
                "type": "select",
                "label": "Variant",
                "required": True,
                "options": _VARIANTS,
                "default": "info",
            },
        ],
    }


class DummyApplicationNotificationPlugin:
    name = "dummy_application_notification"
    version = "1.0.0"

    def init(self, app_config: dict[str, Any]) -> dict[str, Any]:
        _ = app_config
        return {}

    def get_config_schema(self) -> dict[str, Any]:
        return {}

    def get_actions(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        inputs = {
            "presentation": {"type": "string", "required": True},
            "variant": {"type": "string", "required": True},
        }
        return [
            {
                "id": "emit_application_notification",
                "label": "Show application notification",
                "inputs": inputs,
            },
            {
                "id": "resolve_application_notification",
                "label": "Resolve application notification",
                "inputs": {},
            },
        ]

    def get_ui_elements(
        self, state: dict[str, Any], config=None, context=None
    ) -> list[dict[str, Any]]:
        _ = state, config, context
        return [
            {
                "ui_type": "application_action",
                "id": "emit_application_notification",
                "label": "Demo application notification",
                "icon": "bell",
                "action_id": "emit_application_notification",
                "dialog": _dialog(),
                "param_map": {
                    "presentation": "$dialog.presentation",
                    "variant": "$dialog.variant",
                },
            },
            {
                "ui_type": "application_action",
                "id": "resolve_application_notification",
                "label": "Resolve demo application notification",
                "icon": "check",
                "action_id": "resolve_application_notification",
            },
        ]

    def get_commands(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return []

    def execute_action(
        self, app: Any, action_id: str, params: dict[str, Any], context, state
    ) -> dict[str, Any]:
        _ = context, state
        if action_id == "resolve_application_notification":
            items = [
                item
                for item in app.list_application_notifications()
                if item.get("key") == "dummy:application:notification"
                and item.get("status") == "pending"
            ]
            if not items:
                return {"status": "ok", "message": "No pending demo notification."}
            app.resolve_application_notification(
                items[-1]["id"], {"action_id": action_id}
            )
            return {"status": "ok", "message": "Demo notification resolved."}
        if action_id != "emit_application_notification":
            raise KeyError(action_id)
        presentation = str(params.get("presentation") or "banner")
        variant = str(params.get("variant") or "info")
        notification = app.create_application_notification(
            {
                "key": "dummy:application:notification",
                "severity": variant,
                "title": "Application notification demo",
                "body": f"{variant} notification using {presentation} presentation.",
                "source": {"plugin": self.name},
                "display": {
                    "format": "text",
                    "title": "Application notification demo",
                    "body": f"{variant} notification using {presentation} presentation.",
                    "variant": variant,
                    "presentation": presentation,
                    "dismissible": True,
                },
                "model_visibility": "hidden",
            }
        )
        return {"status": "ok", "notification_id": notification["id"]}


__all__ = ["DummyApplicationNotificationPlugin"]
