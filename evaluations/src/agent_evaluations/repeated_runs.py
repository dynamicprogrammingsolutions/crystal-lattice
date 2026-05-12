from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Sequence, Set, Tuple


def normalize_repeat_count(raw_value: Any) -> int:
    if raw_value is None:
        return 1
    value = int(raw_value)
    if value < 1:
        raise ValueError("repeat_count must be at least 1")
    return value


def task_instance_id(task_payload: Dict[str, Any]) -> str:
    raw = task_payload.get("task_instance_id")
    if isinstance(raw, str) and raw:
        return raw
    base_task_id = task_payload.get("task_id")
    if not isinstance(base_task_id, str) or not base_task_id:
        raise ValueError("task payload missing task_id")
    return base_task_id


def expand_task_payloads_with_repeats(
    tasks: Sequence[Dict[str, Any]],
    *,
    repeat_count: int,
) -> List[Dict[str, Any]]:
    normalized_repeat_count = normalize_repeat_count(repeat_count)
    expanded: List[Dict[str, Any]] = []
    for task in tasks:
        base_task_id = task.get("task_id")
        if not isinstance(base_task_id, str) or not base_task_id:
            raise ValueError("benchmark manifest task missing task_id")
        for repeat_index in range(normalized_repeat_count):
            payload = deepcopy(task)
            payload["repeat_count"] = normalized_repeat_count
            payload["repeat_index"] = repeat_index
            payload["task_instance_id"] = (
                base_task_id if normalized_repeat_count == 1 else f"{base_task_id}#r{repeat_index + 1}"
            )
            expanded.append(payload)
    return expanded


def aggregate_results_by_task_id(results: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    grouped: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for item in results:
        task_payload = item.get("task") if isinstance(item.get("task"), dict) else {}
        task_id = task_payload.get("task_id") or item.get("task_id")
        if not isinstance(task_id, str) or not task_id:
            continue
        grouped[task_id].append(item)

    aggregates: List[Dict[str, Any]] = []
    for task_id in sorted(grouped):
        instances = sorted(
            grouped[task_id],
            key=lambda item: (
                int(item.get("repeat_index", 0) or 0),
                str(item.get("task_instance_id") or ""),
            ),
        )
        task_payload = instances[0].get("task")
        repeat_count = max(int(item.get("repeat_count", 1) or 1) for item in instances)
        eligible_instances = [item for item in instances if item.get("eligible_for_accuracy", True)]
        matched_instances = [
            item for item in eligible_instances if ((item.get("score") or {}).get("matched") is True)
        ]
        outcome_counts: Dict[str, int] = defaultdict(int)
        state_counts: Dict[str, int] = defaultdict(int)
        failure_category_counts: Dict[str, int] = defaultdict(int)
        costs = [float(item["cost"]) for item in instances if isinstance(item.get("cost"), (int, float))]
        instance_summaries = []
        for item in instances:
            outcome = item.get("outcome")
            state = item.get("state")
            failure_category = item.get("failure_category")
            if isinstance(outcome, str):
                outcome_counts[outcome] += 1
            if isinstance(state, str):
                state_counts[state] += 1
            if isinstance(failure_category, str) and failure_category:
                failure_category_counts[failure_category] += 1
            instance_summaries.append(
                {
                    "task_instance_id": item.get("task_instance_id"),
                    "repeat_index": item.get("repeat_index"),
                    "outcome": outcome,
                    "state": state,
                    "eligible_for_accuracy": item.get("eligible_for_accuracy", True),
                    "matched": ((item.get("score") or {}).get("matched") is True),
                    "score": float((item.get("score") or {}).get("score") or 0.0),
                    "cost": item.get("cost"),
                    "imported_result": bool(item.get("imported_result")),
                    "import_mode": item.get("import_mode"),
                    "finished_at": item.get("finished_at"),
                }
            )

        eligible_instance_count = len(eligible_instances)
        matched_instance_count = len(matched_instances)
        success_rate = (
            matched_instance_count / eligible_instance_count if eligible_instance_count > 0 else None
        )
        aggregates.append(
            {
                "task_id": task_id,
                "task": task_payload,
                "repeat_count": repeat_count,
                "completed_instance_count": len(instances),
                "eligible_instance_count": eligible_instance_count,
                "matched_instance_count": matched_instance_count,
                "success_rate": success_rate,
                "excluded_missing_target_context_count": outcome_counts.get("skipped_missing_target_context", 0),
                "imported_instance_count": sum(1 for item in instances if item.get("imported_result") is True),
                "outcome_counts": dict(sorted(outcome_counts.items())),
                "state_counts": dict(sorted(state_counts.items())),
                "failure_category_counts": dict(sorted(failure_category_counts.items())),
                "cost_total": sum(costs) if costs else None,
                "cost_average": (sum(costs) / len(costs)) if costs else None,
                "instance_results": instance_summaries,
            }
        )
    return aggregates


def _load_jsonl_rows(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        return []
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


def _logical_task_payload(task_payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        key: value
        for key, value in task_payload.items()
        if key not in {"planned_start_at", "repeat_count", "repeat_index", "task_instance_id"}
    }


def _task_payloads_by_instance_id(tasks: Sequence[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    indexed: Dict[str, Dict[str, Any]] = {}
    for task in tasks:
        if not isinstance(task, dict):
            raise ValueError("run manifest tasks must be objects")
        instance_id = task_instance_id(task)
        if instance_id in indexed:
            raise ValueError(f"Duplicate task_instance_id in run manifest: {instance_id}")
        indexed[instance_id] = task
    return indexed


def validate_result_row_against_task_payload(
    row: Dict[str, Any],
    task_payload: Dict[str, Any],
) -> None:
    instance_id = task_instance_id(task_payload)
    row_instance_id = row.get("task_instance_id")
    if row_instance_id != instance_id:
        raise ValueError(
            f"Result row task_instance_id mismatch: expected {instance_id!r}, got {row_instance_id!r}"
        )

    row_repeat_index = int(row.get("repeat_index") or 0)
    task_repeat_index = int(task_payload.get("repeat_index") or 0)
    if row_repeat_index != task_repeat_index:
        raise ValueError(
            f"Result row repeat_index mismatch for {instance_id!r}: "
            f"expected {task_repeat_index}, got {row_repeat_index}"
        )

    row_task = row.get("task")
    if not isinstance(row_task, dict):
        raise ValueError(f"Result row {instance_id!r} missing task payload")
    expected_task = _logical_task_payload(task_payload)
    if row_task != expected_task:
        raise ValueError(f"Result row task payload mismatch for {instance_id!r}")

    row_task_id = row_task.get("task_id") or row.get("task_id")
    task_id = task_payload.get("task_id")
    if row_task_id != task_id:
        raise ValueError(
            f"Result row task_id mismatch for {instance_id!r}: expected {task_id!r}, got {row_task_id!r}"
        )


def select_result_rows_for_manifest(
    rows: Sequence[Dict[str, Any]],
    tasks: Sequence[Dict[str, Any]],
    *,
    require_all_known: bool,
) -> List[Dict[str, Any]]:
    indexed_tasks = _task_payloads_by_instance_id(tasks)
    selected: List[Dict[str, Any]] = []
    seen_instance_ids: Set[str] = set()
    for row in rows:
        if not isinstance(row, dict):
            raise ValueError("Result rows must be objects")
        instance_id = row.get("task_instance_id")
        if not isinstance(instance_id, str) or not instance_id:
            raise ValueError("Result row missing task_instance_id")
        task_payload = indexed_tasks.get(instance_id)
        if task_payload is None:
            if require_all_known:
                raise ValueError(f"Result row refers to unknown task_instance_id {instance_id!r}")
            continue
        validate_result_row_against_task_payload(row, task_payload)
        if instance_id in seen_instance_ids:
            raise ValueError(f"Duplicate result row for task_instance_id {instance_id!r}")
        seen_instance_ids.add(instance_id)
        selected.append(row)
    return selected


def load_existing_results_for_manifest(
    results_jsonl_path: Path,
    tasks: Sequence[Dict[str, Any]],
) -> Tuple[List[Dict[str, Any]], Set[str]]:
    rows = _load_jsonl_rows(results_jsonl_path)
    selected = select_result_rows_for_manifest(rows, tasks, require_all_known=True)
    return selected, {str(row["task_instance_id"]) for row in selected}