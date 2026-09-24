from __future__ import annotations

import json

from ..handoff_semantic import (
    parse_handoff_semantic,
    validate_handoff_semantic,
)
from ..scenarios import scenario_by_id


def test_handoff_semantic_schema() -> None:
    scenario = scenario_by_id("tg01-eleventy-archive-handoff")
    value = {
        "schema_version": 1,
        "scenario_id": scenario.scenario_id,
        "assessments": [
            {
                "stage": "fresh-agent",
                "variant": "retain",
                "producer": {
                    "profile": "glm",
                    "reasoning_effort": "max",
                },
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
        ],
    }

    parsed = parse_handoff_semantic("```json\n" + json.dumps(value) + "\n```")
    validate_handoff_semantic(
        parsed,
        scenario=scenario,
        expected_count=1,
    )


def test_handoff_semantic_accepts_incomplete_negative_control() -> None:
    scenario = scenario_by_id("tg02-fastapi-pagination-handoff")
    value = {
        "schema_version": 1,
        "scenario_id": scenario.scenario_id,
        "assessments": [
            {
                "stage": "fresh-agent",
                "variant": "incomplete",
                "producer": {
                    "profile": "glm",
                    "reasoning_effort": "max",
                },
                "plan_coverage": "partial",
                "missing_outcomes": ["NOTES-4"],
                "lost_facts_or_decisions": ["Header decision missing."],
                "invented_scope_or_decisions": [],
                "testing_boundary": "partial",
                "documentation_boundary": "partial",
                "task_self_contained": False,
                "broad_rediscovery": True,
                "handoff_quality_score": 50,
                "efficiency_interpretation": "Reinvestigated the repository.",
                "summary": "The incomplete task caused avoidable work.",
            }
        ],
    }

    validate_handoff_semantic(
        value,
        scenario=scenario,
        expected_count=1,
    )
