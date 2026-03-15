from __future__ import annotations

import base64

import pytest

from agent_app.session_assets import FilesystemSessionAssetStore
from agent_core import Session

from openai_responses_plugins.openai_responses_attachments_extension import (
    OpenAIResponsesAttachmentsExtension,
)


def test_attachment_extension_schema_tags_and_init_defaults() -> None:
    extension = OpenAIResponsesAttachmentsExtension()

    assert extension.name == "openai_responses_attachments"
    assert extension.get_tags({}, []) == ["ext:openai_responses_attachments"]
    assert extension.required_tags() == ["openai_responses"]

    schema = extension.get_config_schema()
    assert schema == {
        "image_attachment_mode": {
            "type": "string",
            "required": False,
            "enum": ["inline", "upload"],
            "default": "inline",
            "description": (
                "Image attachment handling. Use inline to send image content directly, "
                "or upload to route image attachments through the upload-backed path."
            ),
        },
        "attachment_upload_mode": {
            "type": "string",
            "required": False,
            "enum": ["direct", "upload_before_send"],
            "default": "upload_before_send",
            "description": (
                "Internal upload-backed attachment policy. upload_before_send uploads "
                "attachment-backed files through the OpenAI Files API immediately before "
                "the Responses request. Legacy direct is normalized for compatibility."
            ),
        }
    }

    state = extension.init({}, {})
    assert state["openai_responses_attachments"] == {
        "image_attachment_mode": "inline",
        "attachment_upload_mode": "upload_before_send",
    }


def test_attachment_extension_ui_contains_image_mode_select_and_pdf_attachment() -> None:
    extension = OpenAIResponsesAttachmentsExtension()

    elements = extension.get_ui_elements(config={}, tags=["openai_responses"], models=[])

    assert elements == [
        {
            "type": "select",
            "key": "image_attachment_mode",
            "label": "Image Attachment Mode",
            "options": [
                {"value": "inline", "label": "inline"},
                {"value": "upload", "label": "upload"},
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


def test_attachment_extension_ui_hidden_without_provider_tag() -> None:
    extension = OpenAIResponsesAttachmentsExtension()

    assert extension.get_ui_elements(config={}, tags=["other"], models=[]) == []


def test_attachment_extension_initialize_request_normalizes_state() -> None:
    extension = OpenAIResponsesAttachmentsExtension()

    native_messages, state = extension.initialize_request(
        [],
        {
            "config": {"attachment_upload_mode": "upload_before_send"},
            "request": {"payload": {"model": "gpt-5-mini"}},
        },
    )

    assert native_messages == []
    assert state["openai_responses_attachments"] == {
        "image_attachment_mode": "inline",
        "attachment_upload_mode": "upload_before_send",
    }


def test_attachment_extension_normalizes_legacy_direct_mode_to_inline_images() -> None:
    extension = OpenAIResponsesAttachmentsExtension()

    state = extension.init({"attachment_upload_mode": "direct"}, {})

    assert state["openai_responses_attachments"] == {
        "image_attachment_mode": "inline",
        "attachment_upload_mode": "upload_before_send",
    }


def test_attachment_extension_prefers_explicit_image_upload_mode() -> None:
    extension = OpenAIResponsesAttachmentsExtension()

    state = extension.init(
        {"attachment_upload_mode": "direct", "image_attachment_mode": "upload"},
        {},
    )

    assert state["openai_responses_attachments"] == {
        "image_attachment_mode": "upload",
        "attachment_upload_mode": "upload_before_send",
    }


def test_attachment_extension_actions_are_exposed() -> None:
    extension = OpenAIResponsesAttachmentsExtension()

    actions = extension.get_actions({})

    assert actions == [
        {
            "id": "store_attachment",
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
            "id": "delete_attachment",
            "label": "Delete attachment",
            "description": "Delete a stored session-owned attachment asset.",
            "inputs": {
                "asset_id": {"type": "string", "required": True},
            },
        },
    ]


def test_store_attachment_action_persists_session_asset(tmp_path: Path) -> None:
    extension = OpenAIResponsesAttachmentsExtension()
    asset_store = FilesystemSessionAssetStore(tmp_path / "session_assets")
    session = Session(session_id="sess_123", messages=[], metadata={})

    result = extension.execute_action(
        "store_attachment",
        session,
        [],
        {
            "client_attachment_id": "draft_1",
            "attachment_type": "image",
            "filename": "square.png",
            "mime_type": "image/png",
            "data_base64": base64.b64encode(b"png-bytes").decode("ascii"),
        },
        {"session_asset_store": asset_store},
        {},
    )

    asset = result["attachment_asset"]
    asset_ref = asset["asset_ref"]
    asset_id = asset_ref["asset_id"]
    stored = asset_store.load("sess_123", asset_id)

    assert stored.filename == "square.png"
    assert stored.mime_type == "image/png"
    assert stored.provider_refs == {"openai_responses": {"status": "not_uploaded"}}
    assert result["session_metadata"]["session_assets"][asset_id]["client_attachment_id"] == "draft_1"


def test_delete_attachment_action_removes_session_asset(tmp_path: Path) -> None:
    extension = OpenAIResponsesAttachmentsExtension()
    asset_store = FilesystemSessionAssetStore(tmp_path / "session_assets")
    stored = asset_store.store_base64(
        session_id="sess_123",
        attachment_type="pdf",
        filename="brief.pdf",
        mime_type="application/pdf",
        data_base64=base64.b64encode(b"pdf-bytes").decode("ascii"),
        provider_refs={"openai_responses": {"status": "not_uploaded"}},
    )
    session = Session(
        session_id="sess_123",
        messages=[],
        metadata={
            "session_assets": {
                stored.asset_id: {
                    **stored.public_descriptor(),
                    "client_attachment_id": "draft_2",
                }
            }
        },
    )

    result = extension.execute_action(
        "delete_attachment",
        session,
        [],
        {"asset_id": stored.asset_id},
        {"session_asset_store": asset_store},
        {},
    )

    assert result["deleted_attachment_asset"]["asset_ref"]["asset_id"] == stored.asset_id
    assert result["session_metadata"]["session_assets"] == {}
    with pytest.raises(FileNotFoundError):
        asset_store.load("sess_123", stored.asset_id)


def test_store_attachment_action_rejects_invalid_mime_type(tmp_path: Path) -> None:
    extension = OpenAIResponsesAttachmentsExtension()
    asset_store = FilesystemSessionAssetStore(tmp_path / "session_assets")
    session = Session(session_id="sess_123", messages=[], metadata={})

    with pytest.raises(ValueError, match=r"image/\* mime_type"):
        extension.execute_action(
            "store_attachment",
            session,
            [],
            {
                "attachment_type": "image",
                "filename": "not-image.txt",
                "mime_type": "text/plain",
                "data_base64": base64.b64encode(b"x").decode("ascii"),
            },
            {"session_asset_store": asset_store},
            {},
        )