"""Task-file quality assessment tests.

The quality assessment judges one produced subject per request: the prompt
material carries no producer identity, validity, or tool metrics; the
response schema carries a fixed grade per dimension; normalization rejects
unknown grades and scenario mismatches; and the saved record keeps the
subject-to-producer mapping.
"""

from __future__ import annotations

import pytest

from ..quality import (
    QUALITY_DIMENSIONS,
    aggregate_quality_dimensions,
    normalize_quality_assessment,
    parse_quality_response,
    quality_prompt,
    quality_record,
    quality_summary,
    validate_quality_assessment,
)
from ..scenarios import scenario_by_id
from ..semantic import ProducerSubject


SCENARIO = scenario_by_id("tg01-eleventy-archive-handoff")


def _producer_record(*, valid: bool = True) -> dict[str, object]:
    return {
        "scenario_id": SCENARIO.scenario_id,
        "producer": {"profile": "glm", "model": "model-x", "reasoning_effort": "max"},
        "valid": valid,
        "invalid_reasons": [] if valid else ["provider errors: provider limit"],
        "response": "assistant response alpha",
        "task_files": {"tasks/alpha.md": "# Task alpha\n"},
        "task_tree": {"implementation_task_count": 1},
        "tool_metrics": {"total": 4, "read": 4},
    }


def _subject(record: dict[str, object]) -> ProducerSubject:
    return ProducerSubject(
        scenario_id=SCENARIO.scenario_id,
        profile="glm",
        effort="max",
        sample_index=0,
        record=record,
    )


def _response(**grade_overrides: str) -> dict[str, object]:
    grades = {
        "plan_design_completeness": "complete",
        "durable_context_preservation": "partial",
        "findability": "complete",
        "section_appropriateness": "partial",
        "plan_justification": "justified",
        "task_kind_fit": "fits",
    }
    grades.update(grade_overrides)
    return {
        "schema_version": 1,
        "scenario_id": SCENARIO.scenario_id,
        "assessment": {
            "task_kind": "development",
            "dimensions": {
                name: {"grade": grade, "occurrences": []}
                for name, grade in grades.items()
            },
            "summary": "A concise judgment.",
        },
    }


def test_prompt_carries_no_producer_identity() -> None:
    prompt = quality_prompt(SCENARIO, _producer_record())

    assert "assistant response alpha" in prompt
    assert "tasks/alpha.md" in prompt
    for leaked in ("model-x", "tool_metrics", "invalid_reasons", '"valid"'):
        assert leaked not in prompt


def test_prompt_rejects_invalid_subjects() -> None:
    with pytest.raises(ValueError, match="valid subject"):
        quality_prompt(SCENARIO, _producer_record(valid=False))


def test_parse_tolerates_fenced_json() -> None:
    import json

    text = "```json\n" + json.dumps(_response()) + "\n```"
    assert parse_quality_response(text)["scenario_id"] == SCENARIO.scenario_id


def test_normalize_accepts_every_declared_grade() -> None:
    record = _producer_record()
    for name, grades in QUALITY_DIMENSIONS.items():
        for grade in grades:
            response = _response(**{name: grade})
            value = normalize_quality_assessment(response, record=record)
            assert value["dimensions"][name]["grade"] == grade
            validate_quality_assessment(value)


def test_normalize_rejects_unknown_grade() -> None:
    with pytest.raises(ValueError, match="plan_design_completeness"):
        normalize_quality_assessment(
            _response(plan_design_completeness="excellent"),
            record=_producer_record(),
        )


def test_normalize_rejects_scenario_mismatch() -> None:
    response = _response()
    response["scenario_id"] = "some-other-scenario"
    with pytest.raises(ValueError, match="does not match"):
        normalize_quality_assessment(response, record=_producer_record())


def test_quality_record_keeps_subject_mapping() -> None:
    record = _producer_record()
    value = normalize_quality_assessment(_response(), record=record)
    saved = quality_record(SCENARIO, _subject(record), value)

    assert saved["subject"] == {
        "profile": "glm",
        "reasoning_effort": "max",
        "sample_index": 0,
    }
    assert saved["scenario_id"] == SCENARIO.scenario_id
    assert "development" in quality_summary(saved["assessment"])


def test_aggregate_reports_grade_shares() -> None:
    record = _producer_record()
    first = normalize_quality_assessment(_response(), record=record)
    second = normalize_quality_assessment(_response(findability="poor"), record=record)
    aggregate = aggregate_quality_dimensions([first, second])

    assert aggregate["assessment_count"] == 2
    assert aggregate["dimensions"]["findability"]["grade_counts"] == {
        "complete": 1,
        "poor": 1,
    }
    assert aggregate["dimensions"]["plan_justification"]["top_grade_share"] == 1.0


def test_aggregate_handles_empty() -> None:
    assert aggregate_quality_dimensions([])["assessment_count"] == 0
