from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from string import Template
from typing import Any, Mapping, Sequence

from agent_eval.runner import select_cell_records

from .configuration import (
    CATEGORIES,
    negative_control,
    plan_variants,
    producer_cells,
)
from .scenarios import TaskGuidanceScenario
from .semantic import (
    continuation_cell_identity,
    handoff_cell_identity,
)
from .stages import STAGES


HANDOFF_SCHEMA_VERSION = 2
HANDOFF_RECORD_VERSION = 2


@dataclass(frozen=True)
class HandoffSubject:
    """One produced handoff plan: a sample of one handoff cell."""

    scenario_id: str
    stage: str
    variant: str
    profile: str
    effort: str
    sample_index: int
    record: Mapping[str, Any]


def handoff_assessment_subject_identity(value: Mapping[str, Any]) -> str:
    """The cell identity of one per-subject handoff assessment record."""

    subject = value.get("subject") or {}
    assessment = value.get("assessment") or {}
    return (
        f"{value.get('scenario_id')}:{assessment.get('variant')}:"
        f"{subject.get('profile')}:{subject.get('reasoning_effort')}"
    )


def load_handoff_subjects(
    artifact_root: Path,
    *,
    scenario: TaskGuidanceScenario,
    labels: Sequence[str] | None,
    allow_partial: bool = False,
    selection: Sequence[tuple[str, str, str, str]] | None = None,
) -> list[HandoffSubject]:
    """The scenario's handoff subjects under the given run labels.

    Selection delegates to the consolidation core; every sample of a
    cell is one subject. ``selection`` limits the expected subjects to
    ``(stage, variant, profile, effort)`` tuples (one assessment case
    owns one subject cell); without it every declared subject is
    expected: the fresh-agent plans per variant, the same-agent
    continuations, and the designated negative control.
    """

    fresh = _scenario_cells(
        select_cell_records(
            artifact_root,
            record_name=STAGES["handoff-plan"].record,
            cell_identity=handoff_cell_identity,
            labels=labels,
        ),
        scenario.scenario_id,
    )
    same = _scenario_cells(
        select_cell_records(
            artifact_root,
            record_name=STAGES["continuation"].record,
            cell_identity=continuation_cell_identity,
            labels=labels,
        ),
        scenario.scenario_id,
    )
    negative = _scenario_cells(
        select_cell_records(
            artifact_root,
            record_name=STAGES["negative-control"].record,
            cell_identity=handoff_cell_identity,
            labels=labels,
        ),
        scenario.scenario_id,
    )
    generated = _scenario_cells(
        select_cell_records(
            artifact_root,
            record_name=STAGES["generated-plan"].record,
            cell_identity=continuation_cell_identity,
            labels=labels,
        ),
        scenario.scenario_id,
    )
    cells = producer_cells(scenario.category)
    variants = plan_variants(scenario.category)
    has_continuation = "continuation" in CATEGORIES[scenario.category]["stages"]
    control = negative_control(scenario.category)
    has_control = control is not None and control["scenario"] == scenario.scenario_id

    wanted = set(selection) if selection is not None else None

    def _selected(stage: str, variant: str, profile: str, effort: str) -> bool:
        return wanted is None or (stage, variant, profile, effort) in wanted

    missing: list[str] = []
    subjects: list[HandoffSubject] = []

    def _add_subjects(
        stage: str,
        variant: str,
        profile: str,
        effort: str,
        records: Mapping[str, tuple[Any, ...]],
        record_name: str,
        *,
        key: str | None = None,
    ) -> None:
        if not _selected(stage, variant, profile, effort):
            return
        cell_key = (
            key
            if key is not None
            else f"{scenario.scenario_id}:{variant}:{profile}:{effort}"
        )
        samples = records.get(cell_key)
        if not samples:
            missing.append(f"{record_name}:{variant}:{profile}:{effort}")
            return
        for record in sorted(samples, key=lambda item: item.sample_index):
            subjects.append(
                HandoffSubject(
                    scenario_id=scenario.scenario_id,
                    stage=stage,
                    variant=variant,
                    profile=profile,
                    effort=effort,
                    sample_index=record.sample_index,
                    record=record.value,
                )
            )

    for variant in variants:
        for profile, effort in cells:
            _add_subjects("fresh-agent", variant, profile, effort, fresh, "fresh")
    if has_continuation:
        for profile, effort in cells:
            _add_subjects(
                "same-agent",
                "generated-task",
                profile,
                effort,
                same,
                "same",
                key=f"{scenario.scenario_id}:{profile}:{effort}",
            )
    if "generated-plan" in CATEGORIES[scenario.category]["stages"]:
        for profile, effort in cells:
            _add_subjects(
                "fresh-agent",
                "generated-file",
                profile,
                effort,
                generated,
                "generated",
                key=f"{scenario.scenario_id}:{profile}:{effort}",
            )
    if has_control:
        assert control is not None
        _add_subjects(
            "fresh-agent",
            "incomplete",
            control["agent"],
            control["effort"],
            negative,
            "negative",
        )

    if missing and not allow_partial:
        raise FileNotFoundError(
            f"missing handoff records for {scenario.scenario_id}: {missing}"
        )
    return subjects


def subjects_block_reason(subjects: Sequence[HandoffSubject]) -> str | None:
    """Why an assessment case cannot run; ``None`` when it can.

    A case is blocked only when every subject is invalid (or none
    exists); the reason lists each subject's recorded invalid reasons.
    """

    if any(subject.record.get("valid") is True for subject in subjects):
        return None
    if not subjects:
        return "no handoff subjects were found for the cell"
    entries = [
        f"{subject.stage}:{subject.variant}:{subject.profile}:{subject.effort}"
        f" sample {subject.sample_index}: "
        f"{subject.record.get('invalid_reasons')!r}"
        for subject in subjects
    ]
    return "no valid handoff subjects — " + "; ".join(entries)


# The fixed instruction part of the assessment prompt. Per-evaluation
# material is substituted into the $-placeholders; the template itself
# is extracted verbatim into the scenarios export.
HANDOFF_ASSESSMENT_PROMPT_TEMPLATE = Template(
    """\
Assess whether this task handoff and the resulting plan would let another
agent continue correctly without the original conversation or broad
rediscovery.

Use the reviewed target as the authority. Judge the task and plan together:
requirements and approved conditions, verified facts and source pointers,
material decisions and questions, exclusions, dependencies, testing
boundaries, documentation work, and plan status. An omit-plan task must not
contain disguised implementation direction, but the later plan must still be
complete. A retained-plan task should let the later agent reuse the plan rather
than reconstruct it unnecessarily.

Tool-call efficiency is secondary. Interpret it only after plan quality. Do not
reward a low call count when the plan omits outcomes or invents unsupported
behavior.

This is a read-only planning stage. Do not penalize a plan because newly
verified details remain in the response rather than being written back into
the task file; file mutation is prohibited here. Judge whether the presented
plan is complete and whether the durable task was sufficient to produce it.

The `incomplete` variant is an intentional negative control. It should require
more reconstruction or produce lower-quality planning than a complete handoff;
assess the result rather than assuming failure from the label.

The `generated-file` variant is a fresh-session plan made only from another
agent's generated task files: judge whether those files alone let the planning
agent produce a complete plan without broad rediscovery.

Return JSON only:

{
  "schema_version": 2,
  "scenario_id": "$scenario_id",
  "assessment": {
    "stage": "fresh-agent|same-agent",
    "variant": "retain|omit|incomplete|generated-task|generated-file",
    "plan_coverage": "complete|partial|poor",
    "missing_outcomes": ["OUTCOME-ID"],
    "lost_facts_or_decisions": ["description"],
    "invented_scope_or_decisions": ["description"],
    "testing_boundary": "decisive|partial|poor",
    "documentation_boundary": "appropriate|partial|poor",
    "task_self_contained": true,
    "broad_rediscovery": true,
    "handoff_quality_score": 0,
    "efficiency_interpretation": "concise evidence-based interpretation",
    "summary": "concise evidence-based interpretation"
  }
}

Scores are integers from 0 through 100. `broad_rediscovery` is true only when
the agent repeated substantial investigation that a complete task should have
made unnecessary.

Reviewed target:

$target_json

Subject material:

$subject_json
"""
)


def handoff_semantic_prompt(
    scenario: TaskGuidanceScenario,
    subject: HandoffSubject,
) -> str:
    """One per-subject handoff assessment prompt.

    The stage and variant labels stay — the rubric interprets them —
    but the subject material carries the produced work only: no
    producer identity, validity, or tool metrics.
    """

    record = subject.record
    if record.get("valid") is not True:
        raise ValueError("handoff prompt accepts only a valid subject record")
    subject_material = {
        "stage": subject.stage,
        "variant": subject.variant,
        "plan_response": record["response"],
        "task_files": record["task_files"],
    }
    return HANDOFF_ASSESSMENT_PROMPT_TEMPLATE.substitute(
        scenario_id=scenario.scenario_id,
        target_json=json.dumps(scenario.target, indent=2, sort_keys=True),
        subject_json=json.dumps(subject_material, indent=2, sort_keys=True),
    )


def parse_handoff_semantic(text: str) -> dict[str, Any]:
    stripped = text.strip()
    fenced = re.fullmatch(
        r"```(?:json)?\s*(.*?)\s*```",
        stripped,
        flags=re.DOTALL | re.IGNORECASE,
    )
    if fenced:
        stripped = fenced.group(1)
    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start < 0 or end <= start:
            raise
        value = json.loads(stripped[start : end + 1])
    if not isinstance(value, dict):
        raise ValueError("handoff semantic response must be an object")
    return value


def validate_handoff_semantic(
    value: Mapping[str, Any],
    *,
    scenario: TaskGuidanceScenario,
    stage: str,
    variant: str,
) -> None:
    if value.get("schema_version") != HANDOFF_SCHEMA_VERSION:
        raise ValueError(
            f"handoff semantic schema_version must be {HANDOFF_SCHEMA_VERSION}"
        )
    if value.get("scenario_id") != scenario.scenario_id:
        raise ValueError("handoff semantic scenario_id mismatch")
    assessment = value.get("assessment")
    if not isinstance(assessment, Mapping):
        raise ValueError("handoff assessment must be an object")
    if "producer" in assessment or "assessments" in value:
        raise ValueError("handoff response must not echo producer identity or a batch")
    if assessment.get("stage") != stage:
        raise ValueError(f"handoff assessment stage must be {stage!r}")
    if assessment.get("variant") != variant:
        raise ValueError(f"handoff assessment variant must be {variant!r}")
    _choice(assessment, "stage", {"fresh-agent", "same-agent"})
    _choice(
        assessment,
        "variant",
        {"retain", "omit", "incomplete", "generated-task", "generated-file"},
    )
    _choice(assessment, "plan_coverage", {"complete", "partial", "poor"})
    _choice(assessment, "testing_boundary", {"decisive", "partial", "poor"})
    _choice(
        assessment,
        "documentation_boundary",
        {"appropriate", "partial", "poor"},
    )
    for key in (
        "missing_outcomes",
        "lost_facts_or_decisions",
        "invented_scope_or_decisions",
    ):
        if not isinstance(assessment.get(key), list):
            raise ValueError(f"handoff {key} must be a list")
    for key in ("task_self_contained", "broad_rediscovery"):
        if not isinstance(assessment.get(key), bool):
            raise ValueError(f"handoff {key} must be boolean")
    score = assessment.get("handoff_quality_score")
    if not isinstance(score, int) or not 0 <= score <= 100:
        raise ValueError("handoff_quality_score must be 0..100")
    for key in ("efficiency_interpretation", "summary"):
        if not isinstance(assessment.get(key), str):
            raise ValueError(f"handoff {key} must be a string")


def handoff_assessment_record(
    scenario: TaskGuidanceScenario,
    subject: HandoffSubject,
    assessment: Mapping[str, Any],
) -> dict[str, Any]:
    """The saved per-subject handoff assessment record.

    The prompt never reveals the producer; the record keeps the
    subject-to-producer mapping so the judgment stays attributable.
    """

    return {
        "schema_version": HANDOFF_RECORD_VERSION,
        "scenario_id": scenario.scenario_id,
        "subject": {
            "profile": subject.profile,
            "reasoning_effort": subject.effort,
            "sample_index": subject.sample_index,
        },
        "assessment": assessment,
    }


def _scenario_cells(
    cells: Mapping[str, tuple[Any, ...]],
    scenario_id: str,
) -> dict[str, tuple[Any, ...]]:
    prefix = f"{scenario_id}:"
    return {key: records for key, records in cells.items() if key.startswith(prefix)}


def _choice(value: Mapping[str, Any], key: str, choices: set[str]) -> None:
    selected = value.get(key)
    if selected not in choices:
        raise ValueError(f"handoff {key} must be one of {sorted(choices)}")
