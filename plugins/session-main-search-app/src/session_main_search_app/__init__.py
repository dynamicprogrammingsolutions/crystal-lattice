from __future__ import annotations

from typing import Any, Dict, List, Optional


class SessionMainSearchAppPlugin:
    """Contribute the ordinary declarative search for session lists."""

    name = "session_main_search"
    version = "1.0.0"

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        _ = app_config
        return {}

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return []

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = state, config, context
        return [
            {
                "ui_type": "session_list_filter",
                "id": "session_search",
                "label": "Search",
                "icon": "search",
                "order": 0,
                "type": "text",
                "match": "contains",
                "data": [
                    "session_id",
                    "preview",
                    "presentation.title",
                    "presentation.subtitle",
                    "presentation.meta",
                ],
                "case_sensitive": False,
                "default": "",
                "main_search": True,
            }
        ]

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = app, params, context, state
        raise ValueError(f"SessionMainSearchAppPlugin exposes no action {action_id!r}")


__all__ = ["SessionMainSearchAppPlugin"]
