from __future__ import annotations

import base64
from typing import Any, Dict, List, Optional, Tuple

from agent_core.types import ProviderExtensionPlugin, ProviderPlugin


_SESSION_ASSETS_METADATA_KEY = "session_assets"
_STORE_ATTACHMENT_ACTION_ID = "store_attachment"
_DELETE_ATTACHMENT_ACTION_ID = "delete_attachment"
_DOWNLOAD_ATTACHMENT_ACTION_ID = "download_attachment"
_DOWNLOAD_PLUGIN_ID = "fake_image_generation_attachments"

_GENERATED_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAusB9Y9l9WQAAAAASUVORK5CYII="
)


class FakeImageGenerationProvider(ProviderPlugin):
    name: str = "fake_image_generation"
    version: str = "0.1.0"
    call_api_calls: int = 0
    stream_api_calls: int = 0

    @classmethod
    def reset_counts(cls) -> None:
        cls.call_api_calls = 0
        cls.stream_api_calls = 0

    def get_config_schema(self) -> Dict[str, Any]:
        return {"model": {"type": "string", "required": False}}

    def get_ui_elements(
        self,
        config: Optional[Dict[str, Any]] = None,
        tags: Optional[List[str]] = None,
        models: Optional[List[Dict[str, Any]]] = None,
    ) -> List[Dict[str, Any]]:
        _ = config, tags, models
        return []

    def get_tags(self, config: Dict[str, Any], models: List[Dict[str, Any]]) -> List[str]:
        _ = config, models
        return ["fake_image_generation"]

    def init(self, config: Dict[str, Any]) -> Dict[str, Any]:
        return {"config": config}

    def initialize_request(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        return list(native_messages), state

    def to_native_messages(
        self,
        messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = state, context
        native: List[Dict[str, Any]] = []
        for message in messages:
            if not isinstance(message, dict):
                continue
            item: Dict[str, Any] = {
                "role": message.get("role", "user"),
                "content": message.get("content", ""),
            }
            if isinstance(message.get("multipartContent"), list):
                item["multipartContent"] = message["multipartContent"]
            native.append(item)
        return native

    def from_native_messages(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        context: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        _ = state, context
        out: List[Dict[str, Any]] = []
        for native_idx, item in enumerate(native_messages):
            if not isinstance(item, dict):
                continue
            text = item.get("content")
            if not isinstance(text, str):
                text = ""
            multipart = item.get("multipartContent")
            message: Dict[str, Any] = {
                "role": item.get("role", "assistant"),
                "content": text,
                "metadata": {"native_indices": [native_idx]},
            }
            if isinstance(multipart, list) and multipart:
                message["multipartContent"] = multipart
            out.append(message)
        return out

    def _request_context(self, state: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        value = state.get("_request_context")
        return value if isinstance(value, dict) else None

    def _session_asset_store(self, state: Dict[str, Any]) -> Any:
        context = self._request_context(state)
        store = context.get("session_asset_store") if isinstance(context, dict) else None
        if store is None:
            raise RuntimeError("[fake_image_generation_provider] session_asset_store missing")
        return store

    def _session_id(self, state: Dict[str, Any]) -> str:
        context = self._request_context(state)
        session_id = context.get("session_id") if isinstance(context, dict) else None
        if not isinstance(session_id, str) or not session_id:
            session_dict = context.get("session") if isinstance(context, dict) else None
            session_id = session_dict.get("session_id") if isinstance(session_dict, dict) else None
        if not isinstance(session_id, str) or not session_id:
            raise RuntimeError("[fake_image_generation_provider] session_id missing")
        return session_id

    def _session_asset_index(self, state: Dict[str, Any]) -> Dict[str, Any]:
        context = self._request_context(state)
        session_dict = context.get("session") if isinstance(context, dict) else None
        metadata = session_dict.get("metadata") if isinstance(session_dict, dict) else {}
        assets = metadata.get(_SESSION_ASSETS_METADATA_KEY) if isinstance(metadata, dict) else {}
        return dict(assets) if isinstance(assets, dict) else {}

    def _generate_assistant_and_patch(
        self,
        state: Dict[str, Any],
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        asset_store = self._session_asset_store(state)
        session_id = self._session_id(state)
        generated = asset_store.store_base64(
            session_id=session_id,
            attachment_type="image",
            filename="generated-fake.png",
            mime_type="image/png",
            data_base64=_GENERATED_PNG_BASE64,
            provider_refs={"fake_image_generation": {"status": "generated"}},
        )
        descriptor = generated.public_descriptor()
        asset_index = self._session_asset_index(state)
        asset_index[generated.asset_id] = descriptor
        assistant = {
            "role": "assistant",
            "content": "FAKE_IMAGE_OK",
            "multipartContent": [
                {
                    "type": "image",
                    "content": {
                        "asset_ref": descriptor["asset_ref"],
                        "filename": descriptor["filename"],
                        "mime_type": descriptor["mime_type"],
                    },
                    "metadata": {
                        "download_plugin_id": _DOWNLOAD_PLUGIN_ID,
                    },
                }
            ],
        }
        patch = {_SESSION_ASSETS_METADATA_KEY: asset_index}
        return assistant, patch

    def call_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]], List[Dict[str, Any]], Dict[str, Any]]:
        _ = request_id
        type(self).call_api_calls += 1
        assistant, patch = self._generate_assistant_and_patch(state)
        new_state = {
            **state,
            "session_metadata_patch": patch,
        }
        return [], [assistant], [*native_messages, assistant], new_state

    def stream_api(
        self,
        native_messages: List[Dict[str, Any]],
        state: Dict[str, Any],
        *,
        request_id: str | None = None,
    ):
        _ = native_messages, state, request_id
        type(self).stream_api_calls += 1
        raise NotImplementedError(
            "[fake_image_generation_provider] stream_api not implemented"
        )


class FakeImageGenerationAttachmentsExtension(ProviderExtensionPlugin):
    name: str = _DOWNLOAD_PLUGIN_ID
    version: str = "0.1.0"
    priority: int = 52

    def required_tags(self) -> List[str]:
        return ["fake_image_generation"]

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
                "inputs": {"asset_id": {"type": "string", "required": True}},
            },
            {
                "id": _DOWNLOAD_ATTACHMENT_ACTION_ID,
                "label": "Download attachment",
                "description": "Download a stored session-owned attachment asset.",
                "inputs": {"asset_id": {"type": "string", "required": True}},
            },
        ]

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

    def _store_attachment_action(
        self,
        session: Any,
        native_messages: List[Dict[str, Any]],
        params: Dict[str, Any],
        context: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        asset_store = self._attachment_asset_store(context)
        record = asset_store.store_base64(
            session_id=session.session_id,
            attachment_type=str(params.get("attachment_type") or "image"),
            filename=str(params.get("filename") or "attachment.png"),
            mime_type=str(params.get("mime_type") or "image/png"),
            data_base64=str(params.get("data_base64") or ""),
            provider_refs={"fake_image_generation": {"status": "local_only"}},
        )
        descriptor = record.public_descriptor()
        client_attachment_id = params.get("client_attachment_id")
        if isinstance(client_attachment_id, str) and client_attachment_id:
            descriptor["client_attachment_id"] = client_attachment_id

        asset_index = self._session_asset_index(session)
        asset_index[record.asset_id] = descriptor
        return {
            "native_messages": list(native_messages),
            "session_metadata": {_SESSION_ASSETS_METADATA_KEY: asset_index},
            "attachment_asset": descriptor,
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
        deleted = asset_store.load(session.session_id, asset_id)
        asset_store.delete(session.session_id, asset_id)
        asset_index.pop(asset_id, None)
        return {
            "native_messages": list(native_messages),
            "session_metadata": {_SESSION_ASSETS_METADATA_KEY: asset_index},
            "deleted_attachment_asset": deleted.public_descriptor(),
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