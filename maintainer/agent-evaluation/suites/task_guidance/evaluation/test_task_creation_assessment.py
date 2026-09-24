"""The live task-creation assessment matrix, parametrized from the configuration.

One case per assessed scenario, judged by the stage's declared agent. The
assessment loads the invocation's producer records under the run label
and skips with the missing cells listed when a sliced run has not
produced them.
"""

from __future__ import annotations

import json

import pytest

from ..configuration import selected_artifact_root
from ..scenarios import scenario_by_id
from ..semantic import (
    load_producer_records,
    normalize_semantic_assessment,
    parse_semantic_response,
    producer_cells_from_records,
    semantic_prompt,
    semantic_summary,
    validate_semantic_assessment,
)
from ..stages import STAGES
from .matrix import CellCase, task_creation_assessment_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.task_creation_assessment]


@pytest.mark.parametrize(
    "case",
    task_creation_assessment_cases(),
    ids=lambda item: item.id,
)
@pytest.mark.requirements("TGEVAL-007", "TGEVAL-009", "TGEVAL-010", "DOCVAL-014")
def test_task_creation_assessment(
    agent_harness,
    run_label: str,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    scenario = scenario_by_id(case.scenario_id)
    harness = agent_harness(case.agent)
    try:
        records = load_producer_records(
            selected_artifact_root(),
            scenario=scenario,
            labels=[run_label],
            allow_partial=False,
        )
    except FileNotFoundError as error:
        pytest.skip(f"missing upstream records under label {run_label!r}: {error}")
    valid_records = [record for record in records if record.get("valid") is True]
    invalid_records = [record for record in records if record.get("valid") is not True]
    if not valid_records:
        raise AssertionError(
            f"no valid producers for {scenario.scenario_id}: "
            f"{[record.get('invalid_reasons') for record in invalid_records]!r}"
        )
    prompt = semantic_prompt(scenario, valid_records)
    runs = harness.run_assessment(
        test_id=f"task-guidance-semantic-{scenario.scenario_id}",
        prompt=prompt,
        reasoning_effort=case.effort,
        fresh=bool(run_options["fresh"]),
        samples=int(run_options["samples"]),
    )
    for run in runs:
        _record_assessment_run(scenario, run, valid_records, invalid_records)


def _record_assessment_run(
    scenario,
    run,
    valid_records: list,
    invalid_records: list,
) -> None:
    if run.value is None:
        raise AssertionError(f"semantic run produced no value: {run.error!r}")
    if run.error is not None or not run.value.completed or run.value.errors:
        raise AssertionError(
            f"semantic run failed: error={run.error!r}, "
            f"outcome_errors={run.value.errors!r}"
        )
    value = normalize_semantic_assessment(
        parse_semantic_response(run.value.response),
        records=valid_records,
    )
    cells = producer_cells_from_records(valid_records)
    validate_semantic_assessment(
        value,
        scenario=scenario,
        expected_cells=cells,
    )
    summary = semantic_summary(value)
    run.record(
        STAGES["task-creation-assessment"].record,
        {
            "schema_version": 1,
            "scenario_id": scenario.scenario_id,
            "producer_records": valid_records,
            "invalid_producer_records": invalid_records,
            "assessment": value,
            "summary": summary,
        },
    )
    run.record(
        "task-guidance-semantic-summary.md",
        "# Task-guidance semantic assessment\n\n"
        f"- Scenario: `{scenario.scenario_id}`\n"
        f"- Valid producers: `{len(valid_records)}`\n"
        f"- Invalid producers skipped: `{len(invalid_records)}`\n"
        f"- Summary: `{json.dumps(summary, sort_keys=True)}`\n",
    )
