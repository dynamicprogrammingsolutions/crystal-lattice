"""Reviewable integration scenarios for the application session-list contract."""

from __future__ import annotations

from contextlib import contextmanager
import json
import os
from pathlib import Path
import threading
import time
from typing import Any, Iterator

import pytest
from fastapi.testclient import TestClient

from agent_app.application_future import AgentApplication
from agent_core import Message, Session
from agent_terminal_app import server as server_mod
from agent_terminal_app.terminal_app import TerminalApplication


ROOT = Path(__file__).resolve().parents[3]


class SessionListIntegrationFixturePlugin:
    """Real loader fixture for contribution, context, and failure assertions."""

    name = "session_list_integration_fixture"
    version = "1.0.0"

    def init(self, app_config: dict[str, Any]) -> dict[str, Any]:
        _ = app_config
        return {}

    def get_config_schema(self) -> dict[str, Any]:
        return {}

    def get_ui_elements(
        self,
        state: dict[str, Any],
        config: dict[str, Any] | None = None,
        context: dict[str, Any] | None = None,
    ) -> list[dict[str, Any]]:
        _ = state, config, context
        return [
            {
                "ui_type": "session_list_field",
                "id": "integration_subtitle",
                "role": "subtitle",
                "data": "integration.marker",
                "template": "Fixture {{data}}",
            }
        ]

    def get_actions(self, state: dict[str, Any]) -> list[dict[str, Any]]:
        _ = state
        return [
            {
                "id": "contribute_integration_fields",
                "label": "Contribute integration fields",
                "trigger": "session_list",
                "inputs": {
                    "session_id": {"required": True},
                    "session_summary": {"required": True},
                    "session": {"required": True},
                },
            },
            {
                "id": "optionally_fail_integration",
                "label": "Optionally fail integration",
                "trigger": "session_list",
                "inputs": {
                    "session_summary": {"required": True},
                },
            },
        ]

    def execute_action(
        self,
        app: Any,
        action_id: str,
        params: dict[str, Any],
        context: dict[str, Any] | None,
        state: dict[str, Any],
    ) -> dict[str, Any]:
        _ = app, state
        if (context or {}).get("lifecycle") != "session_list":
            raise ValueError("expected the session_list lifecycle")
        summary = params["session_summary"]
        metadata = summary.get("metadata") or {}

        if action_id == "optionally_fail_integration":
            if metadata.get("fail_integration_action"):
                raise RuntimeError("simulated plugin failure")
            return {"session_list_fields": {"after_integration_failure": True}}

        if action_id != "contribute_integration_fields":
            raise ValueError(f"unknown action {action_id!r}")
        if params["session"].session_id != params["session_id"]:
            raise ValueError("declared session inputs did not match")

        result: dict[str, Any] = {
            "session_list_fields": {
                "integration": {
                    "marker": params["session_id"],
                }
            }
        }
        if metadata.get("invalid_integration_order"):
            result["session_list_order"] = {
                "key": "integration.marker",
                "direction": "sideways",
            }
        return result


def _write_config(
    tmp_path: Path,
    *,
    foreground_timeout_seconds: float = 1.0,
    persistent_cache_enabled: bool = True,
    include_list_plugins: bool = True,
) -> Path:
    plugins = ["plugins.echo_openai_like_provider.EchoOpenAILikeProvider"]
    if include_list_plugins:
        plugins.extend(
            (
                (f"{__name__}." "SessionListIntegrationFixturePlugin"),
                f"path:{ROOT / 'plugins' / 'session-pinned-app'}",
                f"path:{ROOT / 'plugins' / 'session-status-app'}",
                f"path:{ROOT / 'plugins' / 'session-ordering-buckets-app'}",
            )
        )
    config = {
        "plugin_cache_dir": str(tmp_path / "plugin-cache"),
        "providers": {
            "echo": {
                "provider": "echo_openai_like",
                "model": "test-model",
            }
        },
        "plugins": plugins,
        "agents": {"default": {"provider": "echo"}},
        "application": {
            "cached_background_session_list": {
                "foreground_timeout_seconds": foreground_timeout_seconds,
                "worker_count": 1,
                "persistent_cache_enabled": persistent_cache_enabled,
                "local_cache_directory": str(tmp_path / "session-list-cache"),
            }
        },
    }
    path = tmp_path / "config.json"
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def _save_session(
    application: AgentApplication,
    *,
    session_id: str,
    user_messages: list[str],
    metadata: dict[str, Any] | None = None,
) -> None:
    messages = [Message(role="system", content="system")]
    messages.extend(Message(role="user", content=content) for content in user_messages)
    application.save_session(
        Session(
            session_id=session_id,
            messages=messages,
            metadata={"agent_id": "default", **(metadata or {})},
        )
    )


def _set_mtime(path: Path, seconds: float) -> None:
    nanoseconds = int(seconds * 1_000_000_000)
    os.utime(path, ns=(nanoseconds, nanoseconds))


@contextmanager
def _serve(application: AgentApplication) -> Iterator[TestClient]:
    server_mod.app.dependency_overrides[server_mod.get_agent_app] = lambda: application
    try:
        with TestClient(server_mod.app) as client:
            yield client
    finally:
        server_mod.app.dependency_overrides.clear()


def _session_by_id(response: Any) -> dict[str, dict[str, Any]]:
    assert response.status_code == 200
    payload = response.json()
    assert set(payload) == {"sessions"}
    return {summary["session_id"]: summary for summary in payload["sessions"]}


# Requirements:
# - SLIST-001: Exercises list, exact, diagnostics, filter schema, and filter evaluation.
# - SLIST-002: Reviews opaque filesystem records and exact record lookup through the app store.
# - SLIST-003: Asserts normalized/truncated preview, metadata exclusion, fields, and presentation.
# - SLIST-004: Checks declared inputs, contributions, and isolated failure through real loading.
# - SLIST-005: Confirms plugin ordering and diagnostic fallback for an invalid order.
# - SLIST-006: Confirms dotted contributed presentation, title fallback, and status metadata.
# - SLIST-007: Applies real declarative filters before a limit and bypasses them for exact lookup.
# - SLIST-008: Isolates both a failed list action and one malformed stored JSON document.
# - SLIST-009: Reuses a summary, then observes an externally changed filesystem revision.
# - SLIST-010: Reviews the same result through HTTP, terminal, and exact-summary adapters.
@pytest.mark.integration
def test_preserved_session_listing_contract_in_a_real_application(
    tmp_path: Path,
) -> None:
    """Given real sessions and plugins, all established consumers share one contract."""

    config_path = _write_config(tmp_path)
    session_root = tmp_path / "sessions"
    application = AgentApplication(config_path, session_root)
    long_preview = "  Alpha   " + ("word " * 30)
    _save_session(
        application,
        session_id="older-pinned",
        user_messages=[long_preview],
        metadata={
            "pinned": True,
            "status": "done",
            "native_messages": [{"role": "user", "content": "private"}],
            "fail_integration_action": True,
        },
    )
    _save_session(
        application,
        session_id="newer-active",
        user_messages=["newer preview"],
        metadata={
            "status": "todo",
            "invalid_integration_order": True,
        },
    )
    malformed_path = session_root / "malformed.json"
    malformed_path.write_text("{not json", encoding="utf-8")
    _set_mtime(session_root / "older-pinned.json", 1.0)
    _set_mtime(session_root / "newer-active.json", 3.0)
    _set_mtime(malformed_path, 0.5)

    try:
        records = application._session_store.list_records()
        assert {record.session_id for record in records} == {
            "older-pinned",
            "newer-active",
            "malformed",
        }
        assert all(not hasattr(record, "path") for record in records)
        assert application._session_store.get_record("older-pinned") is not None

        with _serve(application) as client:
            first_response = client.get("/sessions")
            first = first_response.json()["sessions"]
            by_id = _session_by_id(first_response)

            assert [summary["session_id"] for summary in first][:2] == [
                "older-pinned",
                "newer-active",
            ]
            pinned = by_id["older-pinned"]
            assert len(pinned["preview"]) == 80
            assert pinned["preview"].startswith("Alpha word word")
            assert "  " not in pinned["preview"]
            assert "native_messages" not in pinned["metadata"]
            assert pinned["session_status_label"] == "Done"
            assert pinned["presentation"]["title"] == pinned["preview"]
            assert pinned["presentation"]["subtitle"] == "Fixture older-pinned"
            assert pinned["presentation"]["meta"] == "Status: Done"
            assert pinned["integration"]["marker"] == "older-pinned"
            assert "after_integration_failure" not in pinned
            assert by_id["malformed"]["preview"] == ""
            assert by_id["malformed"]["metadata"] == {}
            diagnostic_codes = {
                item["code"] for item in application.get_session_list_diagnostics()
            }
            assert "session_summary_load_failed" in diagnostic_codes
            assert "session_list_action_failed" in diagnostic_codes
            assert "invalid_session_list_order_spec" in diagnostic_codes

            exact = client.get("/sessions/older-pinned/summary")
            assert exact.status_code == 200
            assert exact.json()["session"] == pinned
            assert client.get("/sessions/missing/summary").status_code == 404

            terminal = TerminalApplication(
                config_path=config_path,
                session_root=session_root,
                agent_app=application,
            )
            assert terminal.list_sessions_metadata() == first

            filtered = application.list_session_summaries(
                filter_values={"pinned_state": True},
                apply_filter_defaults=True,
                limit=1,
            )
            assert [summary["session_id"] for summary in filtered] == ["older-pinned"]
            assert (
                application.get_session_summary("newer-active")["session_id"]
                == "newer-active"
            )
            schema = application.get_session_list_filter_schema()
            assert {"pinned_state", "session_status"}.issubset(
                {item["id"] for item in schema["filters"]}
            )
            second_response = client.get("/sessions")
            assert second_response.json() == first_response.json()

            newer_path = session_root / "newer-active.json"
            raw = json.loads(newer_path.read_text(encoding="utf-8"))
            raw["messages"][1]["content"] = "externally updated"
            newer_path.write_text(json.dumps(raw), encoding="utf-8")
            _set_mtime(newer_path, 4.0)
            refreshed = client.get("/sessions/newer-active/summary")
            assert refreshed.status_code == 200
            assert refreshed.json()["session"]["preview"] == "externally updated"
    finally:
        application.close()


# Requirements:
# - SLIST-011: Uses only public list responses while private context selects the resolver.
# - SLIST-012: Delays attribute enumeration and proves no content load starts before it ends.
# - SLIST-013: Returns every mixed complete/blocked session in the unchanged HTTP shape.
# - SLIST-015: Verifies newest-first work, the post-enumeration deadline, and later completion.
# - SLIST-016: Reviews complete-first ordering, conservative filters, and limit-last behavior.
# - SLIST-017: Leaves one bounded background worker to finish the simulated hydration.
# - SLIST-020: Exercises the production HTTP route without any client-specific scan protocol.
@pytest.mark.integration
def test_cold_icloud_like_http_listing_returns_all_sessions_then_converges(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Given slow metadata and hydration, HTTP returns a useful complete collection."""

    metadata_delay = 0.06
    foreground_timeout = 0.05
    config_path = _write_config(
        tmp_path,
        foreground_timeout_seconds=foreground_timeout,
    )
    session_root = tmp_path / "sessions"
    application = AgentApplication(config_path, session_root)
    _save_session(
        application,
        session_id="newest",
        user_messages=["newest preview"],
        metadata={"status": "done"},
    )
    _save_session(
        application,
        session_id="middle-blocked",
        user_messages=["middle preview"],
        metadata={"status": "todo"},
    )
    _save_session(
        application,
        session_id="oldest",
        user_messages=["oldest preview"],
        metadata={"status": "todo"},
    )
    _set_mtime(session_root / "newest.json", 3.0)
    _set_mtime(session_root / "middle-blocked.json", 2.0)
    _set_mtime(session_root / "oldest.json", 1.0)

    store = application._session_store
    original_list_records = store.list_records
    original_load = store.load
    enumeration_finished = threading.Event()
    hydration_started = threading.Event()
    release_hydration = threading.Event()
    load_order: list[str] = []
    load_lock = threading.Lock()

    def delayed_list_records() -> Any:
        time.sleep(metadata_delay)
        records = original_list_records()
        enumeration_finished.set()
        return records

    def delayed_load(
        session_id: str,
        *,
        snapshot_id: str | None = None,
    ) -> Session | None:
        assert enumeration_finished.is_set()
        with load_lock:
            load_order.append(session_id)
        if session_id == "middle-blocked":
            hydration_started.set()
            assert release_hydration.wait(timeout=3.0)
        return original_load(session_id, snapshot_id=snapshot_id)

    monkeypatch.setattr(store, "list_records", delayed_list_records)
    monkeypatch.setattr(store, "load", delayed_load)

    try:
        with _serve(application) as client:
            started = time.monotonic()
            response = client.get("/sessions")
            elapsed = time.monotonic() - started

            assert enumeration_finished.is_set()
            assert hydration_started.is_set()
            assert elapsed >= metadata_delay + (foreground_timeout * 0.7)
            assert elapsed < metadata_delay + foreground_timeout + 0.35
            sessions = response.json()["sessions"]
            assert [item["session_id"] for item in sessions] == [
                "newest",
                "middle-blocked",
                "oldest",
            ]
            assert sessions[0]["preview"] == "newest preview"
            assert sessions[1]["preview"] == ""
            assert sessions[2]["preview"] == ""
            assert all("summary_state" not in item for item in sessions)
            assert load_order == ["newest", "middle-blocked"]

            filtered_and_limited = application.list_session_summaries(
                filter_values={"session_status": ["done"]},
                apply_filter_defaults=True,
                limit=2,
            )
            assert [item["session_id"] for item in filtered_and_limited] == [
                "newest",
                "middle-blocked",
            ]

            release_hydration.set()
            deadline = time.monotonic() + 3.0
            completed: list[dict[str, Any]] = []
            while time.monotonic() < deadline:
                completed = client.get("/sessions").json()["sessions"]
                if all(item["preview"] for item in completed):
                    break
            assert [item["preview"] for item in completed] == [
                "newest preview",
                "middle preview",
                "oldest preview",
            ]
            assert load_order == ["newest", "middle-blocked", "oldest"]
    finally:
        release_hydration.set()
        application.close()


# Requirements:
# - SLIST-009: Confirms real save, external revision, and delete paths invalidate reused data.
# - SLIST-014: Restarts AgentApplication and lists unchanged sessions with zero content loads.
# - SLIST-018: Corrupts only derived state, then verifies safe rebuild and source preservation.
# - SLIST-019: Converges persistent summaries after save, external edit, and deletion.
@pytest.mark.integration
def test_persistent_summaries_survive_restart_and_follow_real_mutations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Given persisted summaries, restarts and source mutations converge safely."""

    config_path = _write_config(tmp_path, include_list_plugins=False)
    session_root = tmp_path / "sessions"
    cache_root = tmp_path / "session-list-cache"

    first_application = AgentApplication(config_path, session_root)
    _save_session(
        first_application,
        session_id="mutable",
        user_messages=["original"],
    )
    _save_session(
        first_application,
        session_id="survivor",
        user_messages=["survives cache corruption"],
    )
    with _serve(first_application) as client:
        assert set(_session_by_id(client.get("/sessions"))) == {
            "mutable",
            "survivor",
        }
    first_application.close()

    second_application = AgentApplication(config_path, session_root)
    second_store = second_application._session_store
    original_load = second_store.load
    load_calls: list[str] = []

    def counting_load(
        session_id: str,
        *,
        snapshot_id: str | None = None,
    ) -> Session | None:
        load_calls.append(session_id)
        return original_load(session_id, snapshot_id=snapshot_id)

    monkeypatch.setattr(second_store, "load", counting_load)
    try:
        with _serve(second_application) as client:
            warm = _session_by_id(client.get("/sessions"))
            assert warm["mutable"]["preview"] == "original"
            assert load_calls == []

            second_application.save_session(
                Session(
                    session_id="mutable",
                    messages=[Message(role="user", content="saved update")],
                    metadata={"agent_id": "default"},
                )
            )
            load_calls.clear()
            saved = _session_by_id(client.get("/sessions"))
            assert saved["mutable"]["preview"] == "saved update"
            assert load_calls == ["mutable"]

            mutable_path = session_root / "mutable.json"
            raw = json.loads(mutable_path.read_text(encoding="utf-8"))
            raw["messages"][0]["content"] = "external update"
            mutable_path.write_text(json.dumps(raw), encoding="utf-8")
            stat = mutable_path.stat()
            os.utime(
                mutable_path,
                ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000),
            )
            external = client.get("/sessions/mutable/summary")
            assert external.status_code == 200
            assert external.json()["session"]["preview"] == "external update"

            second_application.delete_session("mutable")
            after_delete = _session_by_id(client.get("/sessions"))
            assert set(after_delete) == {"survivor"}
    finally:
        second_application.close()

    cache_files = list(cache_root.glob("*.sqlite3"))
    assert len(cache_files) == 1
    cache_files[0].write_bytes(b"corrupt derived state")

    third_application = AgentApplication(config_path, session_root)
    try:
        with _serve(third_application) as client:
            rebuilt = _session_by_id(client.get("/sessions"))
            assert rebuilt["survivor"]["preview"] == "survives cache corruption"
            assert (session_root / "survivor.json").is_file()
            assert list(cache_root.glob("*.corrupt-*"))
    finally:
        third_application.close()


# Requirements:
# - SLIST-013: Keeps the session present while two real HTTP requests await one hydration.
# - SLIST-015: Automatically resolves the newest externally changed revision in background.
# - SLIST-017: Coalesces concurrent HTTP calls and cooperatively closes a blocked resolver.
# - SLIST-019: Discards stale in-flight content and publishes only the external revision.
# - SLIST-020: Preserves the ordinary HTTP response throughout concurrency and shutdown.
@pytest.mark.integration
def test_concurrent_http_hydration_discards_stale_work_and_closes_cleanly(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Given concurrent hydration and an external edit, only current data is published."""

    config_path = _write_config(
        tmp_path,
        foreground_timeout_seconds=0.04,
        persistent_cache_enabled=False,
        include_list_plugins=False,
    )
    session_root = tmp_path / "sessions"
    application = AgentApplication(config_path, session_root)
    _save_session(
        application,
        session_id="changing",
        user_messages=["old content"],
    )
    store = application._session_store
    original_load = store.load
    first_load_started = threading.Event()
    release_first_load = threading.Event()
    close_load_started = threading.Event()
    release_close_load = threading.Event()
    load_count = 0
    load_lock = threading.Lock()

    def blocked_first_load(
        session_id: str,
        *,
        snapshot_id: str | None = None,
    ) -> Session | None:
        nonlocal load_count
        loaded = original_load(session_id, snapshot_id=snapshot_id)
        with load_lock:
            load_count += 1
            call_number = load_count
        if call_number == 1:
            first_load_started.set()
            assert release_first_load.wait(timeout=3.0)
        elif call_number == 3:
            close_load_started.set()
            assert release_close_load.wait(timeout=3.0)
        return loaded

    monkeypatch.setattr(store, "load", blocked_first_load)

    try:
        with _serve(application) as client:
            barrier = threading.Barrier(3)
            responses: list[Any] = []

            def request_sessions() -> None:
                barrier.wait()
                responses.append(client.get("/sessions"))

            threads = [
                threading.Thread(target=request_sessions),
                threading.Thread(target=request_sessions),
            ]
            for thread in threads:
                thread.start()
            barrier.wait()
            assert first_load_started.wait(timeout=1.0)
            for thread in threads:
                thread.join(timeout=1.0)

            assert len(responses) == 2
            assert load_count == 1
            for response in responses:
                by_id = _session_by_id(response)
                assert by_id["changing"]["preview"] == ""

            session_path = session_root / "changing.json"
            raw = json.loads(session_path.read_text(encoding="utf-8"))
            raw["messages"][1]["content"] = "current external content"
            session_path.write_text(json.dumps(raw), encoding="utf-8")
            stat = session_path.stat()
            os.utime(
                session_path,
                ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000),
            )
            while_stale = _session_by_id(client.get("/sessions"))
            assert while_stale["changing"]["preview"] == ""

            release_first_load.set()
            deadline = time.monotonic() + 3.0
            current: dict[str, dict[str, Any]] = {}
            while time.monotonic() < deadline:
                current = _session_by_id(client.get("/sessions"))
                if current["changing"]["preview"] == "current external content":
                    break
            assert current["changing"]["preview"] == "current external content"
            assert load_count == 2

            raw = json.loads(session_path.read_text(encoding="utf-8"))
            raw["messages"][1]["content"] = "blocked during close"
            session_path.write_text(json.dumps(raw), encoding="utf-8")
            stat = session_path.stat()
            os.utime(
                session_path,
                ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000),
            )
            closing = _session_by_id(client.get("/sessions"))
            assert closing["changing"]["preview"] == ""
            assert close_load_started.is_set()

            application.close()
            release_close_load.set()
    finally:
        release_first_load.set()
        release_close_load.set()
        application.close()

    workers = application._session_list_service._resolver._workers
    deadline = time.monotonic() + 1.0
    while time.monotonic() < deadline and any(worker.is_alive() for worker in workers):
        time.sleep(0.01)
    assert all(not worker.is_alive() for worker in workers)
