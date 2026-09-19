from __future__ import annotations

import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from openai_responses_plugins.chatgpt_usage_journal import (
    append_rate_limit_snapshot,
    append_request_usage,
    append_usage_reset,
    export_journal_csv,
    iter_journal_records,
    latest_rate_limits,
    percent_history,
    resolve_usage_journal_path,
    totals_since_last_reset,
)


def _config(tmp_path: Path) -> dict:
    return {
        "chatgpt_credentials_path": str(tmp_path / "auth" / "chatgpt-auth.json"),
    }


def _snapshots(used_percent: float = 40.0) -> list[dict]:
    return [
        {
            "limit_id": "codex",
            "limit_name": "Codex",
            "primary": {
                "used_percent": used_percent,
                "window_minutes": 300,
                "resets_at": 1704069000,
            },
            "secondary": {
                "used_percent": 10.0,
                "window_minutes": 10080,
                "resets_at": 1705000000,
            },
            "credits": None,
        }
    ]


def test_journal_path_defaults_to_rate_limits_sibling(tmp_path: Path) -> None:
    path = resolve_usage_journal_path(_config(tmp_path))
    assert path == tmp_path / "auth" / "chatgpt-usage-journal.ndjson"


def test_journal_path_honors_explicit_override(tmp_path: Path) -> None:
    override = tmp_path / "elsewhere" / "journal.ndjson"
    config = {**_config(tmp_path), "chatgpt_usage_journal_path": str(override)}
    assert resolve_usage_journal_path(config) == override


def test_append_and_iterate_records(tmp_path: Path) -> None:
    path = resolve_usage_journal_path(_config(tmp_path))

    assert append_rate_limit_snapshot(
        path, snapshots=_snapshots(30.0), plan_type="plus"
    )
    assert append_request_usage(
        path,
        input_tokens=100,
        cached_tokens=20,
        output_tokens=10,
        reasoning_tokens=2,
        estimated_cost=0.001,
        model="gpt-5",
        response_id="resp_1",
        rate_limits={
            "captured_at": "2026-01-01T00:00:00Z",
            "snapshots": _snapshots(35.0),
        },
    )
    assert append_usage_reset(path)

    records = list(iter_journal_records(path))
    assert [record["type"] for record in records] == [
        "rate_limit_snapshot",
        "request_usage",
        "usage_reset",
    ]
    assert records[0]["plan_type"] == "plus"
    assert records[1]["input_tokens"] == 100
    assert records[1]["rate_limits"]["snapshots"][0]["primary"]["used_percent"] == 35.0


def test_append_is_append_only(tmp_path: Path) -> None:
    path = resolve_usage_journal_path(_config(tmp_path))
    for index in range(3):
        append_request_usage(path, input_tokens=index, estimated_cost=0.5)

    text = path.read_text(encoding="utf-8")
    lines = [line for line in text.splitlines() if line.strip()]
    assert len(lines) == 3
    assert [json.loads(line)["input_tokens"] for line in lines] == [0, 1, 2]


def test_malformed_and_unknown_lines_are_skipped(tmp_path: Path) -> None:
    path = resolve_usage_journal_path(_config(tmp_path))
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        "not json\n"
        '{"type": "unknown_thing"}\n'
        "\n"
        + json.dumps(
            {
                "type": "usage_reset",
                "timestamp": "2026-01-01T00:00:00Z",
                "source": "manual",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    records = list(iter_journal_records(path))
    assert [record["type"] for record in records] == ["usage_reset"]


def test_date_filtering_is_inclusive(tmp_path: Path) -> None:
    path = resolve_usage_journal_path(_config(tmp_path))
    base = datetime(2026, 1, 1, 12, 0, 0, tzinfo=timezone.utc)
    for hours in (0, 1, 2):
        append_request_usage(
            path,
            input_tokens=hours,
            timestamp=base + timedelta(hours=hours),
        )

    from_dt = base + timedelta(hours=1)
    to_dt = base + timedelta(hours=2)
    records = list(iter_journal_records(path, from_dt=from_dt, to_dt=to_dt))
    assert [record["input_tokens"] for record in records] == [1, 2]


def test_totals_since_last_reset(tmp_path: Path) -> None:
    path = resolve_usage_journal_path(_config(tmp_path))
    append_request_usage(path, input_tokens=100, output_tokens=10, estimated_cost=0.25)
    append_request_usage(path, input_tokens=50, output_tokens=5, estimated_cost=0.125)
    append_usage_reset(path)
    append_request_usage(path, input_tokens=7, output_tokens=3, estimated_cost=0.01)

    totals = totals_since_last_reset(path)
    assert totals["request_count"] == 1
    assert totals["input_tokens"] == 7
    assert totals["output_tokens"] == 3
    assert totals["estimated_cost"] == 0.01
    assert isinstance(totals["reset_at"], str)

    # Without any reset marker, all records contribute.
    path2 = path.with_name("journal2.ndjson")
    append_request_usage(path2, input_tokens=1, estimated_cost=0.5)
    append_request_usage(path2, input_tokens=2, estimated_cost=1.5)
    totals2 = totals_since_last_reset(path2)
    assert totals2["request_count"] == 2
    assert totals2["input_tokens"] == 3
    assert totals2["estimated_cost"] == 2.0
    assert totals2["reset_at"] is None


def test_totals_since_reset_with_date_range(tmp_path: Path) -> None:
    path = resolve_usage_journal_path(_config(tmp_path))
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    append_request_usage(path, input_tokens=1, timestamp=base)
    append_usage_reset(path, timestamp=base + timedelta(hours=1))
    append_request_usage(path, input_tokens=2, timestamp=base + timedelta(hours=2))
    append_request_usage(path, input_tokens=4, timestamp=base + timedelta(hours=3))

    totals = totals_since_last_reset(
        path,
        from_dt=base + timedelta(hours=1, minutes=30),
        to_dt=base + timedelta(hours=2, minutes=30),
    )
    assert totals["request_count"] == 1
    assert totals["input_tokens"] == 2


def test_latest_rate_limits_at_point_in_time(tmp_path: Path) -> None:
    path = resolve_usage_journal_path(_config(tmp_path))
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    append_rate_limit_snapshot(
        path,
        snapshots=_snapshots(10.0),
        captured_at=base,
    )
    append_rate_limit_snapshot(
        path,
        snapshots=_snapshots(60.0),
        captured_at=base + timedelta(hours=1),
    )

    at_dt = base + timedelta(minutes=30)
    snapshot = latest_rate_limits(path, at_dt=at_dt)
    assert snapshot is not None
    assert snapshot["snapshots"][0]["primary"]["used_percent"] == 10.0

    latest = latest_rate_limits(path)
    assert latest is not None
    assert latest["snapshots"][0]["primary"]["used_percent"] == 60.0


def test_latest_rate_limits_reads_request_record_snapshots(tmp_path: Path) -> None:
    path = resolve_usage_journal_path(_config(tmp_path))
    append_request_usage(
        path,
        input_tokens=1,
        rate_limits={"snapshots": _snapshots(77.0)},
    )
    snapshot = latest_rate_limits(path)
    assert snapshot is not None
    assert snapshot["snapshots"][0]["primary"]["used_percent"] == 77.0


def test_percent_history_flattens_windows(tmp_path: Path) -> None:
    path = resolve_usage_journal_path(_config(tmp_path))
    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    append_rate_limit_snapshot(path, snapshots=_snapshots(20.0), captured_at=base)
    append_request_usage(
        path,
        input_tokens=1,
        timestamp=base + timedelta(hours=1),
        rate_limits={"snapshots": _snapshots(45.0)},
    )

    history = percent_history(path)
    assert len(history) == 4
    assert [entry["used_percent"] for entry in history] == [20.0, 10.0, 45.0, 10.0]
    assert {entry["window"] for entry in history} == {"primary", "secondary"}
    assert all(entry["timestamp"] is not None for entry in history)


def test_export_journal_csv(tmp_path: Path) -> None:
    path = resolve_usage_journal_path(_config(tmp_path))
    append_rate_limit_snapshot(path, snapshots=_snapshots(25.0), plan_type="plus")
    append_request_usage(
        path,
        input_tokens=100,
        cached_tokens=20,
        output_tokens=10,
        estimated_cost=0.001,
        model="gpt-5",
        response_id="resp_1",
    )
    append_usage_reset(path)

    target = tmp_path / "export.csv"
    rows = export_journal_csv(path, target)
    assert rows == 4  # 2 snapshot windows + 1 request + 1 reset

    lines = target.read_text(encoding="utf-8").splitlines()
    header = lines[0].split(",")
    assert "timestamp" in header
    assert "used_percent" in header
    assert "estimated_cost" in header
    assert "remaining_percent" in header

    import csv

    with open(target, encoding="utf-8", newline="") as handle:
        parsed = list(csv.DictReader(handle))
    assert [row["type"] for row in parsed] == [
        "rate_limit_snapshot",
        "rate_limit_snapshot",
        "request_usage",
        "usage_reset",
    ]
    assert parsed[0]["remaining_percent"] == "75.0"
    assert parsed[2]["input_tokens"] == "100"
    assert parsed[2]["estimated_cost"] == "0.001"


def test_append_failures_are_swallowed(tmp_path: Path) -> None:
    # A path whose parent is a regular file cannot be created; appends must
    # fail softly rather than raise.
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    path = blocker / "sub" / "journal.ndjson"
    assert append_request_usage(path, input_tokens=1) is False
    assert append_rate_limit_snapshot(path, snapshots=_snapshots()) is False
    assert append_usage_reset(path) is False


def test_invalid_records_are_rejected(tmp_path: Path) -> None:
    path = resolve_usage_journal_path(_config(tmp_path))
    assert append_rate_limit_snapshot(path, snapshots=[]) is False
    assert append_rate_limit_snapshot(path, snapshots=[{"limit_id": "x"}]) is True
    # Missing/unknown type records are rejected without touching the file.
    from openai_responses_plugins.chatgpt_usage_journal import append_journal_record

    assert append_journal_record(path, {"type": "bogus"}) is False
    assert append_journal_record(path, {"no_type": True}) is False
