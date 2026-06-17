from __future__ import annotations

"""Demo application plugin for server-settings UI validation."""

from typing import Any


class DummySettingsAppPlugin:
    name = "dummy_settings_app_plugin"
    version = "1.0.0"

    def __init__(self) -> None:
        self.executed: list[dict[str, Any]] = []

    def get_config_schema(self) -> dict[str, Any]:
        return {}

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
                "ui_type": "config",
                "scope": "server",
                "key": "dummy_server_mode",
                "type": "select",
                "label": "Dummy server mode",
                "description": "Demo server-scoped select setting.",
                "default": "fast",
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
                "description": "Demo server-scoped boolean setting.",
                "default": False,
            },
            {
                "ui_type": "config",
                "scope": "server",
                "key": "dummy_server_name",
                "type": "text",
                "label": "Dummy server name",
                "description": "Demo server-scoped text setting.",
                "default": "Alpha",
            },
            {
                "ui_type": "config",
                "scope": "session",
                "key": "dummy_session_mode",
                "type": "text",
                "label": "Dummy session mode",
                "description": "Demo session-scoped setting used to verify filtering.",
            },
        ]

    def init(self, app_config: dict[str, Any]) -> dict[str, Any]:
        _ = app_config
        return {"settings_lifecycle_calls": []}

    def get_actions(self, state: dict[str, Any]) -> list[dict[str, Any]]:
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
        _ = app, params
        record = {
            "action_id": action_id,
            "context": dict(context or {}),
        }
        self.executed.append(record)
        calls = state.get("settings_lifecycle_calls")
        if isinstance(calls, list):
            calls.append(record)
        return {"recorded": True, "record": record}


__all__ = ["DummySettingsAppPlugin"]