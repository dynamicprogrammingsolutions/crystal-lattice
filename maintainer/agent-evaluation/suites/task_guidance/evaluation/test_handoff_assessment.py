"""The live handoff assessment matrix, parametrized per subject.

One case per handoff subject — a fresh-agent plan per variant, a
same-agent continuation, or the designated negative control; every
sample of the subject cell gets its own assessment request. The stage
and variant labels stay in the rubric material; the producer identity
does not. Cases with no valid subject skip with the recorded reasons.
The recipe lives in :mod:`execution`, shared with the parallel run CLI."""

from __future__ import annotations

import pytest

from .execution import CaseSkipped, execute_handoff_assessment
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
    try:
        execute_handoff_assessment(agent_harness, run_label, run_options, case)
    except CaseSkipped as skip:
        pytest.skip(str(skip))
