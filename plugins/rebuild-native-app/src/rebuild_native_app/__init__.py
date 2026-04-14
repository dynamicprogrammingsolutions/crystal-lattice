from __future__ import annotations

"""Application plugin to rebuild provider-native history from core messages.

This plugin exposes a session-level action and UI schema so that UIs can
surface a "Rebuild native history" button. When invoked, it calls
``AgentCore.rebuild_native_history`` with the effective configuration for
the session and saves the updated session.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING, Tuple

from agent_core import Session

from agent_app.config import resolve_request_config

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from agent_app.application_future import AgentApplication


class RebuildNativeAppPlugin:
    name = "rebuild_native"
    version = "1.0.0"

    def __init__(self) -> None:  # pragma: no cover - trivial initializer
        self._state: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # ApplicationPlugin protocol methods
    # ------------------------------------------------------------------

    def _normalize_slice_bounds(
        self,
        message_count: int,
        start: Optional[int],
        end: Optional[int],
    ) -> Tuple[int, int]:
        def _bound(value: Optional[int], default: int) -> int:
            if value is None:
                return default
            idx = value
            if idx < 0:
                idx = message_count + idx
            if idx < 0:
                return 0
            if idx > message_count:
                return message_count
            return idx

        start_idx = _bound(start, 0)
        end_idx = _bound(end, message_count)

        if start_idx >= end_idx:
            raise ValueError("message_range selects no messages")

        return start_idx, end_idx

    def get_config_schema(self) -> Dict[str, Any]:
        """Return config schema keys under the top-level ``application`` key."""

        return {
            "rebuild_native_enabled": {
                "type": "boolean",
                "default": True,
                "description": (
                    "Show a 'Rebuild native history' session action that recomputes "
                    "provider-native history from the current messages."
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
        """Return UI schema elements for the rebuild-native action."""

        enabled = bool(state.get("rebuild_native_enabled", True))
        if not enabled:
            return []

        return [
            {
                "ui_type": "session_action",
                "id": "rebuild_native_history",
                "label": "Rebuild native history",
                "icon": "refresh-cw",
                "order": 45,
                "action_id": "rebuild_native_history",
                "fixed_params": {},
                "param_map": {
                    "session_id": "$session.session_id",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Rebuild native history",
                    "message": (
                        "Recompute provider-native history from the current messages. "
                        "Optionally provide Python-style slice bounds to rebuild "
                        "only part of the native history."
                    ),
                    "inputs": [
                        {
                            "name": "start",
                            "type": "integer",
                            "label": "Start index",
                            "required": False,
                            "placeholder": "e.g. 0 or -10",
                        },
                        {
                            "name": "end",
                            "type": "integer",
                            "label": "End index (optional)",
                            "required": False,
                            "placeholder": "leave blank for end",
                        },
                    ],
                },
            }
        ]

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        application_cfg = app_config.get("application")
        if not isinstance(application_cfg, dict):
            application_cfg = {}

        raw_enabled = application_cfg.get("rebuild_native_enabled")
        enabled = bool(raw_enabled) if raw_enabled is not None else True

        self._state = {"rebuild_native_enabled": enabled}
        return dict(self._state)

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:  # type: ignore[override]
        return [
            {
                "id": "rebuild_native_history",
                "label": "Rebuild native history",
                "description": "Recompute provider-native history from the current messages.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "start": {"type": "integer", "required": False},
                    "end": {"type": "integer", "required": False},
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
        if action_id != "rebuild_native_history":
            raise ValueError(
                f"Unknown action_id {action_id!r} for RebuildNativeAppPlugin"
            )

        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        with app.acquire_session_lock(session_id):
            ctx = app.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            core, base_config, session = ctx

            # Respect per-session overrides when computing the effective config.
            md = session.metadata if isinstance(session.metadata, dict) else {}
            md_overrides_val = md.get("overrides")
            md_overrides: Dict[str, Any] = (
                md_overrides_val if isinstance(md_overrides_val, dict) else {}
            )
            effective_config = resolve_request_config(base_config, md_overrides)

            raw_start = params.get("start")
            raw_end = params.get("end")
            if raw_start is None and raw_end is None:
                new_session = core.rebuild_native_history(session, effective_config)
                result_message = "Rebuilt provider-native history from core messages."
            else:
                if raw_start is not None and (
                    not isinstance(raw_start, int) or isinstance(raw_start, bool)
                ):
                    raise ValueError("start must be an integer")
                if raw_end is not None and (
                    not isinstance(raw_end, int) or isinstance(raw_end, bool)
                ):
                    raise ValueError("end must be an integer")
                start_idx, end_idx = self._normalize_slice_bounds(
                    len(session.messages),
                    raw_start,
                    raw_end,
                )
                new_session = core.rebuild_native_history(
                    session,
                    effective_config,
                    start=start_idx,
                    end=end_idx,
                )
                result_message = (
                    f"Rebuilt provider-native history for visible messages "
                    f"[{start_idx}:{end_idx}]."
                )
            app.save_session(new_session)

        return {
            "mutations": {
                "created_session_ids": [],
                "updated_session_ids": [session_id],
                "deleted_session_ids": [],
            },
            "ui_effects": {
                "reload_session_ids": [session_id],
            },
            "message": result_message,
        }


__all__ = ["RebuildNativeAppPlugin"]
