from __future__ import annotations

import base64
import binascii
import mimetypes
from typing import Any, Callable, Dict, Tuple

from .openai_responses_attachment_assets import session_asset_ref_from_content


SessionAssetResolver = Callable[[Dict[str, Any], str], Tuple[str, str, bytes]]


def decode_base64_bytes(data_base64: str, *, field_name: str) -> bytes:
    try:
        return base64.b64decode(data_base64, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise ValueError(
            f"[openai_responses_provider] invalid base64 payload for {field_name}"
        ) from exc


def decode_data_url(url: str) -> Tuple[str, str]:
    if not isinstance(url, str) or not url.startswith("data:"):
        raise ValueError("[openai_responses_provider] expected data URL")

    header, sep, data_base64 = url.partition(",")
    if not sep:
        raise ValueError("[openai_responses_provider] malformed data URL")
    if not header.endswith(";base64"):
        raise ValueError("[openai_responses_provider] data URL must use base64 encoding")

    mime_type = header[5:-7]
    if not mime_type:
        raise ValueError("[openai_responses_provider] data URL missing MIME type")
    return mime_type, data_base64


def default_filename_for_mime(mime_type: str, default_stem: str) -> str:
    extension = mimetypes.guess_extension(mime_type) or ""
    if extension == ".jpe":
        extension = ".jpg"
    return f"{default_stem}{extension}"


def data_url_from_bytes(*, mime_type: str, payload_bytes: bytes) -> str:
    encoded = base64.b64encode(payload_bytes).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def image_content_to_input_image(
    content: Any,
    *,
    resolve_session_asset: SessionAssetResolver,
) -> Dict[str, Any]:
    if not isinstance(content, dict):
        raise ValueError(
            "[openai_responses_provider] image multipartContent part requires dict content"
        )

    asset_ref = session_asset_ref_from_content(content)
    if asset_ref is not None:
        _, mime_type, payload_bytes = resolve_session_asset(asset_ref, "image")
        return {
            "type": "input_image",
            "image_url": data_url_from_bytes(mime_type=mime_type, payload_bytes=payload_bytes),
        }

    url = content.get("url")
    if not isinstance(url, str) or not url:
        data_base64 = content.get("data_base64")
        mime_type = content.get("mime_type")
        if isinstance(data_base64, str) and data_base64:
            if not isinstance(mime_type, str) or not mime_type:
                raise ValueError(
                    "[openai_responses_provider] image multipartContent part using data_base64 requires mime_type"
                )
            url = f"data:{mime_type};base64,{data_base64}"

    if not isinstance(url, str) or not url:
        raise ValueError(
            "[openai_responses_provider] image multipartContent part requires content.url or content.data_base64"
        )

    return {"type": "input_image", "image_url": url}


def pdf_content_to_input_file(
    content: Any,
    *,
    resolve_session_asset: SessionAssetResolver,
) -> Dict[str, Any]:
    if not isinstance(content, dict):
        raise ValueError(
            "[openai_responses_provider] pdf multipartContent part requires dict content"
        )

    asset_ref = session_asset_ref_from_content(content)
    if asset_ref is not None:
        filename, _, payload_bytes = resolve_session_asset(asset_ref, "pdf")
        return {
            "type": "input_file",
            "file_data": base64.b64encode(payload_bytes).decode("ascii"),
            "filename": filename,
        }

    filename = content.get("filename")
    if not isinstance(filename, str) or not filename:
        raise ValueError(
            "[openai_responses_provider] pdf multipartContent part requires content.filename"
        )

    file_url = content.get("url")
    if isinstance(file_url, str) and file_url:
        if file_url.startswith("data:"):
            mime_type, data_base64 = decode_data_url(file_url)
            if mime_type != "application/pdf":
                raise ValueError(
                    "[openai_responses_provider] pdf multipartContent data URL must use application/pdf"
                )
            return {"type": "input_file", "file_data": data_base64, "filename": filename}
        return {"type": "input_file", "file_url": file_url, "filename": filename}

    data_base64 = content.get("data_base64")
    mime_type = content.get("mime_type")
    if isinstance(data_base64, str) and data_base64:
        if mime_type != "application/pdf":
            raise ValueError(
                "[openai_responses_provider] pdf multipartContent part using data_base64 requires mime_type application/pdf"
            )
        return {"type": "input_file", "file_data": data_base64, "filename": filename}

    raise ValueError(
        "[openai_responses_provider] pdf multipartContent part requires content.url or content.data_base64"
    )