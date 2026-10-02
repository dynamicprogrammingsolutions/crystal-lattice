"""The live file-readability assessment matrix, per subject cell.

One case per (scenario, producer cell); every sample of the cell is one
subject and gets its own assessment request over every top-level
section present, with the deterministic structure facts embedded. The
conversation is deliberately absent. Cases with no valid subject skip
with the recorded reasons. The recipe lives in :mod:`execution`,
shared with the parallel run CLI."""

from __future__ import annotations

import pytest

from .execution import CaseSkipped, execute_file_readability_assessment
from .matrix import CellCase, file_readability_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.file_readability_assessment]


@pytest.mark.parametrize("case", file_readability_cases(), ids=lambda item: item.id)
def test_file_readability_assessment(
    agent_harness,
    run_label: str,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    try:
        execute_file_readability_assessment(agent_harness, run_label, run_options, case)
    except CaseSkipped as skip:
        pytest.skip(str(skip))
