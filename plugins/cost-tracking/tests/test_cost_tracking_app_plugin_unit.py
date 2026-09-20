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
