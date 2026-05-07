from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from typing import Any, Dict

import pytest


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
OPENAI_RESPONSES_SRC = ROOT / "plugins/openai_responses/src"
if str(OPENAI_RESPONSES_SRC) not in sys.path:
    sys.path.insert(0, str(OPENAI_RESPONSES_SRC))

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from agent_terminal_app import server as server_mod  # noqa: E402
from openai_responses_plugins.openai_responses_provider import (
    OpenAIResponsesProvider,
)  # noqa: E402

pytestmark = [pytest.mark.integration, pytest.mark.openai]


def _write_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "openai": {
                "provider": "openai_responses",
                "model": "gpt-5-mini",
                "api_key": "test_key",
                "base_url": "https://api.openai.com/v1",
                "timeout": 120,
            }
        },
        "plugins": [
            "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider",
            "openai_responses_plugins.openai_responses_attachments_extension.OpenAIResponsesAttachmentsExtension",
        ],
        "agents": {"default": {"provider": "openai"}},
    }
    path = tmp_path / "config_openai_responses_attachment_preview.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path, monkeypatch: Any) -> AgentApplication:
    monkeypatch.setattr(OpenAIResponsesProvider, "get_models", lambda self, config: [])
    previous = getattr(server_mod, "_agent_app", None)
    if previous is not None:
        previous.close()
    return AgentApplication(
        str(_write_config(tmp_path)),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )


def test_list_messages_enriches_asset_ref_images_with_preview_bytes(
    tmp_path: Path, monkeypatch: Any
) -> None:
    app = _build_app(tmp_path, monkeypatch)
    _core, _base_config, session = app.create_session("default")
    server_mod._agent_app = app

    image_bytes = b"image-preview-bytes"
    image_record = app.get_session_asset_store().store_base64(
        session_id=session.session_id,
        attachment_type="image",
        filename="square.png",
        mime_type="image/png",
        data_base64=base64.b64encode(image_bytes).decode("ascii"),
    )
    pdf_record = app.get_session_asset_store().store_base64(
        session_id=session.session_id,
        attachment_type="pdf",
        filename="brief.pdf",
        mime_type="application/pdf",
        data_base64=base64.b64encode(b"pdf-bytes").decode("ascii"),
    )

    server_mod.add_message(
        session.session_id,
        {
            "role": "user",
            "content": "see stored assets",
            "multipartContent": [
                {
                    "type": "image",
                    "content": {"asset_ref": image_record.asset_ref()},
                    "metadata": {},
                },
                {
                    "type": "pdf",
                    "content": {"asset_ref": pdf_record.asset_ref()},
                    "metadata": {},
                },
            ],
        },
        app_instance=app,
    )

    response = server_mod.list_session_messages(session.session_id, app_instance=app)

    message = response["messages"][0]["message"]
    image_part = message["multipartContent"][0]
    pdf_part = message["multipartContent"][1]

    assert image_part["content"]["filename"] == "square.png"
    assert image_part["content"]["mime_type"] == "image/png"
    assert image_part["content"]["preview_data_base64"] == base64.b64encode(
        image_bytes
    ).decode("ascii")
    assert image_part["content"]["preview_mime_type"] == "image/png"

    assert pdf_part["content"]["filename"] == "brief.pdf"
    assert pdf_part["content"]["mime_type"] == "application/pdf"
    assert "preview_data_base64" not in pdf_part["content"]


def test_list_messages_marks_missing_asset_refs(
    tmp_path: Path, monkeypatch: Any
) -> None:
    app = _build_app(tmp_path, monkeypatch)
    _core, _base_config, session = app.create_session("default")
    server_mod._agent_app = app

    image_record = app.get_session_asset_store().store_base64(
        session_id=session.session_id,
        attachment_type="image",
        filename="missing.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"missing-bytes").decode("ascii"),
    )

    server_mod.add_message(
        session.session_id,
        {
            "role": "user",
            "content": "see missing asset",
            "multipartContent": [
                {
                    "type": "image",
                    "content": {"asset_ref": image_record.asset_ref()},
                    "metadata": {},
                }
            ],
        },
        app_instance=app,
    )
    assert (
        app.get_session_asset_store().delete(session.session_id, image_record.asset_id)
        is True
    )

    response = server_mod.list_session_messages(session.session_id, app_instance=app)

    image_part = response["messages"][0]["message"]["multipartContent"][0]
    assert image_part["metadata"]["asset_missing"] is True
    assert "preview_data_base64" not in image_part["content"]
