"""Integration coverage for the application session-list contract."""

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
    """Application plugin used to exercise session-list action behavior."""

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
# - SLIST-002: Asserts opaque filesystem records and exact record lookup through the app store.
# - SLIST-003: Asserts normalized/truncated preview, metadata exclusion, fields, and presentation.
# - SLIST-004: Checks declared inputs, contributions, and isolated failure through plugin loading.
# - SLIST-005: Confirms plugin ordering and diagnostic fallback for an invalid order.
# - SLIST-006: Confirms dotted contributed presentation, title fallback, and status metadata.
# - SLIST-007: Applies configured filters before a limit and bypasses them for exact lookup.
# - SLIST-008: Isolates both a failed list action and one malformed stored JSON document.
# - SLIST-009: Reuses a summary, then observes an externally changed filesystem revision.
# - SLIST-010: Asserts the same result through HTTP, terminal, and exact-summary adapters.
@pytest.mark.integration
def test_preserved_session_listing_contract_across_storage_plugins_and_adapters(
    tmp_path: Path,
) -> None:
    """Verify the established contract across storage, plugins, and adapters.

    Setup:
        Configure the session-list fixture, pin, status, and ordering plugins.
        Store one newer session, one older pinned session, and one malformed
        JSON file. The pinned session asks the fixture action to fail after an
        earlier action contributes a nested field. The newer session returns
        an invalid order declaration.

    Requirement assertions:
        SLIST-001 and SLIST-002 are asserted by the record collection, exact
        record lookup, filter schema, diagnostics, and exact summary calls.
        SLIST-003 and SLIST-006 are asserted by the preview, metadata,
        contributed fields, and presentation checks on ``older-pinned``.
        SLIST-004, SLIST-005, and SLIST-008 are asserted by the contributed
        field, pin ordering, malformed-file fallback, and the three diagnostic
        code checks.
        SLIST-007 is asserted by the pinned filter with ``limit=1`` and the
        unfiltered exact lookup.
        SLIST-009 is asserted by identical repeated output followed by an
        external file revision whose new preview is returned.
        SLIST-010 is asserted by matching HTTP and terminal collections, the
        HTTP envelope helper, exact HTTP lookup, and the missing-ID 404.
    """

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
        # SLIST-001, SLIST-002: membership and exact storage records expose no path.
        records = application._session_store.list_records()
        assert {record.session_id for record in records} == {
            "older-pinned",
            "newer-active",
            "malformed",
        }
        assert all(not hasattr(record, "path") for record in records)
        assert application._session_store.get_record("older-pinned") is not None

        with _serve(application) as client:
            # SLIST-001, SLIST-010: the HTTP adapter returns the shared envelope.
            first_response = client.get("/sessions")
            first = first_response.json()["sessions"]
            by_id = _session_by_id(first_response)

            # SLIST-004, SLIST-005: declared contributions place the pin first.
            assert [summary["session_id"] for summary in first][:2] == [
                "older-pinned",
                "newer-active",
            ]
            pinned = by_id["older-pinned"]
            # SLIST-003, SLIST-004, SLIST-006: complete summary and presentation.
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

            # SLIST-004, SLIST-005, SLIST-008: independent failures use fallbacks.
            assert by_id["malformed"]["preview"] == ""
            assert by_id["malformed"]["metadata"] == {}
            diagnostic_codes = {
                item["code"] for item in application.get_session_list_diagnostics()
            }
            assert "session_summary_load_failed" in diagnostic_codes
            assert "session_list_action_failed" in diagnostic_codes
            assert "invalid_session_list_order_spec" in diagnostic_codes

            # SLIST-001, SLIST-007, SLIST-010: exact lookup is unfiltered.
            exact = client.get("/sessions/older-pinned/summary")
            assert exact.status_code == 200
            assert exact.json()["session"] == pinned
            assert client.get("/sessions/missing/summary").status_code == 404

            # SLIST-010: terminal listing delegates to the same application result.
            terminal = TerminalApplication(
                config_path=config_path,
                session_root=session_root,
                agent_app=application,
            )
            assert terminal.list_sessions_metadata() == first

            # SLIST-001, SLIST-007: configured filters run before the limit.
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

            # SLIST-009: an unchanged revision reuses the same summary result.
            second_response = client.get("/sessions")
            assert second_response.json() == first_response.json()

            # SLIST-009: a changed filesystem revision invalidates that result.
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
# - SLIST-016: Asserts complete-first ordering, conservative filters, and limit-last behavior.
# - SLIST-017: Leaves one bounded background worker to finish the simulated hydration.
# - SLIST-020: Exercises the production HTTP route without any client-specific scan protocol.
@pytest.mark.integration
def test_delayed_session_content_returns_all_http_entries_then_converges(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify bounded listing when file attributes and content arrive separately.

    Setup:
        Store three sessions with descending modification times and configure a
        50 ms foreground interval with one resolver worker. Delay attribute
        enumeration by 60 ms, let the newest session load immediately, block
        the middle session, and leave the oldest session queued.

    Requirement assertions:
        SLIST-012 is asserted inside ``delayed_load`` and by the enumeration
        event checks: no content load begins before enumeration finishes.
        SLIST-015 is asserted by the elapsed-time bounds and ``load_order``:
        enumeration time is outside the foreground interval and work starts
        newest first before continuing in the background.
        SLIST-011, SLIST-013, and SLIST-020 are asserted by the first HTTP
        response: it retains the normal envelope and summary shape, includes
        all three IDs, and exposes no resolver-state field.
        SLIST-016 is asserted by the complete/placeholder order and by the
        filtered, limited result that conservatively retains the blocked item.
        SLIST-017 is asserted by the single-worker load sequence and eventual
        completion after the hydration gate is released.
    """

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
        # SLIST-012: content access is forbidden until enumeration completes.
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
            # SLIST-012, SLIST-015: enumeration precedes the bounded content wait.
            started = time.monotonic()
            response = client.get("/sessions")
            elapsed = time.monotonic() - started

            assert enumeration_finished.is_set()
            assert hydration_started.is_set()
            assert elapsed >= metadata_delay + (foreground_timeout * 0.7)
            assert elapsed < metadata_delay + foreground_timeout + 0.35

            # SLIST-011, SLIST-013, SLIST-016, SLIST-020: all entries use one shape.
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

            # SLIST-016: unresolved filter data is retained and limit is last.
            filtered_and_limited = application.list_session_summaries(
                filter_values={"session_status": ["done"]},
                apply_filter_defaults=True,
                limit=2,
            )
            assert [item["session_id"] for item in filtered_and_limited] == [
                "newest",
                "middle-blocked",
            ]

            # SLIST-015, SLIST-017: queued content completes in mtime order.
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
# - SLIST-009: Confirms application save, external revision, and delete invalidation paths.
# - SLIST-014: Restarts AgentApplication and lists unchanged sessions with zero content loads.
# - SLIST-018: Corrupts only derived state, then verifies safe rebuild and source preservation.
# - SLIST-019: Converges persistent summaries after save, external edit, and deletion.
@pytest.mark.integration
def test_persistent_summaries_survive_restart_and_follow_source_mutations(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify persistent reuse, source invalidation, and cache recovery.

    Setup:
        Populate the persistent summary cache from two filesystem sessions,
        close the first application, and open a second application over the
        same configuration and session root. Count every session-content load.
        Then update one session through the application, edit its JSON file
        externally, delete it, close the application, and corrupt the SQLite
        cache before opening a third application.

    Requirement assertions:
        SLIST-014 is asserted when the second application returns both cached
        previews while ``load_calls`` remains empty.
        SLIST-009 and SLIST-019 are asserted by the targeted load after
        ``save_session``, the externally edited preview, and the deleted ID's
        absence from the next collection.
        SLIST-018 is asserted when the third application reconstructs the
        survivor summary, leaves its source JSON file intact, and quarantines
        the corrupt derived database.
    """

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
        # Setup for SLIST-014: populate complete persistent summaries.
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
            # SLIST-014: unchanged summaries survive restart without content reads.
            warm = _session_by_id(client.get("/sessions"))
            assert warm["mutable"]["preview"] == "original"
            assert load_calls == []

            # SLIST-009, SLIST-019: application save invalidates only its session.
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

            # SLIST-009, SLIST-019: an external revision replaces cached content.
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

            # SLIST-009, SLIST-019: deletion removes source and derived membership.
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
            # SLIST-018: corrupt derived state is quarantined and rebuilt.
            rebuilt = _session_by_id(client.get("/sessions"))
            assert rebuilt["survivor"]["preview"] == "survives cache corruption"
            assert (session_root / "survivor.json").is_file()
            assert list(cache_root.glob("*.corrupt-*"))
    finally:
        third_application.close()


# Requirements:
# - SLIST-013: Keeps the session present while two concurrent HTTP requests await hydration.
# - SLIST-015: Automatically resolves the newest externally changed revision in background.
# - SLIST-017: Coalesces concurrent HTTP calls and cooperatively closes a blocked resolver.
# - SLIST-019: Discards stale in-flight content and publishes only the external revision.
# - SLIST-020: Preserves the ordinary HTTP response throughout concurrency and shutdown.
@pytest.mark.integration
def test_concurrent_http_hydration_discards_stale_work_and_stops_workers(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Verify coalescing, revision replacement, and resolver shutdown.

    Setup:
        Disable persistence, configure one worker and a 40 ms foreground
        interval, and store one session. Two HTTP threads list concurrently
        while the first content load is blocked after reading the old revision.
        The source file is then edited twice: once to supersede the in-flight
        result and once to start another blocked load during application close.

    Requirement assertions:
        SLIST-013, SLIST-017, and SLIST-020 are asserted when both concurrent
        HTTP responses contain the session as a normal placeholder while
        ``load_count`` remains one.
        SLIST-015 and SLIST-019 are asserted when releasing the stale load
        triggers one new load and only the externally updated preview appears.
        SLIST-017 and SLIST-020 are asserted when close returns during the
        third blocked load and every implementation-owned worker subsequently
        terminates.
    """

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

            # SLIST-013, SLIST-017, SLIST-020: two requests share one load.
            assert len(responses) == 2
            assert load_count == 1
            for response in responses:
                by_id = _session_by_id(response)
                assert by_id["changing"]["preview"] == ""

            # SLIST-015, SLIST-019: change the source while old work is in flight.
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

            # SLIST-015, SLIST-019: stale output is discarded and current data wins.
            release_first_load.set()
            deadline = time.monotonic() + 3.0
            current: dict[str, dict[str, Any]] = {}
            while time.monotonic() < deadline:
                current = _session_by_id(client.get("/sessions"))
                if current["changing"]["preview"] == "current external content":
                    break
            assert current["changing"]["preview"] == "current external content"
            assert load_count == 2

            # SLIST-017, SLIST-020: close while the replacement load is blocked.
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
    # SLIST-017: every resolver worker terminates after the blocked read returns.
    assert all(not worker.is_alive() for worker in workers)
