"""The live presented-plan content assessment matrix, per subject.

One case per plan-stage subject — a fresh-agent plan per variant, a
same-agent continuation, or the designated negative control; every
sample of the subject cell gets its own assessment request. The judged
material is the presented plan text embedded in the prompt; neither
the producer identity nor the variant labels reach the judge. Cases
with no valid subject skip with the recorded reasons.
"""

from __future__ import annotations

import pytest

from ..configuration import assessment_cell, selected_artifact_root
from ..handoff_semantic import load_handoff_subjects, subjects_block_reason
from ..plan_content import (
    normalize_plan_content_assessment,
    parse_plan_content_response,
    plan_content_prompt,
    plan_content_record,
    validate_plan_content_assessment,
)
from ..scenarios import scenario_by_id
from ..stages import STAGES
from .matrix import CellCase, plan_content_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.plan_content_assessment]


@pytest.mark.parametrize("case", plan_content_cases(), ids=lambda item: item.id)
def test_plan_content_assessment(
    agent_harness,
    run_label: str,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    assert case.variant is not None
    scenario = scenario_by_id(case.scenario_id)
    judge, judge_effort = assessment_cell(scenario.category, "plan-content-assessment")
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
        prompt = plan_content_prompt(scenario, subject.record)
        runs = harness.run_assessment(
            test_id=(
                f"task-guidance-plan-content-{scenario.scenario_id}-"
                f"{subject.variant}-{subject.profile}-{subject.effort}-"
                f"s{subject.sample_index}"
            ),
            prompt=prompt,
            reasoning_effort=judge_effort,
            fresh=bool(run_options["fresh"]),
            samples=int(run_options["samples"]),
        )
        for run in runs:
            _record_plan_content_run(scenario, subject, run)


def _record_plan_content_run(scenario, subject, run) -> None:
    if run.value is None or run.error is not None:
        raise AssertionError(f"plan-content run failed: {run.error!r}")
    if not run.value.completed or run.value.errors:
        raise AssertionError(f"plan-content provider errors: {run.value.errors!r}")
    value = normalize_plan_content_assessment(
        parse_plan_content_response(run.value.response),
        scenario=scenario,
    )
    validate_plan_content_assessment(value, scenario=scenario)
    record = plan_content_record(scenario, subject, value)
    run.record(STAGES["plan-content-assessment"].record, record)
    run.record(
        "task-guidance-plan-content-summary.md",
        "# Task-guidance presented-plan content assessment\n\n"
        f"- Scenario: `{scenario.scenario_id}`\n"
        f"- Subject: `{subject.stage}:{subject.variant}:"
        f"{subject.profile}:{subject.effort}`"
        f" sample {subject.sample_index}\n"
        f"- Summary: `{record['summary']}`\n",
    )
