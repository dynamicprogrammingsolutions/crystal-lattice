from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .artifacts import record_paths
from .configuration import (
    AGENTS,
    CATEGORIES,
    all_producer_cells,
    negative_control_designations,
    plan_variants,
    producer_cells,
)
from .scenarios import SCENARIOS
from .semantic import (
    QUALITY_DIMENSIONS,
    aggregate_quality_metrics,
    expected_producer_cells,
)
from .stages import STAGES
from .topology import task_tree


def _scenarios_with_stage(stage: str) -> list:
    """The scenarios whose category declares one stage."""

    return [
        scenario
        for scenario in SCENARIOS
        if stage in CATEGORIES[scenario.category]["stages"]
    ]


def consolidate_results(
    artifact_root: Path,
    *,
    producer_attempt: str,
    handoff_attempt: str,
    semantic_attempt: str,
    dataset_id: str = "task-guidance-b0-20260919",
    label: str = "current-guidance baseline",
) -> dict[str, Any]:
    producers = _latest_records(
        artifact_root,
        record_name=STAGES["task-creation"].record,
        identity=_producer_identity,
        predicate=lambda value: value.get("run_attempt") == producer_attempt,
    )
    handoffs = _latest_records(
        artifact_root,
        record_name=STAGES["handoff-plan"].record,
        identity=_handoff_identity,
        predicate=lambda value: value.get("run_attempt") == handoff_attempt,
    )
    continuations = _latest_records(
        artifact_root,
        record_name=STAGES["continuation"].record,
        identity=_continuation_identity,
        predicate=lambda value: value.get("run_attempt") == producer_attempt,
    )
    semantics = _latest_records(
        artifact_root,
        record_name=STAGES["task-creation-assessment"].record,
        identity=lambda value: str(value.get("scenario_id")),
        predicate=lambda value: (
            value.get("producer_attempt") == producer_attempt
            and value.get("semantic_attempt") == semantic_attempt
        ),
    )
    handoff_semantics = _latest_records(
        artifact_root,
        record_name=STAGES["handoff-assessment"].record,
        identity=lambda value: str(value.get("scenario_id")),
        predicate=lambda value: (
            value.get("producer_attempt") == producer_attempt
            and value.get("handoff_attempt") == handoff_attempt
            and value.get("semantic_attempt") == semantic_attempt
        ),
    )
    negative_controls = _latest_records(
        artifact_root,
        record_name=STAGES["negative-control"].record,
        identity=lambda value: str(value.get("scenario_id")),
        predicate=lambda value: value.get("run_attempt") == handoff_attempt,
    )
    provider_blockers = _latest_records(
        artifact_root,
        record_name=STAGES["task-creation"].record,
        identity=_provider_identity,
        predicate=lambda value: (
            value.get("valid") is False
            and any(
                "provider errors" in str(reason)
                for reason in value.get("invalid_reasons", ())
            )
        ),
    )

    expected_producers = {
        f"{scenario.scenario_id}:{profile}:{effort}"
        for scenario in SCENARIOS
        for profile, effort in expected_producer_cells(scenario)
    }
    expected_handoffs = {
        f"{scenario.scenario_id}:{variant}:{profile}:{effort}"
        for scenario in _scenarios_with_stage("handoff-plan")
        for variant in plan_variants(scenario.category)
        for profile, effort in producer_cells(scenario.category)
    }
    expected_continuations = {
        f"{scenario.scenario_id}:{profile}:{effort}"
        for scenario in _scenarios_with_stage("continuation")
        for profile, effort in producer_cells(scenario.category)
    }
    expected_semantics = {
        scenario.scenario_id
        for scenario in _scenarios_with_stage("task-creation-assessment")
    }
    expected_handoff_semantics = {
        scenario.scenario_id for scenario in _scenarios_with_stage("handoff-assessment")
    }
    expected_negative_controls = {
        control["scenario"] for control in negative_control_designations()
    }
    producer_values = [
        {
            **record,
            "task_tree": task_tree(record.get("task_files", {})),
        }
        for record in producers.values()
    ]
    handoff_values = list(handoffs.values())
    continuation_values = list(continuations.values())
    semantic_values = list(semantics.values())
    handoff_semantic_values = list(handoff_semantics.values())
    negative_control_values = list(negative_controls.values())
    valid_provider_identities = {
        _provider_identity(record)
        for record in producer_values
        if record.get("valid") is True
    }
    provider_blocker_values = [
        record
        for identity, record in provider_blockers.items()
        if identity not in valid_provider_identities
    ]
    return {
        "schema_version": 1,
        "dataset_id": dataset_id,
        "label": label,
        "attempts": {
            "producer": producer_attempt,
            "handoff": handoff_attempt,
            "semantic": semantic_attempt,
        },
        "producer_records": producer_values,
        "handoff_records": handoff_values,
        "same_agent_records": continuation_values,
        "semantic_records": semantic_values,
        "semantic_quality": _semantic_quality(semantic_values),
        "handoff_semantic_records": handoff_semantic_values,
        "negative_control_records": negative_control_values,
        "provider_blocker_records": provider_blocker_values,
        "status": {
            "producers": _status(
                expected_producers,
                producers,
                valid_key="valid",
            ),
            "handoffs": _status(
                expected_handoffs,
                handoffs,
                valid_key="valid",
            ),
            "same_agent": _status(
                expected_continuations,
                continuations,
                valid_key="valid",
            ),
            "semantics": {
                "expected": len(expected_semantics),
                "present": len(semantics),
                "missing": sorted(expected_semantics - set(semantics)),
            },
            "handoff_semantics": {
                "expected": len(expected_handoff_semantics),
                "present": len(handoff_semantics),
                "missing": sorted(expected_handoff_semantics - set(handoff_semantics)),
            },
            "negative_controls": {
                "expected": len(expected_negative_controls),
                "present": len(negative_controls),
                "missing": sorted(expected_negative_controls - set(negative_controls)),
            },
            "provider_blockers": {
                "present": len(provider_blocker_values),
                "identities": sorted(
                    _provider_identity(record) for record in provider_blocker_values
                ),
            },
        },
    }


def render_summary(value: dict[str, Any]) -> str:
    status = value["status"]
    lines = [
        f"# Task-guidance {value['label']} status",
        "",
        f"- Producer attempt: `{value['attempts']['producer']}`",
        f"- Handoff attempt: `{value['attempts']['handoff']}`",
        f"- Semantic attempt: `{value['attempts']['semantic']}`",
        "",
        "| Stage | Expected | Present | Valid | Invalid | Missing |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for key, title in (
        ("producers", "Task creation"),
        ("handoffs", "Fresh-agent planning"),
        ("same_agent", "Same-agent planning"),
    ):
        item = status[key]
        lines.append(
            f"| {title} | {item['expected']} | {item['present']} | "
            f"{item['valid']} | {item['invalid']} | {len(item['missing'])} |"
        )
    semantics = status["semantics"]
    lines.append(
        f"| Semantic batches | {semantics['expected']} | "
        f"{semantics['present']} | — | — | {len(semantics['missing'])} |"
    )
    handoff_semantics = status["handoff_semantics"]
    lines.append(
        f"| Handoff semantic batches | {handoff_semantics['expected']} | "
        f"{handoff_semantics['present']} | — | — | "
        f"{len(handoff_semantics['missing'])} |"
    )
    negative_controls = status["negative_controls"]
    lines.append(
        f"| Negative controls | {negative_controls['expected']} | "
        f"{negative_controls['present']} | — | — | "
        f"{len(negative_controls['missing'])} |"
    )
    provider_blockers = status["provider_blockers"]
    lines.append(
        f"| Provider setup blockers | — | {provider_blockers['present']} | "
        "— | — | — |"
    )
    invalid = [
        record
        for group in (
            value["producer_records"],
            value["handoff_records"],
            value["same_agent_records"],
        )
        for record in group
        if record.get("valid") is False
    ]
    if invalid:
        lines.extend(["", "## Invalid records", ""])
        for record in invalid:
            identity = (
                _producer_identity(record)
                if "variant" not in record
                else _handoff_identity(record)
            )
            lines.append(
                f"- `{identity}`: "
                + "; ".join(str(item) for item in record["invalid_reasons"])
            )
    if value["provider_blocker_records"]:
        lines.extend(["", "## Provider setup blockers", ""])
        for record in value["provider_blocker_records"]:
            lines.append(
                f"- `{_provider_identity(record)}`: "
                + "; ".join(str(item) for item in record["invalid_reasons"])
            )
    quality = value.get("semantic_quality", {})
    cohorts = quality.get("cohorts", {})
    if cohorts:
        lines.extend(
            [
                "",
                "## Task-creation semantic quality",
                "",
                "| Cohort | Assessments | Overall success | "
                + " | ".join(_quality_title(name) for name in QUALITY_DIMENSIONS)
                + " |",
                "|---|---:|---:|" + "---:|" * len(QUALITY_DIMENSIONS),
            ]
        )
        for name in (
            "all",
            *AGENTS,
            *(f"{agent}:{effort}" for agent, effort in all_producer_cells()),
        ):
            cohort = cohorts.get(name)
            if not cohort:
                continue
            dimensions = cohort["dimensions"]
            lines.append(
                f"| {_cohort_title(name)} | {cohort['assessment_count']} | "
                f"{cohort['overall_success_percentage']:.1f}% | "
                + " | ".join(
                    f"{dimensions[dimension]['average_score']:.1f}%"
                    for dimension in QUALITY_DIMENSIONS
                )
                + " |"
            )
    return "\n".join(lines).rstrip() + "\n"


def _semantic_quality(
    semantic_records: list[dict[str, Any]],
) -> dict[str, Any]:
    assessments = [
        assessment
        for record in semantic_records
        for assessment in record.get("assessment", {}).get("assessments", ())
        if isinstance(assessment, dict)
    ]
    groups: dict[str, list[dict[str, Any]]] = {
        "all": assessments,
    }
    for assessment in assessments:
        producer = assessment.get("producer", {})
        profile = str(producer.get("profile"))
        effort = str(producer.get("reasoning_effort"))
        groups.setdefault(profile, []).append(assessment)
        groups.setdefault(f"{profile}:{effort}", []).append(assessment)
    return {
        "cohorts": {
            name: aggregate_quality_metrics(items)
            for name, items in groups.items()
            if items
        }
    }


def _quality_title(name: str) -> str:
    return {
        "fragmentation": "Fragmentation",
        "phase_only_children": "Phase-only",
        "layer_split_without_independent_value": "Layer split",
        "evidence_reownership": "Evidence reownership",
        "unsafe_dependencies": "Dependency safety",
        "piecewise_crossing_evidence": "Production crossing",
    }[name]


def _cohort_title(name: str) -> str:
    if name == "all":
        return "All"
    if ":" in name:
        agent, effort = name.split(":", 1)
        return f"{agent.upper()} {effort}"
    return name.upper()


def _latest_records(
    artifact_root: Path,
    *,
    record_name: str,
    identity,
    predicate,
) -> dict[str, dict[str, Any]]:
    selected: dict[str, tuple[float, dict[str, Any]]] = {}
    for path in record_paths(artifact_root, record_name):
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        if not isinstance(value, dict) or not predicate(value):
            continue
        key = identity(value)
        modified = path.stat().st_mtime
        if key not in selected or modified > selected[key][0]:
            selected[key] = (modified, value)
    return {key: item[1] for key, item in selected.items()}


def _producer_identity(value: dict[str, Any]) -> str:
    producer = value.get("producer") or {}
    return (
        f"{value.get('scenario_id')}:{producer.get('profile')}:"
        f"{producer.get('reasoning_effort')}"
    )


def _handoff_identity(value: dict[str, Any]) -> str:
    producer = value.get("producer") or {}
    return (
        f"{value.get('scenario_id')}:{value.get('variant')}:"
        f"{producer.get('profile')}:{producer.get('reasoning_effort')}"
    )


def _continuation_identity(value: dict[str, Any]) -> str:
    producer = value.get("producer") or {}
    return (
        f"{value.get('scenario_id')}:{producer.get('profile')}:"
        f"{producer.get('reasoning_effort')}"
    )


def _provider_identity(value: dict[str, Any]) -> str:
    producer = value.get("producer") or {}
    return (
        f"{producer.get('profile')}:{producer.get('model')}:"
        f"{producer.get('reasoning_effort')}"
    )


def _status(
    expected: set[str],
    observed: dict[str, dict[str, Any]],
    *,
    valid_key: str,
) -> dict[str, Any]:
    valid = sum(record.get(valid_key) is True for record in observed.values())
    invalid = sum(record.get(valid_key) is False for record in observed.values())
    return {
        "expected": len(expected),
        "present": len(observed),
        "valid": valid,
        "invalid": invalid,
        "missing": sorted(expected - set(observed)),
    }
