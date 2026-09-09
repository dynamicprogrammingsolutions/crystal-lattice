from __future__ import annotations

import json
import os
from pathlib import Path
import threading
import time
from typing import Iterator, Tuple

import pytest
from fastapi.testclient import TestClient

from agent_app.application_future import AgentApplication
from agent_app.session_listing import SessionListService
from agent_app.sessions import SessionStoreRecord
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


# Requirements: SLIST-003, SLIST-004, SLIST-005, SLIST-007, SLIST-010
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
        "meta": "Status: To do",
    }
    assert by_id["newer"]["session_status_label"] == "To do"
    assert by_id["newer"]["metadata"]["background_state"] == "ready"
    assert "native_messages" not in by_id["newer"]["metadata"]
    assert by_id["older"]["metadata"]["pinned"] is True
    assert by_id["older"]["presentation"]["meta"] == "Status: Done"
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


# Requirements: SLIST-004, SLIST-005, SLIST-010
def test_session_list_http_contract_orders_configured_pinned_metadata(
    tmp_path: Path,
) -> None:
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
                    f"path:{ROOT / 'plugins' / 'session-ordering-buckets-app'}",
                ],
                "agents": {"default": {"provider": "echo"}},
                "application": {
                    "session_pinned_metadata_key": "favorite",
                },
            }
        ),
        encoding="utf-8",
    )
    session_root = tmp_path / "sessions"
    application = AgentApplication(str(config_path), str(session_root))
    server_mod.app.dependency_overrides[server_mod.get_agent_app] = lambda: application
    client = TestClient(server_mod.app)

    try:
        _save_session(
            application,
            session_id="pinned-older",
            preview="pinned preview",
            metadata={},
        )
        _save_session(
            application,
            session_id="unpinned-newer",
            preview="unpinned preview",
            metadata={},
        )
        result = application.execute_application_action(
            plugin_id="session_pinned",
            action_id="toggle_session_pinned",
            params={"session_id": "pinned-older"},
        )
        assert result["mutations"]["updated_session_ids"] == ["pinned-older"]

        pinned_path = session_root / "pinned-older.json"
        unpinned_path = session_root / "unpinned-newer.json"
        os.utime(pinned_path, ns=(1_000_000_000, 1_000_000_000))
        os.utime(unpinned_path, ns=(2_000_000_000, 2_000_000_000))

        response = client.get("/sessions")
        assert response.status_code == 200
        summaries = response.json()["sessions"]
        assert [summary["session_id"] for summary in summaries] == [
            "pinned-older",
            "unpinned-newer",
        ]
        assert summaries[0]["metadata"]["favorite"] is True
        assert summaries[0]["pinned_rank"] == 0
        assert summaries[1]["pinned_rank"] == 1
        assert "pinned" not in summaries[0]

        ui_response = client.get("/application/ui-schema")
        assert ui_response.status_code == 200
        pin_action = next(
            element
            for element in ui_response.json()["elements"]
            if element.get("id") == "toggle_session_pinned"
        )
        assert pin_action["ui_type"] == "session_list_action"
        assert pin_action["rich_ui"]["value_path"] == "metadata.favorite"
        assert pin_action["rich_ui"]["missing_value"] is False
        assert pin_action["rich_ui"]["placements"] == [
            "header_trailing",
            "actions_bar",
        ]
        assert pin_action["rich_ui"]["appearance"]["active"]["tone"] == "highlight"
    finally:
        server_mod.app.dependency_overrides.clear()
        application.close()


# Requirements: SLIST-004, SLIST-005, SLIST-007, SLIST-010
def test_session_list_http_contract_sorts_recent_archives_below_other_sessions(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    import session_ordering_buckets_app as ordering_module

    fake_now = 1_700_000_000.0
    monkeypatch.setattr(ordering_module.time, "time", lambda: fake_now)

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
                    f"path:{ROOT / 'plugins' / 'session-archive-app'}",
                    f"path:{ROOT / 'plugins' / 'session-ordering-buckets-app'}",
                ],
                "agents": {"default": {"provider": "echo"}},
                "application": {
                    "session_archived_metadata_key": "hidden",
                },
            }
        ),
        encoding="utf-8",
    )
    session_root = tmp_path / "sessions"
    application = AgentApplication(str(config_path), str(session_root))
    server_mod.app.dependency_overrides[server_mod.get_agent_app] = lambda: application
    client = TestClient(server_mod.app)

    try:
        _save_session(
            application,
            session_id="recent-active",
            preview="recent active preview",
            metadata={"hidden": False},
        )
        _save_session(
            application,
            session_id="recent-archived",
            preview="recent archived preview",
            metadata={"hidden": False},
        )
        _save_session(
            application,
            session_id="old-active",
            preview="old active preview",
            metadata={"hidden": False},
        )
        _save_session(
            application,
            session_id="old-archived",
            preview="old archived preview",
            metadata={"hidden": True},
        )

        archive_result = application.execute_application_action(
            plugin_id="session_archive",
            action_id="toggle_session_archived",
            params={"session_id": "recent-archived"},
        )
        assert archive_result["mutations"]["updated_session_ids"] == ["recent-archived"]

        archive_window_seconds = 60 * 24 * 60 * 60
        timestamps = {
            "recent-active": fake_now - 3600,
            "recent-archived": fake_now - 60,
            "old-active": fake_now - archive_window_seconds,
            "old-archived": fake_now - archive_window_seconds - 1,
        }
        for session_id, timestamp in timestamps.items():
            path = session_root / f"{session_id}.json"
            timestamp_ns = int(timestamp * 1_000_000_000)
            os.utime(path, ns=(timestamp_ns, timestamp_ns))

        response = client.get("/sessions")
        assert response.status_code == 200
        summaries = response.json()["sessions"]
        assert [summary["session_id"] for summary in summaries] == [
            "recent-active",
            "old-active",
            "old-archived",
            "recent-archived",
        ]
        assert [summary["recent_archived_rank"] for summary in summaries] == [
            0,
            0,
            0,
            1,
        ]
        assert summaries[-1]["metadata"]["hidden"] is True
        assert "archived" not in summaries[-1]["metadata"]

        default_visible = application.list_session_summaries(apply_filter_defaults=True)
        assert [summary["session_id"] for summary in default_visible] == [
            "recent-active",
            "old-active",
        ]

        all_sessions = application.list_session_summaries(
            filter_values={"archive_state": None},
            apply_filter_defaults=True,
        )
        assert [summary["session_id"] for summary in all_sessions] == [
            "recent-active",
            "old-active",
            "old-archived",
            "recent-archived",
        ]
    finally:
        server_mod.app.dependency_overrides.clear()
        application.close()


# Requirements: SLIST-008, SLIST-010
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
        "session_status_label": "To do",
        "presentation": {
            "title": "Session malforme",
            "subtitle": None,
            "meta": "Status: To do",
        },
    }


class _BlockedHttpSessionStore:
    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()
        self.record = SessionStoreRecord(
            session_id="icloud-placeholder",
            modified=2.0,
            revision=("icloud-placeholder", 1),
        )

    def list_records(self) -> list[SessionStoreRecord]:
        return [self.record]

    def get_record(self, session_id: str) -> SessionStoreRecord | None:
        return self.record if session_id == self.record.session_id else None

    def load(
        self,
        session_id: str,
        *,
        snapshot_id: str | None = None,
    ) -> Session | None:
        _ = snapshot_id
        self.started.set()
        assert self.release.wait(timeout=2.0)
        return Session(
            session_id=session_id,
            messages=[Message(role="user", content="hydrated")],
            metadata={},
        )

    def save(self, session: Session) -> None:
        raise AssertionError("save is not used by this test")

    def delete(self, session_id: str) -> None:
        raise AssertionError("delete is not used by this test")


# Requirements: SLIST-013, SLIST-015, SLIST-020
def test_session_list_http_contract_returns_placeholder_before_slow_load() -> None:
    store = _BlockedHttpSessionStore()
    service = SessionListService(
        store=store,
        list_actions=lambda: [],
        list_ui_elements=lambda: [],
        execute_action=lambda *_args, **_kwargs: {},
        logger=None,
        context={
            "application_config": {
                "application": {
                    "cached_background_session_list": {
                        "foreground_timeout_seconds": 0.03,
                    }
                }
            }
        },
    )

    class _Application:
        def list_session_summaries(
            self,
            *,
            limit: int | None = None,
        ) -> list[dict[str, object]]:
            return service.list_session_summaries(limit=limit)

    server_mod.app.dependency_overrides[server_mod.get_agent_app] = _Application
    client = TestClient(server_mod.app)
    started = time.monotonic()
    try:
        response = client.get("/sessions")
    finally:
        server_mod.app.dependency_overrides.clear()

    assert time.monotonic() - started < 0.5
    assert response.status_code == 200
    assert response.json() == {
        "sessions": [
            {
                "session_id": "icloud-placeholder",
                "modified": 2.0,
                "preview": "",
                "metadata": {},
                "presentation": {
                    "title": "Session icloud-p",
                    "subtitle": None,
                    "meta": None,
                },
            }
        ]
    }
    assert store.started.is_set()

    store.release.set()
    service._shutdown()
