from __future__ import annotations

import json
import os
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
    resolve_summary_csv_path,
    resolve_usage_journal_path,
    resolve_working_directory,
    session_id_from_state,
    summary_csv_enabled,
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


def test_journal_path_follows_crystal_data_dir_without_overrides(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("CRYSTAL_DATA_DIR", str(tmp_path / "data"))
    path = resolve_usage_journal_path({})
    assert path == tmp_path / "data" / "auth" / "chatgpt-usage-journal.ndjson"
    assert resolve_summary_csv_path({}) == (
        tmp_path / "data" / "auth" / "chatgpt-usage-summary.csv"
    )


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


def test_session_fields_are_recorded(tmp_path: Path) -> None:
    path = resolve_usage_journal_path(_config(tmp_path))
    assert append_rate_limit_snapshot(
        path,
        snapshots=_snapshots(30.0),
        session_id="session-a",
        working_directory="/work/repo",
    )
    assert append_request_usage(
        path,
        input_tokens=1,
        estimated_cost=0.01,
        session_id="session-a",
        working_directory="/work/repo",
    )

    records = list(iter_journal_records(path))
    assert [record["session_id"] for record in records] == ["session-a", "session-a"]
    assert [record["working_directory"] for record in records] == [
        "/work/repo",
        "/work/repo",
    ]


def test_session_fields_are_omitted_when_missing(tmp_path: Path) -> None:
    path = resolve_usage_journal_path(_config(tmp_path))
    assert append_rate_limit_snapshot(path, snapshots=_snapshots())
    assert append_request_usage(path, input_tokens=1)

    for record in iter_journal_records(path):
        assert "session_id" not in record
        assert "working_directory" not in record


def test_session_id_from_state_reads_request_context() -> None:
    assert session_id_from_state({"_request_context": {"session_id": "abc"}}) == "abc"
    assert session_id_from_state({"_request_context": {}}) is None
    assert session_id_from_state({}) is None
    assert session_id_from_state(None) is None
    assert session_id_from_state({"_request_context": "bogus"}) is None


def test_resolve_working_directory_is_absolute() -> None:
    absolute = resolve_working_directory({"working_directory": "/work/repo"})
    assert absolute == "/work/repo"

    relative = resolve_working_directory({"working_directory": "sub/dir"})
    assert relative == os.path.abspath("sub/dir")

    assert resolve_working_directory({"working_directory": "  "}) is None
    assert resolve_working_directory({"working_directory": 42}) is None
    assert resolve_working_directory({}) is None
    assert resolve_working_directory(None) is None


def _summary_config(tmp_path: Path) -> dict:
    return {
        "chatgpt_credentials_path": str(tmp_path / "auth" / "chatgpt-auth.json"),
    }


def test_summary_csv_path_defaults_to_journal_sibling(tmp_path: Path) -> None:
    config = _summary_config(tmp_path)
    assert (
        resolve_summary_csv_path(config)
        == tmp_path / "auth" / "chatgpt-usage-summary.csv"
    )

    override = tmp_path / "elsewhere" / "summary.csv"
    config = {**config, "chatgpt_usage_summary_csv_path": str(override)}
    assert resolve_summary_csv_path(config) == override


def test_summary_csv_enabled_defaults_on() -> None:
    assert summary_csv_enabled({}) is True
    assert summary_csv_enabled({"track_chatgpt_usage_summary_csv": True}) is True
    assert summary_csv_enabled({"track_chatgpt_usage_summary_csv": False}) is False
    assert summary_csv_enabled(None) is False


def _read_summary_rows(path: Path) -> list[dict]:
    import csv

    with open(path, encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def test_summary_csv_appended_per_record_with_totals(tmp_path: Path) -> None:
    config = _summary_config(tmp_path)
    path = resolve_usage_journal_path(config)
    csv_path = resolve_summary_csv_path(config)

    assert append_rate_limit_snapshot(
        path,
        snapshots=_snapshots(51.0),
        session_id="session-a",
        working_directory="/work/repo",
        config=config,
    )
    assert append_request_usage(
        path,
        input_tokens=100,
        output_tokens=10,
        estimated_cost=0.02,
        rate_limits={"snapshots": _snapshots(52.0)},
        session_id="session-a",
        working_directory="/work/repo",
        config=config,
    )
    assert append_usage_reset(path, config=config)
    assert append_request_usage(
        path,
        estimated_cost=0.01,
        session_id="session-b",
        config=config,
    )

    rows = _read_summary_rows(csv_path)
    assert len(rows) == 4
    assert list(rows[0].keys()) == [
        "time",
        "working_directory",
        "session_id",
        "estimated_cost",
        "total_cost",
        "used_percent",
    ]
    # Snapshot row: no request cost, current total, primary used percent.
    assert rows[0]["session_id"] == "session-a"
    assert rows[0]["working_directory"] == "/work/repo"
    assert rows[0]["estimated_cost"] == ""
    assert float(rows[0]["total_cost"]) == 0.0
    assert float(rows[0]["used_percent"]) == 51.0
    # Request row: its own cost is included in the since-reset total.
    assert float(rows[1]["estimated_cost"]) == 0.02
    assert float(rows[1]["total_cost"]) == 0.02
    assert float(rows[1]["used_percent"]) == 52.0
    # Reset row: totals start counting from zero again.
    assert rows[2]["estimated_cost"] == ""
    assert float(rows[2]["total_cost"]) == 0.0
    assert rows[2]["used_percent"] == ""
    # Post-reset request counts from the reset marker.
    assert float(rows[3]["estimated_cost"]) == 0.01
    assert float(rows[3]["total_cost"]) == 0.01
    assert rows[3]["session_id"] == "session-b"


def test_summary_csv_can_be_disabled(tmp_path: Path) -> None:
    config = {
        **_summary_config(tmp_path),
        "track_chatgpt_usage_summary_csv": False,
    }
    path = resolve_usage_journal_path(config)
    assert append_request_usage(path, input_tokens=1, config=config)
    assert append_usage_reset(path, config=config)
    assert not resolve_summary_csv_path(config).exists()


def test_summary_csv_skipped_without_config(tmp_path: Path) -> None:
    path = resolve_usage_journal_path(_summary_config(tmp_path))
    assert append_request_usage(path, input_tokens=1)
    assert not resolve_summary_csv_path(_summary_config(tmp_path)).exists()


def test_summary_csv_honors_path_override(tmp_path: Path) -> None:
    override = tmp_path / "custom" / "summary.csv"
    config = {
        **_summary_config(tmp_path),
        "chatgpt_usage_summary_csv_path": str(override),
    }
    path = resolve_usage_journal_path(config)
    assert append_request_usage(path, input_tokens=1, estimated_cost=0.5, config=config)
    rows = _read_summary_rows(override)
    assert len(rows) == 1
    assert float(rows[0]["total_cost"]) == 0.5


def test_export_journal_csv_includes_session_fields(tmp_path: Path) -> None:
    path = resolve_usage_journal_path(_config(tmp_path))
    assert append_request_usage(
        path,
        input_tokens=1,
        session_id="session-a",
        working_directory="/work/repo",
    )
    assert append_rate_limit_snapshot(
        path,
        snapshots=_snapshots(),
        session_id="session-a",
        working_directory="/work/repo",
    )

    target = tmp_path / "export.csv"
    export_journal_csv(path, target)
    rows = _read_summary_rows(target)
    assert all(row["session_id"] == "session-a" for row in rows)
    assert all(row["working_directory"] == "/work/repo" for row in rows)
