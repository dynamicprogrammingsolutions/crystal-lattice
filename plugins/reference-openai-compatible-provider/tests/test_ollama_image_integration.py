from __future__ import annotations

import os

import pytest
import requests

from hosted_test_utils import build_reference_core


_RED_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADUlEQVR42mP8z8BQDwAFgwJ/"
    "l8nK2AAAAABJRU5ErkJggg=="
)


def _ollama_available(base_url: str) -> bool:
    try:
        response = requests.get(f"{base_url.rstrip('/')}/models", timeout=2)
        return bool(response.ok)
    except Exception:
        return False


def _ollama_cfg() -> dict:
    return {
        "base_url": os.environ.get(
            "OLLAMA_OPENAI_BASE_URL", "http://localhost:11434/v1"
        ),
        "model": os.environ.get("OLLAMA_OPENAI_VISION_MODEL", "qwen2.5vl:3b"),
        "timeout": float(os.environ.get("OLLAMA_OPENAI_TIMEOUT", "120")),
    }


@pytest.mark.integration
@pytest.mark.ollama
def test_base64_image_ollama_openai_compat() -> None:
    cfg = _ollama_cfg()
    if not _ollama_available(cfg["base_url"]):
        pytest.skip("Ollama OpenAI-compatible endpoint not reachable")

    core = build_reference_core()
    session = core.create_session()
    session = core.add_message(
        session,
        "user",
        "Describe this image in five words or fewer.",
        multipart_content=[
            {
                "type": "image",
                "content": {
                    "data_base64": _RED_PNG_BASE64,
                    "mime_type": "image/png",
                    "filename": "red.png",
                },
                "metadata": {},
            }
        ],
    )

    try:
        _session2, finals = core.send_request(session, cfg)
    except RuntimeError as exc:
        message = str(exc)
        if "not found" in message and cfg["model"] in message:
            pytest.skip(
                f"Ollama vision model {cfg['model']!r} is not installed; "
                "set OLLAMA_OPENAI_VISION_MODEL or install the model locally"
            )
        raise

    assert finals and finals[-1]["role"] == "assistant"
    assert isinstance(finals[-1].get("content"), str)
    assert finals[-1]["content"].strip()