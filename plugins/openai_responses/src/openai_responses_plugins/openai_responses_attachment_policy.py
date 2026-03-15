from __future__ import annotations

from typing import Any, Dict, Optional


ATTACHMENT_UPLOAD_MODE_KEY = "attachment_upload_mode"
IMAGE_ATTACHMENT_MODE_KEY = "image_attachment_mode"
ATTACHMENT_STATE_KEY = "openai_responses_attachments"
ATTACHMENT_UPLOAD_MODE_DIRECT = "direct"
ATTACHMENT_UPLOAD_MODE_UPLOAD = "upload_before_send"
IMAGE_ATTACHMENT_MODE_INLINE = "inline"
IMAGE_ATTACHMENT_MODE_UPLOAD = "upload"
UPLOAD_MODE_VALUES = (ATTACHMENT_UPLOAD_MODE_DIRECT, ATTACHMENT_UPLOAD_MODE_UPLOAD)
IMAGE_ATTACHMENT_MODE_VALUES = (IMAGE_ATTACHMENT_MODE_INLINE, IMAGE_ATTACHMENT_MODE_UPLOAD)
ATTACHMENT_SOURCES_METADATA_KEY = "_openai_responses_attachment_sources"
UPLOADED_ATTACHMENTS_METADATA_KEY = "_openai_responses_uploaded_attachments"


def normalized_attachment_settings(config: Dict[str, Any]) -> Dict[str, str]:
    return {
        IMAGE_ATTACHMENT_MODE_KEY: normalized_image_attachment_mode(config),
        ATTACHMENT_UPLOAD_MODE_KEY: normalized_attachment_upload_mode(config),
    }


def normalized_image_attachment_mode(config: Dict[str, Any]) -> str:
    raw = config.get(IMAGE_ATTACHMENT_MODE_KEY)
    if isinstance(raw, str) and raw in IMAGE_ATTACHMENT_MODE_VALUES:
        return raw
    if config.get(ATTACHMENT_UPLOAD_MODE_KEY) == ATTACHMENT_UPLOAD_MODE_DIRECT:
        return IMAGE_ATTACHMENT_MODE_INLINE
    return IMAGE_ATTACHMENT_MODE_INLINE


def normalized_attachment_upload_mode(config: Dict[str, Any]) -> str:
    raw = config.get(ATTACHMENT_UPLOAD_MODE_KEY)
    if raw == ATTACHMENT_UPLOAD_MODE_DIRECT:
        return ATTACHMENT_UPLOAD_MODE_UPLOAD
    if isinstance(raw, str) and raw == ATTACHMENT_UPLOAD_MODE_UPLOAD:
        return raw
    return ATTACHMENT_UPLOAD_MODE_UPLOAD


def resolve_attachment_upload_mode(state: Dict[str, Any]) -> str:
    attachment_state = state.get(ATTACHMENT_STATE_KEY)
    if isinstance(attachment_state, dict):
        return normalized_attachment_upload_mode(attachment_state)

    config = state.get("config") if isinstance(state.get("config"), dict) else {}
    return normalized_attachment_upload_mode(config)


def resolve_image_attachment_mode(state: Dict[str, Any]) -> str:
    attachment_state = state.get(ATTACHMENT_STATE_KEY)
    if isinstance(attachment_state, dict):
        return normalized_image_attachment_mode(attachment_state)

    config = state.get("config") if isinstance(state.get("config"), dict) else {}
    return normalized_image_attachment_mode(config)


def normalized_multipart_part(part: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    part_type = part.get("type")
    if part_type not in ("image", "pdf"):
        return None

    content = part.get("content")
    metadata = part.get("metadata")
    normalized: Dict[str, Any] = {"type": part_type}
    normalized["content"] = dict(content) if isinstance(content, dict) else {}
    normalized["metadata"] = dict(metadata) if isinstance(metadata, dict) else {}
    return normalized


def attachment_source_map(raw_internal_metadata: Optional[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    if not isinstance(raw_internal_metadata, dict):
        return {}
    raw_sources = raw_internal_metadata.get(ATTACHMENT_SOURCES_METADATA_KEY)
    if not isinstance(raw_sources, list):
        return {}

    source_map: Dict[int, Dict[str, Any]] = {}
    for entry in raw_sources:
        if not isinstance(entry, dict):
            continue
        content_index = entry.get("content_index")
        multipart_part = entry.get("multipart_part")
        if not isinstance(content_index, int) or not isinstance(multipart_part, dict):
            continue
        normalized = normalized_multipart_part(multipart_part)
        if normalized is not None:
            source_map[content_index] = normalized
    return source_map


def uploaded_attachment_map(raw_internal_metadata: Optional[Dict[str, Any]]) -> Dict[int, Dict[str, Any]]:
    if not isinstance(raw_internal_metadata, dict):
        return {}
    raw_uploaded = raw_internal_metadata.get(UPLOADED_ATTACHMENTS_METADATA_KEY)
    if not isinstance(raw_uploaded, list):
        return {}

    uploaded_map: Dict[int, Dict[str, Any]] = {}
    for entry in raw_uploaded:
        if not isinstance(entry, dict):
            continue
        content_index = entry.get("content_index")
        uploaded_part = entry.get("uploaded_part")
        if not isinstance(content_index, int) or not isinstance(uploaded_part, dict):
            continue
        uploaded_map[content_index] = dict(uploaded_part)
    return uploaded_map