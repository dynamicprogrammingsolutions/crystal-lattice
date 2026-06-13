from __future__ import annotations

import base64
from pathlib import Path

from agent_app.session_assets import FilesystemSessionAssetStore
from agent_core import Session

from openrouter_plugins.openrouter_attachments_extension import (
    OpenRouterAttachmentsExtension,
)


def test_openrouter_attachments_extension_exposes_image_composer_attachment() -> None:
    extension = OpenRouterAttachmentsExtension()

    ui = extension.get_ui_elements(tags=["openrouter"])

    assert ui == [
        {
            "ui_type": "composer_attachment",
            "key": "openrouter_attachments:attachment:image",
            "attachment_type": "image",
            "attachment_action_plugin": "openrouter_attachments",
            "supports_url": True,
            "supports_upload": True,
            "supported_file_types": ["png", "jpg", "jpeg", "webp", "gif"],
            "display_placement": "below",
            "label": "Image",
            "icon": "image",
        }
    ]


def test_openrouter_attachments_extension_actions_include_download() -> None:
    extension = OpenRouterAttachmentsExtension()

    actions = extension.get_actions({})

    assert [action["id"] for action in actions] == [
        "store_attachment",
        "delete_attachment",
        "download_attachment",
    ]


def test_openrouter_attachments_extension_download_returns_base64_payload(
    tmp_path: Path,
) -> None:
    extension = OpenRouterAttachmentsExtension()
    asset_store = FilesystemSessionAssetStore(tmp_path / "session_assets")
    stored = asset_store.store_base64(
        session_id="sess_123",
        attachment_type="image",
        filename="input.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"image-bytes").decode("ascii"),
        provider_refs={"openrouter": {"status": "local_only"}},
    )
    session = Session(
        session_id="sess_123",
        messages=[],
        metadata={
            "session_assets": {
                stored.asset_id: stored.public_descriptor(),
            }
        },
    )

    result = extension.execute_action(
        "download_attachment",
        session,
        [],
        {"asset_id": stored.asset_id},
        {"session_asset_store": asset_store},
        {},
    )

    assert result["attachment_asset"]["asset_ref"]["asset_id"] == stored.asset_id
    assert result["data_base64"] == base64.b64encode(b"image-bytes").decode("ascii")