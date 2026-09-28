"""Unit tests for the cost tracking application plugin."""

from __future__ import annotations

from pathlib import Path

import pytest

from cost_tracking_plugins import cost_store
from cost_tracking_plugins.cost_tracking_app_plugin import CostTrackingAppPlugin


class _FakeApp:
    """Minimal AgentApplication stand-in exposing load_session."""

    def __init__(self, session_config: dict) -> None:
        self._session_config = session_config

    def load_session(self, session_id: str):
        if session_id != "session-1":
            return None
        return (None, self._session_config, None)


def _state(tmp_path: Path) -> dict:
    return {"config": {}}


def _session_config(tmp_path: Path) -> dict:
    return {"cost_tracking_db_path": str(tmp_path / "costs.sqlite3")}


def _seed(db_path: Path) -> None:
    cost_store.record_request_usage(
        db_path,
        bucket="openai-responses-chatgpt",
        session_id="s1",
        working_directory="/tmp/ws",
        estimated_cost=1.0,
        response_id="r1",
        time="2026-01-01T00:00:00+00:00",
    )
    cost_store.record_request_usage(
        db_path,
        bucket="openai-responses-api",
        session_id="s1",
        working_directory="/tmp/ws",
        estimated_cost=2.0,
        response_id="r2",
        time="2026-01-02T00:00:00+00:00",
    )


def test_ui_elements_contribute_report_and_reset_actions() -> None:
    plugin = CostTrackingAppPlugin()

    elements = plugin.get_ui_elements({})
    by_id = {element["id"]: element for element in elements}

    assert set(by_id) == {
        "cost_tracking_show_report",
        "cost_tracking_reset_bucket",
    }
    assert by_id["cost_tracking_show_report"]["action_id"] == "show_cost_report"
    reset_dialog = by_id["cost_tracking_reset_bucket"]["dialog"]
    assert reset_dialog["kind"] == "form"
    assert reset_dialog["inputs"][0]["name"] == "bucket"
    assert reset_dialog["inputs"][0]["required"] is True


def test_get_actions_declares_report_and_reset() -> None:
    actions = {
        action["id"]: action for action in CostTrackingAppPlugin().get_actions({})
    }

    assert set(actions) == {"show_cost_report", "reset_cost_tracking"}
    assert actions["reset_cost_tracking"]["inputs"]["bucket"]["required"] is True


def test_show_cost_report_lists_buckets_and_overall(tmp_path: Path) -> None:
    db_path = tmp_path / "costs.sqlite3"
    _seed(db_path)
    plugin = CostTrackingAppPlugin()
    app = _FakeApp(_session_config(tmp_path))

    result = plugin.execute_action(
        app, "show_cost_report", {"session_id": "session-1"}, None, _state(tmp_path)
    )

    report = result["report"]
    assert report["total_cost"] == pytest.approx(3.0)
    assert report["request_count"] == 2
    buckets = {entry["bucket"]: entry for entry in report["buckets"]}
    assert buckets["openai-responses-chatgpt"]["total_cost"] == pytest.approx(1.0)
    assert buckets["openai-responses-api"]["total_cost"] == pytest.approx(2.0)

    body = result["display"]["body"]
    assert "openai-responses-chatgpt" in body
    assert "`$3.000000`" in body


def test_show_cost_report_handles_empty_store(tmp_path: Path) -> None:
    plugin = CostTrackingAppPlugin()
    app = _FakeApp(_session_config(tmp_path))

    result = plugin.execute_action(
        app, "show_cost_report", {"session_id": "session-1"}, None, _state(tmp_path)
    )

    assert result["report"]["request_count"] == 0
    assert "No cost records yet." in result["display"]["body"]


def test_reset_cost_tracking_appends_marker_and_report_reflects_it(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "costs.sqlite3"
    _seed(db_path)
    plugin = CostTrackingAppPlugin()
    app = _FakeApp(_session_config(tmp_path))

    result = plugin.execute_action(
        app,
        "reset_cost_tracking",
        {"session_id": "session-1", "bucket": "openai-responses-chatgpt"},
        None,
        _state(tmp_path),
    )

    assert result["reset"]["bucket"] == "openai-responses-chatgpt"
    buckets = {entry["bucket"]: entry for entry in result["report"]["buckets"]}
    assert buckets["openai-responses-chatgpt"]["request_count"] == 0
    assert buckets["openai-responses-chatgpt"]["last_reset_at"] is not None
    assert buckets["openai-responses-api"]["request_count"] == 1
    assert "recorded history is preserved" in result["display"]["body"]

    # The reset also appends a marker row to the summary CSV beside the
    # store, so rolling bucket totals in the CSV restart visibly.
    import csv

    csv_path = db_path.with_name("cost-tracking-summary.csv")
    with open(csv_path, encoding="utf-8", newline="") as handle:
        rows = list(csv.DictReader(handle))
    assert len(rows) == 1
    assert rows[0]["bucket"] == "openai-responses-chatgpt"
    assert rows[0]["cost"] == ""
    assert float(rows[0]["bucket_total_cost"]) == 0.0


def test_reset_requires_bucket(tmp_path: Path) -> None:
    plugin = CostTrackingAppPlugin()
    app = _FakeApp(_session_config(tmp_path))

    with pytest.raises(ValueError):
        plugin.execute_action(
            app,
            "reset_cost_tracking",
            {"session_id": "session-1", "bucket": "  "},
            None,
            _state(tmp_path),
        )


def test_actions_require_session_id(tmp_path: Path) -> None:
    plugin = CostTrackingAppPlugin()
    app = _FakeApp(_session_config(tmp_path))

    with pytest.raises(ValueError):
        plugin.execute_action(app, "show_cost_report", {}, None, _state(tmp_path))


def test_unknown_session_raises_key_error(tmp_path: Path) -> None:
    plugin = CostTrackingAppPlugin()
    app = _FakeApp(_session_config(tmp_path))

    with pytest.raises(KeyError):
        plugin.execute_action(
            app,
            "show_cost_report",
            {"session_id": "missing"},
            None,
            _state(tmp_path),
        )


def test_db_path_falls_back_to_data_dir(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CRYSTAL_DATA_DIR", str(tmp_path / "data"))
    plugin = CostTrackingAppPlugin()
    app = _FakeApp({})

    db_path = plugin._db_path(app, _state(tmp_path), "session-1")

    assert db_path == tmp_path / "data" / "cost-tracking" / "cost-tracking.sqlite3"


def test_app_level_db_path_override(tmp_path: Path) -> None:
    plugin = CostTrackingAppPlugin()
    app = _FakeApp({})
    state = {"config": {"db_path": str(tmp_path / "override.sqlite3")}}

    db_path = plugin._db_path(app, state, "session-1")

    assert db_path == tmp_path / "override.sqlite3"


def test_unknown_action_raises_key_error(tmp_path: Path) -> None:
    plugin = CostTrackingAppPlugin()
    app = _FakeApp(_session_config(tmp_path))

    with pytest.raises(KeyError):
        plugin.execute_action(app, "bogus", {}, None, _state(tmp_path))


def test_show_cost_report_lists_top_sessions_and_projects(
    tmp_path: Path, monkeypatch
) -> None:
    db_path = tmp_path / "costs.sqlite3"
    cost_store.record_request_usage(
        db_path,
        bucket="openai-responses-chatgpt",
        session_id="s1",
        working_directory="/tmp/ws",
        estimated_cost=1.0,
        response_id="r1",
        time="2026-01-01T00:00:00+00:00",
    )
    cost_store.record_request_usage(
        db_path,
        bucket="openai-responses-chatgpt",
        session_id="s2",
        working_directory="/tmp/other",
        estimated_cost=2.0,
        response_id="r2",
        time="2026-01-02T00:00:00+00:00",
    )
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "projects.json").write_text(
        '{"projects": {"/tmp/ws": {"name": "workspace"}, '
        '"/tmp/other": {"name": "other-project"}}}',
        encoding="utf-8",
    )
    monkeypatch.setenv("CRYSTAL_DATA_DIR", str(data_dir))
    plugin = CostTrackingAppPlugin()
    app = _FakeApp(_session_config(tmp_path))

    result = plugin.execute_action(
        app, "show_cost_report", {"session_id": "session-1"}, None, _state(tmp_path)
    )

    assert [entry["session_id"] for entry in result["top_sessions"]] == ["s2", "s1"]
    assert [entry["working_directory"] for entry in result["top_projects"]] == [
        "/tmp/other",
        "/tmp/ws",
    ]
    body = result["display"]["body"]
    assert "### Top sessions" in body
    assert "### Top projects" in body
    # Working directories render as resolved project names.
    assert "other-project" in body
    assert "workspace" in body
    assert "`s2`" in body


def test_project_names_fall_back_to_raw_paths(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("CRYSTAL_DATA_DIR", str(tmp_path / "missing"))
    from cost_tracking_plugins.cost_tracking_app_plugin import _project_display_name

    assert _project_display_name("/tmp/ws") == "/tmp/ws"
    (tmp_path / "missing").mkdir()
    (tmp_path / "missing" / "projects.json").write_text("not json", encoding="utf-8")
    assert _project_display_name("/tmp/ws") == "/tmp/ws"


def _local_moment(days_ago: int, hour: int = 12) -> str:
    from datetime import datetime, timedelta

    moment = datetime.now().astimezone() - timedelta(days=days_ago)
    return moment.replace(hour=hour, minute=0, second=0, microsecond=0).isoformat()


def _seed_daily(db_path: Path) -> None:
    """Seed a 5-project, 2-bucket window plus one out-of-window row."""

    rows = [
        # (days_ago, working_directory, bucket, cost)
        (0, "/tmp/p1", "b1", 5.0),
        (0, "/tmp/p2", "b2", 4.0),
        (0, "/tmp/p3", "b1", 2.0),
        (2, "/tmp/p1", "b1", 3.0),
        (2, "/tmp/p4", "b2", 1.0),
        (2, "/tmp/p5", "b1", 0.5),
        (10, "/tmp/p1", "b1", 100.0),
    ]
    for index, (days_ago, working_directory, bucket, cost) in enumerate(rows):
        cost_store.record_request_usage(
            db_path,
            bucket=bucket,
            session_id=f"s{index}",
            working_directory=working_directory,
            model="m",
            estimated_cost=cost,
            response_id=f"r{index}",
            time=_local_moment(days_ago),
        )


def _table_rows(body: str, section: str) -> list:
    lines = body.splitlines()
    start = lines.index(f"### {section}") + 1
    rows = []
    for line in lines[start:]:
        if line.startswith("| "):
            rows.append(line)
        elif rows:
            break
    return rows


def test_show_cost_report_renders_daily_tables(tmp_path: Path, monkeypatch) -> None:
    db_path = tmp_path / "costs.sqlite3"
    _seed_daily(db_path)
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "projects.json").write_text(
        '{"projects": {"/tmp/p1": {"name": "alpha"}}}', encoding="utf-8"
    )
    monkeypatch.setenv("CRYSTAL_DATA_DIR", str(data_dir))
    plugin = CostTrackingAppPlugin()
    app = _FakeApp(_session_config(tmp_path))

    from datetime import datetime, timedelta

    today = datetime.now().astimezone().date().isoformat()
    two_days_ago = (datetime.now().astimezone().date() - timedelta(days=2)).isoformat()
    yesterday = (datetime.now().astimezone().date() - timedelta(days=1)).isoformat()

    result = plugin.execute_action(
        app, "show_cost_report", {"session_id": "session-1"}, None, _state(tmp_path)
    )

    body = result["display"]["body"]
    assert "### Last 7 days by project" in body
    assert "### Last 7 days by bucket" in body

    # Project columns: top 3 by window cost (alpha 8, p2 4, p3 2) plus a
    # Rest column aggregating p4 and p5.
    project_rows = _table_rows(body, "Last 7 days by project")
    assert project_rows[0] == "| Day | Total | alpha | /tmp/p2 | /tmp/p3 | Rest |"
    assert project_rows[8] == (
        f"| {today} | `$11.000000` | `$5.000000` | `$4.000000` | "
        "`$2.000000` | `$0.000000` |"
    )
    assert project_rows[6] == (
        f"| {two_days_ago} | `$4.500000` | `$3.000000` | `$0.000000` | "
        "`$0.000000` | `$1.500000` |"
    )
    # Seven zero-filled day rows.
    assert len(project_rows) == 9
    assert f"| {yesterday} | `$0.000000` | `$0.000000` | `$0.000000` | " in body

    # Bucket columns ranked by window cost: b1 (10.5) before b2 (5.0);
    # only two buckets, so no Rest column.
    bucket_rows = _table_rows(body, "Last 7 days by bucket")
    assert bucket_rows[0] == "| Day | Total | b1 | b2 |"

    assert result["daily_projects"][today]["/tmp/p1"] == pytest.approx(5.0)


def test_show_cost_report_daily_project_table_always_shown(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "costs.sqlite3"
    cost_store.record_request_usage(
        db_path,
        bucket="b1",
        session_id="s1",
        working_directory="/tmp/ws",
        estimated_cost=1.0,
        response_id="r1",
        time=_local_moment(0),
    )
    plugin = CostTrackingAppPlugin()
    app = _FakeApp(_session_config(tmp_path))

    result = plugin.execute_action(
        app, "show_cost_report", {"session_id": "session-1"}, None, _state(tmp_path)
    )

    body = result["display"]["body"]
    # Single project: the table still renders with one project column,
    # but the single-bucket daily table stays hidden.
    assert "### Last 7 days by project" in body
    assert "### Last 7 days by bucket" not in body
    project_rows = _table_rows(body, "Last 7 days by project")
    assert project_rows[0] == "| Day | Total | /tmp/ws |"
    assert "Rest" not in body


def test_show_cost_report_skips_daily_tables_without_window_data(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "costs.sqlite3"
    _seed(db_path)  # Rows from 2026-01-01: far outside the 7-day window.
    plugin = CostTrackingAppPlugin()
    app = _FakeApp(_session_config(tmp_path))

    result = plugin.execute_action(
        app, "show_cost_report", {"session_id": "session-1"}, None, _state(tmp_path)
    )

    body = result["display"]["body"]
    assert "Last 7 days by project" not in body
    assert "Last 7 days by bucket" not in body
