"""ChatGPT usage journal support for the chatgpt-auth-app plugin.

Self-contained reader/writer for the append-only ChatGPT usage journal
(``chatgpt-usage-journal.ndjson``) written by the ``openai_responses``
provider and usage extension. The journal records every captured ChatGPT
rate-limit snapshot, every ChatGPT-backed request's estimated usage together
with the rate-limit state observed on the same response, and manual reset
markers. This module reads those records to build usage reports and appends
reset markers; it never rewrites or truncates existing records.
"""

from __future__ import annotations

import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

DEFAULT_CHATGPT_RATE_LIMITS_FILENAME = "chatgpt-rate-limits.json"
DEFAULT_CHATGPT_USAGE_JOURNAL_FILENAME = "chatgpt-usage-journal.ndjson"
RATE_LIMIT_SNAPSHOT_RECORD_TYPE = "rate_limit_snapshot"
REQUEST_USAGE_RECORD_TYPE = "request_usage"
USAGE_RESET_RECORD_TYPE = "usage_reset"
JOURNAL_RECORD_TYPES = frozenset(
    {
        RATE_LIMIT_SNAPSHOT_RECORD_TYPE,
        REQUEST_USAGE_RECORD_TYPE,
        USAGE_RESET_RECORD_TYPE,
    }
)

_DATETIME_INPUT_FORMATS = (
    "%Y-%m-%d",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%d %H:%M:%S",
)

_write_lock = threading.Lock()


def resolve_rate_limits_path(config: Dict[str, Any]) -> Path:
    """Resolve the ChatGPT rate-limits file path (same chain as the app)."""

    raw = config.get("chatgpt_rate_limits_path")
    if isinstance(raw, str) and raw.strip():
        return Path(raw).expanduser()
    credentials_path = config.get("chatgpt_credentials_path")
    if isinstance(credentials_path, str) and credentials_path.strip():
        return (
            Path(credentials_path)
            .expanduser()
            .with_name(DEFAULT_CHATGPT_RATE_LIMITS_FILENAME)
        )
    config_dir = os.environ.get("CONFIG_DIR")
    if isinstance(config_dir, str) and config_dir:
        return (
            Path(config_dir).expanduser()
            / "auth"
            / DEFAULT_CHATGPT_RATE_LIMITS_FILENAME
        )
    return Path.cwd() / "auth" / DEFAULT_CHATGPT_RATE_LIMITS_FILENAME


def resolve_usage_journal_path(config: Dict[str, Any]) -> Path:
    raw = config.get("chatgpt_usage_journal_path")
    if isinstance(raw, str) and raw.strip():
        return Path(raw).expanduser()
    rate_limits_path = resolve_rate_limits_path(config)
    return rate_limits_path.with_name(DEFAULT_CHATGPT_USAGE_JOURNAL_FILENAME)


def parse_report_datetime(raw: Any) -> Optional[datetime]:
    """Parse a report date or date+time text input in the server's timezone.

    Accepts ``YYYY-MM-DD``, ``YYYY-MM-DD HH:MM``, ``YYYY-MM-DD HH:MM:SS``,
    and ISO ``T``-separated timestamps. Naive values are interpreted in the
    server's own timezone. Returns ``None`` when the text cannot be parsed.
    """

    if not isinstance(raw, str):
        return None
    text = raw.strip()
    if not text:
        return None
    for fmt in _DATETIME_INPUT_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt)
        except ValueError:
            continue
        return parsed.astimezone()
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        return parsed.astimezone()
    return parsed


def _parse_timestamp(raw: Any) -> Optional[datetime]:
    """Parse a journal record timestamp; naive values are treated as UTC."""

    if not isinstance(raw, str) or not raw.strip():
        return None
    text = raw.strip()
    if text.endswith("Z"):
        text = text[:-1] + "+00:00"
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def iter_journal_records(
    path: Path,
    *,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
) -> Iterator[Dict[str, Any]]:
    """Yield parsed journal records in file order, optionally date-filtered.

    ``from_dt``/``to_dt`` are inclusive bounds compared against each record's
    ``timestamp``. Malformed lines are skipped.
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
            observed_at = _parse_timestamp(record.get("timestamp"))
            if observed_at is None:
                continue
            if from_dt is not None and observed_at < from_dt:
                continue
            if to_dt is not None and observed_at > to_dt:
                continue
        yield record


def _record_in_range(
    record: Dict[str, Any],
    from_dt: Optional[datetime],
    to_dt: Optional[datetime],
) -> bool:
    if from_dt is None and to_dt is None:
        return True
    observed_at = _parse_timestamp(record.get("timestamp"))
    if observed_at is None:
        return False
    if from_dt is not None and observed_at < from_dt:
        return False
    if to_dt is not None and observed_at > to_dt:
        return False
    return True


def _record_rate_limits(record: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    if record.get("type") == RATE_LIMIT_SNAPSHOT_RECORD_TYPE:
        snapshots = record.get("snapshots")
        if isinstance(snapshots, list) and snapshots:
            return {"snapshots": snapshots}
        return None
    if record.get("type") == REQUEST_USAGE_RECORD_TYPE:
        rate_limits = record.get("rate_limits")
        if isinstance(rate_limits, dict) and rate_limits:
            return rate_limits
        return None
    return None


def totals_from_records(records: List[Dict[str, Any]]) -> Dict[str, Any]:
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


def percent_history_entries(
    records: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Flatten snapshot windows in the records into chronological entries."""

    entries: List[Dict[str, Any]] = []
    for record in records:
        payload = _record_rate_limits(record)
        if payload is None:
            continue
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
                entries.append(entry)
    return entries


def summarize_percent_history(
    entries: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Aggregate chronological percent entries per limit window."""

    grouped: Dict[Any, Dict[str, Any]] = {}
    order: List[Any] = []
    for entry in entries:
        key = (entry.get("limit_id"), entry.get("window"))
        summary = grouped.get(key)
        if summary is None:
            summary = {
                "limit_id": entry.get("limit_id"),
                "window": entry.get("window"),
                "window_minutes": entry.get("window_minutes"),
                "first_used_percent": entry.get("used_percent"),
                "last_used_percent": entry.get("used_percent"),
                "min_used_percent": entry.get("used_percent"),
                "max_used_percent": entry.get("used_percent"),
                "last_resets_at": entry.get("resets_at"),
            }
            grouped[key] = summary
            order.append(key)
            continue
        used = entry.get("used_percent")
        summary["last_used_percent"] = used
        summary["min_used_percent"] = min(summary["min_used_percent"], used)
        summary["max_used_percent"] = max(summary["max_used_percent"], used)
        summary["last_resets_at"] = entry.get("resets_at")
        if (
            summary.get("window_minutes") is None
            and entry.get("window_minutes") is not None
        ):
            summary["window_minutes"] = entry.get("window_minutes")
    return [grouped[key] for key in order]


def build_usage_report(
    path: Path,
    *,
    from_dt: Optional[datetime] = None,
    to_dt: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Build the structured data for a usage report.

    Without a date range the report covers usage accumulated since the most
    recent reset marker (or the journal start when no marker exists). With a
    date range the report covers the inclusive range instead.
    """

    all_records = list(iter_journal_records(path))

    reset_at: Optional[str] = None
    scoped: List[Dict[str, Any]] = []
    for record in all_records:
        if record.get("type") == USAGE_RESET_RECORD_TYPE:
            reset_at = (
                record.get("timestamp")
                if isinstance(record.get("timestamp"), str)
                else None
            )
            scoped = []
            continue
        if not _record_in_range(record, from_dt, to_dt):
            continue
        scoped.append(record)

    if from_dt is None and to_dt is None:
        usage_records = [
            r for r in scoped if r.get("type") == REQUEST_USAGE_RECORD_TYPE
        ]
        reset_boundary = reset_at
    else:
        usage_records = [
            r
            for r in all_records
            if r.get("type") == REQUEST_USAGE_RECORD_TYPE
            and _record_in_range(r, from_dt, to_dt)
        ]
        reset_boundary = None

    totals = totals_from_records(usage_records)

    latest_rate_limits: Optional[Dict[str, Any]] = None
    for record in scoped:
        payload = _record_rate_limits(record)
        if payload is not None:
            latest_rate_limits = payload

    percent_summary = summarize_percent_history(percent_history_entries(scoped))

    return {
        "from_dt": from_dt,
        "to_dt": to_dt,
        "reset_at": reset_boundary if (from_dt is None and to_dt is None) else None,
        "totals": totals,
        "latest_rate_limits": latest_rate_limits,
        "percent_summary": percent_summary,
        "record_count": len(all_records),
    }


def append_usage_reset(path: Path, *, source: str = "chatgpt_auth_app") -> bool:
    """Append a manual reset marker to the journal. Best-effort."""

    record = {
        "type": USAGE_RESET_RECORD_TYPE,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "source": source,
    }
    try:
        line = json.dumps(record, sort_keys=True)
        with _write_lock:
            path.parent.mkdir(parents=True, exist_ok=True)
            with open(path, "a", encoding="utf-8") as handle:
                handle.write(line + "\n")
        return True
    except Exception:
        return False


__all__ = [
    "DEFAULT_CHATGPT_USAGE_JOURNAL_FILENAME",
    "JOURNAL_RECORD_TYPES",
    "RATE_LIMIT_SNAPSHOT_RECORD_TYPE",
    "REQUEST_USAGE_RECORD_TYPE",
    "USAGE_RESET_RECORD_TYPE",
    "append_usage_reset",
    "build_usage_report",
    "iter_journal_records",
    "parse_report_datetime",
    "percent_history_entries",
    "resolve_usage_journal_path",
    "summarize_percent_history",
    "totals_from_records",
]
