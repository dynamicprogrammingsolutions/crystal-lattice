from __future__ import annotations

import json
from pathlib import Path

import pytest

from suites.documentation_standard.requirement_quality import (
    ALL_SCENARIOS,
    PRODUCER_CASES,
    SCENARIOS,
    candidate_task_guidance_source,
    current_task_guidance_source,
    load_target,
    requirement_minimal_guidance_source,
    scenario_fixture_facts,
    scenario_prompt,
    scenario_project_context,
    scenario_task_file_prompt,
)
from suites.documentation_standard.requirement_quality_evaluator import (
    REQUIREMENT_CLASSIFICATIONS,
    SIGNALS,
    build_evaluator_prompt,
    dataset_records_for_scenario,
    load_accepted_anchors,
    load_accepted_dataset,
    parse_evaluator_response,
    parse_evaluator_response_with_repairs,
    validate_evaluator_result,
)
from suites.documentation_standard.freeze_requirement_quality_current_results import (
    SEMANTIC_RESULTS_OUTPUT,
    TASK_DATASET_OUTPUT,
)
from suites.documentation_standard.support import PROFILES, apply_fixture
from suites.documentation_standard.test_requirement_quality_task_guidance import (
    _task_structure_findings,
)


@pytest.mark.parametrize(
    "scenario",
    ALL_SCENARIOS,
    ids=lambda value: value.scenario_id,
)
def test_requirement_quality_target_and_prompt_are_valid(scenario) -> None:
    target = load_target(scenario)
    assert 3 <= len(target["required_outcomes"]) <= 8
    assert scenario_prompt(scenario)
    assert scenario_fixture_facts(scenario)


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda value: value.scenario_id)
def test_primary_requirement_quality_scenario_has_project_context(scenario) -> None:
    target = load_target(scenario)
    project = target["project"]

    assert scenario_project_context(scenario)
    assert project["name"] == scenario.project_name
    assert project["kind"] == scenario.project_kind
    assert project["upstream"] == scenario.upstream
    assert project["revision"] == scenario.upstream_revision
    assert len(project["revision"]) == 40
    assert target["task_scope"]
    assert target["task_file_scope"]
    assert len(target["testing_expectations"]["required_evidence"]) == 3
    assert target["testing_expectations"]["important_crossing"]
    assert target["testing_expectations"]["avoid"]
    prompt = scenario_task_file_prompt(scenario)
    assert prompt
    assert "Create one task file with a Draft execution plan" in prompt
    assert "testing strategy" not in prompt.lower()
    assert "test plan" not in prompt.lower()


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda value: value.scenario_id)
def test_requirement_quality_fixture_matches_scenario(
    tmp_path: Path,
    scenario,
) -> None:
    workspace = tmp_path / "workspace"
    workspace.mkdir()
    (workspace / ".git").mkdir()

    apply_fixture(workspace, scenario.fixture_id, "base")

    assert (workspace / "AGENTS.md").is_file()
    assert (workspace / "README.md").is_file()
    assert (workspace / "UPSTREAM.md").is_file()
    assert (workspace / "docs/development/index.md").is_file()
    assert not (workspace / "docs/development/specifications").exists()


def test_requirement_minimal_guidance_has_no_scope_restraint_rule() -> None:
    guidance = requirement_minimal_guidance_source()
    paths = tuple(item.path for item in guidance.files())
    text = "\n".join(
        guidance.read_bytes(path).decode("utf-8") for path in paths
    ).lower()

    assert paths == ("AGENTS.md", "docs/development/documentation.md")
    assert "tasks-v7" not in text
    assert "more analysis" not in text
    assert "optional improvement" not in text
    assert "do not turn implementation" not in text
    assert "primary evidence" not in text


def test_current_task_guidance_uses_maintained_general_and_task_files() -> None:
    guidance = current_task_guidance_source()
    paths = tuple(item.path for item in guidance.files())
    text = "\n".join(
        guidance.read_bytes(path).decode("utf-8") for path in paths
    )

    assert paths == (
        "docs/development/documentation.md",
        "agents/TASKS-v7.md",
    )
    assert "### Requirement verification" in text
    assert "### Additional implementation verification" in text
    assert "Include the testing strategy" not in text


def test_candidate_task_guidance_contains_the_approved_replacements() -> None:
    current = current_task_guidance_source()
    candidate = candidate_task_guidance_source()
    text = "\n".join(
        candidate.read_bytes(path).decode("utf-8")
        for path in candidate.paths
    )

    assert candidate.paths == current.paths
    assert candidate.sha256() != current.sha256()
    assert "minimum approved outcomes and constraints" in text
    assert (
        "Easy-to-reverse code does not make a public contract a local choice"
        in text
    )
    assert "Do not invent fallback or error behavior" in text
    assert "A mock is insufficient when it supplies or bypasses that behavior" in text
    assert "do not install dependencies or create scratch implementations" in text
    assert "remove incidental changes before handoff" in text
    assert "testing strategy" not in scenario_task_file_prompt(SCENARIOS[0]).lower()


def test_accepted_requirement_quality_dataset_is_complete() -> None:
    dataset = load_accepted_dataset()
    anchors = load_accepted_anchors()

    assert len(dataset["records"]) == len(SCENARIOS) * len(PRODUCER_CASES)
    assert set(anchors["scenarios"]) == {
        scenario.scenario_id for scenario in SCENARIOS
    }
    for scenario in SCENARIOS:
        records = dataset_records_for_scenario(dataset, scenario)
        assert [record["candidate_id"] for record in records] == [
            f"{profile}-{effort}" for profile, effort in PRODUCER_CASES
        ]


def test_semantic_evaluator_prompt_and_schema_round_trip() -> None:
    scenario = SCENARIOS[0]
    target = load_target(scenario)
    dataset = load_accepted_dataset()
    candidate = dataset_records_for_scenario(dataset, scenario)[0]
    prompt = build_evaluator_prompt(
        dataset_id=dataset["dataset_id"],
        scenario=scenario,
        target=target,
        candidates=[candidate],
        assess_testing=False,
    )
    result = {
        "schema_version": 1,
        "dataset_id": dataset["dataset_id"],
        "scenario_id": scenario.scenario_id,
        "assessments": [
            {
                "candidate_id": candidate["candidate_id"],
                "requirement_assessment": {
                    "coverage_status": "complete",
                    "coverage": [
                        {
                            "outcome_id": outcome["id"],
                            "status": "complete",
                            "evidence": "Candidate evidence.",
                            "notes": "",
                        }
                        for outcome in target["required_outcomes"]
                    ],
                    "signals": ["exact_accessibility_mechanism"],
                    "added_obligations": [
                        {
                            "summary": "Exact relation attributes.",
                            "classification": "acceptance_example_promoted",
                            "severity": "minor",
                            "source_excerpt": "rel=prev/next",
                            "rationale": "The target requires accessibility, not this mechanism.",
                        }
                    ],
                    "grouping": [],
                    "expansion_severity": "low",
                    "review_burden": "low",
                    "summary": "Complete with one minor addition.",
                },
                "testing_plan_assessment": None,
            }
        ],
    }
    parsed = parse_evaluator_response(json.dumps(result))

    assert "Requirement count is not a verdict" in prompt
    assert set(REQUIREMENT_CLASSIFICATIONS)
    assert set(SIGNALS)
    validate_evaluator_result(
        parsed,
        dataset_id=dataset["dataset_id"],
        scenario=scenario,
        target=target,
        candidate_ids=[candidate["candidate_id"]],
        assess_testing=False,
    )

    repair_fixture = {
        "assessments": [
            {
                "candidate_id": "first",
                "testing_plan_assessment": {"summary": "one"},
            },
            {
                "candidate_id": "second",
                "testing_plan_assessment": {"summary": "two"},
            },
        ]
    }
    rendered_repair_fixture = json.dumps(
        repair_fixture,
        separators=(",", ":"),
    )
    malformed = rendered_repair_fixture.replace(
        '"one"}},{"candidate_id"',
        '"one"},{"candidate_id"',
        1,
    )
    repaired, repairs = parse_evaluator_response_with_repairs(malformed)
    assert repaired == repair_fixture
    assert len(repairs) == 1

    final_fixture = {"assessments": [repair_fixture["assessments"][0]]}
    rendered_final_fixture = json.dumps(
        final_fixture,
        separators=(",", ":"),
    )
    malformed_final = rendered_final_fixture.replace(
        '"one"}}]}',
        '"one"}]}',
        1,
    )
    repaired_final, final_repairs = parse_evaluator_response_with_repairs(
        malformed_final
    )
    assert repaired_final == final_fixture
    assert len(final_repairs) == 1


def test_frozen_task_and_semantic_datasets_are_complete() -> None:
    task_dataset = json.loads(TASK_DATASET_OUTPUT.read_text(encoding="utf-8"))
    semantic = json.loads(SEMANTIC_RESULTS_OUTPUT.read_text(encoding="utf-8"))

    assert task_dataset["dataset_id"] == "current-task-guidance-20260914"
    assert len(task_dataset["records"]) == len(SCENARIOS) * len(PRODUCER_CASES)
    assert tuple(
        item["path"] for item in task_dataset["guidance"]["files"]
    ) == (
        "docs/development/documentation.md",
        "agents/TASKS-v7.md",
    )
    assert len(semantic["results"]) == len(SCENARIOS) * 2
    assert {
        value["dataset_id"] for value in semantic["results"]
    } == {
        "initial-minimal-guidance-20260914",
        "current-task-guidance-20260914",
    }
    repaired = [
        value
        for value in semantic["results"]
        if value.get("response_repairs")
    ]
    assert len(repaired) == 1
    assert repaired[0]["dataset_id"] == "current-task-guidance-20260914"
    assert repaired[0]["scenario_id"] == "35-flask-vue-book-filter"


def test_frozen_candidate_datasets_are_complete() -> None:
    fixture_root = Path(
        "maintainer/agent-evaluation/suites/documentation_standard/fixtures"
    )
    variants = (
        (
            "candidate-task-guidance-20260915",
            fixture_root
            / "candidate_task_guidance_requirement_quality_dataset.json",
            fixture_root / "requirement_quality_candidate_semantic_results.json",
        ),
        (
            "candidate-task-guidance-v2-20260915",
            fixture_root
            / "candidate_v2_task_guidance_requirement_quality_dataset.json",
            fixture_root
            / "requirement_quality_candidate_v2_semantic_results.json",
        ),
    )
    expected_candidates = {
        f"{profile}-{effort}" for profile, effort in PRODUCER_CASES
    }

    for dataset_id, task_path, semantic_path in variants:
        task_dataset = json.loads(task_path.read_text(encoding="utf-8"))
        semantic_dataset = json.loads(
            semantic_path.read_text(encoding="utf-8")
        )
        assert task_dataset["dataset_id"] == dataset_id
        assert semantic_dataset["dataset_id"] == dataset_id
        assert len(task_dataset["records"]) == len(SCENARIOS) * len(
            PRODUCER_CASES
        )
        assert len(semantic_dataset["results"]) == len(SCENARIOS)
        for scenario in SCENARIOS:
            assert {
                record["candidate_id"]
                for record in task_dataset["records"]
                if record["scenario_id"] == scenario.scenario_id
            } == expected_candidates


def test_task_structure_parser_uses_the_required_closing_sequence() -> None:
    valid = {
        "tasks/20260915-demo.md": """# Demo

Description.

## Requirements checklist

- [ ] R1: Observable behavior.

## Execution plan

Status: Draft

### Documentation

An earlier documentation discussion.

### Implementation decisions and open questions

No open questions.

### Documentation

No user documentation change.

### Task checklist

- [ ] Implement.
- [ ] Add `## Implementation Notes` only after execution starts.

### Requirement verification

- R1: Public-boundary test.
"""
    }
    invalid = {
        path: text.replace(
            "### Implementation decisions and open questions\n\n"
            "No open questions.\n\n",
            "",
        )
        for path, text in valid.items()
    }

    assert not [
        finding for finding in _task_structure_findings(valid) if not finding.passed
    ]
    failures = [
        finding.name
        for finding in _task_structure_findings(invalid)
        if not finding.passed
    ]
    assert failures == ["plan closing sections are present and ordered"]

    premature_notes = {
        path: text + "\n## Implementation Notes\n\nNot started.\n"
        for path, text in valid.items()
    }
    note_failures = [
        finding.name
        for finding in _task_structure_findings(premature_notes)
        if not finding.passed
    ]
    assert note_failures == [
        "planning output has no implementation or completion notes"
    ]


def test_requirement_quality_profiles_apply_provider_specific_effort() -> None:
    glm = PROFILES["glm"].request_overrides(Path("/tmp/work"), reasoning_effort="max")
    gpt = PROFILES["gpt"].request_overrides(Path("/tmp/work"), reasoning_effort="xhigh")

    assert glm["request_options"] == {"reasoning_effort": "max"}
    assert "reasoning_effort" not in glm
    assert gpt["reasoning_effort"] == "xhigh"
    assert "request_options" not in gpt
    assert gpt["auth_mode"] == "chatgpt"