"""SQLite store for the generic cost tracking plugin.

The store records one row per provider request that carries usage metadata
and a provider-defined cost bucket. It supports the aggregations the plugin
needs:

- footer session totals filtered by (working_directory, session_id);
- reset-aware report totals filtered by bucket and time;
- a growing summary CSV beside the SQLite file with per-request rows plus
  rolling per-session and per-bucket (reset-aware) totals.

All functions are best-effort by contract at the call sites (the extension
swallows failures so journaling can never break the request pipeline), but
the store itself raises on genuine misuse so tests can catch schema bugs.
"""

from __future__ import annotations

import csv
import os
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional


DEFAULT_COST_DB_RELATIVE_PATH = "cost-tracking/cost-tracking.sqlite3"
DEFAULT_COST_SUMMARY_CSV_FILENAME = "cost-tracking-summary.csv"

COST_SUMMARY_CSV_FIELDNAMES = [
    "time",
    "bucket",
    "working_directory",
    "session_id",
    "model",
    "cost",
    "session_total_cost",
    "bucket_total_cost",
]

_SCHEMA_STATEMENTS = (
    """
    CREATE TABLE IF NOT EXISTS cost_requests (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT NOT NULL,
        bucket TEXT NOT NULL,
        session_id TEXT,
        working_directory TEXT,
        model TEXT,
        response_id TEXT,
        input_tokens INTEGER,
        cached_tokens INTEGER,
        cache_write_tokens INTEGER,
        output_tokens INTEGER,
        reasoning_tokens INTEGER,
        estimated_cost REAL,
        actual_cost REAL
    )
    """,
    """
    CREATE UNIQUE INDEX IF NOT EXISTS idx_cost_requests_response_id
    ON cost_requests(response_id)
    WHERE response_id IS NOT NULL
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_cost_requests_session
    ON cost_requests(working_directory, session_id)
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_cost_requests_bucket_time
    ON cost_requests(bucket, time)
    """,
    """
    CREATE TABLE IF NOT EXISTS cost_resets (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        time TEXT NOT NULL,
        bucket TEXT NOT NULL
    )
    """,
    """
    CREATE INDEX IF NOT EXISTS idx_cost_resets_bucket_time
    ON cost_resets(bucket, time)
    """,
)

_write_lock = threading.Lock()


def utcnow_iso() -> str:
    """Return the current UTC time as a sortable ISO 8601 string."""

    return datetime.now(timezone.utc).isoformat()


def resolve_cost_db_path(config: Optional[Dict[str, Any]]) -> Path:
    """Resolve the cost store location.

    Explicit ``cost_tracking_db_path`` config wins; otherwise the store lives
    under the Crystal data directory (``CRYSTAL_DATA_DIR``, default
    ``~/.crystal``) so user-owned cost data never follows the active config
    file location.
    """

    raw = config.get("cost_tracking_db_path") if isinstance(config, dict) else None
    if isinstance(raw, str) and raw.strip():
        return Path(raw).expanduser()

    data_dir = os.environ.get("CRYSTAL_DATA_DIR")
    if isinstance(data_dir, str) and data_dir:
        return Path(data_dir) / DEFAULT_COST_DB_RELATIVE_PATH
    return Path.cwd() / DEFAULT_COST_DB_RELATIVE_PATH


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


def _coerce_float(value: Any) -> Optional[float]:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        return None
    return float(value)


def record_request_usage(
    db_path: Path,
    *,
    bucket: str,
    session_id: Optional[str] = None,
    working_directory: Optional[str] = None,
    model: Optional[str] = None,
    response_id: Optional[str] = None,
    input_tokens: Optional[int] = None,
    cached_tokens: Optional[int] = None,
    cache_write_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    reasoning_tokens: Optional[int] = None,
    estimated_cost: Optional[float] = None,
    actual_cost: Optional[float] = None,
    time: Optional[str] = None,
) -> bool:
    """Record one request usage row.

    Returns ``False`` when the response id was already recorded so
    re-finalize and rebuild paths never duplicate rows.
    """

    if not isinstance(bucket, str) or not bucket.strip():
        raise ValueError("bucket must be a non-empty string")

    values: Dict[str, Any] = {
        "time": time if isinstance(time, str) and time else utcnow_iso(),
        "bucket": bucket,
        "session_id": session_id if isinstance(session_id, str) else None,
        "working_directory": (
            working_directory if isinstance(working_directory, str) else None
        ),
        "model": model if isinstance(model, str) else None,
        "response_id": response_id if isinstance(response_id, str) else None,
        "input_tokens": _coerce_int(input_tokens),
        "cached_tokens": _coerce_int(cached_tokens),
        "cache_write_tokens": _coerce_int(cache_write_tokens),
        "output_tokens": _coerce_int(output_tokens),
        "reasoning_tokens": _coerce_int(reasoning_tokens),
        "estimated_cost": _coerce_float(estimated_cost),
        "actual_cost": _coerce_float(actual_cost),
    }

    columns = ", ".join(values)
    placeholders = ", ".join("?" for _ in values)
    with _write_lock:
        conn = _connect(db_path)
        try:
            _ensure_schema(conn)
            try:
                conn.execute(
                    f"INSERT INTO cost_requests ({columns}) VALUES ({placeholders})",
                    tuple(values.values()),
                )
                conn.commit()
                return True
            except sqlite3.IntegrityError:
                # Unique response id already recorded.
                conn.rollback()
                return False
        finally:
            conn.close()


def session_totals(
    db_path: Path, *, working_directory: str, session_id: str
) -> Dict[str, Any]:
    """Return the cost total and request count for one workspace session.

    Session totals are factual history and are not affected by reset markers.
    Cost prefers the actual cost reported by the provider and falls back to
    the estimated cost.
    """

    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        row = conn.execute(
            """
            SELECT COUNT(*), COALESCE(SUM(COALESCE(actual_cost, estimated_cost, 0.0)), 0.0)
            FROM cost_requests
            WHERE working_directory = ? AND session_id = ?
            """,
            (working_directory, session_id),
        ).fetchone()
        return {
            "request_count": int(row[0]) if row else 0,
            "total_cost": float(row[1]) if row else 0.0,
        }
    finally:
        conn.close()


def _last_reset_time(conn: sqlite3.Connection, bucket: str) -> Optional[str]:
    row = conn.execute(
        "SELECT MAX(time) FROM cost_resets WHERE bucket = ?", (bucket,)
    ).fetchone()
    if row and isinstance(row[0], str):
        return row[0]
    return None


def bucket_report(db_path: Path) -> Dict[str, Any]:
    """Return reset-aware cost totals per bucket and overall.

    Each bucket total covers the requests recorded after that bucket's most
    recent reset marker (or all of them when the bucket was never reset).
    """

    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        buckets = [
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT bucket FROM cost_requests ORDER BY bucket"
            ).fetchall()
        ]
        entries: List[Dict[str, Any]] = []
        overall_total = 0.0
        overall_count = 0
        for bucket in buckets:
            reset_at = _last_reset_time(conn, bucket)
            params: List[Any] = [bucket]
            time_filter = ""
            if reset_at is not None:
                time_filter = " AND time > ?"
                params.append(reset_at)
            row = conn.execute(
                f"""
                SELECT COUNT(*),
                       COALESCE(SUM(COALESCE(actual_cost, estimated_cost, 0.0)), 0.0)
                FROM cost_requests
                WHERE bucket = ?{time_filter}
                """,
                params,
            ).fetchone()
            request_count = int(row[0]) if row else 0
            total_cost = float(row[1]) if row else 0.0
            entries.append(
                {
                    "bucket": bucket,
                    "request_count": request_count,
                    "total_cost": total_cost,
                    "last_reset_at": reset_at,
                }
            )
            overall_total += total_cost
            overall_count += request_count
        return {
            "buckets": entries,
            "total_cost": overall_total,
            "request_count": overall_count,
        }
    finally:
        conn.close()


def bucket_total_since_reset(db_path: Path, *, bucket: str) -> Dict[str, Any]:
    """Return the reset-aware cost total for one bucket.

    The total covers the requests recorded after the bucket's most recent
    reset marker (or all of them when the bucket was never reset), matching
    the report semantics.
    """

    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        reset_at = _last_reset_time(conn, bucket)
        params: List[Any] = [bucket]
        time_filter = ""
        if reset_at is not None:
            time_filter = " AND time > ?"
            params.append(reset_at)
        row = conn.execute(
            f"""
            SELECT COUNT(*),
                   COALESCE(SUM(COALESCE(actual_cost, estimated_cost, 0.0)), 0.0)
            FROM cost_requests
            WHERE bucket = ?{time_filter}
            """,
            params,
        ).fetchone()
        return {
            "bucket": bucket,
            "request_count": int(row[0]) if row else 0,
            "total_cost": float(row[1]) if row else 0.0,
            "last_reset_at": reset_at,
        }
    finally:
        conn.close()


def resolve_summary_csv_path(db_path: Path, config: Optional[Dict[str, Any]]) -> Path:
    """Resolve the summary CSV location beside the SQLite store.

    Explicit ``cost_tracking_summary_csv_path`` config wins; otherwise the
    CSV lives next to the resolved database file.
    """

    raw = (
        config.get("cost_tracking_summary_csv_path")
        if isinstance(config, dict)
        else None
    )
    if isinstance(raw, str) and raw.strip():
        return Path(raw).expanduser()
    return Path(db_path).with_name(DEFAULT_COST_SUMMARY_CSV_FILENAME)


def summary_csv_enabled(config: Optional[Dict[str, Any]]) -> bool:
    """Return whether the summary CSV should be appended (default enabled)."""

    if not isinstance(config, dict):
        return True
    return config.get("track_cost_tracking_summary_csv") is not False


def _append_summary_csv_row(csv_path: Path, row: Dict[str, Any]) -> bool:
    """Append one summary row, writing the header for a fresh file."""

    with _write_lock:
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        needs_header = not csv_path.exists() or csv_path.stat().st_size == 0
        with open(csv_path, "a", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(
                handle, fieldnames=COST_SUMMARY_CSV_FIELDNAMES, extrasaction="ignore"
            )
            if needs_header:
                writer.writeheader()
            writer.writerow(row)
    return True


def append_request_summary_csv(
    db_path: Path,
    config: Optional[Dict[str, Any]],
    *,
    bucket: str,
    session_id: Optional[str] = None,
    working_directory: Optional[str] = None,
    model: Optional[str] = None,
    cost: Optional[float] = None,
    time: Optional[str] = None,
) -> bool:
    """Append one per-request summary row with rolling totals.

    Call after the request row was inserted so the rolling totals computed
    from the store include it. ``session_total_cost`` is the factual total
    for the (working_directory, session_id) pair (not reset-aware, matching
    the footer semantics); ``bucket_total_cost`` covers the bucket since its
    most recent reset marker (matching the report semantics). Best-effort:
    failures are swallowed and reported via the return value so the CSV can
    never break the request pipeline.
    """

    if not summary_csv_enabled(config):
        return False
    try:
        session_total: Optional[float] = None
        if isinstance(working_directory, str) and isinstance(session_id, str):
            totals = session_totals(
                db_path, working_directory=working_directory, session_id=session_id
            )
            session_total = float(totals.get("total_cost") or 0.0)
        bucket_total = float(
            bucket_total_since_reset(db_path, bucket=bucket).get("total_cost") or 0.0
        )
        row: Dict[str, Any] = {
            "time": time if isinstance(time, str) and time else utcnow_iso(),
            "bucket": bucket,
            "working_directory": working_directory,
            "session_id": session_id,
            "model": model,
            "cost": (
                float(cost)
                if isinstance(cost, (int, float)) and not isinstance(cost, bool)
                else ""
            ),
            "session_total_cost": (session_total if session_total is not None else ""),
            "bucket_total_cost": bucket_total,
        }
        return _append_summary_csv_row(resolve_summary_csv_path(db_path, config), row)
    except Exception:
        return False


def append_reset_summary_csv(
    db_path: Path,
    config: Optional[Dict[str, Any]],
    *,
    bucket: str,
    time: Optional[str] = None,
) -> bool:
    """Append one reset marker row so the CSV shows where totals restart.

    The row carries the bucket and a zeroed ``bucket_total_cost``; request
    columns stay empty. Best-effort, like the request rows.
    """

    if not summary_csv_enabled(config):
        return False
    try:
        row: Dict[str, Any] = {
            "time": time if isinstance(time, str) and time else utcnow_iso(),
            "bucket": bucket,
            "working_directory": "",
            "session_id": "",
            "model": "",
            "cost": "",
            "session_total_cost": "",
            "bucket_total_cost": 0.0,
        }
        return _append_summary_csv_row(resolve_summary_csv_path(db_path, config), row)
    except Exception:
        return False


def known_buckets(db_path: Path) -> List[str]:
    """Return the distinct buckets recorded in the store."""

    conn = _connect(db_path)
    try:
        _ensure_schema(conn)
        return [
            row[0]
            for row in conn.execute(
                "SELECT DISTINCT bucket FROM cost_requests ORDER BY bucket"
            ).fetchall()
        ]
    finally:
        conn.close()


def reset_bucket(
    db_path: Path, *, bucket: str, time: Optional[str] = None
) -> Dict[str, Any]:
    """Append a reset marker for one bucket.

    Subsequent report totals for that bucket cover only records recorded
    after the marker; the recorded history itself is preserved.
    """

    if not isinstance(bucket, str) or not bucket.strip():
        raise ValueError("bucket must be a non-empty string")
    marker_time = time if isinstance(time, str) and time else utcnow_iso()
    with _write_lock:
        conn = _connect(db_path)
        try:
            _ensure_schema(conn)
            conn.execute(
                "INSERT INTO cost_resets (time, bucket) VALUES (?, ?)",
                (marker_time, bucket),
            )
            conn.commit()
        finally:
            conn.close()
    return {"bucket": bucket, "reset_at": marker_time}


__all__ = [
    "COST_SUMMARY_CSV_FIELDNAMES",
    "DEFAULT_COST_DB_RELATIVE_PATH",
    "DEFAULT_COST_SUMMARY_CSV_FILENAME",
    "append_request_summary_csv",
    "append_reset_summary_csv",
    "bucket_report",
    "bucket_total_since_reset",
    "known_buckets",
    "record_request_usage",
    "resolve_cost_db_path",
    "resolve_summary_csv_path",
    "reset_bucket",
    "session_totals",
    "summary_csv_enabled",
    "utcnow_iso",
]
