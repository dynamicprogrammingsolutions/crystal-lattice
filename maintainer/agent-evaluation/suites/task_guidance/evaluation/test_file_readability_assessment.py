"""The live file-readability assessment matrix, per subject cell.

One case per (scenario, producer cell); every sample of the cell is one
subject and gets its own assessment request. The judged material — the
task files with measured per-section structure facts — is embedded as
rendered text; no producer identity, validity, or tool metrics reach the
judge, and the conversation is deliberately absent: readability is a
property of the files a reader sees. Cases with no valid subject skip
with the recorded reasons.
"""

from __future__ import annotations

import pytest

from ..configuration import assessment_cell, selected_artifact_root
from ..file_quality import (
    file_readability_prompt,
    file_readability_record,
    normalize_file_readability,
    parse_file_readability,
    validate_file_readability,
)
from ..scenarios import scenario_by_id
from ..semantic import load_producer_subjects, subjects_block_reason
from ..stages import STAGES
from .matrix import CellCase, file_readability_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.file_readability_assessment]


@pytest.mark.parametrize("case", file_readability_cases(), ids=lambda item: item.id)
def test_file_readability_assessment(
    agent_harness,
    run_label: str,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    scenario = scenario_by_id(case.scenario_id)
    judge, judge_effort = assessment_cell(
        scenario.category, "file-readability-assessment"
    )
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
        prompt = file_readability_prompt(scenario, subject.record)
        runs = harness.run_assessment(
            test_id=(
                f"task-guidance-file-readability-{scenario.scenario_id}-"
                f"{subject.profile}-{subject.effort}-s{subject.sample_index}"
            ),
            prompt=prompt,
            reasoning_effort=judge_effort,
            fresh=bool(run_options["fresh"]),
            samples=int(run_options["samples"]),
        )
        for run in runs:
            _record_readability_run(scenario, subject, run)


def _record_readability_run(scenario, subject, run) -> None:
    if run.value is None or run.error is not None:
        raise AssertionError(f"readability run failed: {run.error!r}")
    if not run.value.completed or run.value.errors:
        raise AssertionError(f"readability provider errors: {run.value.errors!r}")
    value = normalize_file_readability(
        parse_file_readability(run.value.response),
        scenario=scenario,
        record=subject.record,
    )
    validate_file_readability(value)
    record = file_readability_record(scenario, subject, value)
    run.record(STAGES["file-readability-assessment"].record, record)
    run.record(
        "task-guidance-file-readability-summary.md",
        "# Task-guidance file-readability assessment\n\n"
        f"- Scenario: `{scenario.scenario_id}`\n"
        f"- Subject: `{subject.profile}:{subject.effort}`"
        f" sample {subject.sample_index}\n"
        f"- Summary: `{record['summary']}`\n",
    )
