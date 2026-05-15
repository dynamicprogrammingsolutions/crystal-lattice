from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:  # pragma: no cover
    from agent_app.application_future import AgentApplication


DOWNLOAD_ATTACHMENT_ACTION_ID = "download_attachment"


class SessionAssetAttachmentsAppPlugin:
    """Generic application plugin for session asset attachment actions."""

    name = "session_asset_attachments"
    version = "0.1.0"

    def get_config_schema(self) -> Dict[str, Any]:
        return {}

    def init(self, app_config: Dict[str, Any]) -> Dict[str, Any]:
        _ = app_config
        return {}

    def get_ui_elements(
        self,
        state: Dict[str, Any],
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = state, config, tags, models
        return []

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": DOWNLOAD_ATTACHMENT_ACTION_ID,
                "label": "Download attachment",
                "description": "Download a stored session-owned attachment asset.",
                "inputs": {
                    "session_id": {"type": "string", "required": True},
                    "asset_id": {"type": "string", "required": True},
                },
            }
        ]

    def execute_action(
        self,
        app: "AgentApplication",
        action_id: str,
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = context, state
        if action_id != DOWNLOAD_ATTACHMENT_ACTION_ID:
            raise ValueError(f"Unknown action_id {action_id!r}")

        session_id = params.get("session_id")
        asset_id = params.get("asset_id")
        if not isinstance(session_id, str) or not session_id:
            raise ValueError("session_id must be a non-empty string")
        if not isinstance(asset_id, str) or not asset_id:
            raise ValueError("asset_id must be a non-empty string")

        asset_store = app.get_session_asset_store()
        record = asset_store.load(session_id, asset_id)
        payload = asset_store.load_bytes(session_id, asset_id)
        return {
            "attachment_asset": record.public_descriptor(),
            "data_base64": base64.b64encode(payload).decode("ascii"),
            "message": f"Downloaded attachment {asset_id}",
        }


__all__ = ["SessionAssetAttachmentsAppPlugin"]