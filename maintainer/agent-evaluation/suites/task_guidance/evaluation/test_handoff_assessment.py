"""The live handoff assessment matrix, parametrized per subject.

One case per handoff subject — a fresh-agent plan per variant, a
same-agent continuation, or the designated negative control; every
sample of the subject cell gets its own assessment request. The stage
and variant labels stay in the rubric material; the producer identity
does not. Cases with no valid subject skip with the recorded reasons.
"""

from __future__ import annotations

import pytest

from ..configuration import assessment_cell, selected_artifact_root
from ..handoff_semantic import (
    handoff_assessment_record,
    handoff_semantic_prompt,
    load_handoff_subjects,
    parse_handoff_semantic,
    subjects_block_reason,
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
    assert case.variant is not None
    scenario = scenario_by_id(case.scenario_id)
    judge, judge_effort = assessment_cell(scenario.category, "handoff-assessment")
    harness = agent_harness(judge)
    stage = "same-agent" if case.variant == "generated-task" else "fresh-agent"
    try:
        subjects = load_handoff_subjects(
            selected_artifact_root(),
            scenario=scenario,
            labels=[run_label],
            selection={(stage, case.variant, case.agent, case.effort)},
        )
    except FileNotFoundError as error:
        pytest.skip(f"missing upstream records under label {run_label!r}: {error}")
    reason = subjects_block_reason(subjects)
    if reason is not None:
        pytest.skip(reason)
    for subject in subjects:
        prompt = handoff_semantic_prompt(scenario, subject)
        runs = harness.run_assessment(
            test_id=(
                f"task-guidance-handoff-semantic-{scenario.scenario_id}-"
                f"{subject.variant}-{subject.profile}-{subject.effort}-"
                f"s{subject.sample_index}"
            ),
            prompt=prompt,
            reasoning_effort=judge_effort,
            fresh=bool(run_options["fresh"]),
            samples=int(run_options["samples"]),
        )
        for run in runs:
            _record_assessment_run(scenario, subject, run)


def _record_assessment_run(scenario, subject, run) -> None:
    if run.value is None or run.error is not None:
        raise AssertionError(f"handoff semantic run failed: {run.error!r}")
    if not run.value.completed or run.value.errors:
        raise AssertionError(f"handoff semantic provider errors: {run.value.errors!r}")
    value = parse_handoff_semantic(run.value.response)
    validate_handoff_semantic(
        value,
        scenario=scenario,
        stage=subject.stage,
        variant=subject.variant,
    )
    record = handoff_assessment_record(scenario, subject, value["assessment"])
    run.record(STAGES["handoff-assessment"].record, record)
    run.record(
        "task-guidance-handoff-semantic-summary.md",
        "# Task-guidance handoff semantic assessment\n\n"
        f"- Scenario: `{scenario.scenario_id}`\n"
        f"- Subject: `{subject.stage}:{subject.variant}:"
        f"{subject.profile}:{subject.effort}`"
        f" sample {subject.sample_index}\n"
        f"- Score: `{record['assessment']['handoff_quality_score']}`\n",
    )
