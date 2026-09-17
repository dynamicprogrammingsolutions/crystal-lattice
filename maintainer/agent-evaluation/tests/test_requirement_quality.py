from __future__ import annotations

import json
from pathlib import Path

import pytest

from suites.documentation_standard.requirement_quality import (
    ALL_SCENARIOS,
    PRODUCER_CASES,
    ROOT_GUIDANCE_BASELINE_REVISION,
    SCENARIOS,
    candidate_task_guidance_source,
    current_task_guidance_source,
    load_target,
    requirement_minimal_guidance_source,
    root_guidance_source,
    scenario_root_plan_prompt,
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
from suites.documentation_standard.root_guidance_quality import (
    QUALITY_DIMENSIONS,
    QUALITY_METRICS,
    build_quality_prompt,
    mapped_quality_result,
    quality_label_mapping,
    validate_quality_result,
)
from suites.documentation_standard.root_guidance_scoring import (
    aggregate_scored_cells,
    score_semantic_assessment,
)
from suites.documentation_standard.render_root_guidance_snapshots import (
    SNAPSHOT_ROOT,
    SNAPSHOT_VARIANTS,
)
from suites.documentation_standard.freeze_requirement_quality_current_results import (
    SEMANTIC_RESULTS_OUTPUT,
    TASK_DATASET_OUTPUT,
)
from suites.documentation_standard.freeze_root_guidance_focused_results import (
    FOCUSED_CASES,
    OUTPUT_PATH as ROOT_GUIDANCE_FOCUSED_RESULTS,
    dataset_id as root_guidance_dataset_id,
    test_prefix as root_guidance_test_prefix,
)
from suites.documentation_standard.freeze_root_guidance_full_matrix import (
    OUTPUT_PATH as ROOT_GUIDANCE_FULL_MATRIX_RESULTS,
)
from suites.documentation_standard.analyze_root_guidance_full_matrix import (
    ANALYSIS_PATH as ROOT_GUIDANCE_FULL_MATRIX_ANALYSIS,
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
    root_prompt = scenario_root_plan_prompt(scenario)
    assert root_prompt
    assert "completion requirements" in root_prompt
    assert "concise implementation plan" in root_prompt
    assert "testing strategy" not in root_prompt.lower()
    assert "test plan" not in root_prompt.lower()
    assert "create one task file" not in root_prompt.lower()


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
    assert candidate.name == "candidate-task-guidance-v3"
    assert candidate.sha256() != current.sha256()
    assert "minimum approved outcomes and constraints" in text
    assert (
        "Easy-to-reverse code does not make a public contract a local choice"
        in text
    )
    assert "Do not invent fallback or error behavior" in text
    assert (
        "A mock that supplies or bypasses the claimed behavior is not "
        "decisive evidence"
    ) in text
    assert "keep it outside requirements and implementation until approved" in text
    assert "representative accepted and rejected boundaries" not in text
    assert "Missing test infrastructure alone" not in text
    assert "do not install dependencies or create scratch implementations" in text
    assert "remove incidental changes before handoff" in text
    assert "testing strategy" not in scenario_task_file_prompt(SCENARIOS[0]).lower()


def test_root_guidance_variants_are_isolated_and_reproducible(
    tmp_path: Path,
) -> None:
    baseline = root_guidance_source("baseline", "root-only")
    requirements = root_guidance_source("requirements", "root-only")
    testing = root_guidance_source("testing", "root-only")
    combined = root_guidance_source("combined", "task")
    requirements_v2 = root_guidance_source("requirements-v2", "root-only")
    testing_v2 = root_guidance_source("testing-v2", "root-only")
    combined_v2 = root_guidance_source("combined-v2", "task")

    baseline_text = baseline.read_bytes("AGENTS.md").decode("utf-8")
    requirements_text = requirements.read_bytes("AGENTS.md").decode("utf-8")
    testing_text = testing.read_bytes("AGENTS.md").decode("utf-8")
    combined_text = combined.read_bytes("AGENTS.md").decode("utf-8")
    requirements_v2_text = requirements_v2.read_bytes("AGENTS.md").decode(
        "utf-8"
    )
    testing_v2_text = testing_v2.read_bytes("AGENTS.md").decode("utf-8")
    combined_v2_text = combined_v2.read_bytes("AGENTS.md").decode("utf-8")

    assert baseline.revision == ROOT_GUIDANCE_BASELINE_REVISION
    assert baseline.paths == (
        "AGENTS.md",
        "docs/development/documentation.md",
        "docs/development/crystal-lattice-documentation.md",
    )
    assert combined.paths == (
        "AGENTS.md",
        "docs/development/documentation.md",
        "docs/development/crystal-lattice-documentation.md",
        "agents/TASKS-v7.md",
    )
    assert "\n## Requirements\n" not in baseline_text
    assert "\n## Requirements\n" in requirements_text
    assert "\n## Requirements\n" not in testing_text
    assert "\n## Requirements\n" in combined_text
    assert "\n## Testing Principles\n" in baseline_text
    assert "\n## Testing Principles\n" in requirements_text
    assert "\n## Testing\n" in testing_text
    assert "\n## Testing Principles\n" not in testing_text
    assert "\n## Testing\n" in combined_text
    assert "A mock that supplies or bypasses" in testing_text
    assert "remains outside requirements and implementation" in requirements_text
    assert "Evidence needed to prove an outcome is not another" in (
        requirements_v2_text
    )
    assert "does not authorize an internal mechanism" in requirements_v2_text
    assert "Separate component tests do not prove" in testing_v2_text
    assert "valid boundaries and representative invalid" in testing_v2_text
    assert "Planning-only work leaves no generated files" in testing_v2_text
    assert "\n## Requirements\n" in combined_v2_text
    assert "\n## Testing\n" in combined_v2_text

    baseline_docs = baseline.read_bytes(
        "docs/development/documentation.md"
    )
    for guidance in (
        requirements,
        testing,
        combined,
        requirements_v2,
        testing_v2,
        combined_v2,
    ):
        assert guidance.read_bytes(
            "docs/development/documentation.md"
        ) == baseline_docs
    task_source = root_guidance_source("baseline", "task")
    baseline_tasks = task_source.read_bytes("agents/TASKS-v7.md")
    assert combined.read_bytes("agents/TASKS-v7.md") == baseline_tasks
    assert combined_v2.read_bytes("agents/TASKS-v7.md") == baseline_tasks

    workspace = tmp_path / "workspace"
    requirements.copy_to(workspace)
    assert (workspace / "AGENTS.md").read_text(encoding="utf-8") == (
        requirements_text
    )
    assert (
        requirements.metadata()["content_override_paths"]
        == ["AGENTS.md"]
    )
    assert len(
        {
            baseline.sha256(),
            requirements.sha256(),
            testing.sha256(),
            combined.sha256(),
            requirements_v2.sha256(),
            testing_v2.sha256(),
            combined_v2.sha256(),
        }
    ) == 7


def test_root_guidance_focused_selection_is_unique_and_traceable() -> None:
    identities: set[tuple[str, str, str, str]] = set()
    for (variant, mode, scenario_id), cases in FOCUSED_CASES.items():
        assert variant
        assert mode in {"root-only", "task"}
        assert scenario_id in {
            scenario.scenario_id for scenario in SCENARIOS
        }
        assert root_guidance_dataset_id(variant, mode) == (
            f"root-guidance-{variant}-{mode}-20260917"
        )
        assert root_guidance_test_prefix(variant, mode) == (
            f"requirement-root-{variant}-{mode}"
        )
        assert cases
        for profile, effort in cases:
            identity = (
                variant,
                mode,
                scenario_id,
                f"{profile}-{effort}",
            )
            assert identity not in identities
            identities.add(identity)
            assert (profile, effort) in PRODUCER_CASES
    assert len(identities) == 66


def test_frozen_root_guidance_focused_results_are_complete() -> None:
    value = json.loads(
        ROOT_GUIDANCE_FOCUSED_RESULTS.read_text(encoding="utf-8")
    )

    assert value["schema_version"] == 1
    assert value["dataset_id"] == "root-guidance-focused-20260917"
    assert len(value["producer_records"]) == 66
    assert len(value["semantic_assessments"]) == 60
    assert len(value["producer_failed_attempts"]) == 1
    assert len(value["semantic_errors"]) == 3
    assert len(value["missing_semantic_assessments"]) == 6
    assert all(
        "effective_message" not in record["guidance"]
        for record in value["producer_records"]
    )
    decision_missing = [
        item
        for item in value["missing_semantic_assessments"]
        if item["variant"] in {"baseline", "combined-v2"}
    ]
    assert decision_missing == []


def test_frozen_legacy_root_guidance_full_matrix_is_complete() -> None:
    matrix = json.loads(
        ROOT_GUIDANCE_FULL_MATRIX_RESULTS.read_text(encoding="utf-8")
    )
    analysis = json.loads(
        ROOT_GUIDANCE_FULL_MATRIX_ANALYSIS.read_text(encoding="utf-8")
    )

    assert matrix["dataset_id"] == "root-guidance-full-matrix-20260917"
    assert len(matrix["producer_records"]) == 84
    assert len(matrix["semantic_assessments"]) == 84
    assert matrix["semantic_errors"] == []
    assert matrix["missing_semantic_assessments"] == []
    assert matrix["pairwise_quality_records"] == []
    assert len(matrix["missing_pairwise_quality"]) == 42
    assert analysis["counts"] == {
        "producer_records": 84,
        "semantic_assessments": 84,
        "pairwise_quality_records": 0,
        "producer_failures": 7,
        "semantic_errors": 0,
        "missing_semantic_assessments": 0,
        "pairwise_quality_errors": 0,
        "missing_pairwise_quality": 42,
    }


def test_root_guidance_effort_scoring_distinguishes_quality_axes() -> None:
    assessment = {
        "requirement_assessment": {
            "coverage_status": "complete",
            "expansion_severity": "low",
            "added_obligations": [],
            "grouping": [],
        },
        "testing_plan_assessment": {
            "overall_coverage": "complete",
            "layer_selection": "appropriate",
            "important_crossing": "present",
            "verification_focus": "focused",
            "duplication": "none",
            "combinatorial_expansion": "none",
        },
    }
    high = score_semantic_assessment(assessment, effort="high")

    assert high == {
        "effort": "high",
        "effort_tier": "high_assurance",
        "coverage_score": 100,
        "scope_score": 85,
        "testing_score": 100,
        "requirement_expectation_met": True,
        "testing_expectation_met": True,
        "effort_expectation_met": True,
        "material_added_obligations": 0,
        "material_grouping_issues": 0,
    }

    partial = {
        **assessment,
        "requirement_assessment": {
            **assessment["requirement_assessment"],
            "coverage_status": "partial",
        },
        "testing_plan_assessment": {
            **assessment["testing_plan_assessment"],
            "overall_coverage": "partial",
            "important_crossing": "missing",
        },
    }
    low = score_semantic_assessment(partial, effort="low")
    high_partial = score_semantic_assessment(partial, effort="high")

    assert low["requirement_expectation_met"] is True
    assert low["testing_expectation_met"] is True
    assert high_partial["requirement_expectation_met"] is False
    assert high_partial["testing_expectation_met"] is False

    aggregate = aggregate_scored_cells(
        [
            {"scores": high, "assessment": assessment},
            {"scores": high_partial, "assessment": partial},
        ]
    )
    assert aggregate["cells"] == 2
    assert aggregate["average_coverage_score"] == 80.0
    assert aggregate["effort_expectation_met"] == 1


def test_root_guidance_pairwise_quality_contract() -> None:
    scenario = next(
        item
        for item in SCENARIOS
        if item.scenario_id == "34-fastapi-notes-pagination"
    )
    mapping = quality_label_mapping(
        scenario_id=scenario.scenario_id,
        mode="task",
        candidate_id="gpt-high",
    )
    assert set(mapping) == {"A", "B"}
    assert set(mapping.values()) == {"baseline", "combined-v2"}

    semantic = {
        "candidate_id": "gpt-high",
        "requirement_assessment": {"summary": "complete and focused"},
        "testing_plan_assessment": {"summary": "decisive"},
    }
    prompt = build_quality_prompt(
        scenario=scenario,
        target=load_target(scenario),
        mode="task",
        candidate_id="gpt-high",
        outputs={
            "baseline": {
                "producer": {"profile": "gpt"},
                "generated_files": {"tasks/a.md": "first output"},
            },
            "combined-v2": {
                "producer": {"profile": "gpt"},
                "generated_files": {"tasks/a.md": "second output"},
            },
        },
        semantic_assessments={
            "baseline": semantic,
            "combined-v2": semantic,
        },
        label_mapping=mapping,
    )
    assert "Do not reward verbosity" in prompt
    assert '"combined-v2"' not in prompt
    assert '"baseline"' not in prompt

    result = {
        "schema_version": 1,
        "scenario_id": scenario.scenario_id,
        "candidate_id": "gpt-high",
        "dimension_reviews": [
            {
                "dimension": dimension,
                "preferred": "A",
                "difference": "slight",
                "rationale": "A is easier to use.",
            }
            for dimension in QUALITY_DIMENSIONS
        ],
        "scores": {
            label: {metric: 4 for metric in QUALITY_METRICS}
            for label in ("A", "B")
        },
        "overall_preference": "A",
        "overall_difference": "slight",
        "strengths_a": ["clear"],
        "strengths_b": ["complete"],
        "weaknesses_a": [],
        "weaknesses_b": ["long"],
        "guidance_effects": [
            {
                "observation": "Requirements are shorter.",
                "likely_cause": "dedicated_requirements_section",
                "confidence": "medium",
                "rationale": "The section emphasizes minimum outcomes.",
            }
        ],
        "summary": "A is slightly easier to review.",
    }
    validate_quality_result(
        result,
        scenario_id=scenario.scenario_id,
        candidate_id="gpt-high",
    )
    mapped = mapped_quality_result(result, label_mapping=mapping)
    assert mapped["overall_preference"] == mapping["A"]
    assert set(mapped["scores"]) == {"baseline", "combined-v2"}


@pytest.mark.parametrize("variant", SNAPSHOT_VARIANTS)
def test_rendered_root_guidance_snapshot_matches_runtime_variant(
    variant: str,
) -> None:
    expected = root_guidance_source(variant, "root-only").read_bytes(
        "AGENTS.md"
    )
    assert (SNAPSHOT_ROOT / variant / "AGENTS.md").read_bytes() == expected


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
    testing_prompt = build_evaluator_prompt(
        dataset_id=dataset["dataset_id"],
        scenario=scenario,
        target=target,
        candidates=[candidate],
        assess_testing=True,
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
    assert "For each planning candidate" in testing_prompt
    assert "outside requirements" in prompt
    assert "not an added obligation" in prompt
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

    subset = {
        **dataset,
        "records": [
            record
            for record in dataset["records"]
            if record["scenario_id"] == scenario.scenario_id
            and record["candidate_id"] in {"glm-max", "gpt-medium"}
        ],
    }
    assert [
        record["candidate_id"]
        for record in dataset_records_for_scenario(subset, scenario)
    ] == ["glm-max", "gpt-medium"]

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

    trailing_comma_fixture = {
        "schema_version": 1,
        "values": [{"name": "one"}],
    }
    trailing_comma_text = json.dumps(
        trailing_comma_fixture,
        indent=2,
    ).replace(
        '"one"\n    }',
        '"one",\n    }',
    )
    repaired_trailing, trailing_repairs = (
        parse_evaluator_response_with_repairs(trailing_comma_text)
    )
    assert repaired_trailing == trailing_comma_fixture
    assert len(trailing_repairs) == 1


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
            "v2",
            fixture_root
            / "candidate_task_guidance_requirement_quality_dataset.json",
            fixture_root / "requirement_quality_candidate_semantic_results.json",
        ),
        (
            "candidate-task-guidance-v2-20260915",
            "v2",
            fixture_root
            / "candidate_v2_task_guidance_requirement_quality_dataset.json",
            fixture_root
            / "requirement_quality_candidate_v2_semantic_results.json",
        ),
        (
            "candidate-task-guidance-v3-20260915",
            "v3",
            fixture_root
            / "candidate_v3_task_guidance_requirement_quality_dataset.json",
            fixture_root
            / "requirement_quality_candidate_v3_semantic_results.json",
        ),
    )
    expected_candidates = {
        f"{profile}-{effort}" for profile, effort in PRODUCER_CASES
    }

    for dataset_id, prompt_version, task_path, semantic_path in variants:
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
        assert {
            result["evaluator"]["prompt_version"]
            for result in semantic_dataset["results"]
        } == {prompt_version}
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