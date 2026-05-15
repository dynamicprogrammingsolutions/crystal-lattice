from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Set


def _load_json_object(path: Path) -> Dict[str, Any]:
    loaded = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(loaded, dict):
        raise ValueError(f"Expected JSON object in {path}")
    return loaded


def _load_jsonl_objects(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line_number, raw_line in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        stripped = raw_line.strip()
        if not stripped:
            continue
        loaded = json.loads(stripped)
        if not isinstance(loaded, dict):
            raise ValueError(f"Expected JSON object in {path} line {line_number}")
        rows.append(loaded)
    return rows


def is_task_fully_solved(aggregate: Dict[str, Any]) -> bool:
    repeat_count = int(aggregate.get("repeat_count") or 1)
    completed_instance_count = int(aggregate.get("completed_instance_count") or 0)
    eligible_instance_count = int(aggregate.get("eligible_instance_count") or 0)
    matched_instance_count = int(aggregate.get("matched_instance_count") or 0)
    excluded_missing_target_context_count = int(
        aggregate.get("excluded_missing_target_context_count") or 0
    )
    return (
        completed_instance_count == repeat_count
        and eligible_instance_count == repeat_count
        and matched_instance_count == repeat_count
        and excluded_missing_target_context_count == 0
    )


def collect_fully_solved_task_ids(aggregates: Iterable[Dict[str, Any]]) -> Set[str]:
    solved_task_ids: Set[str] = set()
    for aggregate in aggregates:
        if not is_task_fully_solved(aggregate):
            continue
        task_id = aggregate.get("task_id")
        if isinstance(task_id, str) and task_id:
            solved_task_ids.add(task_id)
    return solved_task_ids


def build_filtered_manifest(
    manifest: Dict[str, Any],
    *,
    excluded_task_ids: Set[str],
) -> Dict[str, Any]:
    tasks = manifest.get("tasks")
    if not isinstance(tasks, list):
        raise ValueError("Manifest must contain a tasks list")

    filtered_tasks = [
        task
        for task in tasks
        if isinstance(task, dict)
        and isinstance(task.get("task_id"), str)
        and task["task_id"] not in excluded_task_ids
    ]

    return {
        **manifest,
        "task_count": len(filtered_tasks),
        "tasks": filtered_tasks,
        "excluded_fully_solved_task_ids": sorted(excluded_task_ids),
        "excluded_fully_solved_task_count": len(excluded_task_ids),
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Filter a RepoQA prompted manifest to remove tasks solved on every repeat."
    )
    parser.add_argument("--input-manifest", required=True)
    parser.add_argument("--task-aggregate-jsonl", required=True)
    parser.add_argument("--output-manifest", required=True)
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    manifest_path = Path(args.input_manifest).expanduser()
    aggregate_path = Path(args.task_aggregate_jsonl).expanduser()
    output_path = Path(args.output_manifest).expanduser()

    manifest = _load_json_object(manifest_path)
    aggregates = _load_jsonl_objects(aggregate_path)
    excluded_task_ids = collect_fully_solved_task_ids(aggregates)
    filtered_manifest = build_filtered_manifest(
        manifest,
        excluded_task_ids=excluded_task_ids,
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(filtered_manifest, indent=2, sort_keys=True) + "\n", encoding="utf-8")

    print(
        json.dumps(
            {
                "input_manifest": str(manifest_path),
                "task_aggregate_jsonl": str(aggregate_path),
                "output_manifest": str(output_path),
                "input_task_count": len(manifest.get("tasks") or []),
                "excluded_fully_solved_task_count": len(excluded_task_ids),
                "output_task_count": len(filtered_manifest.get("tasks") or []),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())