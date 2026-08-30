from __future__ import annotations

from typing import Any, Dict

from fastapi.testclient import TestClient

from agent_terminal_app.server import app, get_agent_app


class _StatusApplication:
    def __init__(self) -> None:
        self.requested: list[str] | None = None

    def get_session_request_statuses(
        self,
        session_ids: list[str],
    ) -> Dict[str, Any]:
        self.requested = session_ids
        if any(not isinstance(value, str) or not value for value in session_ids):
            raise ValueError("session_ids must contain only non-empty strings")
        return {
            "version": 1,
            "authority": "derived_transient",
            "statuses": [
                {
                    "session_id": session_id,
                    "request_id": None,
                    "state": "succeeded",
                    "basis": "session_tail",
                    "session_modified": 10.0,
                }
                for session_id in dict.fromkeys(session_ids)
                if session_id != "missing"
            ],
            "missing_session_ids": [
                session_id
                for session_id in dict.fromkeys(session_ids)
                if session_id == "missing"
            ],
        }


def test_status_endpoint_requires_explicit_session_ids() -> None:
    application = _StatusApplication()
    app.dependency_overrides[get_agent_app] = lambda: application
    client = TestClient(app)
    try:
        response = client.post("/sessions/request-statuses", json={})
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert response.json()["detail"] == "session_ids is required"
    assert application.requested is None


def test_status_endpoint_returns_only_requested_statuses_and_partial_missing() -> None:
    application = _StatusApplication()
    app.dependency_overrides[get_agent_app] = lambda: application
    client = TestClient(app)
    try:
        response = client.post(
            "/sessions/request-statuses",
            json={"session_ids": ["one", "missing", "one"]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 200
    assert application.requested == ["one", "missing", "one"]
    body = response.json()
    assert body["version"] == 1
    assert body["authority"] == "derived_transient"
    assert [status["session_id"] for status in body["statuses"]] == ["one"]
    assert body["missing_session_ids"] == ["missing"]
    assert isinstance(body["generated_at"], str)


def test_status_endpoint_validates_session_id_items() -> None:
    application = _StatusApplication()
    app.dependency_overrides[get_agent_app] = lambda: application
    client = TestClient(app)
    try:
        response = client.post(
            "/sessions/request-statuses",
            json={"session_ids": ["ok", ""]},
        )
    finally:
        app.dependency_overrides.clear()

    assert response.status_code == 400
    assert "non-empty strings" in response.json()["detail"]
