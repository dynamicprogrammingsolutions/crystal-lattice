from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, time, timedelta, timezone
import random
import time as time_mod
from typing import Any, Dict, Iterable, List, Optional
from zoneinfo import ZoneInfo

from .utils import isoformat_utc


_WEEKDAY_MAP = {
    "mon": 0,
    "monday": 0,
    "tue": 1,
    "tuesday": 1,
    "wed": 2,
    "wednesday": 2,
    "thu": 3,
    "thursday": 3,
    "fri": 4,
    "friday": 4,
    "sat": 5,
    "saturday": 5,
    "sun": 6,
    "sunday": 6,
}


def _parse_hhmm(raw: str, *, end_of_day: bool = False) -> int:
    parts = raw.strip().split(":")
    if len(parts) != 2:
        raise ValueError(f"Invalid HH:MM time: {raw!r}")
    hour = int(parts[0])
    minute = int(parts[1])
    if end_of_day and hour == 24 and minute == 0:
        return 24 * 60
    if hour < 0 or hour > 23 or minute < 0 or minute > 59:
        raise ValueError(f"Invalid HH:MM time: {raw!r}")
    return hour * 60 + minute


def _tz_name(raw: Any) -> str:
    if isinstance(raw, str) and raw.strip():
        return raw.strip()
    return "UTC"


@dataclass(frozen=True)
class WorkingHoursWindow:
    start_minute: int
    end_minute: int


@dataclass(frozen=True)
class TaskStartPolicy:
    timezone_name: str
    window_minutes: int
    tasks_per_window: int
    max_parallel_tasks: int
    randomize_task_starts: bool
    random_seed: int
    allowed_weekdays: Optional[set[int]]
    working_hours: List[WorkingHoursWindow]
    max_tasks_per_day: Optional[int]

    @property
    def timezone(self) -> ZoneInfo:
        return ZoneInfo(self.timezone_name)


def policy_from_config(
    raw: Dict[str, Any],
    *,
    default_seed: int = 0,
) -> TaskStartPolicy:
    weekdays_raw = raw.get("allowed_weekdays")
    weekday_set: Optional[set[int]] = None
    if isinstance(weekdays_raw, list) and weekdays_raw:
        weekday_set = set()
        for item in weekdays_raw:
            if not isinstance(item, str):
                continue
            key = item.strip().lower()
            if key in _WEEKDAY_MAP:
                weekday_set.add(_WEEKDAY_MAP[key])

    windows: List[WorkingHoursWindow] = []
    working_hours_raw = raw.get("working_hours")
    if isinstance(working_hours_raw, list):
        for item in working_hours_raw:
            if not isinstance(item, dict):
                continue
            start = item.get("start")
            end = item.get("end")
            if not isinstance(start, str) or not isinstance(end, str):
                continue
            windows.append(
                WorkingHoursWindow(
                    start_minute=_parse_hhmm(start),
                    end_minute=_parse_hhmm(end, end_of_day=True),
                )
            )

    window_minutes = int(raw.get("window_minutes") or 60)
    tasks_per_window = int(raw.get("tasks_per_window") or raw.get("max_tasks_per_window") or 10)
    max_parallel_tasks = int(raw.get("max_parallel_tasks") or 1)
    randomize = bool(raw.get("randomize_task_starts", False))
    random_seed = int(raw.get("random_seed") or default_seed)
    max_tasks_per_day = raw.get("max_tasks_per_day")
    if max_tasks_per_day is not None:
        max_tasks_per_day = int(max_tasks_per_day)

    return TaskStartPolicy(
        timezone_name=_tz_name(raw.get("timezone")),
        window_minutes=max(1, window_minutes),
        tasks_per_window=max(1, tasks_per_window),
        max_parallel_tasks=max(1, max_parallel_tasks),
        randomize_task_starts=randomize,
        random_seed=random_seed,
        allowed_weekdays=weekday_set,
        working_hours=windows,
        max_tasks_per_day=max_tasks_per_day,
    )


def _local_minutes(dt: datetime) -> int:
    return dt.hour * 60 + dt.minute


def is_allowed_start(dt: datetime, policy: TaskStartPolicy) -> bool:
    local_dt = dt.astimezone(policy.timezone)
    if policy.allowed_weekdays is not None and local_dt.weekday() not in policy.allowed_weekdays:
        return False
    if not policy.working_hours:
        return True
    minute = _local_minutes(local_dt)
    return any(window.start_minute <= minute < window.end_minute for window in policy.working_hours)


def _first_window_start_for_day(day: date, policy: TaskStartPolicy) -> datetime:
    tz = policy.timezone
    if policy.working_hours:
        minute = min(window.start_minute for window in policy.working_hours)
        hour = minute // 60
        minute_part = minute % 60
        return datetime(day.year, day.month, day.day, hour, minute_part, tzinfo=tz)
    return datetime(day.year, day.month, day.day, 0, 0, tzinfo=tz)


def next_allowed_start(dt: datetime, policy: TaskStartPolicy) -> datetime:
    current = dt.astimezone(policy.timezone)
    for _ in range(370):
        weekday_ok = policy.allowed_weekdays is None or current.weekday() in policy.allowed_weekdays
        if weekday_ok:
            if not policy.working_hours:
                return current

            minute = _local_minutes(current)
            for window in sorted(policy.working_hours, key=lambda item: item.start_minute):
                if minute < window.start_minute:
                    hour = window.start_minute // 60
                    minute_part = window.start_minute % 60
                    return current.replace(hour=hour, minute=minute_part, second=0, microsecond=0)
                if window.start_minute <= minute < window.end_minute:
                    return current

        next_day = current.date() + timedelta(days=1)
        current = _first_window_start_for_day(next_day, policy)
    raise RuntimeError("Could not find the next allowed start time within one year")


def plan_task_starts(
    *,
    task_count: int,
    anchor: datetime,
    policy: TaskStartPolicy,
) -> List[datetime]:
    if task_count <= 0:
        return []

    rng = random.Random(policy.random_seed)
    window_duration = timedelta(minutes=policy.window_minutes)
    current_window_start = next_allowed_start(anchor, policy)
    starts: List[datetime] = []
    tasks_per_day: Dict[date, int] = {}

    while len(starts) < task_count:
        current_window_start = next_allowed_start(current_window_start, policy)
        local_day = current_window_start.astimezone(policy.timezone).date()
        day_used = tasks_per_day.get(local_day, 0)
        if policy.max_tasks_per_day is not None and day_used >= policy.max_tasks_per_day:
            current_window_start = _first_window_start_for_day(local_day + timedelta(days=1), policy)
            continue

        window_capacity = policy.tasks_per_window
        if policy.max_tasks_per_day is not None:
            window_capacity = min(window_capacity, policy.max_tasks_per_day - day_used)

        remaining = task_count - len(starts)
        count = min(window_capacity, remaining)
        if count <= 0:
            current_window_start = _first_window_start_for_day(local_day + timedelta(days=1), policy)
            continue

        if policy.randomize_task_starts:
            offsets = sorted(rng.uniform(0.0, window_duration.total_seconds()) for _ in range(count))
            starts.extend(current_window_start + timedelta(seconds=offset) for offset in offsets)
        else:
            starts.extend(current_window_start for _ in range(count))

        tasks_per_day[local_day] = day_used + count
        current_window_start = current_window_start + window_duration

    return starts


def sleep_until(target: datetime, *, reason: str | None = None) -> Dict[str, Any]:
    now = datetime.now(timezone.utc)
    if target <= now:
        return {
            "reason": reason or "already_due",
            "slept_seconds": 0.0,
            "target_time": isoformat_utc(target),
        }

    delay = (target - now).total_seconds()
    time_mod.sleep(delay)
    return {
        "reason": reason or "waiting_for_planned_start",
        "slept_seconds": delay,
        "target_time": isoformat_utc(target),
    }
