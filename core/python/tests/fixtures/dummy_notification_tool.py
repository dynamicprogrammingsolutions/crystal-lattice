from __future__ import annotations

from typing import Any


class DummyNotificationTool:
    name = "dummy_notification_tool"
    version = "1.0.0"

    def execute_tool(
        self,
        tool_name: str,
        arguments: dict[str, Any],
        state: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        _ = arguments, state
        if tool_name != "emit_notification":
            return {"success": False, "error": "unknown tool"}
        sink = (context or {}).get("notification_sink")
        stored = (
            sink.create(
                {
                    "key": "dummy:tool:notification",
                    "severity": "warning",
                    "title": "Tool notification",
                    "body": "The tool continued after emitting this notification.",
                    "source": {"plugin": self.name},
                    "display": {
                        "format": "text",
                        "body": "The tool continued after emitting this notification.",
                        "presentation": "inline",
                    },
                    "model_visibility": "hidden",
                }
            )
            if sink is not None
            else None
        )
        return {"success": True, "notification_id": stored and stored.get("id")}


__all__ = ["DummyNotificationTool"]