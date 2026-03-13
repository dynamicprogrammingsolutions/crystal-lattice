from __future__ import annotations

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
        "attachment_upload_mode": {
            "type": "string",
            "required": False,
            "enum": ["direct", "upload_before_send"],
            "default": "direct",
            "description": (
                "Attachment send strategy. Use upload_before_send to upload image/PDF "
                "attachments through the OpenAI Files API before the Responses request."
            ),
        }
    }

    state = extension.init({}, {})
    assert state["openai_responses_attachments"] == {"attachment_upload_mode": "direct"}


def test_attachment_extension_ui_contains_mode_select_and_pdf_attachment() -> None:
    extension = OpenAIResponsesAttachmentsExtension()

    elements = extension.get_ui_elements(config={}, tags=["openai_responses"], models=[])

    assert elements == [
        {
            "type": "select",
            "key": "attachment_upload_mode",
            "label": "Attachment Upload Mode",
            "options": [
                {"value": "direct", "label": "direct"},
                {"value": "upload_before_send", "label": "upload_before_send"},
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
        "attachment_upload_mode": "upload_before_send"
    }