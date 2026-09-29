"""The live fresh-agent planning matrix, parametrized from the configuration.

One case per handoff scenario × plan variant × producer cell. The
canonical handoff task file must stand alone: the run starts from a fresh
session and a fresh workspace, and planning must not mutate any file.
The recipe lives in :mod:`execution`, shared with the parallel run CLI.
"""

from __future__ import annotations

import pytest

from .execution import execute_handoff_plan
from .matrix import CellCase, handoff_plan_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.handoff_plan]


@pytest.mark.parametrize("case", handoff_plan_cases(), ids=lambda item: item.id)
@pytest.mark.requirements(
    "TGEVAL-003",
    "TGEVAL-004",
    "TGEVAL-006",
    "TGEVAL-008",
    "TGEVAL-010",
)
def test_handoff_plan(
    agent_harness,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    execute_handoff_plan(agent_harness, run_options, case)
