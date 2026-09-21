from __future__ import annotations

import hashlib
import json
import os
import subprocess
from collections.abc import Iterator

import pytest

from .runner import (
    TaskGuidanceHarness,
    TaskRunValue,
    selected_profile,
)
from .artifacts import selected_dataset_id
from .fixtures import FIXTURE_VERSION, fixture_sha256
from .scenarios import SCENARIOS, TaskGuidanceScenario
from .topology import task_tree


pytestmark = [pytest.mark.agent_eval, pytest.mark.task_guidance_baseline]


PRODUCER_CELLS = (
    ("glm", "max", "all"),
    ("gpt", "high", "all"),
    ("gpt", "xhigh", "decomposition"),
    ("gpt", "max", "decomposition"),
)


@pytest.fixture(scope="session")
def task_guidance_harness() -> Iterator[TaskGuidanceHarness]:
    profile = selected_profile()
    _enforce_real_model_gate(profile.name, profile.model)
    harness = TaskGuidanceHarness(profile)
    yield harness
    harness.close()


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda item: item.scenario_id)
@pytest.mark.parametrize(
    ("producer_profile", "reasoning_effort", "scenario_category"),
    PRODUCER_CELLS,
    ids=lambda item: item,
)
@pytest.mark.requirements(
    "TGEVAL-002",
    "TGEVAL-003",
    "TGEVAL-007",
    "TGEVAL-009",
    "TGEVAL-010",
    "DOCVAL-014",
)
def test_task_guidance_b0_producer(
    task_guidance_harness: TaskGuidanceHarness,
    scenario: TaskGuidanceScenario,
    producer_profile: str,
    reasoning_effort: str,
    scenario_category: str,
) -> None:
    if task_guidance_harness.profile.name != producer_profile:
        pytest.skip(f"run with AGENT_EVAL_PROFILE={producer_profile}")
    if scenario_category != "all" and scenario.category != scenario_category:
        pytest.skip(f"{reasoning_effort} is limited to {scenario_category}")
    selected = os.getenv("AGENT_EVAL_TASK_SCENARIO", "").strip()
    if selected and scenario.scenario_id != selected:
        pytest.skip(f"run is limited to {selected}")
    selected_effort = os.getenv("AGENT_EVAL_TASK_EFFORT", "").strip()
    if selected_effort and reasoning_effort != selected_effort:
        pytest.skip(f"run is limited to effort {selected_effort}")

    repeat_variant = os.getenv(
        "AGENT_EVAL_TASK_GUIDANCE_RUN_ATTEMPT",
        "default",
    ).strip()
    run = task_guidance_harness.run_task_creation(
        scenario=scenario,
        reasoning_effort=reasoning_effort,
        cache_variant=repeat_variant,
    )
    value = _require_value(run.value, run.error)
    changed = tuple(run.changed_paths)
    changed_task_paths = tuple(
        path for path in changed if path.startswith("tasks/") and path.endswith(".md")
    )
    invalid_reasons: list[str] = []
    if run.error is not None:
        invalid_reasons.append(f"run error: {run.error}")
    if not value.completed:
        invalid_reasons.append("request did not complete")
    if value.errors:
        invalid_reasons.append(f"provider errors: {value.errors!r}")
    if not value.response.strip():
        invalid_reasons.append("assistant response is empty")
    if not value.task_files:
        invalid_reasons.append("no task files were produced")
    if set(value.task_files) != set(changed_task_paths):
        invalid_reasons.append(
            "captured task files do not match changed task paths: "
            f"{sorted(value.task_files)!r} != {sorted(changed_task_paths)!r}"
        )
    non_task_changes = [path for path in changed if path not in changed_task_paths]
    if non_task_changes:
        invalid_reasons.append(f"non-task changes: {non_task_changes!r}")
    delivery = value.delivery
    if delivery.get("agents_occurrences") != 1:
        invalid_reasons.append("workspace AGENTS.md was not delivered exactly once")
    if delivery.get("tasks_occurrences") != 1:
        invalid_reasons.append("TASKS-v7 was not delivered exactly once")
    if delivery.get("tool_family_matches") is not True:
        invalid_reasons.append("model-family tool schema does not match")
    if delivery.get("suite_wrapper_absent") is not True:
        invalid_reasons.append("suite-specific guidance wrapper was injected")

    tree = task_tree(value.task_files)
    target = scenario.target
    record = {
        "schema_version": 1,
        "dataset_id": selected_dataset_id(),
        "scenario_id": scenario.scenario_id,
        "category": scenario.category,
        "project": target["project"],
        "fixture": {
            "version": FIXTURE_VERSION,
            "sha256": fixture_sha256(scenario.fixture_id),
        },
        "target_sha256": hashlib.sha256(
            scenario.target_path.read_bytes()
        ).hexdigest(),
        "target": target,
        "prompt": scenario.prompt,
        "producer": {
            "profile": producer_profile,
            "model": task_guidance_harness.profile.model,
            "reasoning_effort": reasoning_effort,
        },
        "run_attempt": repeat_variant,
        "changed_paths": changed,
        "task_files": value.task_files,
        "task_tree": tree,
        "tool_metrics": value.tool_metrics,
        "delivery": delivery,
        "response": value.response,
        "valid": not invalid_reasons,
        "invalid_reasons": invalid_reasons,
    }
    run.record("task-guidance-producer.json", record)
    run.record(
        "task-guidance-producer-summary.md",
        _summary_markdown(record),
    )
    assert not invalid_reasons, "\n".join(invalid_reasons)


def _require_value(value: TaskRunValue | None, error: object) -> TaskRunValue:
    if value is not None:
        return value
    raise AssertionError(f"producer returned no value: {error!r}")


def _summary_markdown(record: dict[str, object]) -> str:
    tree = record["task_tree"]
    assert isinstance(tree, dict)
    lines = [
        f"# Task-guidance producer: {record['scenario_id']}",
        "",
        f"- Valid: `{record['valid']}`",
        f"- Producer: `{json.dumps(record['producer'], sort_keys=True)}`",
        f"- Task files: `{tree['task_file_count']}`",
        f"- Phase-named files: `{len(tree['phase_named_files'])}`",
        f"- Tool metrics: `{json.dumps(record['tool_metrics'], sort_keys=True)}`",
        "",
        "## Task files",
        "",
    ]
    for path in sorted(cast_dict(record["task_files"])):
        lines.append(f"- `{path}`")
    if record["invalid_reasons"]:
        lines.extend(["", "## Invalid reasons", ""])
        lines.extend(f"- {item}" for item in record["invalid_reasons"])
    return "\n".join(lines).rstrip() + "\n"


def cast_dict(value: object) -> dict[str, object]:
    if not isinstance(value, dict):
        raise TypeError(f"expected dict, got {type(value).__name__}")
    return value


def _enforce_real_model_gate(profile_name: str, model: str) -> None:
    if os.getenv("AGENT_EVAL_RUN_REAL") != "1":
        raise RuntimeError("set AGENT_EVAL_RUN_REAL=1 to execute producers")
    if profile_name == "gpt" and os.getenv("AGENT_EVAL_ALLOW_HOSTED") != "1":
        raise RuntimeError("set AGENT_EVAL_ALLOW_HOSTED=1 for ChatGPT producers")
    if profile_name == "glm":
        result = subprocess.run(
            ["ollama", "show", model],
            check=False,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            detail = (result.stderr or result.stdout).strip()
            raise RuntimeError(f"Ollama cannot resolve {model!r}: {detail}")