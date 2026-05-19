from __future__ import annotations

from datetime import datetime, timedelta, timezone

from agent_evaluations.scheduler import plan_task_starts, policy_from_config


def test_plan_task_starts_enforces_window_quota_without_randomness() -> None:
    policy = policy_from_config(
        {
            "window_minutes": 60,
            "tasks_per_window": 10,
            "max_parallel_tasks": 3,
            "randomize_task_starts": False,
        }
    )
    anchor = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    starts = plan_task_starts(task_count=12, anchor=anchor, policy=policy)

    assert len(starts) == 12
    assert all(start == anchor for start in starts[:10])
    assert all(start == anchor + timedelta(hours=1) for start in starts[10:])


def test_plan_task_starts_randomizes_within_each_window() -> None:
    policy = policy_from_config(
        {
            "window_minutes": 60,
            "tasks_per_window": 3,
            "max_parallel_tasks": 2,
            "randomize_task_starts": True,
            "random_seed": 7,
        }
    )
    anchor = datetime(2025, 1, 1, 12, 0, tzinfo=timezone.utc)
    starts = plan_task_starts(task_count=4, anchor=anchor, policy=policy)

    assert len(starts) == 4
    assert starts[:3] == sorted(starts[:3])
    assert all(anchor <= start <= anchor + timedelta(hours=1) for start in starts[:3])
    assert anchor + timedelta(hours=1) <= starts[3] <= anchor + timedelta(hours=2)
