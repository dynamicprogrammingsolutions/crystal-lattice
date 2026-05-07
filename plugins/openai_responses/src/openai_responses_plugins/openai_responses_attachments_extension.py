"""OpenAI Responses attachment policy extension.

Owns attachment upload mode policy and attachment-related UI that does not
belong in the transport-focused provider implementation.
"""

from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin
from .openai_responses_attachment_policy import (
    ATTACHMENT_STATE_KEY as _ATTACHMENT_STATE_KEY,
    ATTACHMENT_UPLOAD_MODE_KEY as _ATTACHMENT_UPLOAD_MODE_KEY,
    IMAGE_ATTACHMENT_MODE_INLINE as _IMAGE_ATTACHMENT_MODE_INLINE,
    IMAGE_ATTACHMENT_MODE_KEY as _IMAGE_ATTACHMENT_MODE_KEY,
    IMAGE_ATTACHMENT_MODE_UPLOAD as _IMAGE_ATTACHMENT_MODE_UPLOAD,
    IMAGE_ATTACHMENT_MODE_VALUES as _IMAGE_ATTACHMENT_MODE_VALUES,
    UPLOAD_MODE_VALUES as _UPLOAD_MODE_VALUES,
    normalized_attachment_settings,
)

_SESSION_ASSETS_METADATA_KEY = "session_assets"
_UPLOAD_BEFORE_SEND_MODE = "upload_before_send"
_STORE_ATTACHMENT_ACTION_ID = "store_attachment"
_DELETE_ATTACHMENT_ACTION_ID = "delete_attachment"
_DOWNLOAD_ATTACHMENT_ACTION_ID = "download_attachment"


class OpenAIResponsesAttachmentsExtension(ProviderExtensionPlugin):
    name: str = "openai_responses_attachments"
    version: str = "0.1.0"
    priority: int = 52

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        _ = config, models
        return ["ext:openai_responses_attachments"]

    def required_tags(self) -> List[str]:
        return ["openai_responses"]

    def get_config_schema(self) -> Dict[str, Any]:
        return {
            _IMAGE_ATTACHMENT_MODE_KEY: {
                "type": "string",
                "required": False,
                "enum": list(_IMAGE_ATTACHMENT_MODE_VALUES),
                "default": _IMAGE_ATTACHMENT_MODE_INLINE,
                "description": (
                    "Image attachment handling. Use inline to send image content directly, "
                    "or upload to route image attachments through the upload-backed path."
                ),
            },
            _ATTACHMENT_UPLOAD_MODE_KEY: {
                "type": "string",
                "required": False,
                "enum": list(_UPLOAD_MODE_VALUES),
                "default": _UPLOAD_BEFORE_SEND_MODE,
                "description": (
                    "Internal upload-backed attachment policy. upload_before_send uploads "
                    "attachment-backed files through the OpenAI Files API immediately before "
                    "the Responses request. Legacy direct is normalized for compatibility."
                ),
            }
        }

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = config, models
        if isinstance(tags, list) and "openai_responses" not in tags:
            return []

        return [
            {
                "type": "select",
                "key": _IMAGE_ATTACHMENT_MODE_KEY,
                "label": "Image Attachment Mode",
                "options": [
                    {"value": _IMAGE_ATTACHMENT_MODE_INLINE, "label": _IMAGE_ATTACHMENT_MODE_INLINE},
                    {"value": _IMAGE_ATTACHMENT_MODE_UPLOAD, "label": _IMAGE_ATTACHMENT_MODE_UPLOAD},
                ],
            },
            {
                "ui_type": "composer_attachment",
                "key": "openai_responses:attachment:pdf",
                "attachment_type": "pdf",
                "supports_url": True,
                "supported_file_types": ["pdf"],
                "display_placement": "below",
                "label": "PDF",
                "icon": "file-text",
            },
        ]

    def init(self, config: Dict[str, Any], state: Dict[str, Any]) -> Dict[str, Any]:
        return {
            **state,
            _ATTACHMENT_STATE_KEY: normalized_attachment_settings(config),
        }

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
        state: Optional[Dict[str, Any]] = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = messages, state, context
        return list(native_messages)

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
        state: Optional[Dict[str, Any]] = None,
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = native_messages, state, context
        return list(messages)

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        attachment_state = state.get(_ATTACHMENT_STATE_KEY)
        if isinstance(attachment_state, dict):
            normalized = normalized_attachment_settings(attachment_state)
            if attachment_state == normalized:
                return list(native_messages), state
            return list(native_messages), {
                **state,
                _ATTACHMENT_STATE_KEY: normalized,
            }

        config = state.get("config") if isinstance(state.get("config"), dict) else {}
        return list(native_messages), {
            **state,
            _ATTACHMENT_STATE_KEY: normalized_attachment_settings(config),
        }

    def get_actions(self, state: Dict[str, Any]) -> List[Dict[str, Any]]:
        _ = state
        return [
            {
                "id": _STORE_ATTACHMENT_ACTION_ID,
                "label": "Store attachment",
                "description": "Store one attachment as a session-owned asset.",
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
        if attachment_type not in {"image", "pdf"}:
            raise ValueError("attachment_type must be 'image' or 'pdf'")
        if not isinstance(filename, str) or not filename:
            raise ValueError("filename must be a non-empty string")
        if not isinstance(mime_type, str) or not mime_type:
            raise ValueError("mime_type must be a non-empty string")
        if not isinstance(data_base64, str) or not data_base64:
            raise ValueError("data_base64 must be a non-empty string")

        if attachment_type == "pdf":
            if mime_type != "application/pdf":
                raise ValueError("pdf attachments must use mime_type application/pdf")
        elif not mime_type.startswith("image/"):
            raise ValueError("image attachments must use an image/* mime_type")

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
            provider_refs={"openai_responses": {"status": "not_uploaded"}},
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
        asset_id = params.get("asset_id")
        if not isinstance(asset_id, str) or not asset_id:
            raise ValueError("asset_id must be a non-empty string")

        asset_store = self._attachment_asset_store(context)
        deleted_record = asset_store.load(session.session_id, asset_id)
        deleted = asset_store.delete(session.session_id, asset_id)
        if not deleted:
            raise FileNotFoundError(f"Asset {asset_id!r} not found")

        asset_index = self._session_asset_index(session)
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