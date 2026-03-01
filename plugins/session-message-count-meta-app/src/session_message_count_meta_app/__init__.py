from __future__ import annotations

"""Application-level plugin that exposes message-count metadata.

This plugin contributes a ``session_list_field`` for the total number of
messages in a session and a lightweight action that can be triggered when
building the sessions list to compute that count. The action is marked with
``trigger: "session_list"`` so that the HTTP layer can invoke it when
serving ``/sessions`` without frontends needing to know about it.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from agent_core import Session

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from agent_app.application_future import AgentApplication


class SessionMessageCountMetaAppPlugin:
    """Application plugin that surfaces per-session message counts."""

    name = "session_message_count_meta"
    version = "1.0.0"

    def __init__(self) -> None:  # pragma: no cover - trivial initializer
        self._state: Dict[str, Any] = {}

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        return [
            {
                "ui_type": "session_list_field",
                "id": "session_message_count_meta",
                "role": "meta",
                "label": "Messages",
                "data": "message_count",
                "template": "{{data}} messages",
                "order": 10,
            }
        ]

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - trivial
        self._state = {}
        return dict(self._state)

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:  # type: ignore[override]
        return [
            {
                "id": "compute_session_message_count_meta",
                "label": "Compute session message count",
                "description": "Compute total number of messages in a session for list metadata.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    # ``session_summary`` and ``session`` are intentionally
                    # untyped so the application layer can pass them through
                    # without additional validation.
                    "session_summary": {"required": False},
                    "session": {"required": False},
                },
                "trigger": "session_list",
            }
        ]

    def execute_action(
        self,
        app: "AgentApplication",  # type: ignore[override]
        action_id: str,
        params: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if action_id != "compute_session_message_count_meta":
            raise ValueError(
                f"Unknown action_id {action_id!r} for SessionMessageCountMetaAppPlugin",
            )

        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        session_obj = params.get("session")
        if not isinstance(session_obj, Session):
            ctx = app.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")
            _core, _base, session_obj = ctx

        count = len(session_obj.messages)

        return {"session_list_fields": {"message_count": count}}


__all__ = ["SessionMessageCountMetaAppPlugin"]
