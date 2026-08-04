from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any


_PRESENTATIONS = ["banner", "modal"]
_VARIANTS = ["info", "success", "warning", "error"]
_RETENTION_POLICIES = ["until_resolved", "ttl", "until_server_restart"]
_FOLLOWUP_OPTIONS = ["none", "one", "multiple"]


def _followup_actions(params: dict[str, Any]) -> list[dict[str, Any]]:
    mode = str(params.get("followup_buttons") or "none")
    if mode not in _FOLLOWUP_OPTIONS:
        raise ValueError(f"Unsupported follow-up button mode: {mode}")
    count = 0 if mode == "none" else 1 if mode == "one" else 3
    return [
        {
            "kind": "run_action",
            "id": f"followup_{index}",
            "label": f"Follow-up {index}",
            "plugin": "dummy_application_notification",
            "action_id": "notification_followup",
            "action_owner": "application",
            "fixed_params": {
                "presentation": params.get("presentation"),
                "variant": params.get("variant"),
                "followup_index": index,
            },
        }
        for index in range(1, count + 1)
    ]


def _retention(params: dict[str, Any]) -> dict[str, Any]:
    policy = str(params.get("retention") or "until_resolved")
    if policy not in _RETENTION_POLICIES:
        raise ValueError(f"Unsupported notification retention policy: {policy}")
    if policy != "ttl":
        return {"policy": policy}
    ttl_seconds = params.get("ttl_seconds", 60)
    if (
        not isinstance(ttl_seconds, int)
        or isinstance(ttl_seconds, bool)
        or ttl_seconds <= 0
    ):
        raise ValueError("ttl_seconds must be a positive integer")
    expires_at = datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)
    return {
        "policy": "ttl",
        "expires_at": expires_at.isoformat().replace("+00:00", "Z"),
    }


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
            {
                "name": "retention",
                "type": "select",
                "label": "Retention",
                "required": True,
                "options": _RETENTION_POLICIES,
                "default": "until_resolved",
            },
            {
                "name": "ttl_seconds",
                "type": "integer",
                "label": "TTL seconds",
                "required": False,
                "default": 60,
            },
            {
                "name": "followup_buttons",
                "type": "select",
                "label": "Follow-up buttons",
                "required": True,
                "options": _FOLLOWUP_OPTIONS,
                "default": "none",
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
            "retention": {"type": "string", "required": False},
            "ttl_seconds": {"type": "integer", "required": False},
            "followup_buttons": {"type": "string", "required": False},
        }
        return [
            {
                "id": "notification_followup",
                "label": "Notification follow-up",
                "inputs": {
                    "presentation": {"type": "string", "required": True},
                    "variant": {"type": "string", "required": True},
                    "followup_index": {"type": "integer", "required": False},
                },
            },
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
            {
                "id": "expire_application_notification",
                "label": "Expire application notification",
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
                    "retention": "$dialog.retention",
                    "ttl_seconds": "$dialog.ttl_seconds",
                    "followup_buttons": "$dialog.followup_buttons",
                },
            },
            {
                "ui_type": "application_action",
                "id": "resolve_application_notification",
                "label": "Resolve demo application notification",
                "icon": "check",
                "action_id": "resolve_application_notification",
            },
            {
                "ui_type": "application_action",
                "id": "expire_application_notification",
                "label": "Expire demo application notification",
                "icon": "clock",
                "action_id": "expire_application_notification",
            },
        ]

    def get_commands(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return []

    def execute_action(
        self, app: Any, action_id: str, params: dict[str, Any], context, state
    ) -> dict[str, Any]:
        _ = context, state
        if action_id == "notification_followup":
            presentation = str(params.get("presentation") or "banner")
            variant = str(params.get("variant") or "info")
            index = int(params.get("followup_index") or 1)
            return {
                "status": "ok",
                "display": {
                    "format": "text",
                    "title": f"Application follow-up {index}",
                    "body": "The application notification follow-up ran.",
                    "variant": variant,
                    "presentation": presentation,
                    "dismissible": True,
                },
            }
        if action_id in {
            "resolve_application_notification",
            "expire_application_notification",
        }:
            items = [
                item
                for item in app.list_application_notifications()
                if item.get("key") == "dummy:application:notification"
                and item.get("status") == "pending"
            ]
            if not items:
                return {"status": "ok", "message": "No pending demo notification."}
            if action_id == "resolve_application_notification":
                app.resolve_application_notification(
                    items[-1]["id"], {"action_id": action_id}
                )
                message = "Demo notification resolved."
            else:
                app.expire_application_notification(
                    items[-1]["id"],
                    reason="demo_action",
                )
                message = "Demo notification expired."
            return {"status": "ok", "message": message}
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
                    "actions": _followup_actions(params),
                },
                "model_visibility": "hidden",
                "retention": _retention(params),
            }
        )
        return {"status": "ok", "notification_id": notification["id"]}


__all__ = ["DummyApplicationNotificationPlugin"]
