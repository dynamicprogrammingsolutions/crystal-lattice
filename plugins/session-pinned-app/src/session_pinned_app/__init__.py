"""Application-level plugin for pinning and filtering sessions.

This plugin toggles a boolean flag in session metadata (for example,
``metadata["pinned"]``), exposes the existing lightweight pin control, and
contributes a declarative Boolean filter over the same configured metadata key.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

from agent_core import Session

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from agent_app.application_future import AgentApplication


class SessionPinnedAppPlugin:
    """Application plugin that manages pinned state for sessions."""

    name = "session_pinned"
    version = "1.0.0"

    def __init__(self) -> None:  # pragma: no cover - trivial initializer
        self._state: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # ApplicationPlugin protocol methods
    # ------------------------------------------------------------------

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "session_pinned_metadata_key": {
                "type": "string",
                "description": (
                    "Metadata key used for storing pinned state on "
                    "sessions. When not set, defaults to 'pinned'."
                ),
                "default": "pinned",
            },
        }

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        """Expose the legacy pin control and a declarative pin filter.

        Frontends can treat this as a star-style pin toggle attached to
        each row in the sessions list. The element delegates to the
        ``toggle_session_pinned`` action. The filter uses the same configured
        metadata key and defaults to Any so enabling the plugin does not hide
        sessions.
        """

        pinned_key = state.get("pinned_metadata_key") or "pinned"

        return [
            {
                "ui_type": "session_list_toggle_pinned",
                "id": "toggle_session_pinned_star",
                "label": "Pin/unpin session",
                "icon": "star",
                "order": 0,
                "data": f"metadata.{pinned_key}",
                "missing_value": False,
                "action_id": "toggle_session_pinned",
                "param_map": {
                    "session_id": "$session.session_id",
                },
                "dialog": {"kind": "none"},
            },
            {
                "ui_type": "session_list_filter",
                "id": "pinned_state",
                "label": "Pinned",
                "icon": "star",
                "order": 10,
                "type": "boolean",
                "match": "equals",
                "data": f"metadata.{pinned_key}",
                "missing_value": False,
                "default": None,
                "options": [
                    {
                        "value": False,
                        "label": "Not pinned",
                        "icon": "star",
                        "tone": "muted",
                    },
                    {
                        "value": True,
                        "label": "Pinned",
                        "icon": "star",
                        "tone": "warning",
                    },
                ],
            },
        ]

    def init(
        self, app_config: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover - trivial
        application_cfg = app_config.get("application")
        if not isinstance(application_cfg, dict):
            application_cfg = {}

        raw_key = application_cfg.get("session_pinned_metadata_key")
        if isinstance(raw_key, str) and raw_key.strip():
            pinned_key = raw_key.strip()
        else:
            pinned_key = "pinned"

        self._state = {"pinned_metadata_key": pinned_key}
        return dict(self._state)

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:  # type: ignore[override]
        return [
            {
                "id": "toggle_session_pinned",
                "label": "Toggle pinned state",
                "description": "Toggle whether a session is pinned in the list.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "source": {"type": "string", "required": False},
                },
            }
        ]

    def execute_action(
        self,
        app: "AgentApplication",  # type: ignore[override]
        action_id: str,
        params: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if action_id != "toggle_session_pinned":
            raise ValueError(
                f"Unknown action_id {action_id!r} for SessionPinnedAppPlugin",
            )

        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        pinned_key = state.get("pinned_metadata_key") or "pinned"

        with app.acquire_session_lock(session_id):
            ctx = app.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            _core, _base, session = ctx
            metadata = session.metadata if isinstance(session.metadata, dict) else {}

            current_val = metadata.get(pinned_key)
            current = bool(current_val)
            new_pinned = not current

            new_metadata = {**metadata, pinned_key: new_pinned}

            new_session = Session(
                session_id=session.session_id,
                messages=session.messages,
                metadata=new_metadata,
            )
            new_session = app.save_session(new_session)

            stored = app.publish_event(
                {
                    "type": "session_metadata_updated",
                    "session_id": new_session.session_id,
                    "fields": [pinned_key],
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
            "message": "Session pinned state updated.",
        }


__all__ = ["SessionPinnedAppPlugin"]
