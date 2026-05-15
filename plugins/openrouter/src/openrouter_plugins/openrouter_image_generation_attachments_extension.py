from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin


_SESSION_ASSETS_METADATA_KEY = "session_assets"
_STORE_ATTACHMENT_ACTION_ID = "store_attachment"
_DELETE_ATTACHMENT_ACTION_ID = "delete_attachment"
_DOWNLOAD_ATTACHMENT_ACTION_ID = "download_attachment"


class OpenRouterImageGenerationAttachmentsExtension(ProviderExtensionPlugin):
    name: str = "openrouter_image_generation_attachments"
    version: str = "0.1.0"
    priority: int = 52

    def required_tags(self) -> List[str]:
        return ["openrouter_image_generation"]

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = config, models
        if isinstance(tags, list) and "openrouter_image_generation" not in tags:
            return []
        return [
            {
                "ui_type": "composer_attachment",
                "key": "openrouter_image_generation_attachments:attachment:image",
                "attachment_type": "image",
                "supports_url": True,
                "supported_file_types": ["png", "jpg", "jpeg", "webp"],
                "display_placement": "below",
                "label": "Input Image",
                "icon": "image",
            }
        ]

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        _ = config, models
        return ["ext:openrouter_image_generation_attachments"]

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": _STORE_ATTACHMENT_ACTION_ID,
                "label": "Store attachment",
                "description": "Store one image attachment as a session-owned asset.",
                "inputs": {
                    "client_attachment_id": {"type": "string", "required": False},
                    "attachment_type": {"type": "string", "required": True},
                    "filename": {"type": "string", "required": True},
                    "mime_type": {"type": "string", "required": True},
                    "data_base64": {"type": "string", "required": True},
                },
            },
            {
                "id": _DELETE_ATTACHMENT_ACTION_ID,
                "label": "Delete attachment",
                "description": "Delete a stored session-owned attachment asset.",
                "inputs": {
                    "asset_id": {"type": "string", "required": True},
                },
            },
            {
                "id": _DOWNLOAD_ATTACHMENT_ACTION_ID,
                "label": "Download attachment",
                "description": "Download a stored session-owned attachment asset.",
                "inputs": {
                    "asset_id": {"type": "string", "required": True},
                },
            },
        ]

    def execute_action(
        self,
        action_id: str,
        session: Any,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Dict[str, Any]:
        _ = state
        if action_id == _STORE_ATTACHMENT_ACTION_ID:
            return self._store_attachment_action(session, native_messages, params, context)
        if action_id == _DELETE_ATTACHMENT_ACTION_ID:
            return self._delete_attachment_action(session, native_messages, params, context)
        if action_id == _DOWNLOAD_ATTACHMENT_ACTION_ID:
            return self._download_attachment_action(session, native_messages, params, context)
        raise ValueError(f"Unknown action_id {action_id!r}")

    def _attachment_asset_store(self, context: Optional[Dict[str, Any]]) -> Any:
        if isinstance(context, dict) and context.get("session_asset_store") is not None:
            return context["session_asset_store"]
        raise RuntimeError("session_asset_store missing from action context")

    def _session_asset_index(self, session: Any) -> Dict[str, Any]:
        metadata = session.metadata if isinstance(getattr(session, "metadata", None), dict) else {}
        index = metadata.get(_SESSION_ASSETS_METADATA_KEY)
        return dict(index) if isinstance(index, dict) else {}

    def _validate_attachment_payload(
        self,
        *,
        attachment_type: Any,
        filename: Any,
        mime_type: Any,
        data_base64: Any,
    ) -> Tuple[str, str, str, str]:
        if attachment_type != "image":
            raise ValueError("attachment_type must be 'image'")
        if not isinstance(filename, str) or not filename:
            raise ValueError("filename must be a non-empty string")
        if not isinstance(mime_type, str) or not mime_type.startswith("image/"):
            raise ValueError("image attachments must use an image/* mime_type")
        if not isinstance(data_base64, str) or not data_base64:
            raise ValueError("data_base64 must be a non-empty string")
        return attachment_type, filename, mime_type, data_base64

    def _store_attachment_action(
        self,
        session: Any,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        asset_store = self._attachment_asset_store(context)
        attachment_type, filename, mime_type, data_base64 = self._validate_attachment_payload(
            attachment_type=params.get("attachment_type"),
            filename=params.get("filename"),
            mime_type=params.get("mime_type"),
            data_base64=params.get("data_base64"),
        )
        record = asset_store.store_base64(
            session_id=session.session_id,
            attachment_type=attachment_type,
            filename=filename,
            mime_type=mime_type,
            data_base64=data_base64,
            provider_refs={"openrouter_image_generation": {"status": "local_only"}},
        )
        asset_descriptor = record.public_descriptor()
        client_attachment_id = params.get("client_attachment_id")
        if isinstance(client_attachment_id, str) and client_attachment_id:
            asset_descriptor["client_attachment_id"] = client_attachment_id

        asset_index = self._session_asset_index(session)
        asset_index[record.asset_id] = asset_descriptor
        return {
            "native_messages": list(native_messages),
            "session_metadata": {_SESSION_ASSETS_METADATA_KEY: asset_index},
            "attachment_asset": asset_descriptor,
            "message": f"Stored attachment {record.asset_id}",
        }

    def _delete_attachment_action(
        self,
        session: Any,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        asset_store = self._attachment_asset_store(context)
        asset_id = params.get("asset_id")
        if not isinstance(asset_id, str) or not asset_id:
            raise ValueError("asset_id must be a non-empty string")

        asset_index = self._session_asset_index(session)
        existing_descriptor = asset_index.get(asset_id)
        if not isinstance(existing_descriptor, dict):
            raise FileNotFoundError(f"Attachment asset {asset_id!r} not found")

        deleted_record = asset_store.load(session.session_id, asset_id)
        asset_store.delete(session.session_id, asset_id)
        asset_index.pop(asset_id, None)
        return {
            "native_messages": list(native_messages),
            "session_metadata": {_SESSION_ASSETS_METADATA_KEY: asset_index},
            "deleted_attachment_asset": deleted_record.public_descriptor(),
            "message": f"Deleted attachment {asset_id}",
        }

    def _download_attachment_action(
        self,
        session: Any,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        asset_store = self._attachment_asset_store(context)
        asset_id = params.get("asset_id")
        if not isinstance(asset_id, str) or not asset_id:
            raise ValueError("asset_id must be a non-empty string")
        record = asset_store.load(session.session_id, asset_id)
        payload = asset_store.load_bytes(session.session_id, asset_id)
        return {
            "native_messages": list(native_messages),
            "attachment_asset": record.public_descriptor(),
            "data_base64": base64.b64encode(payload).decode("ascii"),
            "message": f"Downloaded attachment {asset_id}",
        }