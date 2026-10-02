"""Suite test configuration: live-run options and per-agent harnesses.

The run options map one-to-one onto the run-model layer: ``--label`` is
the provenance label recorded for every executed request, ``--fresh``
re-executes requests that already have a cache entry, and ``--samples N``
executes each request N times as variance samples. Live tests run only
under explicit ``agent_eval`` marker selection; the parametrized matrix
comes from the configuration manifest, so both agents execute in one
invocation through session-cached per-agent harnesses.
"""

from __future__ import annotations

from typing import Iterator

import pytest

from agent_eval.runner import generate_run_label

from ..runner import TaskGuidanceHarness


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--label",
        default=None,
        help="run label recorded as provenance for every executed request",
    )
    parser.addoption(
        "--fresh",
        action="store_true",
        help="re-execute requests even when a cache entry exists",
    )
    parser.addoption(
        "--samples",
        type=int,
        default=1,
        help="execute each request N times as variance samples",
    )


@pytest.fixture(scope="session")
def run_label(request: pytest.FixtureRequest) -> str:
    """One run label for the whole invocation."""

    raw = request.config.getoption("--label")
    return str(raw) if raw else generate_run_label()


@pytest.fixture(scope="session")
def run_options(request: pytest.FixtureRequest) -> dict[str, object]:
    return {
        "fresh": bool(request.config.getoption("--fresh")),
        "samples": int(request.config.getoption("--samples")),
    }


@pytest.fixture(scope="session")
def agent_harness(
    run_label: str,
) -> Iterator[object]:
    """Session-cached harnesses: one per declared agent, one shared label."""

    harnesses: dict[str, TaskGuidanceHarness] = {}

    def factory(agent_name: str) -> TaskGuidanceHarness:
        if agent_name not in harnesses:
            harnesses[agent_name] = TaskGuidanceHarness(
                agent_name,
                label=run_label,
            )
        return harnesses[agent_name]

    yield factory
    for harness in harnesses.values():
        harness.close()
    harnesses.clear()
