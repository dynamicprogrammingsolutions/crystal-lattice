"""The live same-agent continuation matrix.

One case per planning scenario × producer cell: the producer run is
replayed (or executed), then the same session continues and presents its
plan. The recipe lives in :mod:`execution`, shared with the parallel
run CLI.
"""

from __future__ import annotations

import pytest

from .execution import execute_continuation
from .matrix import CellCase, continuation_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.continuation]


@pytest.mark.parametrize("case", continuation_cases(), ids=lambda item: item.id)
def test_continuation(
    agent_harness,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    execute_continuation(agent_harness, run_options, case)
