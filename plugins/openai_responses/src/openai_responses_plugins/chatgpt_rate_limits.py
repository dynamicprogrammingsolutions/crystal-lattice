from __future__ import annotations

import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional

from .chatgpt_credentials import (
    isoformat_utc,
    load_credentials,
    parse_iso8601,
    write_json_atomic,
)


DEFAULT_CHATGPT_RATE_LIMITS_RELATIVE_PATH = "auth/chatgpt-rate-limits.json"
RATE_LIMIT_STALE_THRESHOLD_MINUTES = 15


def resolve_rate_limits_path(config: Dict[str, Any]) -> Path:
    raw = config.get("chatgpt_rate_limits_path")
    if isinstance(raw, str) and raw.strip():
        return Path(raw).expanduser()

    credentials_path = config.get("chatgpt_credentials_path")
    if isinstance(credentials_path, str) and credentials_path.strip():
        return Path(credentials_path).expanduser().with_name("chatgpt-rate-limits.json")

    # Rate-limit snapshots are user-owned usage data, so they follow the
    # Crystal data directory rather than the active config file location
    # (``CONFIG_DIR`` can point at copied config assets, for example in the
    # cloud runtime).
    data_dir = os.environ.get("CRYSTAL_DATA_DIR")
    if isinstance(data_dir, str) and data_dir:
        return Path(data_dir).expanduser() / DEFAULT_CHATGPT_RATE_LIMITS_RELATIVE_PATH

    return Path.cwd() / DEFAULT_CHATGPT_RATE_LIMITS_RELATIVE_PATH


def load_rate_limits_state(path: Path) -> Dict[str, Any]:
    return load_credentials(path)


def _header_str(headers: Mapping[str, Any], name: str) -> Optional[str]:
    value = headers.get(name)
    if value is None:
        value = headers.get(name.lower())
    if value is None:
        return None
    if isinstance(value, bytes):
        try:
            decoded = value.decode("utf-8")
        except Exception:
            return None
        return decoded
    if isinstance(value, str):
        return value
    return str(value)


def _header_bool(headers: Mapping[str, Any], name: str) -> Optional[bool]:
    raw = _header_str(headers, name)
    if not isinstance(raw, str):
        return None
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes"}:
        return True
    if normalized in {"0", "false", "no"}:
        return False
    return None


def _header_int(headers: Mapping[str, Any], name: str) -> Optional[int]:
    raw = _header_str(headers, name)
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        return int(raw.strip())
    except ValueError:
        return None


def _header_float(headers: Mapping[str, Any], name: str) -> Optional[float]:
    raw = _header_str(headers, name)
    if not isinstance(raw, str) or not raw.strip():
        return None
    try:
        return float(raw.strip())
    except ValueError:
        return None


def _normalize_limit_id(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _header_name_to_limit_id(header_name: str) -> Optional[str]:
    lower = header_name.strip().lower()
    if not lower.startswith("x-"):
        return None
    for suffix in (
        "-primary-used-percent",
        "-primary-window-minutes",
        "-primary-reset-at",
        "-secondary-used-percent",
        "-secondary-window-minutes",
        "-secondary-reset-at",
        "-limit-name",
    ):
        if lower.endswith(suffix):
            limit = lower[2 : -len(suffix)]
            if limit:
                return _normalize_limit_id(limit)
    return None


def _parse_window(
    headers: Mapping[str, Any],
    *,
    prefix: str,
    kind: str,
) -> Optional[Dict[str, Any]]:
    used_percent = _header_float(headers, f"{prefix}-{kind}-used-percent")
    window_minutes = _header_int(headers, f"{prefix}-{kind}-window-minutes")
    resets_at = _header_int(headers, f"{prefix}-{kind}-reset-at")

    has_data = (
        used_percent is not None or window_minutes is not None or resets_at is not None
    )
    if not has_data:
        return None

    payload: Dict[str, Any] = {}
    if used_percent is not None:
        payload["used_percent"] = used_percent
    if window_minutes is not None:
        payload["window_minutes"] = window_minutes
    if resets_at is not None:
        payload["resets_at"] = resets_at
    return payload


def _parse_credits(headers: Mapping[str, Any]) -> Optional[Dict[str, Any]]:
    has_credits = _header_bool(headers, "x-codex-credits-has-credits")
    unlimited = _header_bool(headers, "x-codex-credits-unlimited")
    if has_credits is None or unlimited is None:
        return None
    balance = _header_str(headers, "x-codex-credits-balance")
    cleaned = balance.strip() if isinstance(balance, str) else None
    payload: Dict[str, Any] = {
        "has_credits": has_credits,
        "unlimited": unlimited,
        "balance": cleaned or None,
    }
    return payload


def parse_rate_limit_for_limit(
    headers: Mapping[str, Any],
    limit_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    normalized_limit = _normalize_limit_id(limit_id or "codex").replace("_", "-")
    prefix = f"x-{normalized_limit}"
    primary = _parse_window(headers, prefix=prefix, kind="primary")
    secondary = _parse_window(headers, prefix=prefix, kind="secondary")
    credits = _parse_credits(headers)
    limit_name = _header_str(headers, f"{prefix}-limit-name")
    if isinstance(limit_name, str):
        limit_name = limit_name.strip() or None

    if primary is None and secondary is None and credits is None:
        return None

    return {
        "limit_id": _normalize_limit_id(limit_id or "codex"),
        "limit_name": limit_name,
        "primary": primary,
        "secondary": secondary,
        "credits": credits,
    }


def parse_all_rate_limit_headers(headers: Mapping[str, Any]) -> List[Dict[str, Any]]:
    snapshots: List[Dict[str, Any]] = []
    default_snapshot = parse_rate_limit_for_limit(headers)
    if default_snapshot is not None:
        snapshots.append(default_snapshot)

    extra_limit_ids = sorted(
        {
            limit_id
            for key in headers.keys()
            if isinstance(key, str)
            for limit_id in [_header_name_to_limit_id(key)]
            if isinstance(limit_id, str) and limit_id != "codex"
        }
    )
    for limit_id in extra_limit_ids:
        snapshot = parse_rate_limit_for_limit(headers, limit_id=limit_id)
        if snapshot is not None:
            snapshots.append(snapshot)

    return snapshots


def _merge_snapshot(
    existing: Dict[str, Any], incoming: Dict[str, Any]
) -> Dict[str, Any]:
    merged = dict(existing)
    merged["limit_id"] = incoming.get("limit_id") or existing.get("limit_id")
    merged["limit_name"] = incoming.get("limit_name") or existing.get("limit_name")
    merged["primary"] = incoming.get("primary")
    merged["secondary"] = incoming.get("secondary")
    merged["credits"] = (
        incoming.get("credits")
        if incoming.get("credits") is not None
        else existing.get("credits")
    )
    merged["plan_type"] = incoming.get("plan_type") or existing.get("plan_type")
    return merged


def persist_rate_limit_snapshots(
    path: Path,
    snapshots: List[Dict[str, Any]],
    *,
    captured_at: Optional[datetime] = None,
    plan_type: Any = None,
    source: str = "x-codex-headers",
) -> Dict[str, Any]:
    existing = load_rate_limits_state(path)
    existing_snapshots = existing.get("snapshots")
    existing_by_id: Dict[str, Dict[str, Any]] = {}
    if isinstance(existing_snapshots, list):
        for snapshot in existing_snapshots:
            if not isinstance(snapshot, dict):
                continue
            limit_id = snapshot.get("limit_id")
            if isinstance(limit_id, str) and limit_id:
                existing_by_id[limit_id] = snapshot

    merged_by_id = dict(existing_by_id)
    for snapshot in snapshots:
        if not isinstance(snapshot, dict):
            continue
        limit_id = snapshot.get("limit_id")
        if not isinstance(limit_id, str) or not limit_id:
            continue
        incoming = dict(snapshot)
        if isinstance(plan_type, str) and plan_type:
            incoming["plan_type"] = plan_type
        previous = merged_by_id.get(limit_id)
        merged_by_id[limit_id] = (
            _merge_snapshot(previous, incoming)
            if isinstance(previous, dict)
            else incoming
        )

    next_state = {
        "captured_at": isoformat_utc(captured_at or datetime.now(timezone.utc)),
        "source": source,
        "snapshots": list(merged_by_id.values()),
    }
    if isinstance(plan_type, str) and plan_type:
        next_state["plan_type"] = plan_type
    elif isinstance(existing.get("plan_type"), str) and existing.get("plan_type"):
        next_state["plan_type"] = existing.get("plan_type")

    write_json_atomic(path, next_state)
    return next_state


def limit_snapshot_is_stale(
    rate_limits_state: Dict[str, Any], *, now: Optional[datetime] = None
) -> bool:
    captured_at = parse_iso8601(rate_limits_state.get("captured_at"))
    if captured_at is None:
        return False
    observed_at = now or datetime.now(timezone.utc)
    return observed_at - captured_at > timedelta(
        minutes=RATE_LIMIT_STALE_THRESHOLD_MINUTES
    )


__all__ = [
    "DEFAULT_CHATGPT_RATE_LIMITS_RELATIVE_PATH",
    "RATE_LIMIT_STALE_THRESHOLD_MINUTES",
    "limit_snapshot_is_stale",
    "load_rate_limits_state",
    "parse_all_rate_limit_headers",
    "parse_rate_limit_for_limit",
    "persist_rate_limit_snapshots",
    "resolve_rate_limits_path",
]
