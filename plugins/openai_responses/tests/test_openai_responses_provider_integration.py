from __future__ import annotations

import base64
import os
from pathlib import Path
import subprocess

import pytest
from dotenv import load_dotenv

from agent_app.session_assets import FilesystemSessionAssetStore
from agent_core import AgentCore
from openai_responses_plugins.openai_responses_attachments_extension import (
    OpenAIResponsesAttachmentsExtension,
)
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


def _upload_backed_image_test_config(api_key: str) -> dict[str, object]:
    return {
        **_vision_test_config(api_key),
        "image_attachment_mode": "upload",
        "attachment_upload_mode": "upload_before_send",
    }


def _build_attachment_core() -> AgentCore:
    core = AgentCore()
    core.register_provider(OpenAIResponsesProvider, [OpenAIResponsesAttachmentsExtension])
    return core


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


def _generate_text_pdf(tmp_path: Path) -> Path:
    pdf_path = tmp_path / "attachment-brief.pdf"
    try:
        subprocess.run(
            [
                "magick",
                "-background",
                "white",
                "-fill",
                "black",
                "-size",
                "800x400",
                "caption:PDF_STAGE2_OK",
                str(pdf_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        pytest.skip("magick not available; skipping generated-pdf integration test")
    except subprocess.CalledProcessError as exc:
        pytest.fail(f"failed to generate test PDF with ImageMagick: {exc.stderr.strip()}")

    if not pdf_path.exists():
        pytest.fail("ImageMagick did not create the expected test PDF")
    return pdf_path


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


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_uploaded_image_real_api(
    ensure_openai_api_key: str,
    tmp_path: Path,
) -> None:
    core = _build_attachment_core()

    config = _upload_backed_image_test_config(ensure_openai_api_key)
    image_path = _generate_red_square_png(tmp_path)
    image_data_url = _make_data_url(image_path, "image/png")

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        (
            "Reply with exactly RED_SQUARE_UPLOAD_OK if the attached image is predominantly "
            "a solid red square. Otherwise reply with exactly NOT_RED."
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

    assert responses
    assert "RED_SQUARE_UPLOAD_OK" in responses[-1]["content"]

    native_history = (new_session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert any(
        isinstance(item, dict)
        and item.get("type") == "message"
        and isinstance(item.get("_metadata"), dict)
        and any(
            isinstance(entry, dict)
            and isinstance((entry.get("uploaded_part") or {}).get("file_id"), str)
            and (entry.get("uploaded_part") or {}).get("type") == "input_image"
            for entry in (item.get("_metadata") or {}).get("_openai_responses_uploaded_attachments", [])
        )
        for item in native_history
    )


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_uploaded_pdf_real_api(
    ensure_openai_api_key: str,
    tmp_path: Path,
) -> None:
    core = _build_attachment_core()

    config = _vision_test_config(ensure_openai_api_key)
    pdf_path = _generate_text_pdf(tmp_path)
    pdf_data_url = _make_data_url(pdf_path, "application/pdf")

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        (
            "Reply with exactly PDF_UPLOAD_OK if you can access one attached PDF whose visible "
            "text includes PDF_STAGE2_OK. Otherwise reply with exactly PDF_UPLOAD_FAIL."
        ),
        config=config,
        multipart_content=[
            {
                "type": "pdf",
                "content": {
                    "url": pdf_data_url,
                    "mime_type": "application/pdf",
                    "filename": pdf_path.name,
                },
                "metadata": {},
            }
        ],
    )

    new_session, responses = core.send_request(session, config)

    assert responses
    assert "PDF_UPLOAD_OK" in responses[-1]["content"]

    native_history = (new_session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert any(
        isinstance(item, dict)
        and item.get("type") == "message"
        and isinstance(item.get("_metadata"), dict)
        and any(
            isinstance(entry, dict)
            and isinstance((entry.get("uploaded_part") or {}).get("file_id"), str)
            and (entry.get("uploaded_part") or {}).get("type") == "input_file"
            for entry in (item.get("_metadata") or {}).get("_openai_responses_uploaded_attachments", [])
        )
        for item in native_history
    )


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_session_asset_image_real_api(
    ensure_openai_api_key: str,
    tmp_path: Path,
) -> None:
    core = _build_attachment_core()
    asset_store = FilesystemSessionAssetStore(tmp_path / "session_assets")

    config = {
        **_upload_backed_image_test_config(ensure_openai_api_key),
        "_session_asset_store": asset_store,
    }
    image_path = _generate_red_square_png(tmp_path)
    image_record = asset_store.store_base64(
        session_id="sess_asset_image",
        attachment_type="image",
        filename=image_path.name,
        mime_type="image/png",
        data_base64=base64.b64encode(image_path.read_bytes()).decode("ascii"),
    )

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        (
            "Reply with exactly ASSET_IMAGE_OK if the attached stored image is predominantly "
            "a solid red square. Otherwise reply with exactly NOT_RED."
        ),
        config=config,
        multipart_content=[
            {
                "type": "image",
                "content": {
                    "asset_ref": image_record.asset_ref(),
                    "mime_type": image_record.mime_type,
                    "filename": image_record.filename,
                },
                "metadata": {},
            }
        ],
    )

    new_session, responses = core.send_request(session, config)

    assert responses
    assert "ASSET_IMAGE_OK" in responses[-1]["content"]

    updated_record = asset_store.load(image_record.session_id, image_record.asset_id)
    assert isinstance(updated_record.provider_refs["openai_responses"]["file_id"], str)

    native_history = (new_session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert any(
        isinstance(item, dict)
        and item.get("type") == "message"
        and isinstance(item.get("_metadata"), dict)
        and any(
            isinstance(entry, dict)
            and (entry.get("multipart_part") or {}).get("content", {}).get("asset_ref") == image_record.asset_ref()
            for entry in (item.get("_metadata") or {}).get("_openai_responses_attachment_sources", [])
        )
        for item in native_history
    )


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_session_asset_pdf_real_api(
    ensure_openai_api_key: str,
    tmp_path: Path,
) -> None:
    core = _build_attachment_core()
    asset_store = FilesystemSessionAssetStore(tmp_path / "session_assets")

    config = {
        **_vision_test_config(ensure_openai_api_key),
        "_session_asset_store": asset_store,
    }
    pdf_path = _generate_text_pdf(tmp_path)
    pdf_record = asset_store.store_base64(
        session_id="sess_asset_pdf",
        attachment_type="pdf",
        filename=pdf_path.name,
        mime_type="application/pdf",
        data_base64=base64.b64encode(pdf_path.read_bytes()).decode("ascii"),
    )

    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        (
            "Reply with exactly ASSET_PDF_OK if you can access one attached stored PDF whose "
            "visible text includes PDF_STAGE2_OK. Otherwise reply with exactly ASSET_PDF_FAIL."
        ),
        config=config,
        multipart_content=[
            {
                "type": "pdf",
                "content": {
                    "asset_ref": pdf_record.asset_ref(),
                    "mime_type": pdf_record.mime_type,
                    "filename": pdf_record.filename,
                },
                "metadata": {},
            }
        ],
    )

    new_session, responses = core.send_request(session, config)

    assert responses
    assert "ASSET_PDF_OK" in responses[-1]["content"]

    updated_record = asset_store.load(pdf_record.session_id, pdf_record.asset_id)
    assert isinstance(updated_record.provider_refs["openai_responses"]["file_id"], str)

    native_history = (new_session.metadata or {}).get("native_messages")
    assert isinstance(native_history, list)
    assert any(
        isinstance(item, dict)
        and item.get("type") == "message"
        and isinstance(item.get("_metadata"), dict)
        and any(
            isinstance(entry, dict)
            and (entry.get("multipart_part") or {}).get("content", {}).get("asset_ref") == pdf_record.asset_ref()
            for entry in (item.get("_metadata") or {}).get("_openai_responses_attachment_sources", [])
        )
        for item in native_history
    )
