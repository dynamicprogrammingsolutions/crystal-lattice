from __future__ import annotations

from collections import defaultdict
from copy import deepcopy
from typing import Any, Dict, Iterable, List, Sequence


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
                "outcome_counts": dict(sorted(outcome_counts.items())),
                "state_counts": dict(sorted(state_counts.items())),
                "failure_category_counts": dict(sorted(failure_category_counts.items())),
                "cost_total": sum(costs) if costs else None,
                "cost_average": (sum(costs) / len(costs)) if costs else None,
                "instance_results": instance_summaries,
            }
        )
    return aggregates