from __future__ import annotations

import base64
from pathlib import Path

import pytest

from agent_app.session_assets import FilesystemSessionAssetStore

from reference_openai_compatible_provider.provider import OpenAICompatibleProvider


def test_provider_converts_image_url_and_base64_parts() -> None:
    provider = OpenAICompatibleProvider()
    state = provider.init({"model": "test-model"})

    native = provider.to_native_messages(
        [
            {
                "role": "user",
                "content": "describe",
                "multipartContent": [
                    {
                        "type": "image",
                        "content": {"url": "https://example.com/cat.png"},
                        "metadata": {},
                    },
                    {
                        "type": "image",
                        "content": {
                            "data_base64": "QUJDRA==",
                            "mime_type": "image/png",
                        },
                        "metadata": {},
                    },
                ],
            }
        ],
        state,
    )

    assert native == [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "describe"},
                {"type": "image_url", "image_url": {"url": "https://example.com/cat.png"}},
                {"type": "image_url", "image_url": {"url": "data:image/png;base64,QUJDRA=="}},
            ],
        }
    ]


def test_provider_converts_session_asset_refs_to_data_urls(tmp_path: Path) -> None:
    provider = OpenAICompatibleProvider()
    asset_store = FilesystemSessionAssetStore(tmp_path / "session_assets")
    image_record = asset_store.store_base64(
        session_id="sess_asset",
        attachment_type="image",
        filename="square.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"image-bytes").decode("ascii"),
    )
    state = provider.init({"model": "test-model", "_session_asset_store": asset_store})

    native = provider.to_native_messages(
        [
            {
                "role": "user",
                "content": "describe",
                "multipartContent": [
                    {
                        "type": "image",
                        "content": {
                            "asset_ref": image_record.asset_ref(),
                            "filename": image_record.filename,
                            "mime_type": image_record.mime_type,
                        },
                        "metadata": {},
                    }
                ],
            }
        ],
        state,
    )

    assert native[0]["content"][1] == {
        "type": "image_url",
        "image_url": {
            "url": "data:image/png;base64,"
            + base64.b64encode(b"image-bytes").decode("ascii")
        },
    }


def test_provider_rejects_disabled_base64_images() -> None:
    provider = OpenAICompatibleProvider()
    state = provider.init(
        {
            "model": "test-model",
            "allow_image_attachment_base64": False,
            "allow_image_attachment_url": True,
        }
    )

    with pytest.raises(ValueError, match="base64"):
        provider.to_native_messages(
            [
                {
                    "role": "user",
                    "content": "",
                    "multipartContent": [
                        {
                            "type": "image",
                            "content": {
                                "data_base64": "QUJDRA==",
                                "mime_type": "image/png",
                            },
                            "metadata": {},
                        }
                    ],
                }
            ],
            state,
        )


def test_provider_rejects_disabled_remote_image_urls() -> None:
    provider = OpenAICompatibleProvider()
    state = provider.init(
        {
            "model": "test-model",
            "allow_image_attachment_base64": True,
            "allow_image_attachment_url": False,
        }
    )

    with pytest.raises(ValueError, match="remote image URL"):
        provider.to_native_messages(
            [
                {
                    "role": "user",
                    "content": "",
                    "multipartContent": [
                        {
                            "type": "image",
                            "content": {"url": "https://example.com/cat.png"},
                            "metadata": {},
                        }
                    ],
                }
            ],
            state,
        )


def test_provider_round_trips_image_content_from_native() -> None:
    provider = OpenAICompatibleProvider()
    messages = provider.from_native_messages(
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "describe"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/cat.png"},
                    },
                ],
            }
        ],
        {},
    )

    assert messages == [
        {
            "role": "user",
            "content": "describe",
            "multipartContent": [
                {
                    "type": "image",
                    "content": {"url": "https://example.com/cat.png"},
                    "metadata": {},
                }
            ],
            "metadata": {"native_indices": [0]},
        }
    ]