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
    path = tmp_path / "config_openai_responses_attachment_actions.json"
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


def test_actions_endpoint_stores_deletes_and_downloads_attachment_asset(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    app = _build_app(tmp_path, monkeypatch)
    _core, _base_config, session = app.create_session("default")
    server_mod._agent_app = app

    store_resp = server_mod.execute_action(
        {
            "plugin": "openai_responses_attachments",
            "action_id": "store_attachment",
            "action_owner": "provider_extension",
            "inputs": {
                "session_id": session.session_id,
                "client_attachment_id": "draft_1",
                "attachment_type": "pdf",
                "filename": "brief.pdf",
                "mime_type": "application/pdf",
                "data_base64": base64.b64encode(b"pdf-bytes").decode("ascii"),
            },
        },
        app_instance=app,
    )

    assert store_resp["status"] == "ok"
    asset = store_resp["result"]["attachment_asset"]
    asset_id = asset["asset_ref"]["asset_id"]
    assert asset["client_attachment_id"] == "draft_1"

    loaded_session = app.load_session_record(session.session_id)
    assert loaded_session is not None
    session_assets = (loaded_session.metadata or {}).get("session_assets")
    assert isinstance(session_assets, dict)
    assert session_assets[asset_id]["filename"] == "brief.pdf"
    assert (
        app.get_session_asset_store().load_bytes(session.session_id, asset_id)
        == b"pdf-bytes"
    )

    download_resp = server_mod.execute_action(
        {
            "plugin": "openai_responses_attachments",
            "action_id": "download_attachment",
            "action_owner": "provider_extension",
            "inputs": {
                "session_id": session.session_id,
                "asset_id": asset_id,
            },
        },
        app_instance=app,
    )

    assert download_resp["status"] == "ok"
    assert (
        download_resp["result"]["attachment_asset"]["asset_ref"]["asset_id"] == asset_id
    )
    assert download_resp["result"]["data_base64"] == base64.b64encode(
        b"pdf-bytes"
    ).decode("ascii")

    delete_resp = server_mod.execute_action(
        {
            "plugin": "openai_responses_attachments",
            "action_id": "delete_attachment",
            "action_owner": "provider_extension",
            "inputs": {
                "session_id": session.session_id,
                "asset_id": asset_id,
            },
        },
        app_instance=app,
    )

    assert delete_resp["status"] == "ok"
    assert (
        delete_resp["result"]["deleted_attachment_asset"]["asset_ref"]["asset_id"]
        == asset_id
    )

    loaded_after_delete = app.load_session_record(session.session_id)
    assert loaded_after_delete is not None
    assert (loaded_after_delete.metadata or {}).get("session_assets") == {}
