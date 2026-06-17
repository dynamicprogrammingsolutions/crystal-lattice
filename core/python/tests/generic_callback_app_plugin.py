"""Generic callback application plugin fixture for action deep-link tests."""

from __future__ import annotations

from typing import Any, Dict, List


class GenericCallbackAppPlugin:
    name = "generic_callback_app"
    version = "1.0.0"

    def __init__(self) -> None:
        self.executed: List[Dict[str, Any]] = []

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        return {}

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "id": "complete_external_flow",
                "label": "Complete external flow",
                "description": "Completes a generic external callback flow.",
                "inputs": {
                    "result": {"type": "string", "required": True},
                    "nonce": {"type": "string", "required": False},
                    "redirect_url": {"type": "string", "required": True},
                },
            }
        ]

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Dict[str, Any] | None = None,
        tags: List[str] | None = None,
        models: List[Dict[str, Any]] | None = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "session_action",
                "id": "complete_external_flow",
                "label": "Complete external flow",
                "action_id": "complete_external_flow",
            }
        ]

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: Dict[str, Any],
        context: Dict[str, Any] | None,
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
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


__all__ = ["GenericCallbackAppPlugin"]
