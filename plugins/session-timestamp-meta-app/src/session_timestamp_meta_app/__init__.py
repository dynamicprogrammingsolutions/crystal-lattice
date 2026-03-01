from __future__ import annotations

"""Application-level plugin that exposes session created/updated timestamps.

This plugin contributes ``session_list_field`` entries that reference
``session_created_at`` and ``session_updated_at`` fields on the
``/sessions`` summary entries.

An accompanying ``trigger == "session_list"`` action computes these
fields from the first and last message timestamps in each session when
possible, falling back to the session's ``modified`` timestamp when
message timestamps are unavailable.

Frontends can use ``metadata.format == "datetime"`` together with these
numeric epoch-second fields to render human-readable date/time strings.
"""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from agent_core import Session

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from agent_app.application_future import AgentApplication


class SessionTimestampMetaAppPlugin:
    """Application plugin that surfaces session created/updated timestamps."""

    name = "session_timestamp_meta"
    version = "1.0.0"

    def __init__(self) -> None:  # pragma: no cover - trivial initializer
        self._state: Dict[str, Any] = {}

    def get_config_schema(self) -> Dict[str, Any]:
        # Configuration is intentionally minimal; provided for completeness.
        #
        # ``session_time_use_modified_when_missing`` controls whether
        # the plugin falls back to the ``modified`` timestamp from the
        # session summary when message-level timestamps are unavailable.
        return {
            "session_time_use_modified_when_missing": {
                "type": "boolean",
                "description": (
                    "When true, fall back to the session's 'modified' "
                    "timestamp if no message metadata timestamps are present."
                ),
            }
        }

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
                "id": "session_updated_at_field",
                "role": "meta",
                "label": "Updated",
                "data": "session_updated_at",
                "template": "Updated: {{data}}",
                "order": 0,
                "metadata": {"format": "datetime"},
            },
            {
                "ui_type": "session_list_field",
                "id": "session_created_at_field",
                "role": "meta",
                "label": "Created",
                "data": "session_created_at",
                "template": "Created: {{data}}",
                "order": 1,
                "metadata": {"format": "datetime"},
            },
        ]

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:  # pragma: no cover - trivial
        application_cfg = app_config.get("application") if isinstance(app_config, dict) else {}
        use_modified = application_cfg.get("session_time_use_modified_when_missing")
        if not isinstance(use_modified, bool):
            use_modified = True

        self._state = {"use_modified_when_missing": use_modified}
        return dict(self._state)

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:  # type: ignore[override]
        # Single lightweight action used when building the sessions list.
        return [
            {
                "id": "compute_session_time_meta",
                "label": "Compute session created/updated times",
                "description": (
                    "Derive session_created_at and session_updated_at from "
                    "message metadata timestamps."
                ),
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

    @staticmethod
    def _iso_to_epoch_seconds(value: Any) -> Optional[float]:
        if not isinstance(value, str) or not value:
            return None
        try:
            dt = datetime.fromisoformat(value)
        except Exception:  # pragma: no cover - defensive
            return None
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return float(dt.timestamp())

    def execute_action(
        self,
        app: "AgentApplication",  # type: ignore[override]
        action_id: str,
        params: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        if action_id != "compute_session_time_meta":
            raise ValueError(
                f"Unknown action_id {action_id!r} for SessionTimestampMetaAppPlugin",
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

        created_ts: Optional[float] = None
        updated_ts: Optional[float] = None

        # Inspect message metadata timestamps when available.
        for msg in session_obj.messages:
            md = msg.metadata or {}
            ts_val = md.get("timestamp") if isinstance(md, dict) else None
            epoch = self._iso_to_epoch_seconds(ts_val)
            if epoch is None:
                continue
            if created_ts is None or epoch < created_ts:
                created_ts = epoch
            if updated_ts is None or epoch > updated_ts:
                updated_ts = epoch

        # Optional fallback when message timestamps are missing.
        if (created_ts is None or updated_ts is None) and state.get(
            "use_modified_when_missing", True
        ):
            summary = params.get("session_summary")
            if isinstance(summary, dict):
                mtime = summary.get("modified")
                if isinstance(mtime, (int, float)) and not isinstance(mtime, bool):
                    ts = float(mtime)
                    if created_ts is None:
                        created_ts = ts
                    if updated_ts is None:
                        updated_ts = ts

        if created_ts is None or updated_ts is None:
            # Nothing to contribute for this session.
            return {"session_list_fields": {}}

        return {
            "session_list_fields": {
                "session_created_at": created_ts,
                "session_updated_at": updated_ts,
            }
        }


__all__ = ["SessionTimestampMetaAppPlugin"]
