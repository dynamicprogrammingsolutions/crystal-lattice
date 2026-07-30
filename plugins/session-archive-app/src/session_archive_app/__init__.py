"""Application-level plugin for archiving and filtering sessions."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from agent_core import Session

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from agent_app.application_future import AgentApplication


class SessionArchiveAppPlugin:
    """Manage archived state stored in configurable session metadata."""

    name = "session_archive"
    version = "1.0.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "session_archived_metadata_key": {
                "type": "string",
                "description": (
                    "Metadata key used for storing archived state on sessions. "
                    "Defaults to 'archived' when not set."
                ),
                "default": "archived",
            }
        }

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        application_cfg = app_config.get("application")
        if not isinstance(application_cfg, dict):
            application_cfg = {}
        raw_key = application_cfg.get("session_archived_metadata_key")
        metadata_key = (
            raw_key.strip()
            if isinstance(raw_key, str) and raw_key.strip()
            else "archived"
        )
        return {"archived_metadata_key": metadata_key}

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": "toggle_session_archived",
                "label": "Toggle archived state",
                "description": "Archive or restore a session in the list.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
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
        metadata_key = state.get("archived_metadata_key") or "archived"
        return [
            {
                "ui_type": "session_list_action",
                "id": "toggle_session_archived",
                "label": "Archive/restore session",
                "icon": "archive",
                "order": 20,
                "action_id": "toggle_session_archived",
                "param_map": {
                    "session_id": "$session.session_id",
                },
                "dialog": {"kind": "none"},
                "rich_ui": {
                    "kind": "toggle",
                    "value_path": f"metadata.{metadata_key}",
                    "missing_value": False,
                    "active_value": True,
                    "default_pinned": True,
                    "appearance": {
                        "active": {"tone": "primary"},
                        "inactive": {"tone": "muted"},
                    },
                },
            },
            {
                "ui_type": "session_list_filter",
                "id": "archive_state",
                "label": "Archive state",
                "icon": "archive",
                "order": 30,
                "type": "boolean",
                "match": "equals",
                "data": f"metadata.{metadata_key}",
                "missing_value": False,
                "default": False,
                "options": [
                    {
                        "value": False,
                        "label": "Not archived",
                        "icon": "archive",
                        "tone": "muted",
                    },
                    {
                        "value": True,
                        "label": "Archived",
                        "icon": "archive",
                        "tone": "primary",
                    },
                ],
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
        if action_id != "toggle_session_archived":
            raise ValueError(
                f"Unknown action_id {action_id!r} for SessionArchiveAppPlugin"
            )
        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        metadata_key = state.get("archived_metadata_key") or "archived"
        with app.acquire_session_lock(session_id):
            ctx = app.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            _core, _base_config, session = ctx
            metadata = session.metadata if isinstance(session.metadata, dict) else {}
            new_session = Session(
                session_id=session.session_id,
                messages=session.messages,
                metadata={
                    **metadata,
                    metadata_key: not bool(metadata.get(metadata_key)),
                },
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
                app.record_checkpoint(new_session.session_id, stored.get("request_id"))
            except Exception:  # pragma: no cover - defensive
                pass

        return {
            "mutations": {
                "created_session_ids": [],
                "updated_session_ids": [session_id],
                "deleted_session_ids": [],
            },
            "ui_effects": {},
            "message": "Session archived state updated.",
        }


__all__ = ["SessionArchiveAppPlugin"]
