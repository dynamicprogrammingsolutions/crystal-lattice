"""Unit tests for the cost tracking SQLite store."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from cost_tracking_plugins import cost_store


def _record(db_path: Path, bucket: str = "b1", **overrides):
    params = {
        "bucket": bucket,
        "session_id": "s1",
        "working_directory": "/tmp/ws",
        "model": "m",
        "response_id": None,
        "input_tokens": 100,
        "cached_tokens": 10,
        "cache_write_tokens": None,
        "output_tokens": 20,
        "reasoning_tokens": 5,
        "estimated_cost": 0.5,
        "actual_cost": None,
    }
    params.update(overrides)
    return cost_store.record_request_usage(db_path, **params)


def test_record_and_session_totals(tmp_path: Path) -> None:
    db_path = tmp_path / "costs.sqlite3"

    assert _record(db_path, response_id="r1") is True
    assert _record(db_path, response_id="r2", estimated_cost=0.25) is True

    totals = cost_store.session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    assert totals["request_count"] == 2
    assert totals["total_cost"] == pytest.approx(0.75)


def test_record_dedupes_by_response_id(tmp_path: Path) -> None:
    db_path = tmp_path / "costs.sqlite3"

    assert _record(db_path, response_id="r1") is True
    assert _record(db_path, response_id="r1", estimated_cost=999.0) is False

    totals = cost_store.session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    assert totals["request_count"] == 1
    assert totals["total_cost"] == pytest.approx(0.5)


def test_session_totals_prefer_actual_cost(tmp_path: Path) -> None:
    db_path = tmp_path / "costs.sqlite3"

    _record(db_path, response_id="r1", estimated_cost=0.5, actual_cost=0.2)
    _record(db_path, response_id="r2", estimated_cost=0.3)

    totals = cost_store.session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    assert totals["total_cost"] == pytest.approx(0.2 + 0.3)


def test_session_totals_filter_by_workspace_and_session(tmp_path: Path) -> None:
    db_path = tmp_path / "costs.sqlite3"

    _record(db_path, response_id="r1")
    _record(db_path, response_id="r2", session_id="s2")
    _record(db_path, response_id="r3", working_directory="/tmp/other")

    totals = cost_store.session_totals(
        db_path, working_directory="/tmp/ws", session_id="s1"
    )
    assert totals["request_count"] == 1
    # The same session id in a different workspace stays separate.
    other = cost_store.session_totals(
        db_path, working_directory="/tmp/other", session_id="s1"
    )
    assert other["request_count"] == 1


def test_bucket_report_is_reset_aware(tmp_path: Path) -> None:
    db_path = tmp_path / "costs.sqlite3"

    _record(
        db_path,
        bucket="b1",
        response_id="r1",
        estimated_cost=1.0,
        time="2026-01-01T00:00:00+00:00",
    )
    _record(
        db_path,
        bucket="b1",
        response_id="r2",
        estimated_cost=2.0,
        time="2026-01-02T00:00:00+00:00",
    )
    _record(
        db_path,
        bucket="b2",
        response_id="r3",
        estimated_cost=4.0,
        time="2026-01-03T00:00:00+00:00",
    )

    report = cost_store.bucket_report(db_path)
    assert report["total_cost"] == pytest.approx(7.0)
    assert report["request_count"] == 3
    by_bucket = {entry["bucket"]: entry for entry in report["buckets"]}
    assert by_bucket["b1"]["total_cost"] == pytest.approx(3.0)

    cost_store.reset_bucket(db_path, bucket="b1", time="2026-01-01T12:00:00+00:00")

    report = cost_store.bucket_report(db_path)
    by_bucket = {entry["bucket"]: entry for entry in report["buckets"]}
    # Only the post-reset b1 record counts; b2 is untouched.
    assert by_bucket["b1"]["total_cost"] == pytest.approx(2.0)
    assert by_bucket["b1"]["request_count"] == 1
    assert by_bucket["b1"]["last_reset_at"] == "2026-01-01T12:00:00+00:00"
    assert by_bucket["b2"]["total_cost"] == pytest.approx(4.0)
    assert report["total_cost"] == pytest.approx(6.0)
    assert report["request_count"] == 2


def test_reset_bucket_requires_bucket(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        cost_store.reset_bucket(tmp_path / "costs.sqlite3", bucket="  ")


def test_record_requires_bucket(tmp_path: Path) -> None:
    with pytest.raises(ValueError):
        cost_store.record_request_usage(tmp_path / "costs.sqlite3", bucket="")


def test_known_buckets(tmp_path: Path) -> None:
    db_path = tmp_path / "costs.sqlite3"
    assert cost_store.known_buckets(db_path) == []
    _record(db_path, bucket="b2", response_id="r1")
    _record(db_path, bucket="b1", response_id="r2")
    assert cost_store.known_buckets(db_path) == ["b1", "b2"]


def test_resolve_cost_db_path_prefers_explicit_override(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("CRYSTAL_DATA_DIR", str(tmp_path / "data"))
    override = tmp_path / "elsewhere" / "costs.sqlite3"
    assert (
        cost_store.resolve_cost_db_path({"cost_tracking_db_path": str(override)})
        == override
    )


def test_resolve_cost_db_path_follows_crystal_data_dir(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setenv("CRYSTAL_DATA_DIR", str(tmp_path / "data"))
    assert cost_store.resolve_cost_db_path({}) == (
        tmp_path / "data" / "cost-tracking" / "cost-tracking.sqlite3"
    )


def test_resolve_cost_db_path_falls_back_to_cwd(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.delenv("CRYSTAL_DATA_DIR", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(os, "getcwd", lambda: str(tmp_path))
    assert cost_store.resolve_cost_db_path(None) == (
        tmp_path / "cost-tracking" / "cost-tracking.sqlite3"
    )


def _csv_rows(csv_path: Path) -> list[dict]:
    import csv as csv_module

    with open(csv_path, encoding="utf-8", newline="") as handle:
        return list(csv_module.DictReader(handle))


def _summary_csv_path(db_path: Path) -> Path:
    return db_path.with_name("cost-tracking-summary.csv")


def _record_and_summarize(db_path: Path, config=None, **overrides):
    params = {
        "bucket": "b1",
        "session_id": "s1",
        "working_directory": "/tmp/ws",
        "model": "m",
        "response_id": None,
        "estimated_cost": 0.5,
        "actual_cost": None,
    }
    params.update(overrides)
    recorded = cost_store.record_request_usage(db_path, **params)
    appended = cost_store.append_request_summary_csv(
        db_path,
        config,
        bucket=params["bucket"],
        session_id=params["session_id"],
        working_directory=params["working_directory"],
        model=params["model"],
        cost=(
            params["actual_cost"]
            if params["actual_cost"] is not None
            else params["estimated_cost"]
        ),
    )
    return recorded, appended


def test_summary_csv_appends_request_rows_with_rolling_totals(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "costs.sqlite3"

    _record_and_summarize(db_path, response_id="r1", estimated_cost=0.5)
    _record_and_summarize(db_path, response_id="r2", estimated_cost=0.25)

    rows = _csv_rows(_summary_csv_path(db_path))
    assert len(rows) == 2
    assert rows[0]["bucket"] == "b1"
    assert rows[0]["session_id"] == "s1"
    assert rows[0]["working_directory"] == "/tmp/ws"
    assert float(rows[0]["cost"]) == pytest.approx(0.5)
    assert float(rows[0]["session_total_cost"]) == pytest.approx(0.5)
    assert float(rows[0]["bucket_total_cost"]) == pytest.approx(0.5)
    assert float(rows[1]["cost"]) == pytest.approx(0.25)
    assert float(rows[1]["session_total_cost"]) == pytest.approx(0.75)
    assert float(rows[1]["bucket_total_cost"]) == pytest.approx(0.75)


def test_summary_csv_bucket_total_is_reset_aware(tmp_path: Path) -> None:
    db_path = tmp_path / "costs.sqlite3"

    _record_and_summarize(db_path, response_id="r1", estimated_cost=0.5)
    cost_store.reset_bucket(db_path, bucket="b1")
    _record_and_summarize(db_path, response_id="r2", estimated_cost=0.25)

    rows = _csv_rows(_summary_csv_path(db_path))
    assert len(rows) == 2
    # Session totals are factual history and keep growing across resets.
    assert float(rows[1]["session_total_cost"]) == pytest.approx(0.75)
    # Bucket totals restart after the reset marker.
    assert float(rows[1]["bucket_total_cost"]) == pytest.approx(0.25)


def test_append_reset_summary_csv_writes_marker_row(tmp_path: Path) -> None:
    db_path = tmp_path / "costs.sqlite3"
    _record_and_summarize(db_path, response_id="r1")

    assert cost_store.append_reset_summary_csv(db_path, None, bucket="b1") is True
    rows = _csv_rows(_summary_csv_path(db_path))
    assert len(rows) == 2
    marker = rows[-1]
    assert marker["bucket"] == "b1"
    assert marker["cost"] == ""
    assert marker["session_id"] == ""
    assert float(marker["bucket_total_cost"]) == pytest.approx(0.0)


def test_summary_csv_row_without_session_fields(tmp_path: Path) -> None:
    db_path = tmp_path / "costs.sqlite3"

    cost_store.record_request_usage(
        db_path, bucket="b1", estimated_cost=0.5, response_id="r1"
    )
    assert (
        cost_store.append_request_summary_csv(db_path, None, bucket="b1", cost=0.5)
        is True
    )

    rows = _csv_rows(_summary_csv_path(db_path))
    assert len(rows) == 1
    assert rows[0]["session_id"] == ""
    assert rows[0]["session_total_cost"] == ""
    assert float(rows[0]["bucket_total_cost"]) == pytest.approx(0.5)


def test_summary_csv_disabled_by_config(tmp_path: Path) -> None:
    db_path = tmp_path / "costs.sqlite3"
    config = {"track_cost_tracking_summary_csv": False}

    cost_store.record_request_usage(
        db_path, bucket="b1", estimated_cost=0.5, response_id="r1"
    )
    assert (
        cost_store.append_request_summary_csv(db_path, config, bucket="b1", cost=0.5)
        is False
    )
    assert not _summary_csv_path(db_path).exists()


def test_summary_csv_path_override(tmp_path: Path) -> None:
    db_path = tmp_path / "costs.sqlite3"
    csv_path = tmp_path / "elsewhere" / "summary.csv"
    config = {"cost_tracking_summary_csv_path": str(csv_path)}

    cost_store.record_request_usage(
        db_path, bucket="b1", estimated_cost=0.5, response_id="r1"
    )
    assert (
        cost_store.append_request_summary_csv(
            db_path,
            config,
            bucket="b1",
            session_id="s1",
            working_directory="/tmp/ws",
            cost=0.5,
        )
        is True
    )
    assert len(_csv_rows(csv_path)) == 1


def test_summary_csv_best_effort_on_unwritable_path(tmp_path: Path) -> None:
    db_path = tmp_path / "costs.sqlite3"
    blocker = tmp_path / "blocker"
    blocker.write_text("not a directory", encoding="utf-8")
    config = {"cost_tracking_summary_csv_path": str(blocker / "summary.csv")}

    cost_store.record_request_usage(
        db_path, bucket="b1", estimated_cost=0.5, response_id="r1"
    )
    assert (
        cost_store.append_request_summary_csv(db_path, config, bucket="b1", cost=0.5)
        is False
    )


def test_bucket_total_since_reset_matches_report(tmp_path: Path) -> None:
    db_path = tmp_path / "costs.sqlite3"

    _record(db_path, response_id="r1")
    cost_store.reset_bucket(db_path, bucket="b1")
    _record(db_path, response_id="r2", estimated_cost=0.25)

    totals = cost_store.bucket_total_since_reset(db_path, bucket="b1")
    assert totals["request_count"] == 1
    assert totals["total_cost"] == pytest.approx(0.25)
    assert totals["last_reset_at"] is not None
