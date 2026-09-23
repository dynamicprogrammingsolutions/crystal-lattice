"""Unit tests for the duration tracking SQLite store."""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Any, Dict, List

import pytest

from duration_tracking_plugins import duration_store


def _record(db_path: Path, **overrides):
    params: Dict[str, Any] = {
        "session_id": "s1",
        "working_directory": "/tmp/ws",
        "model": "m",
        "request_id": None,
        "duration_ms": 1200,
        "duration_started_at": "2026-01-01T00:00:00+00:00",
        "duration_finished_at": "2026-01-01T00:00:01.200000+00:00",
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
    assert "idx_duration_requests_request_id" in _table_indexes(
        db_path, "duration_requests"
    )
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


def test_record_dedupes_by_request_id(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    assert _record(db_path, request_id="r1") is True
    assert _record(db_path, request_id="r1", duration_ms=999) is False

    totals = duration_store.session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    assert totals["request_count"] == 1
    assert totals["total_ms"] == 1200


def test_record_without_request_id_does_not_dedup(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"

    assert _record(db_path, request_id=None) is True
    assert _record(db_path, request_id=None) is True

    totals = duration_store.session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    assert totals["request_count"] == 2


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
