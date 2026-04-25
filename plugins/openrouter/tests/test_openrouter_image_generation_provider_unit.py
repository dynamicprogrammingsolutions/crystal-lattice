from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict, List

import pytest

from agent_app.session_assets import FilesystemSessionAssetStore

from openrouter_plugins.openrouter_image_generation_provider import (
    OpenRouterImageGenerationProvider,
)


def test_openrouter_image_generation_provider_rejects_multi_turn_history() -> None:
    provider = OpenRouterImageGenerationProvider()
    state = provider.init(
        {
            "model": "google/gemini-2.5-flash-image",
            "api_key": "test",
        }
    )

    core_messages: List[Dict[str, Any]] = [
        {"role": "user", "content": "first"},
        {"role": "user", "content": "second"},
    ]

    with pytest.raises(ValueError, match="exactly one user message"):
        native = provider.to_native_messages(core_messages, state)
        provider._validate_v1_input(native)


def test_openrouter_image_generation_provider_resolves_asset_ref_input_image(
    tmp_path: Path,
) -> None:
    provider = OpenRouterImageGenerationProvider()
    asset_store = FilesystemSessionAssetStore(tmp_path / "session_assets")
    record = asset_store.store_base64(
        session_id="sess_123",
        attachment_type="image",
        filename="input.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"png-bytes").decode("ascii"),
        provider_refs={},
    )
    state = provider.init(
        {
            "model": "google/gemini-2.5-flash-image",
            "api_key": "test",
        }
    )

    native = provider.to_native_messages(
        [
            {
                "role": "user",
                "content": "edit this",
                "multipartContent": [
                    {
                        "type": "image",
                        "content": {
                            "asset_ref": record.asset_ref(),
                        },
                    }
                ],
            }
        ],
        state,
        context={
            "session_id": "sess_123",
            "session_asset_store": asset_store,
        },
    )

    assert native == [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": "edit this"},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": "data:image/png;base64,cG5nLWJ5dGVz",
                    },
                },
            ],
        }
    ]


def test_openrouter_image_generation_provider_from_native_messages_preserves_user_image_inputs() -> None:
    provider = OpenRouterImageGenerationProvider()
    state = provider.init(
        {
            "model": "google/gemini-2.5-flash-image",
            "api_key": "test",
        }
    )

    messages = provider.from_native_messages(
        [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "edit this"},
                    {
                        "type": "image_url",
                        "image_url": {"url": "https://example.com/input.png"},
                    },
                ],
            }
        ],
        state,
    )

    assert messages == [
        {
            "role": "user",
            "content": "edit this",
            "multipartContent": [
                {
                    "type": "image",
                    "content": {"url": "https://example.com/input.png"},
                    "metadata": {},
                }
            ],
            "metadata": {"native_indices": [0]},
        }
    ]


def test_openrouter_image_generation_provider_get_models_queries_image_output_models(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    provider = OpenRouterImageGenerationProvider()
    captured: Dict[str, Any] = {}

    class _FakeResponse:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> Dict[str, Any]:
            return {
                "data": [
                    {"id": "black-forest-labs/flux.2-klein-4b", "name": "Flux Klein"},
                ]
            }

    def _fake_get(url: str, *, params: Dict[str, Any], timeout: int) -> _FakeResponse:
        captured["url"] = url
        captured["params"] = params
        captured["timeout"] = timeout
        return _FakeResponse()

    monkeypatch.setattr("requests.get", _fake_get)

    models = provider.get_models({"base_url": "https://openrouter.ai/api/v1"})

    assert captured["url"] == "https://openrouter.ai/api/v1/models"
    assert captured["params"] == {"output_modalities": "image"}
    assert captured["timeout"] == 10
    assert models == [
        {"id": "black-forest-labs/flux.2-klein-4b", "name": "Flux Klein"},
    ]