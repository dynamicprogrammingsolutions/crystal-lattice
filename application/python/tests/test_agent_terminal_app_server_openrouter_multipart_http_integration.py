"""OpenRouter multipart (image) integration test via the real FastAPI server.

This exercises the HTTP endpoints end-to-end (create session, append a
multipart user message, send request, poll events, and list messages).

Requires OPENROUTER_API_KEY.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

try:  # Load .env from the repo root
    from dotenv import load_dotenv

    ROOT = Path(__file__).resolve().parents[3]
    load_dotenv(ROOT / ".env")
except Exception:
    ROOT = Path(__file__).resolve().parents[3]


if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

APP_PY = ROOT / "application" / "python"
CORE_PY = ROOT / "core" / "python"
OPENROUTER_PLUGIN_SRC = ROOT / "plugins" / "openrouter" / "src"

for entry in (APP_PY, CORE_PY, OPENROUTER_PLUGIN_SRC):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))


from agent_app.application_future import AgentApplication
from agent_app.events import InMemoryEventStore


OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")
BASE_URL = "https://openrouter.ai/api/v1"
MODEL_GEMINI_FLASH_PREVIEW = "google/gemini-3-flash-preview"


@pytest.fixture(scope="module")
def ensure_api_key() -> None:
    if not OPENROUTER_API_KEY:
        pytest.skip("OPENROUTER_API_KEY not set; skipping OpenRouter integration test")


@pytest.mark.openrouter
def test_http_openrouter_multipart_image_flow(ensure_api_key: None, tmp_path: Path) -> None:
    from agent_terminal_app import server as server_mod
    from agent_terminal_app.server import app as fastapi_app
    from agent_terminal_app.server import get_agent_app

    cfg = {
        "providers": {
            "openrouter": {
                "provider": "openrouter",
                "model": MODEL_GEMINI_FLASH_PREVIEW,
                "api_key": OPENROUTER_API_KEY,
                "base_url": BASE_URL,
                "timeout": 60,
            }
        },
        "plugins": [
            "openrouter_plugins.openrouter_provider.OpenRouterProvider",
        ],
        "agents": {"default": {"provider": "openrouter"}},
    }

    config_path = tmp_path / "config_openrouter_multipart_http.json"
    config_path.write_text(__import__("json").dumps(cfg), encoding="utf-8")
    session_root = tmp_path / "sessions"

    event_store = InMemoryEventStore()
    app_instance = AgentApplication(
        str(config_path),
        str(session_root),
        event_store=event_store,
    )

    fastapi_app.dependency_overrides[get_agent_app] = lambda: app_instance
    client = TestClient(fastapi_app)

    try:
        system_message = "You are a helpful assistant."
        resp = client.post(
            "/sessions",
            json={"agent_id": "default", "system_message": system_message},
        )
        assert resp.status_code == 200
        session_id = resp.json()["session"]["session_id"]

        multipart = [
            {
                "type": "image",
                "content": {
                    "url": "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg",
                },
                "metadata": {},
            }
        ]

        resp = client.post(
            f"/sessions/{session_id}/messages",
            json={
                "role": "user",
                "content": "What's in this image?",
                "multipartContent": multipart,
                "metadata": None,
            },
        )
        assert resp.status_code == 200

        send_resp = client.post(
            f"/sessions/{session_id}/send",
            json={"config_overrides": {}},
        )
        assert send_resp.status_code == 200
        body = send_resp.json()
        assert body.get("status") == "started"
        request_id = body.get("request_id")
        assert isinstance(request_id, str) and request_id

        last_event_id: str | None = None
        deadline = time.time() + 60.0
        seen_final = False

        while time.time() < deadline:
            params = {"session_id": session_id}
            if last_event_id is not None:
                params["since_id"] = last_event_id
            ev_resp = client.get("/events", params=params)
            assert ev_resp.status_code == 200
            events = ev_resp.json().get("events") or []
            if events:
                last_event_id = events[-1].get("event_id") or last_event_id
                types = {ev.get("type") for ev in events if isinstance(ev, dict)}
                if "final" in types or "request_completed" in types:
                    seen_final = True
                    break
            time.sleep(0.2)

        assert seen_final, "timed out waiting for OpenRouter response"

        msg_resp = client.get(f"/sessions/{session_id}/messages")
        assert msg_resp.status_code == 200
        results = msg_resp.json().get("messages") or []
        assert results

        user_msg = results[-2]["message"]
        assert user_msg["role"] == "user"
        assert user_msg.get("multipartContent") == multipart

        assistant_msg = results[-1]["message"]
        assert assistant_msg["role"] == "assistant"
        assert isinstance(assistant_msg.get("content"), str)
        assert assistant_msg["content"].strip()

    finally:
        server_mod.app.dependency_overrides.pop(get_agent_app, None)
