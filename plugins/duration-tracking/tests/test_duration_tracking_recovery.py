from __future__ import annotations

import json
import sqlite3
import sys
from pathlib import Path
from typing import Any

import pytest

from duration_tracking_plugins import duration_store
from duration_tracking_plugins.recovery import (
    main,
    recover_projects,
    repair_session_metadata,
)


def _fixture(tmp_path: Path) -> tuple[Path, Path, Path]:
    project = tmp_path / "project"
    sessions = project / ".crystal" / "sessions"
    sessions.mkdir(parents=True)
    db_path = tmp_path / "duration.sqlite3"

    def owner(index: int, duration: int, **extra: Any) -> dict[str, Any]:
        return {
            "role": "assistant",
            "content": f"message {index}",
            "_metadata": {
                "duration_started_at": f"2026-10-06T12:00:{index:02}+00:00",
                "duration_finished_at": f"2026-10-06T12:00:{index + 1:02}+00:00",
                "duration_ms": duration,
                "turn_duration_ms": duration,
                **extra,
            },
        }

    first = owner(
        0,
        1000,
        human_time_session_total=60_000,
        human_time_turn_delta=60_000,
        turn={"id": 1, "has_tool_calls": False, "is_terminal": True},
    )
    intermediate = owner(
        2,
        2000,
        human_time_session_total=120_000,
        human_time_turn_delta=60_000,
        turn={"id": 2, "has_tool_calls": True, "is_terminal": False},
    )
    tool_only = {
        **owner(4, 4000, turn={"id": 2, "has_tool_calls": True}),
        "type": "function_call",
    }
    tool_only.pop("role")
    final = owner(
        6,
        3000,
        human_time_session_total=120_000,
        human_time_turn_delta=0,
        duration_session_total=6000,
        tool_duration_session_total=5000,
        duration_session_combined_total=11000,
        turn={"id": 2, "has_tool_calls": False, "is_terminal": True},
    )
    tool_output = {
        "type": "function_call_output",
        "_metadata": {
            "duration_started_at": "2026-10-06T12:00:05+00:00",
            "duration_finished_at": "2026-10-06T12:00:06+00:00",
            "duration_ms": 5000,
        },
    }
    # The older stamp predates known tracking; it must not be silently imported.
    old = owner(0, 7000)
    old["_metadata"]["duration_started_at"] = "2026-10-05T12:00:00+00:00"
    old["_metadata"]["duration_finished_at"] = "2026-10-05T12:00:01+00:00"
    native = [
        {"role": "user", "content": "hello"},
        old,
        first,
        intermediate,
        {"type": "function_call"},
        tool_only,
        tool_output,
        final,
    ]
    messages = []
    for index, item in enumerate(native):
        if item.get("role") == "assistant":
            messages.append(
                {
                    "role": "assistant",
                    "content": item["content"],
                    "metadata": {**item["_metadata"], "native_indices": [index]},
                }
            )
    path = sessions / "s1.json"
    path.write_text(
        json.dumps(
            {
                "session_id": "s1",
                "messages": messages,
                "metadata": {
                    "native_messages": native,
                    "native_messages_integrity": {"message_count": len(messages)},
                    "agent_id": "agent-that-no-longer-exists",
                },
            }
        )
    )
    for item in [first, intermediate, final]:
        md = item["_metadata"]
        duration_store.record_request_duration(
            db_path,
            session_id="s1",
            working_directory=str(project),
            model="test-model",
            request_id=f"request-{md['turn']['id']}",
            duration_ms=md["duration_ms"],
            duration_started_at=md["duration_started_at"],
            duration_finished_at=md["duration_finished_at"],
            time=md["duration_finished_at"],
        )
    return project, db_path, path


def test_recovery_preview_is_read_only(tmp_path: Path) -> None:
    project, db_path, path = _fixture(tmp_path)
    original = path.read_bytes()
    original_db = db_path.read_bytes()

    result = recover_projects(db_path, [project])

    assert result["missing_rounds"] == 1
    assert result["missing_ms"] == 4000
    assert path.read_bytes() == original
    assert db_path.read_bytes() == original_db
    assert not db_path.with_name("backups").exists()


def test_recovery_backfills_and_repairs_snapshots_idempotently(tmp_path: Path) -> None:
    project, db_path, path = _fixture(tmp_path)
    original = json.loads(path.read_text())

    result = recover_projects(db_path, [project], apply=True)

    assert result["missing_rounds"] == 1
    assert (Path(result["backup_dir"]) / db_path.name).is_file()
    backups = list((Path(result["backup_dir"]) / "sessions").rglob("s1.json"))
    assert len(backups) == 1
    assert json.loads(backups[0].read_text()) == original
    assert duration_store.session_totals(
        db_path,
        working_directory=str(project),
        session_id="s1",
    ) == {"request_count": 4, "total_ms": 10000}
    with sqlite3.connect(db_path) as conn:
        assert conn.execute(
            "SELECT request_id,model FROM duration_requests WHERE duration_ms=4000"
        ).fetchone() == ("request-2", "test-model")

    fixed = json.loads(path.read_text())
    assert fixed["metadata"]["native_messages_integrity"] == (
        original["metadata"]["native_messages_integrity"]
    )
    assert [msg["content"] for msg in fixed["messages"]] == [
        msg["content"] for msg in original["messages"]
    ]
    final_md = fixed["messages"][-1]["metadata"]
    assert final_md["human_time_turn_delta"] == 60_000
    assert final_md["duration_session_total"] == 10000
    assert final_md["duration_session_combined_total"] == 15000
    intermediate_md = fixed["metadata"]["native_messages"][3]["_metadata"]
    assert not any(key.startswith("human_time_") for key in intermediate_md)
    assert final_md["human_time_session_total"] == 120_000

    second = recover_projects(db_path, [project], apply=True)
    assert second["missing_rounds"] == 0
    assert second["sessions"] == []


def test_recovery_preserves_concurrently_changed_session(
    tmp_path: Path,
    monkeypatch: Any,
) -> None:
    project, db_path, path = _fixture(tmp_path)
    record = duration_store.record_request_duration
    newer = {**json.loads(path.read_text()), "concurrent": True}

    def record_and_change(*args: Any, **kwargs: Any) -> bool:
        path.write_text(json.dumps(newer))
        return record(*args, **kwargs)

    monkeypatch.setattr(duration_store, "record_request_duration", record_and_change)
    result = recover_projects(db_path, [project], apply=True)

    assert (
        result["sessions"][0]["metadata_deferred"] == "session changed during recovery"
    )
    assert json.loads(path.read_text()) == newer


def test_recovery_preserves_delta_when_compaction_removed_the_baseline() -> None:
    internal = {
        "human_time_session_total": 150_000,
        "human_time_turn_delta": 90_000,
        "human_time_turn_delta_formatted": "1.5m",
    }
    session = {
        "messages": [
            {
                "role": "assistant",
                "metadata": {**internal, "native_indices": [1]},
            }
        ],
        "metadata": {
            "native_messages": [
                {"type": "compaction"},
                {"role": "assistant", "_metadata": internal},
            ],
        },
    }

    repaired = repair_session_metadata(session, [])

    assert repaired == session


def _add_session(
    db_path: Path, source_path: Path, project: Path, session_id: str
) -> Path:
    session = {**json.loads(source_path.read_text()), "session_id": session_id}
    path = project / ".crystal" / "sessions" / f"{session_id}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(session))
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        rows = conn.execute(
            "SELECT * FROM duration_requests WHERE session_id='s1' AND working_directory=?",
            (str(source_path.parents[2]),),
        ).fetchall()
    for source_row in rows:
        row = dict(source_row)
        row.pop("id")
        row.update(session_id=session_id, working_directory=str(project))
        duration_store.record_request_duration(db_path, **row)
    return path


@pytest.mark.parametrize("apply", [False, True])
def test_recovery_session_filter_is_scoped_to_the_project(
    tmp_path: Path, apply: bool
) -> None:
    project, db_path, path = _fixture(tmp_path)
    neighbor = _add_session(db_path, path, project, "s2")
    other_project = tmp_path / "other-project"
    same_id_elsewhere = _add_session(db_path, path, other_project, "s1")
    originals = {
        neighbor: neighbor.read_bytes(),
        same_id_elsewhere: same_id_elsewhere.read_bytes(),
    }

    result = recover_projects(db_path, [project], session_id="s1", apply=apply)

    assert result["session_id"] == "s1"
    assert result["missing_rounds"] == 1
    assert [entry["path"] for entry in result["sessions"]] == [str(path)]
    for unselected, original in originals.items():
        assert unselected.read_bytes() == original
    assert duration_store.session_totals(
        db_path, working_directory=str(project), session_id="s1"
    )["request_count"] == (4 if apply else 3)
    for selected_project, selected_id in [(project, "s2"), (other_project, "s1")]:
        assert duration_store.session_totals(
            db_path,
            working_directory=str(selected_project),
            session_id=selected_id,
        ) == {"request_count": 3, "total_ms": 6000}


def test_recovery_cli_session_filter_skips_unrelated_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    project, db_path, path = _fixture(tmp_path)
    neighbor = _add_session(db_path, path, project, "s2")
    neighbor.write_text("unrelated malformed session")
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "recovery",
            "--db",
            str(db_path),
            "--project",
            str(project),
            "--session",
            "s1",
        ],
    )

    main()

    result = json.loads(capsys.readouterr().out)
    assert result["applied"] is False
    assert result["session_id"] == "s1"
    assert [entry["path"] for entry in result["sessions"]] == [str(path)]
    assert neighbor.read_text() == "unrelated malformed session"
