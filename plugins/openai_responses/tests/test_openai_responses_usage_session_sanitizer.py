from __future__ import annotations

import json
import subprocess
from pathlib import Path

from openai_responses_plugins.openai_responses_usage_session_sanitizer import (
    sanitize_session_payload,
)

SANITIZER_SCRIPT = (
    Path(__file__).resolve().parents[1] / "scripts" / "sanitize_session_usage.py"
)


def _usage() -> dict[str, object]:
    return {
        "input_tokens": 100,
        "output_tokens": 20,
        "future_scalar": "preserved",
        "attribution": {
            "request_fields": {"model": "gpt-test"},
            "items": [{"input_tokens": 100, "content": "repeated"}],
        },
    }


def _session_payload(session_id: str = "session-1") -> dict[str, object]:
    return {
        "session_id": session_id,
        "messages": [
            {
                "role": "assistant",
                "content": "answer",
                "metadata": {
                    "usage": _usage(),
                    "phase_messages": [
                        {
                            "phase": "final_answer",
                            "content": "answer",
                            "metadata": {"usage": _usage()},
                        }
                    ],
                },
            }
        ],
        "metadata": {
            "native_messages": [
                {
                    "type": "message",
                    "role": "assistant",
                    "content": [{"type": "output_text", "text": "answer"}],
                    "_metadata": {
                        "usage": _usage(),
                        "_openai_responses_usage_raw": _usage(),
                    },
                }
            ],
            "native_messages_integrity": {
                "message_count": 1,
                "total_chars": 6,
            },
            "unrelated": {"usage": _usage()},
        },
    }


def test_sanitize_session_payload_is_targeted_and_idempotent() -> None:
    original = _session_payload()

    sanitized, counts = sanitize_session_payload(original)
    sanitized_again, second_counts = sanitize_session_payload(sanitized)

    assert counts == {"core": 1, "phase": 1, "native": 1, "private": 1}
    assert second_counts == {"core": 0, "phase": 0, "native": 0, "private": 0}
    assert sanitized_again is sanitized
    assert sanitized["messages"][0]["content"] == "answer"
    assert sanitized["messages"][0]["metadata"]["usage"] == {
        "input_tokens": 100,
        "output_tokens": 20,
        "future_scalar": "preserved",
    }
    phase_usage = sanitized["messages"][0]["metadata"]["phase_messages"][0]["metadata"][
        "usage"
    ]
    assert phase_usage == {
        "input_tokens": 100,
        "output_tokens": 20,
        "future_scalar": "preserved",
    }
    native_metadata = sanitized["metadata"]["native_messages"][0]["_metadata"]
    assert "attribution" not in native_metadata["usage"]
    assert "attribution" not in native_metadata["_openai_responses_usage_raw"]
    assert sanitized["metadata"]["unrelated"] == original["metadata"]["unrelated"]
    assert original["messages"][0]["metadata"]["usage"]["attribution"]


def test_sanitizer_command_dry_run_and_apply(
    tmp_path: Path,
) -> None:
    session_root = tmp_path / "sessions"
    backup_root = tmp_path / "migration-backups"
    session_root.mkdir()
    session_path = session_root / "session-1.json"
    session_path.write_text(json.dumps(_session_payload(), indent=2), encoding="utf-8")
    snapshot_root = session_root / ".snapshots"
    snapshot_root.mkdir()
    snapshot_path = snapshot_root / "session-1.123.json"
    snapshot_payload = {
        **_session_payload(),
        "snapshot_id": "session-1.123",
        "readonly": True,
        "snapshot_created_at": "2026-09-12T00:00:00Z",
        "snapshot_reason": "test",
        "snapshot_metadata": {},
    }
    snapshot_path.write_text(json.dumps(snapshot_payload, indent=2), encoding="utf-8")

    dry_run = subprocess.run(
        [str(SANITIZER_SCRIPT), "--session-root", str(session_root)],
        check=True,
        capture_output=True,
        text=True,
    )
    dry_report = json.loads(dry_run.stdout)
    assert dry_report["totals"]["files_would_change"] == 2
    assert dry_report["totals"]["files_would_change_by_kind"] == {
        "session": 1,
        "snapshot": 1,
    }
    assert dry_report["totals"]["occurrences"] == {
        "core": 2,
        "phase": 2,
        "native": 2,
        "private": 2,
    }
    assert "attribution" in session_path.read_text(encoding="utf-8")
    assert "attribution" in snapshot_path.read_text(encoding="utf-8")

    apply_run = subprocess.run(
        [
            str(SANITIZER_SCRIPT),
            "--session-root",
            str(session_root),
            "--apply",
            "--backup-dir",
            str(backup_root),
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    apply_report = json.loads(apply_run.stdout)
    assert apply_report["totals"]["files_changed"] == 2
    assert apply_report["totals"]["files_changed_by_kind"] == {
        "session": 1,
        "snapshot": 1,
    }
    assert all(
        Path(item["backup_path"]).is_file()
        for item in apply_report["files"]
        if item["status"] == "changed"
    )
    published = json.loads(session_path.read_text(encoding="utf-8"))
    assert "attribution" not in published["messages"][0]["metadata"]["usage"]
    assert (
        "attribution"
        not in published["messages"][0]["metadata"]["phase_messages"][0]["metadata"][
            "usage"
        ]
    )
    assert (
        "attribution"
        not in published["metadata"]["native_messages"][0]["_metadata"]["usage"]
    )
    assert "attribution" in published["metadata"]["unrelated"]["usage"]
    published_snapshot = json.loads(snapshot_path.read_text(encoding="utf-8"))
    assert "attribution" not in published_snapshot["messages"][0]["metadata"]["usage"]
    assert published_snapshot["snapshot_id"] == "session-1.123"
    assert published_snapshot["readonly"] is True

    second_run = subprocess.run(
        [str(SANITIZER_SCRIPT), "--session-root", str(session_root)],
        check=True,
        capture_output=True,
        text=True,
    )
    second_report = json.loads(second_run.stdout)
    assert second_report["totals"]["files_would_change"] == 0
