from __future__ import annotations

import base64

from openai_responses_plugins.openai_responses_attachment_parts import (
    decode_base64_bytes,
    decode_data_url,
    image_content_to_input_image,
    pdf_content_to_input_file,
)
from openai_responses_plugins.openai_responses_attachment_policy import (
    ATTACHMENT_SOURCES_METADATA_KEY,
    ATTACHMENT_UPLOAD_MODE_KEY,
    IMAGE_ATTACHMENT_MODE_KEY,
    attachment_source_map,
    normalized_attachment_settings,
    resolve_image_attachment_mode,
    uploaded_attachment_map,
    UPLOADED_ATTACHMENTS_METADATA_KEY,
)


def test_normalized_attachment_settings_maps_legacy_direct_to_inline_upload_before_send() -> None:
    normalized = normalized_attachment_settings({ATTACHMENT_UPLOAD_MODE_KEY: "direct"})

    assert normalized[IMAGE_ATTACHMENT_MODE_KEY] == "inline"
    assert normalized[ATTACHMENT_UPLOAD_MODE_KEY] == "upload_before_send"


def test_resolve_image_attachment_mode_prefers_extension_state() -> None:
    state = {
        "config": {IMAGE_ATTACHMENT_MODE_KEY: "inline"},
        "openai_responses_attachments": {IMAGE_ATTACHMENT_MODE_KEY: "upload"},
    }

    assert resolve_image_attachment_mode(state) == "upload"


def test_attachment_metadata_maps_ignore_invalid_entries() -> None:
    metadata = {
        ATTACHMENT_SOURCES_METADATA_KEY: [
            {"content_index": 0, "multipart_part": {"type": "image", "content": {"url": "x"}}},
            {"content_index": "bad", "multipart_part": {"type": "pdf"}},
        ],
        UPLOADED_ATTACHMENTS_METADATA_KEY: [
            {"content_index": 1, "uploaded_part": {"type": "input_file", "file_id": "file_123"}},
            {"content_index": None, "uploaded_part": {"type": "input_image"}},
        ],
    }

    assert attachment_source_map(metadata) == {
        0: {"type": "image", "content": {"url": "x"}, "metadata": {}}
    }
    assert uploaded_attachment_map(metadata) == {
        1: {"type": "input_file", "file_id": "file_123"}
    }


def test_image_content_to_input_image_uses_session_asset_resolver() -> None:
    part = image_content_to_input_image(
        {
            "asset_ref": {
                "kind": "session_asset",
                "session_id": "sess_1",
                "asset_id": "asset_1",
                "attachment_type": "image",
            }
        },
        resolve_session_asset=lambda asset_ref, expected_type: (
            "image.png",
            "image/png",
            b"png-bytes",
        ),
    )

    assert part["type"] == "input_image"
    assert part["image_url"] == "data:image/png;base64," + base64.b64encode(b"png-bytes").decode("ascii")


def test_pdf_content_to_input_file_accepts_data_url() -> None:
    pdf_bytes = base64.b64encode(b"pdf-bytes").decode("ascii")

    part = pdf_content_to_input_file(
        {
            "filename": "doc.pdf",
            "url": f"data:application/pdf;base64,{pdf_bytes}",
        },
        resolve_session_asset=lambda asset_ref, expected_type: ("", "", b""),
    )

    assert part == {
        "type": "input_file",
        "file_data": pdf_bytes,
        "filename": "doc.pdf",
    }


def test_decode_helpers_validate_payloads() -> None:
    assert decode_data_url("data:text/plain;base64,SGk=") == ("text/plain", "SGk=")
    assert decode_base64_bytes("SGk=", field_name="field") == b"Hi"