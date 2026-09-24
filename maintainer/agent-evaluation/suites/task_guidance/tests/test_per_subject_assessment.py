"""Per-subject assessment tests: one subject per request.

The redesigned assessments judge one produced subject per request under a
neutral subject label: the prompt material carries no producer identity,
validity, or tool metrics; the response schema echoes no producer and
must match the subject's stage and variant labels; the saved record keeps
the subject-to-producer mapping; every sample of a cell is one subject;
and a case whose subjects are all invalid is blocked with the recorded
reasons instead of assessed.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from ..handoff_semantic import (
    HANDOFF_SCHEMA_VERSION,
    HandoffSubject,
    handoff_assessment_record,
    handoff_assessment_subject_identity,
    handoff_semantic_prompt,
    load_handoff_subjects,
    parse_handoff_semantic,
    subjects_block_reason as handoff_subjects_block_reason,
    validate_handoff_semantic,
)
from ..scenarios import scenario_by_id
from ..semantic import (
    SEMANTIC_SCHEMA_VERSION,
    ProducerSubject,
    assessment_record,
    assessment_subject_identity,
    load_producer_subjects,
    normalize_semantic_assessment,
    parse_semantic_response,
    semantic_prompt,
    subjects_block_reason,
    validate_semantic_assessment,
)
from ..stages import STAGES


SCENARIO = scenario_by_id("tg01-eleventy-archive-handoff")
HANDOFF_SCENARIO = scenario_by_id("tg02-fastapi-pagination-handoff")


def _producer_record(
    *,
    scenario_id: str = "tg01-eleventy-archive-handoff",
    agent: str = "glm",
    effort: str = "max",
    valid: bool = True,
    marker: str = "alpha",
) -> dict[str, object]:
    return {
        "scenario_id": scenario_id,
        "producer": {
            "profile": agent,
            "model": "model-x",
            "reasoning_effort": effort,
        },
        "valid": valid,
        "invalid_reasons": [] if valid else ["provider errors: provider limit"],
        "response": f"assistant response {marker}",
        "task_files": {f"tasks/{marker}.md": f"# Task {marker}\n"},
        "task_tree": {"implementation_task_count": 1},
        "tool_metrics": {"total": 4, "read": 4},
    }


def _plan_record(
    *,
    scenario_id: str = "tg02-fastapi-pagination-handoff",
    variant: str = "retain",
    agent: str = "glm",
    effort: str = "max",
    valid: bool = True,
    marker: str = "plan",
) -> dict[str, object]:
    return {
        "scenario_id": scenario_id,
        "variant": variant,
        "producer": {
            "profile": agent,
            "model": "model-x",
            "reasoning_effort": effort,
        },
        "valid": valid,
        "invalid_reasons": [] if valid else ["provider errors: limit"],
        "response": f"plan response {marker}",
        "task_files": {f"tasks/{marker}.md": f"# {marker}\n"},
        "tool_metrics": {"total": 2, "read": 2},
    }


def _write_run_record(
    root: Path,
    agent: str,
    run_id: str,
    record_name: str,
    value: dict[str, object],
    *,
    label: str = "l1",
    sample_index: int = 0,
) -> None:
    records = root / agent / "runs" / run_id / "records"
    records.mkdir(parents=True, exist_ok=True)
    (records / record_name).write_text(json.dumps(value), encoding="utf-8")
    (records / "run-model.json").write_text(
        json.dumps(
            {
                "schema": 1,
                "label": label,
                "identity": f"identity-{run_id}",
                "cache_hit": False,
                "sample_index": sample_index,
                "run_id": run_id,
            }
        ),
        encoding="utf-8",
    )


# --- One subject per prompt, no provenance in the material -----------------


def test_task_creation_prompt_carries_one_subject_without_provenance() -> None:
    first = _producer_record(marker="first")
    # A second subject exists in the same matrix; it must not leak in.
    _producer_record(marker="second", agent="gpt", effort="high")

    prompt = semantic_prompt(SCENARIO, first)

    assert "tasks/first.md" in prompt
    assert "assistant response first" in prompt
    assert "tasks/second.md" not in prompt
    assert "assistant response second" not in prompt
    for forbidden in (
        '"profile"',
        '"reasoning_effort"',
        '"model"',
        '"tool_metrics"',
        '"valid"',
        '"invalid_reasons"',
    ):
        assert forbidden not in prompt, forbidden
    assert SCENARIO.scenario_id in prompt


def test_task_creation_prompt_rejects_invalid_subjects() -> None:
    invalid = _producer_record(valid=False)

    with pytest.raises(ValueError, match="valid"):
        semantic_prompt(SCENARIO, invalid)


def test_handoff_prompt_keeps_stage_and_variant_without_provenance() -> None:
    subject = HandoffSubject(
        scenario_id=HANDOFF_SCENARIO.scenario_id,
        stage="fresh-agent",
        variant="retain",
        profile="glm",
        effort="max",
        sample_index=0,
        record=_plan_record(),
    )

    prompt = handoff_semantic_prompt(HANDOFF_SCENARIO, subject)

    assert "fresh-agent" in prompt
    assert "retain" in prompt
    assert "plan response plan" in prompt
    for forbidden in (
        '"profile"',
        '"reasoning_effort"',
        '"model"',
        '"tool_metrics"',
        '"valid"',
        '"invalid_reasons"',
    ):
        assert forbidden not in prompt, forbidden


# --- The response schema echoes no producer --------------------------------


def _task_creation_assessment(**overrides: object) -> dict[str, object]:
    value: dict[str, object] = {
        "outcome_coverage": "complete",
        "missing_outcomes": [],
        "added_obligations": [],
        "semantic_deliverable_count": 2,
        "actual_task_count": 2,
        "deliverable_mappings": [],
        "mergeable_groups": [],
        "unmatched_tasks": [],
        "overpacked_tasks": [],
        "valid_layer_boundaries": [],
        "automatic_layer_fragments": [],
        "dependency_issues": [],
        "crossing_ownership": "complete",
        "fragmentation_severity": "none",
        "fragmentation_ratio": 1.0,
        "quality_metrics": {
            name: {"status": "none", "score": 100, "occurrences": []}
            for name in (
                "fragmentation",
                "phase_only_children",
                "layer_split_without_independent_value",
                "evidence_reownership",
                "unsafe_dependencies",
                "piecewise_crossing_evidence",
            )
        },
        "partition_quality_score": 95,
        "handoff_quality_score": 90,
        "summary": "Coherent deliverables.",
    }
    value.update(overrides)
    return value


def test_task_creation_response_schema_has_no_producer_echo() -> None:
    subject_record = _producer_record()
    value = {
        "schema_version": SEMANTIC_SCHEMA_VERSION,
        "scenario_id": SCENARIO.scenario_id,
        "assessment": _task_creation_assessment(),
    }
    normalized = normalize_semantic_assessment(value, record=subject_record)
    validate_semantic_assessment(normalized, scenario=SCENARIO)

    with_producer = {
        "schema_version": SEMANTIC_SCHEMA_VERSION,
        "scenario_id": SCENARIO.scenario_id,
        "assessment": _task_creation_assessment(
            producer={"profile": "glm", "reasoning_effort": "max"}
        ),
    }
    with pytest.raises(ValueError, match="producer"):
        validate_semantic_assessment(with_producer, scenario=SCENARIO)

    stale = {
        "schema_version": 2,
        "scenario_id": SCENARIO.scenario_id,
        "assessment": _task_creation_assessment(),
    }
    with pytest.raises(ValueError, match="schema_version"):
        validate_semantic_assessment(stale, scenario=SCENARIO)


def _handoff_assessment(**overrides: object) -> dict[str, object]:
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


def test_handoff_response_schema_matches_subject_labels() -> None:
    value = {
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "scenario_id": HANDOFF_SCENARIO.scenario_id,
        "assessment": _handoff_assessment(),
    }
    validate_handoff_semantic(
        value,
        scenario=HANDOFF_SCENARIO,
        stage="fresh-agent",
        variant="retain",
    )

    wrong_variant = {
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "scenario_id": HANDOFF_SCENARIO.scenario_id,
        "assessment": _handoff_assessment(variant="omit"),
    }
    with pytest.raises(ValueError, match="variant"):
        validate_handoff_semantic(
            wrong_variant,
            scenario=HANDOFF_SCENARIO,
            stage="fresh-agent",
            variant="retain",
        )

    with_producer = {
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "scenario_id": HANDOFF_SCENARIO.scenario_id,
        "assessment": _handoff_assessment(
            producer={"profile": "glm", "reasoning_effort": "max"}
        ),
    }
    with pytest.raises(ValueError, match="producer"):
        validate_handoff_semantic(
            with_producer,
            scenario=HANDOFF_SCENARIO,
            stage="fresh-agent",
            variant="retain",
        )

    stale = {
        "schema_version": 1,
        "scenario_id": HANDOFF_SCENARIO.scenario_id,
        "assessment": _handoff_assessment(),
    }
    with pytest.raises(ValueError, match="schema_version"):
        validate_handoff_semantic(
            stale,
            scenario=HANDOFF_SCENARIO,
            stage="fresh-agent",
            variant="retain",
        )


def test_assessment_parsers_accept_fenced_single_judgments() -> None:
    task_value = {
        "schema_version": SEMANTIC_SCHEMA_VERSION,
        "scenario_id": SCENARIO.scenario_id,
        "assessment": _task_creation_assessment(),
    }
    parsed = parse_semantic_response("```json\n" + json.dumps(task_value) + "\n```")
    assert parsed["assessment"]["partition_quality_score"] == 95

    handoff_value = {
        "schema_version": HANDOFF_SCHEMA_VERSION,
        "scenario_id": HANDOFF_SCENARIO.scenario_id,
        "assessment": _handoff_assessment(),
    }
    parsed_handoff = parse_handoff_semantic(
        "```json\n" + json.dumps(handoff_value) + "\n```"
    )
    assert parsed_handoff["assessment"]["handoff_quality_score"] == 95


# --- The record keeps the subject-to-producer mapping ----------------------


def test_task_creation_record_keeps_the_subject_mapping() -> None:
    subject = ProducerSubject(
        scenario_id=SCENARIO.scenario_id,
        profile="glm",
        effort="max",
        sample_index=2,
        record=_producer_record(),
    )
    assessment = _task_creation_assessment()

    record = assessment_record(SCENARIO, subject, assessment)

    assert record["scenario_id"] == SCENARIO.scenario_id
    assert record["subject"] == {
        "profile": "glm",
        "reasoning_effort": "max",
        "sample_index": 2,
    }
    assert record["assessment"] == assessment
    assert record["summary"]["partition_quality_score"] == 95
    assert assessment_subject_identity(record) == (f"{SCENARIO.scenario_id}:glm:max")


def test_handoff_record_keeps_the_subject_mapping() -> None:
    subject = HandoffSubject(
        scenario_id=HANDOFF_SCENARIO.scenario_id,
        stage="fresh-agent",
        variant="retain",
        profile="glm",
        effort="max",
        sample_index=1,
        record=_plan_record(),
    )
    assessment = _handoff_assessment()

    record = handoff_assessment_record(HANDOFF_SCENARIO, subject, assessment)

    assert record["scenario_id"] == HANDOFF_SCENARIO.scenario_id
    assert record["subject"] == {
        "profile": "glm",
        "reasoning_effort": "max",
        "sample_index": 1,
    }
    assert record["assessment"]["variant"] == "retain"
    assert handoff_assessment_subject_identity(record) == (
        f"{HANDOFF_SCENARIO.scenario_id}:retain:glm:max"
    )


# --- Every sample of a cell is one subject ---------------------------------


def test_producer_loader_returns_every_sample_of_a_cell(tmp_path: Path) -> None:
    for index, marker in enumerate(("one", "two")):
        _write_run_record(
            tmp_path,
            "glm",
            f"glm-run-{index}",
            STAGES["task-creation"].record,
            _producer_record(marker=marker),
            sample_index=index,
        )
    _write_run_record(
        tmp_path,
        "gpt",
        "gpt-run",
        STAGES["task-creation"].record,
        _producer_record(agent="gpt", effort="high", marker="gpt"),
    )

    subjects = load_producer_subjects(
        tmp_path,
        scenario=SCENARIO,
        labels=["l1"],
        cells=[("glm", "max")],
    )

    assert [(subject.profile, subject.effort) for subject in subjects] == [
        ("glm", "max"),
        ("glm", "max"),
    ]
    assert [subject.sample_index for subject in subjects] == [0, 1]
    assert subjects[0].record["response"] == "assistant response one"
    assert subjects[1].record["response"] == "assistant response two"


def test_producer_loader_reports_missing_cells(tmp_path: Path) -> None:
    _write_run_record(
        tmp_path,
        "glm",
        "glm-run",
        STAGES["task-creation"].record,
        _producer_record(),
    )

    with pytest.raises(FileNotFoundError, match="gpt"):
        load_producer_subjects(
            tmp_path,
            scenario=SCENARIO,
            labels=["l1"],
        )
    partial = load_producer_subjects(
        tmp_path,
        scenario=SCENARIO,
        labels=["l1"],
        allow_partial=True,
    )
    assert [subject.profile for subject in partial] == ["glm"]


def test_handoff_loader_returns_every_subject_kind(tmp_path: Path) -> None:
    _write_run_record(
        tmp_path,
        "glm",
        "fresh-retain",
        STAGES["handoff-plan"].record,
        _plan_record(variant="retain"),
    )
    _write_run_record(
        tmp_path,
        "glm",
        "fresh-omit",
        STAGES["handoff-plan"].record,
        _plan_record(variant="omit", marker="omit-plan"),
    )
    _write_run_record(
        tmp_path,
        "glm",
        "same-run",
        STAGES["continuation"].record,
        {
            **_plan_record(variant="generated-task", marker="same"),
            "task_creation_tool_metrics": {"total": 5},
            "continuation_tool_metrics": {"total": 1},
        },
    )
    _write_run_record(
        tmp_path,
        "glm",
        "control-run",
        STAGES["negative-control"].record,
        _plan_record(variant="incomplete", marker="control"),
    )

    subjects = load_handoff_subjects(
        tmp_path,
        scenario=HANDOFF_SCENARIO,
        labels=["l1"],
        allow_partial=True,
    )

    observed = [
        (subject.stage, subject.variant, subject.profile, subject.effort)
        for subject in subjects
    ]
    assert observed == [
        ("fresh-agent", "retain", "glm", "max"),
        ("fresh-agent", "omit", "glm", "max"),
        ("same-agent", "generated-task", "glm", "max"),
        ("fresh-agent", "incomplete", "glm", "max"),
    ]
    control = subjects[3]
    assert control.record["response"] == "plan response control"


def test_handoff_loader_selection_limits_the_expected_subjects(
    tmp_path: Path,
) -> None:
    _write_run_record(
        tmp_path,
        "glm",
        "fresh-retain",
        STAGES["handoff-plan"].record,
        _plan_record(variant="retain"),
    )

    with pytest.raises(FileNotFoundError, match="omit"):
        load_handoff_subjects(
            tmp_path,
            scenario=HANDOFF_SCENARIO,
            labels=["l1"],
            selection={("fresh-agent", "omit", "glm", "max")},
        )
    selected = load_handoff_subjects(
        tmp_path,
        scenario=HANDOFF_SCENARIO,
        labels=["l1"],
        selection={("fresh-agent", "retain", "glm", "max")},
    )
    assert [subject.variant for subject in selected] == ["retain"]


# --- Invalid upstreams block with a recorded reason ------------------------


def test_all_invalid_subjects_block_with_the_recorded_reasons() -> None:
    invalid = ProducerSubject(
        scenario_id=SCENARIO.scenario_id,
        profile="glm",
        effort="max",
        sample_index=0,
        record=_producer_record(valid=False),
    )

    reason = subjects_block_reason([invalid])

    assert reason is not None
    assert "glm:max" in reason
    assert "provider limit" in reason


def test_one_valid_subject_unblocks_the_assessment() -> None:
    subjects = [
        ProducerSubject(
            scenario_id=SCENARIO.scenario_id,
            profile="glm",
            effort="max",
            sample_index=0,
            record=_producer_record(valid=False),
        ),
        ProducerSubject(
            scenario_id=SCENARIO.scenario_id,
            profile="glm",
            effort="max",
            sample_index=1,
            record=_producer_record(marker="good"),
        ),
    ]

    assert subjects_block_reason(subjects) is None
    assert handoff_subjects_block_reason([]) is not None
