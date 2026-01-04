from __future__ import annotations

"""Application-level plugin that exposes a timestamp meta field for sessions.

This plugin contributes a ``session_list_field`` that points to the
``modified`` timestamp returned by the ``/sessions`` endpoint. Frontends
can use the accompanying ``metadata.format == "datetime"`` hint to
render a human-readable date/time string.
"""

from typing import Any, Dict, List, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from agent_app.application_future import AgentApplication


class SessionTimestampMetaAppPlugin:
    """Application plugin that surfaces the session's modified timestamp."""

    name = "session_timestamp_meta"
    version = "1.0.0"

    def __init__(self) -> None:  # pragma: no cover - trivial initializer
        self._state: Dict[str, Any] = {}

    def get_config_schema(self) -> Dict[str, Any]:
        # No configuration required; provided for completeness.
        return {}

    def get_ui_elements(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "session_list_field",
                "id": "session_timestamp_meta",
                "role": "meta",
                "label": "Updated",
                "data": "modified",
                "template": "Updated: {{data}}",
                "order": 0,
                "metadata": {"format": "datetime"},
            }
        ]

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - trivial
        self._state = {}
        return dict(self._state)

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:  # type: ignore[override]
        # This plugin is display-only and does not expose any actions.
        return []

    def execute_action(
        self,
        app: "AgentApplication",  # type: ignore[override]
        action_id: str,
        params: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        # No actions are defined; guard against misconfiguration.
        raise ValueError(
            f"Unknown action_id {action_id!r} for SessionTimestampMetaAppPlugin",
        )


__all__ = ["SessionTimestampMetaAppPlugin"]
