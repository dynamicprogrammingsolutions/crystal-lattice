"""SQLite store for the duration tracking plugin.

The store records one row per measured provider call (LLM round) in
``duration_requests``. Tool loops run one finalize per LLM round under a
single request id, so rows are deduplicated by their measurement stamps
(``duration_started_at``/``duration_finished_at``), not by request id —
the same granularity the cost store uses with its per-response rows. The
``tool_durations`` table ships with the same schema so the tool-call
recording (which the same package adds on the framework's
``finalize_tool_call`` seam) needs no migration. It supports
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
    # Migration: the original unique index on request_id alone recorded
    # only the first LLM round of tool-loop requests, because every
    # round of one user request shares the same request id. Rounds are
    # now keyed by their measurement stamps (unique per provider call),
    # matching the cost store's one-row-per-response granularity.
    """
    DROP INDEX IF EXISTS idx_duration_requests_request_id
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_duration_requests_round
    ON duration_requests(
        working_directory, session_id, duration_started_at, duration_finished_at
    )
    WHERE duration_started_at IS NOT NULL AND duration_finished_at IS NOT NULL
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
    """
    CREATE TABLE IF NOT EXISTS human_time_spans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id TEXT,
        working_directory TEXT NOT NULL,
        from_time TEXT NOT NULL,
        to_time TEXT NOT NULL,
        duration_ms INTEGER NOT NULL,
        request_id TEXT
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_human_time_spans_session
    ON human_time_spans(working_directory, session_id)
    """,
    """
    CREATE TABLE IF NOT EXISTS human_time_requests (
        request_id TEXT PRIMARY KEY,
        processed_at TEXT NOT NULL
    )
    """,
)

_write_lock = threading.Lock()

HUMAN_TIME_SPANS_BATCH_CAP = 1000


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
    """Record one measured provider call (LLM round) row.

    Rows dedup by (working_directory, session_id, duration_started_at,
    duration_finished_at) so re-finalize and rebuild paths never
    duplicate a round, while the later rounds of a tool-loop request
    (same request id, different stamps) each get their own row. Rows
    without measurement stamps do not dedup (SQLite unique indexes
    treat NULLs as distinct).
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
                # Identical round (same session + stamps) already recorded.
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


# --- Human time spans (subtask 030) ---
#
# Contract (user, 2026-09-24/25): the frontend computes durations and sends
# spans ``{session_id|null, from, to}``; each upload batch carries a
# frontend-assigned request id used as the retry-dedup key (range overlap is
# never the dedup mechanism). No two stored rows ever overlap: the first
# entry wins — an entry's ``to`` (end) time is its priority timestamp, so
# an earlier-ending entry beats a later one even when batches arrive out of
# order (ties keep the existing row). Losing spans trim to their
# non-overlapping remainders (possibly split into several entries; fully
# covered spans store nothing). Special cases: spans with the same session
# key (equal session ids, or both null) merge into one union entry, and a
# session-bearing entry always beats a session-less one regardless of end
# times. Reports are plain SUM aggregations over the stored durations.


def _parse_span_timestamp(value: Any) -> Optional[datetime]:
    """Parse a tolerant ISO-8601 timestamp; naive values are treated as UTC."""

    if not isinstance(value, str) or not value.strip():
        return None
    raw = value.strip()
    if raw.endswith(("Z", "z")):
        raw = raw[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(raw)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def _normalize_span_timestamp(value: datetime) -> str:
    """Canonical storage form: uniform, lexicographically sortable."""

    return value.astimezone(timezone.utc).isoformat(timespec="microseconds")


def _span_duration_ms(from_time: str, to_time: str) -> int:
    """Duration between two canonical stored timestamps."""

    start = datetime.fromisoformat(from_time)
    end = datetime.fromisoformat(to_time)
    return int((end - start).total_seconds() * 1000)


def _trim_ranges(ranges: List[tuple], cut_from: str, cut_to: str) -> List[tuple]:
    """Remove ``[cut_from, cut_to]`` from a list of disjoint ranges."""

    trimmed: List[tuple] = []
    for start, end in ranges:
        if start < cut_to and end > cut_from:
            if start < cut_from:
                trimmed.append((start, cut_from))
            if cut_to < end:
                trimmed.append((cut_to, end))
        else:
            trimmed.append((start, end))
    return trimmed


def _incoming_span_wins(
    incoming_session_id: Optional[str],
    incoming_to: str,
    existing_session_id: Optional[str],
    existing_to: str,
) -> bool:
    """Overlap priority: session-bearing beats session-less; earlier end wins."""

    if incoming_session_id is not None and existing_session_id is None:
        return True
    if incoming_session_id is None and existing_session_id is not None:
        return False
    # Equal "sessionness" (both session-bearing with different sessions, or
    # both session-less under different working directories): the earlier
    # end time is the first entry and wins; ties keep the existing row.
    return incoming_to < existing_to


def _insert_span_row(
    conn: sqlite3.Connection,
    *,
    session_id: Optional[str],
    working_directory: str,
    from_time: str,
    to_time: str,
    request_id: Optional[str],
) -> None:
    conn.execute(
        """
        INSERT INTO human_time_spans
            (session_id, working_directory, from_time, to_time,
             duration_ms, request_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            session_id,
            working_directory,
            from_time,
            to_time,
            _span_duration_ms(from_time, to_time),
            request_id,
        ),
    )


def _validated_human_time_span(
    span: Any,
    batch_working_directory: Optional[str],
) -> Optional[Dict[str, Any]]:
    if not isinstance(span, dict) or "session_id" not in span:
        return None
    session_id = span["session_id"]
    if session_id is not None and (not isinstance(session_id, str) or not session_id):
        return None
    working_directory = span.get("working_directory", batch_working_directory)
    if not isinstance(working_directory, str) or not working_directory:
        return None
    start = _parse_span_timestamp(span.get("from"))
    end = _parse_span_timestamp(span.get("to"))
    if start is None or end is None or start > end:
        return None
    return {
        "session_id": session_id,
        "working_directory": working_directory,
        "from_time": _normalize_span_timestamp(start),
        "to_time": _normalize_span_timestamp(end),
    }


def count_invalid_human_time_spans(
    spans: List[Any], *, working_directory: Optional[str] = None
) -> int:
    """Count spans that cannot be recorded by an all-or-none batch."""

    return sum(
        _validated_human_time_span(span, working_directory) is None for span in spans
    )


def _apply_human_time_span(
    conn: sqlite3.Connection,
    span: Dict[str, Any],
    request_id: str,
    counts: Dict[str, int],
) -> None:
    """Resolve one validated span into the overlap-free span table."""

    session_id = span["session_id"]
    working_directory = span["working_directory"]
    from_time = span["from_time"]
    to_time = span["to_time"]

    # 1. Same-session rows that overlap or touch merge into one union
    #    entry (loop defensively in case a chain expands the range).
    #    Session identity is the session id: rows of the same session merge
    #    even when earlier batches resolved a different working directory
    #    (the merged entry consolidates under the incoming resolution).
    #    Session-less rows merge only within the same working directory.
    merged_any = False
    while True:
        if session_id is None:
            cluster = conn.execute(
                """
                SELECT id, from_time, to_time FROM human_time_spans
                WHERE working_directory = ? AND session_id IS NULL
                  AND from_time <= ? AND to_time >= ?
                """,
                (working_directory, to_time, from_time),
            ).fetchall()
        else:
            cluster = conn.execute(
                """
                SELECT id, from_time, to_time FROM human_time_spans
                WHERE session_id IS ?
                  AND from_time <= ? AND to_time >= ?
                """,
                (session_id, to_time, from_time),
            ).fetchall()
        if not cluster:
            break
        merged_any = True
        from_time = min([from_time] + [row[1] for row in cluster])
        to_time = max([to_time] + [row[2] for row in cluster])
        conn.executemany(
            "DELETE FROM human_time_spans WHERE id = ?",
            [(row[0],) for row in cluster],
        )
    if merged_any:
        counts["merged"] += 1

    # 2. Compete with different-session rows that strictly overlap the
    #    merged range; losers trim to their non-overlapping remainders.
    pieces: List[tuple] = [(from_time, to_time)]
    if session_id is None:
        competitors = conn.execute(
            """
            SELECT id, session_id, working_directory, from_time, to_time, request_id
            FROM human_time_spans
            WHERE (session_id IS NOT NULL OR working_directory != ?)
              AND from_time < ? AND to_time > ?
            ORDER BY from_time, id
            """,
            (working_directory, to_time, from_time),
        ).fetchall()
    else:
        competitors = conn.execute(
            """
            SELECT id, session_id, working_directory, from_time, to_time, request_id
            FROM human_time_spans
            WHERE session_id IS NOT ?
              AND from_time < ? AND to_time > ?
            ORDER BY from_time, id
            """,
            (session_id, to_time, from_time),
        ).fetchall()
    for row in competitors:
        (
            row_id,
            row_session_id,
            row_working_directory,
            row_from,
            row_to,
            row_request_id,
        ) = row
        if not any(
            piece_from < row_to and piece_to > row_from
            for piece_from, piece_to in pieces
        ):
            continue
        if _incoming_span_wins(session_id, to_time, row_session_id, row_to):
            # The incoming entry wins: trim the existing row against the
            # incoming entry's current pieces.
            remainders: List[tuple] = [(row_from, row_to)]
            for piece_from, piece_to in pieces:
                remainders = _trim_ranges(remainders, piece_from, piece_to)
            conn.execute("DELETE FROM human_time_spans WHERE id = ?", (row_id,))
            for remainder_from, remainder_to in remainders:
                _insert_span_row(
                    conn,
                    session_id=row_session_id,
                    working_directory=row_working_directory,
                    from_time=remainder_from,
                    to_time=remainder_to,
                    request_id=row_request_id,
                )
        else:
            # The existing entry wins: trim the incoming pieces.
            pieces = _trim_ranges(pieces, row_from, row_to)

    # 3. Store whatever remains of the incoming entry.
    if pieces:
        for piece_from, piece_to in pieces:
            _insert_span_row(
                conn,
                session_id=session_id,
                working_directory=working_directory,
                from_time=piece_from,
                to_time=piece_to,
                request_id=request_id,
            )
        counts["recorded"] += 1
    else:
        counts["absorbed"] += 1


def record_human_time_spans(
    db_path: Path,
    *,
    working_directory: Optional[str] = None,
    request_id: Optional[str] = None,
    spans: Optional[List[Any]] = None,
) -> Dict[str, Any]:
    """Record one frontend-reported human-time span batch.

    Dedup is by ``request_id`` (frontend-assigned, stable across retries of
    the same batch): a processed id returns ``duplicate`` without touching
    spans. Each span is ``{session_id: str|null, from, to}`` with an optional
    per-span ``working_directory`` overriding the batch-level value; the
    plugin computes and stores ``duration_ms = to - from``. Overlaps resolve
    so no two stored rows ever overlap (see the module notes above).

    Span-level counts: ``recorded`` spans stored at least one row, ``merged``
    spans merged with same-session-key rows, ``skipped`` invalid spans, and
    ``absorbed`` valid spans fully covered by winning existing entries. Batch
    validation is all-or-none: if any span is invalid, no request marker or
    span is recorded.

    Raises ``ValueError`` for structurally invalid batches (missing request
    id, non-list spans, more than ``HUMAN_TIME_SPANS_BATCH_CAP`` spans);
    malformed spans return a skipped count without recording the batch.
    """

    if not isinstance(request_id, str) or not request_id.strip():
        raise ValueError("request_id must be a non-empty string")
    if not isinstance(spans, list):
        raise ValueError("spans must be a list")
    if len(spans) > HUMAN_TIME_SPANS_BATCH_CAP:
        raise ValueError(
            f"spans batch exceeds the {HUMAN_TIME_SPANS_BATCH_CAP}-span cap"
        )

    counts: Dict[str, int] = {
        "recorded": 0,
        "merged": 0,
        "skipped": 0,
        "absorbed": 0,
    }
    validated_spans = [
        _validated_human_time_span(span, working_directory) for span in spans
    ]
    invalid_count = sum(span is None for span in validated_spans)

    with _write_lock:
        conn = _connect(db_path)
        try:
            _ensure_schema(conn)
            try:
                already = conn.execute(
                    "SELECT 1 FROM human_time_requests WHERE request_id = ?",
                    (request_id,),
                ).fetchone()
                if already:
                    conn.rollback()
                    return {**counts, "duplicate": True}
                if invalid_count:
                    conn.rollback()
                    return {
                        **counts,
                        "skipped": invalid_count,
                        "duplicate": False,
                    }
                conn.execute(
                    "INSERT INTO human_time_requests (request_id, processed_at)"
                    " VALUES (?, ?)",
                    (request_id, utcnow_iso()),
                )
                for span in validated_spans:
                    assert span is not None
                    _apply_human_time_span(conn, span, request_id, counts)
                conn.commit()
                return {**counts, "duplicate": False}
            except Exception:
                conn.rollback()
                raise
        finally:
            conn.close()


def human_time_session_totals(
    db_path: Path, *, working_directory: str, session_id: str
) -> Dict[str, Any]:
    """Return the human-time total and span count for one workspace session."""

    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        row = conn.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(duration_ms), 0)
            FROM human_time_spans
            WHERE working_directory = ? AND session_id = ?
            """,
            (working_directory, session_id),
        ).fetchone()
        return {
            "span_count": int(row[0]) if row else 0,
            "total_ms": int(row[1]) if row else 0,
        }
    finally:
        conn.close()


def human_time_project_totals(
    db_path: Path, *, working_directory: str
) -> Dict[str, Any]:
    """Return the human-time total over all spans of one working directory.

    Includes session-less rows (e.g. session-list activity), which per-session
    totals exclude; kept for future project-level reports.
    """

    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        row = conn.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(duration_ms), 0)
            FROM human_time_spans
            WHERE working_directory = ?
            """,
            (working_directory,),
        ).fetchone()
        return {
            "span_count": int(row[0]) if row else 0,
            "total_ms": int(row[1]) if row else 0,
        }
    finally:
        conn.close()


def human_time_overall_totals(db_path: Path) -> Dict[str, Any]:
    """Return human-time totals across every project and session."""

    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        row = conn.execute(
            """
            SELECT
                COUNT(*),
                COALESCE(SUM(duration_ms), 0),
                COALESCE(SUM(CASE WHEN session_id IS NULL THEN 1 ELSE 0 END), 0),
                COALESCE(
                    SUM(CASE WHEN session_id IS NULL THEN duration_ms ELSE 0 END),
                    0
                )
            FROM human_time_spans
            """
        ).fetchone()
        return {
            "span_count": int(row[0]) if row else 0,
            "total_ms": int(row[1]) if row else 0,
            "sessionless_span_count": int(row[2]) if row else 0,
            "sessionless_ms": int(row[3]) if row else 0,
        }
    finally:
        conn.close()


def top_human_time_sessions(db_path: Path, *, limit: int = 10) -> List[Dict[str, Any]]:
    """Return the top session-bearing groups by recorded human time."""

    if not isinstance(limit, int) or limit <= 0:
        limit = 10
    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        rows = conn.execute(
            """
            SELECT working_directory, session_id, COUNT(*),
                   COALESCE(SUM(duration_ms), 0)
            FROM human_time_spans
            WHERE session_id IS NOT NULL
            GROUP BY working_directory, session_id
            ORDER BY 4 DESC, 3 DESC, working_directory, session_id
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "working_directory": row[0],
                "session_id": row[1],
                "span_count": int(row[2]),
                "total_ms": int(row[3]),
            }
            for row in rows
        ]
    finally:
        conn.close()


def top_human_time_projects(db_path: Path, *, limit: int = 3) -> List[Dict[str, Any]]:
    """Return top projects with session-less time included and identified."""

    if not isinstance(limit, int) or limit <= 0:
        limit = 3
    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        rows = conn.execute(
            """
            SELECT
                working_directory,
                COUNT(*),
                COALESCE(SUM(duration_ms), 0),
                COALESCE(SUM(CASE WHEN session_id IS NULL THEN 1 ELSE 0 END), 0),
                COALESCE(
                    SUM(CASE WHEN session_id IS NULL THEN duration_ms ELSE 0 END),
                    0
                )
            FROM human_time_spans
            GROUP BY working_directory
            ORDER BY 3 DESC, 2 DESC, working_directory
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [
            {
                "working_directory": row[0],
                "span_count": int(row[1]),
                "total_ms": int(row[2]),
                "sessionless_span_count": int(row[3]),
                "sessionless_ms": int(row[4]),
            }
            for row in rows
        ]
    finally:
        conn.close()


def human_time_diagnostics(
    db_path: Path,
    *,
    working_directory: str,
    session_id: Optional[str] = None,
) -> Dict[str, Any]:
    """Return compact user-facing diagnostics for one human-time target."""

    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        if session_id is None:
            span_row = conn.execute(
                """
                SELECT COUNT(*), COALESCE(SUM(duration_ms), 0), MAX(to_time)
                FROM human_time_spans
                WHERE working_directory = ?
                """,
                (working_directory,),
            ).fetchone()
        else:
            span_row = conn.execute(
                """
                SELECT COUNT(*), COALESCE(SUM(duration_ms), 0), MAX(to_time)
                FROM human_time_spans
                WHERE working_directory = ? AND session_id = ?
                """,
                (working_directory, session_id),
            ).fetchone()
        request_row = conn.execute(
            """
            SELECT request_id, processed_at
            FROM human_time_requests
            ORDER BY processed_at DESC, rowid DESC
            LIMIT 1
            """
        ).fetchone()
        return {
            "span_count": int(span_row[0]) if span_row else 0,
            "total_ms": int(span_row[1]) if span_row else 0,
            "last_span_to": span_row[2] if span_row else None,
            "last_request_id": request_row[0] if request_row else None,
            "last_processed_at": request_row[1] if request_row else None,
        }
    finally:
        conn.close()


__all__ = [
    "DEFAULT_DURATION_DB_RELATIVE_PATH",
    "DEFAULT_DURATION_SUMMARY_CSV_FILENAME",
    "DURATION_SUMMARY_CSV_FIELDNAMES",
    "HUMAN_TIME_SPANS_BATCH_CAP",
    "append_request_summary_csv",
    "count_invalid_human_time_spans",
    "human_time_diagnostics",
    "human_time_overall_totals",
    "human_time_project_totals",
    "human_time_session_totals",
    "overall_totals",
    "record_human_time_spans",
    "record_request_duration",
    "record_tool_duration",
    "resolve_duration_db_path",
    "resolve_summary_csv_path",
    "session_totals",
    "summary_csv_enabled",
    "tool_session_totals",
    "top_human_time_projects",
    "top_human_time_sessions",
    "top_projects",
    "top_sessions",
    "utcnow_iso",
]
