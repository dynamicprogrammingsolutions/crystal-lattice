from __future__ import annotations

import json

import pytest

from ..scenarios import scenario_by_id
from ..semantic import (
    SEMANTIC_SCHEMA_VERSION,
    aggregate_quality_metrics,
    normalize_semantic_assessment,
    parse_semantic_response,
    semantic_prompt,
    semantic_summary,
    validate_semantic_assessment,
)


SCENARIO = scenario_by_id("tg04-flask-vue-discovery-decomposition")


def _assessment(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "outcome_coverage": "complete",
        "missing_outcomes": [],
        "added_obligations": [],
        "semantic_deliverable_count": 2,
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
            "phase_only_children": {"status": "none", "score": 100, "occurrences": []},
            "layer_split_without_independent_value": {
                "status": "none",
                "score": 100,
                "occurrences": [],
            },
            "evidence_reownership": {"status": "none", "score": 100, "occurrences": []},
            "unsafe_dependencies": {"status": "none", "score": 100, "occurrences": []},
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
    value.update(overrides)
    return value


def _subject_record() -> dict[str, object]:
    return {
        "producer": {"profile": "glm", "reasoning_effort": "max"},
        "valid": True,
        "response": "produced the task set",
        "task_files": {
            "tasks/demo/000-main.md": "# Main\n",
            "tasks/demo/010-one.md": "# One\n",
            "tasks/demo/020-two.md": "# Two\n",
        },
        "task_tree": {"implementation_task_count": 2},
        "tool_metrics": {"total": 4},
    }


def test_parse_normalize_and_validate_one_subject_judgment() -> None:
    value = {
        "schema_version": SEMANTIC_SCHEMA_VERSION,
        "scenario_id": SCENARIO.scenario_id,
        "assessment": _assessment(),
    }

    parsed = parse_semantic_response("```json\n" + json.dumps(value) + "\n```")
    normalized = normalize_semantic_assessment(parsed, record=_subject_record())
    validate_semantic_assessment(normalized, scenario=SCENARIO)

    assessment = normalized["assessment"]
    assert assessment["actual_task_count"] == 2
    assert assessment["fragmentation_ratio"] == 1.0
    assert assessment["unmatched_tasks"] == []
    summary = semantic_summary(assessment)
    assert summary["partition_quality_score"] == 70
    assert summary["fragmentation_severity"] == "medium"
    assert summary["quality_dimensions"]["fragmentation"] == "medium"


def test_semantic_validation_rejects_a_mismatched_scenario() -> None:
    value = {
        "schema_version": SEMANTIC_SCHEMA_VERSION,
        "scenario_id": "not-the-scenario",
        "assessment": _assessment(),
    }

    with pytest.raises(ValueError, match="scenario_id"):
        validate_semantic_assessment(value, scenario=SCENARIO)


def test_semantic_validation_rejects_invalid_scores() -> None:
    value = {
        "schema_version": SEMANTIC_SCHEMA_VERSION,
        "scenario_id": SCENARIO.scenario_id,
        "assessment": _assessment(partition_quality_score=101),
    }

    with pytest.raises(ValueError, match="partition_quality_score"):
        validate_semantic_assessment(value, scenario=SCENARIO)


def test_semantic_prompt_material_is_the_produced_work_only() -> None:
    prompt = semantic_prompt(SCENARIO, _subject_record())

    assert "tasks/demo/010-one.md" in prompt
    assert "produced the task set" in prompt
    assert '"profile"' not in prompt
    assert '"tool_metrics"' not in prompt
    assert '"valid"' not in prompt


def test_quality_aggregation_groups_occurrences_and_scores() -> None:
    first = _assessment()
    second = _assessment()
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
    assessment = _assessment(
        crossing_ownership="partial",
        overall_success_percentage=72.2,
    )
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
    value = {
        "schema_version": SEMANTIC_SCHEMA_VERSION,
        "scenario_id": SCENARIO.scenario_id,
        "assessment": assessment,
    }

    validate_semantic_assessment(value, scenario=SCENARIO)
