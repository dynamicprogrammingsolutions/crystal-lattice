from __future__ import annotations

import hashlib
import os
from collections.abc import Iterator

import pytest

from .artifacts import selected_dataset_id
from .runner import PlanRunValue, TaskGuidanceHarness, selected_agent
from .scenarios import SCENARIOS, TaskGuidanceScenario


pytestmark = [pytest.mark.agent_eval, pytest.mark.task_guidance_baseline]


HANDOFF_SCENARIOS = tuple(
    scenario for scenario in SCENARIOS if scenario.category == "handoff"
)
HANDOFF_CELLS = (("glm", "max"), ("gpt", "high"))


@pytest.fixture(scope="session")
def handoff_harness() -> Iterator[TaskGuidanceHarness]:
    agent_name = selected_agent()
    if os.getenv("AGENT_EVAL_RUN_REAL") != "1":
        raise RuntimeError("set AGENT_EVAL_RUN_REAL=1 for handoff planning")
    if agent_name == "gpt" and os.getenv("AGENT_EVAL_ALLOW_HOSTED") != "1":
        raise RuntimeError("set AGENT_EVAL_ALLOW_HOSTED=1 for ChatGPT")
    harness = TaskGuidanceHarness(agent_name)
    yield harness
    harness.close()


@pytest.mark.parametrize("variant", ("retain", "omit"))
@pytest.mark.parametrize(
    ("producer_profile", "reasoning_effort"),
    HANDOFF_CELLS,
    ids=lambda value: value,
)
@pytest.mark.parametrize(
    "scenario",
    HANDOFF_SCENARIOS,
    ids=lambda item: item.scenario_id,
)
@pytest.mark.requirements(
    "TGEVAL-003",
    "TGEVAL-004",
    "TGEVAL-006",
    "TGEVAL-008",
    "TGEVAL-010",
)
def test_fresh_agent_plans_from_canonical_handoff(
    handoff_harness: TaskGuidanceHarness,
    scenario: TaskGuidanceScenario,
    producer_profile: str,
    reasoning_effort: str,
    variant: str,
) -> None:
    if handoff_harness.agent_name != producer_profile:
        pytest.skip(f"run with AGENT_EVAL_PROFILE={producer_profile}")
    selected = os.getenv("AGENT_EVAL_TASK_SCENARIO", "").strip()
    if selected and scenario.scenario_id != selected:
        pytest.skip(f"run is limited to {selected}")
    attempt = os.getenv(
        "AGENT_EVAL_TASK_HANDOFF_RUN_ATTEMPT",
        "default",
    ).strip()
    run = handoff_harness.run_plan_from_handoff(
        scenario=scenario,
        variant=variant,
        reasoning_effort=reasoning_effort,
        cache_variant=attempt,
    )
    value = _require_value(run.value, run.error)
    invalid: list[str] = []
    if run.error is not None or not value.completed or value.errors:
        invalid.append(f"run failure: {run.error!r}, {value.errors!r}")
    if not value.response.strip():
        invalid.append("empty planning response")
    if run.changed_paths:
        invalid.append(f"planning mutated files: {run.changed_paths!r}")
    if value.delivery.get("agents_occurrences") != 1:
        invalid.append("AGENTS.md delivery mismatch")
    if value.delivery.get("tasks_occurrences") != 1:
        invalid.append("TASKS-v7 delivery mismatch")
    record = {
        "schema_version": 1,
        "dataset_id": selected_dataset_id(),
        "scenario_id": scenario.scenario_id,
        "variant": variant,
        "producer": {
            "profile": producer_profile,
            "model": handoff_harness.agent["model"],
            "reasoning_effort": reasoning_effort,
        },
        "run_attempt": attempt,
        "target_sha256": hashlib.sha256(scenario.target_path.read_bytes()).hexdigest(),
        "target": scenario.target,
        "response": value.response,
        "tool_metrics": value.tool_metrics,
        "task_files": value.task_files,
        "delivery": value.delivery,
        "valid": not invalid,
        "invalid_reasons": invalid,
    }
    run.record("task-guidance-handoff-plan.json", record)
    assert not invalid, "\n".join(invalid)


def _require_value(value: PlanRunValue | None, error: object) -> PlanRunValue:
    if value is not None:
        return value
    raise AssertionError(f"handoff run produced no value: {error!r}")
