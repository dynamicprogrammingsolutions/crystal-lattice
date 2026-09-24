from __future__ import annotations

import json
from pathlib import Path

from ..results import consolidate_results, render_summary


def _write_record(root: Path, name: str, value: dict[str, object]) -> None:
    path = root / name / "records" / "task-guidance-producer.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(value), encoding="utf-8")


def test_consolidation_separates_invalid_and_missing_records(
    tmp_path: Path,
) -> None:
    _write_record(
        tmp_path,
        "glm",
        {
            "scenario_id": "tg01-eleventy-archive-handoff",
            "producer": {"profile": "glm", "reasoning_effort": "max"},
            "run_attempt": "r1",
            "valid": True,
            "invalid_reasons": [],
            "task_files": {"tasks/demo.md": "# Demo\n"},
        },
    )
    _write_record(
        tmp_path,
        "gpt",
        {
            "scenario_id": "tg01-eleventy-archive-handoff",
            "producer": {"profile": "gpt", "reasoning_effort": "high"},
            "run_attempt": "r1",
            "valid": False,
            "invalid_reasons": ["provider errors: provider limit"],
            "task_files": {},
        },
    )

    value = consolidate_results(tmp_path, labels=["r1"])

    status = value["status"]["producers"]
    assert status["valid"] == 1
    assert status["invalid"] == 1
    assert status["present"] == 2
    assert value["producer_records"][0]["task_tree"]["implementation_task_count"] in {
        0,
        1,
    }
    assert value["status"]["handoff_semantics"]["expected"] == 3
    assert value["status"]["negative_controls"]["expected"] == 1
    assert value["status"]["provider_blockers"]["present"] == 1
    assert "provider limit" in render_summary(value)
