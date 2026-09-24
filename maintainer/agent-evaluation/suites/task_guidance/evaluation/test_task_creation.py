"""The live task-creation matrix, parametrized from the configuration.

One case per scenario × producer cell, derived from the manifest; the
case ids support ``-k`` slicing (``-k glm``, ``-k tg01``, ``-k max``).
Every sample of a cell records its own stage record under the
invocation's run label.
"""

from __future__ import annotations

import hashlib

import pytest

from ..fixtures import FIXTURE_VERSION, fixture_sha256
from ..runner import TaskRunValue
from ..scenarios import TaskGuidanceScenario, scenario_by_id
from ..stages import STAGES
from ..topology import task_tree
from .matrix import CellCase, task_creation_cases


pytestmark = [pytest.mark.agent_eval, pytest.mark.task_creation]


@pytest.mark.parametrize("case", task_creation_cases(), ids=lambda item: item.id)
@pytest.mark.requirements(
    "TGEVAL-002",
    "TGEVAL-003",
    "TGEVAL-007",
    "TGEVAL-009",
    "TGEVAL-010",
    "DOCVAL-014",
)
def test_task_creation(
    agent_harness,
    run_options: dict[str, object],
    case: CellCase,
) -> None:
    scenario = scenario_by_id(case.scenario_id)
    harness = agent_harness(case.agent)
    runs = harness.run_task_creation(
        scenario=scenario,
        reasoning_effort=case.effort,
        fresh=bool(run_options["fresh"]),
        samples=int(run_options["samples"]),
    )
    for run in runs:
        _record_task_creation_run(harness, scenario, case, run)


def _record_task_creation_run(
    harness,
    scenario: TaskGuidanceScenario,
    case: CellCase,
    run,
) -> None:
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
        invalid_reasons.append(f"non-task changes: {non_task_changes}")
    delivery = value.delivery
    if delivery.get("agents_occurrences") != 1:
        invalid_reasons.append("workspace AGENTS.md was not delivered exactly once")
    if delivery.get("tasks_occurrences") != 1:
        invalid_reasons.append("TASKS-v7 was not delivered exactly once")
    if delivery.get("tool_family_matches") is not True:
        invalid_reasons.append("model-family tool schema does not match")
    if delivery.get("suite_wrapper_absent") is not True:
        invalid_reasons.append("suite-specific guidance wrapper was injected")

    target = scenario.target
    record = {
        "schema_version": 1,
        "scenario_id": scenario.scenario_id,
        "category": scenario.category,
        "project": target["project"],
        "fixture": {
            "version": FIXTURE_VERSION,
            "sha256": fixture_sha256(scenario.fixture_id),
        },
        "target_sha256": hashlib.sha256(scenario.target_path.read_bytes()).hexdigest(),
        "target": target,
        "prompt": scenario.prompt,
        "producer": {
            "profile": case.agent,
            "model": harness.agent["model"],
            "reasoning_effort": case.effort,
        },
        "changed_paths": changed,
        "task_files": value.task_files,
        "task_tree": task_tree(value.task_files),
        "tool_metrics": value.tool_metrics,
        "delivery": delivery,
        "response": value.response,
        "valid": not invalid_reasons,
        "invalid_reasons": invalid_reasons,
    }
    run.record(STAGES["task-creation"].record, record)
    run.record(
        "task-guidance-producer-summary.md",
        _summary_markdown(record),
    )
    assert not invalid_reasons, "\n".join(invalid_reasons)


def _require_value(value: TaskRunValue | None, error: object) -> TaskRunValue:
    if value is not None:
        return value
    raise AssertionError(f"producer returned no value: {error!r}")


def _summary_markdown(record: dict) -> str:
    lines = [
        f"# Task creation — {record['scenario_id']}",
        "",
        f"- Producer: `{record['producer']['profile']}`"
        f" ({record['producer']['model']}, effort"
        f" `{record['producer']['reasoning_effort']}`)",
        f"- Valid: `{record['valid']}`",
        f"- Task files: `{len(record['task_files'])}`",
        f"- Tool calls: `{record['tool_metrics']['total']}`",
    ]
    if record["invalid_reasons"]:
        lines.append("- Invalid reasons:")
        lines.extend(f"  - `{item}`" for item in record["invalid_reasons"])
    return "\n".join(lines) + "\n"
