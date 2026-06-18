from __future__ import annotations

from typing import Any, Dict, List, Optional


class DummySettingsAppPlugin:
    name = "dummy_settings_app_plugin"
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
        return [
            {
                "ui_type": "config",
                "scope": "server",
                "key": "dummy_server_mode",
                "type": "select",
                "label": "Dummy server mode",
                "options": [
                    {"value": "fast", "label": "Fast"},
                    {"value": "careful", "label": "Careful"},
                ],
            },
            {
                "ui_type": "config",
                "scope": "server",
                "key": "dummy_server_enabled",
                "type": "checkbox",
                "label": "Dummy server enabled",
            },
            {
                "ui_type": "config",
                "scope": "session",
                "key": "dummy_session_mode",
                "type": "text",
                "label": "Dummy session mode",
            },
        ]

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        _ = app_config
        return {}

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "record_server_settings_changed",
                "label": "Record server settings change",
                "inputs": {},
                "trigger": "server_settings_changed",
            },
            {
                "id": "record_session_settings_changed",
                "label": "Record session settings change",
                "inputs": {},
                "trigger": "session_settings_changed",
            },
        ]

    def get_commands(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return []

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = app, params, state
        record = {
            "action_id": action_id,
            "context": dict(context or {}),
        }
        self.executed.append(record)
        return {"recorded": True, "record": record}


__all__ = ["DummySettingsAppPlugin"]