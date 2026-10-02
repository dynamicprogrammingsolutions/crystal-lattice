"""The live task-creation assessment matrix, parametrized per subject cell.

One case per (scenario, producer cell); every sample of the cell is one
subject and gets its own assessment request under a neutral subject
label. The judging agent comes from the stage's declared assessment
cell. Cases with no valid subject skip with the recorded reasons. The
recipe lives in :mod:`execution`, shared with the parallel run CLI."""

from __future__ import annotations

import pytest

from .execution import CaseSkipped, execute_task_creation_assessment
from .matrix import CellCase, task_creation_assessment_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.task_creation_assessment]


@pytest.mark.parametrize(
    "case", task_creation_assessment_cases(), ids=lambda item: item.id
)
@pytest.mark.requirements("TGEVAL-007", "TGEVAL-009", "TGEVAL-010", "DOCVAL-014")
def test_task_creation_assessment(
    agent_harness,
    run_label: str,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    try:
        execute_task_creation_assessment(agent_harness, run_label, run_options, case)
    except CaseSkipped as skip:
        pytest.skip(str(skip))
