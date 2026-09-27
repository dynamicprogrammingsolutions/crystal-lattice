"""Presented-plan content assessment tests.

The plan-content assessment judges one presented plan per request: the
prompt embeds the plan and both requirement layers as rendered text —
no producer identity, validity, tool metrics, or variant labels, and no
JSON map of the subject; the response schema grades every declared
requirement exactly once; non-top grades require a named finding; and
the saved record keeps the subject-to-producer mapping with the
stage/variant labels.
"""

from __future__ import annotations

import json

import pytest

from ..handoff_semantic import HandoffSubject
from ..plan_content import (
    GENERIC_PLAN_GRADES,
    GENERIC_PLAN_REQUIREMENTS,
    aggregate_plan_content,
    expected_plan_requirement_ids,
    normalize_plan_content_assessment,
    parse_plan_content_response,
    plan_content_prompt,
    plan_content_record,
    requirement_grades,
    validate_plan_content_assessment,
)
from ..scenarios import scenario_by_id


SCENARIO = scenario_by_id("tg01-eleventy-archive-handoff")
OTHER = scenario_by_id("tg02-fastapi-pagination-handoff")

PLAN_TEXT = (
    "# Implementation plan\n\n"
    "We paginate the blog archive with `/blog/` as page one and\n"
    "`/blog/page/2/` as the recommended — not yet approved — later-page\n"
    "pattern.\n"
)


def _subject_record(*, valid: bool = True) -> dict[str, object]:
    return {
        "scenario_id": SCENARIO.scenario_id,
        "producer": {"profile": "glm", "model": "model-x", "reasoning_effort": "max"},
        "valid": valid,
        "invalid_reasons": [] if valid else ["provider errors: provider limit"],
        "response": PLAN_TEXT,
        "task_files": {"tasks/alpha.md": "# Task alpha\n"},
        "tool_metrics": {"total": 4, "read": 4},
    }


def _handoff_subject(record: dict[str, object]) -> HandoffSubject:
    return HandoffSubject(
        scenario_id=SCENARIO.scenario_id,
        stage="fresh-agent",
        variant="retain",
        profile="glm",
        effort="max",
        sample_index=0,
        record=record,
    )


def _response(
    *,
    scenario_id: str | None = None,
    grades: dict[str, tuple[str, str]] | None = None,
) -> dict[str, object]:
    scenario = scenario_id or SCENARIO.scenario_id
    resolved = {
        requirement_id: ("conveyed", "")
        for requirement_id in expected_plan_requirement_ids(SCENARIO)
    }
    resolved["GENERIC-9"] = ("self-contained", "")
    resolved["GENERIC-10"] = ("proportionate", "")
    if grades:
        for requirement_id, (grade, finding) in grades.items():
            resolved[requirement_id] = (grade, finding)
    return {
        "schema_version": 1,
        "scenario_id": scenario,
        "assessment": {
            "requirements": {
                requirement_id: {"grade": grade, "finding": finding}
                for requirement_id, (grade, finding) in resolved.items()
            },
            "missed_requirements": [],
            "summary": "A concise judgment.",
        },
    }


def test_expected_requirement_ids_join_both_layers() -> None:
    expected = expected_plan_requirement_ids(SCENARIO)

    assert expected[:7] == tuple(f"PLAN-{index}" for index in range(1, 8))
    assert expected[7:] == tuple(f"GENERIC-{index}" for index in range(1, 11))
    assert len(set(expected)) == len(expected)
    scales = requirement_grades(SCENARIO)
    assert scales["PLAN-1"] == ("conveyed", "partial", "missing")
    assert scales["GENERIC-9"] == ("self-contained", "partial", "external-dependency")
    assert scales["GENERIC-10"] == ("proportionate", "over-detailed")


def test_generic_requirements_have_unique_ids_and_scales() -> None:
    ids = [requirement["id"] for requirement in GENERIC_PLAN_REQUIREMENTS]

    assert len(ids) == len(set(ids)) == 10
    for requirement in GENERIC_PLAN_REQUIREMENTS:
        assert requirement["requirement"].strip()
        assert len(requirement["grades"]) >= 2
        assert tuple(requirement["grades"]) == GENERIC_PLAN_GRADES[requirement["id"]]


def test_prompt_embeds_text_and_requirements_without_identity() -> None:
    prompt = plan_content_prompt(SCENARIO, _subject_record())

    assert PLAN_TEXT in prompt
    assert "GENERIC-9" in prompt and "GENERIC-10" in prompt
    assert "PLAN-1" in prompt and "ARCHIVE-1" in prompt
    # Rendered text, not JSON maps of the target or subject.
    assert '"plan_target"' not in prompt
    assert '"task_files"' not in prompt
    assert '"response"' not in prompt
    for leaked in ("model-x", "tool_metrics", "invalid_reasons", '"retain"'):
        assert leaked not in prompt


def test_prompt_rejects_invalid_subjects() -> None:
    with pytest.raises(ValueError, match="valid subject"):
        plan_content_prompt(SCENARIO, _subject_record(valid=False))


def test_parse_tolerates_fenced_json() -> None:
    text = "```json\n" + json.dumps(_response()) + "\n```"
    assert parse_plan_content_response(text)["scenario_id"] == SCENARIO.scenario_id


def test_normalize_accepts_top_grades_without_findings() -> None:
    value = normalize_plan_content_assessment(_response(), scenario=SCENARIO)

    validate_plan_content_assessment(value, scenario=SCENARIO)
    assert value["requirements"]["PLAN-1"]["grade"] == "conveyed"
    assert value["requirements"]["GENERIC-9"]["grade"] == "self-contained"


def test_normalize_accepts_declared_non_top_grades_with_findings() -> None:
    value = normalize_plan_content_assessment(
        _response(
            grades={
                "PLAN-2": ("partial", "cap mechanism named, exactly-once unstated"),
                "GENERIC-9": ("external-dependency", "contract only in linked file"),
                "GENERIC-10": ("over-detailed", "lists every validation rule"),
            }
        ),
        scenario=SCENARIO,
    )

    validate_plan_content_assessment(value, scenario=SCENARIO)
    assert value["requirements"]["GENERIC-9"]["grade"] == "external-dependency"


def test_normalize_rejects_missing_requirement() -> None:
    response = _response()
    del response["assessment"]["requirements"]["PLAN-4"]
    with pytest.raises(ValueError, match="missing=\\['PLAN-4'\\]"):
        normalize_plan_content_assessment(response, scenario=SCENARIO)


def test_normalize_rejects_unknown_requirement() -> None:
    response = _response()
    response["assessment"]["requirements"]["PLAN-99"] = {
        "grade": "conveyed",
        "finding": "",
    }
    with pytest.raises(ValueError, match="unexpected=\\['PLAN-99'\\]"):
        normalize_plan_content_assessment(response, scenario=SCENARIO)


def test_normalize_rejects_grade_outside_scale() -> None:
    with pytest.raises(ValueError, match="not in"):
        normalize_plan_content_assessment(
            _response(grades={"GENERIC-10": ("conveyed", "")}),
            scenario=SCENARIO,
        )


def test_normalize_requires_finding_for_non_top_grade() -> None:
    with pytest.raises(ValueError, match="without a finding"):
        normalize_plan_content_assessment(
            _response(grades={"PLAN-3": ("missing", "")}),
            scenario=SCENARIO,
        )


def test_normalize_rejects_scenario_mismatch() -> None:
    with pytest.raises(ValueError, match="does not match"):
        normalize_plan_content_assessment(
            _response(scenario_id=OTHER.scenario_id),
            scenario=SCENARIO,
        )


def test_record_keeps_mapping_and_derives_coverage() -> None:
    record = _subject_record()
    value = normalize_plan_content_assessment(
        _response(
            grades={
                "PLAN-2": ("partial", "cap mechanism named, exactly-once unstated"),
                "GENERIC-6": ("missing", "no rollback or risk stated"),
            }
        ),
        scenario=SCENARIO,
    )

    saved = plan_content_record(SCENARIO, _handoff_subject(record), value)

    assert saved["subject"] == {
        "profile": "glm",
        "reasoning_effort": "max",
        "sample_index": 0,
    }
    assert saved["assessment"]["variant"] == "retain"
    assert saved["assessment"]["stage"] == "fresh-agent"
    assert saved["assessment"]["coverage"] == round(15 / 17, 3)
    assert "PLAN-2" in saved["summary"] and "GENERIC-6" in saved["summary"]


def test_aggregate_reports_counts_and_zero_variance() -> None:
    def _saved(grades: dict[str, tuple[str, str]]) -> dict[str, object]:
        value = normalize_plan_content_assessment(
            _response(grades=grades), scenario=SCENARIO
        )
        return plan_content_record(SCENARIO, _handoff_subject(_subject_record()), value)

    first = _saved(
        {"PLAN-2": ("partial", "cap mechanism named, exactly-once unstated")}
    )
    second = _saved({"GENERIC-6": ("missing", "no rollback or risk stated")})

    aggregate = aggregate_plan_content([first, second])

    assert aggregate["assessment_count"] == 2
    counts = aggregate["requirements"]["PLAN-2"]["grade_counts"]
    assert counts == {"conveyed": 1, "partial": 1}
    assert aggregate["requirements"]["GENERIC-1"]["grade_counts"] == {"conveyed": 2}
    assert "GENERIC-1" in aggregate["zero_variance_requirements"]
    assert "PLAN-2" not in aggregate["zero_variance_requirements"]
    assert aggregate["mean_coverage"] == round((16 / 17 + 16 / 17), 3) / 2


def test_aggregate_handles_empty() -> None:
    assert aggregate_plan_content([])["assessment_count"] == 0
