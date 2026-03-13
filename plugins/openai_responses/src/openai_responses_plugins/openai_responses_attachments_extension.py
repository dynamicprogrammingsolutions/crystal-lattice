"""OpenAI Responses attachment policy extension.

Owns attachment upload mode policy and attachment-related UI that does not
belong in the transport-focused provider implementation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin


_ATTACHMENT_UPLOAD_MODE_KEY = "attachment_upload_mode"
_ATTACHMENT_STATE_KEY = "openai_responses_attachments"
_DIRECT_MODE = "direct"
_UPLOAD_BEFORE_SEND_MODE = "upload_before_send"
_UPLOAD_MODE_VALUES = (_DIRECT_MODE, _UPLOAD_BEFORE_SEND_MODE)


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
            _ATTACHMENT_UPLOAD_MODE_KEY: {
                "type": "string",
                "required": False,
                "enum": list(_UPLOAD_MODE_VALUES),
                "default": _DIRECT_MODE,
                "description": (
                    "Attachment send strategy. Use upload_before_send to upload image/PDF "
                    "attachments through the OpenAI Files API before the Responses request."
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
                "key": _ATTACHMENT_UPLOAD_MODE_KEY,
                "label": "Attachment Upload Mode",
                "options": [
                    {"value": _DIRECT_MODE, "label": _DIRECT_MODE},
                    {"value": _UPLOAD_BEFORE_SEND_MODE, "label": _UPLOAD_BEFORE_SEND_MODE},
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
            _ATTACHMENT_STATE_KEY: {
                _ATTACHMENT_UPLOAD_MODE_KEY: self._normalized_mode(config),
            },
        }

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        native_messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        _ = messages
        return list(native_messages)

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        messages: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        _ = native_messages
        return list(messages)

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        attachment_state = state.get(_ATTACHMENT_STATE_KEY)
        if isinstance(attachment_state, dict):
            normalized = self._normalized_mode(attachment_state)
            if attachment_state.get(_ATTACHMENT_UPLOAD_MODE_KEY) == normalized:
                return list(native_messages), state
            return list(native_messages), {
                **state,
                _ATTACHMENT_STATE_KEY: {
                    _ATTACHMENT_UPLOAD_MODE_KEY: normalized,
                },
            }

        config = state.get("config") if isinstance(state.get("config"), dict) else {}
        return list(native_messages), {
            **state,
            _ATTACHMENT_STATE_KEY: {
                _ATTACHMENT_UPLOAD_MODE_KEY: self._normalized_mode(config),
            },
        }

    def _normalized_mode(self, config: Dict[str, Any]) -> str:
        raw = config.get(_ATTACHMENT_UPLOAD_MODE_KEY)
        if isinstance(raw, str) and raw in _UPLOAD_MODE_VALUES:
            return raw
        return _DIRECT_MODE