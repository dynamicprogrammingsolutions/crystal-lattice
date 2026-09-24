"""The live negative-control run, from the configuration's designation.

The control plans from the incomplete variant of the designated scenario's
canonical handoff task file: a run expected to come out worse than a
complete handoff, proving the evaluation can distinguish good from bad
handoffs. One designation per category, declared in the manifest.
"""

from __future__ import annotations

import pytest

from ..runner import PlanRunValue
from ..scenarios import scenario_by_id
from ..stages import STAGES
from .matrix import CellCase, negative_control_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.negative_control]


@pytest.mark.parametrize("case", negative_control_cases(), ids=lambda item: item.id)
@pytest.mark.requirements("TGEVAL-004", "TGEVAL-008")
def test_negative_control(
    agent_harness,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    assert case.variant is not None
    scenario = scenario_by_id(case.scenario_id)
    harness = agent_harness(case.agent)
    runs = harness.run_negative_control(
        category=case.category,
        fresh=bool(run_options["fresh"]),
        samples=int(run_options["samples"]),
    )
    for run in runs:
        _record_control_run(harness, scenario, case, run)


def _record_control_run(
    harness,
    scenario,
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
    record = {
        "schema_version": 1,
        "scenario_id": scenario.scenario_id,
        "variant": case.variant,
        "producer": {
            "profile": case.agent,
            "model": harness.agent["model"],
            "reasoning_effort": case.effort,
        },
        "response": value.response,
        "tool_metrics": value.tool_metrics,
        "task_files": value.task_files,
        "valid": not invalid,
        "invalid_reasons": invalid,
    }
    run.record(STAGES["negative-control"].record, record)
    assert not invalid, "\n".join(invalid)


def _require_value(value: PlanRunValue | None, error: object) -> PlanRunValue:
    if value is not None:
        return value
    raise AssertionError(f"negative control produced no value: {error!r}")
