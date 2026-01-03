"""Dummy application-level plugin for tests.

This plugin is used by application-layer tests to verify loading,
introspection, and action execution of ApplicationPlugin instances.
"""

from __future__ import annotations

from typing import Any, Dict, List


class DummyAppPlugin:
    """Minimal application-level plugin used by tests.

    The plugin exposes a single action and a single UI element and records
    calls made to :meth:`init` and :meth:`execute_action` so tests can
    assert on behaviour.
    """

    name = "dummy_app_plugin"
    version = "1.0.0"

    def __init__(self) -> None:
        self.init_config: Dict[str, Any] | None = None
        self.executed: List[Dict[str, Any]] = []

    def get_config_schema(self) -> Dict[str, Any]:
        return {"enabled": {"type": "boolean", "default": True}}

    def get_ui_elements(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Deliberately omit the "plugin" field; the application layer should
        # attach it when flattening the global UI schema.
        return [
            {
                "ui_type": "session_action",
                "id": "dummy_ui",
                "label": "Dummy action",
                "action_id": "do_dummy",
            }
        ]

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        self.init_config = dict(app_config)
        return {"seen_application_keys": sorted(app_config.keys())}

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        # Simple action with a single required string parameter.
        return [
            {
                "id": "do_dummy",
                "label": "Do dummy",
                "description": "Dummy test action.",
                "inputs": {
                    "value": {"type": "string", "required": True},
                },
            }
        ]

    def execute_action(
        self,
        app: Any,  # AgentApplication, but kept generic to avoid import cycle
        action_id: str,
        params: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        record = {
            "action_id": action_id,
            "params": dict(params),
            "state": dict(state),
        }
        self.executed.append(record)
        # Echo back inputs so tests can validate the result path.
        return {"echo": dict(params), "record": record}


__all__ = ["DummyAppPlugin"]
