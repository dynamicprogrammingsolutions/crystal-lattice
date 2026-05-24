from __future__ import annotations

import base64
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import pytest
from fastapi.testclient import TestClient


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
from agent_terminal_app.server import app as fastapi_app  # noqa: E402
from agent_terminal_app.server import get_agent_app  # noqa: E402
from repo_test_env import get_repo_env  # noqa: E402


def _vision_model() -> str:
    return os.getenv("OPENAI_RESPONSES_VISION_MODEL") or "gpt-5-mini"


def _write_config(tmp_path: Path, api_key: str) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "openai": {
                "provider": "openai_responses",
                "model": _vision_model(),
                "api_key": api_key,
                "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
                "timeout": 120,
                "attachment_upload_mode": "upload_before_send",
            }
        },
        "plugins": [
            "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider",
            "openai_responses_plugins.openai_responses_attachments_extension.OpenAIResponsesAttachmentsExtension",
        ],
        "agents": {"default": {"provider": "openai"}},
    }
    path = tmp_path / "config_openai_responses_attachment_action_flow.json"
    path.write_text(json.dumps(cfg), encoding="utf-8")
    return path


def _build_app(tmp_path: Path, api_key: str) -> AgentApplication:
    config_path = _write_config(tmp_path, api_key)
    return AgentApplication(
        str(config_path),
        str(tmp_path / "sessions"),
        event_store=InMemoryEventStore(),
    )


def _install_test_client(app_instance: AgentApplication) -> TestClient:
    fastapi_app.dependency_overrides[get_agent_app] = lambda: app_instance
    return TestClient(fastapi_app)


def _generate_text_pdf(tmp_path: Path, marker_text: str) -> Path:
    pdf_path = tmp_path / f"{marker_text.lower()}-action-flow.pdf"
    try:
        subprocess.run(
            [
                "magick",
                "-background",
                "white",
                "-fill",
                "black",
                "-size",
                "900x500",
                f"caption:{marker_text}",
                str(pdf_path),
            ],
            check=True,
            capture_output=True,
            text=True,
        )
    except FileNotFoundError:
        pytest.skip("magick not available; skipping FastAPI attachment action-flow test")
    except subprocess.CalledProcessError as exc:
        pytest.fail(f"failed to generate FastAPI PDF fixture: {exc.stderr.strip()}")

    if not pdf_path.exists():
        pytest.fail("ImageMagick did not create the expected FastAPI PDF fixture")
    return pdf_path


def _wait_for_final_event(client: TestClient, session_id: str, timeout_seconds: float = 120.0) -> List[Dict[str, Any]]:
    deadline = time.time() + timeout_seconds
    last_event_id: Optional[str] = None
    all_events: List[Dict[str, Any]] = []

    while time.time() < deadline:
        params: Dict[str, Any] = {"session_id": session_id}
        if last_event_id is not None:
            params["since_id"] = last_event_id

        response = client.get("/events", params=params)
        assert response.status_code == 200
        batch = response.json().get("events") or []
        if batch:
            last_event_id = batch[-1].get("event_id") or last_event_id
            all_events.extend(batch)
            event_types = {ev.get("type") for ev in all_events}
            if "final" in event_types or "request_completed" in event_types:
                return all_events

        time.sleep(0.25)

    raise AssertionError("timed out waiting for final/request_completed events")


@pytest.fixture(scope="module")
def ensure_openai_api_key() -> str:
    api_key = get_repo_env("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI FastAPI attachment action-flow tests")
    return api_key


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openai
def test_openai_responses_action_store_then_send_asset_ref_endpoint_real_api(
    ensure_openai_api_key: str,
    tmp_path: Path,
) -> None:
    app_instance = _build_app(tmp_path, api_key=ensure_openai_api_key)
    client = _install_test_client(app_instance)

    try:
        create_response = client.post("/sessions", json={"agent_id": "default"})
        assert create_response.status_code == 200
        session_id = create_response.json()["session"]["session_id"]

        marker = "PDF_ACTION_FLOW_OK"
        pdf_path = _generate_text_pdf(tmp_path, marker)
        pdf_base64 = base64.b64encode(pdf_path.read_bytes()).decode("ascii")

        store_response = client.post(
            "/actions",
            json={
                "plugin": "openai_responses_attachments",
                "action_id": "store_attachment",
                "action_owner": "provider_extension",
                "inputs": {
                    "session_id": session_id,
                    "client_attachment_id": "draft_fastapi_pdf",
                    "attachment_type": "pdf",
                    "filename": pdf_path.name,
                    "mime_type": "application/pdf",
                    "data_base64": pdf_base64,
                },
            },
        )
        assert store_response.status_code == 200
        asset = store_response.json()["result"]["attachment_asset"]

        add_response = client.post(
            f"/sessions/{session_id}/messages",
            json={
                "role": "user",
                "content": (
                    "Reply with exactly PDF_ACTION_FLOW_OK if you can access one attached "
                    "stored PDF whose visible text includes PDF_ACTION_FLOW_OK. Otherwise "
                    "reply with exactly PDF_ACTION_FLOW_FAIL."
                ),
                "multipartContent": [
                    {
                        "type": "pdf",
                        "content": {
                            "asset_ref": asset["asset_ref"],
                            "mime_type": asset["mime_type"],
                            "filename": asset["filename"],
                        },
                        "metadata": {},
                    }
                ],
                "metadata": None,
            },
        )
        assert add_response.status_code == 200

        send_response = client.post(f"/sessions/{session_id}/send", json={"config_overrides": {}})
        assert send_response.status_code == 200
        assert send_response.json()["status"] == "started"

        events = _wait_for_final_event(client, session_id)
        assert any(event.get("type") == "final" for event in events)

        loaded = app_instance.load_session(session_id)
        assert loaded is not None
        _core, _base_config, session = loaded

        assert "PDF_ACTION_FLOW_OK" in session.messages[-1].content
        assert session.messages[0].multipart_content == [
            {
                "type": "pdf",
                "content": {
                    "asset_ref": asset["asset_ref"],
                    "mime_type": asset["mime_type"],
                    "filename": asset["filename"],
                },
                "metadata": {},
            }
        ]

        stored_record = app_instance.get_session_asset_store().load(
            session_id,
            asset["asset_ref"]["asset_id"],
        )
        assert isinstance(stored_record.provider_refs["openai_responses"]["file_id"], str)
    finally:
        fastapi_app.dependency_overrides.clear()