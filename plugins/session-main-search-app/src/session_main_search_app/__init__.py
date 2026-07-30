from __future__ import annotations

from typing import Any, Dict, List, Optional

from agent_core import Session


FIRST_USER_MESSAGE_FIELD = "first_user_message"


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
        return [
            {
                "id": "compute_first_user_message",
                "label": "Compute first user message",
                "description": (
                    "Expose the complete first non-empty user message for "
                    "session-list filtering."
                ),
                "inputs": {
                    "session": {"required": False},
                },
                "trigger": "session_list",
            }
        ]

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
                    FIRST_USER_MESSAGE_FIELD,
                    "presentation.title",
                    "presentation.subtitle",
                    "presentation.meta",
                ],
                "case_sensitive": False,
                "default": "",
                "main_search": True,
            },
            {
                "ui_type": "session_list_filter",
                "id": "session_title_search",
                "label": "Title / subtitle",
                "icon": "type",
                "order": 10,
                "type": "text",
                "match": "contains",
                "data": [
                    "presentation.title",
                    "presentation.subtitle",
                ],
                "case_sensitive": False,
                "default": "",
            },
            {
                "ui_type": "session_list_filter",
                "id": "session_first_message_search",
                "label": "First message",
                "icon": "message-square",
                "order": 20,
                "type": "text",
                "match": "contains",
                "data": FIRST_USER_MESSAGE_FIELD,
                "case_sensitive": False,
                "default": "",
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
        _ = app, context, state
        if action_id != "compute_first_user_message":
            raise ValueError(
                f"Unknown action_id {action_id!r} for SessionMainSearchAppPlugin"
            )

        session = params.get("session")
        if not isinstance(session, Session):
            return {"session_list_fields": {FIRST_USER_MESSAGE_FIELD: ""}}

        for message in session.messages:
            if message.role != "user" or not isinstance(message.content, str):
                continue
            normalized = " ".join(message.content.split())
            if normalized:
                return {
                    "session_list_fields": {
                        FIRST_USER_MESSAGE_FIELD: normalized,
                    }
                }

        return {"session_list_fields": {FIRST_USER_MESSAGE_FIELD: ""}}


__all__ = ["FIRST_USER_MESSAGE_FIELD", "SessionMainSearchAppPlugin"]
