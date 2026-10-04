"""The live planning-session matrix, parametrized from the configuration.

One case per dev scenario × planning variant, produced by the category's
declared planning cell. The planning turn presents the implementation
plan for the scenario's natural request without implementing: the tasks
guidance is compiled into the guided arm's system message and absent
from the unguided arm's, and planning must not mutate any file.
"""

from __future__ import annotations

import pytest

from .execution import execute_planning_session
from .matrix import CellCase, planning_session_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.planning_session]


@pytest.mark.parametrize("case", planning_session_cases(), ids=lambda item: item.id)
@pytest.mark.requirements(
    "TGEVAL-003",
    "TGEVAL-010",
)
def test_planning_session(
    agent_harness,
    run_label: str,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    execute_planning_session(agent_harness, run_label, run_options, case)
