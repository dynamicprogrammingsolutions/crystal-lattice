from __future__ import annotations

import base64
from pathlib import Path

from agent_app.session_assets import FilesystemSessionAssetStore
from agent_core import Session

from reference_openai_compatible_provider.attachments_extension import (
    OpenAICompatibleAttachmentsExtension,
)
from reference_openai_compatible_provider.attachment_policy import (
    ATTACHMENT_STATE_KEY,
    IMAGE_ATTACHMENT_ALLOW_BASE64_KEY,
    IMAGE_ATTACHMENT_ALLOW_URL_KEY,
)


def test_attachment_extension_exposes_image_ui_based_on_capabilities() -> None:
    extension = OpenAICompatibleAttachmentsExtension()

    both_enabled = extension.get_ui_elements(
        {IMAGE_ATTACHMENT_ALLOW_BASE64_KEY: True, IMAGE_ATTACHMENT_ALLOW_URL_KEY: True},
        ["provider:openai_compatible"],
        [],
    )
    assert both_enabled[0]["supports_upload"] is True
    assert both_enabled[0]["supports_url"] is True

    url_only = extension.get_ui_elements(
        {IMAGE_ATTACHMENT_ALLOW_BASE64_KEY: False, IMAGE_ATTACHMENT_ALLOW_URL_KEY: True},
        ["provider:openai_compatible"],
        [],
    )
    assert url_only[0]["supports_upload"] is False
    assert url_only[0]["supports_url"] is True

    disabled = extension.get_ui_elements(
        {IMAGE_ATTACHMENT_ALLOW_BASE64_KEY: False, IMAGE_ATTACHMENT_ALLOW_URL_KEY: False},
        ["provider:openai_compatible"],
        [],
    )
    assert disabled == []


def test_attachment_extension_initializes_normalized_state() -> None:
    extension = OpenAICompatibleAttachmentsExtension()
    state = extension.init(
        {IMAGE_ATTACHMENT_ALLOW_BASE64_KEY: "false"},
        {},
    )
    assert state[ATTACHMENT_STATE_KEY] == {
        IMAGE_ATTACHMENT_ALLOW_BASE64_KEY: False,
        IMAGE_ATTACHMENT_ALLOW_URL_KEY: True,
    }


def test_store_attachment_action_persists_session_asset(tmp_path: Path) -> None:
    extension = OpenAICompatibleAttachmentsExtension()
    asset_store = FilesystemSessionAssetStore(tmp_path / "session_assets")
    session = Session(session_id="s1", messages=[], metadata={})

    result = extension.execute_action(
        "store_attachment",
        session,
        [],
        {
            "client_attachment_id": "draft_1",
            "attachment_type": "image",
            "filename": "red.png",
            "mime_type": "image/png",
            "data_base64": base64.b64encode(b"image-bytes").decode("ascii"),
        },
        {"session_asset_store": asset_store},
        {},
    )

    asset = result["attachment_asset"]
    asset_id = asset["asset_ref"]["asset_id"]
    assert asset["client_attachment_id"] == "draft_1"
    assert result["session_metadata"]["session_assets"][asset_id]["filename"] == "red.png"
    assert asset_store.load_bytes("s1", asset_id) == b"image-bytes"


def test_delete_attachment_action_removes_session_asset(tmp_path: Path) -> None:
    extension = OpenAICompatibleAttachmentsExtension()
    asset_store = FilesystemSessionAssetStore(tmp_path / "session_assets")
    stored = asset_store.store_base64(
        session_id="s1",
        attachment_type="image",
        filename="red.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"image-bytes").decode("ascii"),
    )
    session = Session(
        session_id="s1",
        messages=[],
        metadata={
            "session_assets": {
                stored.asset_id: stored.public_descriptor(),
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
