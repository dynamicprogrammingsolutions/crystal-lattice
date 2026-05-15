from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from openai_responses_plugins.chatgpt_rate_limits import (
    limit_snapshot_is_stale,
    load_rate_limits_state,
    parse_all_rate_limit_headers,
    parse_rate_limit_for_limit,
    persist_rate_limit_snapshots,
    resolve_rate_limits_path,
)


def test_parse_rate_limit_for_default_codex_headers() -> None:
    snapshot = parse_rate_limit_for_limit(
        {
            "x-codex-primary-used-percent": "12.5",
            "x-codex-primary-window-minutes": "300",
            "x-codex-primary-reset-at": "1704069000",
            "x-codex-secondary-used-percent": "40.0",
            "x-codex-secondary-window-minutes": "10080",
            "x-codex-secondary-reset-at": "1704074400",
            "x-codex-credits-has-credits": "true",
            "x-codex-credits-unlimited": "false",
            "x-codex-credits-balance": "38",
        }
    )

    assert snapshot == {
        "limit_id": "codex",
        "limit_name": None,
        "primary": {
            "used_percent": 12.5,
            "window_minutes": 300,
            "resets_at": 1704069000,
        },
        "secondary": {
            "used_percent": 40.0,
            "window_minutes": 10080,
            "resets_at": 1704074400,
        },
        "credits": {
            "has_credits": True,
            "unlimited": False,
            "balance": "38",
        },
    }


def test_parse_all_rate_limit_headers_includes_extra_limit_family() -> None:
    snapshots = parse_all_rate_limit_headers(
        {
            "x-codex-primary-used-percent": "20",
            "x-codex-primary-window-minutes": "300",
            "x-codex-primary-reset-at": "1704069000",
            "x-codex-other-primary-used-percent": "88",
            "x-codex-other-primary-window-minutes": "43200",
            "x-codex-other-primary-reset-at": "1705000000",
            "x-codex-other-limit-name": "monthly",
        }
    )

    assert [snapshot["limit_id"] for snapshot in snapshots] == ["codex", "codex_other"]
    assert snapshots[1]["limit_name"] == "monthly"
    assert snapshots[1]["primary"]["window_minutes"] == 43200


def test_persist_rate_limit_snapshots_preserves_prior_credits_and_other_limits(tmp_path: Path) -> None:
    path = tmp_path / "auth" / "chatgpt-rate-limits.json"
    initial = persist_rate_limit_snapshots(
        path,
        [
            {
                "limit_id": "codex",
                "primary": {"used_percent": 10.0, "window_minutes": 300, "resets_at": 111},
                "secondary": None,
                "credits": {"has_credits": True, "unlimited": False, "balance": "25"},
            },
            {
                "limit_id": "codex_other",
                "limit_name": "monthly",
                "primary": {"used_percent": 50.0, "window_minutes": 43200, "resets_at": 222},
                "secondary": None,
                "credits": None,
            },
        ],
        captured_at=datetime(2026, 4, 12, 10, 0, tzinfo=timezone.utc),
        plan_type="plus",
    )
    assert initial["plan_type"] == "plus"

    updated = persist_rate_limit_snapshots(
        path,
        [
            {
                "limit_id": "codex",
                "primary": {"used_percent": 20.0, "window_minutes": 300, "resets_at": 333},
                "secondary": None,
                "credits": None,
            }
        ],
        captured_at=datetime(2026, 4, 12, 10, 5, tzinfo=timezone.utc),
    )

    snapshots = {snapshot["limit_id"]: snapshot for snapshot in updated["snapshots"]}
    assert snapshots["codex"]["primary"]["used_percent"] == 20.0
    assert snapshots["codex"]["credits"]["balance"] == "25"
    assert snapshots["codex_other"]["limit_name"] == "monthly"
    saved = json.loads(path.read_text(encoding="utf-8"))
    assert saved["plan_type"] == "plus"
    assert len(saved["snapshots"]) == 2


def test_resolve_rate_limits_path_defaults_next_to_credentials_path() -> None:
    path = resolve_rate_limits_path({"chatgpt_credentials_path": "/tmp/demo/chatgpt-auth.json"})
    assert str(path).endswith("/tmp/demo/chatgpt-rate-limits.json")


def test_limit_snapshot_is_stale_detects_old_capture_time(tmp_path: Path) -> None:
    path = tmp_path / "auth" / "chatgpt-rate-limits.json"
    persist_rate_limit_snapshots(
        path,
        [{"limit_id": "codex", "primary": {"used_percent": 10.0}}],
        captured_at=datetime.now(timezone.utc) - timedelta(minutes=20),
    )
    saved = load_rate_limits_state(path)
    assert limit_snapshot_is_stale(saved) is True