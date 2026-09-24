"""The live fresh-agent planning matrix, parametrized from the configuration.

One case per handoff scenario × plan variant × producer cell. The
canonical handoff task file must stand alone: the run starts from a fresh
session and a fresh workspace, and planning must not mutate any file.
"""

from __future__ import annotations

import hashlib

import pytest

from ..runner import PlanRunValue
from ..scenarios import TaskGuidanceScenario, scenario_by_id
from ..stages import STAGES
from .matrix import CellCase, handoff_plan_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.handoff_plan]


@pytest.mark.parametrize("case", handoff_plan_cases(), ids=lambda item: item.id)
@pytest.mark.requirements(
    "TGEVAL-003",
    "TGEVAL-004",
    "TGEVAL-006",
    "TGEVAL-008",
    "TGEVAL-010",
)
def test_handoff_plan(
    agent_harness,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    assert case.variant is not None
    scenario = scenario_by_id(case.scenario_id)
    harness = agent_harness(case.agent)
    runs = harness.run_plan_from_handoff(
        scenario=scenario,
        variant=case.variant,
        reasoning_effort=case.effort,
        fresh=bool(run_options["fresh"]),
        samples=int(run_options["samples"]),
    )
    for run in runs:
        _record_plan_run(harness, scenario, case, run)


def _record_plan_run(
    harness,
    scenario: TaskGuidanceScenario,
    case: CellCase,
    run,
) -> None:
    value = _require_value(run.value, run.error)
    invalid: list[str] = []
    if run.error is not None or not value.completed or value.errors:
        invalid.append(f"run failure: {run.error!r}, {value.errors!r}")
    if not value.response.strip():
        invalid.append("empty planning response")
    if run.changed_paths:
        invalid.append(f"planning mutated files: {run.changed_paths!r}")
    if value.delivery.get("agents_occurrences") != 1:
        invalid.append("AGENTS.md delivery mismatch")
    if value.delivery.get("tasks_occurrences") != 1:
        invalid.append("TASKS-v7 delivery mismatch")
    record = {
        "schema_version": 1,
        "scenario_id": scenario.scenario_id,
        "variant": case.variant,
        "producer": {
            "profile": case.agent,
            "model": harness.agent["model"],
            "reasoning_effort": case.effort,
        },
        "target_sha256": hashlib.sha256(scenario.target_path.read_bytes()).hexdigest(),
        "target": scenario.target,
        "response": value.response,
        "tool_metrics": value.tool_metrics,
        "task_files": value.task_files,
        "delivery": value.delivery,
        "valid": not invalid,
        "invalid_reasons": invalid,
    }
    run.record(STAGES["handoff-plan"].record, record)
    assert not invalid, "\n".join(invalid)


def _require_value(value: PlanRunValue | None, error: object) -> PlanRunValue:
    if value is not None:
        return value
    raise AssertionError(f"handoff run produced no value: {error!r}")
