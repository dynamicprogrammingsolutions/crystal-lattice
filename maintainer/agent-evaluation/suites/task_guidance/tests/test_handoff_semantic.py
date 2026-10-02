from __future__ import annotations

import json

import pytest

from ..handoff_semantic import (
    HANDOFF_SCHEMA_VERSION,
    HandoffSubject,
    handoff_semantic_prompt,
    parse_handoff_semantic,
    validate_handoff_semantic,
)
from ..scenarios import scenario_by_id


SCENARIO = scenario_by_id("tg01-eleventy-archive-handoff")


def _judgment(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "stage": "fresh-agent",
        "variant": "retain",
        "plan_coverage": "complete",
        "missing_outcomes": [],
        "lost_facts_or_decisions": [],
        "invented_scope_or_decisions": [],
        "testing_boundary": "decisive",
        "documentation_boundary": "appropriate",
        "task_self_contained": True,
        "broad_rediscovery": False,
        "handoff_quality_score": 95,
        "efficiency_interpretation": "Read the task and reused it.",
        "summary": "Complete.",
    }
    value.update(overrides)
    return value


def _subject(
    *,
    stage: str = "fresh-agent",
    variant: str = "retain",
    record: dict[str, object] | None = None,
) -> HandoffSubject:
    return HandoffSubject(
        scenario_id=SCENARIO.scenario_id,
        stage=stage,
        variant=variant,
        profile="glm",
        effort="max",
        sample_index=0,
        record=record
        or {
            "valid": True,
            "response": "the plan response",
            "task_files": {"tasks/010-one.md": "# One\n"},
        },
    )


def test_handoff_semantic_schema() -> None:
    value = {
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "scenario_id": SCENARIO.scenario_id,
        "assessment": _judgment(),
    }

    parsed = parse_handoff_semantic("```json\n" + json.dumps(value) + "\n```")
    validate_handoff_semantic(
        parsed,
        scenario=SCENARIO,
        stage="fresh-agent",
        variant="retain",
    )


def test_handoff_semantic_accepts_incomplete_negative_control() -> None:
    value = {
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "scenario_id": SCENARIO.scenario_id,
        "assessment": _judgment(
            variant="incomplete",
            plan_coverage="partial",
            missing_outcomes=["NOTES-4"],
            lost_facts_or_decisions=["Header decision missing."],
            testing_boundary="partial",
            documentation_boundary="partial",
            task_self_contained=False,
            broad_rediscovery=True,
            handoff_quality_score=50,
            efficiency_interpretation="Reinvestigated the repository.",
            summary="The incomplete task caused avoidable work.",
        ),
    }

    validate_handoff_semantic(
        value,
        scenario=SCENARIO,
        stage="fresh-agent",
        variant="incomplete",
    )


def test_handoff_semantic_rejects_a_stage_mismatch() -> None:
    value = {
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "scenario_id": SCENARIO.scenario_id,
        "assessment": _judgment(stage="same-agent"),
    }

    with pytest.raises(ValueError, match="stage"):
        validate_handoff_semantic(
            value,
            scenario=SCENARIO,
            stage="fresh-agent",
            variant="retain",
        )


def test_handoff_prompt_material_keeps_labels_not_provenance() -> None:
    prompt = handoff_semantic_prompt(SCENARIO, _subject())

    assert "fresh-agent" in prompt
    assert "retain" in prompt
    assert "the plan response" in prompt
    assert '"profile"' not in prompt
    assert '"tool_metrics"' not in prompt
    assert '"valid"' not in prompt
