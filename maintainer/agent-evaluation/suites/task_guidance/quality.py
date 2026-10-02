"""The per-subject task-file quality assessment.

A separate identity-blind assessment of one producer subject that judges
task-file quality dimensions the decomposition assessment does not score:
whether the execution plan expresses the decided design, whether the file
preserves the conversation's durable context, whether a human reviewer can
find things, whether content sits in the right section, whether a plan is
justified by actual planning, and whether the file fits the kind of work.

Every dimension is phrased as a positive completeness property with a few
ordered grades; nothing bans a shape mechanically.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from string import Template
from typing import Any, Mapping, Sequence

from .scenarios import TaskGuidanceScenario
from .semantic import ProducerSubject

QUALITY_RECORD_VERSION = 1

# Grades are ordered best-to-worst for every dimension.
QUALITY_DIMENSIONS: dict[str, tuple[str, ...]] = {
    "plan_design_completeness": ("complete", "partial", "poor"),
    "durable_context_preservation": ("complete", "partial", "poor"),
    "findability": ("complete", "partial", "poor"),
    "section_appropriateness": ("complete", "partial", "poor"),
    "plan_justification": ("justified", "not_applicable", "fabricated"),
    "task_kind_fit": ("fits", "forced", "missing"),
}

TASK_QUALITY_ASSESSMENT_PROMPT_TEMPLATE = Template(
    """\
Assess the task files one agent produced for a fixed scenario, together
with that agent's final conversation response. The response and the files
are the complete evidence; judge what a reader of the files alone would
get.

Judge quality as completeness properties, not shape rules:

- `plan_design_completeness`: a reader of the execution plan alone can
  reconstruct the decided design — component responsibilities, interfaces
  or data flow, compatibility and dependency states, material decisions,
  and how the requirements are verified. An ordered list of work steps
  without the design behind it is `poor`; a plan covering some design
  elements is `partial`.
- `durable_context_preservation`: every approved outcome, material
  decision, verified fact with its source, and verification approach the
  conversation established appears in the task files — compressed, not
  dropped. List dropped material as occurrences. Use `not checked here`
  only when the conversation established nothing durable.
- `findability`: a reviewer can locate the outcome, the design,
  responsibility boundaries, dependencies, open questions, and decisive
  evidence without reading whole sections. Dense unbroken prose and very
  long list items that mix several facts reduce this.
- `section_appropriateness`: content sits where a continuing agent looks
  for it — outcomes and constraints in requirements, rationale and
  learned facts in supporting details, direction in the execution plan,
  unresolved items in questions and decisions.
- `plan_justification`: the execution plan reflects planning that
  actually happened. `justified` when the plan restates or organizes the
  conversation's planning; `not_applicable` when no execution plan
  exists; `fabricated` when the plan asserts design detail the
  conversation never established.
- `task_kind_fit`: the file uses the sections the work needs and states
  acceptance evidence appropriate to the work's kind — tests for code,
  review acceptance for documentation, rollback and verification for
  operations, brief or style acceptance for content. `forced` when
  inapplicable sections are filled mechanically; `missing` when the
  work's own acceptance evidence is absent.

Do not reward verbosity, tables, or formatting of its own. Do not
penalize brevity that loses nothing. The target and the natural user
request define what is material.

Return JSON only with this shape:

{
  "schema_version": 1,
  "scenario_id": "$scenario_id",
  "assessment": {
    "task_kind": "development|documentation|operations|content|other",
    "dimensions": {
      "plan_design_completeness": {
        "grade": "complete|partial|poor",
        "occurrences": [
          {"description": "what is missing or present", "evidence": "quote or reference"}
        ]
      },
      "durable_context_preservation": {
        "grade": "complete|partial|poor",
        "occurrences": []
      },
      "findability": {
        "grade": "complete|partial|poor",
        "occurrences": []
      },
      "section_appropriateness": {
        "grade": "complete|partial|poor",
        "occurrences": []
      },
      "plan_justification": {
        "grade": "justified|not_applicable|fabricated",
        "occurrences": []
      },
      "task_kind_fit": {
        "grade": "fits|forced|missing",
        "occurrences": []
      }
    },
    "summary": "concise evidence-based interpretation"
  }
}

Occurrence lists carry concrete gaps or exemplary strengths; an empty list
with a top grade is valid.

Reviewed target:

$target_json

Natural user request:

$prompt

Subject material:

$subject_json
"""
)


def quality_prompt(
    scenario: TaskGuidanceScenario,
    record: Mapping[str, Any],
) -> str:
    """One per-subject quality assessment prompt.

    The subject material is the produced work only — no producer
    identity, validity, or tool metrics — matching the decomposition
    assessment's blinding.
    """

    if record.get("valid") is not True:
        raise ValueError("quality prompt accepts only a valid subject record")
    subject_material = {
        "response": record["response"],
        "task_files": record["task_files"],
        "task_tree": record["task_tree"],
    }
    return TASK_QUALITY_ASSESSMENT_PROMPT_TEMPLATE.substitute(
        scenario_id=scenario.scenario_id,
        target_json=json.dumps(scenario.target, indent=2, sort_keys=True),
        prompt=scenario.prompt,
        subject_json=json.dumps(subject_material, indent=2, sort_keys=True),
    )


def parse_quality_response(text: str) -> dict[str, Any]:
    """Parse the model's JSON response, tolerating fenced code blocks."""

    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("quality response contains no JSON object")
    value = json.loads(match.group(0))
    if not isinstance(value, dict):
        raise ValueError("quality response is not an object")
    return value


def normalize_quality_assessment(
    value: Mapping[str, Any],
    *,
    record: Mapping[str, Any],
) -> dict[str, Any]:
    """Normalize one parsed response into the saved assessment shape."""

    assessment = value.get("assessment")
    if not isinstance(assessment, Mapping):
        raise ValueError("quality response has no assessment object")
    dimensions: dict[str, Any] = {}
    raw = assessment.get("dimensions")
    if not isinstance(raw, Mapping):
        raise ValueError("quality assessment has no dimensions object")
    for name, grades in QUALITY_DIMENSIONS.items():
        entry = raw.get(name)
        if not isinstance(entry, Mapping):
            raise ValueError(f"quality assessment misses dimension {name!r}")
        grade = entry.get("grade")
        if grade not in grades:
            raise ValueError(
                f"quality dimension {name!r} grade {grade!r} not in {grades}"
            )
        occurrences = entry.get("occurrences", [])
        if not isinstance(occurrences, list):
            raise ValueError(f"quality dimension {name!r} occurrences not a list")
        dimensions[name] = {
            "grade": grade,
            "occurrences": occurrences,
        }
    task_kind = assessment.get("task_kind")
    if not isinstance(task_kind, str) or not task_kind:
        task_kind = "other"
    scenario_id = value.get("scenario_id")
    if scenario_id != record.get("scenario_id"):
        raise ValueError(
            f"quality assessment scenario {scenario_id!r} does not match subject"
        )
    return {
        "schema_version": QUALITY_RECORD_VERSION,
        "scenario_id": scenario_id,
        "task_kind": task_kind,
        "dimensions": dimensions,
        "summary": str(assessment.get("summary", "")).strip(),
    }


def validate_quality_assessment(value: Mapping[str, Any]) -> None:
    """Assert the normalized assessment is complete and self-consistent."""

    if value.get("schema_version") != QUALITY_RECORD_VERSION:
        raise ValueError("unexpected quality assessment schema version")
    dimensions = value.get("dimensions")
    if not isinstance(dimensions, Mapping) or set(dimensions) != set(
        QUALITY_DIMENSIONS
    ):
        raise ValueError("quality assessment dimensions do not match the contract")
    for name, grades in QUALITY_DIMENSIONS.items():
        if dimensions[name]["grade"] not in grades:
            raise ValueError(f"quality dimension {name!r} has an invalid grade")


def quality_record(
    scenario: TaskGuidanceScenario,
    subject: ProducerSubject,
    assessment: Mapping[str, Any],
) -> dict[str, Any]:
    """The saved per-subject quality record.

    The prompt never reveals the producer; the record keeps the
    subject-to-producer mapping so the judgment stays attributable.
    """

    return {
        "schema_version": QUALITY_RECORD_VERSION,
        "scenario_id": scenario.scenario_id,
        "subject": {
            "profile": subject.profile,
            "reasoning_effort": subject.effort,
            "sample_index": subject.sample_index,
        },
        "assessment": dict(assessment),
        "summary": quality_summary(assessment),
    }


def quality_summary(assessment: Mapping[str, Any]) -> str:
    dimensions = assessment.get("dimensions", {})
    grades = [
        f"{name}={dimensions[name]['grade']}"
        for name in QUALITY_DIMENSIONS
        if name in dimensions
    ]
    kind = assessment.get("task_kind", "other")
    return f"[{kind}] " + ", ".join(grades)


def aggregate_quality_dimensions(
    assessments: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Aggregate the quality grades across one collection of subjects."""

    if not assessments:
        return {"assessment_count": 0, "dimensions": {}}
    dimensions: dict[str, Any] = {}
    for name, grades in QUALITY_DIMENSIONS.items():
        counts = Counter(
            str(assessment["dimensions"][name]["grade"])
            for assessment in assessments
            if name in assessment.get("dimensions", {})
        )
        top = grades[0]
        occurrences = sum(
            len(assessment["dimensions"][name].get("occurrences", []))
            for assessment in assessments
            if name in assessment.get("dimensions", {})
        )
        dimensions[name] = {
            "grade_counts": dict(counts),
            "top_grade_share": round(counts.get(top, 0) / len(assessments), 3),
            "occurrence_count": occurrences,
        }
    return {
        "assessment_count": len(assessments),
        "dimensions": dimensions,
    }
