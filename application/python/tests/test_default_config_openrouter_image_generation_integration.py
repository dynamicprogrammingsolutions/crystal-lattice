from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

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

from fastapi.testclient import TestClient  # noqa: E402

from agent_terminal_app.server import app as fastapi_app  # noqa: E402
from agent_terminal_app.server import get_agent_app  # noqa: E402


@pytest.fixture(scope="module")
def ensure_openrouter_api_key() -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        pytest.skip(
            "OPENROUTER_API_KEY not set; skipping default-config OpenRouter image-generation integration test"
        )
    return api_key


def _assert_generated_image_response(
    session_like: Any,
    final_messages: list[dict[str, Any]],
    asset_store: Any,
    *,
    require_session_asset_metadata: bool = True,
) -> None:
    assert final_messages, "expected final assistant messages"
    assistant = final_messages[-1]
    assert assistant["role"] == "assistant"
    multipart = assistant.get("multipartContent")
    assert (
        isinstance(multipart, list) and multipart
    ), "expected assistant multipart image output"

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

    if not require_session_asset_metadata:
        return

    metadata = getattr(session_like, "metadata", None) or {}
    session_assets = (
        metadata.get("session_assets") if isinstance(metadata, dict) else None
    )
    assert isinstance(session_assets, dict)
    assert asset_ref["asset_id"] in session_assets


def _install_test_client(app_instance: Any) -> TestClient:
    fastapi_app.dependency_overrides[get_agent_app] = lambda: app_instance
    return TestClient(fastapi_app)


def _wait_for_final_event(
    client: TestClient,
    session_id: str,
    timeout_seconds: float = 120.0,
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
            event_types = {event.get("type") for event in all_events}
            if "final" in event_types or "request_completed" in event_types:
                return all_events

        time.sleep(0.25)

    raise AssertionError("timed out waiting for final/request_completed events")


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openrouter
def test_default_config_openrouter_image_agent_generates_asset_backed_image(
    ensure_openrouter_api_key: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.chdir(workspace)

    monkeypatch.setenv("OPENROUTER_API_KEY", ensure_openrouter_api_key)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("FIREWORKS_API_KEY", "test-fireworks-key")
    monkeypatch.setenv("ZAI_API_KEY", "test-zai-key")

    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    monkeypatch.setenv(
        "CLOUD_RUNTIME_BUILD_CONTEXT", str(tmp_path / "cloud-runtime-context")
    )
    session_root = tmp_path / "sessions"

    app = AgentApplication(
        str(config_path), str(session_root), event_store=InMemoryEventStore()
    )
    assert app.get_config_errors() == []

    try:
        core, base_config, session = app.create_session("openrouter-image")
        session = core.add_message(
            session,
            "user",
            "Generate a simple orange circle icon on a plain background.",
            {},
            base_config,
        )
        app.save_session(session)

        events = list(app.send_request(core, session, base_config, stream=False))
        error_events = [event for event in events if event.get("type") == "error"]
        if error_events:
            detail = error_events[-1].get("detail")
            if isinstance(detail, str) and (
                "402" in detail or "Payment Required" in detail
            ):
                pytest.skip(
                    f"OpenRouter account could not access default-config image-generation agent: {detail}"
                )

        final_events = [event for event in events if event.get("type") == "final"]
        assert (
            final_events
        ), "expected final event from default-config image-generation agent"

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


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.openrouter
def test_default_config_openrouter_image_agent_send_message_endpoint_real_api(
    ensure_openrouter_api_key: str,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    from agent_app.application_future import AgentApplication
    from agent_app.events import InMemoryEventStore

    workspace = tmp_path / "workspace"
    workspace.mkdir()
    monkeypatch.chdir(workspace)

    monkeypatch.setenv("OPENROUTER_API_KEY", ensure_openrouter_api_key)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("GEMINI_API_KEY", "test-gemini-key")
    monkeypatch.setenv("TAVILY_API_KEY", "test-tavily-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    monkeypatch.setenv("FIREWORKS_API_KEY", "test-fireworks-key")
    monkeypatch.setenv("ZAI_API_KEY", "test-zai-key")

    config_path = (
        ROOT
        / "application"
        / "python"
        / "agent_terminal_app"
        / "default_config"
        / "config.json"
    )
    monkeypatch.setenv(
        "CLOUD_RUNTIME_BUILD_CONTEXT", str(tmp_path / "cloud-runtime-context")
    )
    session_root = tmp_path / "sessions"

    app = AgentApplication(
        str(config_path), str(session_root), event_store=InMemoryEventStore()
    )
    assert app.get_config_errors() == []
    client = _install_test_client(app)

    try:
        create_response = client.post(
            "/sessions", json={"agent_id": "openrouter-image"}
        )
        assert create_response.status_code == 200
        session_id = create_response.json()["session"]["session_id"]

        send_response = client.post(
            f"/sessions/{session_id}/send_message",
            json={
                "message": {
                    "role": "user",
                    "content": "Generate a simple teal circle icon on a plain background.",
                },
                "config_overrides": {},
            },
        )
        assert send_response.status_code == 200
        assert send_response.json()["status"] == "started"

        events = _wait_for_final_event(client, session_id)
        error_events = [event for event in events if event.get("type") == "error"]
        if error_events:
            detail = error_events[-1].get("detail")
            if isinstance(detail, str) and (
                "402" in detail or "Payment Required" in detail
            ):
                pytest.skip(
                    f"OpenRouter account could not access default-config image-generation endpoint test: {detail}"
                )
        assert not error_events, error_events

        final_events = [event for event in events if event.get("type") == "final"]
        assert final_events, "expected final event from send_message endpoint"

        loaded_session = app.load_session_record(session_id)
        assert loaded_session is not None
        _assert_generated_image_response(
            loaded_session,
            final_events[-1]["messages"],
            app.get_session_asset_store(),
            require_session_asset_metadata=False,
        )
    finally:
        fastapi_app.dependency_overrides.clear()
        app.close()
