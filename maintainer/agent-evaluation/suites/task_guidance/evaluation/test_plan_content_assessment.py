"""The live presented-plan content assessment matrix, per subject.

One case per plan-stage subject — a fresh-agent plan per variant, a
same-agent continuation, or the designated negative control; every
sample of the subject cell gets its own assessment request. The judged
material is the presented plan text embedded in the prompt; neither
the producer identity nor the variant labels reach the judge. Cases
with no valid subject skip with the recorded reasons. The recipe lives
in :mod:`execution`, shared with the parallel run CLI."""

from __future__ import annotations

import pytest

from .execution import CaseSkipped, execute_plan_content_assessment
from .matrix import CellCase, plan_content_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.plan_content_assessment]


@pytest.mark.parametrize("case", plan_content_cases(), ids=lambda item: item.id)
def test_plan_content_assessment(
    agent_harness,
    run_label: str,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    try:
        execute_plan_content_assessment(agent_harness, run_label, run_options, case)
    except CaseSkipped as skip:
        pytest.skip(str(skip))
