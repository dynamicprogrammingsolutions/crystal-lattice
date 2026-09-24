from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path
from string import Template
from typing import Any, Mapping, Sequence

from agent_eval.runner import select_cell_records

from .configuration import producer_cells
from .scenarios import TaskGuidanceScenario
from .stages import STAGES


SEMANTIC_SCHEMA_VERSION = 2
QUALITY_DIMENSIONS = (
    "fragmentation",
    "phase_only_children",
    "layer_split_without_independent_value",
    "evidence_reownership",
    "unsafe_dependencies",
    "piecewise_crossing_evidence",
)
FRAGMENTATION_SCORES = {
    "none": 100,
    "low": 67,
    "medium": 33,
    "high": 0,
}
ISSUE_SCORES = {
    "none": 100,
    "partial": 50,
    "present": 0,
}


def expected_producer_cells(
    scenario: TaskGuidanceScenario,
) -> tuple[tuple[str, str], ...]:
    return producer_cells(scenario.category)


def producer_cell_identity(value: Mapping[str, Any]) -> str:
    """The cell identity of one task-creation record."""

    producer = value.get("producer") or {}
    return (
        f"{value.get('scenario_id')}:{producer.get('profile')}:"
        f"{producer.get('reasoning_effort')}"
    )


def handoff_cell_identity(value: Mapping[str, Any]) -> str:
    """The cell identity of one handoff-plan or negative-control record."""

    producer = value.get("producer") or {}
    return (
        f"{value.get('scenario_id')}:{value.get('variant')}:"
        f"{producer.get('profile')}:{producer.get('reasoning_effort')}"
    )


def continuation_cell_identity(value: Mapping[str, Any]) -> str:
    """The cell identity of one continuation record."""

    producer = value.get("producer") or {}
    return (
        f"{value.get('scenario_id')}:{producer.get('profile')}:"
        f"{producer.get('reasoning_effort')}"
    )


def scenario_cell_identity(value: Mapping[str, Any]) -> str:
    """The cell identity of one assessment record (one per scenario)."""

    return str(value.get("scenario_id"))


def _latest_sample(samples: Sequence[Any]) -> Any:
    return max(samples, key=lambda record: (record.sample_index, record.modified))


def load_producer_records(
    artifact_root: Path,
    *,
    scenario: TaskGuidanceScenario,
    labels: Sequence[str] | None,
    allow_partial: bool = False,
) -> list[dict[str, Any]]:
    """The scenario's producer records under the given run labels.

    Selection delegates to the consolidation core; each cell contributes
    its latest sample. Without ``labels`` the latest label of each cell
    is selected.
    """

    cells = select_cell_records(
        artifact_root,
        record_name=STAGES["task-creation"].record,
        cell_identity=producer_cell_identity,
        labels=labels,
    )
    expected = [
        f"{scenario.scenario_id}:{agent}:{effort}"
        for agent, effort in expected_producer_cells(scenario)
    ]
    missing = [key for key in expected if key not in cells]
    if missing and not allow_partial:
        raise FileNotFoundError(
            f"missing producer records for {scenario.scenario_id}: {missing}"
        )
    return [_latest_sample(cells[key]).value for key in expected if key in cells]


# The fixed instruction part of the assessment prompt. Per-evaluation
# material is substituted into the $-placeholders; the template itself
# is extracted verbatim into the scenarios export.
TASK_CREATION_ASSESSMENT_PROMPT_TEMPLATE = Template(
    """\
Assess task-guidance behavior for one fixed scenario across several producer
profiles. Use the reviewed target, not raw task count, as the authority.

Judge whether each task set preserves approved outcomes and partitions work
into coherent deliverables. A technical layer is a valid separate task only
when completion leaves an independently usable, acceptable, deferable, owned,
or reviewable result. Identify subtasks that are merely phases or layer
fragments and could merge without losing independent value. Also identify
overpacked tasks that hide several independent deliverables.

The natural user request is part of the authority. Do not label behavior
explicitly requested there or listed in approved outcomes as added scope.
A coordinating parent file such as `000-main.md` is not an implementation
deliverable: exclude it from `actual_task_count`, fragmentation ratio, and
unmatched tasks unless it contains separately assigned implementation work.
For `crossing_ownership`, apply the target's exact `important_crossings`.
Separate mocked component tests and direct route/helper tests do not prove a
required production connection. Mark the crossing complete only when the task
names at least one check through that exact connection; otherwise mark it
partial or missing and explain the gap.

Do not reward verbosity, exact filenames, or matching the target's task count
mechanically. Do not penalize an acceptable alternative partition described by
the target. Treat tests, documentation, implementation, review, and deployment
as work within a deliverable unless their result is independently required.

Assess these issue dimensions separately:

- `fragmentation`: the overall mismatch between actual tasks and coherent
  deliverables;
- `phase_only_children`: implementation, testing, documentation, deployment,
  cleanup, or review children that only complete another delivery;
- `layer_split_without_independent_value`: frontend, backend, transport,
  storage, or package children that lack independent users, ownership,
  compatibility, acceptance, or a complete product outcome;
- `evidence_reownership`: a final integration, verification, or documentation
  child re-owning evidence that belongs with outcome-delivery children;
- `unsafe_dependencies`: missing, unnecessary, or wrong dependencies that
  permit a broken intermediate state or serialize independently deliverable
  work;
- `piecewise_crossing_evidence`: separate mocks, component checks, direct
  routes, or helper tests without one decisive check through the required
  production connection.

For fragmentation use `none|low|medium|high`. For every other dimension use
`none|partial|present`. `none` means the issue is absent, `partial` means a
limited or incomplete instance, and `present` means a material instance.
List concrete occurrences separately. Do not invent numeric scores; the
evaluator derives them deterministically from these statuses.

Return JSON only with this shape:

{
  "schema_version": 2,
  "scenario_id": "$scenario_id",
  "assessments": [
    {
      "producer": {"profile": "glm|gpt", "reasoning_effort": "..."},
      "outcome_coverage": "complete|partial|poor",
      "missing_outcomes": ["OUTCOME-ID"],
      "added_obligations": ["description"],
      "semantic_deliverable_count": 0,
      "actual_task_count": 0,
      "deliverable_mappings": [
        {
          "deliverable_id": "target id",
          "task_paths": ["tasks/..."],
          "coverage": "complete|partial|missing",
          "coherence": "coherent|fragmented|overpacked",
          "reason": "short evidence"
        }
      ],
      "mergeable_groups": [
        {"task_paths": ["tasks/..."], "reason": "why these are one deliverable"}
      ],
      "unmatched_tasks": ["tasks/..."],
      "overpacked_tasks": ["tasks/..."],
      "valid_layer_boundaries": ["tasks/..."],
      "automatic_layer_fragments": ["tasks/..."],
      "dependency_issues": ["description"],
      "crossing_ownership": "complete|partial|missing",
      "fragmentation_severity": "none|low|medium|high",
      "fragmentation_ratio": 0.0,
      "quality_metrics": {
        "fragmentation": {
          "status": "none|low|medium|high",
          "occurrences": [
            {
              "task_paths": ["tasks/..."],
              "description": "concrete occurrence"
            }
          ]
        },
        "phase_only_children": {
          "status": "none|partial|present",
          "occurrences": []
        },
        "layer_split_without_independent_value": {
          "status": "none|partial|present",
          "occurrences": []
        },
        "evidence_reownership": {
          "status": "none|partial|present",
          "occurrences": []
        },
        "unsafe_dependencies": {
          "status": "none|partial|present",
          "occurrences": []
        },
        "piecewise_crossing_evidence": {
          "status": "none|partial|present",
          "occurrences": []
        }
      },
      "partition_quality_score": 0,
      "handoff_quality_score": 0,
      "summary": "concise evidence-based interpretation"
    }
  ]
}

Scores are integers from 0 through 100. `fragmentation_ratio` is actual task
files divided by the semantic coherent-deliverable count, or 0 when no
deliverable exists; it is descriptive rather than decisive.

Reviewed target:

$target_json

Natural user request:

$prompt

Producer records:

$records_json
"""
)


def semantic_prompt(
    scenario: TaskGuidanceScenario,
    records: list[dict[str, Any]],
) -> str:
    invalid = [record for record in records if record.get("valid") is not True]
    if invalid:
        raise ValueError("semantic prompt accepts only valid producer records")
    compact_records = [
        {
            "producer": record["producer"],
            "valid": record["valid"],
            "invalid_reasons": record["invalid_reasons"],
            "response": record["response"],
            "task_files": record["task_files"],
            "task_tree": record["task_tree"],
            "tool_metrics": record["tool_metrics"],
        }
        for record in records
    ]
    return TASK_CREATION_ASSESSMENT_PROMPT_TEMPLATE.substitute(
        scenario_id=scenario.scenario_id,
        target_json=json.dumps(scenario.target, indent=2, sort_keys=True),
        prompt=scenario.prompt,
        records_json=json.dumps(compact_records, indent=2, sort_keys=True),
    )


def producer_cells_from_records(
    records: list[dict[str, Any]],
) -> tuple[tuple[str, str], ...]:
    values: list[tuple[str, str]] = []
    for record in records:
        producer = record.get("producer")
        if not isinstance(producer, dict):
            raise ValueError("producer record has no producer object")
        profile = producer.get("profile")
        effort = producer.get("reasoning_effort")
        if not isinstance(profile, str) or not isinstance(effort, str):
            raise ValueError("producer identity is incomplete")
        values.append((profile, effort))
    return tuple(values)


def normalize_semantic_assessment(
    value: dict[str, Any],
    *,
    records: list[dict[str, Any]],
) -> dict[str, Any]:
    by_identity = {
        (
            str(record["producer"]["profile"]),
            str(record["producer"]["reasoning_effort"]),
        ): record
        for record in records
    }
    assessments = value.get("assessments")
    if not isinstance(assessments, list):
        return value
    for assessment in assessments:
        if not isinstance(assessment, dict):
            continue
        producer = assessment.get("producer")
        if not isinstance(producer, dict):
            continue
        identity = (
            str(producer.get("profile")),
            str(producer.get("reasoning_effort")),
        )
        record = by_identity.get(identity)
        if record is None:
            continue
        from .topology import task_tree

        tree = task_tree(record["task_files"])
        implementation_count = int(tree["implementation_task_count"])
        assessment["actual_task_count"] = implementation_count
        coordinating = set(tree["coordinating_files"])
        unmatched = assessment.get("unmatched_tasks")
        if isinstance(unmatched, list):
            assessment["unmatched_tasks"] = [
                path for path in unmatched if path not in coordinating
            ]
        semantic_count = assessment.get("semantic_deliverable_count")
        if isinstance(semantic_count, int) and semantic_count > 0:
            assessment["fragmentation_ratio"] = round(
                implementation_count / semantic_count,
                3,
            )
        else:
            assessment["fragmentation_ratio"] = 0.0
        _normalize_quality_metrics(assessment)
    return value


def parse_semantic_response(text: str) -> dict[str, Any]:
    stripped = text.strip()
    fenced = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```",
        stripped,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if fenced is not None:
        stripped = fenced.group(1)
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start < 0 or end <= start:
            raise
        value = json.loads(stripped[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("semantic response must be an object")
    return value


def validate_semantic_assessment(
    value: Mapping[str, Any],
    *,
    scenario: TaskGuidanceScenario,
    expected_cells: tuple[tuple[str, str], ...],
) -> None:
    if value.get("schema_version") != SEMANTIC_SCHEMA_VERSION:
        raise ValueError(f"semantic schema_version must be {SEMANTIC_SCHEMA_VERSION}")
    if value.get("scenario_id") != scenario.scenario_id:
        raise ValueError("semantic scenario_id does not match")
    assessments = value.get("assessments")
    if not isinstance(assessments, list):
        raise ValueError("semantic assessments must be a list")
    observed: set[tuple[str, str]] = set()
    for assessment in assessments:
        if not isinstance(assessment, dict):
            raise ValueError("semantic assessment entry must be an object")
        producer = assessment.get("producer")
        if not isinstance(producer, dict):
            raise ValueError("semantic producer must be an object")
        key = (
            str(producer.get("profile")),
            str(producer.get("reasoning_effort")),
        )
        if key in observed:
            raise ValueError(f"duplicate semantic producer: {key}")
        observed.add(key)
        _choice(
            assessment,
            "outcome_coverage",
            {"complete", "partial", "poor"},
        )
        _choice(
            assessment,
            "crossing_ownership",
            {"complete", "partial", "missing"},
        )
        _choice(
            assessment,
            "fragmentation_severity",
            {"none", "low", "medium", "high"},
        )
        _validate_quality_metrics(assessment)
        for key_name in (
            "missing_outcomes",
            "added_obligations",
            "deliverable_mappings",
            "mergeable_groups",
            "unmatched_tasks",
            "overpacked_tasks",
            "valid_layer_boundaries",
            "automatic_layer_fragments",
            "dependency_issues",
        ):
            if not isinstance(assessment.get(key_name), list):
                raise ValueError(f"semantic {key_name} must be a list")
        for score_name in (
            "partition_quality_score",
            "handoff_quality_score",
        ):
            score = assessment.get(score_name)
            if not isinstance(score, int) or not 0 <= score <= 100:
                raise ValueError(f"semantic {score_name} must be 0..100")
        ratio = assessment.get("fragmentation_ratio")
        if not isinstance(ratio, (int, float)) or ratio < 0:
            raise ValueError("fragmentation_ratio must be non-negative")
        for count_name in (
            "semantic_deliverable_count",
            "actual_task_count",
        ):
            count = assessment.get(count_name)
            if not isinstance(count, int) or count < 0:
                raise ValueError(f"semantic {count_name} must be non-negative")
        if not isinstance(assessment.get("summary"), str):
            raise ValueError("semantic summary must be a string")
    if observed != set(expected_cells):
        raise ValueError(
            f"semantic producers do not match: {observed!r} != "
            f"{set(expected_cells)!r}"
        )


def semantic_summary(value: Mapping[str, Any]) -> dict[str, Any]:
    assessments = value["assessments"]
    assert isinstance(assessments, list)
    severities = Counter(str(item["fragmentation_severity"]) for item in assessments)
    coverage = Counter(str(item["outcome_coverage"]) for item in assessments)
    return {
        "assessment_count": len(assessments),
        "coverage": dict(coverage),
        "fragmentation": dict(severities),
        "quality_metrics": aggregate_quality_metrics(assessments),
        "average_partition_quality": round(
            sum(int(item["partition_quality_score"]) for item in assessments)
            / len(assessments),
            1,
        ),
        "average_handoff_quality": round(
            sum(int(item["handoff_quality_score"]) for item in assessments)
            / len(assessments),
            1,
        ),
    }


def aggregate_quality_metrics(
    assessments: list[Mapping[str, Any]],
) -> dict[str, Any]:
    if not assessments:
        return {
            "assessment_count": 0,
            "overall_success_percentage": 0.0,
            "dimensions": {},
        }
    dimensions: dict[str, Any] = {}
    for name in QUALITY_DIMENSIONS:
        metrics = [assessment["quality_metrics"][name] for assessment in assessments]
        status_counts = Counter(str(metric["status"]) for metric in metrics)
        dimensions[name] = {
            "average_score": round(
                sum(int(metric["score"]) for metric in metrics) / len(metrics),
                1,
            ),
            "affected_assessments": sum(
                1 for metric in metrics if metric["status"] != "none"
            ),
            "occurrence_count": sum(len(metric["occurrences"]) for metric in metrics),
            "status_counts": dict(status_counts),
        }
    return {
        "assessment_count": len(assessments),
        "overall_success_percentage": round(
            sum(
                float(assessment["overall_success_percentage"])
                for assessment in assessments
            )
            / len(assessments),
            1,
        ),
        "dimensions": dimensions,
    }


def _normalize_quality_metrics(assessment: dict[str, Any]) -> None:
    values = assessment.get("quality_metrics")
    if not isinstance(values, dict):
        return
    scores: list[int] = []
    for name in QUALITY_DIMENSIONS:
        metric = values.get(name)
        if not isinstance(metric, dict):
            continue
        status = metric.get("status")
        mapping = FRAGMENTATION_SCORES if name == "fragmentation" else ISSUE_SCORES
        if status in mapping:
            metric["score"] = mapping[str(status)]
            scores.append(metric["score"])
    if len(scores) == len(QUALITY_DIMENSIONS):
        assessment["overall_success_percentage"] = round(
            sum(scores) / len(scores),
            1,
        )


def _validate_quality_metrics(assessment: Mapping[str, Any]) -> None:
    values = assessment.get("quality_metrics")
    if not isinstance(values, Mapping):
        raise ValueError("semantic quality_metrics must be an object")
    if set(values) != set(QUALITY_DIMENSIONS):
        raise ValueError(
            "semantic quality_metrics dimensions must be "
            f"{sorted(QUALITY_DIMENSIONS)!r}"
        )
    for name in QUALITY_DIMENSIONS:
        metric = values[name]
        if not isinstance(metric, Mapping):
            raise ValueError(f"semantic quality metric {name} must be an object")
        scores = FRAGMENTATION_SCORES if name == "fragmentation" else ISSUE_SCORES
        status = metric.get("status")
        if status not in scores:
            raise ValueError(
                f"semantic quality metric {name} status must be one of "
                f"{sorted(scores)!r}"
            )
        expected_score = scores[str(status)]
        if metric.get("score") != expected_score:
            raise ValueError(
                f"semantic quality metric {name} score must be " f"{expected_score}"
            )
        occurrences = metric.get("occurrences")
        if not isinstance(occurrences, list):
            raise ValueError(
                f"semantic quality metric {name} occurrences must be a list"
            )
        for occurrence in occurrences:
            if not isinstance(occurrence, Mapping):
                raise ValueError(
                    f"semantic quality metric {name} occurrence must be an object"
                )
            paths = occurrence.get("task_paths")
            if not isinstance(paths, list) or not all(
                isinstance(path, str) for path in paths
            ):
                raise ValueError(
                    f"semantic quality metric {name} task_paths must be strings"
                )
            if not isinstance(occurrence.get("description"), str):
                raise ValueError(
                    f"semantic quality metric {name} description must be text"
                )
    if values["fragmentation"]["status"] != assessment["fragmentation_severity"]:
        raise ValueError(
            "semantic fragmentation metric must match fragmentation_severity"
        )
    expected_overall = round(
        sum(int(values[name]["score"]) for name in QUALITY_DIMENSIONS)
        / len(QUALITY_DIMENSIONS),
        1,
    )
    if assessment.get("overall_success_percentage") != expected_overall:
        raise ValueError(
            "semantic overall_success_percentage must be " f"{expected_overall}"
        )


def _choice(
    value: Mapping[str, Any],
    key: str,
    choices: set[str],
) -> None:
    selected = value.get(key)
    if selected not in choices:
        raise ValueError(f"semantic {key} must be one of {sorted(choices)}")
