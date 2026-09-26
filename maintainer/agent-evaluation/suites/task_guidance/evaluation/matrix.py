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
    stage: str = ""


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
    """One case per assessed subject cell, judged by the declared agent.

    The subjects are the scenario's producer cells; the judging agent
    comes from the stage's declared assessment cell.
    """

    cases = []
    for scenario in _scenarios_with("task-creation-assessment"):
        for subject_agent, subject_effort in producer_cells(scenario.category):
            cases.append(
                CellCase(
                    id=f"{scenario.scenario_id}-{subject_agent}-{subject_effort}",
                    scenario_id=scenario.scenario_id,
                    agent=subject_agent,
                    effort=subject_effort,
                    category=scenario.category,
                    stage="task-creation-assessment",
                )
            )
    return tuple(cases)


def generated_plan_cases() -> tuple[CellCase, ...]:
    """One case per generated-file planning cell.

    The subjects are the scenario's producer cells; each case re-produces
    (or replays) the parent task-creation run and plans from its files
    with a fresh session.
    """

    cases = []
    for scenario in _scenarios_with("generated-plan"):
        for agent, effort in producer_cells(scenario.category):
            cases.append(
                CellCase(
                    id=f"{scenario.scenario_id}-{agent}-{effort}",
                    scenario_id=scenario.scenario_id,
                    agent=agent,
                    effort=effort,
                    category=scenario.category,
                    stage="generated-plan",
                )
            )
    return tuple(cases)


def task_quality_assessment_cases() -> tuple[CellCase, ...]:
    """One case per quality-assessed subject cell, judged by the declared
    agent.

    The subjects are the scenario's producer cells — the same subjects the
    decomposition assessment judges — so both views of one subject stay
    comparable.
    """

    cases = []
    for scenario in _scenarios_with("task-quality-assessment"):
        for subject_agent, subject_effort in producer_cells(scenario.category):
            cases.append(
                CellCase(
                    id=f"{scenario.scenario_id}-{subject_agent}-{subject_effort}",
                    scenario_id=scenario.scenario_id,
                    agent=subject_agent,
                    effort=subject_effort,
                    category=scenario.category,
                    stage="task-quality-assessment",
                )
            )
    return tuple(cases)


def handoff_assessment_cases() -> tuple[CellCase, ...]:
    """One case per assessed handoff subject, judged by the declared agent.

    The subjects are the fresh-agent plans per variant, the same-agent
    continuations, and the designated negative control.
    """

    cases = []
    for scenario in _scenarios_with("handoff-assessment"):
        cells = producer_cells(scenario.category)
        has_continuation = "continuation" in CATEGORIES[scenario.category]["stages"]
        for variant in plan_variants(scenario.category):
            for subject_agent, subject_effort in cells:
                cases.append(
                    CellCase(
                        id=(
                            f"{scenario.scenario_id}-{variant}-"
                            f"{subject_agent}-{subject_effort}"
                        ),
                        scenario_id=scenario.scenario_id,
                        agent=subject_agent,
                        effort=subject_effort,
                        variant=variant,
                        category=scenario.category,
                        stage="handoff-assessment",
                    )
                )
        if has_continuation:
            for subject_agent, subject_effort in cells:
                cases.append(
                    CellCase(
                        id=(
                            f"{scenario.scenario_id}-generated-task-"
                            f"{subject_agent}-{subject_effort}"
                        ),
                        scenario_id=scenario.scenario_id,
                        agent=subject_agent,
                        effort=subject_effort,
                        variant="generated-task",
                        category=scenario.category,
                        stage="handoff-assessment",
                    )
                )
        has_generated = "generated-plan" in CATEGORIES[scenario.category]["stages"]
        if has_generated:
            for subject_agent, subject_effort in cells:
                cases.append(
                    CellCase(
                        id=(
                            f"{scenario.scenario_id}-generated-file-"
                            f"{subject_agent}-{subject_effort}"
                        ),
                        scenario_id=scenario.scenario_id,
                        agent=subject_agent,
                        effort=subject_effort,
                        variant="generated-file",
                        category=scenario.category,
                        stage="handoff-assessment",
                    )
                )
        control = negative_control(scenario.category)
        if control is not None and control["scenario"] == scenario.scenario_id:
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
                    category=scenario.category,
                    stage="handoff-assessment",
                )
            )
    return tuple(cases)
