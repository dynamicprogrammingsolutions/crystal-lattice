from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from .artifacts import selected_dataset_id
from .handoff_semantic import (
    handoff_semantic_prompt,
    load_handoff_records,
    parse_handoff_semantic,
    validate_handoff_semantic,
)
from .runner import TaskGuidanceHarness, selected_profile
from .scenarios import SCENARIOS, TaskGuidanceScenario


pytestmark = [pytest.mark.agent_eval, pytest.mark.task_guidance_semantic]


HANDOFF_SCENARIOS = tuple(
    scenario for scenario in SCENARIOS if scenario.category == "handoff"
)


@pytest.fixture(scope="session")
def handoff_semantic_harness() -> Iterator[TaskGuidanceHarness]:
    profile = selected_profile()
    if profile.name != "glm":
        pytest.skip("handoff semantic assessment uses GLM")
    if os.getenv("AGENT_EVAL_RUN_REAL") != "1":
        raise RuntimeError("set AGENT_EVAL_RUN_REAL=1 for semantic assessment")
    harness = TaskGuidanceHarness(profile)
    yield harness
    harness.close()


@pytest.mark.parametrize(
    "scenario",
    HANDOFF_SCENARIOS,
    ids=lambda item: item.scenario_id,
)
@pytest.mark.requirements("TGEVAL-004", "TGEVAL-005", "TGEVAL-006", "TGEVAL-008")
def test_handoff_semantic_assessment(
    handoff_semantic_harness: TaskGuidanceHarness,
    scenario: TaskGuidanceScenario,
) -> None:
    producer_attempt = os.getenv(
        "AGENT_EVAL_TASK_GUIDANCE_RUN_ATTEMPT",
        "default",
    ).strip()
    handoff_attempt = os.getenv(
        "AGENT_EVAL_TASK_HANDOFF_RUN_ATTEMPT",
        "default",
    ).strip()
    semantic_attempt = os.getenv(
        "AGENT_EVAL_TASK_GUIDANCE_SEMANTIC_ATTEMPT",
        "default",
    ).strip()
    allow_partial = os.getenv(
        "AGENT_EVAL_TASK_ALLOW_PARTIAL",
        "",
    ).strip() == "1"
    artifact_root = Path(
        os.getenv(
            "AGENT_EVAL_ARTIFACT_ROOT",
            str(
                Path(__file__).resolve().parents[4]
                / "tmp"
                / "agent-evaluation"
                / "task-guidance"
            ),
        )
    ).expanduser()
    fresh, same = load_handoff_records(
        artifact_root,
        scenario=scenario,
        handoff_attempt=handoff_attempt,
        producer_attempt=producer_attempt,
        allow_partial=allow_partial,
    )
    prompt = handoff_semantic_prompt(scenario, fresh, same)
    valid_count = sum(item.get("valid") is True for item in (*fresh, *same))
    run = handoff_semantic_harness.run_assessment(
        test_id=f"task-guidance-handoff-semantic-{scenario.scenario_id}",
        prompt=prompt,
        reasoning_effort="max",
        cache_variant=(
            f"{producer_attempt}:{handoff_attempt}:{semantic_attempt}"
        ),
    )
    if run.value is None or run.error is not None:
        raise AssertionError(f"handoff semantic run failed: {run.error!r}")
    if not run.value.completed or run.value.errors:
        raise AssertionError(
            f"handoff semantic provider errors: {run.value.errors!r}"
        )
    value = parse_handoff_semantic(run.value.response)
    validate_handoff_semantic(
        value,
        scenario=scenario,
        expected_count=valid_count,
    )
    run.record(
        "task-guidance-handoff-semantic.json",
        {
            "schema_version": 1,
            "dataset_id": selected_dataset_id(),
            "scenario_id": scenario.scenario_id,
            "producer_attempt": producer_attempt,
            "handoff_attempt": handoff_attempt,
            "semantic_attempt": semantic_attempt,
            "fresh_records": fresh,
            "same_agent_records": same,
            "assessment": value,
        },
    )
    run.record(
        "task-guidance-handoff-semantic-summary.md",
        "# Task-guidance handoff semantic assessment\n\n"
        f"- Scenario: `{scenario.scenario_id}`\n"
        f"- Assessments: `{valid_count}`\n"
        f"- Partial mode: `{allow_partial}`\n"
        f"- Raw JSON: `{json.dumps(value, sort_keys=True)[:1000]}`\n",
    )