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
from dotenv import load_dotenv
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
import openai_responses_plugins.openai_responses_provider as provider_module  # noqa: E402
from openai_responses_plugins.openai_responses_provider import (
    OpenAIResponsesProvider,
)  # noqa: E402

pytestmark = [pytest.mark.integration, pytest.mark.openai]


class _FakeUploadFileObject:
    def __init__(self, file_id: str) -> None:
        self.id = file_id

    def model_dump(self, mode: str = "python") -> Dict[str, Any]:
        _ = mode
        return {"id": self.id}


class _FakeFilesResource:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _FakeUploadFileObject:
        self.calls.append(kwargs)
        return _FakeUploadFileObject(f"file_{len(self.calls)}")


class _FakeResponse:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload

    def model_dump(self, mode: str = "python") -> Dict[str, Any]:
        _ = mode
        return self._payload


class _FakeResponsesResource:
    def __init__(self) -> None:
        self.calls: List[Dict[str, Any]] = []

    def create(self, **kwargs: Any) -> _FakeResponse:
        self.calls.append(kwargs)
        return _FakeResponse(
            {
                "id": "resp_attachment_endpoint_test",
                "output": [
                    {
                        "type": "message",
                        "role": "assistant",
                        "content": [{"type": "output_text", "text": "PDF_ENDPOINT_OK"}],
                    }
                ],
            }
        )


class _FakeClient:
    def __init__(self) -> None:
        self.files = _FakeFilesResource()
        self.responses = _FakeResponsesResource()


def _write_config(tmp_path: Path, api_key: str) -> Path:
    cfg: Dict[str, Any] = {
        "plugin_cache_dir": str(tmp_path / ".plugin_cache"),
        "providers": {
            "openai": {
                "provider": "openai_responses",
                "model": os.getenv("OPENAI_RESPONSES_VISION_MODEL") or "gpt-5-mini",
                "api_key": api_key,
                "base_url": os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1",
                "timeout": 120,
            }
        },
        "plugins": [
            "openai_responses_plugins.openai_responses_provider.OpenAIResponsesProvider",
            "openai_responses_plugins.openai_responses_attachments_extension.OpenAIResponsesAttachmentsExtension",
        ],
        "agents": {"default": {"provider": "openai"}},
    }
    path = tmp_path / "config_openai_responses_attachment_endpoints.json"
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


def _make_data_url(path: Path, mime_type: str) -> str:
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _generate_text_pdf(tmp_path: Path, marker_text: str) -> Path:
    pdf_path = tmp_path / f"{marker_text.lower()}-attachment.pdf"
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
        pytest.skip("magick not available; skipping PDF endpoint test")
    except subprocess.CalledProcessError as exc:
        pytest.fail(
            f"failed to generate test PDF with ImageMagick: {exc.stderr.strip()}"
        )

    if not pdf_path.exists():
        pytest.fail("ImageMagick did not create the expected PDF")
    return pdf_path


def _wait_for_final_event(
    client: TestClient, session_id: str, timeout_seconds: float = 120.0
) -> List[Dict[str, Any]]:
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
    load_dotenv(ROOT / ".env")
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY not set; skipping OpenAI attachment endpoint tests")
    return api_key


def test_send_message_applies_request_overrides_before_pdf_append(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(OpenAIResponsesProvider, "get_models", lambda self, config: [])

    app_instance = _build_app(tmp_path, api_key="test_key")
    captured: Dict[str, Any] = {}

    def _fake_send_request(
        core_arg: Any,
        session_arg: Any,
        base_config_arg: Any,
        overrides_arg: Dict[str, Any] | None,
        *,
        stream: bool = True,
        request_id: str | None = None,
        baseline_file_state: Any = None,
    ):
        captured["overrides"] = overrides_arg
        yield {
            "type": "request_started",
            "session_id": session_arg.session_id,
            "request_id": request_id,
            "stream": bool(stream),
        }
        yield {
            "type": "final",
            "session_id": session_arg.session_id,
            "request_id": request_id,
            "messages": [],
        }
        yield {
            "type": "request_completed",
            "session_id": session_arg.session_id,
            "request_id": request_id,
        }

    app_instance.send_request = _fake_send_request  # type: ignore[assignment]
    client = _install_test_client(app_instance)

    try:
        create_response = client.post("/sessions", json={"agent_id": "default"})
        assert create_response.status_code == 200
        session_id = create_response.json()["session"]["session_id"]

        pdf_path = _generate_text_pdf(tmp_path, "PDF_ENDPOINT_OK")
        pdf_data_url = _make_data_url(pdf_path, "application/pdf")

        response = client.post(
            f"/sessions/{session_id}/send_message",
            json={
                "message": {
                    "role": "user",
                    "content": "Please read the attached PDF.",
                    "multipartContent": [
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
                    "metadata": None,
                },
                "config_overrides": {"attachment_upload_mode": "upload_before_send"},
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "started"

        _wait_for_final_event(client, session_id, timeout_seconds=15.0)

        loaded = app_instance.load_session(session_id)
        assert loaded is not None
        _core, _base_config, session = loaded

        assert session.messages[0].multipart_content == [
            {
                "type": "pdf",
                "content": {
                    "url": pdf_data_url,
                    "mime_type": "application/pdf",
                    "filename": pdf_path.name,
                },
                "metadata": {},
            }
        ]
        assert captured["overrides"] == {"attachment_upload_mode": "upload_before_send"}
    finally:
        fastapi_app.dependency_overrides.clear()


def test_add_message_returns_400_for_pdf_without_upload_mode(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fake_client = _FakeClient()
    monkeypatch.setattr(provider_module, "OpenAI", lambda **kwargs: fake_client)
    monkeypatch.setattr(OpenAIResponsesProvider, "get_models", lambda self, config: [])

    app_instance = _build_app(tmp_path, api_key="test_key")
    client = _install_test_client(app_instance)

    try:
        create_response = client.post("/sessions", json={"agent_id": "default"})
        assert create_response.status_code == 200
        session_id = create_response.json()["session"]["session_id"]

        pdf_path = _generate_text_pdf(tmp_path, "PDF_ENDPOINT_BAD")
        pdf_data_url = _make_data_url(pdf_path, "application/pdf")

        response = client.post(
            f"/sessions/{session_id}/messages",
            json={
                "role": "user",
                "content": "Please read the attached PDF.",
                "multipartContent": [
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
                "metadata": None,
            },
        )

        assert response.status_code == 400
        assert "attachment_upload_mode=upload_before_send" in response.json()["detail"]
    finally:
        fastapi_app.dependency_overrides.clear()


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_send_message_uploaded_pdf_endpoint_real_api(
    ensure_openai_api_key: str,
    tmp_path: Path,
) -> None:
    app_instance = _build_app(tmp_path, api_key=ensure_openai_api_key)
    client = _install_test_client(app_instance)

    try:
        create_response = client.post("/sessions", json={"agent_id": "default"})
        assert create_response.status_code == 200
        session_id = create_response.json()["session"]["session_id"]

        pdf_path = _generate_text_pdf(tmp_path, "PDF_ENDPOINT_SEND_MESSAGE_OK")
        pdf_data_url = _make_data_url(pdf_path, "application/pdf")

        response = client.post(
            f"/sessions/{session_id}/send_message",
            json={
                "message": {
                    "role": "user",
                    "content": (
                        "Reply with exactly PDF_ENDPOINT_SEND_MESSAGE_OK if you can access one "
                        "attached PDF whose visible text includes PDF_ENDPOINT_SEND_MESSAGE_OK. "
                        "Otherwise reply with exactly PDF_ENDPOINT_SEND_MESSAGE_FAIL."
                    ),
                    "multipartContent": [
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
                    "metadata": None,
                },
                "config_overrides": {"attachment_upload_mode": "upload_before_send"},
            },
        )

        assert response.status_code == 200
        assert response.json()["status"] == "started"

        _wait_for_final_event(client, session_id)

        loaded = app_instance.load_session(session_id)
        assert loaded is not None
        _core, _base_config, session = loaded

        assert "PDF_ENDPOINT_SEND_MESSAGE_OK" in session.messages[-1].content
        assert session.messages[0].multipart_content == [
            {
                "type": "pdf",
                "content": {
                    "url": pdf_data_url,
                    "mime_type": "application/pdf",
                    "filename": pdf_path.name,
                },
                "metadata": {},
            }
        ]
    finally:
        fastapi_app.dependency_overrides.clear()


@pytest.mark.integration
@pytest.mark.openai
def test_openai_responses_add_message_then_send_uploaded_pdf_endpoint_real_api(
    ensure_openai_api_key: str,
    tmp_path: Path,
) -> None:
    app_instance = _build_app(tmp_path, api_key=ensure_openai_api_key)
    client = _install_test_client(app_instance)

    try:
        create_response = client.post("/sessions", json={"agent_id": "default"})
        assert create_response.status_code == 200
        session_id = create_response.json()["session"]["session_id"]

        override_response = client.patch(
            f"/sessions/{session_id}/overrides",
            json={"key": "attachment_upload_mode", "value": "upload_before_send"},
        )
        assert override_response.status_code == 200

        pdf_path = _generate_text_pdf(tmp_path, "PDF_ENDPOINT_TWO_CALL_OK")
        pdf_data_url = _make_data_url(pdf_path, "application/pdf")

        add_response = client.post(
            f"/sessions/{session_id}/messages",
            json={
                "role": "user",
                "content": (
                    "Reply with exactly PDF_ENDPOINT_TWO_CALL_OK if you can access one attached "
                    "PDF whose visible text includes PDF_ENDPOINT_TWO_CALL_OK. Otherwise reply "
                    "with exactly PDF_ENDPOINT_TWO_CALL_FAIL."
                ),
                "multipartContent": [
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
                "metadata": None,
            },
        )
        assert add_response.status_code == 200

        send_response = client.post(
            f"/sessions/{session_id}/send", json={"config_overrides": {}}
        )
        assert send_response.status_code == 200
        assert send_response.json()["status"] == "started"

        _wait_for_final_event(client, session_id)

        loaded = app_instance.load_session(session_id)
        assert loaded is not None
        _core, _base_config, session = loaded

        assert "PDF_ENDPOINT_TWO_CALL_OK" in session.messages[-1].content
        assert session.messages[0].multipart_content == [
            {
                "type": "pdf",
                "content": {
                    "url": pdf_data_url,
                    "mime_type": "application/pdf",
                    "filename": pdf_path.name,
                },
                "metadata": {},
            }
        ]

        native_history = (session.metadata or {}).get("native_messages")
        assert isinstance(native_history, list)
        assert any(
            isinstance(item, dict)
            and item.get("type") == "message"
            and any(
                isinstance(part, dict) and part.get("type") == "input_file"
                for part in (item.get("content") or [])
            )
            for item in native_history
        )
    finally:
        fastapi_app.dependency_overrides.clear()
