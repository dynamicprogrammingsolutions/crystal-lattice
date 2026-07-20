from __future__ import annotations

from typing import Any, Dict, List, Optional


class SessionFiltersFixturePlugin:
    name = "session_filters_fixture"
    version = "1.0.0"

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        _ = app_config
        return {}

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

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
                "data": ["session_id", "preview", "presentation.title"],
                "type": "text",
                "match": "contains",
                "case_sensitive": False,
                "default": "",
                "main_search": True,
                "order": 0,
            },
            {
                "ui_type": "session_list_filter",
                "id": "archived",
                "label": "Archived",
                "data": "metadata.archived",
                "type": "boolean",
                "match": "equals",
                "missing_value": False,
                "default": False,
                "order": 10,
            },
        ]

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return []


class ConflictingSessionSearchFixturePlugin:
    name = "conflicting_session_search_fixture"
    version = "1.0.0"

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        _ = app_config
        return {}

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

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
                "id": "other_search",
                "label": "Other search",
                "data": "metadata.title",
                "type": "text",
                "match": "equals",
                "main_search": True,
            }
        ]

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return []


__all__ = [
    "ConflictingSessionSearchFixturePlugin",
    "SessionFiltersFixturePlugin",
]
