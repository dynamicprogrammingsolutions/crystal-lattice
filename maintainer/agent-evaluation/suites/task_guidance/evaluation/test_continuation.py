"""The live same-agent continuation matrix, parametrized from the configuration.

One case per continuation scenario × producer cell. The continuation
shares the task-creation run's workspace (the produced task files stay in
place) and its session prefix, so each case first produces — or replays —
the parent task-creation run, then continues from it.
"""

from __future__ import annotations

import pytest

from ..runner import PlanRunValue, TaskRunValue
from ..scenarios import TaskGuidanceScenario, scenario_by_id
from ..stages import STAGES
from .matrix import CellCase, continuation_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.continuation]


@pytest.mark.parametrize("case", continuation_cases(), ids=lambda item: item.id)
@pytest.mark.requirements("TGEVAL-005", "TGEVAL-008", "TGEVAL-010")
def test_continuation(
    agent_harness,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    scenario = scenario_by_id(case.scenario_id)
    harness = agent_harness(case.agent)
    parents = harness.run_task_creation(
        scenario=scenario,
        reasoning_effort=case.effort,
        fresh=bool(run_options["fresh"]),
        samples=int(run_options["samples"]),
    )
    for parent in parents:
        parent_value = _require_task_value(parent.value, parent.error)
        _require_valid_parent(harness, scenario, case, parent, parent_value)
        runs = harness.continue_same_agent_plan(
            parent=parent,
            scenario=scenario,
            reasoning_effort=case.effort,
            fresh=bool(run_options["fresh"]),
            samples=int(run_options["samples"]),
        )
        for run in runs:
            _record_continuation_run(harness, scenario, case, run, parent_value)


def _require_valid_parent(
    harness,
    scenario: TaskGuidanceScenario,
    case: CellCase,
    parent,
    parent_value: TaskRunValue,
) -> None:
    parent_invalid: list[str] = []
    if parent.error is not None:
        parent_invalid.append(f"parent run error: {parent.error!r}")
    if not parent_value.completed or parent_value.errors:
        parent_invalid.append(
            "parent provider failure: "
            f"completed={parent_value.completed!r}, "
            f"errors={parent_value.errors!r}"
        )
    if not parent_value.response.strip():
        parent_invalid.append("parent assistant response is empty")
    if not parent_value.task_files:
        parent_invalid.append("parent task creation produced no task files")
    if parent_value.delivery.get("agents_occurrences") != 1:
        parent_invalid.append("parent AGENTS.md delivery mismatch")
    if parent_value.delivery.get("tasks_occurrences") != 1:
        parent_invalid.append("parent TASKS-v7 delivery mismatch")
    if parent_value.delivery.get("tool_family_matches") is not True:
        parent_invalid.append("parent model-family tool schema mismatch")
    if parent_invalid:
        raise AssertionError("\n".join(parent_invalid))


def _record_continuation_run(
    harness,
    scenario: TaskGuidanceScenario,
    case: CellCase,
    run,
    parent_value: TaskRunValue,
) -> None:
    value = _require_plan_value(run.value, run.error)
    invalid: list[str] = []
    if run.error is not None or not value.completed or value.errors:
        invalid.append(f"run failure: {run.error!r}, {value.errors!r}")
    if not value.response.strip():
        invalid.append("empty planning response")
    if value.mutation_count:
        invalid.append(f"planning used mutation tools: {value.mutation_count}")
    if dict(value.task_files) != dict(parent_value.task_files):
        invalid.append("planning changed the generated task files")
    record = {
        "schema_version": 1,
        "scenario_id": scenario.scenario_id,
        "producer": {
            "profile": case.agent,
            "model": harness.agent["model"],
            "reasoning_effort": case.effort,
        },
        "target": scenario.target,
        "task_files": parent_value.task_files,
        "response": value.response,
        "task_creation_tool_metrics": parent_value.tool_metrics,
        "continuation_tool_metrics": value.tool_metrics,
        "valid": not invalid,
        "invalid_reasons": invalid,
    }
    run.record(STAGES["continuation"].record, record)
    assert not invalid, "\n".join(invalid)


def _require_task_value(
    value: TaskRunValue | None,
    error: object,
) -> TaskRunValue:
    if value is not None:
        return value
    raise AssertionError(f"task creation produced no value: {error!r}")


def _require_plan_value(
    value: PlanRunValue | None,
    error: object,
) -> PlanRunValue:
    if value is not None:
        return value
    raise AssertionError(f"continuation produced no value: {error!r}")
