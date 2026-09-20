from __future__ import annotations

from typing import Any, Dict


IMAGE_ATTACHMENT_ALLOW_BASE64_KEY = "allow_image_attachment_base64"
IMAGE_ATTACHMENT_ALLOW_URL_KEY = "allow_image_attachment_url"
ATTACHMENT_STATE_KEY = "reference_openai_compatible_attachments"


def _normalized_bool(value: Any, *, default: bool) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"1", "true", "yes", "on"}:
            return True
        if normalized in {"0", "false", "no", "off"}:
            return False
    return default


def normalized_image_attachment_settings(config: Dict[str, Any]) -> Dict[str, bool]:
    return {
        IMAGE_ATTACHMENT_ALLOW_BASE64_KEY: _normalized_bool(
            config.get(IMAGE_ATTACHMENT_ALLOW_BASE64_KEY),
            default=True,
        ),
        IMAGE_ATTACHMENT_ALLOW_URL_KEY: _normalized_bool(
            config.get(IMAGE_ATTACHMENT_ALLOW_URL_KEY),
            default=True,
        ),
    }


def resolve_image_attachment_settings(state: Dict[str, Any]) -> Dict[str, bool]:
    attachment_state = state.get(ATTACHMENT_STATE_KEY)
    if isinstance(attachment_state, dict):
        return normalized_image_attachment_settings(attachment_state)

    config = state.get("config") if isinstance(state.get("config"), dict) else {}
    return normalized_image_attachment_settings(config)


def allow_image_attachment_base64(state: Dict[str, Any]) -> bool:
    return resolve_image_attachment_settings(state)[IMAGE_ATTACHMENT_ALLOW_BASE64_KEY]


def allow_image_attachment_url(state: Dict[str, Any]) -> bool:
    return resolve_image_attachment_settings(state)[IMAGE_ATTACHMENT_ALLOW_URL_KEY]
