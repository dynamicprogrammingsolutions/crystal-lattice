"""The per-subject presented-plan content assessment.

One identity-blind judgment of a single presented plan — the response of
a plan-stage run — against two committed requirement layers: the
scenario's task-specific plan content requirements (the ``plan_target``
in the reviewed target) and the suite-level generic requirements every
human-centered plan must satisfy. The judge answers one question:
would a human reader get from this plan the content that matters?

The judged material is embedded as rendered text — the plan, the
requirement layers, and the approved outcomes — never as a JSON map of
the subject; JSON appears only in the response contract. Producer
identity, validity, and tool metrics stay out of the prompt.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from string import Template
from typing import Any, Mapping, Sequence

from .scenarios import TaskGuidanceScenario
from .handoff_semantic import HandoffSubject

PLAN_CONTENT_RECORD_VERSION = 1

# One generic requirement every presented plan is judged against. The
# grades are ordered best-to-worst; the first is the top grade a
# finding is not required for.
GENERIC_PLAN_REQUIREMENTS: tuple[dict[str, Any], ...] = (
    {
        "id": "GENERIC-1",
        "grades": ("conveyed", "partial", "missing"),
        "requirement": (
            "High-impact decisions, each marked decided or open: the "
            "decisions that shape the work are surfaced — not buried in "
            "steps — each labeled decided (with brief rationale) or open "
            "(as an explicit approval question, with a recommendation "
            "when one exists)."
        ),
    },
    {
        "id": "GENERIC-2",
        "grades": ("conveyed", "partial", "missing"),
        "requirement": (
            "The result at its public boundary before mechanics: what "
            "the finished work produces — behavior, contract, surface "
            "change — so direction and construction are judgeable "
            "separately."
        ),
    },
    {
        "id": "GENERIC-3",
        "grades": ("conveyed", "partial", "missing"),
        "requirement": (
            "What stays untouched and why: existing behavior that must "
            "remain compatible, and scope deliberately excluded."
        ),
    },
    {
        "id": "GENERIC-4",
        "grades": ("conveyed", "partial", "missing"),
        "requirement": (
            "The constraints and assumptions that shaped the approach: "
            "the hard constraints that ruled out alternatives, and the "
            "assumptions relied on with how each could be cheaply "
            "confirmed."
        ),
    },
    {
        "id": "GENERIC-5",
        "grades": ("conveyed", "partial", "missing"),
        "requirement": (
            "Verification with a decisive boundary: what evidence, at "
            "which boundary, would prove the outcomes — and what that "
            "verification deliberately does not cover."
        ),
    },
    {
        "id": "GENERIC-6",
        "grades": ("conveyed", "partial", "missing"),
        "requirement": (
            "Risks, blast radius, and the way back: what could break "
            "and for whom; the reversibility answer — rollback, phases "
            "that keep every step shippable, escape hatches."
        ),
    },
    {
        "id": "GENERIC-7",
        "grades": ("conveyed", "partial", "missing"),
        "requirement": (
            "The logic of the sequence: why the steps are in this order "
            "(dependencies, contract before consumers, risk first) and "
            "the milestones where progress becomes verifiable or usable."
        ),
    },
    {
        "id": "GENERIC-8",
        "grades": ("conveyed", "partial", "missing"),
        "requirement": (
            "What feedback the plan needs from the reader: approvals "
            "wanted, questions needing answers, priorities to confirm — "
            "stated, not implied."
        ),
    },
    {
        "id": "GENERIC-9",
        "grades": ("self-contained", "partial", "external-dependency"),
        "requirement": (
            "Self-containedness: everything needed to evaluate the plan "
            "is in the text — facts stated not referenced; links carry, "
            "never replace (delete every link and code reference, the "
            "plan must still be evaluable); terms introduced at first "
            "use; earlier context restated in decided form; snippets "
            "illustrate while prose asserts; specifics appear as "
            "values. The duty covers evaluation-relevant facts, not "
            "every detail."
        ),
    },
    {
        "id": "GENERIC-10",
        "grades": (
            "proportionate",
            "over-detailed",
        ),
        "requirement": (
            "Depth follows decisions; mechanics stay summarized: "
            "promises with boundaries instead of specifications, "
            "strategy over inventory, public surface over internal "
            "mechanics. Detail earns its place only when changing it "
            "would change the reader's decision."
        ),
    },
)

GENERIC_PLAN_GRADES: dict[str, tuple[str, ...]] = {
    requirement["id"]: tuple(requirement["grades"])
    for requirement in GENERIC_PLAN_REQUIREMENTS
}

PLAN_CONTENT_PROMPT_TEMPLATE = Template(
    """\
Assess the presented plan below — the response one agent produced when
asked to present its implementation plan for a fixed task. Judge what
a human reader of this text alone would get. You are the human reader.

The plan is judged against two requirement layers. Grade every
requirement: `conveyed` when the plan carries the content a reader
needs (briefly is fine), `partial` when some of it is present or it is
present but unclear, `missing` when the reader would not get it. The
two special requirements use their own grades, listed with them.

Rules that apply across all requirements:

- Any requirement graded below its top grade requires a finding: name
  where the plan falls short, concretely, quoting or pointing at the
  passage. An empty finding with a non-top grade is invalid.
- A requirement whose meaning depends on an external resource the
  reader must open grades at most `partial`, however good the resource
  is. Links may carry extra evidence; they must never replace content
  the reader needs.
- Depth must match impact: verbosity is not rewarded, and brevity that
  loses nothing is not penalized.
- Judge content, not formatting. How the plan is typeset is not graded
  here; what it conveys is.

Generic requirements (every plan):

$generic_requirements

Task-specific requirements for this scenario (what a plan for THIS
task must convey):

$task_requirements

Approved outcomes of the scenario (the authority the plan serves; use
them to harvest content the requirement lists may have missed):

$approved_outcomes

Return JSON only with this shape:

{
  "schema_version": 1,
  "scenario_id": "$scenario_id",
  "assessment": {
    "requirements": {
      "REQUIREMENT-ID": {
        "grade": "…",
        "finding": "required unless the grade is top; empty otherwise"
      }
    },
    "missed_requirements": [
      "human-needed content neither layer above asked for, if any"
    ],
    "summary": "concise evidence-based interpretation"
  }
}

Every requirement id from both layers must appear exactly once in
`requirements`.

The presented plan:

$presented_plan
"""
)


def scenario_plan_requirements(
    scenario: TaskGuidanceScenario,
) -> tuple[Mapping[str, Any], ...]:
    """The scenario's task-specific plan content requirements."""

    plan_target = (scenario.target.get("plan_target") or {}).get("required_content", ())
    return tuple(plan_target)


def expected_plan_requirement_ids(
    scenario: TaskGuidanceScenario,
) -> tuple[str, ...]:
    """Every requirement id one judgment must grade, in order."""

    return tuple(
        [str(item.get("id")) for item in scenario_plan_requirements(scenario)]
        + [str(requirement["id"]) for requirement in GENERIC_PLAN_REQUIREMENTS]
    )


def requirement_grades(scenario: TaskGuidanceScenario) -> dict[str, tuple[str, ...]]:
    """The grade scale of every requirement id of one scenario."""

    scales = {
        str(requirement["id"]): tuple(requirement["grades"])
        for requirement in GENERIC_PLAN_REQUIREMENTS
    }
    for item in scenario_plan_requirements(scenario):
        scales[str(item.get("id"))] = ("conveyed", "partial", "missing")
    return scales


def _render_generic_requirements() -> str:
    return "\n".join(
        f"- {requirement['id']} ({'/'.join(requirement['grades'])}): "
        f"{requirement['requirement']}"
        for requirement in GENERIC_PLAN_REQUIREMENTS
    )


def _render_task_requirements(scenario: TaskGuidanceScenario) -> str:
    items = scenario_plan_requirements(scenario)
    if not items:
        return "- (this scenario declares no task-specific requirements)"
    return "\n".join(
        f"- {item.get('id')} (conveyed/partial/missing): {item.get('content')}"
        for item in items
    )


def _render_approved_outcomes(scenario: TaskGuidanceScenario) -> str:
    return "\n".join(
        f"- {outcome.get('id')}: {outcome.get('outcome')}"
        for outcome in scenario.target.get("approved_outcomes", ())
    )


def plan_content_prompt(
    scenario: TaskGuidanceScenario,
    record: Mapping[str, Any],
) -> str:
    """One per-subject presented-plan assessment prompt.

    The subject material is the presented plan text only — no producer
    identity, validity, tool metrics, or variant labels — matching the
    other assessments' blinding. The plan is embedded as text inside a
    fenced block; nothing about the subject travels as JSON.
    """

    if record.get("valid") is not True:
        raise ValueError("plan-content prompt accepts only a valid subject record")
    plan = record["response"]
    if not isinstance(plan, str) or not plan.strip():
        raise ValueError("plan-content subject has no response text")
    return PLAN_CONTENT_PROMPT_TEMPLATE.substitute(
        scenario_id=scenario.scenario_id,
        generic_requirements=_render_generic_requirements(),
        task_requirements=_render_task_requirements(scenario),
        approved_outcomes=_render_approved_outcomes(scenario),
        presented_plan=plan,
    )


def parse_plan_content_response(text: str) -> dict[str, Any]:
    """Parse the model's JSON response, tolerating fenced code blocks."""

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
        raise ValueError("plan-content response must be an object")
    return value


def normalize_plan_content_assessment(
    value: Mapping[str, Any],
    *,
    scenario: TaskGuidanceScenario,
) -> dict[str, Any]:
    """Normalize one parsed response into the saved assessment shape."""

    assessment = value.get("assessment")
    if not isinstance(assessment, Mapping):
        raise ValueError("plan-content response has no assessment object")
    scenario_id = value.get("scenario_id")
    if scenario_id != scenario.scenario_id:
        raise ValueError(
            f"plan-content assessment scenario {scenario_id!r} does not"
            f" match {scenario.scenario_id!r}"
        )
    raw = assessment.get("requirements")
    if not isinstance(raw, Mapping):
        raise ValueError("plan-content assessment has no requirements object")
    expected = expected_plan_requirement_ids(scenario)
    if set(raw) != set(expected):
        missing = sorted(set(expected) - set(raw))
        extra = sorted(set(raw) - set(expected))
        raise ValueError(
            f"plan-content requirements do not match the contract:"
            f" missing={missing}, unexpected={extra}"
        )
    scales = requirement_grades(scenario)
    requirements: dict[str, Any] = {}
    for requirement_id in expected:
        entry = raw[requirement_id]
        if not isinstance(entry, Mapping):
            raise ValueError(f"requirement {requirement_id!r} is not an object")
        grade = entry.get("grade")
        grades = scales[requirement_id]
        if grade not in grades:
            raise ValueError(
                f"requirement {requirement_id!r} grade {grade!r} not in {grades}"
            )
        finding = str(entry.get("finding", "")).strip()
        if grade != grades[0] and not finding:
            raise ValueError(
                f"requirement {requirement_id!r} graded {grade!r} without a finding"
            )
        requirements[requirement_id] = {"grade": grade, "finding": finding}
    missed = assessment.get("missed_requirements", [])
    if not isinstance(missed, list) or any(
        not isinstance(item, str) for item in missed
    ):
        raise ValueError("plan-content missed_requirements must be a string list")
    return {
        "schema_version": PLAN_CONTENT_RECORD_VERSION,
        "scenario_id": scenario_id,
        "requirements": requirements,
        "missed_requirements": [str(item) for item in missed],
        "summary": str(assessment.get("summary", "")).strip(),
    }


def validate_plan_content_assessment(
    value: Mapping[str, Any],
    *,
    scenario: TaskGuidanceScenario,
) -> None:
    """Assert the normalized assessment is complete and self-consistent."""

    if value.get("schema_version") != PLAN_CONTENT_RECORD_VERSION:
        raise ValueError("unexpected plan-content assessment schema version")
    expected = expected_plan_requirement_ids(scenario)
    requirements = value.get("requirements")
    if not isinstance(requirements, Mapping) or set(requirements) != set(expected):
        raise ValueError("plan-content requirements do not match the contract")
    scales = requirement_grades(scenario)
    for requirement_id in expected:
        entry = requirements[requirement_id]
        if entry["grade"] not in scales[requirement_id]:
            raise ValueError(f"requirement {requirement_id!r} has an invalid grade")
        if entry["grade"] != scales[requirement_id][0] and not entry["finding"]:
            raise ValueError(
                f"requirement {requirement_id!r} non-top grade lacks a finding"
            )


def plan_content_record(
    scenario: TaskGuidanceScenario,
    subject: HandoffSubject,
    assessment: Mapping[str, Any],
) -> dict[str, Any]:
    """The saved per-subject plan-content record.

    The prompt never reveals the producer or the variant; the record
    keeps the subject-to-producer mapping and the stage/variant labels
    so the judgment stays attributable and collectable.
    """

    scales = requirement_grades(scenario)
    requirements = assessment["requirements"]
    top = sum(
        1
        for requirement_id, grades in scales.items()
        if requirements.get(requirement_id, {}).get("grade") == grades[0]
    )
    coverage = round(top / len(scales), 3) if scales else 0.0
    return {
        "schema_version": PLAN_CONTENT_RECORD_VERSION,
        "scenario_id": scenario.scenario_id,
        "subject": {
            "profile": subject.profile,
            "reasoning_effort": subject.effort,
            "sample_index": subject.sample_index,
        },
        "assessment": {
            "stage": subject.stage,
            "variant": subject.variant,
            "requirements": requirements,
            "missed_requirements": list(assessment["missed_requirements"]),
            "coverage": coverage,
            "summary": assessment["summary"],
        },
        "summary": _plan_content_summary(subject, coverage, requirements),
    }


def _plan_content_summary(
    subject: HandoffSubject, coverage: float, requirements: Mapping[str, Any]
) -> str:
    gaps = sorted(
        requirement_id
        for requirement_id, entry in requirements.items()
        if entry.get("grade")
        not in (None, "conveyed", "self-contained", "proportionate")
    )
    gap_text = ", ".join(gaps) if gaps else "no gaps"
    return f"[{subject.variant}] top-grade coverage {coverage:.0%}; gaps: {gap_text}"


def aggregate_plan_content(
    records: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Aggregate grades across one collection of plan-content records."""

    if not records:
        return {"assessment_count": 0, "requirements": {}}
    requirements: dict[str, Any] = {}
    grade_sets: dict[str, set[str]] = {}
    ids = sorted(
        {
            requirement_id
            for record in records
            for requirement_id in (
                (record.get("assessment") or {}).get("requirements") or {}
            )
        }
    )
    for requirement_id in ids:
        grades = [
            (record.get("assessment") or {})
            .get("requirements", {})
            .get(requirement_id, {})
            for record in records
        ]
        grades = [entry.get("grade") for entry in grades if isinstance(entry, Mapping)]
        counts = Counter(str(grade) for grade in grades if grade is not None)
        grade_sets[requirement_id] = {str(grade) for grade in counts}
        requirements[requirement_id] = {
            "grade_counts": dict(counts),
            "judged": len(grades),
        }
    coverages = [
        (record.get("assessment") or {}).get("coverage")
        for record in records
        if isinstance(record.get("assessment"), Mapping)
        and record["assessment"].get("coverage") is not None
    ]
    return {
        "assessment_count": len(records),
        "requirements": requirements,
        "mean_coverage": (
            round(sum(coverages) / len(coverages), 3) if coverages else None
        ),
        "zero_variance_requirements": sorted(
            requirement_id
            for requirement_id, grades in grade_sets.items()
            if len(grades) == 1
        ),
    }
