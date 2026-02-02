from __future__ import annotations

import os
import sys
from pathlib import Path

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


def test_openrouter_config_loads_and_plugins_resolve(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Load the OpenRouter terminal config and ensure plugin specs resolve.

    This test is intentionally offline: it does not call OpenRouter.
    It validates that the new plugin-repo architecture can be resolved
    via LocalPath module-only specs.
    """

    from agent_app.application_future import AgentApplication

    config_path = APP_PY / "agent_terminal_app" / "config_openrouter_app_layer.json"
    session_root = tmp_path / "sessions"

    # Ensure placeholders used by the config resolve.
    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")

    # Ensure the default cache path (~/.crystal/cache/plugins) resolves into
    # a temporary home directory so the test is reproducible and does not
    # write into the developer's real home.
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    app = AgentApplication(str(config_path), str(session_root))
    errs = app.get_config_errors()
    assert errs == [], f"expected no config/plugin errors, got: {errs}"


def test_openrouter_app_plugins_execute_via_server_endpoints(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Sanity-check application plugins via FastAPI endpoints.

    This stays offline (no OpenRouter calls). It exercises the /actions
    endpoint against an AgentApplication built from the standard
    config_openrouter_app_layer.json and verifies that application plugins
    are available and can modify session metadata.
    """

    from agent_app.application_future import AgentApplication
    from agent_terminal_app import server as server_mod

    config_path = APP_PY / "agent_terminal_app" / "config_openrouter_app_layer.json"
    session_root = tmp_path / "sessions"

    monkeypatch.setenv("OPENROUTER_API_KEY", "test_key")
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    app = AgentApplication(str(config_path), str(session_root))
    errs = app.get_config_errors()
    assert errs == [], f"expected no config/plugin errors, got: {errs}"

    # Ensure FastAPI dependency injection uses this instance.
    server_mod._agent_app = app

    client = TestClient(server_mod.app)

    actions = client.get("/application/actions").json().get("actions") or []
    assert any(
        isinstance(a, dict)
        and a.get("plugin") == "session_pinned"
        and a.get("id") == "toggle_session_pinned"
        for a in actions
    ), f"expected session_pinned action in /application/actions, got: {actions}"

    resp = client.post("/sessions", json={})
    assert resp.status_code == 200
    created = resp.json().get("session") or {}
    session_id = created.get("session_id")
    assert isinstance(session_id, str) and session_id

    toggle = client.post(
        "/actions",
        json={
            "plugin": "session_pinned",
            "action_id": "toggle_session_pinned",
            "inputs": {"session_id": session_id},
        },
    )
    assert toggle.status_code == 200
    payload = toggle.json()
    assert payload.get("status") == "ok", payload

    listed = client.get("/sessions").json().get("sessions") or []
    entry = next((s for s in listed if isinstance(s, dict) and s.get("session_id") == session_id), None)
    assert entry is not None
    metadata = entry.get("metadata") or {}
    assert metadata.get("pinned") is True
