"""The live task-creation assessment matrix, parametrized per subject cell.

One case per (scenario, producer cell); every sample of the cell is one
subject and gets its own assessment request under a neutral subject
label. The judging agent comes from the stage's declared assessment
cell. Cases with no valid subject skip with the recorded reasons.
"""

from __future__ import annotations

import pytest

from ..configuration import assessment_cell, selected_artifact_root
from ..scenarios import scenario_by_id
from ..semantic import (
    assessment_record,
    load_producer_subjects,
    normalize_semantic_assessment,
    parse_semantic_response,
    semantic_prompt,
    subjects_block_reason,
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
    judge, judge_effort = assessment_cell(scenario.category, "task-creation-assessment")
    harness = agent_harness(judge)
    try:
        subjects = load_producer_subjects(
            selected_artifact_root(),
            scenario=scenario,
            labels=[run_label],
            cells=[(case.agent, case.effort)],
        )
    except FileNotFoundError as error:
        pytest.skip(f"missing upstream records under label {run_label!r}: {error}")
    reason = subjects_block_reason(subjects)
    if reason is not None:
        pytest.skip(reason)
    for subject in subjects:
        prompt = semantic_prompt(scenario, subject.record)
        runs = harness.run_assessment(
            test_id=(
                f"task-guidance-semantic-{scenario.scenario_id}-"
                f"{subject.profile}-{subject.effort}-s{subject.sample_index}"
            ),
            prompt=prompt,
            reasoning_effort=judge_effort,
            fresh=bool(run_options["fresh"]),
            samples=int(run_options["samples"]),
        )
        for run in runs:
            _record_assessment_run(scenario, subject, run)


def _record_assessment_run(scenario, subject, run) -> None:
    if run.value is None:
        raise AssertionError(f"semantic run produced no value: {run.error!r}")
    if run.error is not None or not run.value.completed or run.value.errors:
        raise AssertionError(
            f"semantic run failed: error={run.error!r}, "
            f"outcome_errors={run.value.errors!r}"
        )
    value = normalize_semantic_assessment(
        parse_semantic_response(run.value.response),
        record=subject.record,
    )
    validate_semantic_assessment(value, scenario=scenario)
    record = assessment_record(scenario, subject, value["assessment"])
    run.record(STAGES["task-creation-assessment"].record, record)
    run.record(
        "task-guidance-semantic-summary.md",
        "# Task-guidance semantic assessment\n\n"
        f"- Scenario: `{scenario.scenario_id}`\n"
        f"- Subject: `{subject.profile}:{subject.effort}`"
        f" sample {subject.sample_index}\n"
        f"- Summary: `{record['summary']}`\n",
    )
