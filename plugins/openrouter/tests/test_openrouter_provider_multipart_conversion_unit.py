from __future__ import annotations

import base64
from pathlib import Path
from typing import Any, Dict, List

import pytest
import requests

from agent_app.session_assets import FilesystemSessionAssetStore
from agent_core.tool_result_payloads import (
    FORMAT_OPENAI_CHAT_COMPLETIONS,
    TOOL_RESULT_FIELD,
    make_provider_native_tool_result,
)
from openrouter_plugins.openrouter_provider import OpenRouterProvider


def test_openrouter_provider_converts_image_multipart_content() -> None:
    provider = OpenRouterProvider()
    state = provider.init(
        {
            "model": "google/gemini-2.5-flash-lite",
            "api_key": "test",
            "base_url": "https://openrouter.ai/api/v1",
        }
    )

    core_messages: List[Dict[str, Any]] = [
        {
            "role": "user",
            "content": "What's in this image?",
            "multipartContent": [
                {
                    "type": "image",
                    "content": {"url": "https://example.com/image.png"},
                    "metadata": {},
                }
            ],
        }
    ]

    native = provider.to_native_messages(core_messages, state)
    assert len(native) == 1
    msg = native[0]
    assert msg.get("role") == "user"
    content = msg.get("content")
    assert isinstance(content, list)
    assert content[0] == {"type": "text", "text": "What's in this image?"}
    assert content[1] == {
        "type": "image_url",
        "image_url": {"url": "https://example.com/image.png"},
    }


def test_openrouter_provider_preserves_provider_native_tool_result_content() -> None:
    provider = OpenRouterProvider()
    state = provider.init(
        {
            "model": "moonshotai/kimi-k2.5",
            "api_key": "test",
            "base_url": "https://openrouter.ai/api/v1",
        }
    )
    payload = make_provider_native_tool_result(
        format=FORMAT_OPENAI_CHAT_COMPLETIONS,
        content=[
            {"type": "text", "text": '<image path="sample.png">'},
            {
                "type": "image_url",
                "image_url": {"url": "data:image/png;base64,QUJDRA=="},
            },
            {"type": "text", "text": "</image>"},
        ],
    )

    native = provider.to_native_messages(
        [
            {
                "role": "tool",
                "content": "opened image",
                TOOL_RESULT_FIELD: payload,
                "metadata": {"tool_call_id": "call_1"},
            }
        ],
        state,
    )

    assert native == [
        {
            "role": "tool",
            "content": payload["content"],
            "tool_call_id": "call_1",
        }
    ]
    assert "QUJDRA==" not in native[0]["content"][0]["text"]
    assert "QUJDRA==" not in native[0]["content"][2]["text"]


def test_openrouter_provider_expands_request_override_asset_refs_before_send(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    provider = OpenRouterProvider()
    asset_store = FilesystemSessionAssetStore(tmp_path / "session_assets")
    image_record = asset_store.store_base64(
        session_id="sess_asset",
        attachment_type="image",
        filename="square.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"image-bytes").decode("ascii"),
    )
    state = provider.init(
        {
            "model": "moonshotai/kimi-k2.5",
            "api_key": "test",
            "base_url": "https://openrouter.ai/api/v1",
        }
    )
    native: List[Dict[str, Any]] = [
        {
            "role": "tool",
            "tool_call_id": "call_1",
            "content": [
                {"type": "text", "text": '<image path="square.png">'},
                {
                    "type": "image_url",
                    "image_url": {
                        "asset_ref": image_record.asset_ref(),
                        "filename": image_record.filename,
                        "mime_type": image_record.mime_type,
                    },
                },
                {"type": "text", "text": "</image>"},
            ],
        }
    ]
    _, initialized = provider.initialize_request(
        native,
        state,
        context={"session_asset_store": asset_store, "session_id": "sess_asset"},
    )
    assert "asset_ref" in repr(initialized["request"]["messages"])
    assert "data:image/png;base64" not in repr(initialized["request"]["messages"])
    # Simulate a later feature rebuilding request["messages"] from compact
    # durable native history after provider initialize_request has run.
    initialized = {
        **initialized,
        "_request_context": {
            "session_asset_store": asset_store,
            "session_id": "sess_asset",
        },
        "request": {**initialized["request"], "messages": native},
    }

    captured: Dict[str, Any] = {}

    class Response:
        ok = True
        status_code = 200
        text = "{}"
        encoding = "utf-8"

        def json(self) -> Dict[str, Any]:
            return {"choices": [{"message": {"role": "assistant", "content": "ok"}}]}

        def close(self) -> None:
            pass

    def post(self: requests.Session, *args: Any, **kwargs: Any) -> Response:
        captured["json"] = kwargs.get("json")
        return Response()

    monkeypatch.setattr(requests.Session, "post", post)

    provider.call_api(native, initialized)

    payload = captured["json"]
    assert isinstance(payload, dict)
    assert "asset_ref" not in repr(payload)
    assert "data:image/png;base64," + base64.b64encode(b"image-bytes").decode(
        "ascii"
    ) in repr(payload)
