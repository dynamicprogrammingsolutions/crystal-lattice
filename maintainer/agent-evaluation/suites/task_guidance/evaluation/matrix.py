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
    creation_variants,
    negative_control,
    omit_scenario,
    plan_variants,
    planning_cell,
    planning_variants,
    producer_cells,
    thinking_variants,
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
    parent_variant: str | None = None
    thinking: str = "default"


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


def planning_session_cases() -> tuple[CellCase, ...]:
    """One case per planning scenario × planning variant.

    Every arm of a category's shared plans is produced by the declared
    planning cell; the continuation cells reuse these runs.
    """

    cases = []
    for scenario in _scenarios_with("planning-session"):
        agent, effort = planning_cell(scenario.category)
        for variant in planning_variants(scenario.category):
            cases.append(
                CellCase(
                    id=f"{scenario.scenario_id}-{variant}-{agent}-{effort}",
                    scenario_id=scenario.scenario_id,
                    agent=agent,
                    effort=effort,
                    variant=variant,
                    category=scenario.category,
                    stage="planning-session",
                )
            )
    return tuple(cases)


def _cell_thinking(agent: str) -> tuple[str, ...]:
    """The thinking variants one producer cell runs: declared or default."""

    return thinking_variants(agent) or ("default",)


def task_creation_from_plan_cases() -> tuple[CellCase, ...]:
    """One case per from-plan scenario × producer cell × creation variant.

    Every producer cell continues every planning arm with the standard
    creation ask; the instructed omit-plan ask runs only on its
    designated scenario, on top of the guided arm. Cells of agents that
    declare thinking variants run each way (the reasoning-state
    dimension); other cells keep provider-default behavior.
    """

    cases = []
    for scenario in _scenarios_with("task-creation-from-plan"):
        category = scenario.category
        cells = producer_cells(category)
        designated = omit_scenario(category)
        for arm in planning_variants(category):
            if "standard" not in creation_variants(category):
                continue
            for agent, effort in cells:
                for thinking in _cell_thinking(agent):
                    token = f"-{thinking}" if thinking != "default" else ""
                    cases.append(
                        CellCase(
                            id=(
                                f"{scenario.scenario_id}-{arm}-standard-"
                                f"{agent}-{effort}{token}"
                            ),
                            scenario_id=scenario.scenario_id,
                            agent=agent,
                            effort=effort,
                            variant="standard",
                            category=category,
                            stage="task-creation-from-plan",
                            parent_variant=arm,
                            thinking=thinking,
                        )
                    )
        if (
            "omit-plan" in creation_variants(category)
            and designated == scenario.scenario_id
        ):
            for agent, effort in cells:
                for thinking in _cell_thinking(agent):
                    token = f"-{thinking}" if thinking != "default" else ""
                    cases.append(
                        CellCase(
                            id=(
                                f"{scenario.scenario_id}-guided-omit-plan-"
                                f"{agent}-{effort}{token}"
                            ),
                            scenario_id=scenario.scenario_id,
                            agent=agent,
                            effort=effort,
                            variant="omit-plan",
                            category=category,
                            stage="task-creation-from-plan",
                            parent_variant="guided",
                            thinking=thinking,
                        )
                    )
    return tuple(cases)


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

    return _producer_assessment_cases("task-quality-assessment")


def file_fidelity_cases() -> tuple[CellCase, ...]:
    """One case per fidelity-assessed subject cell, judged by the declared
    agent.

    The subjects are the scenario's producer cells; the fidelity judge
    asks whether the files carry the conversation's decided design and
    durable context.
    """

    return _producer_assessment_cases("file-fidelity-assessment")


def file_readability_cases() -> tuple[CellCase, ...]:
    """One case per readability-assessed subject cell, judged by the
    declared agent.

    The subjects are the scenario's producer cells; the readability
    judge asks how easily a human reader can work with each section.
    """

    return _producer_assessment_cases("file-readability-assessment")


def _producer_assessment_cases(stage: str) -> tuple[CellCase, ...]:
    """Enumerate every producer subject cell for one assessment stage."""

    cases = []
    for scenario in _scenarios_with(stage):
        for subject_agent, subject_effort in producer_cells(scenario.category):
            cases.append(
                CellCase(
                    id=f"{scenario.scenario_id}-{subject_agent}-{subject_effort}",
                    scenario_id=scenario.scenario_id,
                    agent=subject_agent,
                    effort=subject_effort,
                    category=scenario.category,
                    stage=stage,
                )
            )
    return tuple(cases)


def handoff_assessment_cases() -> tuple[CellCase, ...]:
    """One case per assessed handoff subject, judged by the declared agent.

    The subjects are the fresh-agent plans per variant, the same-agent
    continuations, and the designated negative control.
    """

    return _plan_stage_subject_cases("handoff-assessment")


def plan_content_cases() -> tuple[CellCase, ...]:
    """One case per presented-plan subject, judged by the declared agent.

    The subjects are the same plan-stage runs the handoff assessment
    judges — every fresh-agent plan per variant, the same-agent
    continuations, and the designated negative control — so the
    presented plan gets a content judgment beside the handoff judgment.
    """

    return _plan_stage_subject_cases("plan-content-assessment")


def _plan_stage_subject_cases(stage: str) -> tuple[CellCase, ...]:
    """Enumerate every plan-stage subject cell for one assessment stage."""

    cases = []
    for scenario in _scenarios_with(stage):
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
                        stage=stage,
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
                        stage=stage,
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
                        stage=stage,
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
                    stage=stage,
                )
            )
    return tuple(cases)
