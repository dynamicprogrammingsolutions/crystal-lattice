"""The live fresh-agent generated-file planning matrix.

One case per generated-file planning scenario × producer cell. Each case
first produces — or replays — the parent task-creation run, then a fresh
session plans from exactly the files the producer wrote: no producer
session, no scratch state. The files must stand alone. The recipe lives
in :mod:`execution`, shared with the parallel run CLI.
"""

from __future__ import annotations

import pytest

from .execution import execute_generated_plan
from .matrix import CellCase, generated_plan_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.generated_plan]


@pytest.mark.parametrize("case", generated_plan_cases(), ids=lambda item: item.id)
def test_generated_plan(
    agent_harness,
    run_label: str,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    execute_generated_plan(agent_harness, run_label, run_options, case)
