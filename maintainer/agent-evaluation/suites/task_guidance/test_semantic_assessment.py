from __future__ import annotations

import json
import os
from collections.abc import Iterator
from pathlib import Path

import pytest

from .artifacts import selected_dataset_id
from .runner import TaskGuidanceHarness, selected_profile
from .scenarios import SCENARIOS, TaskGuidanceScenario
from .semantic import (
    load_producer_records,
    normalize_semantic_assessment,
    parse_semantic_response,
    producer_cells,
    semantic_prompt,
    semantic_summary,
    validate_semantic_assessment,
)


pytestmark = [pytest.mark.agent_eval, pytest.mark.task_guidance_semantic]


@pytest.fixture(scope="session")
def semantic_harness() -> Iterator[TaskGuidanceHarness]:
    profile = selected_profile()
    if profile.name != "glm":
        pytest.skip("semantic assessment uses the GLM profile")
    if os.getenv("AGENT_EVAL_RUN_REAL") != "1":
        raise RuntimeError("set AGENT_EVAL_RUN_REAL=1 for semantic assessment")
    harness = TaskGuidanceHarness(profile)
    yield harness
    harness.close()


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda item: item.scenario_id)
@pytest.mark.requirements("TGEVAL-007", "TGEVAL-009", "TGEVAL-010", "DOCVAL-014")
def test_task_guidance_b0_semantic_assessment(
    semantic_harness: TaskGuidanceHarness,
    scenario: TaskGuidanceScenario,
) -> None:
    producer_attempt = os.getenv(
        "AGENT_EVAL_TASK_GUIDANCE_RUN_ATTEMPT",
        "default",
    ).strip()
    semantic_attempt = os.getenv(
        "AGENT_EVAL_TASK_GUIDANCE_SEMANTIC_ATTEMPT",
        "default",
    ).strip()
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
    records = load_producer_records(
        artifact_root,
        scenario=scenario,
        run_attempt=producer_attempt,
        allow_partial=os.getenv(
            "AGENT_EVAL_TASK_ALLOW_PARTIAL",
            "",
        ).strip()
        == "1",
    )
    valid_records = [
        record for record in records if record.get("valid") is True
    ]
    invalid_records = [
        record for record in records if record.get("valid") is not True
    ]
    if not valid_records:
        raise AssertionError(
            f"no valid producers for {scenario.scenario_id}: "
            f"{[record.get('invalid_reasons') for record in invalid_records]!r}"
        )
    prompt = semantic_prompt(scenario, valid_records)
    run = semantic_harness.run_assessment(
        test_id=f"task-guidance-semantic-{scenario.scenario_id}",
        prompt=prompt,
        reasoning_effort="max",
        cache_variant=f"{producer_attempt}:{semantic_attempt}",
    )
    if run.value is None:
        raise AssertionError(f"semantic run produced no value: {run.error!r}")
    if run.error is not None or not run.value.completed or run.value.errors:
        raise AssertionError(
            f"semantic run failed: error={run.error!r}, "
            f"outcome_errors={run.value.errors!r}"
        )
    value = normalize_semantic_assessment(
        parse_semantic_response(run.value.response),
        records=valid_records,
    )
    cells = producer_cells(valid_records)
    validate_semantic_assessment(
        value,
        scenario=scenario,
        expected_cells=cells,
    )
    summary = semantic_summary(value)
    run.record(
        "task-guidance-semantic.json",
        {
            "schema_version": 1,
            "dataset_id": selected_dataset_id(),
            "scenario_id": scenario.scenario_id,
            "producer_attempt": producer_attempt,
            "semantic_attempt": semantic_attempt,
            "producer_records": valid_records,
            "invalid_producer_records": invalid_records,
            "assessment": value,
            "summary": summary,
        },
    )
    run.record(
        "task-guidance-semantic-summary.md",
        "# Task-guidance semantic assessment\n\n"
        f"- Scenario: `{scenario.scenario_id}`\n"
        f"- Valid producers: `{len(valid_records)}`\n"
        f"- Invalid producers skipped: `{len(invalid_records)}`\n"
        f"- Summary: `{json.dumps(summary, sort_keys=True)}`\n",
    )