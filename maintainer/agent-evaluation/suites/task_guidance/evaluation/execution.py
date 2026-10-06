"""Shared case-execution recipes for the live matrix.

The parametrized live tests and the parallel run CLI both execute every
case through these functions, so the pytest path and the CLI path share
one recipe: request execution, validity checking, and record writing
happen in exactly one place. Producers and dependent stages fail loudly
on invalid samples; assessments raise :class:`CaseSkipped` when their
upstream records are missing or hold no valid subject.
"""

from __future__ import annotations

import json

import hashlib
from typing import Callable, Mapping

from ..configuration import (
    assessment_cell,
    planning_cell,
    planning_gate_cell,
    selected_artifact_root,
)
from ..file_quality import (
    file_fidelity_prompt,
    file_fidelity_record,
    file_readability_prompt,
    file_readability_record,
    normalize_file_fidelity,
    normalize_file_readability,
    parse_file_fidelity,
    parse_file_readability,
    validate_file_fidelity,
    validate_file_readability,
)
from ..fixtures import FIXTURE_VERSION, fixture_sha256
from ..handoff_semantic import (
    handoff_assessment_record,
    handoff_semantic_prompt,
    load_handoff_subjects,
    parse_handoff_semantic,
    validate_handoff_semantic,
)
from ..plan_content import (
    expected_plan_requirement_ids,
    normalize_plan_content_assessment,
    parse_plan_content_response,
    plan_content_prompt,
    plan_content_record,
    requirement_grades,
    validate_plan_content_assessment,
)
from ..runner import PlanRunValue, PlanningRunValue, TaskRunValue, TaskGuidanceHarness
from ..scenarios import TaskGuidanceScenario, scenario_by_id
from ..semantic import (
    assessment_record,
    load_producer_subjects,
    normalize_semantic_assessment,
    parse_semantic_response,
    semantic_prompt,
    validate_semantic_assessment,
)
from ..stages import STAGES
from ..structure import plan_is_absent_or_draft
from ..topology import task_tree
from .matrix import CellCase

HarnessFactory = Callable[..., TaskGuidanceHarness]


class CaseSkipped(Exception):
    """The case has no runnable subject (missing upstream records)."""


def _options(options: Mapping[str, object]) -> tuple[bool, int]:
    return bool(options["fresh"]), int(options["samples"])


# --- task-creation ---------------------------------------------------------


def execute_task_creation(
    harness_factory: HarnessFactory,
    run_label: str,
    options: Mapping[str, object],
    case: CellCase,
) -> None:
    scenario = scenario_by_id(case.scenario_id)
    harness = harness_factory(case.agent)
    fresh, samples = _options(options)
    runs = harness.run_task_creation(
        scenario=scenario,
        reasoning_effort=case.effort,
        fresh=fresh,
        samples=samples,
    )
    for run in runs:
        _record_task_creation_run(harness, scenario, case, run)


def _record_task_creation_run(
    harness: TaskGuidanceHarness,
    scenario: TaskGuidanceScenario,
    case: CellCase,
    run,
) -> None:
    value = _require_task_value(run.value, run.error)
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
    if (target.get("execution_plan") or {}).get("expected") == "absent-or-draft":
        invalid_reasons.extend(
            f"execution-plan expectation violated: {violation}"
            for violation in plan_is_absent_or_draft(value.task_files)
        )
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


# --- handoff-plan ----------------------------------------------------------


def execute_handoff_plan(
    harness_factory: HarnessFactory,
    run_label: str,
    options: Mapping[str, object],
    case: CellCase,
) -> None:
    assert case.variant is not None
    scenario = scenario_by_id(case.scenario_id)
    harness = harness_factory(case.agent)
    fresh, samples = _options(options)
    runs = harness.run_plan_from_handoff(
        scenario=scenario,
        variant=case.variant,
        reasoning_effort=case.effort,
        fresh=fresh,
        samples=samples,
    )
    for run in runs:
        _record_plan_run(harness, scenario, case, run)


def _record_plan_run(
    harness: TaskGuidanceHarness,
    scenario: TaskGuidanceScenario,
    case: CellCase,
    run,
) -> None:
    value = _require_plan_value(run.value, run.error)
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
        "scenario_id": scenario.scenario_id,
        "variant": case.variant,
        "producer": {
            "profile": case.agent,
            "model": harness.agent["model"],
            "reasoning_effort": case.effort,
        },
        "target_sha256": hashlib.sha256(scenario.target_path.read_bytes()).hexdigest(),
        "target": scenario.target,
        "response": value.response,
        "tool_metrics": value.tool_metrics,
        "task_files": value.task_files,
        "delivery": value.delivery,
        "valid": not invalid,
        "invalid_reasons": invalid,
    }
    run.record(STAGES["handoff-plan"].record, record)
    assert not invalid, "\n".join(invalid)


# --- planning-session -------------------------------------------------------


def execute_planning_session(
    harness_factory: HarnessFactory,
    run_label: str,
    options: Mapping[str, object],
    case: CellCase,
) -> None:
    assert case.variant is not None
    scenario = scenario_by_id(case.scenario_id)
    harness = harness_factory(case.agent)
    fresh, samples = _options(options)
    runs = harness.run_planning_session(
        scenario=scenario,
        variant=case.variant,
        reasoning_effort=case.effort,
        fresh=fresh,
        samples=samples,
    )
    judge, judge_effort = planning_gate_cell(scenario.category)
    judge_harness = harness_factory(judge)
    for run in runs:
        record = _record_planning_session_run(harness, scenario, case, run)
        _gate_planning_run(
            judge_harness,
            run,
            scenario=scenario,
            case=case,
            planning_record=record,
            reasoning_effort=judge_effort,
            fresh=fresh,
            samples=samples,
        )


def _record_planning_session_run(
    harness: TaskGuidanceHarness,
    scenario: TaskGuidanceScenario,
    case: CellCase,
    run,
) -> None:
    value = _require_planning_value(run.value, run.error)
    invalid: list[str] = []
    if run.error is not None or not value.completed or value.errors:
        invalid.append(f"run failure: {run.error!r}, {value.errors!r}")
    if not value.response.strip():
        invalid.append("empty planning response")
    if run.changed_paths:
        invalid.append(f"planning mutated files: {run.changed_paths!r}")
    delivery = value.delivery
    if delivery.get("agents_occurrences") != 1:
        invalid.append("AGENTS.md delivery mismatch")
    expected_tasks = 1 if value.variant == "guided" else 0
    if delivery.get("tasks_occurrences") != expected_tasks:
        invalid.append(
            f"TASKS-v7 delivery mismatch for arm {value.variant}: "
            f"{delivery.get('tasks_occurrences')!r} != {expected_tasks}"
        )
    if delivery.get("include_tasks") is not (value.variant == "guided"):
        invalid.append("recorded include_tasks flag does not match the arm")
    if delivery.get("tool_family_matches") is not True:
        invalid.append("model-family tool schema does not match")
    record = {
        "schema_version": 1,
        "scenario_id": scenario.scenario_id,
        "category": scenario.category,
        "variant": value.variant,
        "target_sha256": hashlib.sha256(scenario.target_path.read_bytes()).hexdigest(),
        "target": scenario.target,
        "producer": {
            "profile": case.agent,
            "model": harness.agent["model"],
            "reasoning_effort": case.effort,
        },
        "prompt": value.prompt,
        "response": value.response,
        "tool_metrics": value.tool_metrics,
        "delivery": delivery,
        "valid": not invalid,
        "invalid_reasons": invalid,
    }
    run.record(STAGES["planning-session"].record, record)
    assert not invalid, "\n".join(invalid)
    return record


PLANNING_GATE_RECORD = "task-guidance-planning-gate.json"


def plan_gate_evaluation(
    scenario: TaskGuidanceScenario,
    assessment: Mapping[str, object],
) -> dict:
    """The deterministic gate verdict over one normalized plan assessment.

    Coverage is the fraction of the scenario's plan requirements graded
    at the top of their scale; missing grades cannot reach this function
    (normalization rejects them), so the gate is coverage plus the
    scenario's stricter threshold when it declares one.
    """

    expected = expected_plan_requirement_ids(scenario)
    scales = requirement_grades(scenario)
    covered = sum(
        1
        for requirement_id in expected
        if assessment["requirements"][requirement_id]["grade"]
        == scales[requirement_id][0]
    )
    coverage = covered / len(expected)
    threshold = float(scenario.target.get("plan_gate_min_coverage", 0.8))
    return {
        "coverage": coverage,
        "threshold": threshold,
        "missed_requirements": list(assessment["missed_requirements"]),
        "passed": coverage >= threshold,
    }


def _gate_planning_run(
    judge_harness: TaskGuidanceHarness,
    run,
    *,
    scenario: TaskGuidanceScenario,
    case: CellCase,
    planning_record: Mapping[str, object],
    reasoning_effort: str,
    fresh: bool,
    samples: int,
) -> None:
    """Judge one planning run and record its gate beside the planning record."""

    prompt = plan_content_prompt(scenario, planning_record)
    gate_runs = judge_harness.run_assessment(
        test_id=(
            f"task-guidance-plan-gate-{scenario.scenario_id}-"
            f"{case.variant}-s{run.sample_index if hasattr(run, 'sample_index') else 0}"
        ),
        prompt=prompt,
        reasoning_effort=reasoning_effort,
        fresh=fresh,
        samples=samples,
    )
    for gate_run in gate_runs:
        value = _require_assessment_value(gate_run)
        try:
            assessment = normalize_plan_content_assessment(
                parse_plan_content_response(value.response),
                scenario=scenario,
            )
            verdict = plan_gate_evaluation(scenario, assessment)
        except ValueError as error:
            verdict = None
            gate_failure = f"gate assessment unusable: {error}"
        if verdict is not None:
            gate_failure = None
            run.record(
                PLANNING_GATE_RECORD,
                {
                    "schema_version": 1,
                    "scenario_id": scenario.scenario_id,
                    "variant": case.variant,
                    "judge": {
                        "profile": judge_harness.agent_name,
                        "model": judge_harness.agent["model"],
                        "reasoning_effort": reasoning_effort,
                    },
                    "assessment": assessment,
                    "gate": verdict,
                },
            )
        assert gate_failure is None, gate_failure


# --- task-creation-from-plan ------------------------------------------------


def execute_task_creation_from_plan(
    harness_factory: HarnessFactory,
    run_label: str,
    options: Mapping[str, object],
    case: CellCase,
) -> None:
    assert case.variant is not None
    assert case.parent_variant is not None
    scenario = scenario_by_id(case.scenario_id)
    planning_agent, planning_effort = planning_cell(scenario.category)
    planning_harness = harness_factory(planning_agent)
    fresh, samples = _options(options)
    parents = planning_harness.run_planning_session(
        scenario=scenario,
        variant=case.parent_variant,
        reasoning_effort=planning_effort,
        fresh=fresh,
        samples=samples,
    )
    harness = harness_factory(case.agent, thinking=case.thinking)
    for parent in parents:
        parent_value = _require_planning_value(parent.value, parent.error)
        _require_valid_planning_parent(parent, parent_value)
        runs = harness.run_task_creation_from_plan(
            parent=parent,
            scenario=scenario,
            variant=case.variant,
            reasoning_effort=case.effort,
            fresh=fresh,
            samples=samples,
        )
        for run in runs:
            _record_from_plan_run(harness, scenario, case, run, parent_value)


def _require_valid_planning_parent(parent, parent_value) -> None:
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
        parent_invalid.append("parent planning response is empty")
    if parent.changed_paths:
        parent_invalid.append(
            f"parent planning mutated files: {parent.changed_paths!r}"
        )
    delivery = parent_value.delivery
    if delivery.get("agents_occurrences") != 1:
        parent_invalid.append("parent AGENTS.md delivery mismatch")
    expected_tasks = 1 if parent_value.variant == "guided" else 0
    if delivery.get("tasks_occurrences") != expected_tasks:
        parent_invalid.append("parent TASKS-v7 delivery mismatch")
    if parent_invalid:
        raise AssertionError("\n".join(parent_invalid))


def _record_from_plan_run(
    harness: TaskGuidanceHarness,
    scenario: TaskGuidanceScenario,
    case: CellCase,
    run,
    parent_value,
) -> None:
    value = _require_task_value(run.value, run.error)
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
    if case.variant == "omit-plan":
        invalid_reasons.extend(
            f"instructed omission violated: {violation}"
            for violation in plan_is_absent_or_draft(value.task_files)
        )

    target = scenario.target
    record = {
        "schema_version": 1,
        "scenario_id": scenario.scenario_id,
        "category": scenario.category,
        "variant": case.variant,
        "planning_variant": case.parent_variant,
        "thinking": case.thinking,
        "project": target["project"],
        "fixture": {
            "version": FIXTURE_VERSION,
            "sha256": fixture_sha256(scenario.fixture_id),
        },
        "target_sha256": hashlib.sha256(scenario.target_path.read_bytes()).hexdigest(),
        "target": target,
        "prompt": value.prompt,
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
        "plan_response": parent_value.response,
        "valid": not invalid_reasons,
        "invalid_reasons": invalid_reasons,
    }
    run.record(STAGES["task-creation-from-plan"].record, record)
    assert not invalid_reasons, "\n".join(invalid_reasons)


# --- continuation ----------------------------------------------------------


def execute_continuation(
    harness_factory: HarnessFactory,
    run_label: str,
    options: Mapping[str, object],
    case: CellCase,
) -> None:
    scenario = scenario_by_id(case.scenario_id)
    harness = harness_factory(case.agent)
    fresh, samples = _options(options)
    parents = harness.run_task_creation(
        scenario=scenario,
        reasoning_effort=case.effort,
        fresh=fresh,
        samples=samples,
    )
    for parent in parents:
        parent_value = _require_task_value(parent.value, parent.error)
        _require_valid_parent(parent, parent_value)
        runs = harness.continue_same_agent_plan(
            parent=parent,
            scenario=scenario,
            reasoning_effort=case.effort,
            fresh=fresh,
            samples=samples,
        )
        for run in runs:
            _record_continuation_run(harness, scenario, case, run, parent_value)


def _require_valid_parent(parent, parent_value: TaskRunValue) -> None:
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
        raise AssertionError("\n".join(parent_invalid))


def _record_continuation_run(
    harness: TaskGuidanceHarness,
    scenario: TaskGuidanceScenario,
    case: CellCase,
    run,
    parent_value: TaskRunValue,
) -> None:
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
        "scenario_id": scenario.scenario_id,
        "producer": {
            "profile": case.agent,
            "model": harness.agent["model"],
            "reasoning_effort": case.effort,
        },
        "target": scenario.target,
        "task_files": parent_value.task_files,
        "response": value.response,
        "task_creation_tool_metrics": parent_value.tool_metrics,
        "continuation_tool_metrics": value.tool_metrics,
        "valid": not invalid,
        "invalid_reasons": invalid,
    }
    run.record(STAGES["continuation"].record, record)
    assert not invalid, "\n".join(invalid)


# --- generated-plan --------------------------------------------------------


def execute_generated_plan(
    harness_factory: HarnessFactory,
    run_label: str,
    options: Mapping[str, object],
    case: CellCase,
) -> None:
    scenario = scenario_by_id(case.scenario_id)
    harness = harness_factory(case.agent)
    fresh, samples = _options(options)
    parents = harness.run_task_creation(
        scenario=scenario,
        reasoning_effort=case.effort,
        fresh=fresh,
        samples=samples,
    )
    for parent in parents:
        parent_value = _require_task_value(parent.value, parent.error)
        if not parent_value.task_files:
            raise AssertionError("parent task creation produced no task files")
        runs = harness.run_plan_from_generated(
            parent=parent,
            scenario=scenario,
            reasoning_effort=case.effort,
            fresh=fresh,
            samples=samples,
        )
        for run in runs:
            _record_generated_plan_run(harness, scenario, case, run, parent_value)


def _record_generated_plan_run(
    harness: TaskGuidanceHarness,
    scenario: TaskGuidanceScenario,
    case: CellCase,
    run,
    parent_value: TaskRunValue,
) -> None:
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
        "scenario_id": scenario.scenario_id,
        "producer": {
            "profile": case.agent,
            "model": harness.agent["model"],
            "reasoning_effort": case.effort,
        },
        "target": scenario.target,
        "task_files": parent_value.task_files,
        "response": value.response,
        "task_creation_tool_metrics": parent_value.tool_metrics,
        "planning_tool_metrics": value.tool_metrics,
        "valid": not invalid,
        "invalid_reasons": invalid,
    }
    run.record(STAGES["generated-plan"].record, record)
    assert not invalid, "\n".join(invalid)


# --- negative-control -------------------------------------------------------


def execute_negative_control(
    harness_factory: HarnessFactory,
    run_label: str,
    options: Mapping[str, object],
    case: CellCase,
) -> None:
    assert case.variant is not None
    scenario = scenario_by_id(case.scenario_id)
    harness = harness_factory(case.agent)
    fresh, samples = _options(options)
    runs = harness.run_negative_control(
        category=case.category,
        fresh=fresh,
        samples=samples,
    )
    for run in runs:
        _record_control_run(harness, scenario, case, run)


def _record_control_run(
    harness: TaskGuidanceHarness,
    scenario: TaskGuidanceScenario,
    case: CellCase,
    run,
) -> None:
    value = _require_plan_value(run.value, run.error)
    invalid: list[str] = []
    if run.error is not None or not value.completed or value.errors:
        invalid.append(f"run failure: {run.error!r}, {value.errors!r}")
    if not value.response.strip():
        invalid.append("empty planning response")
    if run.changed_paths:
        invalid.append(f"planning mutated files: {run.changed_paths!r}")
    record = {
        "schema_version": 1,
        "scenario_id": scenario.scenario_id,
        "variant": case.variant,
        "producer": {
            "profile": case.agent,
            "model": harness.agent["model"],
            "reasoning_effort": case.effort,
        },
        "response": value.response,
        "tool_metrics": value.tool_metrics,
        "task_files": value.task_files,
        "valid": not invalid,
        "invalid_reasons": invalid,
    }
    run.record(STAGES["negative-control"].record, record)
    assert not invalid, "\n".join(invalid)


# --- shared -----------------------------------------------------------------


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
    raise AssertionError(f"planning produced no value: {error!r}")


def _require_planning_value(
    value: PlanningRunValue | None,
    error: object,
) -> PlanningRunValue:
    if value is not None:
        return value
    raise AssertionError(f"planning session produced no value: {error!r}")


# --- assessments -------------------------------------------------------------


def _load_subjects(loader, run_label: str, **kwargs):
    try:
        return loader(selected_artifact_root(), labels=[run_label], **kwargs)
    except FileNotFoundError as error:
        raise CaseSkipped(
            f"missing upstream records under label {run_label!r}: {error}"
        ) from error


def _require_assessment_value(run) -> object:
    if run.value is None:
        raise AssertionError(f"assessment produced no value: {run.error!r}")
    if run.error is not None or not run.value.completed or run.value.errors:
        raise AssertionError(
            f"assessment failed: error={run.error!r}, "
            f"outcome_errors={run.value.errors!r}"
        )
    return run.value


def execute_task_creation_assessment(
    harness_factory: HarnessFactory,
    run_label: str,
    options: Mapping[str, object],
    case: CellCase,
) -> None:
    scenario = scenario_by_id(case.scenario_id)
    judge, judge_effort = assessment_cell(scenario.category, "task-creation-assessment")
    harness = harness_factory(judge)
    subjects = _load_subjects(
        load_producer_subjects,
        run_label,
        scenario=scenario,
        cells=[(case.agent, case.effort)],
    )
    from ..semantic import subjects_block_reason

    reason = subjects_block_reason(subjects)
    if reason is not None:
        raise CaseSkipped(reason)
    fresh, samples = _options(options)
    for subject in subjects:
        prompt = semantic_prompt(scenario, subject.record)
        runs = harness.run_assessment(
            test_id=(
                f"task-guidance-semantic-{scenario.scenario_id}-"
                f"{subject.profile}-{subject.effort}-s{subject.sample_index}"
            ),
            prompt=prompt,
            reasoning_effort=judge_effort,
            fresh=fresh,
            samples=samples,
        )
        for run in runs:
            value = _require_assessment_value(run)
            assessment = normalize_semantic_assessment(
                parse_semantic_response(value.response),
                record=subject.record,
            )
            validate_semantic_assessment(assessment, scenario=scenario)
            record = assessment_record(scenario, subject, assessment["assessment"])
            run.record(STAGES["task-creation-assessment"].record, record)
            run.record(
                "task-guidance-semantic-summary.md",
                "# Task-guidance semantic assessment\n\n"
                f"- Scenario: `{scenario.scenario_id}`\n"
                f"- Subject: `{subject.profile}:{subject.effort}`"
                f" sample {subject.sample_index}\n"
                f"- Summary: `{record['summary']}`\n",
            )


def execute_handoff_assessment(
    harness_factory: HarnessFactory,
    run_label: str,
    options: Mapping[str, object],
    case: CellCase,
) -> None:
    assert case.variant is not None
    scenario = scenario_by_id(case.scenario_id)
    judge, judge_effort = assessment_cell(scenario.category, "handoff-assessment")
    harness = harness_factory(judge)
    stage = "same-agent" if case.variant == "generated-task" else "fresh-agent"
    subjects = _load_subjects(
        load_handoff_subjects,
        run_label,
        scenario=scenario,
        selection={(stage, case.variant, case.agent, case.effort)},
    )
    from ..handoff_semantic import subjects_block_reason

    reason = subjects_block_reason(subjects)
    if reason is not None:
        raise CaseSkipped(reason)
    fresh, samples = _options(options)
    for subject in subjects:
        prompt = handoff_semantic_prompt(scenario, subject)
        runs = harness.run_assessment(
            test_id=(
                f"task-guidance-handoff-semantic-{scenario.scenario_id}-"
                f"{subject.variant}-{subject.profile}-{subject.effort}-"
                f"s{subject.sample_index}"
            ),
            prompt=prompt,
            reasoning_effort=judge_effort,
            fresh=fresh,
            samples=samples,
        )
        for run in runs:
            value = _require_assessment_value(run)
            parsed = parse_handoff_semantic(value.response)
            validate_handoff_semantic(
                parsed,
                scenario=scenario,
                stage=subject.stage,
                variant=subject.variant,
            )
            record = handoff_assessment_record(scenario, subject, parsed["assessment"])
            run.record(STAGES["handoff-assessment"].record, record)
            run.record(
                "task-guidance-handoff-semantic-summary.md",
                "# Task-guidance handoff semantic assessment\n\n"
                f"- Scenario: `{scenario.scenario_id}`\n"
                f"- Subject: `{subject.stage}:{subject.variant}:"
                f"{subject.profile}:{subject.effort}`"
                f" sample {subject.sample_index}\n"
                f"- Score: `{record['assessment']['handoff_quality_score']}`\n",
            )


def execute_plan_content_assessment(
    harness_factory: HarnessFactory,
    run_label: str,
    options: Mapping[str, object],
    case: CellCase,
) -> None:
    assert case.variant is not None
    scenario = scenario_by_id(case.scenario_id)
    judge, judge_effort = assessment_cell(scenario.category, "plan-content-assessment")
    harness = harness_factory(judge)
    stage = "same-agent" if case.variant == "generated-task" else "fresh-agent"
    subjects = _load_subjects(
        load_handoff_subjects,
        run_label,
        scenario=scenario,
        selection={(stage, case.variant, case.agent, case.effort)},
    )
    from ..handoff_semantic import subjects_block_reason

    reason = subjects_block_reason(subjects)
    if reason is not None:
        raise CaseSkipped(reason)
    fresh, samples = _options(options)
    for subject in subjects:
        prompt = plan_content_prompt(scenario, subject.record)
        runs = harness.run_assessment(
            test_id=(
                f"task-guidance-plan-content-{scenario.scenario_id}-"
                f"{subject.variant}-{subject.profile}-{subject.effort}-"
                f"s{subject.sample_index}"
            ),
            prompt=prompt,
            reasoning_effort=judge_effort,
            fresh=fresh,
            samples=samples,
        )
        for run in runs:
            value = _require_assessment_value(run)
            assessment = normalize_plan_content_assessment(
                parse_plan_content_response(value.response),
                scenario=scenario,
            )
            validate_plan_content_assessment(assessment, scenario=scenario)
            record = plan_content_record(scenario, subject, assessment)
            run.record(STAGES["plan-content-assessment"].record, record)
            run.record(
                "task-guidance-plan-content-summary.md",
                "# Task-guidance presented-plan content assessment\n\n"
                f"- Scenario: `{scenario.scenario_id}`\n"
                f"- Subject: `{subject.stage}:{subject.variant}:"
                f"{subject.profile}:{subject.effort}`"
                f" sample {subject.sample_index}\n"
                f"- Summary: `{record['summary']}`\n",
            )


JUDGE_JSON_RETRIES = 2


def _parse_judge_response(run, parse, rerun):
    """Parse a judge JSON response, retrying malformed output.

    A judge response that still fails JSON parsing (after the parsers'
    own fence/brace fallback) is re-requested up to ``JUDGE_JSON_RETRIES``
    times within the same logical assessment; re-runs bypass the cache
    read so the same malformed response is not re-served, and a
    successful final retry becomes the cached one.
    """

    current = run
    for retry in range(JUDGE_JSON_RETRIES + 1):
        value = _require_assessment_value(current)
        try:
            return parse(value.response), current
        except json.JSONDecodeError:
            if retry == JUDGE_JSON_RETRIES:
                raise
        current = rerun()[0]
    raise AssertionError("unreachable retry loop")  # pragma: no cover


def execute_file_fidelity_assessment(
    harness_factory: HarnessFactory,
    run_label: str,
    options: Mapping[str, object],
    case: CellCase,
) -> None:
    scenario = scenario_by_id(case.scenario_id)
    judge, judge_effort = assessment_cell(scenario.category, "file-fidelity-assessment")
    harness = harness_factory(judge)
    subjects = _load_subjects(
        load_producer_subjects,
        run_label,
        scenario=scenario,
        cells=[(case.agent, case.effort)],
    )
    from ..semantic import subjects_block_reason

    reason = subjects_block_reason(subjects)
    if reason is not None:
        raise CaseSkipped(reason)
    fresh, samples = _options(options)
    for subject in subjects:
        prompt = file_fidelity_prompt(scenario, subject.record)
        runs = harness.run_assessment(
            test_id=(
                f"task-guidance-file-fidelity-{scenario.scenario_id}-"
                f"{subject.profile}-{subject.effort}-s{subject.sample_index}"
            ),
            prompt=prompt,
            reasoning_effort=judge_effort,
            fresh=fresh,
            samples=samples,
        )
        for run in runs:
            judge_parsed, run = _parse_judge_response(
                run,
                parse_file_fidelity,
                lambda: harness.run_assessment(
                    test_id=(
                        f"task-guidance-file-fidelity-{scenario.scenario_id}-"
                        f"{subject.profile}-{subject.effort}-s{subject.sample_index}"
                    ),
                    prompt=prompt,
                    reasoning_effort=judge_effort,
                    fresh=True,
                ),
            )
            parsed = normalize_file_fidelity(
                judge_parsed,
                scenario=scenario,
            )
            validate_file_fidelity(parsed)
            record = file_fidelity_record(scenario, subject, parsed)
            run.record(STAGES["file-fidelity-assessment"].record, record)
            run.record(
                "task-guidance-file-fidelity-summary.md",
                "# Task-guidance file-fidelity assessment\n\n"
                f"- Scenario: `{scenario.scenario_id}`\n"
                f"- Subject: `{subject.profile}:{subject.effort}`"
                f" sample {subject.sample_index}\n"
                f"- Summary: `{record['summary']}`\n",
            )


def execute_file_readability_assessment(
    harness_factory: HarnessFactory,
    run_label: str,
    options: Mapping[str, object],
    case: CellCase,
) -> None:
    scenario = scenario_by_id(case.scenario_id)
    judge, judge_effort = assessment_cell(
        scenario.category, "file-readability-assessment"
    )
    harness = harness_factory(judge)
    subjects = _load_subjects(
        load_producer_subjects,
        run_label,
        scenario=scenario,
        cells=[(case.agent, case.effort)],
    )
    from ..semantic import subjects_block_reason

    reason = subjects_block_reason(subjects)
    if reason is not None:
        raise CaseSkipped(reason)
    fresh, samples = _options(options)
    for subject in subjects:
        prompt = file_readability_prompt(scenario, subject.record)
        runs = harness.run_assessment(
            test_id=(
                f"task-guidance-file-readability-{scenario.scenario_id}-"
                f"{subject.profile}-{subject.effort}-s{subject.sample_index}"
            ),
            prompt=prompt,
            reasoning_effort=judge_effort,
            fresh=fresh,
            samples=samples,
        )
        for run in runs:
            judge_parsed, run = _parse_judge_response(
                run,
                parse_file_readability,
                lambda: harness.run_assessment(
                    test_id=(
                        f"task-guidance-file-readability-{scenario.scenario_id}-"
                        f"{subject.profile}-{subject.effort}-s{subject.sample_index}"
                    ),
                    prompt=prompt,
                    reasoning_effort=judge_effort,
                    fresh=True,
                ),
            )
            parsed = normalize_file_readability(
                judge_parsed,
                scenario=scenario,
                record=subject.record,
            )
            validate_file_readability(parsed)
            record = file_readability_record(scenario, subject, parsed)
            run.record(STAGES["file-readability-assessment"].record, record)
            run.record(
                "task-guidance-file-readability-summary.md",
                "# Task-guidance file-readability assessment\n\n"
                f"- Scenario: `{scenario.scenario_id}`\n"
                f"- Subject: `{subject.profile}:{subject.effort}`"
                f" sample {subject.sample_index}\n"
                f"- Summary: `{record['summary']}`\n",
            )
