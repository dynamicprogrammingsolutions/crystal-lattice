"""Task-file fidelity and readability assessment tests.

Both judges take embedded rendered material only — no producer
identity, validity, or tool metrics; fidelity also embeds the
conversation, readability deliberately does not. The findings contract
is enforced: every non-top grade requires `{where, why}` findings, the
readability section set must match the files' actual top-level
sections, and both responses carry a mistake-harvesting block.
"""

from __future__ import annotations

import json

import pytest

from ..file_quality import (
    FIDELITY_DIMENSIONS,
    aggregate_file_fidelity,
    aggregate_file_readability,
    file_fidelity_prompt,
    file_fidelity_record,
    file_readability_prompt,
    file_readability_record,
    normalize_file_fidelity,
    normalize_file_readability,
    parse_file_fidelity,
    parse_file_readability,
    quality_target_excerpt,
    validate_file_fidelity,
    validate_file_readability,
)
from ..scenarios import scenario_by_id
from ..semantic import ProducerSubject


SCENARIO = scenario_by_id("tg02-fastapi-pagination-handoff")
KIND_SCENARIO = scenario_by_id("tg07-eleventy-decided-work-tracking")

TASK_FILES = {
    "tasks/notes-pagination.md": (
        "# Notes pagination task\n\n"
        "## Requirements checklist\n\n"
        "- NOTES-1 `limit` and `offset` are optional validated controls.\n\n"
        "## Supporting details\n\n"
        "The route returns the full array today.\n\n"
        "## Implementation plan\n\n"
        "Status: Draft\n\n"
        "Settle the query contract, then add the parameters.\n"
    )
}


def _subject_record(*, valid: bool = True) -> dict[str, object]:
    return {
        "scenario_id": SCENARIO.scenario_id,
        "producer": {"profile": "glm", "model": "model-x", "reasoning_effort": "max"},
        "valid": valid,
        "invalid_reasons": [] if valid else ["provider errors: provider limit"],
        "response": "We decided the query contract: limit 1-100, offset >= 0.",
        "task_files": TASK_FILES,
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


def _fidelity_response(**overrides: object) -> dict[str, object]:
    dimensions = {
        name: {"grade": grades[0], "findings": []}
        for name, grades in FIDELITY_DIMENSIONS.items()
    }
    assessment = {"dimensions": dimensions, "mistakes": [], "summary": "Fine."}
    assessment.update(overrides)
    return {
        "schema_version": 1,
        "scenario_id": SCENARIO.scenario_id,
        "assessment": assessment,
    }


def _readability_response(
    *,
    sections: dict[str, dict[str, object]] | None = None,
    navigation: dict[str, object] | None = None,
    **overrides: object,
) -> dict[str, object]:
    resolved_sections = sections or {
        title: {"grade": "readable", "findings": []}
        for title in (
            "Requirements checklist",
            "Supporting details",
            "Implementation plan",
        )
    }
    assessment = {
        "sections": resolved_sections,
        "navigation": navigation or {"grade": "navigable", "findings": []},
        "mistakes": [],
        "summary": "Fine.",
    }
    assessment.update(overrides)
    return {
        "schema_version": 1,
        "scenario_id": SCENARIO.scenario_id,
        "assessment": assessment,
    }


def test_target_excerpt_drops_decomposition_machinery() -> None:
    excerpt = quality_target_excerpt(SCENARIO)

    assert "NOTES-1" in excerpt and "limit" in excerpt
    for noise in ("acceptable_partition_sizes", "coherent_deliverables"):
        assert noise not in excerpt
    kind_excerpt = quality_target_excerpt(KIND_SCENARIO)
    assert "Task kind: tracking" in kind_excerpt
    assert "Applicable sections:" in kind_excerpt


def test_fidelity_prompt_embeds_text_without_identity() -> None:
    prompt = file_fidelity_prompt(SCENARIO, _subject_record())

    assert "## Requirements checklist" in prompt
    assert "tasks/notes-pagination.md" in prompt
    assert "We decided the query contract" in prompt
    for leaked in ("model-x", "tool_metrics", "invalid_reasons", '"task_files"'):
        assert leaked not in prompt


def test_readability_prompt_carries_facts_and_no_conversation() -> None:
    prompt = file_readability_prompt(SCENARIO, _subject_record())

    assert "| Section | Words |" in prompt
    assert "| Requirements checklist |" in prompt
    assert "tasks/notes-pagination.md" in prompt
    # The conversation is deliberately absent.
    assert "We decided the query contract" not in prompt
    for leaked in ("model-x", "tool_metrics", "invalid_reasons"):
        assert leaked not in prompt


def test_prompts_reject_invalid_subjects() -> None:
    record = _subject_record(valid=False)
    with pytest.raises(ValueError, match="valid subject"):
        file_fidelity_prompt(SCENARIO, record)
    with pytest.raises(ValueError, match="valid subject"):
        file_readability_prompt(SCENARIO, record)


def test_parse_tolerates_fenced_json() -> None:
    text = "```json\n" + json.dumps(_fidelity_response()) + "\n```"
    assert parse_file_fidelity(text)["scenario_id"] == SCENARIO.scenario_id
    assert (
        parse_file_readability(json.dumps(_readability_response()))["scenario_id"]
        == SCENARIO.scenario_id
    )


def test_fidelity_normalize_accepts_all_declared_grades() -> None:
    for name, grades in FIDELITY_DIMENSIONS.items():
        for grade in grades:
            response = _fidelity_response()
            if grade != grades[0]:
                response["assessment"]["dimensions"][name] = {
                    "grade": grade,
                    "findings": [
                        {
                            "where": "Implementation plan",
                            "quote": "text",
                            "why": "reason",
                        }
                    ],
                }
            value = normalize_file_fidelity(response, scenario=SCENARIO)
            validate_file_fidelity(value)
            assert value["dimensions"][name]["grade"] == grade


def test_fidelity_requires_findings_for_non_top_grade() -> None:
    response = _fidelity_response()
    response["assessment"]["dimensions"]["plan_design_completeness"] = {
        "grade": "partial",
        "findings": [],
    }
    with pytest.raises(ValueError, match="without findings"):
        normalize_file_fidelity(response, scenario=SCENARIO)


def test_fidelity_rejects_wrong_findings_shape() -> None:
    response = _fidelity_response()
    response["assessment"]["dimensions"]["task_kind_fit"] = {
        "grade": "missing",
        "findings": [{"where": "", "why": "reason"}],
    }
    with pytest.raises(ValueError, match="where and why"):
        normalize_file_fidelity(response, scenario=SCENARIO)


def test_fidelity_rejects_scenario_mismatch_and_dimensions() -> None:
    response = _fidelity_response()
    response["scenario_id"] = "other"
    with pytest.raises(ValueError, match="does not match"):
        normalize_file_fidelity(response, scenario=SCENARIO)
    response = _fidelity_response()
    del response["assessment"]["dimensions"]["task_kind_fit"]
    with pytest.raises(ValueError, match="do not match the contract"):
        normalize_file_fidelity(response, scenario=SCENARIO)


def test_fidelity_record_keeps_mapping_and_mistakes() -> None:
    response = _fidelity_response(
        mistakes=[
            {
                "where": "Requirements checklist",
                "quote": "…",
                "why": "dropped the ordering guarantee",
            }
        ]
    )
    value = normalize_file_fidelity(response, scenario=SCENARIO)
    saved = file_fidelity_record(SCENARIO, _subject(_subject_record()), value)

    assert saved["subject"]["profile"] == "glm"
    assert len(saved["assessment"]["mistakes"]) == 1
    assert "mistakes=1" in saved["summary"]


def test_readability_normalize_matches_actual_sections() -> None:
    value = normalize_file_readability(
        _readability_response(), scenario=SCENARIO, record=_subject_record()
    )
    validate_file_readability(value)
    assert set(value["sections"]) == {
        "Requirements checklist",
        "Supporting details",
        "Implementation plan",
    }


def test_readability_rejects_unknown_section() -> None:
    sections = {
        "Requirements checklist": {"grade": "readable", "findings": []},
        "Invented section": {"grade": "readable", "findings": []},
        "Supporting details": {"grade": "readable", "findings": []},
        "Implementation plan": {"grade": "readable", "findings": []},
    }
    with pytest.raises(ValueError, match=r"unexpected=\['Invented section'\]"):
        normalize_file_readability(
            _readability_response(sections=sections),
            scenario=SCENARIO,
            record=_subject_record(),
        )


def test_readability_requires_findings_for_non_top() -> None:
    sections = {
        "Requirements checklist": {"grade": "readable", "findings": []},
        "Supporting details": {
            "grade": "unreadable",
            "findings": [
                {
                    "where": "Supporting details",
                    "quote": "…",
                    "why": "one 200-word paragraph",
                }
            ],
        },
        "Implementation plan": {"grade": "readable", "findings": []},
    }
    value = normalize_file_readability(
        _readability_response(sections=sections),
        scenario=SCENARIO,
        record=_subject_record(),
    )
    validate_file_readability(value)
    bad = {
        **sections,
        "Supporting details": {"grade": "partial", "findings": []},
    }
    with pytest.raises(ValueError, match="without findings"):
        normalize_file_readability(
            _readability_response(sections=bad),
            scenario=SCENARIO,
            record=_subject_record(),
        )


def test_readability_navigation_needs_findings_when_not_top() -> None:
    navigation = {"grade": "confusing", "findings": []}
    with pytest.raises(ValueError, match="readability navigation"):
        normalize_file_readability(
            _readability_response(navigation=navigation),
            scenario=SCENARIO,
            record=_subject_record(),
        )


def test_readability_record_and_aggregate() -> None:
    record = _subject_record()
    value = normalize_file_readability(
        _readability_response(
            mistakes=[
                {
                    "where": "Implementation plan",
                    "quote": "…",
                    "why": "wall-like list item",
                }
            ]
        ),
        scenario=SCENARIO,
        record=record,
    )
    saved = file_readability_record(SCENARIO, _subject(record), value)
    assert "3/3 readable" in saved["summary"]
    assert "mistakes=1" in saved["summary"]

    aggregate = aggregate_file_readability([saved["assessment"]])
    assert aggregate["assessment_count"] == 1
    assert aggregate["section_top_share"] == 1.0
    assert aggregate["navigation"] == {"navigable": 1}
    assert aggregate_file_readability([])["assessment_count"] == 0


def test_fidelity_aggregate_reports_shares() -> None:
    first = normalize_file_fidelity(_fidelity_response(), scenario=SCENARIO)
    second = normalize_file_fidelity(
        _fidelity_response(
            dimensions={
                **_fidelity_response()["assessment"]["dimensions"],
                "durable_context_preservation": {
                    "grade": "partial",
                    "findings": [
                        {
                            "where": "Supporting details",
                            "quote": "…",
                            "why": "dropped the ordering guarantee",
                        }
                    ],
                },
            }
        ),
        scenario=SCENARIO,
    )
    aggregate = aggregate_file_fidelity([first, second])
    assert aggregate["assessment_count"] == 2
    assert aggregate["dimensions"]["durable_context_preservation"]["grade_counts"] == {
        "complete": 1,
        "partial": 1,
    }
    assert aggregate["dimensions"]["plan_justification"]["top_grade_share"] == 1.0
    assert aggregate_file_fidelity([])["assessment_count"] == 0
