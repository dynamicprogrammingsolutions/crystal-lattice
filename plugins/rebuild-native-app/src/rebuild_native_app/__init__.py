from __future__ import annotations

"""Application plugin to rebuild provider-native history from core messages.

This plugin exposes a session-level action and UI schema so that UIs can
surface a "Rebuild native history" button. When invoked, it calls
``AgentCore.rebuild_native_history`` with the effective configuration for
the session and saves the updated session.
"""

from typing import Any, Dict, List, Optional, TYPE_CHECKING

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

    def get_ui_elements(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
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
                    "kind": "confirm",
                    "title": "Rebuild native history",
                    "message": (
                        "Recompute provider-native history from the current messages. "
                        "This may slightly adjust message metadata. Continue?"
                    ),
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

            new_session = core.rebuild_native_history(session, effective_config)
            app.save_session(new_session)

        return {
            "created_session_ids": [],
            "updated_session_ids": [session_id],
            "deleted_session_ids": [],
            # Keep selected_session_id as the current session so frontends
            # treat this as an in-place update.
            "selected_session_id": session_id,
            "message": "Rebuilt provider-native history from core messages.",
        }


__all__ = ["RebuildNativeAppPlugin"]
