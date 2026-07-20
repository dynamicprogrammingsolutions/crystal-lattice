from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Iterator, Tuple

import pytest
from fastapi.testclient import TestClient

from agent_app.application_future import AgentApplication
from agent_core import Message, Session
from agent_terminal_app import server as server_mod


ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture
def session_list_http_client(
    tmp_path: Path,
) -> Iterator[Tuple[TestClient, AgentApplication, Path]]:
    config_path = tmp_path / "config.json"
    config_path.write_text(
        json.dumps(
            {
                "providers": {
                    "echo": {
                        "provider": "echo_openai_like",
                        "model": "test-model",
                    }
                },
                "plugins": [
                    "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
                    f"path:{ROOT / 'plugins' / 'session-pinned-app'}",
                    f"path:{ROOT / 'plugins' / 'session-status-app'}",
                ],
                "agents": {"default": {"provider": "echo"}},
            }
        ),
        encoding="utf-8",
    )
    session_root = tmp_path / "sessions"
    application = AgentApplication(str(config_path), str(session_root))
    server_mod.app.dependency_overrides[server_mod.get_agent_app] = lambda: application
    client = TestClient(server_mod.app)

    try:
        yield client, application, session_root
    finally:
        server_mod.app.dependency_overrides.clear()
        application.close()


def _save_session(
    application: AgentApplication,
    *,
    session_id: str,
    preview: str,
    metadata: dict[str, object],
) -> None:
    application.save_session(
        Session(
            session_id=session_id,
            messages=(
                Message(role="system", content="system"),
                Message(role="user", content=preview),
            ),
            metadata={"agent_id": "default", **metadata},
        )
    )


def test_session_list_http_contract_serializes_shared_summaries(
    session_list_http_client: Tuple[TestClient, AgentApplication, Path],
) -> None:
    client, application, session_root = session_list_http_client
    _save_session(
        application,
        session_id="older",
        preview="older preview",
        metadata={"pinned": True, "status": "done"},
    )
    _save_session(
        application,
        session_id="newer",
        preview="newer preview",
        metadata={
            "background_state": "ready",
            "native_messages": [{"role": "user", "content": "private"}],
        },
    )

    older_path = session_root / "older.json"
    newer_path = session_root / "newer.json"
    os.utime(older_path, ns=(1_000_000_000, 1_000_000_000))
    os.utime(newer_path, ns=(2_000_000_000, 2_000_000_000))

    response = client.get("/sessions")
    assert response.status_code == 200
    sessions = response.json()["sessions"]
    assert [summary["session_id"] for summary in sessions] == ["newer", "older"]

    by_id = {summary["session_id"]: summary for summary in sessions}
    assert by_id["newer"]["presentation"] == {
        "title": "newer preview",
        "subtitle": None,
        "meta": None,
    }
    assert by_id["newer"]["metadata"]["background_state"] == "ready"
    assert "native_messages" not in by_id["newer"]["metadata"]
    assert by_id["older"]["metadata"]["pinned"] is True
    assert "pinned" not in by_id["older"]

    pinned = application.list_session_summaries(
        filter_values={"pinned_state": True},
        apply_filter_defaults=True,
    )
    assert [summary["session_id"] for summary in pinned] == ["older"]
    todo = application.list_session_summaries(
        filter_values={"session_status": ["todo"]},
        apply_filter_defaults=True,
    )
    assert [summary["session_id"] for summary in todo] == ["newer"]

    schema_response = client.get("/application/ui-schema")
    assert schema_response.status_code == 200
    filters = {
        element["id"]: element
        for element in schema_response.json()["elements"]
        if element.get("ui_type") == "session_list_filter"
    }
    assert filters["pinned_state"]["plugin"] == "session_pinned"
    assert filters["session_status"]["plugin"] == "session_status"

    limited = client.get("/sessions", params={"limit": 1})
    assert limited.status_code == 200
    assert limited.json()["sessions"] == [by_id["newer"]]

    exact = client.get("/sessions/newer/summary")
    assert exact.status_code == 200
    assert exact.json()["session"] == by_id["newer"]

    missing = client.get("/sessions/missing/summary")
    assert missing.status_code == 404
    assert "missing" in missing.json()["detail"]


def test_session_list_http_contract_isolates_a_malformed_record(
    session_list_http_client: Tuple[TestClient, AgentApplication, Path],
) -> None:
    client, application, session_root = session_list_http_client
    _save_session(
        application,
        session_id="valid",
        preview="valid preview",
        metadata={},
    )
    (session_root / "malformed.json").write_text("{not json", encoding="utf-8")

    response = client.get("/sessions")
    assert response.status_code == 200
    by_id = {summary["session_id"]: summary for summary in response.json()["sessions"]}

    assert by_id["valid"]["preview"] == "valid preview"
    assert by_id["malformed"] == {
        "session_id": "malformed",
        "modified": (session_root / "malformed.json").stat().st_mtime,
        "preview": "",
        "metadata": {},
        "presentation": {
            "title": "Session malforme",
            "subtitle": None,
            "meta": None,
        },
    }
