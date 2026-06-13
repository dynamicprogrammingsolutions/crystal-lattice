from __future__ import annotations

import pytest

from fireworks_test_utils import build_fireworks_cfg, fireworks_model, send_request_or_skip
from hosted_test_utils import build_reference_core


_RED_PNG_BASE64 = (
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAIAAACQd1PeAAAADUlEQVR42mP8z8BQDwAFgwJ/"
    "l8nK2AAAAABJRU5ErkJggg=="
)
_REMOTE_TEST_IMAGE_URL = "https://dummyimage.com/128x128/ff0000/ffffff.png&text=R"
_DEFAULT_FIREWORKS_VISION_MODEL = "fireworks/qwen3-vl-30b-a3b-thinking"
pytestmark = pytest.mark.api


@pytest.mark.integration
@pytest.mark.fireworks
def test_base64_image_fireworks_openai_compat() -> None:
    cfg = build_fireworks_cfg(
        fireworks_model(
            "FIREWORKS_VISION_MODEL",
            _DEFAULT_FIREWORKS_VISION_MODEL,
        )
    )

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

    _session2, finals = send_request_or_skip(core, session, cfg)
    assert finals and finals[-1]["role"] == "assistant"
    assert isinstance(finals[-1].get("content"), str)
    assert finals[-1]["content"].strip()


@pytest.mark.integration
@pytest.mark.fireworks
def test_image_url_fireworks_openai_compat() -> None:
    cfg = build_fireworks_cfg(
        fireworks_model(
            "FIREWORKS_VISION_MODEL",
            _DEFAULT_FIREWORKS_VISION_MODEL,
        )
    )

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
                    "url": _REMOTE_TEST_IMAGE_URL,
                    "mime_type": "image/png",
                    "filename": "remote-red.png",
                },
                "metadata": {},
            }
        ],
    )

    _session2, finals = send_request_or_skip(core, session, cfg)
    assert finals and finals[-1]["role"] == "assistant"
    assert isinstance(finals[-1].get("content"), str)
    assert finals[-1]["content"].strip()