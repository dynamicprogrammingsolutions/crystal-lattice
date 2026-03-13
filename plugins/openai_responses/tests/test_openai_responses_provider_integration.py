from __future__ import annotations

import base64
import os
from pathlib import Path
import subprocess

import pytest
from dotenv import load_dotenv

from agent_core import AgentCore
from openai_responses_plugins.openai_responses_provider import OpenAIResponsesProvider


_ONE_PIXEL_GIF_DATA_URL = (
    "data:image/gif;base64,"
    "R0lGODlhAQABAIABAP8AAP///yH5BAEAAAEALAAAAAABAAEAAAICRAEAOw=="
)


def _vision_test_config(api_key: str) -> dict[str, object]:
    return {
        "model": os.getenv("OPENAI_RESPONSES_VISION_MODEL") or "gpt-5-mini",
        "api_key": api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
    }


def _make_data_url(path: Path, mime_type: str) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _generate_red_square_png(tmp_path: Path) -> Path:
    image_path = tmp_path / "red-square.png"
    try:
        subprocess.run(
            [
                "magick",
                "-size",
                "96x96",
                "xc:red",
                str(image_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        pytest.skip("magick not available; skipping generated-image integration test")
    except subprocess.CalledProcessError as exc:
        pytest.fail(f"failed to generate test image with ImageMagick: {exc.stderr.strip()}")

    if not image_path.exists():
        pytest.fail("ImageMagick did not create the expected test image")
    return image_path


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    repo_root = Path(__file__).resolve().parents[3]
    load_dotenv(repo_root / ".env")

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI integration tests")
    return api_key


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_get_models_real_api(ensure_openai_api_key: str) -> None:
    _ = ensure_openai_api_key

    provider = OpenAIResponsesProvider()
    config = {
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
    }

    models = provider.get_models(config)

    assert isinstance(models, list)
    assert models
    assert all(isinstance(model.get("id"), str) and model["id"] for model in models[:20])


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_non_streaming_gpt5mini_real_api(ensure_openai_api_key: str) -> None:
    core = AgentCore()
    core.register_provider(OpenAIResponsesProvider)

    config = {
        "model": "gpt-5-mini",
        "api_key": ensure_openai_api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
    }

    session = core.create_session()
    session = core.add_message(session, "user", "Reply with exactly: OPENAI_RESPONSES_OK")

    new_session, responses = core.send_request(session, config)

    assert new_session is not None
    assert responses

    final = responses[-1]
    assert final.get("role") == "assistant"
    assert isinstance(final.get("content"), str)
    assert "OPENAI_RESPONSES_OK" in final["content"]

    native_history = (new_session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert any(isinstance(item, dict) and item.get("type") == "message" for item in native_history)


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_streaming_gpt5mini_real_api(ensure_openai_api_key: str) -> None:
    core = AgentCore()
    core.register_provider(OpenAIResponsesProvider)

    config = {
        "model": "gpt-5-mini",
        "api_key": ensure_openai_api_key,
        "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
        "timeout": 120,
    }

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly: OPENAI_RESPONSES_STREAM_OK",
    )

    partial_count = 0
    final_session = None
    final_message = None

    for chunk in core.send_request_stream(session, config):
        if chunk["type"] == "partial":
            content = (chunk.get("message") or {}).get("content")
            if isinstance(content, str) and content:
                partial_count += 1
        elif chunk["type"] == "final":
            final_session = chunk.get("session")
            messages = chunk.get("messages") or []
            if messages:
                final_message = messages[-1]

    assert partial_count > 0
    assert final_session is not None
    assert final_message is not None
    assert final_message.get("role") == "assistant"
    assert isinstance(final_message.get("content"), str)
    assert "OPENAI_RESPONSES_STREAM_OK" in final_message["content"]

    native_history = (final_session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert any(isinstance(item, dict) and item.get("type") == "message" for item in native_history)
    assert all(
        not (
            isinstance(item, dict)
            and isinstance(item.get("type"), str)
            and item["type"].startswith("response.")
        )
        for item in native_history
    )


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_image_data_url_real_api(ensure_openai_api_key: str) -> None:
    core = AgentCore()
    core.register_provider(OpenAIResponsesProvider)

    config = _vision_test_config(ensure_openai_api_key)

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Reply with exactly IMAGE_ATTACHMENT_OK if you received one image attachment.",
        config=config,
        multipart_content=[
            {
                "type": "image",
                "content": {
                    "url": _ONE_PIXEL_GIF_DATA_URL,
                    "mime_type": "image/gif",
                    "filename": "pixel.gif",
                },
                "metadata": {},
            }
        ],
    )

    new_session, responses = core.send_request(session, config)

    assert new_session is not None
    assert responses

    final = responses[-1]
    assert final.get("role") == "assistant"
    assert isinstance(final.get("content"), str)
    assert "IMAGE_ATTACHMENT_OK" in final["content"]

    native_history = (new_session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert any(
        isinstance(item, dict)
        and item.get("type") == "message"
        and any(
            isinstance(part, dict) and part.get("type") == "input_image"
            for part in (item.get("content") or [])
        )
        for item in native_history
    )


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_generated_image_real_api(
    ensure_openai_api_key: str,
    tmp_path: Path,
) -> None:
    core = AgentCore()
    core.register_provider(OpenAIResponsesProvider)

    config = _vision_test_config(ensure_openai_api_key)
    image_path = _generate_red_square_png(tmp_path)
    image_data_url = _make_data_url(image_path, "image/png")

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        (
            "Reply with exactly RED_SQUARE_OK if the attached image is predominantly a solid "
            "red square. Otherwise reply with exactly NOT_RED."
        ),
        config=config,
        multipart_content=[
            {
                "type": "image",
                "content": {
                    "url": image_data_url,
                    "mime_type": "image/png",
                    "filename": image_path.name,
                },
                "metadata": {},
            }
        ],
    )

    new_session, responses = core.send_request(session, config)

    assert new_session is not None
    assert responses

    final = responses[-1]
    assert final.get("role") == "assistant"
    assert isinstance(final.get("content"), str)
    assert "RED_SQUARE_OK" in final["content"]

    native_history = (new_session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert any(
        isinstance(item, dict)
        and item.get("type") == "message"
        and any(
            isinstance(part, dict)
            and part.get("type") == "input_image"
            and part.get("image_url") == image_data_url
            for part in (item.get("content") or [])
        )
        for item in native_history
    )
