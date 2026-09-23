"""SQLite store for the duration tracking plugin.

The store records one row per measured provider request in
``duration_requests``. The ``tool_durations`` table ships with the same
schema so the tool-call recording (which the same package adds on the
framework's ``finalize_tool_call`` seam) needs no migration. It supports
the aggregations the plugin needs:

- session totals filtered by (working_directory, session_id) for the
  chat status bar;
- top sessions and top projects for the report action.

All functions are best-effort by contract at the call sites (the
tracking plugin swallows failures so journaling can never break the
request pipeline); the store itself does not swallow errors so tests
can catch schema bugs.
"""

from __future__ import annotations

import csv
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_DURATION_DB_RELATIVE_PATH = "duration-tracking/duration-tracking.sqlite3"
DEFAULT_DURATION_SUMMARY_CSV_FILENAME = "duration-tracking-summary.csv"

DURATION_SUMMARY_CSV_FIELDNAMES = [
    "time",
    "working_directory",
    "session_id",
    "model",
    "duration",
    "session_total_duration",
]

_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS duration_requests (
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
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_duration_requests_request_id
    ON duration_requests(request_id)
    WHERE request_id IS NOT NULL
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_duration_requests_session
    ON duration_requests(working_directory, session_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS tool_durations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT NOT NULL,
        session_id TEXT,
        working_directory TEXT,
        model TEXT,
        request_id TEXT,
        tool_call_id TEXT,
        tool_name TEXT,
        tool_plugin TEXT,
        duration_ms INTEGER,
        duration_started_at TEXT,
        duration_finished_at TEXT,
        tool_error TEXT
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_tool_durations_call
    ON tool_durations(working_directory, session_id, request_id, tool_call_id)
    WHERE tool_call_id IS NOT NULL
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_tool_durations_session
    ON tool_durations(working_directory, session_id)
    """,
)

_write_lock = threading.Lock()


def utcnow_iso() -> str:
    """Return the current UTC time as a sortable ISO 8601 string."""

    return datetime.now(timezone.utc).isoformat()


def resolve_duration_db_path(config: Optional[Dict[str, Any]]) -> Path:
    """Resolve the duration store location.

    Explicit ``duration_tracking_db_path`` config wins; otherwise the
    store lives under the Crystal data directory (``CRYSTAL_DATA_DIR``,
    default ``~/.crystal``) so user-owned duration data never follows
    the active config file location.
    """

    raw = config.get("duration_tracking_db_path") if isinstance(config, dict) else None
    if isinstance(raw, str) and raw.strip():
        return Path(raw).expanduser()

    data_dir = os.environ.get("CRYSTAL_DATA_DIR")
    if isinstance(data_dir, str) and data_dir:
        return Path(data_dir) / DEFAULT_DURATION_DB_RELATIVE_PATH
    return Path.cwd() / DEFAULT_DURATION_DB_RELATIVE_PATH


def _connect(db_path: Path) -> sqlite3.Connection:
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path), timeout=30.0)
    conn.execute("PRAGMA busy_timeout = 30000")
    return conn


def _ensure_schema(conn: sqlite3.Connection) -> None:
    for statement in _SCHEMA_STATEMENTS:
        conn.execute(statement)


def _coerce_int(value: Any) -> Optional[int]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return int(value)


def _optional_str(value: Any) -> Optional[str]:
    return value if isinstance(value, str) and value else None


def record_request_duration(
    db_path: Path,
    *,
    session_id: Optional[str] = None,
    working_directory: Optional[str] = None,
    model: Optional[str] = None,
    request_id: Optional[str] = None,
    duration_ms: Optional[int] = None,
    duration_started_at: Optional[str] = None,
    duration_finished_at: Optional[str] = None,
    time: Optional[str] = None,
) -> bool:
    """Record one measured provider request row.

    Returns ``False`` when the request id was already recorded so
    re-finalize and rebuild paths never duplicate rows. Rows without a
    request id do not dedup (SQLite unique indexes treat NULLs as
    distinct); callers that always carry a request context never hit
    that case.
    """

    values: Dict[str, Any] = {
        "time": time if isinstance(time, str) and time else utcnow_iso(),
        "session_id": _optional_str(session_id),
        "working_directory": _optional_str(working_directory),
        "model": _optional_str(model),
        "request_id": _optional_str(request_id),
        "duration_ms": _coerce_int(duration_ms),
        "duration_started_at": _optional_str(duration_started_at),
        "duration_finished_at": _optional_str(duration_finished_at),
    }

    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    with _write_lock:
        conn = _connect(db_path)
        try:
            _ensure_schema(conn)
            try:
                conn.execute(
                    f"INSERT INTO duration_requests ({columns}) "
                    f"VALUES ({placeholders})",
                    tuple(values.values()),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Unique request id already recorded.
                conn.rollback()
                return False
        finally:
            conn.close()


def session_totals(
    db_path: Path, *, working_directory: str, session_id: str
) -> Dict[str, Any]:
    """Return the duration total and request count for one workspace session.

    Totals are factual history over the recorded rows; requests without
    a measured duration contribute to the count but not the total.
    """

    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        row = conn.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(duration_ms), 0)
            FROM duration_requests
            WHERE working_directory = ? AND session_id = ?
            """,
            (working_directory, session_id),
        ).fetchone()
        return {
            "request_count": int(row[0]) if row else 0,
            "total_ms": int(row[1]) if row else 0,
        }
    finally:
        conn.close()


def overall_totals(db_path: Path) -> Dict[str, Any]:
    """Return the LLM and tool duration totals over all recorded rows."""

    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        row = conn.execute(
            """
            SELECT
                (SELECT COUNT(*) FROM duration_requests),
                (SELECT COALESCE(SUM(duration_ms), 0) FROM duration_requests),
                (SELECT COUNT(*) FROM tool_durations),
                (SELECT COALESCE(SUM(duration_ms), 0) FROM tool_durations)
            """
        ).fetchone()
        return {
            "request_count": int(row[0]) if row else 0,
            "total_ms": int(row[1]) if row else 0,
            "tool_call_count": int(row[2]) if row else 0,
            "tool_total_ms": int(row[3]) if row else 0,
        }
    finally:
        conn.close()


def resolve_summary_csv_path(db_path: Path, config: Optional[Dict[str, Any]]) -> Path:
    """Resolve the summary CSV location beside the SQLite store.

    Explicit ``duration_tracking_summary_csv_path`` config wins;
    otherwise the CSV lives next to the resolved database file.
    """

    raw = (
        config.get("duration_tracking_summary_csv_path")
        if isinstance(config, dict)
        else None
    )
    if isinstance(raw, str) and raw.strip():
        return Path(raw).expanduser()
    return Path(db_path).with_name(DEFAULT_DURATION_SUMMARY_CSV_FILENAME)


def summary_csv_enabled(config: Optional[Dict[str, Any]]) -> bool:
    """Return whether the summary CSV should be appended (default enabled)."""

    if not isinstance(config, dict):
        return True
    return config.get("track_duration_tracking_summary_csv") is not False


def _append_summary_csv_row(csv_path: Path, row: Dict[str, Any]) -> bool:
    """Append one summary row, writing the header for a fresh file."""

    with _write_lock:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        needs_header = not csv_path.exists() or csv_path.stat().st_size == 0
        with open(csv_path, "a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle,
                fieldnames=DURATION_SUMMARY_CSV_FIELDNAMES,
                extrasaction="ignore",
            )
            if needs_header:
                writer.writeheader()
            writer.writerow(row)
    return True


def append_request_summary_csv(
    db_path: Path,
    config: Optional[Dict[str, Any]],
    *,
    session_id: Optional[str] = None,
    working_directory: Optional[str] = None,
    model: Optional[str] = None,
    duration_ms: Optional[int] = None,
    time: Optional[str] = None,
) -> bool:
    """Append one per-request summary row with the rolling session total.

    Call after the request row was inserted so the rolling total computed
    from the store includes it. ``session_total_duration`` is the factual
    total for the (working_directory, session_id) pair, matching the
    status-bar semantics. Best-effort: failures are swallowed and reported
    via the return value so the CSV can never break the request pipeline.
    """

    if not summary_csv_enabled(config):
        return False
    try:
        session_total: Optional[float] = None
        if isinstance(working_directory, str) and isinstance(session_id, str):
            totals = session_totals(
                db_path, working_directory=working_directory, session_id=session_id
            )
            session_total = float(totals.get("total_ms") or 0)
        row: Dict[str, Any] = {
            "time": time if isinstance(time, str) and time else utcnow_iso(),
            "working_directory": working_directory,
            "session_id": session_id,
            "model": model,
            "duration": (
                float(duration_ms)
                if isinstance(duration_ms, (int, float))
                and not isinstance(duration_ms, bool)
                else ""
            ),
            "session_total_duration": (
                session_total if session_total is not None else ""
            ),
        }
        return _append_summary_csv_row(resolve_summary_csv_path(db_path, config), row)
    except Exception:
        return False


def record_tool_duration(
    db_path: Path,
    *,
    session_id: Optional[str] = None,
    working_directory: Optional[str] = None,
    model: Optional[str] = None,
    request_id: Optional[str] = None,
    tool_call_id: Optional[str] = None,
    tool_name: Optional[str] = None,
    tool_plugin: Optional[str] = None,
    duration_ms: Optional[int] = None,
    duration_started_at: Optional[str] = None,
    duration_finished_at: Optional[str] = None,
    tool_error: Optional[str] = None,
    time: Optional[str] = None,
) -> bool:
    """Record one executed tool-call duration row.

    Returns ``False`` when the composite key
    ``(working_directory, session_id, request_id, tool_call_id)`` was
    already recorded so re-dispatch paths never duplicate rows. Rows
    with a NULL key component do not dedup (SQLite unique indexes treat
    NULLs as distinct); calls without a tool call id (failed inspection)
    are distinct events.
    """

    values: Dict[str, Any] = {
        "time": time if isinstance(time, str) and time else utcnow_iso(),
        "session_id": _optional_str(session_id),
        "working_directory": _optional_str(working_directory),
        "model": _optional_str(model),
        "request_id": _optional_str(request_id),
        "tool_call_id": _optional_str(tool_call_id),
        "tool_name": _optional_str(tool_name),
        "tool_plugin": _optional_str(tool_plugin),
        "duration_ms": _coerce_int(duration_ms),
        "duration_started_at": _optional_str(duration_started_at),
        "duration_finished_at": _optional_str(duration_finished_at),
        "tool_error": _optional_str(tool_error),
    }

    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    with _write_lock:
        conn = _connect(db_path)
        try:
            _ensure_schema(conn)
            try:
                conn.execute(
                    f"INSERT INTO tool_durations ({columns}) "
                    f"VALUES ({placeholders})",
                    tuple(values.values()),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Composite key already recorded.
                conn.rollback()
                return False
        finally:
            conn.close()


def tool_session_totals(
    db_path: Path, *, working_directory: str, session_id: str
) -> Dict[str, Any]:
    """Return the tool duration total and call count for one workspace session."""

    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        row = conn.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(duration_ms), 0)
            FROM tool_durations
            WHERE working_directory = ? AND session_id = ?
            """,
            (working_directory, session_id),
        ).fetchone()
        return {
            "call_count": int(row[0]) if row else 0,
            "total_ms": int(row[1]) if row else 0,
        }
    finally:
        conn.close()


# Per-group tool aggregates joined into the top queries; groups without
# tool rows report zero tool columns.
_TOOL_AGGREGATE_SESSIONS = """
    SELECT working_directory, session_id,
           SUM(duration_ms) AS tool_total_ms, COUNT(*) AS tool_call_count
    FROM tool_durations
    GROUP BY working_directory, session_id
"""

_TOOL_AGGREGATE_PROJECTS = """
    SELECT working_directory,
           SUM(duration_ms) AS tool_total_ms, COUNT(*) AS tool_call_count
    FROM tool_durations
    GROUP BY working_directory
"""


def top_sessions(db_path: Path, *, limit: int = 10) -> List[Dict[str, Any]]:
    """Return the top sessions by recorded request duration.

    Sessions are grouped by (working_directory, session_id); rows
    without both are skipped. Tool totals are joined per session.
    """

    if not isinstance(limit, int) or limit <= 0:
        limit = 10
    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        rows = conn.execute(
            f"""
            SELECT dr.working_directory, dr.session_id, COUNT(*),
                   COALESCE(SUM(dr.duration_ms), 0),
                   COALESCE(t.tool_total_ms, 0), COALESCE(t.tool_call_count, 0)
            FROM duration_requests dr
            LEFT JOIN ({_TOOL_AGGREGATE_SESSIONS}) t
              ON t.working_directory = dr.working_directory
             AND t.session_id = dr.session_id
            WHERE dr.session_id IS NOT NULL
              AND dr.working_directory IS NOT NULL
            GROUP BY dr.working_directory, dr.session_id
            ORDER BY 4 DESC, 3 DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "working_directory": row[0],
                "session_id": row[1],
                "request_count": int(row[2]),
                "total_ms": int(row[3]),
                "tool_total_ms": int(row[4]),
                "tool_call_count": int(row[5]),
            }
            for row in rows
        ]
    finally:
        conn.close()


def top_projects(db_path: Path, *, limit: int = 5) -> List[Dict[str, Any]]:
    """Return the top projects (working directories) by recorded duration.

    Tool totals are joined per project.
    """

    if not isinstance(limit, int) or limit <= 0:
        limit = 5
    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        rows = conn.execute(
            f"""
            SELECT dr.working_directory, COUNT(*),
                   COALESCE(SUM(dr.duration_ms), 0),
                   COALESCE(t.tool_total_ms, 0), COALESCE(t.tool_call_count, 0)
            FROM duration_requests dr
            LEFT JOIN ({_TOOL_AGGREGATE_PROJECTS}) t
              ON t.working_directory = dr.working_directory
            WHERE dr.working_directory IS NOT NULL
            GROUP BY dr.working_directory
            ORDER BY 3 DESC, 2 DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "working_directory": row[0],
                "request_count": int(row[1]),
                "total_ms": int(row[2]),
                "tool_total_ms": int(row[3]),
                "tool_call_count": int(row[4]),
            }
            for row in rows
        ]
    finally:
        conn.close()


__all__ = [
    "DEFAULT_DURATION_DB_RELATIVE_PATH",
    "DEFAULT_DURATION_SUMMARY_CSV_FILENAME",
    "DURATION_SUMMARY_CSV_FIELDNAMES",
    "append_request_summary_csv",
    "overall_totals",
    "record_request_duration",
    "record_tool_duration",
    "resolve_duration_db_path",
    "resolve_summary_csv_path",
    "session_totals",
    "summary_csv_enabled",
    "tool_session_totals",
    "top_projects",
    "top_sessions",
    "utcnow_iso",
]
