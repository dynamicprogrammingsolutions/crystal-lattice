"""Unit tests for the duration tracking application plugin."""

from __future__ import annotations

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


def _state() -> dict:
    return {"config": {}}


def _session_config(tmp_path: Path) -> dict:
    return {"duration_tracking_db_path": str(tmp_path / "durations.sqlite3")}


def _seed(db_path: Path) -> None:
    duration_store.record_request_duration(
        db_path,
        session_id="s1",
        working_directory="/tmp/ws",
        request_id="r1",
        duration_ms=500,
        time="2026-01-01T00:00:00+00:00",
    )
    duration_store.record_request_duration(
        db_path,
        session_id="s2",
        working_directory="/tmp/other",
        request_id="r2",
        duration_ms=1000,
        time="2026-01-02T00:00:00+00:00",
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
        time="2026-01-02T00:00:00+00:00",
    )


def test_ui_elements_contribute_report_action() -> None:
    plugin = DurationTrackingAppPlugin()

    elements = plugin.get_ui_elements({})
    assert len(elements) == 1
    element = elements[0]
    assert element["ui_type"] == "session_action"
    assert element["id"] == "duration_tracking_show_report"
    assert element["label"] == "Show duration report"
    assert element["action_id"] == "show_duration_report"
    assert element["param_map"] == {"session_id": "$session.session_id"}
    assert element["dialog"] == {"kind": "none"}


def test_get_actions_declares_report_and_ingestion() -> None:
    actions = DurationTrackingAppPlugin().get_actions({})

    assert len(actions) == 2
    by_id = {action["id"]: action for action in actions}
    assert by_id["show_duration_report"]["inputs"]["session_id"]["required"] is True
    ingestion = by_id["record_human_time_spans"]
    assert ingestion["inputs"]["request_id"] == {"type": "string", "required": True}
    assert ingestion["inputs"]["spans"] == {"type": "array", "required": True}


def test_show_duration_report_renders_totals_and_tables(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    _seed(db_path)
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
        "request_count": 2,
        "total_ms": 1500,
        "tool_call_count": 1,
        "tool_total_ms": 250,
    }
    assert [entry["session_id"] for entry in result["top_sessions"]] == ["s2", "s1"]
    assert [entry["working_directory"] for entry in result["top_projects"]] == [
        "/tmp/other",
        "/tmp/ws",
    ]

    body = result["display"]["body"]
    assert "## Duration report" in body
    assert "- Total duration: `1.5s`" in body
    assert "- Requests: `2`" in body
    assert "- Average: `750ms`" in body
    # Tool duration surfaces as separate overall lines...
    assert "- Tools: `250ms`" in body
    assert "- Tool calls: `1`" in body
    assert "- Tool average: `250ms`" in body
    assert "### Top sessions" in body
    assert "### Top projects" in body
    # ...and as a separate Tools column, never merged into the LLM total.
    assert "| Project | Session | Total | Requests | Tools |" in body
    assert "| Project | Total | Requests | Tools |" in body
    # Working directories render as resolved project names.
    assert "other-project" in body
    assert "workspace" in body
    assert "`s2`" in body
    assert "no reset windows" in body

    # The session with the tool call reports it; the tool-less session
    # reports a zero Tools column.
    s2_entry = result["top_sessions"][0]
    s1_entry = result["top_sessions"][1]
    assert s2_entry["tool_total_ms"] == 250
    assert s2_entry["tool_call_count"] == 1
    assert s1_entry["tool_total_ms"] == 0
    assert s1_entry["tool_call_count"] == 0


def test_show_duration_report_handles_empty_store(tmp_path: Path) -> None:
    plugin = DurationTrackingAppPlugin()
    app = _FakeApp(_session_config(tmp_path))

    result = plugin.execute_action(
        app, "show_duration_report", {"session_id": "session-1"}, None, _state()
    )

    assert result["report"] == {
        "request_count": 0,
        "total_ms": 0,
        "tool_call_count": 0,
        "tool_total_ms": 0,
    }
    assert "No duration records yet." in result["display"]["body"]


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
                "from": "2026-09-25T08:00:00Z",
                "to": "2026-09-25T08:05:00Z",
            }
        ],
    )
    plugin = DurationTrackingAppPlugin()

    result = plugin.execute_action(
        app, "show_duration_report", {"session_id": "session-1"}, None, _state()
    )

    body = result["display"]["body"]
    assert "- Human time: `5m`" in body
    assert result["human_time"] == {"span_count": 1, "total_ms": 5 * 60 * 1000}


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

    assert "Human time" not in result["display"]["body"]
    assert result["human_time"] is None


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
    app: _FakeApp,
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


def test_record_human_time_spans_resolves_per_span_targets(
    tmp_path: Path,
) -> None:
    """Session spans follow their session's config; session-less spans the
    plugin config (working directory and store location)."""

    session_db = tmp_path / "session.sqlite3"
    app_db = tmp_path / "app.sqlite3"
    app = _FakeApp(
        {
            "duration_tracking_db_path": str(session_db),
            "working_directory": "/tmp/ws",
        }
    )
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
        session_db, working_directory=_wd("/tmp/ws"), session_id="session-1"
    ) == {"span_count": 1, "total_ms": 5 * 60 * 1000}
    assert duration_store.human_time_project_totals(
        app_db, working_directory=_wd("/tmp/app-ws")
    ) == {"span_count": 1, "total_ms": 2 * 60 * 1000}


def test_record_human_time_spans_duplicate_request(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    app = _FakeApp(
        {"duration_tracking_db_path": str(db_path), "working_directory": "/tmp/ws"}
    )
    state = {"config": {}}
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


def test_record_human_time_spans_unknown_session_skips_span(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    app = _FakeApp(
        {"duration_tracking_db_path": str(db_path), "working_directory": "/tmp/ws"}
    )
    state = {"config": {}}
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
    assert result["recorded"] == 1
    assert result["skipped"] == 1


def test_record_human_time_spans_session_less_without_config_skipped(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    app = _FakeApp(
        {"duration_tracking_db_path": str(db_path), "working_directory": "/tmp/ws"}
    )
    # No plugin-config working_directory: session-less spans cannot be
    # keyed and are skipped.
    state = {"config": {}}
    plugin = DurationTrackingAppPlugin()

    result = _ingest(
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
    assert result["recorded"] == 0
    assert result["skipped"] == 1


def test_record_human_time_spans_malformed_spans_skipped(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    app = _FakeApp(
        {"duration_tracking_db_path": str(db_path), "working_directory": "/tmp/ws"}
    )
    state = {"config": {}}
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
    assert result["recorded"] == 1
    assert result["skipped"] == 2


def test_record_human_time_spans_overlap_resolution_applies(
    tmp_path: Path,
) -> None:
    db_path = tmp_path / "durations.sqlite3"
    app = _FakeApp(
        {"duration_tracking_db_path": str(db_path), "working_directory": "/tmp/ws"}
    )
    state = {"config": {}}
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
