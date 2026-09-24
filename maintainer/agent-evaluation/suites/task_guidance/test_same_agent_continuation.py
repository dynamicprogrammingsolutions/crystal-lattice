from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

from .artifacts import selected_dataset_id
from .runner import PlanRunValue, TaskGuidanceHarness, TaskRunValue, selected_agent
from .scenarios import SCENARIOS, TaskGuidanceScenario


pytestmark = [pytest.mark.agent_eval, pytest.mark.task_guidance_baseline]


HANDOFF_SCENARIOS = tuple(
    scenario for scenario in SCENARIOS if scenario.category == "handoff"
)
CONTINUATION_CELLS = (("glm", "max"), ("gpt", "high"))


@pytest.fixture(scope="session")
def continuation_harness() -> Iterator[TaskGuidanceHarness]:
    agent_name = selected_agent()
    if os.getenv("AGENT_EVAL_RUN_REAL") != "1":
        raise RuntimeError("set AGENT_EVAL_RUN_REAL=1 for continuation tests")
    if agent_name == "gpt" and os.getenv("AGENT_EVAL_ALLOW_HOSTED") != "1":
        raise RuntimeError("set AGENT_EVAL_ALLOW_HOSTED=1 for ChatGPT")
    harness = TaskGuidanceHarness(agent_name)
    yield harness
    harness.close()


@pytest.mark.parametrize(
    ("producer_profile", "reasoning_effort"),
    CONTINUATION_CELLS,
    ids=lambda value: value,
)
@pytest.mark.parametrize(
    "scenario",
    HANDOFF_SCENARIOS,
    ids=lambda item: item.scenario_id,
)
@pytest.mark.requirements("TGEVAL-005", "TGEVAL-008", "TGEVAL-010")
def test_same_agent_continues_from_generated_task(
    continuation_harness: TaskGuidanceHarness,
    scenario: TaskGuidanceScenario,
    producer_profile: str,
    reasoning_effort: str,
) -> None:
    if continuation_harness.agent_name != producer_profile:
        pytest.skip(f"run with AGENT_EVAL_PROFILE={producer_profile}")
    selected = os.getenv("AGENT_EVAL_TASK_SCENARIO", "").strip()
    if selected and scenario.scenario_id != selected:
        pytest.skip(f"run is limited to {selected}")
    attempt = os.getenv(
        "AGENT_EVAL_TASK_GUIDANCE_RUN_ATTEMPT",
        "default",
    ).strip()
    parent = continuation_harness.run_task_creation(
        scenario=scenario,
        reasoning_effort=reasoning_effort,
        cache_variant=attempt,
    )
    parent_value = _require_task_value(parent.value, parent.error)
    parent_invalid: list[str] = []
    if parent.error is not None:
        parent_invalid.append(f"parent run error: {parent.error!r}")
    if not parent_value.completed or parent_value.errors:
        parent_invalid.append(
            "parent provider failure: "
            f"completed={parent_value.completed!r}, "
            f"errors={parent_value.errors!r}"
        )
    if not parent_value.response.strip():
        parent_invalid.append("parent assistant response is empty")
    if not parent_value.task_files:
        parent_invalid.append("parent task creation produced no task files")
    if parent_value.delivery.get("agents_occurrences") != 1:
        parent_invalid.append("parent AGENTS.md delivery mismatch")
    if parent_value.delivery.get("tasks_occurrences") != 1:
        parent_invalid.append("parent TASKS-v7 delivery mismatch")
    if parent_value.delivery.get("tool_family_matches") is not True:
        parent_invalid.append("parent model-family tool schema mismatch")
    if parent_invalid:
        parent.record(
            "task-guidance-same-agent-plan.json",
            {
                "schema_version": 1,
                "dataset_id": selected_dataset_id(),
                "scenario_id": scenario.scenario_id,
                "producer": {
                    "profile": producer_profile,
                    "model": continuation_harness.agent["model"],
                    "reasoning_effort": reasoning_effort,
                },
                "run_attempt": attempt,
                "target": scenario.target,
                "task_files": parent_value.task_files,
                "response": "",
                "task_creation_tool_metrics": parent_value.tool_metrics,
                "continuation_tool_metrics": {
                    "list": 0,
                    "mutation": 0,
                    "other": 0,
                    "read": 0,
                    "search": 0,
                    "shell": 0,
                    "total": 0,
                },
                "valid": False,
                "invalid_reasons": parent_invalid,
            },
        )
        raise AssertionError("\n".join(parent_invalid))

    run = continuation_harness.continue_same_agent_plan(
        parent=parent,
        scenario=scenario,
        reasoning_effort=reasoning_effort,
    )
    value = _require_plan_value(run.value, run.error)
    invalid: list[str] = []
    if run.error is not None or not value.completed or value.errors:
        invalid.append(f"run failure: {run.error!r}, {value.errors!r}")
    if not value.response.strip():
        invalid.append("empty planning response")
    if value.mutation_count:
        invalid.append(f"planning used mutation tools: {value.mutation_count}")
    if dict(value.task_files) != dict(parent_value.task_files):
        invalid.append("planning changed the generated task files")
    record = {
        "schema_version": 1,
        "dataset_id": selected_dataset_id(),
        "scenario_id": scenario.scenario_id,
        "producer": {
            "profile": producer_profile,
            "model": continuation_harness.agent["model"],
            "reasoning_effort": reasoning_effort,
        },
        "run_attempt": attempt,
        "target": scenario.target,
        "task_files": parent_value.task_files,
        "response": value.response,
        "task_creation_tool_metrics": parent_value.tool_metrics,
        "continuation_tool_metrics": value.tool_metrics,
        "valid": not invalid,
        "invalid_reasons": invalid,
    }
    run.record("task-guidance-same-agent-plan.json", record)
    assert not invalid, "\n".join(invalid)


def _require_task_value(
    value: TaskRunValue | None,
    error: object,
) -> TaskRunValue:
    if value is not None:
        return value
    raise AssertionError(f"task creation produced no value: {error!r}")


def _require_plan_value(
    value: PlanRunValue | None,
    error: object,
) -> PlanRunValue:
    if value is not None:
        return value
    raise AssertionError(f"continuation produced no value: {error!r}")
