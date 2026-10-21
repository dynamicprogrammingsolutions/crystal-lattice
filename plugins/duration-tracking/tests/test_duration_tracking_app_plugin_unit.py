"""Unit tests for the duration tracking application plugin."""

from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from pathlib import Path
from typing import Any, Optional, Tuple

import pytest

from duration_tracking_plugins import duration_store
from duration_tracking_plugins.duration_tracking_app_plugin import (
    DurationTrackingAppPlugin,
)


class _FakeApp:
    """Minimal AgentApplication stand-in exposing load_session."""

    def __init__(self, session_config: dict) -> None:
        self._session_config = session_config

    def load_session(self, session_id: str) -> Optional[Tuple[Any, Any, Any]]:
        if session_id != "session-1":
            return None
        return (None, self._session_config, None)


class _FailOnSessionLoadApp:
    def load_session(self, session_id: str) -> None:
        raise AssertionError(f"human-time ingestion loaded session {session_id!r}")


def _state() -> dict:
    return {"config": {}}


def _session_config(tmp_path: Path) -> dict:
    return {
        "duration_tracking_db_path": str(tmp_path / "durations.sqlite3"),
        "working_directory": "/tmp/ws",
    }


def _local_time_iso(
    *,
    days_ago: int = 0,
    hour: int = 12,
    minute: int = 0,
) -> str:
    local_now = datetime.now().astimezone()
    local_day = local_now.date() - timedelta(days=days_ago)
    local_value = datetime.combine(local_day, time(hour, minute), local_now.tzinfo)
    return local_value.astimezone(timezone.utc).isoformat()


def _seed(db_path: Path) -> None:
    duration_store.record_request_duration(
        db_path,
        session_id="s1",
        working_directory="/tmp/ws",
        request_id="r1",
        duration_ms=500,
        time=_local_time_iso(hour=12),
    )
    duration_store.record_request_duration(
        db_path,
        session_id="s2",
        working_directory="/tmp/other",
        request_id="r2",
        duration_ms=1000,
        time=_local_time_iso(days_ago=1, hour=12),
    )
    duration_store.record_tool_duration(
        db_path,
        session_id="s2",
        working_directory="/tmp/other",
        request_id="r2",
        tool_call_id="call_1",
        tool_name="read_file",
        tool_plugin="file_reader_tool",
        duration_ms=250,
        time=_local_time_iso(days_ago=1, hour=12),
    )


def test_ui_elements_contribute_report_and_project_reset_actions() -> None:
    plugin = DurationTrackingAppPlugin()

    elements = plugin.get_ui_elements({})
    assert len(elements) == 2
    by_id = {element["id"]: element for element in elements}
    report = by_id["duration_tracking_show_report"]
    assert report["ui_type"] == "session_action"
    assert report["label"] == "Show duration report"
    assert report["action_id"] == "show_duration_report"
    assert report["param_map"] == {"session_id": "$session.session_id"}
    assert report["dialog"] == {"kind": "none"}
    reset = by_id["duration_tracking_reset_project"]
    assert reset["action_id"] == "reset_duration_tracking"
    assert reset["param_map"] == {"session_id": "$session.session_id"}
    assert reset["dialog"]["kind"] == "confirm"
    assert "Recorded history will be preserved" in reset["dialog"]["message"]


def test_get_actions_declares_report_ingestion_and_reset() -> None:
    actions = DurationTrackingAppPlugin().get_actions({})

    assert len(actions) == 3
    by_id = {action["id"]: action for action in actions}
    assert by_id["show_duration_report"]["inputs"]["session_id"]["required"] is True
    ingestion = by_id["record_human_time_spans"]
    assert ingestion["inputs"]["request_id"] == {"type": "string", "required": True}
    assert ingestion["inputs"]["spans"] == {"type": "array", "required": True}
    assert by_id["reset_duration_tracking"]["inputs"] == {
        "session_id": {"type": "string", "required": True}
    }


def test_init_defaults_application_working_directory_from_runtime(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("WORKING_DIR", "/tmp/runtime-workspace")
    plugin = DurationTrackingAppPlugin()

    defaulted = plugin.init({})
    configured = plugin.init(
        {"application": {"duration_tracking": {"working_directory": "/tmp/configured"}}}
    )

    assert defaulted["config"]["working_directory"] == "/tmp/runtime-workspace"
    assert configured["config"]["working_directory"] == "/tmp/configured"


def test_show_duration_report_renders_totals_and_tables(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    _seed(db_path)
    duration_store.record_human_time_spans(
        db_path,
        working_directory="/tmp/ws",
        request_id="human-ws",
        spans=[
            {
                "session_id": "s1",
                "from": _local_time_iso(hour=9),
                "to": _local_time_iso(hour=9, minute=10),
            },
            {
                "session_id": None,
                "from": _local_time_iso(hour=10),
                "to": _local_time_iso(hour=10, minute=5),
            },
        ],
    )
    duration_store.record_human_time_spans(
        db_path,
        working_directory="/tmp/other",
        request_id="human-other",
        spans=[
            {
                "session_id": "s2",
                "from": _local_time_iso(days_ago=1, hour=9),
                "to": _local_time_iso(days_ago=1, hour=9, minute=20),
            }
        ],
    )
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    (data_dir / "projects.json").write_text(
        '{"projects": {"/tmp/ws": {"name": "workspace"}, '
        '"/tmp/other": {"name": "other-project"}}}',
        encoding="utf-8",
    )
    monkeypatch.setenv("CRYSTAL_DATA_DIR", str(data_dir))
    plugin = DurationTrackingAppPlugin()
    app = _FakeApp(_session_config(tmp_path))

    result = plugin.execute_action(
        app, "show_duration_report", {"session_id": "session-1"}, None, _state()
    )

    report = result["report"]
    assert report == {
        "working_directory": "/tmp/ws",
        "last_reset_at": None,
        "request_count": 1,
        "llm_total_ms": 500,
        "tool_call_count": 0,
        "tool_total_ms": 0,
        "combined_total_ms": 500,
        "human_span_count": 2,
        "human_total_ms": 15 * 60 * 1000,
        "human_sessionless_span_count": 1,
        "human_sessionless_ms": 5 * 60 * 1000,
    }
    assert [entry["session_id"] for entry in result["top_sessions"]] == ["s1"]
    assert [entry["working_directory"] for entry in result["top_projects"]] == [
        "/tmp/other",
        "/tmp/ws",
    ]
    assert [entry["session_id"] for entry in result["top_sessions_last_7_days"]] == [
        "s2",
        "s1",
    ]
    assert [
        entry["session_id"]
        for entry in result["top_sessions_by_llm_project_since_reset"]
    ] == ["s1"]
    assert len(result["daily_totals_last_7_days"]) == 7

    body = result["display"]["body"]
    assert "## Duration report" in body
    assert "### Current project since reset" in body
    assert "- Project: `workspace`" in body
    assert "- Window: All recorded history" in body
    assert "- LLM duration: `500ms`" in body
    assert "- Tool duration: `0ms`" in body
    assert "- Human time: `15m`" in body
    assert "- Session-less human time: `5m`" in body
    assert "### Last 7 days" in body
    assert "| Day | LLM time | Tool time | Human time |" in body
    assert "### Top projects by human time — last 7 days" in body
    assert "### Top sessions by human time — current project since reset" in body
    assert "### Top sessions by human time — last 7 days" in body
    assert "### Top sessions by LLM duration — current project since reset" in body
    assert (
        "| Project | Human time | Session-less human | LLM time | Tool time |"
    ) in body
    assert "| Session | LLM duration | LLM calls | Tool time | Human time |" in body
    assert "other-project" in body
    assert "workspace" in body
    assert "`s2`" in body
    assert "Seven-day views use fixed calendar dates" in body


def test_show_duration_report_handles_empty_store(tmp_path: Path) -> None:
    plugin = DurationTrackingAppPlugin()
    app = _FakeApp(_session_config(tmp_path))

    result = plugin.execute_action(
        app, "show_duration_report", {"session_id": "session-1"}, None, _state()
    )

    assert result["report"] == {
        "working_directory": "/tmp/ws",
        "last_reset_at": None,
        "request_count": 0,
        "llm_total_ms": 0,
        "tool_call_count": 0,
        "tool_total_ms": 0,
        "combined_total_ms": 0,
        "human_span_count": 0,
        "human_total_ms": 0,
        "human_sessionless_span_count": 0,
        "human_sessionless_ms": 0,
    }
    assert "- LLM duration: `0ms`" in result["display"]["body"]
    assert "- Tool duration: `0ms`" in result["display"]["body"]
    assert "- LLM + tool duration: `0ms`" in result["display"]["body"]
    assert "- Human time: `0ms`" in result["display"]["body"]
    assert len(result["daily_totals_last_7_days"]) == 7
    assert len(result["daily_totals_project_last_7_days"]) == 7
    assert len(result["daily_totals_session_last_7_days"]) == 7


def test_show_duration_report_seven_day_tables_scope_project_and_session(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    _seed(db_path)
    duration_store.record_request_duration(
        db_path,
        session_id="session-1",
        working_directory="/tmp/ws",
        request_id="current-session",
        duration_ms=2000,
        time=_local_time_iso(hour=12),
    )
    duration_store.record_tool_duration(
        db_path,
        session_id="session-1",
        working_directory="/tmp/ws",
        request_id="current-session",
        tool_call_id="current-tool",
        duration_ms=1000,
        time=_local_time_iso(hour=12),
    )
    duration_store.record_human_time_spans(
        db_path,
        working_directory="/tmp/ws",
        request_id="current-human",
        spans=[
            {
                "session_id": "session-1",
                "from": _local_time_iso(hour=8),
                "to": _local_time_iso(hour=8, minute=1),
            },
            {
                "session_id": None,
                "from": _local_time_iso(hour=9),
                "to": _local_time_iso(hour=9, minute=2),
            },
        ],
    )
    duration_store.reset_project(
        db_path, working_directory="/tmp/ws", time=_local_time_iso(hour=13)
    )

    result = DurationTrackingAppPlugin().execute_action(
        _FakeApp(_session_config(tmp_path)),
        "show_duration_report",
        {"session_id": "session-1"},
        None,
        _state(),
    )

    today = datetime.now().astimezone().date().isoformat()
    assert result["daily_totals_project_last_7_days"][today] == {
        "llm_total_ms": 2500,
        "tool_total_ms": 1000,
        "human_total_ms": 180_000,
    }
    assert result["daily_totals_session_last_7_days"][today] == {
        "llm_total_ms": 2000,
        "tool_total_ms": 1000,
        "human_total_ms": 60_000,
    }
    assert (
        sum(row["llm_total_ms"] for row in result["daily_totals_last_7_days"].values())
        == 3500
    )
    assert result["report"]["llm_total_ms"] == 0
    body = result["display"]["body"]
    assert "### Last 7 days — current project" in body
    assert "### Last 7 days — current session" in body
    assert "Session: `session-1`" in body
    assert "### Last 7 days — all projects" in body
    assert body.count("| Day | LLM time | Tool time | Human time |") == 3
    assert "| **Total** | `2s` | `1s` | `1m` |" in body


def test_show_duration_report_includes_human_time_line(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    app = _FakeApp(
        {"duration_tracking_db_path": str(db_path), "working_directory": "/tmp/ws"}
    )
    duration_store.record_human_time_spans(
        db_path,
        working_directory="/tmp/ws",
        request_id="human-req-1",
        spans=[
            {
                "session_id": "session-1",
                "from": _local_time_iso(hour=8),
                "to": _local_time_iso(hour=8, minute=5),
            }
        ],
    )
    duration_store.record_human_time_spans(
        db_path,
        working_directory="/tmp/ws",
        request_id="human-req-2",
        spans=[
            {
                "session_id": None,
                "from": _local_time_iso(hour=9),
                "to": _local_time_iso(hour=9, minute=2),
            }
        ],
    )
    plugin = DurationTrackingAppPlugin()

    state = {
        "config": {
            "db_path": str(db_path),
            "working_directory": "/tmp/ws",
        }
    }
    result = plugin.execute_action(
        app, "show_duration_report", {"session_id": "session-1"}, None, state
    )

    body = result["display"]["body"]
    assert "- Human time: `7m`" in body
    assert "- Session-less human time: `2m`" in body
    assert "### Top projects by human time — last 7 days" in body
    assert "| /tmp/ws | `7m` | `2m` | `0ms` | `0ms` |" in body
    assert "### Top sessions by human time — current project since reset" in body
    assert "| `session-1` | `5m` | `0ms` | `0ms` |" in body
    assert "### Human time diagnostics" in body
    assert "- Session collection: `Ready`" in body
    assert "- Session-less collection: `Ready`" in body
    assert "- Storage targets: `Shared`" in body
    assert "- Current session stored total: `5m` across `1` stored span" in body
    assert "- Last upload received:" in body
    assert "`human-req-2`" in body
    assert result["human_time"] == {"span_count": 1, "total_ms": 5 * 60 * 1000}
    diagnostics = result["human_time_diagnostics"]
    assert diagnostics["session_collection_ready"] is True
    assert diagnostics["sessionless_collection_ready"] is True
    assert diagnostics["shared_store"] is True
    assert diagnostics["last_request_id"] == "human-req-2"
    assert result["human_time_summary"] == {
        "span_count": 2,
        "total_ms": 7 * 60 * 1000,
        "sessionless_span_count": 1,
        "sessionless_ms": 2 * 60 * 1000,
    }
    assert result["human_time_top_sessions"][0]["session_id"] == "session-1"
    assert result["human_time_top_sessions"][0]["human_total_ms"] == 5 * 60 * 1000
    assert result["human_time_top_projects"][0]["human_sessionless_ms"] == 2 * 60 * 1000


def test_show_duration_report_without_human_time_omits_line(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    _seed(db_path)
    app = _FakeApp(
        {"duration_tracking_db_path": str(db_path), "working_directory": "/tmp/ws"}
    )
    plugin = DurationTrackingAppPlugin()

    result = plugin.execute_action(
        app, "show_duration_report", {"session_id": "session-1"}, None, _state()
    )

    assert "- Human time: `0ms`" in result["display"]["body"]
    assert "### Human time diagnostics" in result["display"]["body"]
    assert result["human_time"] is None


def test_reset_duration_tracking_is_project_scoped_and_preserves_history(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    duration_store.record_request_duration(
        db_path,
        session_id="session-1",
        working_directory="/tmp/ws",
        request_id="before-reset",
        duration_ms=500,
        time="2026-09-28T12:00:00+00:00",
    )
    duration_store.record_request_duration(
        db_path,
        session_id="other-session",
        working_directory="/tmp/other",
        request_id="other-project",
        duration_ms=900,
        time="2026-09-28T13:00:00+00:00",
    )
    plugin = DurationTrackingAppPlugin()
    app = _FakeApp(_session_config(tmp_path))

    result = plugin.execute_action(
        app,
        "reset_duration_tracking",
        {"session_id": "session-1"},
        None,
        _state(),
    )

    assert result["reset"]["working_directory"] == "/tmp/ws"
    assert result["report"]["request_count"] == 0
    assert result["report"]["last_reset_at"] == result["reset"]["reset_at"]
    assert "Recorded history was preserved" in result["display"]["body"]
    assert "Seven-day cross-project views are unchanged" in result["display"]["body"]

    # Reset markers change report windows, not the factual recorded rows.
    assert duration_store.session_totals(
        db_path,
        working_directory="/tmp/ws",
        session_id="session-1",
    ) == {"request_count": 1, "total_ms": 500}
    assert (
        duration_store.project_totals_since_reset(
            db_path, working_directory="/tmp/other"
        )["llm_total_ms"]
        == 900
    )


def test_actions_require_session_id(tmp_path: Path) -> None:
    plugin = DurationTrackingAppPlugin()
    app = _FakeApp(_session_config(tmp_path))

    with pytest.raises(ValueError):
        plugin.execute_action(app, "show_duration_report", {}, None, _state())


def test_unknown_session_raises_key_error(tmp_path: Path) -> None:
    plugin = DurationTrackingAppPlugin()
    app = _FakeApp(_session_config(tmp_path))

    with pytest.raises(KeyError):
        plugin.execute_action(
            app,
            "show_duration_report",
            {"session_id": "missing"},
            None,
            _state(),
        )


def test_unknown_action_raises_key_error(tmp_path: Path) -> None:
    plugin = DurationTrackingAppPlugin()
    app = _FakeApp(_session_config(tmp_path))

    with pytest.raises(KeyError):
        plugin.execute_action(app, "bogus", {}, None, _state())


def test_db_path_falls_back_to_data_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CRYSTAL_DATA_DIR", str(tmp_path / "data"))
    plugin = DurationTrackingAppPlugin()
    app = _FakeApp({})

    db_path = plugin._db_path(app, _state(), "session-1")

    assert (
        db_path == tmp_path / "data" / "duration-tracking" / "duration-tracking.sqlite3"
    )


def test_app_level_db_path_override(tmp_path: Path) -> None:
    plugin = DurationTrackingAppPlugin()
    app = _FakeApp({})
    state = {"config": {"db_path": str(tmp_path / "override.sqlite3")}}

    db_path = plugin._db_path(app, state, "session-1")

    assert db_path == tmp_path / "override.sqlite3"


def test_session_db_path_override_wins_over_app_level(tmp_path: Path) -> None:
    plugin = DurationTrackingAppPlugin()
    session_override = str(tmp_path / "session.sqlite3")
    app = _FakeApp({"duration_tracking_db_path": session_override})
    state = {"config": {"db_path": str(tmp_path / "app-level.sqlite3")}}

    db_path = plugin._db_path(app, state, "session-1")

    assert db_path == tmp_path / "session.sqlite3"


def test_project_names_fall_back_to_raw_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CRYSTAL_DATA_DIR", str(tmp_path / "missing"))
    from duration_tracking_plugins.duration_tracking_app_plugin import (
        _project_display_name,
    )

    assert _project_display_name("/tmp/ws") == "/tmp/ws"
    (tmp_path / "missing").mkdir()
    (tmp_path / "missing" / "projects.json").write_text("not json", encoding="utf-8")
    assert _project_display_name("/tmp/ws") == "/tmp/ws"


# --- Human time span ingestion (subtask 030) ---


def _wd(raw: str) -> str:
    """Mirror the plugin's working-directory normalization for assertions."""

    import os

    return os.path.abspath(os.path.expanduser(raw))


def _ingest(
    plugin: DurationTrackingAppPlugin,
    app: Any,
    state: dict,
    spans: list,
    *,
    request_id: str = "req-1",
) -> dict:
    return plugin.execute_action(
        app,
        "record_human_time_spans",
        {"request_id": request_id, "spans": spans},
        None,
        state,
    )


def test_record_human_time_spans_uses_application_target_without_loading_sessions(
    tmp_path: Path,
) -> None:
    """All spans use the application plugin's store and server project."""

    app_db = tmp_path / "app.sqlite3"
    app = _FailOnSessionLoadApp()
    state = {
        "config": {
            "working_directory": "/tmp/app-ws",
            "db_path": str(app_db),
        }
    }
    plugin = DurationTrackingAppPlugin()

    result = _ingest(
        plugin,
        app,
        state,
        [
            {
                "session_id": "session-1",
                "from": "2026-09-25T08:00:00Z",
                "to": "2026-09-25T08:05:00Z",
            },
            {
                "session_id": None,
                "from": "2026-09-25T09:00:00Z",
                "to": "2026-09-25T09:02:00Z",
            },
        ],
    )

    assert result == {
        "recorded": 2,
        "merged": 0,
        "skipped": 0,
        "absorbed": 0,
        "duplicate": False,
    }
    assert duration_store.human_time_session_totals(
        app_db, working_directory=_wd("/tmp/app-ws"), session_id="session-1"
    ) == {"span_count": 1, "total_ms": 5 * 60 * 1000}
    assert duration_store.human_time_project_totals(
        app_db, working_directory=_wd("/tmp/app-ws")
    ) == {"span_count": 2, "total_ms": 7 * 60 * 1000}


def test_record_human_time_spans_duplicate_request(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    app = _FailOnSessionLoadApp()
    state = {
        "config": {
            "working_directory": "/tmp/ws",
            "db_path": str(db_path),
        }
    }
    plugin = DurationTrackingAppPlugin()

    first = _ingest(
        plugin,
        app,
        state,
        [
            {
                "session_id": "session-1",
                "from": "2026-09-25T08:00:00Z",
                "to": "2026-09-25T08:05:00Z",
            }
        ],
        request_id="r1",
    )
    assert first["recorded"] == 1
    assert first["duplicate"] is False

    # A retried batch (same request id) is recognized and skipped.
    retry = _ingest(
        plugin,
        app,
        state,
        [
            {
                "session_id": "session-1",
                "from": "2026-09-25T08:20:00Z",
                "to": "2026-09-25T08:25:00Z",
            }
        ],
        request_id="r1",
    )
    assert retry == {
        "recorded": 0,
        "merged": 0,
        "skipped": 0,
        "absorbed": 0,
        "duplicate": True,
    }
    assert duration_store.human_time_session_totals(
        db_path, working_directory=_wd("/tmp/ws"), session_id="session-1"
    ) == {"span_count": 1, "total_ms": 5 * 60 * 1000}


def test_record_human_time_spans_accepts_opaque_session_ids(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    app = _FailOnSessionLoadApp()
    state = {
        "config": {
            "working_directory": "/tmp/ws",
            "db_path": str(db_path),
        }
    }
    plugin = DurationTrackingAppPlugin()

    result = _ingest(
        plugin,
        app,
        state,
        [
            {
                "session_id": "missing-session",
                "from": "2026-09-25T08:00:00Z",
                "to": "2026-09-25T08:05:00Z",
            },
            {
                "session_id": "session-1",
                "from": "2026-09-25T08:10:00Z",
                "to": "2026-09-25T08:12:00Z",
            },
        ],
    )
    assert result["recorded"] == 2
    assert result["skipped"] == 0
    assert duration_store.human_time_session_totals(
        db_path, working_directory=_wd("/tmp/ws"), session_id="session-1"
    ) == {"span_count": 1, "total_ms": 2 * 60 * 1000}
    assert duration_store.human_time_session_totals(
        db_path, working_directory=_wd("/tmp/ws"), session_id="missing-session"
    ) == {"span_count": 1, "total_ms": 5 * 60 * 1000}


def test_record_human_time_spans_without_application_working_directory_fails(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    app = _FakeApp(
        {"duration_tracking_db_path": str(db_path), "working_directory": "/tmp/ws"}
    )
    # Missing application attribution is a configuration error, not a
    # span-level rejection that the uploader may discard.
    state = {"config": {}}
    plugin = DurationTrackingAppPlugin()

    with pytest.raises(ValueError, match="working_directory is not configured"):
        _ingest(
            plugin,
            app,
            state,
            [
                {
                    "session_id": None,
                    "from": "2026-09-25T09:00:00Z",
                    "to": "2026-09-25T09:02:00Z",
                }
            ],
        )


def test_record_human_time_spans_malformed_spans_skipped(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    app = _FailOnSessionLoadApp()
    state = {
        "config": {
            "working_directory": "/tmp/ws",
            "db_path": str(db_path),
        }
    }
    plugin = DurationTrackingAppPlugin()

    result = _ingest(
        plugin,
        app,
        state,
        [
            "not-a-dict",
            {
                "session_id": "session-1",
                "from": "not-a-date",
                "to": "2026-09-25T08:05:00Z",
            },
            {
                "session_id": "session-1",
                "from": "2026-09-25T08:00:00Z",
                "to": "2026-09-25T08:05:00Z",
            },
        ],
    )
    assert result["recorded"] == 0
    assert result["skipped"] == 2
    assert duration_store.human_time_session_totals(
        db_path, working_directory=_wd("/tmp/ws"), session_id="session-1"
    ) == {"span_count": 0, "total_ms": 0}


def test_record_human_time_spans_overlap_resolution_applies(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    app = _FailOnSessionLoadApp()
    state = {
        "config": {
            "working_directory": "/tmp/ws",
            "db_path": str(db_path),
        }
    }
    plugin = DurationTrackingAppPlugin()

    _ingest(
        plugin,
        app,
        state,
        [
            {
                "session_id": "session-1",
                "from": "2026-09-25T08:00:00Z",
                "to": "2026-09-25T08:10:00Z",
            }
        ],
        request_id="r1",
    )
    # The same session's overlapping span merges into one union entry.
    result = _ingest(
        plugin,
        app,
        state,
        [
            {
                "session_id": "session-1",
                "from": "2026-09-25T08:05:00Z",
                "to": "2026-09-25T08:15:00Z",
            }
        ],
        request_id="r2",
    )
    assert result["recorded"] == 1
    assert result["merged"] == 1
    assert duration_store.human_time_session_totals(
        db_path, working_directory=_wd("/tmp/ws"), session_id="session-1"
    ) == {"span_count": 1, "total_ms": 15 * 60 * 1000}


def test_record_human_time_spans_invalid_batch_raises(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    app = _FakeApp(
        {"duration_tracking_db_path": str(db_path), "working_directory": "/tmp/ws"}
    )
    state = {"config": {}}
    plugin = DurationTrackingAppPlugin()

    with pytest.raises(ValueError):
        plugin.execute_action(
            app,
            "record_human_time_spans",
            {"spans": []},
            None,
            state,
        )
    with pytest.raises(ValueError):
        plugin.execute_action(
            app,
            "record_human_time_spans",
            {"request_id": "r", "spans": {"a": 1}},
            None,
            state,
        )
    with pytest.raises(ValueError):
        plugin.execute_action(
            app,
            "record_human_time_spans",
            {
                "request_id": "r",
                "spans": [
                    {
                        "session_id": "session-1",
                        "from": "2026-09-25T08:00:00Z",
                        "to": "2026-09-25T08:01:00Z",
                    }
                ]
                * 1001,
            },
            None,
            state,
        )
