"""The live task-creation matrix, parametrized from the configuration.

One case per scenario × producer cell, derived from the manifest; the
case ids support ``-k`` slicing (``-k glm``, ``-k tg01``, ``-k max``).
Every sample of a cell records its own stage record under the
invocation's run label. The recipe lives in :mod:`execution`, shared
with the parallel run CLI.
"""

from __future__ import annotations

import pytest

from .execution import execute_task_creation
from .matrix import CellCase, task_creation_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.task_creation]


@pytest.mark.parametrize("case", task_creation_cases(), ids=lambda item: item.id)
@pytest.mark.requirements(
    "TGEVAL-002",
    "TGEVAL-003",
    "TGEVAL-007",
    "TGEVAL-009",
    "TGEVAL-010",
    "DOCVAL-014",
)
def test_task_creation(
    agent_harness,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    execute_task_creation(agent_harness, run_options, case)
