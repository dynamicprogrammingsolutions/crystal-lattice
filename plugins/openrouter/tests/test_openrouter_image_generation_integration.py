from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
OPENROUTER_SRC = ROOT / "plugins/openrouter/src"
if str(OPENROUTER_SRC) not in sys.path:
    sys.path.insert(0, str(OPENROUTER_SRC))

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from agent_app.session_assets import FilesystemSessionAssetStore  # noqa: E402
from agent_core import AgentCore  # noqa: E402
from openrouter_plugins.openrouter_image_generation_provider import (  # noqa: E402
    OpenRouterImageGenerationProvider,
)


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = os.getenv("OPENROUTER_BASE_URL") or "https://openrouter.ai/api/v1"


@pytest.fixture(scope="module")
def ensure_api_key() -> str:
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set; skipping OpenRouter image-generation integration tests")
    return OPENROUTER_API_KEY


def _assert_generated_image_response(
    session_like: Any,
    responses: list[dict[str, Any]],
    asset_store: FilesystemSessionAssetStore,
) -> None:
    assert responses, "expected at least one final response"
    assistant = responses[-1]
    assert assistant["role"] == "assistant"
    multipart = assistant.get("multipartContent")
    assert isinstance(multipart, list) and multipart, "expected assistant multipart image output"

    image_part = multipart[0]
    assert image_part.get("type") == "image"
    content = image_part.get("content")
    assert isinstance(content, dict)
    asset_ref = content.get("asset_ref")
    assert isinstance(asset_ref, dict)
    assert asset_ref.get("kind") == "session_asset"

    record = asset_store.load(asset_ref["session_id"], asset_ref["asset_id"])
    payload = asset_store.load_bytes(asset_ref["session_id"], asset_ref["asset_id"])
    assert record.mime_type.startswith("image/")
    assert len(payload) > 1000

    metadata = getattr(session_like, "metadata", None) or {}
    session_assets = metadata.get("session_assets") if isinstance(metadata, dict) else None
    assert isinstance(session_assets, dict)
    assert asset_ref["asset_id"] in session_assets


def _skip_on_access_error(exc: Exception, model: str) -> None:
    message = str(exc)
    if "402 Client Error" in message or "Payment Required" in message:
        pytest.skip(f"OpenRouter account could not access {model}: {message}")


@pytest.mark.integration
@pytest.mark.openrouter
@pytest.mark.parametrize(
    ("model", "config_extras", "prompt"),
    [
        (
            "black-forest-labs/flux.2-klein-4b",
            {"aspect_ratio": "1:1"},
            "Generate a simple flat icon of a red square with a white border on a neutral background.",
        ),
        (
            "sourceful/riverflow-v2-fast-preview",
            {"image_config": {"image_size": "1K"}},
            "Generate a simple isometric blue cube sticker on a plain background.",
        ),
        (
            "google/gemini-2.5-flash-image",
            {"output_text": True, "aspect_ratio": "1:1"},
            "Generate a clean product-shot style green mug on white background and briefly describe it.",
        ),
    ],
)
def test_openrouter_image_generation_provider_real_api_non_streaming(
    ensure_api_key: str,
    tmp_path: Path,
    model: str,
    config_extras: Dict[str, Any],
    prompt: str,
) -> None:
    provider = OpenRouterImageGenerationProvider()
    core = AgentCore()
    core.register_provider(OpenRouterImageGenerationProvider)

    session_assets_dir = tmp_path / "session_assets"
    asset_store = FilesystemSessionAssetStore(session_assets_dir)
    session = core.create_session()
    session = core.add_message(session, "user", prompt)

    config = {
        "model": model,
        "api_key": ensure_api_key,
        "base_url": BASE_URL,
        "timeout": 180,
        **config_extras,
    }

    try:
        new_session, responses = core.send_request(
            session,
            config,
            context={
                "session_id": session.session_id,
                "session": session.to_dict(),
                "session_asset_store": asset_store,
            },
        )
    except RuntimeError as exc:
        _skip_on_access_error(exc, model)
        raise

    _assert_generated_image_response(new_session, responses, asset_store)


def _write_image_generation_config(tmp_path: Path, api_key: str, model: str) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "openrouter_image": {
                "provider": "openrouter_image_generation",
                "model": model,
                "api_key": api_key,
                "base_url": BASE_URL,
                "timeout": 180,
                "aspect_ratio": "1:1",
            }
        },
        "plugins": [
            "openrouter_plugins.openrouter_image_generation_provider.OpenRouterImageGenerationProvider",
            "openrouter_plugins.openrouter_image_generation_attachments_extension.OpenRouterImageGenerationAttachmentsExtension",
        ],
        "agents": {"default": {"provider": "openrouter_image"}},
    }
    path = tmp_path / "openrouter_image_generation_config.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


@pytest.mark.integration
@pytest.mark.openrouter
def test_openrouter_image_generation_application_non_streaming_real_api(
    ensure_api_key: str,
    tmp_path: Path,
) -> None:
    app = AgentApplication(
        str(_write_image_generation_config(tmp_path, ensure_api_key, "black-forest-labs/flux.2-klein-4b")),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )
    try:
        core, base_config, session = app.create_session("default")
        session = core.add_message(
            session,
            "user",
            "Generate a tiny yellow triangle icon on a plain background.",
            {},
            app.resolve_effective_config(base_config, session),
        )
        app.save_session(session)

        events = list(app.send_request(core, session, base_config, stream=False))
        error_events = [event for event in events if event.get("type") == "error"]
        if error_events:
            detail = error_events[-1].get("detail")
            if isinstance(detail, str) and ("402" in detail or "Payment Required" in detail):
                pytest.skip(f"OpenRouter account could not access application test model: {detail}")
        final_events = [event for event in events if event.get("type") == "final"]
        assert final_events, "expected final event from non-streaming app request"

        final_messages = final_events[-1]["messages"]
        stored_session = app.load_session_record(session.session_id)
        assert stored_session is not None
        _assert_generated_image_response(
            stored_session,
            final_messages,
            app.get_session_asset_store(),
        )
    finally:
        app.close()