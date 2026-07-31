from __future__ import annotations

from typing import Any


class DummyActionDisplayPlugin:
    name = "dummy_action_display"
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
                "id": "show_action_display",
                "label": "Show action display",
                "inputs": {
                    "presentation": {"type": "string", "required": True},
                    "variant": {"type": "string", "required": True},
                },
            }
        ]

    def get_ui_elements(
        self, state: dict[str, Any], config=None, context=None
    ) -> list[dict[str, Any]]:
        _ = state, config, context
        return [
            {
                "ui_type": "application_action",
                "id": "show_action_display",
                "label": "Demo action display",
                "icon": "layout",
                "action_id": "show_action_display",
                "dialog": {
                    "kind": "form",
                    "title": "Action display demo",
                    "inputs": [
                        {
                            "name": "presentation",
                            "type": "select",
                            "label": "Presentation",
                            "required": True,
                            "options": ["banner", "inline", "modal"],
                            "default": "modal",
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
            }
        ]

    def get_commands(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return []

    def execute_action(
        self, app: Any, action_id: str, params: dict[str, Any], context, state
    ) -> dict[str, Any]:
        _ = app, context, state
        if action_id != "show_action_display":
            raise KeyError(action_id)
        presentation = str(params.get("presentation") or "modal")
        variant = str(params.get("variant") or "info")
        return {
            "status": "ok",
            "display": {
                "display_id": f"dummy-action-display:{presentation}",
                "format": "text",
                "title": "Action display demo",
                "body": f"{variant} response using {presentation} presentation.",
                "variant": variant,
                "presentation": presentation,
                "dismissible": True,
                "actions": [
                    {
                        "kind": "copy_text",
                        "id": "copy",
                        "label": "Copy text",
                        "text": f"{variant}:{presentation}",
                    }
                ],
            },
        }


__all__ = ["DummyActionDisplayPlugin"]
