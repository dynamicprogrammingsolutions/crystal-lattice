"""The live file-fidelity assessment matrix, per subject cell.

One case per (scenario, producer cell); every sample of the cell is one
subject and gets its own assessment request. The judged material — the
task files and the producer's final response — is embedded as rendered
text; no producer identity, validity, or tool metrics reach the judge.
Cases with no valid subject skip with the recorded reasons. The recipe
lives in :mod:`execution`, shared with the parallel run CLI."""

from __future__ import annotations

import pytest

from .execution import CaseSkipped, execute_file_fidelity_assessment
from .matrix import CellCase, file_fidelity_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.file_fidelity_assessment]


@pytest.mark.parametrize("case", file_fidelity_cases(), ids=lambda item: item.id)
def test_file_fidelity_assessment(
    agent_harness,
    run_label: str,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    try:
        execute_file_fidelity_assessment(agent_harness, run_label, run_options, case)
    except CaseSkipped as skip:
        pytest.skip(str(skip))
