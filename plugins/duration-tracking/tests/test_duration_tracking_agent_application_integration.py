"""Integration tests for duration tracking through the public request path.

These tests run a real ``AgentApplication`` request against the local echo
provider with the production duration feature and duration tracking
feature — no test-only bypasses. They assert that duration rows land in
the SQLite store keyed by workspace + session id and that the
store-backed session totals reach the assistant message metadata that
the chat status bar renders, including across a tool-loop turn and a
session reload.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any, Dict, List

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
CORE_PY = ROOT / "core/python"
if str(CORE_PY) not in sys.path:
    sys.path.insert(0, str(CORE_PY))
TESTS_DIR = Path(__file__).resolve().parent
if str(TESTS_DIR) not in sys.path:
    sys.path.insert(0, str(TESTS_DIR))

import pytest  # noqa: E402

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from agent_core import AgentCore, Session  # noqa: E402

from duration_tracking_plugins import duration_store  # noqa: E402

pytestmark = [pytest.mark.integration]


def _make_config(
    tmp_path: Path,
    db_path: Path,
    *,
    provider_overrides: Dict[str, Any] | None = None,
    provider_entry: str = "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
) -> Path:
    provider_config: Dict[str, Any] = {
        "provider": "echo_openai_like",
        "model": "test-model",
        "working_directory": str(tmp_path),
        "duration_tracking_db_path": str(db_path),
    }
    if provider_overrides:
        provider_config.update(provider_overrides)
    cfg: Dict[str, Any] = {
        "providers": {"echo": provider_config},
        "application": {"duration_tracking": {"db_path": str(db_path)}},
        "agents": {
            "default": {
                "provider": "echo",
                "working_directory": str(tmp_path),
                "allowed_paths": [str(tmp_path)],
            }
        },
        "plugins": [
            provider_entry,
            "plugins.file_reader_tool.FileReaderTool",
            "timestamp_extension.duration_extension.DurationExtension",
            "duration_tracking_plugins.duration_tracking_extension.DurationTrackingExtension",
            "duration_tracking_plugins.duration_tracking_app_plugin.DurationTrackingAppPlugin",
        ],
    }
    config_path = tmp_path / "config_duration_tracking.json"
    config_path.write_text(json.dumps(cfg), encoding="utf-8")
    return config_path


def _make_app(
    tmp_path: Path,
    db_path: Path,
    *,
    provider_overrides: Dict[str, Any] | None = None,
    provider_entry: str = "plugins.echo_openai_like_provider.EchoOpenAILikeProvider",
) -> AgentApplication:
    config_path = _make_config(
        tmp_path,
        db_path,
        provider_overrides=provider_overrides,
        provider_entry=provider_entry,
    )
    session_root = tmp_path / "sessions"
    return AgentApplication(
        str(config_path),
        str(session_root),
        core_factory=AgentCore,
        event_store=InMemoryEventStore(),
    )


def _run_request(
    app: AgentApplication,
    core: AgentCore,
    session: Session,
    base_config: Dict[str, Any],
) -> Session:
    events = list(
        app.send_request(core, session, base_config, overrides=None, stream=False)
    )
    checkpoints = [ev for ev in events if ev.get("type") == "session_checkpoint"]
    assert checkpoints, "expected at least one session_checkpoint event"
    final_session = checkpoints[-1]["session"]
    assert isinstance(final_session, Session)
    app.save_session(final_session)
    return final_session


def _assistant_messages(session: Session) -> List[Any]:
    return [m for m in session.messages if getattr(m, "role", None) == "assistant"]


def _request_rows(db_path: Path) -> List[Dict[str, Any]]:
    import sqlite3

    duration_store.session_totals(db_path, working_directory="x", session_id="y")
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in conn.execute("SELECT * FROM duration_requests ORDER BY id")
        ]
    finally:
        conn.close()


def _tool_rows(db_path: Path) -> List[Dict[str, Any]]:
    import sqlite3

    duration_store.tool_session_totals(db_path, working_directory="x", session_id="y")
    conn = sqlite3.connect(str(db_path))
    try:
        conn.row_factory = sqlite3.Row
        return [
            dict(row)
            for row in conn.execute("SELECT * FROM tool_durations ORDER BY id")
        ]
    finally:
        conn.close()


def _read_file_call(call_id: str, path: Path) -> Dict[str, Any]:
    return {
        "id": call_id,
        "type": "function",
        "function": {
            "name": "read_file",
            "arguments": json.dumps({"file_path": str(path)}),
        },
    }


def _seed_pending_tool_calls(
    app: AgentApplication,
    core: AgentCore,
    session: Session,
    tool_calls: List[Dict[str, Any]],
) -> Session:
    session = core.add_message(
        session,
        "assistant",
        "",
        {"tool_calls": tool_calls},
    )
    app.save_session(session)
    return session


def _tool_messages(session: Session) -> List[Any]:
    return [m for m in session.messages if getattr(m, "role", None) == "tool"]


def test_request_records_row_and_projects_session_totals(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    app = _make_app(tmp_path, db_path)
    core, base_config, session = app.create_session("default")

    session = _run_request(app, core, session, base_config)

    rows = _request_rows(db_path)
    assert len(rows) == 1
    assert rows[0]["session_id"] == session.session_id
    assert rows[0]["working_directory"] == str(tmp_path)
    assert isinstance(rows[0]["request_id"], str) and rows[0]["request_id"]
    assert isinstance(rows[0]["duration_ms"], int) and rows[0]["duration_ms"] >= 0
    assert isinstance(rows[0]["duration_started_at"], str)
    assert isinstance(rows[0]["duration_finished_at"], str)
    assert rows[0]["time"] == rows[0]["duration_finished_at"]

    totals = duration_store.session_totals(
        db_path, working_directory=str(tmp_path), session_id=session.session_id
    )
    assert totals == {"request_count": 1, "total_ms": rows[0]["duration_ms"]}

    # The store-backed totals reach the assistant message public metadata
    # that the status bar renders.
    assistant_md = _assistant_messages(session)[-1].metadata or {}
    assert assistant_md.get("duration_session_total") == rows[0]["duration_ms"]
    assert isinstance(assistant_md.get("duration_session_total_formatted"), str)
    assert assistant_md.get("duration_session_total_formatted")
    assert assistant_md.get("duration_session_requests") == 1
    assert assistant_md.get("duration_session_requests_formatted") == "1"
    assert isinstance(assistant_md.get("duration_session_average"), float)
    assert assistant_md.get("duration_session_combined_total") == rows[0]["duration_ms"]

    # The totals survive a save + reload (native-history round-trip).
    loaded = app.load_session(session.session_id)
    assert loaded is not None
    _core2, _config2, reloaded = loaded
    reloaded_md = _assistant_messages(reloaded)[-1].metadata or {}
    assert reloaded_md.get("duration_session_total") == rows[0]["duration_ms"]
    assert reloaded_md.get("duration_session_requests") == 1


def test_totals_accumulate_across_requests(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    app = _make_app(tmp_path, db_path)
    core, base_config, session = app.create_session("default")

    session = _run_request(app, core, session, base_config)
    session = _run_request(app, core, session, base_config)

    rows = _request_rows(db_path)
    assert len(rows) == 2
    # Distinct requests dedup by their own request ids.
    assert rows[0]["request_id"] != rows[1]["request_id"]

    totals = duration_store.session_totals(
        db_path, working_directory=str(tmp_path), session_id=session.session_id
    )
    assert totals == {
        "request_count": 2,
        "total_ms": rows[0]["duration_ms"] + rows[1]["duration_ms"],
    }

    # The latest assistant message carries the accumulated totals.
    assistant_md = _assistant_messages(session)[-1].metadata or {}
    assert assistant_md.get("duration_session_requests") == 2
    assert assistant_md.get("duration_session_requests_formatted") == "2"
    assert (
        assistant_md.get("duration_session_total")
        == rows[0]["duration_ms"] + rows[1]["duration_ms"]
    )


def test_tool_calling_request_records_llm_and_tool_rows(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    app = _make_app(tmp_path, db_path)
    core, base_config, session = app.create_session("default")

    target = tmp_path / "hello.txt"
    target.write_text("hello", encoding="utf-8")
    session = _seed_pending_tool_calls(
        app, core, session, [_read_file_call("call_1", target)]
    )

    session = _run_request(app, core, session, base_config)

    # The tool loop ran and the tool message carries the per-call stamps
    # (020 behavior).
    tool_msgs = _tool_messages(session)
    assert tool_msgs
    tool_md = tool_msgs[-1].metadata or {}
    assert isinstance(tool_md.get("duration_ms"), int)
    assert tool_md["duration_ms"] >= 0

    # One LLM row and one tool row landed, both keyed to the session.
    rows = _request_rows(db_path)
    assert len(rows) == 1
    assert rows[0]["session_id"] == session.session_id
    tool_rows = _tool_rows(db_path)
    assert len(tool_rows) == 1
    assert tool_rows[0]["session_id"] == session.session_id
    assert tool_rows[0]["working_directory"] == str(tmp_path)
    assert tool_rows[0]["tool_call_id"] == "call_1"
    assert tool_rows[0]["tool_name"] == "read_file"
    assert tool_rows[0]["duration_ms"] == tool_md["duration_ms"]
    assert tool_rows[0]["duration_finished_at"] == tool_md["duration_finished_at"]
    assert tool_rows[0]["time"] == tool_md["duration_finished_at"]
    assert tool_rows[0]["tool_error"] is None

    # The assistant message carries both the LLM totals and the tool
    # totals from the store.
    assistant_md = _assistant_messages(session)[-1].metadata or {}
    assert assistant_md.get("duration_session_requests") == 1
    assert assistant_md.get("duration_session_total") == rows[0]["duration_ms"]
    assert assistant_md.get("tool_duration_session_total") == tool_md["duration_ms"]
    assert assistant_md.get("tool_duration_session_calls") == 1
    assert assistant_md.get("duration_session_combined_total") == (
        rows[0]["duration_ms"] + tool_md["duration_ms"]
    )
    assert (
        assistant_md.get("tool_duration_session_total_formatted")
        == tool_md["duration_formatted"]
    )


def test_tool_loop_records_every_llm_round(tmp_path: Path) -> None:
    """A genuine multi-round tool loop records one LLM row per round.

    The provider emits a tool call on its first response, the production
    tool loop executes it, and the second LLM round answers. Both rounds
    share one request id, so this regression-tests the original bug
    where only the first round landed and the session totals froze at
    its snapshot (footer total lower than the last turn duration).
    """

    db_path = tmp_path / "durations.sqlite3"
    app = _make_app(
        tmp_path,
        db_path,
        provider_entry="fixtures.tool_loop_echo_provider.ToolLoopEchoProvider",
    )
    core, base_config, session = app.create_session("default")

    target = tmp_path / "hello.txt"
    target.write_text("hello", encoding="utf-8")
    session = _run_request(app, core, session, base_config)

    # The loop actually ran: one tool message and two assistant messages
    # (the tool-call round and the final answer round).
    tool_msgs = _tool_messages(session)
    assert len(tool_msgs) == 1
    assistants = _assistant_messages(session)
    assert len(assistants) == 2

    # Every LLM round recorded its own row, all under the shared
    # request id, keyed by the round's measurement stamps.
    rows = _request_rows(db_path)
    assert len(rows) == 2
    assert len({row["request_id"] for row in rows}) == 1
    assert rows[0]["request_id"]
    assert rows[0]["session_id"] == session.session_id
    assert rows[0]["working_directory"] == str(tmp_path)
    assert rows[0]["duration_started_at"] != rows[1]["duration_started_at"]

    assert len(_tool_rows(db_path)) == 1

    # The final assistant message stamps store totals that include both
    # rounds, so the session total can never fall below the turn total.
    assistant_md = assistants[-1].metadata or {}
    assert assistant_md.get("duration_session_requests") == 2
    assert assistant_md.get("duration_session_total") == (
        rows[0]["duration_ms"] + rows[1]["duration_ms"]
    )
    assert assistant_md.get("duration_session_total") >= assistant_md.get(
        "turn_duration_ms", 0
    )
    assert assistant_md.get("tool_duration_session_calls") == 1
    intermediate_md = assistants[0].metadata or {}
    assert not any(key.startswith("human_time_") for key in intermediate_md)
    assert assistant_md.get("human_time_turn_delta") == 0
    assert assistant_md.get("human_time_turn_delta_formatted") == "0ms"


def test_multiple_tool_calls_record_one_row_each(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    app = _make_app(tmp_path, db_path)
    core, base_config, session = app.create_session("default")

    target_a = tmp_path / "a.txt"
    target_a.write_text("a", encoding="utf-8")
    target_b = tmp_path / "b.txt"
    target_b.write_text("b", encoding="utf-8")
    session = _seed_pending_tool_calls(
        app,
        core,
        session,
        [_read_file_call("call_1", target_a), _read_file_call("call_2", target_b)],
    )

    session = _run_request(app, core, session, base_config)

    tool_rows = _tool_rows(db_path)
    assert len(tool_rows) == 2
    assert {row["tool_call_id"] for row in tool_rows} == {"call_1", "call_2"}

    tool_msgs = _tool_messages(session)
    assert len(tool_msgs) == 2
    stamped = [
        msg.metadata["duration_ms"]
        for msg in tool_msgs
        if isinstance((msg.metadata or {}).get("duration_ms"), int)
    ]
    assert sorted(row["duration_ms"] for row in tool_rows) == sorted(stamped)

    # The session tool totals aggregate both calls.
    assistant_md = _assistant_messages(session)[-1].metadata or {}
    assert assistant_md.get("tool_duration_session_calls") == 2
    assert assistant_md.get("tool_duration_session_total") == sum(stamped)


def test_unregistered_call_records_no_tool_row(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    app = _make_app(tmp_path, db_path)
    core, base_config, session = app.create_session("default")

    target = tmp_path / "hello.txt"
    target.write_text("hello", encoding="utf-8")
    session = _seed_pending_tool_calls(
        app,
        core,
        session,
        [
            _read_file_call("call_1", target),
            {
                "id": "call_2",
                "type": "function",
                "function": {
                    "name": "no_such_tool",
                    "arguments": json.dumps({"file_path": str(target)}),
                },
            },
        ],
    )

    session = _run_request(app, core, session, base_config)

    # The unregistered call synthesizes an error tool message, but the
    # framework provides no timing facts for it, so it carries no
    # duration stamps — and the tracker records no fabricated row.
    tool_msgs = _tool_messages(session)
    assert len(tool_msgs) == 2
    by_call_id = {msg.metadata.get("tool_call_id"): msg for msg in tool_msgs}
    assert "duration_ms" in (by_call_id["call_1"].metadata or {})
    assert "duration_ms" not in (by_call_id["call_2"].metadata or {})

    tool_rows = _tool_rows(db_path)
    assert [row["tool_call_id"] for row in tool_rows] == ["call_1"]

    # The session tool totals count only the measured call.
    assistant_md = _assistant_messages(session)[-1].metadata or {}
    assert assistant_md.get("tool_duration_session_calls") == 1


def test_tracking_independent_of_duration_footers(tmp_path: Path) -> None:
    db_path = tmp_path / "durations.sqlite3"
    app = _make_app(
        tmp_path,
        db_path,
        provider_overrides={"duration_extension_show_duration": False},
    )
    core, base_config, session = app.create_session("default")

    session = _run_request(app, core, session, base_config)

    # Footers are off, but recording and the store-backed status totals
    # are independent features and both still work.
    rows = _request_rows(db_path)
    assert len(rows) == 1
    assistant_md = _assistant_messages(session)[-1].metadata or {}
    assert assistant_md.get("duration_session_requests") == 1
    assert "duration_ms" not in assistant_md or isinstance(
        assistant_md.get("duration_ms"), int
    )


# --- Human time telemetry (subtask 030) ---


def test_human_time_spans_ingest_through_public_action_path(
    tmp_path: Path,
) -> None:
    """Spans flow through ``execute_application_action`` (the HTTP route's
    entry): session-less spans use the runtime working-directory default,
    retries dedup, overlaps merge, and ingestion never mutates sessions."""

    db_path = tmp_path / "durations.sqlite3"
    app = _make_app(tmp_path, db_path)
    core, base_config, session = app.create_session("default")
    session_id = session.session_id

    result = app.execute_application_action(
        "duration_tracking_app",
        "record_human_time_spans",
        {
            "request_id": "frontend-req-1",
            "spans": [
                {
                    "session_id": session_id,
                    "from": "2026-09-25T08:00:00Z",
                    "to": "2026-09-25T08:05:00Z",
                },
                {
                    # No plugin-config working directory: application
                    # initialization defaults this target from WORKING_DIR.
                    "session_id": None,
                    "from": "2026-09-25T09:00:00Z",
                    "to": "2026-09-25T09:02:00Z",
                },
            ],
        },
    )
    assert result == {
        "recorded": 2,
        "merged": 0,
        "skipped": 0,
        "absorbed": 0,
        "duplicate": False,
    }
    totals = duration_store.human_time_session_totals(
        db_path, working_directory=str(tmp_path), session_id=session_id
    )
    assert totals == {"span_count": 1, "total_ms": 5 * 60 * 1000}
    assert duration_store.human_time_project_totals(
        db_path, working_directory=str(Path.cwd().resolve())
    ) == {"span_count": 1, "total_ms": 2 * 60 * 1000}

    # A retry of the accepted batch is recognized and skipped.
    retry = app.execute_application_action(
        "duration_tracking_app",
        "record_human_time_spans",
        {
            "request_id": "frontend-req-1",
            "spans": [
                {
                    "session_id": session_id,
                    "from": "2026-09-25T10:00:00Z",
                    "to": "2026-09-25T10:05:00Z",
                }
            ],
        },
    )
    assert retry["duplicate"] is True
    assert retry["recorded"] == 0
    assert duration_store.human_time_session_totals(
        db_path, working_directory=str(tmp_path), session_id=session_id
    ) == {"span_count": 1, "total_ms": 5 * 60 * 1000}

    # A new batch with an overlapping same-session span merges into one.
    merged = app.execute_application_action(
        "duration_tracking_app",
        "record_human_time_spans",
        {
            "request_id": "frontend-req-2",
            "spans": [
                {
                    "session_id": session_id,
                    "from": "2026-09-25T08:03:00Z",
                    "to": "2026-09-25T08:08:00Z",
                }
            ],
        },
    )
    assert merged["recorded"] == 1
    assert merged["merged"] == 1
    assert duration_store.human_time_session_totals(
        db_path, working_directory=str(tmp_path), session_id=session_id
    ) == {"span_count": 1, "total_ms": 8 * 60 * 1000}

    # Ingestion never mutates sessions (no save path).
    loaded = app.load_session(session_id)
    assert loaded is not None
    _core2, _config2, reloaded = loaded
    assert len(reloaded.messages) == len(session.messages)


def test_human_time_totals_reach_assistant_metadata_and_report(
    tmp_path: Path,
) -> None:
    """Ingested spans surface like the other duration fields: the footer
    metadata on the next request and the report line."""

    db_path = tmp_path / "durations.sqlite3"
    app = _make_app(tmp_path, db_path)
    core, base_config, session = app.create_session("default")

    app.execute_application_action(
        "duration_tracking_app",
        "record_human_time_spans",
        {
            "request_id": "frontend-req-1",
            "spans": [
                {
                    "session_id": session.session_id,
                    "from": "2026-09-25T08:00:00Z",
                    "to": "2026-09-25T08:05:00Z",
                }
            ],
        },
    )

    session = _run_request(app, core, session, base_config)

    # The store-backed human time total reaches the assistant message
    # public metadata that the footer status-bar element renders.
    assistant_md = _assistant_messages(session)[-1].metadata or {}
    assert assistant_md.get("human_time_session_total") == 5 * 60 * 1000
    assert assistant_md.get("human_time_session_total_formatted") == "5m"
    assert assistant_md.get("human_time_turn_delta") == 5 * 60 * 1000
    assert assistant_md.get("human_time_turn_delta_formatted") == "5m"

    app.execute_application_action(
        "duration_tracking_app",
        "record_human_time_spans",
        {
            "request_id": "frontend-req-2",
            "spans": [
                {
                    "session_id": session.session_id,
                    "from": "2026-09-25T08:05:00Z",
                    "to": "2026-09-25T08:08:00Z",
                }
            ],
        },
    )
    session = _run_request(app, core, session, base_config)
    second_md = _assistant_messages(session)[-1].metadata or {}
    assert second_md.get("human_time_session_total") == 8 * 60 * 1000
    assert second_md.get("human_time_turn_delta") == 3 * 60 * 1000
    assert second_md.get("human_time_turn_delta_formatted") == "3m"

    # And the report action includes the current-project total and factual
    # all-time per-session diagnostics.
    report = app.execute_application_action(
        "duration_tracking_app",
        "show_duration_report",
        {"session_id": session.session_id},
    )
    assert "- Human time: `8m`" in report["display"]["body"]
    assert "- Current session stored total: `8m`" in report["display"]["body"]
    assert report["human_time"] == {"span_count": 1, "total_ms": 8 * 60 * 1000}

    reset = app.execute_application_action(
        "duration_tracking_app",
        "reset_duration_tracking",
        {"session_id": session.session_id},
    )
    assert reset["reset"]["working_directory"] == str(tmp_path)
    assert reset["project_summary_since_reset"]["human_total_ms"] == 0

    reset_report = app.execute_application_action(
        "duration_tracking_app",
        "show_duration_report",
        {"session_id": session.session_id},
    )
    assert "- Human time: `0ms`" in reset_report["display"]["body"]
    # Reset changes the report window only; factual collection diagnostics
    # and message/footer totals remain all-time.
    assert reset_report["human_time"] == {
        "span_count": 1,
        "total_ms": 8 * 60 * 1000,
    }
