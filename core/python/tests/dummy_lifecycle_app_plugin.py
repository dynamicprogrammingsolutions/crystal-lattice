from __future__ import annotations

from typing import Any, Dict, List, Optional


class DummyLifecycleAppPlugin:
    name = "dummy_lifecycle_app_plugin"
    version = "1.0.0"

    def __init__(self) -> None:
        self.executed: List[Dict[str, Any]] = []

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = state, config, tags, models
        return []

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        _ = app_config
        return {}

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {"id": "app_on_session_create", "label": "App create", "inputs": {}, "trigger": "session_create"},
            {
                "id": "app_on_session_delete_prepare",
                "label": "App delete",
                "inputs": {},
                "trigger": "session_delete_prepare",
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
        _ = app, params, state
        record = {"action_id": action_id, "context": dict(context or {})}
        self.executed.append(record)

        if action_id == "app_on_session_create":
            return {"session_metadata": {"app_created_marker": True}}
        if action_id == "app_on_session_delete_prepare":
            return {"message": "delete observed"}
        raise ValueError(f"Unknown action_id {action_id!r}")
