"""Unit tests for the duration tracking SQLite store."""

from __future__ import annotations

import itertools
import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, cast

import pytest

from duration_tracking_plugins import duration_store


_stamp_seq = itertools.count()


def _record(db_path: Path, **overrides):
    # Each call gets unique measurement stamps by default so tests that
    # record several rows behave like distinct LLM rounds; tests for
    # the dedup contract pass explicit identical stamps.
    index = next(_stamp_seq)
    params: Dict[str, Any] = {
        "session_id": "s1",
        "working_directory": "/tmp/ws",
        "model": "m",
        "request_id": None,
        "duration_ms": 1200,
        "duration_started_at": f"2026-01-01T00:00:00.{index:06d}+00:00",
        "duration_finished_at": f"2026-01-01T00:00:01.{index:06d}+00:00",
    }
    params.update(overrides)
    return duration_store.record_request_duration(db_path, **params)


def _table_columns(db_path: Path, table: str) -> set:
    conn = sqlite3.connect(str(db_path))
    try:
        return {row[1] for row in conn.execute(f"PRAGMA table_info({table})")}
    finally:
        conn.close()


def _table_indexes(db_path: Path, table: str) -> set:
    conn = sqlite3.connect(str(db_path))
    try:
        return {
            row[0]
            for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type = 'index'"
                f" AND tbl_name = '{table}'"
            )
        }
    finally:
        conn.close()


def _request_rows(db_path: Path) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute("SELECT * FROM duration_requests")]
    finally:
        conn.close()


def test_schema_creates_both_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    assert _record(db_path, request_id="r1") is True

    assert _table_columns(db_path, "duration_requests") == {
        "id",
        "time",
        "session_id",
        "working_directory",
        "model",
        "request_id",
        "duration_ms",
        "duration_started_at",
        "duration_finished_at",
    }
    # The tool table ships with the same schema so the tool-call recording
    # (subtask 025) needs no migration.
    assert _table_columns(db_path, "tool_durations") == {
        "id",
        "time",
        "session_id",
        "working_directory",
        "model",
        "request_id",
        "tool_call_id",
        "tool_name",
        "tool_plugin",
        "duration_ms",
        "duration_started_at",
        "duration_finished_at",
        "tool_error",
    }
    assert "idx_duration_requests_round" in _table_indexes(db_path, "duration_requests")
    assert "idx_tool_durations_call" in _table_indexes(db_path, "tool_durations")


def test_record_and_session_totals(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    assert _record(db_path, request_id="r1") is True
    assert _record(db_path, request_id="r2", duration_ms=300) is True

    totals = duration_store.session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    assert totals["request_count"] == 2
    assert totals["total_ms"] == 1500


def test_record_dedupes_by_round_stamps(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    stamps = {
        "duration_started_at": "2026-01-01T00:00:00.000000+00:00",
        "duration_finished_at": "2026-01-01T00:00:01.000000+00:00",
    }
    assert _record(db_path, request_id="r1", **stamps) is True
    # Same measurement stamps mean the same LLM round (re-finalize or
    # rebuild path) and must not duplicate, whatever the request id.
    assert _record(db_path, request_id="r1", duration_ms=999, **stamps) is False
    assert _record(db_path, request_id="other-request", **stamps) is False

    totals = duration_store.session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    assert totals["request_count"] == 1
    assert totals["total_ms"] == 1200


def test_tool_loop_rounds_share_request_id_but_record_separately(
    tmp_path: Path,
) -> None:
    """Every LLM round of a tool-loop request gets its own row.

    Tool loops run one finalize per round under a single request id, so
    the request id alone must not dedup (the original bug froze session
    totals at the first round's snapshot).
    """

    db_path = tmp_path / "durations.sqlite3"

    assert (
        _record(
            db_path,
            request_id="shared",
            duration_ms=13933,
            duration_started_at="2026-09-24T08:00:16.404522+00:00",
            duration_finished_at="2026-09-24T08:00:30.337779+00:00",
        )
        is True
    )
    assert (
        _record(
            db_path,
            request_id="shared",
            duration_ms=5059,
            duration_started_at="2026-09-24T08:00:30.766194+00:00",
            duration_finished_at="2026-09-24T08:00:35.825752+00:00",
        )
        is True
    )
    assert (
        _record(
            db_path,
            request_id="shared",
            duration_ms=3317,
            duration_started_at="2026-09-24T08:00:36.422513+00:00",
            duration_finished_at="2026-09-24T08:00:39.739942+00:00",
        )
        is True
    )

    totals = duration_store.session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    assert totals["request_count"] == 3
    assert totals["total_ms"] == 13933 + 5059 + 3317


def test_record_without_stamps_does_not_dedup(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    assert (
        _record(
            db_path,
            request_id="r1",
            duration_started_at=None,
            duration_finished_at=None,
        )
        is True
    )
    assert (
        _record(
            db_path,
            request_id="r2",
            duration_started_at=None,
            duration_finished_at=None,
        )
        is True
    )

    totals = duration_store.session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    assert totals["request_count"] == 2


def test_schema_migrates_legacy_request_id_index(tmp_path: Path) -> None:
    """Databases created with the original global request-id index migrate.

    The legacy index recorded only the first LLM round of tool-loop
    requests; the first store call after the upgrade drops it and keys
    rounds by their measurement stamps, keeping existing rows.
    """

    db_path = tmp_path / "durations.sqlite3"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """
            CREATE TABLE duration_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                time TEXT NOT NULL,
                session_id TEXT,
                working_directory TEXT,
                model TEXT,
                request_id TEXT,
                duration_ms INTEGER,
                duration_started_at TEXT,
                duration_finished_at TEXT
            )
            """
        )
        conn.execute(
            "CREATE UNIQUE INDEX idx_duration_requests_request_id "
            "ON duration_requests(request_id) WHERE request_id IS NOT NULL"
        )
        conn.execute(
            "INSERT INTO duration_requests (time, session_id, working_directory, "
            "model, request_id, duration_ms, duration_started_at, duration_finished_at) "
            "VALUES ('2026-09-24T08:00:30.337779+00:00', 's1', '/tmp/ws', 'm', "
            "'legacy-1', 13933, '2026-09-24T08:00:16.404522+00:00', "
            "'2026-09-24T08:00:30.337779+00:00')"
        )
        conn.commit()
    finally:
        conn.close()

    # Any public store function migrates the schema in place.
    duration_store.session_totals(db_path, working_directory="/tmp/ws", session_id="s1")

    indexes = _table_indexes(db_path, "duration_requests")
    assert "idx_duration_requests_request_id" not in indexes
    assert "idx_duration_requests_round" in indexes

    # The legacy row survives and later rounds of the same request id
    # now record alongside it.
    assert (
        _record(
            db_path,
            request_id="legacy-1",
            duration_ms=5059,
            duration_started_at="2026-09-24T08:00:30.766194+00:00",
            duration_finished_at="2026-09-24T08:00:35.825752+00:00",
        )
        is True
    )
    totals = duration_store.session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    assert totals["request_count"] == 2
    assert totals["total_ms"] == 13933 + 5059


def test_session_totals_filter_by_workspace_and_session(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    assert _record(db_path, request_id="r1") is True
    assert _record(db_path, request_id="r2", session_id="s2") is True
    assert _record(db_path, request_id="r3", working_directory="/tmp/other") is True

    totals = duration_store.session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    assert totals["request_count"] == 1
    # The same session id in a different workspace stays separate.
    other = duration_store.session_totals(
        db_path, working_directory="/tmp/other", session_id="s1"
    )
    assert other["request_count"] == 1


def test_session_totals_zero_for_unknown_session(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    assert _record(db_path, request_id="r1") is True

    totals = duration_store.session_totals(
        db_path, working_directory="/tmp/ws", session_id="unknown"
    )
    assert totals["request_count"] == 0
    assert totals["total_ms"] == 0


def test_record_coerces_malformed_values(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    assert (
        _record(
            db_path,
            request_id="r1",
            duration_ms="not-a-number",
            duration_started_at=123,
            model=42,
        )
        is True
    )

    rows = _request_rows(db_path)
    assert len(rows) == 1
    assert rows[0]["duration_ms"] is None
    assert rows[0]["duration_started_at"] is None
    assert rows[0]["model"] is None
    assert rows[0]["session_id"] == "s1"
    assert rows[0]["working_directory"] == "/tmp/ws"


def test_row_time_uses_explicit_value(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    assert _record(db_path, request_id="r1", time="2026-01-01T00:00:01+00:00") is True
    rows = _request_rows(db_path)
    assert rows[0]["time"] == "2026-01-01T00:00:01+00:00"


def test_row_time_defaults_to_utcnow(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    before = duration_store.utcnow_iso()
    assert _record(db_path, request_id="r1") is True
    after = duration_store.utcnow_iso()
    rows = _request_rows(db_path)
    assert before <= rows[0]["time"] <= after


def test_top_sessions_and_projects(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    _record(db_path, request_id="r1", duration_ms=100)
    _record(db_path, request_id="r2", duration_ms=400)
    _record(
        db_path,
        request_id="r3",
        session_id="s2",
        working_directory="/tmp/other",
        duration_ms=1000,
    )

    sessions = duration_store.top_sessions(db_path)
    assert [entry["session_id"] for entry in sessions] == ["s2", "s1"]
    assert sessions[0]["working_directory"] == "/tmp/other"
    assert sessions[0]["request_count"] == 1
    assert sessions[0]["total_ms"] == 1000
    assert sessions[1]["request_count"] == 2
    assert sessions[1]["total_ms"] == 500

    projects = duration_store.top_projects(db_path)
    assert [entry["working_directory"] for entry in projects] == [
        "/tmp/other",
        "/tmp/ws",
    ]
    assert projects[0]["total_ms"] == 1000
    assert projects[1]["total_ms"] == 500
    assert projects[1]["request_count"] == 2


def test_top_sessions_skips_rows_without_workspace_or_session(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"

    _record(db_path, request_id="r1", session_id=None)
    _record(db_path, request_id="r2", working_directory=None)
    _record(db_path, request_id="r3")

    sessions = duration_store.top_sessions(db_path)
    assert [entry["session_id"] for entry in sessions] == ["s1"]

    projects = duration_store.top_projects(db_path)
    assert [entry["working_directory"] for entry in projects] == ["/tmp/ws"]


def test_top_sessions_limit(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    for index in range(12):
        _record(
            db_path,
            request_id=f"r{index}",
            session_id=f"s{index}",
            duration_ms=index,
        )

    assert len(duration_store.top_sessions(db_path)) == 10
    assert len(duration_store.top_sessions(db_path, limit=3)) == 3
    assert duration_store.top_sessions(db_path)[0]["session_id"] == "s11"
    assert duration_store.top_sessions(db_path, limit=0) == duration_store.top_sessions(
        db_path
    )


def test_overall_totals_cover_all_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    _record(db_path, request_id="r1", duration_ms=1200)
    _record(db_path, request_id="r2", duration_ms=300)
    _record(
        db_path,
        request_id="r3",
        session_id="s2",
        working_directory="/tmp/other",
        duration_ms=500,
    )
    _record_tool(db_path, tool_call_id="call_1")
    _record_tool(
        db_path,
        tool_call_id="call_2",
        session_id="s2",
        working_directory="/tmp/other",
        duration_ms=150,
    )

    totals = duration_store.overall_totals(db_path)
    assert totals == {
        "request_count": 3,
        "total_ms": 2000,
        "tool_call_count": 2,
        "tool_total_ms": 400,
    }


def test_overall_totals_empty_store(tmp_path: Path) -> None:
    totals = duration_store.overall_totals(tmp_path / "durations.sqlite3")
    assert totals == {
        "request_count": 0,
        "total_ms": 0,
        "tool_call_count": 0,
        "tool_total_ms": 0,
    }


def _csv_rows(csv_path: Path) -> List[Dict[str, Any]]:
    import csv as csv_module

    with open(csv_path, encoding="utf-8", newline="") as handle:
        return list(csv_module.DictReader(handle))


def _summary_csv_path(db_path: Path) -> Path:
    return db_path.with_name("duration-tracking-summary.csv")


def _record_and_summarize(db_path: Path, config=None, **overrides):
    params: Dict[str, Any] = {
        "session_id": "s1",
        "working_directory": "/tmp/ws",
        "model": "m",
        "request_id": None,
        "duration_ms": 1200,
    }
    params.update(overrides)
    recorded = duration_store.record_request_duration(db_path, **params)
    appended = duration_store.append_request_summary_csv(
        db_path,
        config,
        session_id=params["session_id"],
        working_directory=params["working_directory"],
        model=params["model"],
        duration_ms=params["duration_ms"],
        time="2026-01-01T00:00:01+00:00",
    )
    return recorded, appended


def test_summary_csv_appends_request_rows_with_rolling_totals(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"

    _record_and_summarize(db_path, request_id="r1", duration_ms=1200)
    _record_and_summarize(db_path, request_id="r2", duration_ms=300)

    rows = _csv_rows(_summary_csv_path(db_path))
    assert len(rows) == 2
    assert rows[0]["working_directory"] == "/tmp/ws"
    assert rows[0]["session_id"] == "s1"
    assert rows[0]["model"] == "m"
    assert rows[0]["time"] == "2026-01-01T00:00:01+00:00"
    assert float(rows[0]["duration"]) == pytest.approx(1200)
    assert float(rows[0]["session_total_duration"]) == pytest.approx(1200)
    assert float(rows[1]["duration"]) == pytest.approx(300)
    assert float(rows[1]["session_total_duration"]) == pytest.approx(1500)


def test_summary_csv_row_without_session_fields(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    duration_store.record_request_duration(db_path, request_id="r1", duration_ms=500)
    assert (
        duration_store.append_request_summary_csv(db_path, None, duration_ms=500)
        is True
    )

    rows = _csv_rows(_summary_csv_path(db_path))
    assert len(rows) == 1
    assert rows[0]["session_id"] == ""
    assert rows[0]["session_total_duration"] == ""
    assert float(rows[0]["duration"]) == pytest.approx(500)


def test_summary_csv_disabled_by_config(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    config = {"track_duration_tracking_summary_csv": False}

    duration_store.record_request_duration(db_path, request_id="r1", duration_ms=500)
    assert (
        duration_store.append_request_summary_csv(db_path, config, duration_ms=500)
        is False
    )
    assert not _summary_csv_path(db_path).exists()


def test_summary_csv_path_override(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    csv_path = tmp_path / "elsewhere" / "summary.csv"
    config = {"duration_tracking_summary_csv_path": str(csv_path)}

    duration_store.record_request_duration(
        db_path,
        request_id="r1",
        session_id="s1",
        working_directory="/tmp/ws",
        duration_ms=500,
    )
    assert (
        duration_store.append_request_summary_csv(
            db_path,
            config,
            session_id="s1",
            working_directory="/tmp/ws",
            duration_ms=500,
        )
        is True
    )
    assert len(_csv_rows(csv_path)) == 1


def test_summary_csv_best_effort_on_unwritable_path(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    config = {"duration_tracking_summary_csv_path": str(blocker / "summary.csv")}

    duration_store.record_request_duration(db_path, request_id="r1", duration_ms=500)
    assert (
        duration_store.append_request_summary_csv(db_path, config, duration_ms=500)
        is False
    )


def _record_tool(db_path: Path, **overrides):
    params: Dict[str, Any] = {
        "session_id": "s1",
        "working_directory": "/tmp/ws",
        "model": "m",
        "request_id": "req-1",
        "tool_call_id": "call_1",
        "tool_name": "read_file",
        "tool_plugin": "file_reader_tool",
        "duration_ms": 250,
        "duration_started_at": "2026-01-01T00:00:00+00:00",
        "duration_finished_at": "2026-01-01T00:00:00.250000+00:00",
    }
    params.update(overrides)
    return duration_store.record_tool_duration(db_path, **params)


def _tool_rows(db_path: Path) -> List[Dict[str, Any]]:
    duration_store.tool_session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        return [dict(row) for row in conn.execute("SELECT * FROM tool_durations")]
    finally:
        conn.close()


def test_record_tool_duration_and_tool_session_totals(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    assert _record_tool(db_path, tool_call_id="call_1") is True
    assert _record_tool(db_path, tool_call_id="call_2", duration_ms=300) is True

    totals = duration_store.tool_session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    assert totals == {"call_count": 2, "total_ms": 550}


def test_record_tool_duration_dedupes_on_composite_key(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    # Same tuple twice: the second is a duplicate.
    assert _record_tool(db_path) is True
    assert _record_tool(db_path, duration_ms=999) is False

    # The same call id in a different request records (providers may reuse
    # sequential call ids across requests).
    assert _record_tool(db_path, request_id="req-2") is True
    # The same call id in a different session records.
    assert _record_tool(db_path, session_id="s2") is True

    totals = duration_store.tool_session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    assert totals == {"call_count": 2, "total_ms": 500}


def test_record_tool_duration_without_call_id_does_not_dedup(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    assert _record_tool(db_path, tool_call_id=None) is True
    assert _record_tool(db_path, tool_call_id=None) is True

    totals = duration_store.tool_session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    assert totals == {"call_count": 2, "total_ms": 500}


def test_tool_session_totals_filter_by_workspace_and_session(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    _record_tool(db_path, tool_call_id="call_1")
    _record_tool(db_path, tool_call_id="call_2", session_id="s2")
    _record_tool(db_path, tool_call_id="call_3", working_directory="/tmp/other")

    totals = duration_store.tool_session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    assert totals == {"call_count": 1, "total_ms": 250}
    other = duration_store.tool_session_totals(
        db_path, working_directory="/tmp/other", session_id="s1"
    )
    assert other == {"call_count": 1, "total_ms": 250}


def test_tool_session_totals_zero_for_unknown_session(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    assert _record_tool(db_path) is True

    totals = duration_store.tool_session_totals(
        db_path, working_directory="/tmp/ws", session_id="unknown"
    )
    assert totals == {"call_count": 0, "total_ms": 0}


def test_record_tool_duration_coerces_malformed_values(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    assert (
        _record_tool(
            db_path,
            duration_ms="not-a-number",
            duration_started_at=123,
            tool_error=42,
        )
        is True
    )

    rows = _tool_rows(db_path)
    assert len(rows) == 1
    assert rows[0]["duration_ms"] is None
    assert rows[0]["duration_started_at"] is None
    assert rows[0]["tool_error"] is None
    assert rows[0]["tool_call_id"] == "call_1"


def test_record_tool_duration_row_time_and_error(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    assert (
        _record_tool(
            db_path,
            time="2026-01-01T00:00:00.250000+00:00",
            tool_error="inspect_call_failed",
        )
        is True
    )

    rows = _tool_rows(db_path)
    assert rows[0]["time"] == "2026-01-01T00:00:00.250000+00:00"
    assert rows[0]["tool_error"] == "inspect_call_failed"


def test_top_sessions_include_tool_columns(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    _record(db_path, request_id="r1", duration_ms=1000)
    _record_tool(db_path, tool_call_id="call_1")
    _record_tool(db_path, tool_call_id="call_2", duration_ms=300)
    _record(
        db_path,
        request_id="r2",
        session_id="s2",
        working_directory="/tmp/other",
        duration_ms=200,
    )

    sessions = duration_store.top_sessions(db_path)
    assert [entry["session_id"] for entry in sessions] == ["s1", "s2"]
    assert sessions[0]["total_ms"] == 1000
    assert sessions[0]["tool_total_ms"] == 550
    assert sessions[0]["tool_call_count"] == 2
    # Sessions without tool rows report zero tool columns.
    assert sessions[1]["tool_total_ms"] == 0
    assert sessions[1]["tool_call_count"] == 0


def test_top_projects_include_tool_columns(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    _record(db_path, request_id="r1", duration_ms=1000)
    _record_tool(db_path, tool_call_id="call_1")
    _record(
        db_path,
        request_id="r2",
        session_id="s2",
        working_directory="/tmp/other",
        duration_ms=200,
    )

    projects = duration_store.top_projects(db_path)
    assert [entry["working_directory"] for entry in projects] == [
        "/tmp/ws",
        "/tmp/other",
    ]
    assert projects[0]["tool_total_ms"] == 250
    assert projects[0]["tool_call_count"] == 1
    assert projects[1]["tool_total_ms"] == 0
    assert projects[1]["tool_call_count"] == 0


def test_resolve_duration_db_path_prefers_explicit_override(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CRYSTAL_DATA_DIR", str(tmp_path / "data"))
    override = tmp_path / "elsewhere" / "durations.sqlite3"
    assert (
        duration_store.resolve_duration_db_path(
            {"duration_tracking_db_path": str(override)}
        )
        == override
    )


def test_resolve_duration_db_path_follows_crystal_data_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CRYSTAL_DATA_DIR", str(tmp_path / "data"))
    assert duration_store.resolve_duration_db_path({}) == (
        tmp_path / "data" / "duration-tracking" / "duration-tracking.sqlite3"
    )


def test_resolve_duration_db_path_falls_back_to_cwd(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.delenv("CRYSTAL_DATA_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(os, "getcwd", lambda: str(tmp_path))
    assert duration_store.resolve_duration_db_path(None) == (
        tmp_path / "duration-tracking" / "duration-tracking.sqlite3"
    )


# --- Human time spans (subtask 030) ---
#
# Contract (user, 2026-09-24/25): the frontend computes durations and sends
# spans {session_id|null, from, to}; each batch carries a request id for
# retry dedup; no two stored rows ever overlap (first entry wins by end-time
# priority; same-session spans merge; session-bearing beats session-less).


def _z(hhmm: str) -> str:
    """Input timestamp form (device clock, Z-suffixed)."""

    return f"2026-09-25T{hhmm}:00Z"


def _ts(hhmm: str) -> str:
    """Canonical stored form for an input timestamp."""

    return f"2026-09-25T{hhmm}:00.000000+00:00"


def _minutes(hhmm: str) -> int:
    hours, mins = hhmm.split(":")
    return int(hours) * 60 + int(mins)


def _span(session_id, start: str, end: str, working_directory=None):
    span: Dict[str, Any] = {"session_id": session_id, "from": _z(start), "to": _z(end)}
    if working_directory is not None:
        span["working_directory"] = working_directory
    return span


def _record_spans(
    db_path: Path,
    spans: List[Any],
    *,
    request_id: str = "req-1",
    working_directory: Optional[str] = "/tmp/ws",
):
    return duration_store.record_human_time_spans(
        db_path,
        working_directory=working_directory,
        request_id=request_id,
        spans=spans,
    )


def _human_time_rows(db_path: Path) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in conn.execute(
                "SELECT session_id, working_directory, from_time, to_time,"
                " duration_ms, request_id FROM human_time_spans"
                " ORDER BY from_time, id"
            )
        ]
    finally:
        conn.close()


def _expected_span_row(
    session_id,
    start: str,
    end: str,
    *,
    request_id: str,
    working_directory: str = "/tmp/ws",
) -> Dict[str, Any]:
    return {
        "session_id": session_id,
        "working_directory": working_directory,
        "from_time": _ts(start),
        "to_time": _ts(end),
        "duration_ms": (_minutes(end) - _minutes(start)) * 60 * 1000,
        "request_id": request_id,
    }


def test_human_time_schema_creates_tables(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    result = _record_spans(db_path, [_span("s1", "08:00", "08:05")])
    assert result == {
        "recorded": 1,
        "merged": 0,
        "skipped": 0,
        "absorbed": 0,
        "duplicate": False,
    }
    assert _table_columns(db_path, "human_time_spans") == {
        "id",
        "session_id",
        "working_directory",
        "from_time",
        "to_time",
        "duration_ms",
        "request_id",
    }
    assert _table_columns(db_path, "human_time_requests") == {
        "request_id",
        "processed_at",
    }
    assert "idx_human_time_spans_session" in _table_indexes(db_path, "human_time_spans")


def test_human_time_spans_batch_and_totals(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    result = _record_spans(
        db_path,
        [
            _span("s1", "08:00", "08:05"),
            _span("s1", "08:10", "08:12"),
            _span(None, "09:00", "09:03"),
            _span("s2", "09:30", "09:31"),
        ],
    )
    assert result["recorded"] == 4
    assert duration_store.human_time_session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    ) == {"span_count": 2, "total_ms": 7 * 60 * 1000}
    assert duration_store.human_time_session_totals(
        db_path, working_directory="/tmp/ws", session_id="s2"
    ) == {"span_count": 1, "total_ms": 60 * 1000}
    assert duration_store.human_time_project_totals(
        db_path, working_directory="/tmp/ws"
    ) == {"span_count": 4, "total_ms": 11 * 60 * 1000}


def test_human_time_project_totals_include_session_less(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    _record_spans(
        db_path, [_span("s1", "08:00", "08:05"), _span(None, "09:00", "09:02")]
    )
    assert duration_store.human_time_project_totals(
        db_path, working_directory="/tmp/ws"
    ) == {"span_count": 2, "total_ms": 7 * 60 * 1000}
    # Session totals exclude the session-less row.
    assert duration_store.human_time_session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    ) == {"span_count": 1, "total_ms": 5 * 60 * 1000}


def test_human_time_report_aggregates_include_sessionless_time(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    batches = [
        (
            "/tmp/alpha",
            "alpha-batch",
            [
                _span("alpha-1", "08:00", "08:10"),
                _span(None, "08:20", "08:25"),
                _span("alpha-2", "08:30", "08:32"),
            ],
        ),
        (
            "/tmp/beta",
            "beta-batch",
            [
                _span("beta-1", "09:00", "09:08"),
                _span(None, "09:10", "09:11"),
            ],
        ),
        ("/tmp/gamma", "gamma-batch", [_span("gamma-1", "10:00", "10:03")]),
        ("/tmp/delta", "delta-batch", [_span("delta-1", "11:00", "11:02")]),
    ]
    for working_directory, request_id, spans in batches:
        result = _record_spans(
            db_path,
            spans,
            request_id=request_id,
            working_directory=working_directory,
        )
        assert result["skipped"] == 0

    assert duration_store.human_time_overall_totals(db_path) == {
        "span_count": 7,
        "total_ms": 31 * 60 * 1000,
        "sessionless_span_count": 2,
        "sessionless_ms": 6 * 60 * 1000,
    }

    sessions = duration_store.top_human_time_sessions(db_path, limit=10)
    assert [entry["session_id"] for entry in sessions] == [
        "alpha-1",
        "beta-1",
        "gamma-1",
        "alpha-2",
        "delta-1",
    ]
    assert sessions[0]["total_ms"] == 10 * 60 * 1000

    projects = duration_store.top_human_time_projects(db_path, limit=3)
    assert [entry["working_directory"] for entry in projects] == [
        "/tmp/alpha",
        "/tmp/beta",
        "/tmp/gamma",
    ]
    assert projects[0] == {
        "working_directory": "/tmp/alpha",
        "span_count": 3,
        "total_ms": 17 * 60 * 1000,
        "sessionless_span_count": 1,
        "sessionless_ms": 5 * 60 * 1000,
    }


def test_human_time_spans_request_id_dedup(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    _record_spans(db_path, [_span("s1", "08:00", "08:05")], request_id="r1")
    # A retried request (same id) is skipped without touching spans.
    result = _record_spans(db_path, [_span("s1", "08:20", "08:25")], request_id="r1")
    assert result == {
        "recorded": 0,
        "merged": 0,
        "skipped": 0,
        "absorbed": 0,
        "duplicate": True,
    }
    assert _human_time_rows(db_path) == [
        _expected_span_row("s1", "08:00", "08:05", request_id="r1")
    ]
    # A new request id applies.
    result = _record_spans(db_path, [_span("s1", "08:20", "08:25")], request_id="r2")
    assert result["duplicate"] is False
    assert result["recorded"] == 1
    assert len(_human_time_rows(db_path)) == 2


def test_human_time_overlap_default_first_entry_wins(tmp_path: Path) -> None:
    """The user's worked example: different sessions, the new span trims."""

    db_path = tmp_path / "durations.sqlite3"
    _record_spans(db_path, [_span("a", "08:14", "08:16")], request_id="r1")
    _record_spans(db_path, [_span("b", "08:18", "08:19")], request_id="r2")
    result = _record_spans(db_path, [_span("c", "08:15", "08:20")], request_id="r3")
    assert result == {
        "recorded": 1,
        "merged": 0,
        "skipped": 0,
        "absorbed": 0,
        "duplicate": False,
    }
    # The new span stores as two entries (8:16-8:18 and 8:19-8:20); the
    # existing entries keep their ranges.
    assert _human_time_rows(db_path) == [
        _expected_span_row("a", "08:14", "08:16", request_id="r1"),
        _expected_span_row("c", "08:16", "08:18", request_id="r3"),
        _expected_span_row("b", "08:18", "08:19", request_id="r2"),
        _expected_span_row("c", "08:19", "08:20", request_id="r3"),
    ]


def test_human_time_overlap_session_wins_session_less_merges_around(
    tmp_path: Path,
) -> None:
    """The user's worked example: only 8:18-8:19 has a session."""

    db_path = tmp_path / "durations.sqlite3"
    _record_spans(db_path, [_span(None, "08:14", "08:16")], request_id="r1")
    _record_spans(db_path, [_span("x", "08:18", "08:19")], request_id="r2")
    result = _record_spans(db_path, [_span(None, "08:15", "08:20")], request_id="r3")
    assert result["recorded"] == 1
    assert result["merged"] == 1
    # The session-bearing row is kept separate with its range intact; the
    # session-less entries merge into one union trimmed around it.
    assert _human_time_rows(db_path) == [
        _expected_span_row(None, "08:14", "08:18", request_id="r3"),
        _expected_span_row("x", "08:18", "08:19", request_id="r2"),
        _expected_span_row(None, "08:19", "08:20", request_id="r3"),
    ]


def test_human_time_same_session_merges_into_union(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    _record_spans(db_path, [_span("s", "08:00", "08:10")], request_id="r1")
    result = _record_spans(db_path, [_span("s", "08:05", "08:15")], request_id="r2")
    assert result["recorded"] == 1
    assert result["merged"] == 1
    assert _human_time_rows(db_path) == [
        _expected_span_row("s", "08:00", "08:15", request_id="r2")
    ]
    # Touching same-session spans merge too.
    result = _record_spans(db_path, [_span("s", "08:15", "08:20")], request_id="r3")
    assert result["merged"] == 1
    assert _human_time_rows(db_path) == [
        _expected_span_row("s", "08:00", "08:20", request_id="r3")
    ]


def test_human_time_end_time_priority_late_arrival_wins(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    _record_spans(db_path, [_span("a", "09:00", "09:10")], request_id="r1")
    # A later-uploaded batch whose span ends earlier is the first entry.
    result = _record_spans(db_path, [_span("b", "08:00", "09:05")], request_id="r2")
    assert result["recorded"] == 1
    assert _human_time_rows(db_path) == [
        _expected_span_row("b", "08:00", "09:05", request_id="r2"),
        _expected_span_row("a", "09:05", "09:10", request_id="r1"),
    ]


def test_human_time_end_time_tie_keeps_existing_row(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    _record_spans(db_path, [_span("a", "08:00", "09:05")], request_id="r1")
    # Equal end times: the existing entry wins; the new span is fully
    # covered and stores nothing.
    result = _record_spans(db_path, [_span("b", "08:30", "09:05")], request_id="r2")
    assert result["recorded"] == 0
    assert result["absorbed"] == 1
    assert _human_time_rows(db_path) == [
        _expected_span_row("a", "08:00", "09:05", request_id="r1")
    ]


def test_human_time_session_beats_session_less_incoming(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    _record_spans(db_path, [_span(None, "08:00", "08:30")], request_id="r1")
    # The incoming session-bearing span wins; the session-less row trims.
    result = _record_spans(db_path, [_span("s", "08:10", "08:20")], request_id="r2")
    assert result["recorded"] == 1
    assert _human_time_rows(db_path) == [
        _expected_span_row(None, "08:00", "08:10", request_id="r1"),
        _expected_span_row("s", "08:10", "08:20", request_id="r2"),
        _expected_span_row(None, "08:20", "08:30", request_id="r1"),
    ]


def test_human_time_session_less_incoming_loses(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    _record_spans(db_path, [_span(None, "08:40", "09:00")], request_id="r1")
    # The incoming session-less span loses; it trims around the row.
    result = _record_spans(db_path, [_span("t", "08:45", "08:55")], request_id="r2")
    assert result["recorded"] == 1
    assert _human_time_rows(db_path) == [
        _expected_span_row(None, "08:40", "08:45", request_id="r1"),
        _expected_span_row("t", "08:45", "08:55", request_id="r2"),
        _expected_span_row(None, "08:55", "09:00", request_id="r1"),
    ]


def test_human_time_session_span_replaces_covered_session_less(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    _record_spans(db_path, [_span(None, "08:02", "08:05")], request_id="r1")
    result = _record_spans(db_path, [_span("s", "08:00", "08:10")], request_id="r2")
    assert result["recorded"] == 1
    # The covered session-less row stores no remainders.
    assert _human_time_rows(db_path) == [
        _expected_span_row("s", "08:00", "08:10", request_id="r2")
    ]


def test_human_time_fully_covered_span_stores_nothing(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    # The session-bearing row wins, so the incoming session-less span is
    # fully covered and stores nothing.
    _record_spans(db_path, [_span("a", "08:00", "08:10")], request_id="r1")
    result = _record_spans(db_path, [_span(None, "08:02", "08:08")], request_id="r2")
    assert result["recorded"] == 0
    assert result["absorbed"] == 1
    assert _human_time_rows(db_path) == [
        _expected_span_row("a", "08:00", "08:10", request_id="r1")
    ]


def test_human_time_touching_different_sessions_stay_separate(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    _record_spans(db_path, [_span("a", "08:00", "08:10")], request_id="r1")
    result = _record_spans(db_path, [_span("b", "08:10", "08:20")], request_id="r2")
    assert result["recorded"] == 1
    assert result["merged"] == 0
    assert _human_time_rows(db_path) == [
        _expected_span_row("a", "08:00", "08:10", request_id="r1"),
        _expected_span_row("b", "08:10", "08:20", request_id="r2"),
    ]


def test_human_time_zero_length_span_stored(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    result = _record_spans(db_path, [_span("s1", "08:00", "08:00")])
    assert result["recorded"] == 1
    rows = _human_time_rows(db_path)
    assert rows[0]["duration_ms"] == 0
    assert duration_store.human_time_session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    ) == {"span_count": 1, "total_ms": 0}


def test_human_time_span_working_directory_override(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    # One batch may mix sessions resolved under different working
    # directories (per-span override over the batch-level value).
    _record_spans(
        db_path,
        [
            _span("s1", "08:00", "08:05"),
            _span("s2", "08:10", "08:15", working_directory="/tmp/other"),
        ],
    )
    assert duration_store.human_time_session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    ) == {"span_count": 1, "total_ms": 5 * 60 * 1000}
    assert duration_store.human_time_session_totals(
        db_path, working_directory="/tmp/other", session_id="s2"
    ) == {"span_count": 1, "total_ms": 5 * 60 * 1000}


def test_human_time_same_session_merges_across_working_directories(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    # Session identity is the session id: when a later batch resolves the
    # same session under a different working directory, overlapping rows
    # merge and consolidate under the incoming resolution.
    _record_spans(
        db_path,
        [_span("s1", "08:00", "08:10")],
        request_id="r1",
        working_directory="/tmp/old-ws",
    )
    result = _record_spans(
        db_path,
        [_span("s1", "08:05", "08:15")],
        request_id="r2",
        working_directory="/tmp/new-ws",
    )
    assert result["recorded"] == 1
    assert result["merged"] == 1
    assert _human_time_rows(db_path) == [
        _expected_span_row(
            "s1", "08:00", "08:15", request_id="r2", working_directory="/tmp/new-ws"
        )
    ]


def test_human_time_timestamp_forms_normalize(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    _record_spans(
        db_path,
        [
            {
                "session_id": "s1",
                "from": "2026-09-25T10:00:00Z",
                "to": "2026-09-25T10:01:00+00:00",
            },
            {
                "session_id": "s2",
                "from": "2026-09-25T11:00:00",
                "to": "2026-09-25T11:02:30.500Z",
            },
        ],
        request_id="r1",
    )
    rows = _human_time_rows(db_path)
    assert rows[0]["from_time"] == "2026-09-25T10:00:00.000000+00:00"
    assert rows[0]["to_time"] == "2026-09-25T10:01:00.000000+00:00"
    assert rows[0]["duration_ms"] == 60 * 1000
    # Naive timestamps are treated as UTC; fractional seconds survive.
    assert rows[1]["from_time"] == "2026-09-25T11:00:00.000000+00:00"
    assert rows[1]["to_time"] == "2026-09-25T11:02:30.500000+00:00"
    assert rows[1]["duration_ms"] == 150500


def test_human_time_rejects_malformed_batch_without_partial_recording(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    result = _record_spans(
        db_path,
        [
            _span("s1", "08:00", "08:05"),
            "not-a-dict",
            {"from": _z("08:00"), "to": _z("08:05")},  # missing session_id
            _span(5, "08:00", "08:05"),  # invalid session id type
            _span("s2", "not-a-date", "08:05"),  # unparseable from
            _span("s2", "08:10", "08:05"),  # from after to
            _span("s2", "08:00", "08:05", working_directory=""),  # empty wd
            {"session_id": "s2", "to": _z("08:05")},  # missing from
        ],
    )
    assert result == {
        "recorded": 0,
        "merged": 0,
        "skipped": 7,
        "absorbed": 0,
        "duplicate": False,
    }
    assert _human_time_rows(db_path) == []

    retry = _record_spans(
        db_path,
        [_span("s1", "08:00", "08:05")],
        request_id="req-1",
    )
    assert retry["duplicate"] is False
    assert retry["recorded"] == 1


def test_human_time_span_without_working_directory_skipped(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    result = _record_spans(
        db_path,
        [_span("s1", "08:00", "08:05")],
        working_directory=None,
    )
    assert result["skipped"] == 1
    assert result["recorded"] == 0
    assert _human_time_rows(db_path) == []


def test_human_time_diagnostics_reports_latest_accepted_upload(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    _record_spans(
        db_path,
        [_span("s1", "08:00", "08:05")],
        request_id="req-diagnostics",
    )

    diagnostics = duration_store.human_time_diagnostics(
        db_path,
        working_directory="/tmp/ws",
        session_id="s1",
    )

    assert diagnostics["span_count"] == 1
    assert diagnostics["total_ms"] == 5 * 60 * 1000
    assert diagnostics["last_span_to"] == "2026-09-25T08:05:00.000000+00:00"
    assert diagnostics["last_request_id"] == "req-diagnostics"
    assert isinstance(diagnostics["last_processed_at"], str)


def test_human_time_batch_cap(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    with pytest.raises(ValueError):
        _record_spans(db_path, [_span("s", "08:00", "08:01") for _ in range(1001)])
    # Exactly 1000 is allowed; identical same-session spans merge into one.
    result = _record_spans(db_path, [_span("s", "08:00", "08:01") for _ in range(1000)])
    assert result["recorded"] == 1000
    assert result["merged"] == 999
    assert len(_human_time_rows(db_path)) == 1


def test_human_time_invalid_request_id_or_spans_raise(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    with pytest.raises(ValueError):
        duration_store.record_human_time_spans(
            db_path, working_directory="/tmp/ws", request_id="", spans=[]
        )
    with pytest.raises(ValueError):
        duration_store.record_human_time_spans(
            db_path, working_directory="/tmp/ws", request_id=None, spans=[]
        )
    with pytest.raises(ValueError):
        duration_store.record_human_time_spans(
            db_path,
            working_directory="/tmp/ws",
            request_id="r",
            spans=cast(List[Any], {"a": 1}),
        )
    with pytest.raises(ValueError):
        duration_store.record_human_time_spans(
            db_path, working_directory="/tmp/ws", request_id="r", spans=None
        )
