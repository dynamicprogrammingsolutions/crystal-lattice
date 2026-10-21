"""Recover missing measured LLM rounds and repair saved duration metadata.

Run with explicit local project roots. The default is a read-only preview;
``--apply`` backs up the database and changed session files before writing.
Only sessions already recorded in the selected database are eligible.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import tempfile
from bisect import bisect_right
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

from . import duration_store
from .duration_tracking_extension import DurationTrackingExtension, _format_duration_ms


def measured_rounds(native: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Read LLM measurement owners, excluding executed-tool duration stamps."""
    feature = DurationTrackingExtension
    rounds = []
    seen = set()
    for item in native:
        if not isinstance(item, dict) or not feature._is_llm_output(item):
            continue
        internal = item.get("_metadata")
        if not isinstance(internal, dict) or not feature._is_duration_record_source(
            internal
        ):
            continue
        if not isinstance(internal.get("turn_duration_ms"), (int, float)):
            continue
        key = (internal["duration_started_at"], internal["duration_finished_at"])
        if key in seen:
            continue
        seen.add(key)
        turn = internal.get("turn")
        rounds.append(
            {
                "duration_started_at": key[0],
                "duration_finished_at": key[1],
                "duration_ms": int(internal["duration_ms"]),
                "turn_id": turn.get("id") if isinstance(turn, dict) else None,
            }
        )
    return rounds


def missing_rounds(
    native: List[Dict[str, Any]], recorded: List[Dict[str, Any]]
) -> List[Dict[str, Any]]:
    """Recover only the known tracking window; preserve unknown provenance."""
    if not recorded:
        return []
    existing = {
        (row["duration_started_at"], row["duration_finished_at"]): row
        for row in recorded
    }
    first_time = min(row["duration_started_at"] or row["time"] for row in recorded)
    rounds = measured_rounds(native)
    provenance: Dict[Any, List[Dict[str, Any]]] = {}
    for round_ in rounds:
        key = (round_["duration_started_at"], round_["duration_finished_at"])
        if round_["turn_id"] is not None and key in existing:
            provenance.setdefault(round_["turn_id"], []).append(existing[key])

    models = {row["model"] for row in recorded if row["model"]}
    missing = []
    for round_ in rounds:
        key = (round_["duration_started_at"], round_["duration_finished_at"])
        if key in existing or key[0] < first_time:
            continue
        source = provenance.get(round_["turn_id"], [])
        request_ids = {row["request_id"] for row in source if row["request_id"]}
        turn_models = {row["model"] for row in source if row["model"]} or models
        missing.append(
            {
                "time": key[1],
                "duration_started_at": key[0],
                "duration_finished_at": key[1],
                "duration_ms": round_["duration_ms"],
                "request_id": (
                    next(iter(request_ids)) if len(request_ids) == 1 else None
                ),
                "model": next(iter(turn_models)) if len(turn_models) == 1 else None,
            }
        )
    return missing


def repair_session_metadata(
    session: Dict[str, Any], recorded: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """Refresh LLM snapshots and completed human deltas without changing content."""
    metadata = session.get("metadata") or {}
    native = metadata.get("native_messages")
    if not isinstance(native, list):
        return session
    feature = DurationTrackingExtension()
    timeline = sorted(recorded, key=lambda row: row["time"])
    times = [row["time"] for row in timeline]
    totals = [0]
    for row in timeline:
        totals.append(totals[-1] + int(row["duration_ms"] or 0))
    first_time = min(times) if times else None
    human_turns = feature._human_turn_metadata_by_index(native)
    repaired = []
    for index, item in enumerate(native):
        if not isinstance(item, dict):
            repaired.append(item)
            continue
        internal = item.get("_metadata")
        if not isinstance(internal, dict):
            repaired.append(item)
            continue
        extra = {
            key: value
            for key, value in internal.items()
            if not (
                key.startswith("human_time_")
                and (
                    not feature._is_completed_assistant(item)
                    or (index in human_turns and key.startswith("human_time_turn_"))
                )
            )
        }
        if index in human_turns:
            extra.update(human_turns[index])
        finished = internal.get("duration_finished_at")
        if (
            feature._is_llm_output(item)
            and isinstance(finished, str)
            and first_time is not None
            and finished >= first_time
            and "turn_duration_ms" in internal
        ):
            count = bisect_right(times, finished)
            total = totals[count]
            extra.update(
                {
                    "duration_session_total": total,
                    "duration_session_total_formatted": _format_duration_ms(total),
                    "duration_session_requests": count,
                    "duration_session_requests_formatted": f"{count:,}",
                }
            )
            if count:
                extra["duration_session_average"] = total / count
                extra["duration_session_average_formatted"] = _format_duration_ms(
                    int(total / count)
                )
            tool_total = extra.get("tool_duration_session_total")
            if isinstance(tool_total, (int, float)):
                combined = total + int(tool_total)
                extra["duration_session_combined_total"] = combined
                extra["duration_session_combined_total_formatted"] = (
                    _format_duration_ms(combined)
                )
        repaired.append({**item, "_metadata": extra} if extra != internal else item)

    messages = []
    for message in session.get("messages", []):
        if not isinstance(message, dict) or message.get("role") != "assistant":
            messages.append(message)
            continue
        public = message.get("metadata")
        if not isinstance(public, dict):
            messages.append(message)
            continue
        indices = public.get("native_indices")
        if not isinstance(indices, list):
            messages.append(message)
            continue
        candidates = [
            repaired[i].get("_metadata") or {}
            for i in indices
            if isinstance(i, int)
            and 0 <= i < len(repaired)
            and isinstance(repaired[i], dict)
        ]
        # The last measured LLM owner supplies the canonical response snapshot.
        stamp = next(
            (md for md in reversed(candidates) if "duration_session_total" in md),
            {},
        )
        machine = {
            key: value
            for key, value in stamp.items()
            if key.startswith("duration_session_")
        }
        messages.append({**message, "metadata": {**public, **machine}})
    messages = feature.from_native_messages(repaired, messages)
    return {
        **session,
        "messages": messages,
        "metadata": {**metadata, "native_messages": repaired},
    }


def _read_rows(
    db_path: Path, project: Path, session_id: Optional[str] = None
) -> Dict[str, List[Dict[str, Any]]]:
    with sqlite3.connect(db_path.resolve().as_uri() + "?mode=ro", uri=True) as conn:
        conn.row_factory = sqlite3.Row
        query = "SELECT * FROM duration_requests WHERE working_directory = ?"
        params = [str(project)]
        if session_id is not None:
            query += " AND session_id = ?"
            params.append(session_id)
        rows = conn.execute(
            query,
            params,
        ).fetchall()
    sessions: Dict[str, List[Dict[str, Any]]] = {}
    for row in rows:
        if row["session_id"]:
            sessions.setdefault(row["session_id"], []).append(dict(row))
    return sessions


def recover_projects(
    db_path: Path,
    projects: List[Path],
    *,
    session_id: Optional[str] = None,
    apply: bool = False,
    backup_dir: Optional[Path] = None,
) -> Dict[str, Any]:
    """Preview or apply recovery, preserving files modified during inspection."""
    report: Dict[str, Any] = {"applied": apply, "sessions": [], "missing_files": []}
    if session_id is not None:
        report["session_id"] = session_id
    if apply:
        if backup_dir is None:
            stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
            backup_dir = db_path.parent / "backups" / stamp
        backup_dir.mkdir(parents=True, exist_ok=False)
        with sqlite3.connect(str(db_path)) as source:
            with sqlite3.connect(str(backup_dir / db_path.name)) as target:
                source.backup(target)
        report["backup_dir"] = str(backup_dir)

    for project in dict.fromkeys(path.resolve() for path in projects):
        for selected_id, rows in _read_rows(db_path, project, session_id).items():
            path = project / ".crystal" / "sessions" / f"{selected_id}.json"
            if not path.is_file():
                report["missing_files"].append(str(path))
                continue
            original = path.read_bytes()
            session = json.loads(original)
            native = (session.get("metadata") or {}).get("native_messages") or []
            missing = missing_rounds(native, rows)
            fixed = repair_session_metadata(session, [*rows, *missing])
            if not missing and fixed == session:
                continue
            entry = {
                "path": str(path),
                "missing_rounds": len(missing),
                "missing_ms": sum(row["duration_ms"] for row in missing),
                "metadata_changed": fixed != session,
            }
            report["sessions"].append(entry)
            if not apply:
                continue
            for row in missing:
                duration_store.record_request_duration(
                    db_path,
                    working_directory=str(project),
                    session_id=selected_id,
                    **row,
                )
            if fixed == session:
                continue
            assert backup_dir is not None
            if path.read_bytes() != original:
                entry["metadata_deferred"] = "session changed during recovery"
                continue
            destination = backup_dir / "sessions" / path.relative_to(path.anchor)
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(original)
            fd, temporary = tempfile.mkstemp(prefix=path.name, dir=path.parent)
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as stream:
                    json.dump(fixed, stream, ensure_ascii=False, indent=2)
                    stream.write("\n")
                if path.read_bytes() != original:
                    entry["metadata_deferred"] = "session changed during recovery"
                    continue
                os.replace(temporary, path)
            finally:
                if os.path.exists(temporary):
                    os.unlink(temporary)

    report["missing_rounds"] = sum(row["missing_rounds"] for row in report["sessions"])
    report["missing_ms"] = sum(row["missing_ms"] for row in report["sessions"])
    if apply:
        assert backup_dir is not None
        (backup_dir / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    return report


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--db", type=Path, required=True)
    parser.add_argument("--project", type=Path, action="append", required=True)
    parser.add_argument(
        "--session",
        dest="session_id",
        help="Recover only this session id within the selected project.",
    )
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    print(
        json.dumps(
            recover_projects(
                args.db, args.project, session_id=args.session_id, apply=args.apply
            ),
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
