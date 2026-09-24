"""The live handoff assessment matrix, parametrized from the configuration.

One case per handoff-assessed scenario, judged by the stage's declared
agent. The assessment loads the invocation's handoff records under the
run label and skips with the missing cells listed when a sliced run has
not produced them.
"""

from __future__ import annotations

import json

import pytest

from ..configuration import selected_artifact_root
from ..handoff_semantic import (
    handoff_semantic_prompt,
    load_handoff_records,
    parse_handoff_semantic,
    validate_handoff_semantic,
)
from ..scenarios import scenario_by_id
from ..stages import STAGES
from .matrix import CellCase, handoff_assessment_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.handoff_assessment]


@pytest.mark.parametrize("case", handoff_assessment_cases(), ids=lambda item: item.id)
@pytest.mark.requirements("TGEVAL-004", "TGEVAL-005", "TGEVAL-006", "TGEVAL-008")
def test_handoff_assessment(
    agent_harness,
    run_label: str,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    scenario = scenario_by_id(case.scenario_id)
    harness = agent_harness(case.agent)
    try:
        fresh, same = load_handoff_records(
            selected_artifact_root(),
            scenario=scenario,
            labels=[run_label],
            allow_partial=False,
        )
    except FileNotFoundError as error:
        pytest.skip(f"missing upstream records under label {run_label!r}: {error}")
    prompt = handoff_semantic_prompt(scenario, fresh, same)
    valid_count = sum(item.get("valid") is True for item in (*fresh, *same))
    runs = harness.run_assessment(
        test_id=f"task-guidance-handoff-semantic-{scenario.scenario_id}",
        prompt=prompt,
        reasoning_effort=case.effort,
        fresh=bool(run_options["fresh"]),
        samples=int(run_options["samples"]),
    )
    for run in runs:
        _record_assessment_run(scenario, run, fresh, same, valid_count)


def _record_assessment_run(
    scenario,
    run,
    fresh: list,
    same: list,
    valid_count: int,
) -> None:
    if run.value is None or run.error is not None:
        raise AssertionError(f"handoff semantic run failed: {run.error!r}")
    if not run.value.completed or run.value.errors:
        raise AssertionError(f"handoff semantic provider errors: {run.value.errors!r}")
    value = parse_handoff_semantic(run.value.response)
    validate_handoff_semantic(
        value,
        scenario=scenario,
        expected_count=valid_count,
    )
    run.record(
        STAGES["handoff-assessment"].record,
        {
            "schema_version": 1,
            "scenario_id": scenario.scenario_id,
            "fresh_records": fresh,
            "same_agent_records": same,
            "assessment": value,
        },
    )
    run.record(
        "task-guidance-handoff-semantic-summary.md",
        "# Task-guidance handoff semantic assessment\n\n"
        f"- Scenario: `{scenario.scenario_id}`\n"
        f"- Assessments: `{valid_count}`\n"
        f"- Raw JSON: `{json.dumps(value, sort_keys=True)[:1000]}`\n",
    )
