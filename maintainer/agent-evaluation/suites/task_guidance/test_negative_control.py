from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

from .artifacts import selected_dataset_id
from .runner import PlanRunValue, TaskGuidanceHarness, selected_profile
from .scenarios import scenario_by_id


pytestmark = [pytest.mark.agent_eval, pytest.mark.task_guidance_baseline]


@pytest.fixture(scope="session")
def negative_control_harness() -> Iterator[TaskGuidanceHarness]:
    profile = selected_profile()
    if profile.name != "glm":
        pytest.skip("initial negative control uses GLM")
    if os.getenv("AGENT_EVAL_RUN_REAL") != "1":
        raise RuntimeError("set AGENT_EVAL_RUN_REAL=1 for negative control")
    harness = TaskGuidanceHarness(profile)
    yield harness
    harness.close()


@pytest.mark.requirements("TGEVAL-004", "TGEVAL-008")
def test_incomplete_handoff_requires_more_reconstruction(
    negative_control_harness: TaskGuidanceHarness,
) -> None:
    scenario = scenario_by_id("tg02-fastapi-pagination-handoff")
    attempt = os.getenv(
        "AGENT_EVAL_TASK_HANDOFF_RUN_ATTEMPT",
        "default",
    ).strip()
    run = negative_control_harness.run_plan_from_handoff(
        scenario=scenario,
        variant="incomplete",
        reasoning_effort="max",
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
    record = {
        "schema_version": 1,
        "dataset_id": selected_dataset_id(),
        "scenario_id": scenario.scenario_id,
        "variant": "incomplete",
        "producer": {
            "profile": "glm",
            "model": negative_control_harness.profile.model,
            "reasoning_effort": "max",
        },
        "run_attempt": attempt,
        "response": value.response,
        "tool_metrics": value.tool_metrics,
        "task_files": value.task_files,
        "valid": not invalid,
        "invalid_reasons": invalid,
    }
    run.record("task-guidance-negative-control.json", record)
    assert not invalid, "\n".join(invalid)


def _require_value(value: PlanRunValue | None, error: object) -> PlanRunValue:
    if value is not None:
        return value
    raise AssertionError(f"negative control produced no value: {error!r}")