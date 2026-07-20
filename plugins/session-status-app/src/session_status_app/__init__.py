"""Application-level plugin for assigning and filtering session status."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from agent_core import Session

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from agent_app.application_future import AgentApplication


STATUS_OPTIONS: List[Dict[str, Any]] = [
    {"value": "todo", "label": "To do", "tone": "muted"},
    {
        "value": "in_progress",
        "label": "In progress",
        "tone": "primary",
    },
    {"value": "blocked", "label": "Blocked", "tone": "danger"},
    {"value": "done", "label": "Done", "tone": "success"},
]
STATUS_VALUES = frozenset(option["value"] for option in STATUS_OPTIONS)


class SessionStatusAppPlugin:
    """Manage status metadata and expose its ordinary action and filter."""

    name = "session_status"
    version = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "session_status_metadata_key": {
                "type": "string",
                "description": (
                    "Metadata key used for storing session status. "
                    "Defaults to 'status' when not set."
                ),
                "default": "status",
            },
        }

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        application_cfg = app_config.get("application")
        if not isinstance(application_cfg, dict):
            application_cfg = {}

        raw_key = application_cfg.get("session_status_metadata_key")
        if isinstance(raw_key, str) and raw_key.strip():
            metadata_key = raw_key.strip()
        else:
            metadata_key = "status"

        return {"status_metadata_key": metadata_key}

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "set_session_status",
                "label": "Set session status",
                "description": "Set a session's workflow status.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "status": {"type": "string", "required": True},
                    "source": {"type": "string", "required": False},
                },
            }
        ]

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = config, context
        metadata_key = state.get("status_metadata_key") or "status"

        return [
            {
                "ui_type": "session_list_action",
                "id": "set_session_status",
                "label": "Set status",
                "icon": "circle",
                "order": 30,
                "action_id": "set_session_status",
                "fixed_params": {"source": "session_list"},
                "param_map": {
                    "session_id": "$session.session_id",
                    "status": "$dialog.status",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Set status",
                    "inputs": [
                        {
                            "name": "status",
                            "type": "select",
                            "label": "Status",
                            "prefill_from": f"$session.metadata.{metadata_key}",
                            "default": "todo",
                            "options": STATUS_OPTIONS,
                            "required": True,
                        }
                    ],
                },
            },
            {
                "ui_type": "session_list_filter",
                "id": "session_status",
                "label": "Status",
                "icon": "circle",
                "order": 20,
                "type": "select",
                "match": "one_of",
                "multiple": True,
                "data": f"metadata.{metadata_key}",
                "missing_value": "todo",
                "default": [],
                "options": STATUS_OPTIONS,
            },
        ]

    def execute_action(
        self,
        app: "AgentApplication",
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = context
        if action_id != "set_session_status":
            raise ValueError(
                f"Unknown action_id {action_id!r} for SessionStatusAppPlugin"
            )

        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        status = params.get("status")
        if not isinstance(status, str) or status not in STATUS_VALUES:
            choices = ", ".join(sorted(STATUS_VALUES))
            raise ValueError(f"status must be one of: {choices}")

        metadata_key = state.get("status_metadata_key") or "status"

        with app.acquire_session_lock(session_id):
            ctx = app.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            _core, _base_config, session = ctx
            metadata = session.metadata if isinstance(session.metadata, dict) else {}
            effective_status = (
                metadata[metadata_key] if metadata_key in metadata else "todo"
            )
            if effective_status == status:
                return self._result(
                    updated_session_ids=[],
                    message="Session status is already up to date.",
                )

            new_session = Session(
                session_id=session.session_id,
                messages=session.messages,
                metadata={**metadata, metadata_key: status},
            )
            new_session = app.save_session(new_session)

            stored = app.publish_event(
                {
                    "type": "session_metadata_updated",
                    "session_id": new_session.session_id,
                    "fields": [metadata_key],
                }
            )
            try:
                app.record_checkpoint(
                    new_session.session_id,
                    stored.get("request_id"),
                )
            except Exception:  # pragma: no cover - defensive
                pass

        return self._result(
            updated_session_ids=[session_id],
            message="Session status updated.",
        )

    @staticmethod
    def _result(
        *,
        updated_session_ids: List[str],
        message: str,
    ) -> Dict[str, Any]:
        return {
            "mutations": {
                "created_session_ids": [],
                "updated_session_ids": updated_session_ids,
                "deleted_session_ids": [],
            },
            "ui_effects": {},
            "message": message,
        }


__all__ = ["STATUS_OPTIONS", "SessionStatusAppPlugin"]
