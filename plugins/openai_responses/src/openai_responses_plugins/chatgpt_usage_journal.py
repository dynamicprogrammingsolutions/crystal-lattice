"""Append-only ChatGPT usage journal.

Records every captured ChatGPT rate-limit snapshot and every ChatGPT-backed
request's estimated usage as NDJSON so plan usage contributors, usage
percentage history, and reset-time changes can be inspected and reconstructed
by date. The journal is append-only: records are never rewritten or truncated
by the platform.
"""

from __future__ import annotations

import csv
import json
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from .chatgpt_credentials import isoformat_utc, parse_iso8601
from .chatgpt_rate_limits import resolve_rate_limits_path


DEFAULT_CHATGPT_USAGE_JOURNAL_RELATIVE_PATH = "auth/chatgpt-usage-journal.ndjson"
DEFAULT_CHATGPT_USAGE_JOURNAL_FILENAME = "chatgpt-usage-journal.ndjson"
JOURNAL_RECORD_TYPES = frozenset(
    {
        "rate_limit_snapshot",
        "request_usage",
        "usage_reset",
    }
)

RATE_LIMIT_SNAPSHOT_RECORD_TYPE = "rate_limit_snapshot"
REQUEST_USAGE_RECORD_TYPE = "request_usage"
USAGE_RESET_RECORD_TYPE = "usage_reset"

_write_lock = threading.Lock()


def resolve_usage_journal_path(config: Dict[str, Any]) -> Path:
    raw = config.get("chatgpt_usage_journal_path")
    if isinstance(raw, str) and raw.strip():
        return Path(raw).expanduser()

    rate_limits_path = resolve_rate_limits_path(config)
    return rate_limits_path.with_name(DEFAULT_CHATGPT_USAGE_JOURNAL_FILENAME)


def append_journal_record(path: Path, record: Dict[str, Any]) -> bool:
    """Append one journal record as a single NDJSON line.

    Best-effort: failures are swallowed and reported via the return value so
    journaling can never break the request pipeline.
    """

    if not isinstance(record, dict) or record.get("type") not in JOURNAL_RECORD_TYPES:
        return False
    try:
        line = json.dumps(record, sort_keys=True)
        with _write_lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        return True
    except Exception:
        return False


def append_rate_limit_snapshot(
    path: Path,
    *,
    snapshots: List[Dict[str, Any]],
    plan_type: Any = None,
    source: str = "x-codex-headers",
    captured_at: Optional[datetime] = None,
) -> bool:
    if not isinstance(snapshots, list) or not snapshots:
        return False
    record: Dict[str, Any] = {
        "type": RATE_LIMIT_SNAPSHOT_RECORD_TYPE,
        "timestamp": isoformat_utc(captured_at or datetime.now(timezone.utc)),
        "source": source,
        "snapshots": snapshots,
    }
    if isinstance(plan_type, str) and plan_type:
        record["plan_type"] = plan_type
    return append_journal_record(path, record)


def append_request_usage(
    path: Path,
    *,
    input_tokens: Optional[int] = None,
    cached_tokens: Optional[int] = None,
    cache_write_tokens: Optional[int] = None,
    output_tokens: Optional[int] = None,
    reasoning_tokens: Optional[int] = None,
    estimated_cached_tokens: Optional[int] = None,
    estimated_cost: Optional[float] = None,
    model: Any = None,
    response_id: Any = None,
    service_tier: Any = None,
    reasoning_mode: Any = None,
    usage: Optional[Dict[str, Any]] = None,
    rate_limits: Optional[Dict[str, Any]] = None,
    timestamp: Optional[datetime] = None,
) -> bool:
    record: Dict[str, Any] = {
        "type": REQUEST_USAGE_RECORD_TYPE,
        "timestamp": isoformat_utc(timestamp or datetime.now(timezone.utc)),
    }
    if isinstance(response_id, str) and response_id:
        record["response_id"] = response_id
    if isinstance(model, str) and model:
        record["model"] = model
    if isinstance(service_tier, str) and service_tier:
        record["service_tier"] = service_tier
    if isinstance(reasoning_mode, str) and reasoning_mode:
        record["reasoning_mode"] = reasoning_mode
    for key, value in (
        ("input_tokens", input_tokens),
        ("cached_tokens", cached_tokens),
        ("cache_write_tokens", cache_write_tokens),
        ("output_tokens", output_tokens),
        ("reasoning_tokens", reasoning_tokens),
        ("estimated_cached_tokens", estimated_cached_tokens),
    ):
        if isinstance(value, int) and not isinstance(value, bool):
            record[key] = value
    if isinstance(estimated_cost, (int, float)) and not isinstance(
        estimated_cost, bool
    ):
        record["estimated_cost"] = float(estimated_cost)
    if isinstance(usage, dict) and usage:
        record["usage"] = usage
    if isinstance(rate_limits, dict) and rate_limits:
        record["rate_limits"] = rate_limits
    return append_journal_record(path, record)


def append_usage_reset(
    path: Path,
    *,
    source: str = "manual",
    timestamp: Optional[datetime] = None,
) -> bool:
    record: Dict[str, Any] = {
        "type": USAGE_RESET_RECORD_TYPE,
        "timestamp": isoformat_utc(timestamp or datetime.now(timezone.utc)),
        "source": source,
    }
    return append_journal_record(path, record)


def iter_journal_records(
    path: Path,
    *,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
) -> Iterator[Dict[str, Any]]:
    """Yield parsed journal records in file order, optionally date-filtered.

    Malformed lines are skipped. ``from_dt``/``to_dt`` are inclusive bounds
    compared against each record's ``timestamp``.
    """

    try:
        text = path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return
    except Exception:
        return
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            record = json.loads(line)
        except Exception:
            continue
        if (
            not isinstance(record, dict)
            or record.get("type") not in JOURNAL_RECORD_TYPES
        ):
            continue
        if from_dt is not None or to_dt is not None:
            observed_at = parse_iso8601(record.get("timestamp"))
            if observed_at is None:
                continue
            if from_dt is not None and observed_at < from_dt:
                continue
            if to_dt is not None and observed_at > to_dt:
                continue
        yield record


def record_rate_limits(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return the rate-limit snapshot payload carried by a journal record."""

    if not isinstance(record, dict):
        return None
    if record.get("type") == RATE_LIMIT_SNAPSHOT_RECORD_TYPE:
        snapshots = record.get("snapshots")
        if isinstance(snapshots, list) and snapshots:
            payload: Dict[str, Any] = {"snapshots": snapshots}
            if isinstance(record.get("plan_type"), str) and record.get("plan_type"):
                payload["plan_type"] = record.get("plan_type")
            return payload
        return None
    if record.get("type") == REQUEST_USAGE_RECORD_TYPE:
        rate_limits = record.get("rate_limits")
        if isinstance(rate_limits, dict) and rate_limits:
            return rate_limits
        return None
    return None


def totals_from_request_usage_records(
    records: List[Dict[str, Any]],
) -> Dict[str, Any]:
    totals: Dict[str, Any] = {
        "request_count": 0,
        "input_tokens": 0,
        "cached_tokens": 0,
        "cache_write_tokens": 0,
        "output_tokens": 0,
        "reasoning_tokens": 0,
        "estimated_cost": 0.0,
    }
    for record in records:
        if (
            not isinstance(record, dict)
            or record.get("type") != REQUEST_USAGE_RECORD_TYPE
        ):
            continue
        totals["request_count"] += 1
        for key in (
            "input_tokens",
            "cached_tokens",
            "cache_write_tokens",
            "output_tokens",
            "reasoning_tokens",
        ):
            value = record.get(key)
            if isinstance(value, int) and not isinstance(value, bool):
                totals[key] += value
        cost = record.get("estimated_cost")
        if isinstance(cost, (int, float)) and not isinstance(cost, bool):
            totals["estimated_cost"] += float(cost)
    return totals


def totals_since_last_reset(
    path: Path,
    *,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Sum request usage accumulated after the most recent reset marker.

    When ``from_dt``/``to_dt`` are given, only records inside the inclusive
    range contribute, but the reset marker is still located across the whole
    journal so a range crossing a reset reports only post-reset records.
    """

    reset_at: Optional[str] = None
    usage_records: List[Dict[str, Any]] = []
    for record in iter_journal_records(path):
        if record.get("type") == USAGE_RESET_RECORD_TYPE:
            reset_at = (
                record.get("timestamp")
                if isinstance(record.get("timestamp"), str)
                else None
            )
            usage_records = []
            continue
        if record.get("type") != REQUEST_USAGE_RECORD_TYPE:
            continue
        if from_dt is not None or to_dt is not None:
            observed_at = parse_iso8601(record.get("timestamp"))
            if observed_at is None:
                continue
            if from_dt is not None and observed_at < from_dt:
                continue
            if to_dt is not None and observed_at > to_dt:
                continue
        usage_records.append(record)

    totals = totals_from_request_usage_records(usage_records)
    totals["reset_at"] = reset_at
    return totals


def latest_rate_limits(
    path: Path,
    *,
    at_dt: Optional[datetime] = None,
) -> Optional[Dict[str, Any]]:
    """Return the most recent rate-limit snapshot payload in the journal.

    With ``at_dt``, only records at or before that moment are considered, so
    the left percentage and next reset time at a specific point in time can be
    reconstructed.
    """

    latest: Optional[Dict[str, Any]] = None
    for record in iter_journal_records(path):
        if at_dt is not None:
            observed_at = parse_iso8601(record.get("timestamp"))
            if observed_at is None or observed_at > at_dt:
                continue
        payload = record_rate_limits(record)
        if payload is not None:
            latest = payload
    return latest


def percent_history(
    path: Path,
    *,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Flatten snapshot windows into a chronological percent history.

    Each entry has ``timestamp``, ``limit_id``, ``window`` (``primary`` or
    ``secondary``), ``used_percent``, ``window_minutes``, and ``resets_at``.
    Entries are derived from both snapshot records and request records that
    carry a rate-limit payload.
    """

    history: List[Dict[str, Any]] = []
    for record in iter_journal_records(path, from_dt=from_dt, to_dt=to_dt):
        payload = record_rate_limits(record)
        if payload is None:
            continue
        timestamp = (
            record.get("timestamp")
            if isinstance(record.get("timestamp"), str)
            else None
        )
        snapshots = payload.get("snapshots")
        if not isinstance(snapshots, list):
            continue
        for snapshot in snapshots:
            if not isinstance(snapshot, dict):
                continue
            limit_id = snapshot.get("limit_id")
            for window_kind in ("primary", "secondary"):
                window = snapshot.get(window_kind)
                if not isinstance(window, dict):
                    continue
                used_percent = window.get("used_percent")
                if not isinstance(used_percent, (int, float)) or isinstance(
                    used_percent, bool
                ):
                    continue
                entry: Dict[str, Any] = {
                    "timestamp": timestamp,
                    "limit_id": (
                        limit_id if isinstance(limit_id, str) and limit_id else "codex"
                    ),
                    "window": window_kind,
                    "used_percent": float(used_percent),
                }
                if isinstance(window.get("window_minutes"), int):
                    entry["window_minutes"] = window.get("window_minutes")
                if isinstance(window.get("resets_at"), int):
                    entry["resets_at"] = window.get("resets_at")
                history.append(entry)
    return history


_CSV_FIELDNAMES = [
    "timestamp",
    "type",
    "limit_id",
    "window",
    "used_percent",
    "remaining_percent",
    "window_minutes",
    "resets_at",
    "plan_type",
    "response_id",
    "model",
    "service_tier",
    "input_tokens",
    "cached_tokens",
    "cache_write_tokens",
    "output_tokens",
    "reasoning_tokens",
    "estimated_cost",
]


def export_journal_csv(
    path: Path,
    target: Path,
    *,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
) -> int:
    """Export journal records to a CSV file for date-based inspection.

    Snapshot records expand to one row per limit window; request and reset
    records occupy a single row each. Returns the number of rows written.
    """

    rows: List[Dict[str, Any]] = []
    for record in iter_journal_records(path, from_dt=from_dt, to_dt=to_dt):
        timestamp = (
            record.get("timestamp") if isinstance(record.get("timestamp"), str) else ""
        )
        record_type = record.get("type")
        base: Dict[str, Any] = {"timestamp": timestamp, "type": record_type}
        if record_type == USAGE_RESET_RECORD_TYPE:
            rows.append(base)
            continue
        if record_type == REQUEST_USAGE_RECORD_TYPE:
            for key in (
                "response_id",
                "model",
                "service_tier",
                "input_tokens",
                "cached_tokens",
                "cache_write_tokens",
                "output_tokens",
                "reasoning_tokens",
                "estimated_cost",
            ):
                value = record.get(key)
                if value is not None:
                    base[key] = value
            rows.append(base)
            continue
        if record_type == RATE_LIMIT_SNAPSHOT_RECORD_TYPE:
            plan_type = record.get("plan_type")
            snapshots = record.get("snapshots")
            if not isinstance(snapshots, list):
                continue
            for snapshot in snapshots:
                if not isinstance(snapshot, dict):
                    continue
                limit_id = snapshot.get("limit_id")
                for window_kind in ("primary", "secondary"):
                    window = snapshot.get(window_kind)
                    if not isinstance(window, dict):
                        continue
                    row = dict(base)
                    row["limit_id"] = (
                        limit_id if isinstance(limit_id, str) and limit_id else "codex"
                    )
                    row["window"] = window_kind
                    used_percent = window.get("used_percent")
                    if isinstance(used_percent, (int, float)) and not isinstance(
                        used_percent, bool
                    ):
                        row["used_percent"] = used_percent
                        row["remaining_percent"] = 100.0 - float(used_percent)
                    if isinstance(window.get("window_minutes"), int):
                        row["window_minutes"] = window.get("window_minutes")
                    if isinstance(window.get("resets_at"), int):
                        row["resets_at"] = window.get("resets_at")
                    if isinstance(plan_type, str) and plan_type:
                        row["plan_type"] = plan_type
                    rows.append(row)

    target.parent.mkdir(parents=True, exist_ok=True)
    with open(target, "w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle, fieldnames=_CSV_FIELDNAMES, extrasaction="ignore"
        )
        writer.writeheader()
        for row in rows:
            writer.writerow(row)
    return len(rows)


__all__ = [
    "DEFAULT_CHATGPT_USAGE_JOURNAL_FILENAME",
    "DEFAULT_CHATGPT_USAGE_JOURNAL_RELATIVE_PATH",
    "JOURNAL_RECORD_TYPES",
    "RATE_LIMIT_SNAPSHOT_RECORD_TYPE",
    "REQUEST_USAGE_RECORD_TYPE",
    "USAGE_RESET_RECORD_TYPE",
    "append_journal_record",
    "append_rate_limit_snapshot",
    "append_request_usage",
    "append_usage_reset",
    "export_journal_csv",
    "iter_journal_records",
    "latest_rate_limits",
    "percent_history",
    "record_rate_limits",
    "resolve_usage_journal_path",
    "totals_from_request_usage_records",
    "totals_since_last_reset",
]
