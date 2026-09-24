from __future__ import annotations

import json
from pathlib import Path

import pytest

from .scenarios import scenario_by_id
from .semantic import (
    aggregate_quality_metrics,
    expected_producer_cells,
    normalize_semantic_assessment,
    parse_semantic_response,
    producer_cells_from_records,
    semantic_summary,
    validate_semantic_assessment,
)


def _assessment(profile: str, effort: str) -> dict[str, object]:
    return {
        "producer": {"profile": profile, "reasoning_effort": effort},
        "outcome_coverage": "complete",
        "missing_outcomes": [],
        "added_obligations": [],
        "semantic_deliverable_count": 4,
        "actual_task_count": 8,
        "deliverable_mappings": [],
        "mergeable_groups": [],
        "unmatched_tasks": [],
        "overpacked_tasks": [],
        "valid_layer_boundaries": [],
        "automatic_layer_fragments": [],
        "dependency_issues": [],
        "crossing_ownership": "complete",
        "fragmentation_severity": "medium",
        "fragmentation_ratio": 2.0,
        "quality_metrics": {
            "fragmentation": {
                "status": "medium",
                "score": 33,
                "occurrences": [
                    {
                        "task_paths": ["tasks/010.md", "tasks/020.md"],
                        "description": "One delivery is split.",
                    }
                ],
            },
            "phase_only_children": {
                "status": "none",
                "score": 100,
                "occurrences": [],
            },
            "layer_split_without_independent_value": {
                "status": "none",
                "score": 100,
                "occurrences": [],
            },
            "evidence_reownership": {
                "status": "none",
                "score": 100,
                "occurrences": [],
            },
            "unsafe_dependencies": {
                "status": "none",
                "score": 100,
                "occurrences": [],
            },
            "piecewise_crossing_evidence": {
                "status": "none",
                "score": 100,
                "occurrences": [],
            },
        },
        "overall_success_percentage": 88.8,
        "partition_quality_score": 70,
        "handoff_quality_score": 80,
        "summary": "Complete but fragmented.",
    }


def test_parse_and_validate_semantic_assessment() -> None:
    scenario = scenario_by_id("tg04-flask-vue-discovery-decomposition")
    cells = expected_producer_cells(scenario)
    value = {
        "schema_version": 2,
        "scenario_id": scenario.scenario_id,
        "assessments": [_assessment(profile, effort) for profile, effort in cells],
    }

    parsed = parse_semantic_response("```json\n" + json.dumps(value) + "\n```")
    validate_semantic_assessment(
        parsed,
        scenario=scenario,
        expected_cells=cells,
    )

    summary = semantic_summary(parsed)
    assert summary["assessment_count"] == 4
    assert summary["fragmentation"] == {"medium": 4}
    assert summary["quality_metrics"]["overall_success_percentage"] == 88.8
    assert summary["quality_metrics"]["dimensions"]["fragmentation"] == {
        "average_score": 33.0,
        "affected_assessments": 4,
        "occurrence_count": 4,
        "status_counts": {"medium": 4},
    }
    assert summary["average_partition_quality"] == 70.0
    assert (
        producer_cells_from_records(
            [
                {
                    "producer": {
                        "profile": profile,
                        "reasoning_effort": effort,
                    }
                }
                for profile, effort in cells
            ]
        )
        == cells
    )


def test_semantic_normalization_excludes_coordinating_parent() -> None:
    value = {
        "assessments": [
            {
                **_assessment("glm", "max"),
                "actual_task_count": 3,
                "semantic_deliverable_count": 2,
                "unmatched_tasks": ["tasks/demo/000-main.md"],
            }
        ]
    }
    record = {
        "producer": {"profile": "glm", "reasoning_effort": "max"},
        "task_files": {
            "tasks/demo/000-main.md": "# Main\n",
            "tasks/demo/010-one.md": "# One\n",
            "tasks/demo/020-two.md": "# Two\n",
        },
    }

    normalized = normalize_semantic_assessment(value, records=[record])
    assessment = normalized["assessments"][0]

    assert assessment["actual_task_count"] == 2
    assert assessment["fragmentation_ratio"] == 1.0
    assert assessment["unmatched_tasks"] == []
    assert assessment["quality_metrics"]["fragmentation"]["score"] == 33
    assert assessment["overall_success_percentage"] == 88.8


def test_semantic_validation_rejects_missing_producer() -> None:
    scenario = scenario_by_id("tg01-eleventy-archive-handoff")
    value = {
        "schema_version": 2,
        "scenario_id": scenario.scenario_id,
        "assessments": [_assessment("glm", "max")],
    }

    with pytest.raises(ValueError, match="producers do not match"):
        validate_semantic_assessment(
            value,
            scenario=scenario,
            expected_cells=expected_producer_cells(scenario),
        )


def test_partial_producer_loading_is_explicit(tmp_path: Path) -> None:
    scenario = scenario_by_id("tg01-eleventy-archive-handoff")
    record = {
        "scenario_id": scenario.scenario_id,
        "run_attempt": "r1",
        "producer": {"profile": "glm", "reasoning_effort": "max"},
        "valid": True,
    }
    path = tmp_path / "glm" / "records" / "task-guidance-producer.json"
    path.parent.mkdir(parents=True)
    path.write_text(json.dumps(record), encoding="utf-8")

    from .semantic import load_producer_records

    with pytest.raises(FileNotFoundError):
        load_producer_records(
            tmp_path,
            scenario=scenario,
            run_attempt="r1",
        )
    loaded = load_producer_records(
        tmp_path,
        scenario=scenario,
        run_attempt="r1",
        allow_partial=True,
    )
    assert loaded == [record]


def test_quality_aggregation_groups_occurrences_and_scores() -> None:
    first = _assessment("glm", "max")
    second = _assessment("gpt", "high")
    second["quality_metrics"]["phase_only_children"] = {
        "status": "present",
        "score": 0,
        "occurrences": [
            {
                "task_paths": ["tasks/030-tests.md"],
                "description": "Tests are a phase-only child.",
            }
        ],
    }
    second["overall_success_percentage"] = 72.2

    value = aggregate_quality_metrics([first, second])

    assert value["assessment_count"] == 2
    assert value["overall_success_percentage"] == 80.5
    assert value["dimensions"]["phase_only_children"] == {
        "average_score": 50.0,
        "affected_assessments": 1,
        "occurrence_count": 1,
        "status_counts": {"none": 1, "present": 1},
    }


def test_partial_crossing_may_be_a_material_piecewise_issue() -> None:
    scenario = scenario_by_id("tg01-eleventy-archive-handoff")
    assessment = _assessment("glm", "max")
    assessment["crossing_ownership"] = "partial"
    assessment["quality_metrics"]["piecewise_crossing_evidence"] = {
        "status": "present",
        "score": 0,
        "occurrences": [
            {
                "task_paths": ["tasks/demo.md"],
                "description": "No check crosses the required production path.",
            }
        ],
    }
    assessment["overall_success_percentage"] = 72.2
    value = {
        "schema_version": 2,
        "scenario_id": scenario.scenario_id,
        "assessments": [assessment, _assessment("gpt", "high")],
    }

    validate_semantic_assessment(
        value,
        scenario=scenario,
        expected_cells=expected_producer_cells(scenario),
    )
