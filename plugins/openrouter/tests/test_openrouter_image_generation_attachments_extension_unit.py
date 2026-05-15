from __future__ import annotations

import base64
from pathlib import Path

from agent_app.session_assets import FilesystemSessionAssetStore
from agent_core import Session

from openrouter_plugins.openrouter_image_generation_attachments_extension import (
    OpenRouterImageGenerationAttachmentsExtension,
)


def test_openrouter_image_generation_attachment_actions_include_download() -> None:
    extension = OpenRouterImageGenerationAttachmentsExtension()

    actions = extension.get_actions({})

    assert [action["id"] for action in actions] == [
        "store_attachment",
        "delete_attachment",
        "download_attachment",
    ]


def test_openrouter_image_generation_attachment_download_returns_base64_payload(
    tmp_path: Path,
) -> None:
    extension = OpenRouterImageGenerationAttachmentsExtension()
    asset_store = FilesystemSessionAssetStore(tmp_path / "session_assets")
    stored = asset_store.store_base64(
        session_id="sess_123",
        attachment_type="image",
        filename="output.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"image-bytes").decode("ascii"),
        provider_refs={"openrouter_image_generation": {"status": "generated"}},
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