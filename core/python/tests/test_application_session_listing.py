from __future__ import annotations

import json
import os
from pathlib import Path
import threading
import time
from typing import Any, Dict, List

import pytest

from agent_app.application_future import AgentApplication
from agent_app.session_listing import (
    SessionListService,
    derive_session_list_presentation,
    resolve_session_list_path,
)
from agent_app.sessions import FilesystemSessionStore, SessionStoreRecord
from agent_core import AgentCore, Message, Session

from .dummy_provider import DummyProvider  # noqa: F401
from .fixtures.session_listing_app_plugin import (  # noqa: F401
    SessionListingFixturePlugin,
    SessionListingSecondFixturePlugin,
)


_CONTRACT_CASES_PATH = (
    Path(__file__).resolve().parents[3]
    / "test"
    / "fixture"
    / "session-list"
    / "v1"
    / "contract-cases.json"
)
_OPEN_APPLICATIONS: List[AgentApplication] = []


@pytest.fixture(autouse=True)
def _close_test_applications() -> Any:
    yield
    while _OPEN_APPLICATIONS:
        _OPEN_APPLICATIONS.pop().close()


def _new_application(config_path: Path, root: Path) -> AgentApplication:
    app = AgentApplication(config_path, root, core_factory=AgentCore)
    _OPEN_APPLICATIONS.append(app)
    return app


def _make_config(
    tmp_path: Path,
    *,
    with_listing_plugin: bool = True,
    with_second_listing_plugin: bool = True,
) -> Path:
    plugins = ["tests.dummy_provider.DummyProvider"]
    if with_listing_plugin:
        plugins.append("tests.fixtures.session_listing_app_plugin.SessionListingFixturePlugin")
        if with_second_listing_plugin:
            plugins.append(
                "tests.fixtures.session_listing_app_plugin.SessionListingSecondFixturePlugin"
            )
    config = {
        "providers": {
            "dummy": {
                "provider": "dummy_provider",
                "model": "test-model",
            }
        },
        "plugins": plugins,
        "agents": {"default": {"provider": "dummy"}},
    }
    path = tmp_path / ("listing_config.json" if with_listing_plugin else "plain_config.json")
    path.write_text(json.dumps(config), encoding="utf-8")
    return path


def _store_session(
    app: AgentApplication,
    *,
    session_id: str,
    content: str,
    metadata: Dict[str, Any],
) -> Session:
    session = Session(
        session_id=session_id,
        messages=(
            Message(role="system", content="system"),
            Message(role="user", content=content),
        ),
        metadata={"agent_id": "default", **metadata},
    )
    return app.save_session(session)


# Requirements: SLIST-002, SLIST-012
def test_filesystem_session_store_enumerates_opaque_records(tmp_path: Path) -> None:
    root = tmp_path / "sessions"
    store = FilesystemSessionStore(root, AgentCore())
    session = Session(session_id="opaque-id", messages=(), metadata={})
    store.save(session)

    records = store.list_records()

    assert len(records) == 1
    assert records[0].session_id == "opaque-id"
    assert isinstance(records[0].modified, float)
    assert not hasattr(records[0], "path")
    assert store.get_record("opaque-id") == records[0]
    assert store.get_record("missing") is None

    first_revision = records[0].revision
    path = root / "opaque-id.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["metadata"] = {"changed": True}
    path.write_text(json.dumps(raw), encoding="utf-8")
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))

    changed = store.get_record("opaque-id")
    assert changed is not None
    assert changed.revision != first_revision


# Requirements: SLIST-001, SLIST-003, SLIST-004, SLIST-005, SLIST-006, SLIST-008
def test_agent_application_builds_shared_summaries_and_plugin_order(
    tmp_path: Path,
) -> None:
    config_path = _make_config(tmp_path)
    root = tmp_path / "sessions"
    app = _new_application(config_path, root)

    _store_session(
        app,
        session_id="a-session",
        content="first preview",
        metadata={
            "title": "Alpha",
            "subtitle": "One",
            "bucket": 0,
            "sort_name": "a",
            "native_messages": [{"large": "private"}],
        },
    )
    _store_session(
        app,
        session_id="b-session",
        content="second preview",
        metadata={
            "bucket": 0,
            "sort_name": "z",
            "fail_list_action": True,
            "contribute_reserved_key": True,
            "contribute_invalid_order": True,
            "second_rank": 0,
        },
    )
    _store_session(
        app,
        session_id="c-session",
        content="third preview",
        metadata={"title": "", "bucket": 1, "sort_name": "x"},
    )

    summaries = app.list_session_summaries()

    assert [item["session_id"] for item in summaries] == [
        "b-session",
        "a-session",
        "c-session",
    ]
    by_id = {item["session_id"]: item for item in summaries}
    assert by_id["a-session"]["preview"] == "first preview"
    assert "native_messages" not in by_id["a-session"]["metadata"]
    assert by_id["a-session"]["message_count"] == 2
    assert by_id["a-session"]["after_failure_action"] is True
    assert by_id["a-session"]["presentation"] == {
        "title": "Alpha",
        "subtitle": "One",
        "meta": "2 messages",
    }
    assert by_id["b-session"]["preview"] == "second preview"
    assert by_id["b-session"]["presentation"]["title"] == "second preview"
    assert "after_failure_action" not in by_id["b-session"]
    assert by_id["c-session"]["presentation"]["title"] == "third preview"
    assert "pinned" not in by_id["a-session"]

    diagnostic_codes = {diagnostic["code"] for diagnostic in app.get_session_list_diagnostics()}
    assert "session_list_action_failed" in diagnostic_codes
    assert "invalid_session_list_field_result" in diagnostic_codes
    assert "invalid_session_list_order_spec" in diagnostic_codes


# Requirements: SLIST-004, SLIST-005
def test_equal_priority_order_uses_plugin_configuration_order(
    tmp_path: Path,
) -> None:
    config_path = _make_config(tmp_path)
    root = tmp_path / "sessions"
    app = _new_application(config_path, root)
    _store_session(
        app,
        session_id="first-plugin-wins",
        content="first",
        metadata={
            "bucket": 0,
            "sort_name": "z",
            "second_rank": 1,
        },
    )
    _store_session(
        app,
        session_id="second-plugin-would-win",
        content="second",
        metadata={
            "bucket": 0,
            "sort_name": "a",
            "second_rank": 0,
        },
    )

    summaries = app.list_session_summaries()

    assert [summary["session_id"] for summary in summaries] == [
        "first-plugin-wins",
        "second-plugin-would-win",
    ]


# Requirement: SLIST-005
def test_fallback_order_is_modified_descending_only(tmp_path: Path) -> None:
    config_path = _make_config(tmp_path, with_listing_plugin=False)
    root = tmp_path / "sessions"
    app = _new_application(config_path, root)

    _store_session(
        app,
        session_id="new-unpinned",
        content="new",
        metadata={"pinned": False},
    )
    _store_session(
        app,
        session_id="old-pinned",
        content="old",
        metadata={"pinned": True},
    )
    old_path = root / "old-pinned.json"
    new_path = root / "new-unpinned.json"
    now_ns = max(old_path.stat().st_mtime_ns, new_path.stat().st_mtime_ns)
    os.utime(old_path, ns=(now_ns - 10_000_000, now_ns - 10_000_000))
    os.utime(new_path, ns=(now_ns, now_ns))

    summaries = app.list_session_summaries()

    assert [item["session_id"] for item in summaries] == [
        "new-unpinned",
        "old-pinned",
    ]
    assert all("pinned" not in item for item in summaries)


# Requirements: SLIST-005, SLIST-008
def test_invalid_plugin_order_falls_back_to_modified_descending(
    tmp_path: Path,
) -> None:
    config_path = _make_config(tmp_path, with_second_listing_plugin=False)
    root = tmp_path / "sessions"
    app = _new_application(config_path, root)
    _store_session(
        app,
        session_id="older",
        content="older",
        metadata={"only_invalid_order": True},
    )
    _store_session(
        app,
        session_id="newer",
        content="newer",
        metadata={"only_invalid_order": True},
    )
    old_path = root / "older.json"
    new_path = root / "newer.json"
    now_ns = max(old_path.stat().st_mtime_ns, new_path.stat().st_mtime_ns)
    os.utime(old_path, ns=(now_ns - 10_000_000, now_ns - 10_000_000))
    os.utime(new_path, ns=(now_ns, now_ns))

    summaries = app.list_session_summaries()

    assert [summary["session_id"] for summary in summaries] == ["newer", "older"]
    assert any(
        diagnostic["code"] == "invalid_session_list_order_spec"
        for diagnostic in app.get_session_list_diagnostics()
    )


# Requirements: SLIST-009, SLIST-014, SLIST-019
def test_summary_cache_persists_across_applications_and_invalidates_on_save(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    config_path = _make_config(tmp_path, with_listing_plugin=False)
    root = tmp_path / "sessions"
    app = _new_application(config_path, root)
    _store_session(
        app,
        session_id="cached",
        content="before",
        metadata={},
    )

    store = app._session_store  # type: ignore[attr-defined]
    original_load = store.load
    load_calls: List[str] = []

    def counting_load(session_id: str, *, snapshot_id: str | None = None) -> Any:
        load_calls.append(session_id)
        return original_load(session_id, snapshot_id=snapshot_id)

    monkeypatch.setattr(store, "load", counting_load)
    assert app.list_session_summaries()[0]["preview"] == "before"
    assert app.list_session_summaries()[0]["preview"] == "before"
    assert load_calls == ["cached"]

    stored = app.load_live_session_record("cached")
    assert stored is not None
    updated = Session(
        session_id=stored.session_id,
        messages=(Message(role="user", content="after"),),
        metadata=stored.metadata,
    )
    app.save_session(updated)
    assert app.list_session_summaries()[0]["preview"] == "after"
    assert load_calls.count("cached") >= 3  # save reload plus summary rebuild

    second_app = _new_application(config_path, root)
    second_store = second_app._session_store  # type: ignore[attr-defined]
    second_original_load = second_store.load
    second_calls: List[str] = []

    def second_counting_load(session_id: str, *, snapshot_id: str | None = None) -> Any:
        second_calls.append(session_id)
        return second_original_load(session_id, snapshot_id=snapshot_id)

    monkeypatch.setattr(second_store, "load", second_counting_load)
    assert second_app.list_session_summaries()[0]["preview"] == "after"
    assert second_calls == []


class _DelayedSessionStore:
    def __init__(self) -> None:
        self.release_older = threading.Event()
        self.load_order: List[str] = []
        self.records = [
            SessionStoreRecord(
                session_id="older",
                modified=1.0,
                revision=("older", 1),
                accessed=3.0,
                created=1.0,
                size=200,
            ),
            SessionStoreRecord(
                session_id="newer",
                modified=2.0,
                revision=("newer", 1),
                accessed=4.0,
                created=2.0,
                size=100,
            ),
        ]

    def list_records(self) -> List[SessionStoreRecord]:
        return self.records

    def get_record(self, session_id: str) -> SessionStoreRecord | None:
        return next(
            (record for record in self.records if record.session_id == session_id),
            None,
        )

    def load(
        self,
        session_id: str,
        *,
        snapshot_id: str | None = None,
    ) -> Session | None:
        _ = snapshot_id
        self.load_order.append(session_id)
        if session_id == "older":
            assert self.release_older.wait(timeout=2.0)
        return Session(
            session_id=session_id,
            messages=[Message(role="user", content=f"{session_id} preview")],
            metadata={},
        )

    def save(self, session: Session) -> None:
        raise AssertionError("save is not used by this test")

    def delete(self, session_id: str) -> None:
        raise AssertionError("delete is not used by this test")


# Requirements: SLIST-012, SLIST-013, SLIST-015, SLIST-016
def test_bounded_listing_returns_complete_prefix_and_placeholder_suffix() -> None:
    store = _DelayedSessionStore()
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
                        "foreground_timeout_seconds": 0.05,
                        "worker_count": 1,
                    }
                }
            }
        },
    )

    started = time.monotonic()
    first = service.list_session_summaries()
    elapsed = time.monotonic() - started

    assert elapsed < 0.5
    assert [summary["session_id"] for summary in first] == ["newer", "older"]
    assert first[0]["preview"] == "newer preview"
    assert first[1] == {
        "session_id": "older",
        "modified": 1.0,
        "preview": "",
        "metadata": {},
        "presentation": {
            "title": "Session older",
            "subtitle": None,
            "meta": None,
        },
    }
    assert store.load_order == ["newer", "older"]

    store.release_older.set()
    deadline = time.monotonic() + 2.0
    completed: List[Dict[str, Any]] = []
    while time.monotonic() < deadline:
        completed = service.list_session_summaries()
        if all(summary["preview"] for summary in completed):
            break
    service._shutdown()

    assert [summary["preview"] for summary in completed] == [
        "newer preview",
        "older preview",
    ]


# Requirements: SLIST-012, SLIST-013
def test_metadata_placeholder_builder_does_not_load_session_content() -> None:
    record = SessionStoreRecord(
        session_id="metadata-only",
        modified=5.0,
        revision=("metadata-only", 1),
        accessed=6.0,
        created=4.0,
        size=123,
    )

    summary = SessionListService._build_metadata_summary(
        record=record,
        fields=(),
    )

    assert summary == {
        "session_id": "metadata-only",
        "modified": 5.0,
        "preview": "",
        "metadata": {},
        "presentation": {
            "title": "Session metadata",
            "subtitle": None,
            "meta": None,
        },
    }


class _OneBlockingSessionStore:
    def __init__(self) -> None:
        self.started = threading.Event()
        self.release = threading.Event()
        self.finished = threading.Event()
        self.load_calls = 0
        self._lock = threading.Lock()
        self.record = SessionStoreRecord(
            session_id="blocked",
            modified=1.0,
            revision=("blocked", 1),
        )

    def list_records(self) -> List[SessionStoreRecord]:
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
        with self._lock:
            self.load_calls += 1
        self.started.set()
        assert self.release.wait(timeout=2.0)
        self.finished.set()
        return Session(
            session_id=session_id,
            messages=[Message(role="user", content="complete")],
            metadata={},
        )

    def save(self, session: Session) -> None:
        raise AssertionError("save is not used by this test")

    def delete(self, session_id: str) -> None:
        raise AssertionError("delete is not used by this test")


def _blocking_service(
    store: _OneBlockingSessionStore,
    *,
    execute_action: Any = None,
    list_actions: Any = None,
) -> SessionListService:
    return SessionListService(
        store=store,
        list_actions=list_actions or (lambda: []),
        list_ui_elements=lambda: [],
        execute_action=execute_action or (lambda *_args, **_kwargs: {}),
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


# Requirement: SLIST-017
def test_concurrent_lists_share_one_inflight_load() -> None:
    store = _OneBlockingSessionStore()
    service = _blocking_service(store)
    barrier = threading.Barrier(3)
    results: List[List[Dict[str, Any]]] = []

    def list_sessions() -> None:
        barrier.wait()
        results.append(service.list_session_summaries())

    threads = [
        threading.Thread(target=list_sessions),
        threading.Thread(target=list_sessions),
    ]
    for thread in threads:
        thread.start()
    barrier.wait()
    assert store.started.wait(timeout=1.0)
    for thread in threads:
        thread.join(timeout=1.0)

    assert len(results) == 2
    assert store.load_calls == 1
    assert all(result[0]["preview"] == "" for result in results)

    store.release.set()
    assert store.finished.wait(timeout=1.0)
    service._shutdown()


# Requirement: SLIST-017
def test_shutdown_discards_blocked_work_before_plugin_enrichment() -> None:
    store = _OneBlockingSessionStore()
    action_calls: List[str] = []
    service = _blocking_service(
        store,
        list_actions=lambda: [
            {
                "plugin": "fixture",
                "id": "enrich",
                "trigger": "session_list",
                "inputs": {"session": {"required": True}},
            }
        ],
        execute_action=lambda _plugin, action, _params, _context: (
            action_calls.append(action) or {}
        ),
    )

    summaries = service.list_session_summaries()
    assert summaries[0]["preview"] == ""
    assert store.started.is_set()

    service._shutdown()
    store.release.set()
    assert store.finished.wait(timeout=1.0)

    deadline = time.monotonic() + 1.0
    while time.monotonic() < deadline:
        if all(not worker.is_alive() for worker in service._resolver._workers):
            break
        time.sleep(0.01)

    assert action_calls == []
    assert all(not worker.is_alive() for worker in service._resolver._workers)


class _ImmediateSessionStore:
    def __init__(self) -> None:
        self.load_calls = 0
        self.record = SessionStoreRecord(
            session_id="immediate",
            modified=1.0,
            revision=("immediate", 1),
        )

    def list_records(self) -> List[SessionStoreRecord]:
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
        self.load_calls += 1
        return Session(
            session_id=session_id,
            messages=[Message(role="user", content="persisted")],
            metadata={},
        )

    def save(self, session: Session) -> None:
        raise AssertionError("save is not used by this test")

    def delete(self, session_id: str) -> None:
        raise AssertionError("delete is not used by this test")


# Requirements: SLIST-011, SLIST-014, SLIST-018
def test_implementation_configuration_controls_persistent_reuse(
    tmp_path: Path,
) -> None:
    cache_directory = tmp_path / "derived"
    application_config = {
        "application": {
            "cached_background_session_list": {
                "foreground_timeout_seconds": 1.0,
                "persistent_cache_enabled": True,
                "local_cache_directory": str(cache_directory),
            }
        }
    }

    def new_service(store: _ImmediateSessionStore) -> SessionListService:
        return SessionListService(
            store=store,
            list_actions=lambda: [],
            list_ui_elements=lambda: [],
            execute_action=lambda *_args, **_kwargs: {},
            logger=None,
            context={
                "application_config": application_config,
                "session_store_identity": "configured-store",
            },
        )

    first_store = _ImmediateSessionStore()
    first_service = new_service(first_store)
    assert first_service.list_session_summaries()[0]["preview"] == "persisted"
    first_service._shutdown()
    assert first_store.load_calls == 1
    assert list(cache_directory.glob("*.sqlite3"))

    second_store = _ImmediateSessionStore()
    second_service = new_service(second_store)
    assert second_service.list_session_summaries()[0]["preview"] == "persisted"
    second_service._shutdown()
    assert second_store.load_calls == 0

    application_config["application"]["cached_background_session_list"][
        "persistent_cache_enabled"
    ] = False
    uncached_store = _ImmediateSessionStore()
    uncached_service = new_service(uncached_store)
    assert uncached_service.list_session_summaries()[0]["preview"] == "persisted"
    uncached_service._shutdown()
    assert uncached_store.load_calls == 1


class _ChangingBlockedSessionStore(_OneBlockingSessionStore):
    def __init__(self) -> None:
        super().__init__()
        self.content = "old"

    def load(
        self,
        session_id: str,
        *,
        snapshot_id: str | None = None,
    ) -> Session | None:
        _ = snapshot_id
        with self._lock:
            self.load_calls += 1
            content = self.content
        self.started.set()
        if content == "old":
            assert self.release.wait(timeout=2.0)
        self.finished.set()
        return Session(
            session_id=session_id,
            messages=[Message(role="user", content=content)],
            metadata={},
        )


# Requirements: SLIST-015, SLIST-019
def test_invalidated_blocked_result_cannot_replace_newer_revision() -> None:
    store = _ChangingBlockedSessionStore()
    service = _blocking_service(store)

    assert service.list_session_summaries()[0]["preview"] == ""
    assert store.started.is_set()

    store.record = SessionStoreRecord(
        session_id="blocked",
        modified=2.0,
        revision=("blocked", 2),
    )
    store.content = "new"
    service.invalidate("blocked")

    assert service.list_session_summaries()[0]["preview"] == ""
    store.release.set()

    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline:
        if store.load_calls == 2:
            break
        time.sleep(0.01)
    summaries = service.list_session_summaries()
    service._shutdown()

    assert summaries[0]["preview"] == "new"
    assert store.load_calls == 2


# Requirements: SLIST-008, SLIST-009, SLIST-019
def test_external_change_and_malformed_record_bypass_stale_summary(
    tmp_path: Path,
) -> None:
    config_path = _make_config(tmp_path, with_listing_plugin=False)
    root = tmp_path / "sessions"
    app = _new_application(config_path, root)
    _store_session(
        app,
        session_id="external",
        content="before",
        metadata={},
    )
    assert app.get_session_summary("external")["preview"] == "before"

    path = root / "external.json"
    raw = json.loads(path.read_text(encoding="utf-8"))
    raw["messages"][0]["content"] = "changed system"
    raw["messages"][1]["content"] = "after external write"
    path.write_text(json.dumps(raw), encoding="utf-8")
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000))

    assert app.get_session_summary("external")["preview"] == "after external write"

    malformed_path = root / "malformed.json"
    malformed_path.write_text("{not json", encoding="utf-8")
    summaries = app.list_session_summaries()
    malformed = next(item for item in summaries if item["session_id"] == "malformed")
    assert malformed["metadata"] == {}
    assert malformed["preview"] == ""
    assert malformed["presentation"]["title"] == "Session malforme"
    assert any(
        diagnostic["code"] == "session_summary_load_failed"
        for diagnostic in app.get_session_list_diagnostics()
    )


# Requirements: SLIST-001, SLIST-007, SLIST-016
def test_filter_seam_runs_after_ordering_and_before_limit(tmp_path: Path) -> None:
    config_path = _make_config(tmp_path)
    root = tmp_path / "sessions"
    app = _new_application(config_path, root)
    _store_session(
        app,
        session_id="first",
        content="first",
        metadata={"bucket": 0, "sort_name": "z"},
    )
    _store_session(
        app,
        session_id="second",
        content="second",
        metadata={"bucket": 0, "sort_name": "a"},
    )
    _store_session(
        app,
        session_id="third",
        content="third",
        metadata={"bucket": 1, "sort_name": "x"},
    )

    calls: List[Dict[str, Any]] = []

    def evaluator(
        summaries: List[Dict[str, Any]],
        *,
        ui_elements: Any,
        filter_values: Any,
        apply_filter_defaults: bool,
    ) -> List[Dict[str, Any]]:
        calls.append(
            {
                "ids": [item["session_id"] for item in summaries],
                "filter_values": filter_values,
                "apply_filter_defaults": apply_filter_defaults,
                "ui_elements": ui_elements,
            }
        )
        return [item for item in summaries if item["session_id"] in {"second", "third"}]

    app.set_session_list_filter_evaluator(evaluator)
    result = app.list_session_summaries(
        filter_values={"fixture": "value"},
        apply_filter_defaults=True,
        limit=1,
    )

    assert calls[0]["ids"] == ["first", "second", "third"]
    assert calls[0]["filter_values"] == {"fixture": "value"}
    assert calls[0]["apply_filter_defaults"] is True
    assert calls[0]["ui_elements"]
    assert [item["session_id"] for item in result] == ["second"]


# Requirements: SLIST-001, SLIST-007
def test_exact_summary_is_independent_of_filters_and_missing_id_errors(
    tmp_path: Path,
) -> None:
    config_path = _make_config(tmp_path, with_listing_plugin=False)
    root = tmp_path / "sessions"
    app = _new_application(config_path, root)
    _store_session(
        app,
        session_id="exact",
        content="exact preview",
        metadata={},
    )
    app.set_session_list_filter_evaluator(lambda summaries, **kwargs: [])  # type: ignore[arg-type]

    assert app.list_session_summaries(filter_values={"hide": True}) == []
    assert app.get_session_summary("exact")["preview"] == "exact preview"

    try:
        app.get_session_summary("missing")
    except KeyError as exc:
        assert "missing" in str(exc)
    else:  # pragma: no cover - assertion guard
        raise AssertionError("missing exact summary should raise KeyError")


# Requirement: SLIST-006
def test_python_uses_shared_path_and_presentation_contract_cases() -> None:
    fixtures = json.loads(_CONTRACT_CASES_PATH.read_text(encoding="utf-8"))

    for case in fixtures["path_cases"]:
        resolved = resolve_session_list_path(case["root"], case["path"])
        assert resolved.found is case["expected"]["found"], case["name"]
        if resolved.found:
            assert resolved.value == case["expected"]["value"], case["name"]

    for case in fixtures["presentation_cases"]:
        diagnostics: List[Any] = []
        fields = SessionListService._normalize_fields(  # type: ignore[attr-defined]
            case["fields"],
            diagnostics,
        )
        assert diagnostics == [], case["name"]
        assert derive_session_list_presentation(case["summary"], fields) == case["expected"], case[
            "name"
        ]
