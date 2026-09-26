from __future__ import annotations

from pathlib import Path
from typing import Any, Mapping, Sequence

from agent_eval.runner import (
    completeness,
    render_selection,
    select_cell_records,
)

from .configuration import (
    AGENTS,
    CATEGORIES,
    all_producer_cells,
    negative_control_designations,
    plan_variants,
    producer_cells,
)
from .handoff_semantic import handoff_assessment_subject_identity
from .scenarios import SCENARIOS
from .semantic import (
    QUALITY_DIMENSIONS,
    aggregate_quality_metrics,
    assessment_subject_identity,
    continuation_cell_identity,
    expected_producer_cells,
    handoff_cell_identity,
    producer_cell_identity,
    scenario_cell_identity,
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
    labels: Sequence[str] | None = None,
    dataset_id: str = "task-guidance-b0-20260919",
    label: str = "current-guidance baseline",
    bundle: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Freeze the consolidated records of one completed evaluation.

    Selection delegates to the consolidation core: without ``labels`` every
    cell contributes its latest run label; with ``labels`` every record of
    the listed labels becomes one sample of its cell. Expected sets derive
    from the configuration manifest and the scenario data.
    """

    producers = select_cell_records(
        artifact_root,
        record_name=STAGES["task-creation"].record,
        cell_identity=producer_cell_identity,
        labels=labels,
    )
    handoffs = select_cell_records(
        artifact_root,
        record_name=STAGES["handoff-plan"].record,
        cell_identity=handoff_cell_identity,
        labels=labels,
    )
    continuations = select_cell_records(
        artifact_root,
        record_name=STAGES["continuation"].record,
        cell_identity=continuation_cell_identity,
        labels=labels,
    )
    semantics = select_cell_records(
        artifact_root,
        record_name=STAGES["task-creation-assessment"].record,
        cell_identity=assessment_subject_identity,
        labels=labels,
    )
    handoff_semantics = select_cell_records(
        artifact_root,
        record_name=STAGES["handoff-assessment"].record,
        cell_identity=handoff_assessment_subject_identity,
        labels=labels,
    )
    negative_controls = select_cell_records(
        artifact_root,
        record_name=STAGES["negative-control"].record,
        cell_identity=scenario_cell_identity,
        labels=labels,
    )
    provider_cells = select_cell_records(
        artifact_root,
        record_name=STAGES["task-creation"].record,
        cell_identity=_provider_identity,
        labels=labels,
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
        f"{scenario.scenario_id}:{profile}:{effort}"
        for scenario in _scenarios_with_stage("task-creation-assessment")
        for profile, effort in producer_cells(scenario.category)
    }
    expected_handoff_semantics = {
        *(
            f"{scenario.scenario_id}:{variant}:{profile}:{effort}"
            for scenario in _scenarios_with_stage("handoff-assessment")
            for variant in plan_variants(scenario.category)
            for profile, effort in producer_cells(scenario.category)
        ),
        *(
            f"{scenario.scenario_id}:generated-task:{profile}:{effort}"
            for scenario in _scenarios_with_stage("handoff-assessment")
            if "continuation" in CATEGORIES[scenario.category]["stages"]
            for profile, effort in producer_cells(scenario.category)
        ),
        *(
            f"{control['scenario']}:{control['variant']}:"
            f"{control['agent']}:{control['effort']}"
            for control in negative_control_designations()
        ),
    }
    expected_negative_controls = {
        control["scenario"] for control in negative_control_designations()
    }

    producer_values = [
        {
            **record.value,
            "run_id": record.run_id,
            "task_tree": task_tree(record.value.get("task_files", {})),
        }
        for samples in producers.values()
        for record in samples
    ]
    handoff_values = _values(handoffs)
    continuation_values = _values(continuations)
    semantic_values = _values(semantics)
    handoff_semantic_values = _values(handoff_semantics)
    negative_control_values = _values(negative_controls)
    valid_provider_identities = {
        cell
        for cell, samples in provider_cells.items()
        if any(record.value.get("valid") is True for record in samples)
    }
    provider_blocker_values = [
        record.value
        for cell, samples in provider_cells.items()
        if cell not in valid_provider_identities
        for record in samples
        if record.value.get("valid") is False
        and any(
            "provider errors" in str(reason)
            for reason in record.value.get("invalid_reasons", ())
        )
    ]
    resolved_labels = sorted(
        {
            record.label
            for selected in (
                producers,
                handoffs,
                continuations,
                semantics,
                handoff_semantics,
                negative_controls,
            )
            for samples in selected.values()
            for record in samples
        }
    )
    return {
        "schema_version": 2,
        "dataset_id": dataset_id,
        "label": label,
        # The resolved labels of the selected records: the explicit selection
        # when one was given, otherwise the labels default selection picked.
        "labels": resolved_labels,
        "bundle": dict(bundle) if bundle is not None else None,
        "selection": render_selection(producers),
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
            "semantics": completeness(expected_semantics, semantics),
            "handoff_semantics": completeness(
                expected_handoff_semantics,
                handoff_semantics,
            ),
            "negative_controls": completeness(
                expected_negative_controls,
                negative_controls,
            ),
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
    labels = value.get("labels")
    attempts = value.get("attempts")
    lines = [
        f"# Task-guidance {value['label']} status",
        "",
    ]
    if labels:
        lines.append("- Labels: " + ", ".join(f"`{item}`" for item in labels))
    elif isinstance(attempts, Mapping):
        # Historical frozen datasets record per-stage attempts.
        lines.extend(
            [
                f"- Producer attempt: `{attempts['producer']}`",
                f"- Handoff attempt: `{attempts['handoff']}`",
                f"- Semantic attempt: `{attempts['semantic']}`",
            ]
        )
    else:
        lines.append("- Labels: latest per cell")
    lines.extend(
        [
            "",
            "| Stage | Expected | Present | Valid | Invalid | Missing |",
            "|---|---:|---:|---:|---:|---:|",
        ]
    )
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
                producer_cell_identity(record)
                if "variant" not in record
                else handoff_cell_identity(record)
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


def _values(cells: Mapping[str, tuple[Any, ...]]) -> list[dict[str, Any]]:
    """Record values with the exact run id of each sample.

    The run id lets the collector map every frozen record to the raw run
    that produced it, so multiple samples of one cell — repeated
    invocations under a label, ``--samples N``, or ``--fresh`` reruns —
    can never collapse onto another sample's run.
    """

    return [
        {**record.value, "run_id": record.run_id}
        for samples in cells.values()
        for record in samples
    ]


def _semantic_quality(
    semantic_records: list[dict[str, Any]],
) -> dict[str, Any]:
    """Cohort quality over the per-subject assessment records."""

    subjects = [
        (record.get("subject") or {}, record.get("assessment"))
        for record in semantic_records
        if isinstance(record.get("assessment"), dict)
    ]
    groups: dict[str, list[dict[str, Any]]] = {
        "all": [assessment for _, assessment in subjects],
    }
    for subject, assessment in subjects:
        profile = str(subject.get("profile"))
        effort = str(subject.get("reasoning_effort"))
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


def _provider_identity(value: dict[str, Any]) -> str:
    producer = value.get("producer") or {}
    return (
        f"{producer.get('profile')}:{producer.get('model')}:"
        f"{producer.get('reasoning_effort')}"
    )


def _status(
    expected: set[str],
    cells: Mapping[str, tuple[Any, ...]],
    *,
    valid_key: str,
) -> dict[str, Any]:
    """Cell-level status: the latest sample of each cell carries validity."""

    valid = 0
    invalid = 0
    for samples in cells.values():
        representative = max(
            samples,
            key=lambda record: (record.sample_index, record.modified),
        )
        if representative.value.get(valid_key) is True:
            valid += 1
        elif representative.value.get(valid_key) is False:
            invalid += 1
    return {
        "expected": len(expected),
        "present": len(cells),
        "valid": valid,
        "invalid": invalid,
        "missing": sorted(set(expected) - set(cells)),
    }
