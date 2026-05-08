from __future__ import annotations

import base64
import json
import sys
from pathlib import Path
from typing import Any, Dict


ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
APP_PY = ROOT / "application/python"
if str(APP_PY) not in sys.path:
    sys.path.insert(0, str(APP_PY))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from agent_terminal_app import server as server_mod  # noqa: E402
from plugins.echo_openai_like_provider import EchoOpenAILikeProvider  # noqa: F401,E402


def _write_config(tmp_path: Path) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "echo": {"provider": "echo_openai_like", "model": "echo-model"},
        },
        "plugins": ["plugins.echo_openai_like_provider.EchoOpenAILikeProvider"],
        "agents": {"default": {"provider": "echo"}},
    }
    path = tmp_path / "config_session_asset_listing.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path) -> AgentApplication:
    previous = getattr(server_mod, "_agent_app", None)
    if previous is not None:
        previous.close()
    return AgentApplication(
        str(_write_config(tmp_path)),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )


def test_list_messages_returns_bare_asset_refs_unchanged(tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    _core, _base_config, session = app.create_session("default")
    server_mod._agent_app = app

    record = app.get_session_asset_store().store_base64(
        session_id=session.session_id,
        attachment_type="image",
        filename="square.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"image-preview-bytes").decode("ascii"),
    )
    stored_part = {
        "type": "image",
        "content": {"asset_ref": record.asset_ref()},
        "metadata": {},
    }

    server_mod.add_message(
        session.session_id,
        {
            "role": "user",
            "content": "see stored asset",
            "multipartContent": [stored_part],
        },
        app_instance=app,
    )

    response = server_mod.list_session_messages(session.session_id, app_instance=app)

    message = response["messages"][0]["message"]
    assert message["multipartContent"] == [stored_part]


def test_list_messages_does_not_mark_missing_asset_refs(tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    _core, _base_config, session = app.create_session("default")
    server_mod._agent_app = app

    record = app.get_session_asset_store().store_base64(
        session_id=session.session_id,
        attachment_type="image",
        filename="missing.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"missing-bytes").decode("ascii"),
    )
    stored_part = {
        "type": "image",
        "content": {"asset_ref": record.asset_ref()},
        "metadata": {},
    }

    server_mod.add_message(
        session.session_id,
        {
            "role": "user",
            "content": "see missing asset",
            "multipartContent": [stored_part],
        },
        app_instance=app,
    )
    assert app.get_session_asset_store().delete(session.session_id, record.asset_id)

    response = server_mod.list_session_messages(session.session_id, app_instance=app)

    image_part = response["messages"][0]["message"]["multipartContent"][0]
    assert image_part == stored_part
    assert "asset_missing" not in image_part["metadata"]
    assert "preview_data_base64" not in image_part["content"]


def test_list_messages_roundtrips_plugin_created_preview_fields(tmp_path: Path) -> None:
    app = _build_app(tmp_path)
    _core, _base_config, session = app.create_session("default")
    server_mod._agent_app = app

    record = app.get_session_asset_store().store_base64(
        session_id=session.session_id,
        attachment_type="image",
        filename="preview.png",
        mime_type="image/png",
        data_base64=base64.b64encode(b"full-image").decode("ascii"),
    )
    stored_part = {
        "type": "image",
        "content": {
            "asset_ref": record.asset_ref(),
            "filename": "preview.png",
            "mime_type": "image/png",
            "preview_data_base64": base64.b64encode(b"preview").decode("ascii"),
            "preview_mime_type": "image/png",
        },
        "metadata": {"download_plugin_id": "session_asset_attachments"},
    }

    server_mod.add_message(
        session.session_id,
        {
            "role": "assistant",
            "content": "image",
            "multipartContent": [stored_part],
        },
        app_instance=app,
    )

    response = server_mod.list_session_messages(session.session_id, app_instance=app)

    assert response["messages"][0]["message"]["multipartContent"] == [stored_part]