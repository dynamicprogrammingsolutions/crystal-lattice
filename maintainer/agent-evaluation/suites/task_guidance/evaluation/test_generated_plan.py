"""The live fresh-agent generated-file planning matrix.

One case per generated-file planning scenario × producer cell. Each case
first produces — or replays — the parent task-creation run, then a fresh
session plans from exactly the files the producer wrote: no producer
session, no scratch state. The files must stand alone.
"""

from __future__ import annotations

import pytest

from ..runner import PlanRunValue, TaskRunValue
from ..scenarios import TaskGuidanceScenario, scenario_by_id
from ..stages import STAGES
from .matrix import CellCase, generated_plan_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.generated_plan]


@pytest.mark.parametrize("case", generated_plan_cases(), ids=lambda item: item.id)
def test_generated_plan(
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
        if not parent_value.task_files:
            raise AssertionError("parent task creation produced no task files")
        runs = harness.run_plan_from_generated(
            parent=parent,
            scenario=scenario,
            reasoning_effort=case.effort,
            fresh=bool(run_options["fresh"]),
            samples=int(run_options["samples"]),
        )
        for run in runs:
            _record_generated_plan_run(harness, scenario, case, run, parent_value)


def _record_generated_plan_run(
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
        "planning_tool_metrics": value.tool_metrics,
        "valid": not invalid,
        "invalid_reasons": invalid,
    }
    run.record(STAGES["generated-plan"].record, record)
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
    raise AssertionError(f"planning produced no value: {error!r}")
