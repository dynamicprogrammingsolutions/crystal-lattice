from __future__ import annotations

import base64
from typing import Any, Callable, Dict, Tuple

from .attachment_assets import session_asset_ref_from_content


SessionAssetResolver = Callable[[Dict[str, Any], str], Tuple[str, str, bytes]]


def is_data_url(url: str) -> bool:
    return isinstance(url, str) and url.startswith("data:")


def data_url_from_bytes(*, mime_type: str, payload_bytes: bytes) -> str:
    encoded = base64.b64encode(payload_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def image_content_to_image_url_part(
    content: Any,
    *,
    resolve_session_asset: SessionAssetResolver,
    allow_base64: bool,
    allow_url: bool,
) -> Dict[str, Any]:
    if not isinstance(content, dict):
        raise ValueError(
            "[reference_openai_compatible_provider] image multipartContent part requires dict content"
        )

    asset_ref = session_asset_ref_from_content(content)
    if asset_ref is not None:
        if not allow_base64:
            raise ValueError(
                "[reference_openai_compatible_provider] asset_ref image attachments require allow_image_attachment_base64=true"
            )
        _, mime_type, payload_bytes = resolve_session_asset(asset_ref, "image")
        return {
            "type": "image_url",
            "image_url": {
                "url": data_url_from_bytes(
                    mime_type=mime_type,
                    payload_bytes=payload_bytes,
                )
            },
        }

    url = content.get("url")
    if isinstance(url, str) and url:
        if is_data_url(url):
            if not allow_base64:
                raise ValueError(
                    "[reference_openai_compatible_provider] data URL image attachments are disabled by config"
                )
        elif not allow_url:
            raise ValueError(
                "[reference_openai_compatible_provider] remote image URL attachments are disabled by config"
            )
        return {"type": "image_url", "image_url": {"url": url}}

    data_base64 = content.get("data_base64")
    mime_type = content.get("mime_type")
    if isinstance(data_base64, str) and data_base64:
        if not allow_base64:
            raise ValueError(
                "[reference_openai_compatible_provider] inline base64 image attachments are disabled by config"
            )
        if not isinstance(mime_type, str) or not mime_type:
            raise ValueError(
                "[reference_openai_compatible_provider] image multipartContent part using data_base64 requires mime_type"
            )
        return {
            "type": "image_url",
            "image_url": {"url": f"data:{mime_type};base64,{data_base64}"},
        }

    raise ValueError(
        "[reference_openai_compatible_provider] image multipartContent part requires content.url, content.data_base64, or content.asset_ref"
    )