"""Application-level plugin for bucketed session list ordering.

This plugin computes lightweight ordering fields for sessions and exposes
``session_list_order`` specs so the HTTP layer can apply a consistent
ordering when serving ``/sessions``.

The default strategy is:

1. Recently archived sessions below every other session.
2. Sessions updated within the last 24 hours.
3. Then, among the rest, pinned sessions before unpinned.
4. Within each bucket, order by last updated time (most recent first).

Ordering is expressed via numeric fields:

* ``recent_archived_rank`` – 1 for archived sessions updated within the last
  60 days, 0 otherwise. Older archived sessions are exempt from archive
  ordering.
* ``updated_24h_rank`` – 0 for sessions updated in the last 24h, 1 otherwise.
* ``pinned_rank`` – 0 when the configured session metadata value is pinned,
  1 for unpinned or missing.
* ``last_updated_sort_key`` – negative epoch seconds for last-updated time,
  so that smaller values correspond to more recent sessions when sorting
  ascending.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TYPE_CHECKING

import time

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from agent_app.application_future import AgentApplication


RECENT_ARCHIVE_WINDOW_SECONDS = 60 * 24 * 60 * 60


class SessionOrderingBucketsAppPlugin:
    """Application plugin that defines a bucketed ordering strategy."""

    name = "session_ordering_buckets"
    version = "1.1.0"

    def __init__(self) -> None:  # pragma: no cover - trivial initializer
        self._state: Dict[str, Any] = {}

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            "session_order_24h_window_seconds": {
                "type": "number",
                "description": (
                    "Length of the 'recently updated' window in seconds "
                    "for session list ordering. Defaults to 86400 (24h)."
                ),
            },
            "session_order_use_updated_at": {
                "type": "boolean",
                "description": (
                    "When true, prefer 'session_updated_at' from the "
                    "session summary as the source of last-updated time, "
                    "falling back to 'modified' when missing."
                ),
            },
            "session_pinned_metadata_key": {
                "type": "string",
                "description": (
                    "Session metadata key used to determine pinned ordering. "
                    "This should match session-pinned-app and defaults to 'pinned'."
                ),
                "default": "pinned",
            },
            "session_archived_metadata_key": {
                "type": "string",
                "description": (
                    "Session metadata key used to determine archive ordering. "
                    "This should match session-archive-app and defaults to "
                    "'archived'."
                ),
                "default": "archived",
            },
        }

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        # This plugin is ordering-only and does not contribute UI elements.
        return []

    def init(
        self, app_config: Dict[str, Any]
    ) -> Dict[str, Any]:  # pragma: no cover - trivial
        application_cfg = (
            app_config.get("application") if isinstance(app_config, dict) else {}
        )

        raw_window = application_cfg.get("session_order_24h_window_seconds")
        window_seconds: float
        if (
            isinstance(raw_window, (int, float))
            and not isinstance(raw_window, bool)
            and raw_window > 0
        ):
            window_seconds = float(raw_window)
        else:
            window_seconds = 86400.0

        raw_use_updated = application_cfg.get("session_order_use_updated_at")
        use_updated_at = (
            bool(raw_use_updated) if isinstance(raw_use_updated, bool) else True
        )

        raw_pinned_key = application_cfg.get("session_pinned_metadata_key")
        if isinstance(raw_pinned_key, str) and raw_pinned_key.strip():
            pinned_metadata_key = raw_pinned_key.strip()
        else:
            pinned_metadata_key = "pinned"

        raw_archived_key = application_cfg.get("session_archived_metadata_key")
        if isinstance(raw_archived_key, str) and raw_archived_key.strip():
            archived_metadata_key = raw_archived_key.strip()
        else:
            archived_metadata_key = "archived"

        self._state = {
            "window_seconds": window_seconds,
            "use_updated_at": use_updated_at,
            "pinned_metadata_key": pinned_metadata_key,
            "archived_metadata_key": archived_metadata_key,
        }
        return dict(self._state)

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:  # type: ignore[override]
        return [
            {
                "id": "compute_session_order_buckets",
                "label": "Compute session order buckets",
                "description": (
                    "Assign recent-archive, 24h, and pinned ranks and a "
                    "recency-based sort key for session list ordering."
                ),
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    # ``session_summary`` is intentionally untyped so the
                    # application layer can pass it through without
                    # additional validation.
                    "session_summary": {"required": False},
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
        if action_id != "compute_session_order_buckets":
            raise ValueError(
                f"Unknown action_id {action_id!r} for SessionOrderingBucketsAppPlugin",
            )

        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        summary = params.get("session_summary")
        if not isinstance(summary, dict):
            summary = {}

        window_seconds = state.get("window_seconds", 86400.0)
        if not isinstance(window_seconds, (int, float)) or isinstance(
            window_seconds, bool
        ):
            window_seconds = 86400.0

        use_updated_at = state.get("use_updated_at", True)
        if not isinstance(use_updated_at, bool):
            use_updated_at = True

        # Determine effective last-updated timestamp in epoch seconds.
        effective_updated: float
        updated_val = summary.get("session_updated_at") if use_updated_at else None
        if isinstance(updated_val, (int, float)) and not isinstance(updated_val, bool):
            effective_updated = float(updated_val)
        else:
            modified_val = summary.get("modified")
            if isinstance(modified_val, (int, float)) and not isinstance(
                modified_val, bool
            ):
                effective_updated = float(modified_val)
            else:
                # Neutral baseline when no usable timestamp is present.
                effective_updated = 0.0

        now_ts = float(time.time())
        threshold = now_ts - float(window_seconds)

        if effective_updated >= threshold:
            updated_24h_rank = 0
        else:
            updated_24h_rank = 1

        metadata = summary.get("metadata")

        pinned_metadata_key = state.get("pinned_metadata_key", "pinned")
        if not isinstance(pinned_metadata_key, str) or not pinned_metadata_key:
            pinned_metadata_key = "pinned"
        pinned_value = (
            metadata.get(pinned_metadata_key) if isinstance(metadata, dict) else None
        )
        pinned_flag = pinned_value is True
        pinned_rank = 0 if pinned_flag else 1

        archived_metadata_key = state.get("archived_metadata_key", "archived")
        if not isinstance(archived_metadata_key, str) or not archived_metadata_key:
            archived_metadata_key = "archived"
        archived_value = (
            metadata.get(archived_metadata_key) if isinstance(metadata, dict) else None
        )
        is_recent_or_exactly_at_archive_boundary = (
            effective_updated >= now_ts - RECENT_ARCHIVE_WINDOW_SECONDS
        )
        recent_archived_rank = (
            1
            if archived_value is True and is_recent_or_exactly_at_archive_boundary
            else 0
        )

        last_updated_sort_key = -effective_updated

        fields = {
            "recent_archived_rank": recent_archived_rank,
            "updated_24h_rank": updated_24h_rank,
            "pinned_rank": pinned_rank,
            "last_updated_sort_key": last_updated_sort_key,
        }

        order_specs = [
            {
                "key": "recent_archived_rank",
                "direction": "asc",
                "fallback": 0,
                "priority": 5,
            },
            {
                "key": "updated_24h_rank",
                "direction": "asc",
                "fallback": 1,
                "priority": 10,
            },
            {
                "key": "pinned_rank",
                "direction": "asc",
                "fallback": 1,
                "priority": 20,
            },
            {
                "key": "last_updated_sort_key",
                "direction": "asc",
                "fallback": 0.0,
                "priority": 30,
            },
        ]

        return {
            "session_list_fields": fields,
            "session_list_order": order_specs,
        }


__all__ = ["SessionOrderingBucketsAppPlugin"]
