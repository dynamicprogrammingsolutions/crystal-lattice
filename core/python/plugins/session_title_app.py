from __future__ import annotations

"""Application-level plugin managing session titles.

This plugin operates at the :class:`agent_app.application_future.AgentApplication`
layer and exposes a single logical action, ``set_session_title``. The action
sets or clears a title field on the session metadata and emits a lightweight
event so that frontends can detect metadata updates.

The plugin also contributes a ``session_list_field`` UI element so that
session-list UIs can render ``metadata.title`` (or a configurable metadata
key) as the preferred title line when present.
"""

from typing import Any, Dict, List, TYPE_CHECKING

from agent_core import Session

if TYPE_CHECKING:  # pragma: no cover - import cycle guard
    from agent_app.application_future import AgentApplication


class SessionTitleAppPlugin:
    """Application-level plugin for managing session titles."""

    name = "session_title"
    version = "1.0.0"

    def __init__(self) -> None:  # pragma: no cover - trivial initializer
        self._state: Dict[str, Any] = {}

    # ------------------------------------------------------------------
    # ApplicationPlugin protocol methods
    # ------------------------------------------------------------------

    def get_config_schema(self) -> Dict[str, Any]:
        """Return config schema keys under the top-level ``application`` key.

        Only a single optional key is defined: ``session_title_metadata_key``
        controls which metadata field is treated as the title. Frontends can
        surface this in configuration UIs if desired.
        """

        return {
            "session_title_metadata_key": {
                "type": "string",
                "description": (
                    "Metadata key used for storing session titles. "
                    "Defaults to 'title' when not set."
                ),
                "default": "title",
            }
        }

    def get_ui_elements(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Return UI schema elements contributed by this plugin.

        Elements are generic and do not carry any behaviour beyond wiring
        parameters for the ``set_session_title`` action and exposing a
        ``session_list_field`` for the configured metadata key.
        """

        metadata_key = state.get("metadata_key") or "title"

        return [
            {
                "ui_type": "session_list_action",
                "id": "edit_title_from_list",
                "label": "Edit title",
                "icon": "type",
                "order": 5,
                "action_id": "set_session_title",
                "fixed_params": {"source": "session_list"},
                "param_map": {
                    "session_id": "$session.session_id",
                    "title": "$dialog.title",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Edit title",
                    "message": "Set a short title for this session.",
                    "inputs": [
                        {
                            "name": "title",
                            "type": "string",
                            "label": "Title",
                            "required": False,
                            "placeholder": "e.g. Daily standup notes",
                        },
                    ],
                },
            },
            {
                "ui_type": "session_action",
                "id": "edit_title_from_view",
                "label": "Edit title",
                "icon": "type",
                "order": 15,
                "action_id": "set_session_title",
                "fixed_params": {"source": "session_view"},
                "param_map": {
                    "session_id": "$session.session_id",
                    "title": "$dialog.title",
                },
                "dialog": {
                    "kind": "form",
                    "title": "Edit title",
                    "message": "Set a short title for this session.",
                    "inputs": [
                        {
                            "name": "title",
                            "type": "string",
                            "label": "Title",
                            "required": False,
                            "placeholder": "e.g. Daily standup notes",
                        },
                    ],
                },
            },
            {
                "ui_type": "session_list_field",
                "id": "session_title_field",
                "key": "session_title",
                "label": "Session title",
                "role": "title",
                "data": f"metadata.{metadata_key}",
                "template": "{{data}}",
                "order": 0,
            },
        ]

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        application_cfg = app_config.get("application")
        if not isinstance(application_cfg, dict):
            application_cfg = {}

        raw_key = application_cfg.get("session_title_metadata_key")
        if isinstance(raw_key, str) and raw_key.strip():
            metadata_key = raw_key.strip()
        else:
            metadata_key = "title"

        self._state = {"metadata_key": metadata_key}
        return dict(self._state)

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:  # type: ignore[override]
        return [
            {
                "id": "set_session_title",
                "label": "Set session title",
                "description": "Set or clear the session's title metadata.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "title": {"type": "string", "required": True},
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
        if action_id == "set_session_title":
            return self._do_set_session_title(app, params, state)

        raise ValueError(f"Unknown action_id {action_id!r} for SessionTitleAppPlugin")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _do_set_session_title(
        self,
        app: "AgentApplication",
        params: Dict[str, Any],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        session_id = params.get("session_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")

        # Inputs have already been validated for primitive types by
        # AgentApplication._validate_action_inputs, so "title" is known to
        # be a string here.
        title_val = params.get("title")
        if not isinstance(title_val, str):  # defensive
            raise ValueError("title must be a string")

        new_title = title_val.strip()
        metadata_key = state.get("metadata_key") or "title"

        with app.acquire_session_lock(session_id):
            ctx = app.load_session(session_id)
            if ctx is None:
                raise KeyError(f"Session {session_id!r} not found")

            _core, _base_config, session = ctx
            metadata = session.metadata if isinstance(session.metadata, dict) else {}

            if new_title:
                new_metadata = {**metadata, metadata_key: new_title}
            else:
                new_metadata = dict(metadata)
                new_metadata.pop(metadata_key, None)

            new_session = Session(
                session_id=session.session_id,
                messages=session.messages,
                metadata=new_metadata,
            )
            app.save_session(new_session)

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
            "created_session_ids": [],
            "updated_session_ids": [session_id],
            "deleted_session_ids": [],
            "message": "Session title updated.",
        }


__all__ = ["SessionTitleAppPlugin"]
