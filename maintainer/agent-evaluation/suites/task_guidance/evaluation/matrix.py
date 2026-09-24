"""The configuration-derived live matrix.

The parametrized live tests and the collection checks both derive every
case from the configuration manifest and the stage catalog; no literal
cell values live in the tests. Case ids are designed for ``-k`` slicing:
``-k glm``, ``-k tg01``, ``-k retain``, and combinations select exactly
the matching cells.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..configuration import (
    CATEGORIES,
    assessment_cell,
    negative_control,
    plan_variants,
    producer_cells,
)
from ..scenarios import SCENARIOS


@dataclass(frozen=True)
class CellCase:
    id: str
    scenario_id: str
    agent: str
    effort: str
    variant: str | None = None
    category: str = ""


def _scenarios_with(stage: str) -> list:
    return [
        scenario
        for scenario in SCENARIOS
        if stage in CATEGORIES[scenario.category]["stages"]
    ]


def task_creation_cases() -> tuple[CellCase, ...]:
    """One case per scenario × producer cell (the task-creation stage)."""

    return tuple(
        CellCase(
            id=f"{scenario.scenario_id}-{agent}-{effort}",
            scenario_id=scenario.scenario_id,
            agent=agent,
            effort=effort,
            category=scenario.category,
        )
        for scenario in SCENARIOS
        for agent, effort in producer_cells(scenario.category)
    )


def handoff_plan_cases() -> tuple[CellCase, ...]:
    """One case per handoff scenario × variant × producer cell."""

    return tuple(
        CellCase(
            id=f"{scenario.scenario_id}-{variant}-{agent}-{effort}",
            scenario_id=scenario.scenario_id,
            agent=agent,
            effort=effort,
            variant=variant,
            category=scenario.category,
        )
        for scenario in _scenarios_with("handoff-plan")
        for variant in plan_variants(scenario.category)
        for agent, effort in producer_cells(scenario.category)
    )


def continuation_cases() -> tuple[CellCase, ...]:
    """One case per continuation scenario × producer cell."""

    return tuple(
        CellCase(
            id=f"{scenario.scenario_id}-{agent}-{effort}",
            scenario_id=scenario.scenario_id,
            agent=agent,
            effort=effort,
            category=scenario.category,
        )
        for scenario in _scenarios_with("continuation")
        for agent, effort in producer_cells(scenario.category)
    )


def negative_control_cases() -> tuple[CellCase, ...]:
    """One case per declared negative-control designation."""

    cases = []
    for category in CATEGORIES:
        control = negative_control(category)
        if control is None:
            continue
        cases.append(
            CellCase(
                id=(
                    f"{control['scenario']}-{control['variant']}-"
                    f"{control['agent']}-{control['effort']}"
                ),
                scenario_id=control["scenario"],
                agent=control["agent"],
                effort=control["effort"],
                variant=control["variant"],
                category=category,
            )
        )
    return tuple(cases)


def task_creation_assessment_cases() -> tuple[CellCase, ...]:
    """One case per assessed scenario, judged by the stage's declared agent."""

    cases = []
    for scenario in _scenarios_with("task-creation-assessment"):
        agent, effort = assessment_cell(scenario.category, "task-creation-assessment")
        cases.append(
            CellCase(
                id=f"{scenario.scenario_id}-{agent}-{effort}",
                scenario_id=scenario.scenario_id,
                agent=agent,
                effort=effort,
                category=scenario.category,
            )
        )
    return tuple(cases)


def handoff_assessment_cases() -> tuple[CellCase, ...]:
    """One case per handoff-assessed scenario, judged by the declared agent."""

    cases = []
    for scenario in _scenarios_with("handoff-assessment"):
        agent, effort = assessment_cell(scenario.category, "handoff-assessment")
        cases.append(
            CellCase(
                id=f"{scenario.scenario_id}-{agent}-{effort}",
                scenario_id=scenario.scenario_id,
                agent=agent,
                effort=effort,
                category=scenario.category,
            )
        )
    return tuple(cases)
