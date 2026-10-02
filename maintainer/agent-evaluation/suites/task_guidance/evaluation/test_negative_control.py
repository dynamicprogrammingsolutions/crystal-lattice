"""The live negative-control run, from the configuration's designation.

The control plans from the incomplete variant of the designated scenario's
canonical handoff task file: a run expected to come out worse than a
complete handoff, proving the evaluation can distinguish good from bad
handoffs. One designation per category, declared in the manifest. The
recipe lives in :mod:`execution`, shared with the parallel run CLI.
"""

from __future__ import annotations

import pytest

from .execution import execute_negative_control
from .matrix import CellCase, negative_control_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.negative_control]


@pytest.mark.parametrize("case", negative_control_cases(), ids=lambda item: item.id)
@pytest.mark.requirements("TGEVAL-004", "TGEVAL-008")
def test_negative_control(
    agent_harness,
    run_label: str,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    execute_negative_control(agent_harness, run_label, run_options, case)
