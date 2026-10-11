from __future__ import annotations

import time
from typing import Any


class ChatOperationsFixture:
    name = "chat_operations_fixture"
    version = "0.1.0"

    def get_config_schema(self) -> dict[str, Any]:
        return {}

    def init(self, app_config: dict[str, Any]) -> dict[str, Any]:
        return {}

    def get_actions(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {"id": action, "label": label, "inputs": {}}
            for action, label in [
                ("slow", "Slow action"),
                ("second", "Second action"),
            ]
        ]

    def get_ui_elements(
        self,
        state: dict[str, Any],
        config: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        return [
            {
                "ui_type": "session_action",
                "id": action,
                "action_id": action,
                "label": label,
                "icon": "zap",
                "dialog": {"kind": "none"},
                "rich_ui": {
                    "kind": "button",
                    "placements": ["session_header"],
                    "default_pinned": True,
                },
            }
            for action, label in [("slow", "Slow action"), ("second", "Second action")]
        ]

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: dict[str, Any],
        context: dict[str, Any] | None,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        if action_id == "slow":
            time.sleep(10)
        elif action_id != "second":
            raise ValueError(action_id)
        return {
            "display": {
                "format": "text",
                "title": f"{action_id} finished",
                "body": f"The {action_id} action completed.",
                "presentation": "inline",
            }
        }