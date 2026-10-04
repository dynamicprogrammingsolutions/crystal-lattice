"""The live from-plan creation matrix, parametrized from the configuration.

One case per dev scenario × planning arm × producer cell (plus the
designated instructed-omission cases). Each producer cell continues the
category's shared planning session of its arm: the tasks guidance is
compiled into the writing turn's system message, and every producer
validity check of the one-shot task-creation stage applies.
"""

from __future__ import annotations

import pytest

from .execution import execute_task_creation_from_plan
from .matrix import CellCase, task_creation_from_plan_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.task_creation_from_plan]


@pytest.mark.parametrize(
    "case", task_creation_from_plan_cases(), ids=lambda item: item.id
)
@pytest.mark.requirements(
    "TGEVAL-003",
    "TGEVAL-010",
)
def test_task_creation_from_plan(
    agent_harness,
    run_label: str,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    execute_task_creation_from_plan(agent_harness, run_label, run_options, case)
