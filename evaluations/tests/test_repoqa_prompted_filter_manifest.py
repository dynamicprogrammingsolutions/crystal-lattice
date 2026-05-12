from __future__ import annotations

import importlib.util
from pathlib import Path


MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "benchmarks"
    / "repoqa_prompted"
    / "filter_manifest_by_success.py"
)
SPEC = importlib.util.spec_from_file_location("repoqa_prompted_filter_manifest", MODULE_PATH)
if SPEC is None or SPEC.loader is None:
    raise RuntimeError(f"Could not load module from {MODULE_PATH}")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)

build_filtered_manifest = MODULE.build_filtered_manifest
collect_fully_solved_task_ids = MODULE.collect_fully_solved_task_ids
is_task_fully_solved = MODULE.is_task_fully_solved


def test_is_task_fully_solved_requires_all_repeats_matched_without_exclusions() -> None:
    assert is_task_fully_solved(
        {
            "task_id": "task-a",
            "repeat_count": 3,
            "completed_instance_count": 3,
            "eligible_instance_count": 3,
            "matched_instance_count": 3,
            "excluded_missing_target_context_count": 0,
        }
    )

    assert not is_task_fully_solved(
        {
            "task_id": "task-b",
            "repeat_count": 3,
            "completed_instance_count": 3,
            "eligible_instance_count": 3,
            "matched_instance_count": 2,
            "excluded_missing_target_context_count": 0,
        }
    )

    assert not is_task_fully_solved(
        {
            "task_id": "task-c",
            "repeat_count": 3,
            "completed_instance_count": 3,
            "eligible_instance_count": 2,
            "matched_instance_count": 2,
            "excluded_missing_target_context_count": 1,
        }
    )


def test_collect_and_filter_manifest_preserves_unsolved_tasks_in_order() -> None:
    manifest = {
        "benchmark": "repoqa-prompted",
        "task_count": 3,
        "tasks": [
            {"task_id": "task-a", "path": "a.py"},
            {"task_id": "task-b", "path": "b.py"},
            {"task_id": "task-c", "path": "c.py"},
        ],
    }
    aggregates = [
        {
            "task_id": "task-a",
            "repeat_count": 3,
            "completed_instance_count": 3,
            "eligible_instance_count": 3,
            "matched_instance_count": 3,
            "excluded_missing_target_context_count": 0,
        },
        {
            "task_id": "task-b",
            "repeat_count": 3,
            "completed_instance_count": 3,
            "eligible_instance_count": 3,
            "matched_instance_count": 1,
            "excluded_missing_target_context_count": 0,
        },
        {
            "task_id": "task-c",
            "repeat_count": 3,
            "completed_instance_count": 3,
            "eligible_instance_count": 2,
            "matched_instance_count": 2,
            "excluded_missing_target_context_count": 1,
        },
    ]

    excluded_task_ids = collect_fully_solved_task_ids(aggregates)
    filtered_manifest = build_filtered_manifest(manifest, excluded_task_ids=excluded_task_ids)

    assert excluded_task_ids == {"task-a"}
    assert filtered_manifest["task_count"] == 2
    assert [task["task_id"] for task in filtered_manifest["tasks"]] == ["task-b", "task-c"]
    assert filtered_manifest["excluded_fully_solved_task_ids"] == ["task-a"]