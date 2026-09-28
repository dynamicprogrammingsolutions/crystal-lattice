"""The reworked task-file assessments: fidelity and readability.

Two focused identity-blind judges replace the six-dimension task-quality
assessment. The fidelity judge asks whether the files carry the
conversation's decided design and durable context, justified by real
planning, in the right sections, with kind-appropriate acceptance
evidence. The readability judge asks how easily a human reader can work
with each section of the files, anchored on measured structure facts.

Both use the findings contract: every grade carries concrete
``{where, quote, why}`` findings, a non-top grade without findings is an
invalid judgment, and every response harvests mistakes — the judge's
search is defect-oriented while the grades stay completeness-oriented.
Judged material is embedded as rendered text (fenced markdown with path
headers); JSON appears only in the response contract. No producer
identity, validity, or tool metrics reach a prompt, and nothing
prescribes formatting elements — tables, lists, and snippets are tools
among many.
"""

from __future__ import annotations

import json
import re
from collections import Counter
from string import Template
from typing import Any, Mapping, Sequence

from .scenarios import TaskGuidanceScenario
from .semantic import ProducerSubject
from .structure import profile_sections

FILE_FIDELITY_RECORD_VERSION = 1
FILE_READABILITY_RECORD_VERSION = 1

# The fidelity dimensions moved unchanged from the task-quality
# assessment; grades are ordered best-to-worst.
FIDELITY_DIMENSIONS: dict[str, tuple[str, ...]] = {
    "plan_design_completeness": ("complete", "partial", "poor"),
    "durable_context_preservation": ("complete", "partial", "poor"),
    "section_appropriateness": ("complete", "partial", "poor"),
    "plan_justification": ("justified", "not_applicable", "fabricated"),
    "task_kind_fit": ("fits", "forced", "missing"),
}

READABILITY_SECTION_GRADES = ("readable", "partial", "unreadable")
READABILITY_NAVIGATION_GRADES = ("navigable", "partial", "confusing")

_FINDING_KEYS = ("where", "quote", "why")


def quality_target_excerpt(scenario: TaskGuidanceScenario) -> str:
    """The quality-relevant excerpt of the reviewed target, as text.

    The decomposition machinery (partition sizes, coherent deliverables,
    crossings, handoff plans) is noise for file-quality questions; the
    excerpt keeps what a fidelity or readability judgment is measured
    against.
    """

    target = scenario.target
    lines = [
        f"# {target.get('title', '')}",
        "",
        str(target.get("task_summary", "")),
        "",
        f"Category: {target.get('category')}",
    ]
    task_kind = target.get("task_kind")
    if task_kind:
        lines.append(f"Task kind: {task_kind}")
    applicable = target.get("applicable_sections")
    if applicable:
        lines.append(
            "Applicable sections: " + "; ".join(str(item) for item in applicable)
        )
    evidence = target.get("acceptance_evidence")
    if evidence:
        lines.append(f"Acceptance evidence: {evidence}")
    lines.extend(["", "Approved outcomes:", ""])
    for outcome in target.get("approved_outcomes", ()):
        lines.append(f"- {outcome.get('id')}: {outcome.get('outcome')}")
    for heading, key in (
        ("Open questions", "open_questions"),
        ("Acceptable alternatives", "acceptable_alternatives"),
    ):
        values = target.get(key) or []
        if values:
            lines.extend(["", f"{heading}:", ""])
            lines.extend(f"- {item}" for item in values)
    return "\n".join(lines)


def _render_task_files(task_files: Mapping[str, str]) -> str:
    parts = []
    for path, text in sorted(task_files.items()):
        parts.append(f"### {path}\n\n````markdown\n{text.strip()}\n````")
    return "\n\n".join(parts)


def _render_findings(findings: Sequence[Mapping[str, Any]] | None) -> list[dict]:
    rendered = []
    for item in findings or ():
        if not isinstance(item, Mapping):
            continue
        rendered.append({key: str(item.get(key, "")) for key in _FINDING_KEYS})
    return rendered


def _normalize_findings(
    value: Mapping[str, Any], *, context: str
) -> list[dict[str, str]]:
    raw = value.get("findings", [])
    if not isinstance(raw, list):
        raise ValueError(f"{context} findings must be a list")
    findings = _render_findings(raw)
    for item in findings:
        if not item["where"].strip() or not item["why"].strip():
            raise ValueError(f"{context} finding needs at least where and why")
    return findings


def _require_findings_for_grade(
    findings: Sequence[Mapping[str, Any]], grade: str, top: str, context: str
) -> None:
    if grade != top and not findings:
        raise ValueError(f"{context} graded {grade!r} without findings")


def _parse_json_object(text: str) -> dict[str, Any]:
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
        raise ValueError("file-quality response must be an object")
    return value


def parse_file_fidelity(text: str) -> dict[str, Any]:
    """Parse the fidelity judge's JSON response."""

    return _parse_json_object(text)


def parse_file_readability(text: str) -> dict[str, Any]:
    """Parse the readability judge's JSON response."""

    return _parse_json_object(text)


# ---------------------------------------------------------------------------
# Fidelity assessment
# ---------------------------------------------------------------------------

FILE_FIDELITY_PROMPT_TEMPLATE = Template(
    """\
Assess the task files one agent produced for a fixed scenario, together
with that agent's final conversation response. Judge whether the files
carry what a continuing agent and a human reviewer need: the decided
design, the conversation's durable context, content in the right
sections, a plan justified by planning that actually happened, and
acceptance evidence that fits the work's kind.

Grade these dimensions:

- `plan_design_completeness`: a reader of the implementation plan alone
  can reconstruct the decided design — component responsibilities,
  interfaces or data flow, compatibility and dependency states, material
  decisions, and how the requirements are verified. An ordered list of
  work steps without the design behind it is `poor`; covering some
  design elements is `partial`.
- `durable_context_preservation`: every approved outcome, material
  decision, verified fact with its source, and verification approach the
  conversation established appears in the task files — compressed, not
  dropped. Use `not checked here` only when the conversation established
  nothing durable.
- `section_appropriateness`: content sits where a continuing agent looks
  for it — outcomes and constraints in requirements, rationale and
  learned facts in supporting details, direction in the implementation
  plan, unresolved items in questions and decisions.
- `plan_justification`: the implementation plan reflects planning that
  actually happened. `justified` when the plan restates or organizes the
  conversation's planning; `not_applicable` when no plan section exists;
  `fabricated` when the plan asserts design detail the conversation
  never established.
- `task_kind_fit`: the file uses the sections the work needs and states
  acceptance evidence appropriate to the work's kind — tests for code,
  review acceptance for documentation, rollback and verification for
  operations, brief or style acceptance for content, recorded decisions
  for tracking work. `forced` when inapplicable sections are filled
  mechanically; `missing` when the work's own acceptance evidence is
  absent.

Every grade carries findings: concrete `{where, quote, why}` items
backing it. A non-top grade with empty findings is invalid. Then hunt
for mistakes explicitly — dropped facts, invented decisions or scope,
content a continuing agent would look for in the wrong place, missing
acceptance evidence — and list each as `{where, quote, why}` in
`mistakes`. Grades stay completeness judgments; the mistake hunt is
your search strategy, not a grade.

Do not reward verbosity or formatting of its own. Do not penalize
brevity that loses nothing. The target excerpt and the natural user
request define what is material.

Return JSON only:

{
  "schema_version": 1,
  "scenario_id": "$scenario_id",
  "assessment": {
    "dimensions": {
      "plan_design_completeness": {
        "grade": "complete|partial|poor",
        "findings": [{"where": "...", "quote": "...", "why": "..."}]
      },
      "durable_context_preservation": {"grade": "...", "findings": []},
      "section_appropriateness": {"grade": "...", "findings": []},
      "plan_justification": {
        "grade": "justified|not_applicable|fabricated",
        "findings": []
      },
      "task_kind_fit": {"grade": "fits|forced|missing", "findings": []}
    },
    "mistakes": [{"where": "...", "quote": "...", "why": "..."}],
    "summary": "concise evidence-based interpretation"
  }
}

Reviewed target excerpt:

$target_excerpt

Natural user request:

$prompt

The producer's final conversation response (the durable-context source
the files must preserve):

$conversation

The produced task files:

$task_files
"""
)


def file_fidelity_prompt(
    scenario: TaskGuidanceScenario,
    record: Mapping[str, Any],
) -> str:
    """One per-subject fidelity prompt: embedded text, no identity."""

    if record.get("valid") is not True:
        raise ValueError("fidelity prompt accepts only a valid subject record")
    return FILE_FIDELITY_PROMPT_TEMPLATE.substitute(
        scenario_id=scenario.scenario_id,
        target_excerpt=quality_target_excerpt(scenario),
        prompt=scenario.prompt,
        conversation=_fence(record.get("response", "")),
        task_files=_render_task_files(record.get("task_files", {})),
    )


def _fence(text: str) -> str:
    return f"````markdown\n{str(text).strip()}\n````"


def normalize_file_fidelity(
    value: Mapping[str, Any],
    *,
    scenario: TaskGuidanceScenario,
) -> dict[str, Any]:
    """Normalize one parsed fidelity response into the saved shape."""

    assessment = value.get("assessment")
    if not isinstance(assessment, Mapping):
        raise ValueError("fidelity response has no assessment object")
    scenario_id = value.get("scenario_id")
    if scenario_id != scenario.scenario_id:
        raise ValueError(
            f"fidelity assessment scenario {scenario_id!r} does not"
            f" match {scenario.scenario_id!r}"
        )
    raw = assessment.get("dimensions")
    if not isinstance(raw, Mapping) or set(raw) != set(FIDELITY_DIMENSIONS):
        raise ValueError("fidelity dimensions do not match the contract")
    dimensions: dict[str, Any] = {}
    for name, grades in FIDELITY_DIMENSIONS.items():
        entry = raw[name]
        if not isinstance(entry, Mapping):
            raise ValueError(f"fidelity dimension {name!r} is not an object")
        grade = entry.get("grade")
        if grade not in grades:
            raise ValueError(
                f"fidelity dimension {name!r} grade {grade!r} not in {grades}"
            )
        findings = _normalize_findings(entry, context=f"fidelity {name}")
        _require_findings_for_grade(findings, grade, grades[0], f"fidelity {name}")
        dimensions[name] = {"grade": grade, "findings": findings}
    mistakes = assessment.get("mistakes", [])
    if not isinstance(mistakes, list):
        raise ValueError("fidelity mistakes must be a list")
    return {
        "schema_version": FILE_FIDELITY_RECORD_VERSION,
        "scenario_id": scenario_id,
        "dimensions": dimensions,
        "mistakes": _render_findings(mistakes),
        "summary": str(assessment.get("summary", "")).strip(),
    }


def validate_file_fidelity(value: Mapping[str, Any]) -> None:
    """Assert the normalized fidelity assessment is complete."""

    if value.get("schema_version") != FILE_FIDELITY_RECORD_VERSION:
        raise ValueError("unexpected fidelity assessment schema version")
    dimensions = value.get("dimensions")
    if not isinstance(dimensions, Mapping) or set(dimensions) != set(
        FIDELITY_DIMENSIONS
    ):
        raise ValueError("fidelity dimensions do not match the contract")
    for name, grades in FIDELITY_DIMENSIONS.items():
        entry = dimensions[name]
        if entry["grade"] not in grades:
            raise ValueError(f"fidelity dimension {name!r} has an invalid grade")
        if entry["grade"] != grades[0] and not entry["findings"]:
            raise ValueError(
                f"fidelity dimension {name!r} non-top grade lacks findings"
            )


def file_fidelity_record(
    scenario: TaskGuidanceScenario,
    subject: ProducerSubject,
    assessment: Mapping[str, Any],
) -> dict[str, Any]:
    """The saved per-subject fidelity record with producer attribution."""

    return {
        "schema_version": FILE_FIDELITY_RECORD_VERSION,
        "scenario_id": scenario.scenario_id,
        "subject": {
            "profile": subject.profile,
            "reasoning_effort": subject.effort,
            "sample_index": subject.sample_index,
        },
        "assessment": dict(assessment),
        "summary": _fidelity_summary(assessment),
    }


def _fidelity_summary(assessment: Mapping[str, Any]) -> str:
    dimensions = assessment.get("dimensions", {})
    grades = [
        f"{name}={dimensions[name]['grade']}"
        for name in FIDELITY_DIMENSIONS
        if name in dimensions
    ]
    mistakes = len(assessment.get("mistakes", ()))
    return ", ".join(grades) + f"; mistakes={mistakes}"


def aggregate_file_fidelity(
    assessments: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Aggregate fidelity grades and mistake counts across subjects."""

    if not assessments:
        return {"assessment_count": 0, "dimensions": {}, "mistake_count": 0}
    dimensions: dict[str, Any] = {}
    for name, grades in FIDELITY_DIMENSIONS.items():
        counts = Counter(
            str(assessment["dimensions"][name]["grade"])
            for assessment in assessments
            if name in assessment.get("dimensions", {})
        )
        dimensions[name] = {
            "grade_counts": dict(counts),
            "top_grade_share": round(counts.get(grades[0], 0) / len(assessments), 3),
        }
    return {
        "assessment_count": len(assessments),
        "dimensions": dimensions,
        "mistake_count": sum(
            len(assessment.get("mistakes", ())) for assessment in assessments
        ),
    }


# ---------------------------------------------------------------------------
# Readability assessment
# ---------------------------------------------------------------------------

FILE_READABILITY_PROMPT_TEMPLATE = Template(
    """\
Assess how easily a human reader can work with the task files below.
You are that reader: a maintainer who must find, understand, and act on
what the files say. Judge every top-level section that is present; do
not invent sections that are absent, and do not grade files or sections
that do not appear.

Grade each present top-level section `readable`, `partial`, or
`unreadable`: can a reader take in that section's content with
reasonable effort — scan it, hold it, and use it? A section is
`unreadable` when a reader must re-read dense prose or wall-like list
items to extract what matters; `partial` when parts strain the reader.

Then grade the whole file's navigation `navigable`, `partial`, or
`confusing`: can a reader find the thing they are looking for — the
outcome, the constraint, the open question, the plan status — from the
file's structure alone?

Measured structure facts are provided per section; anchor on these
numbers rather than impressions. They are facts, not rules: no shape is
banned or required. Formatting elements — tables, ordered lists, code
snippets, short paragraphs — are tools among many; what is graded is
the reader's experience, never the presence of a specific element.

Every grade carries findings: concrete `{where, quote, why}` items. A
non-top grade with empty findings is invalid. Then hunt for
presentation mistakes explicitly — prose walls, list items that mix
several facts, buried load-bearing facts, headings that do not match
their content, walls of unchecked boxes — and list each as
`{where, quote, why}` in `mistakes`.

Depth must match impact: a short section is not a defect; a dense
section is not automatically one either. Verbosity is not rewarded;
brevity that loses nothing is not penalized.

Return JSON only:

{
  "schema_version": 1,
  "scenario_id": "$scenario_id",
  "assessment": {
    "sections": {
      "SECTION TITLE": {
        "grade": "readable|partial|unreadable",
        "findings": [{"where": "...", "quote": "...", "why": "..."}]
      }
    },
    "navigation": {"grade": "navigable|partial|confusing", "findings": []},
    "mistakes": [{"where": "...", "quote": "...", "why": "..."}],
    "summary": "concise evidence-based interpretation"
  }
}

`sections` contains exactly the top-level sections listed in the
measured facts, keyed by the exact Section values of that table
(`<file path> — <section title>`), so multi-file task sets stay
addressable.

What these files are for:

$context_excerpt

Measured structure facts (per file, per top-level section):

$structure_facts

The produced task files:

$task_files
"""
)


def _render_structure_facts(task_files: Mapping[str, str]) -> str:
    lines = []
    for entry in profile_sections(task_files):
        lines.append(f"#### {entry['file']}")
        lines.append("")
        lines.append(
            "| Section | Words | Paragraphs | Longest paragraph | List items | Longest item | Subsections | Tables | Fenced blocks | Code spans |"
        )
        lines.append("|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|")
        for section in entry["sections"]:
            lines.append(
                f"| {section['key']} | {section['words']}"
                f" | {section['paragraph_count']}"
                f" | {section['longest_paragraph_words']}"
                f" | {section['list_item_count']}"
                f" | {section['longest_list_item_words']}"
                f" | {section['subsection_count']}"
                f" | {section['table_row_count']}"
                f" | {section['fenced_block_count']}"
                f" | {section['code_span_count']} |"
            )
        lines.append("")
    return "\n".join(lines).rstrip()


def _readability_context_excerpt(scenario: TaskGuidanceScenario) -> str:
    target = scenario.target
    lines = [
        f"# {target.get('title', '')}",
        "",
        str(target.get("task_summary", "")),
        "",
        f"Category: {target.get('category')}",
    ]
    task_kind = target.get("task_kind")
    if task_kind:
        lines.append(f"Task kind: {task_kind}")
    return "\n".join(lines)


def expected_section_keys(task_files: Mapping[str, str]) -> tuple[str, ...]:
    """Every top-level section key across the files, in file order.

    Keys are `<file path> — <section title>`: with multi-file task sets
    the same section title appears in several files, so the file path
    keeps every judged section addressable and the response contract
    deterministic.
    """

    keys: list[str] = []
    for entry in profile_sections(task_files):
        keys.extend(section["key"] for section in entry["sections"])
    return tuple(keys)


def file_readability_prompt(
    scenario: TaskGuidanceScenario,
    record: Mapping[str, Any],
) -> str:
    """One per-subject readability prompt: embedded text, no identity."""

    if record.get("valid") is not True:
        raise ValueError("readability prompt accepts only a valid subject record")
    return FILE_READABILITY_PROMPT_TEMPLATE.substitute(
        scenario_id=scenario.scenario_id,
        context_excerpt=_readability_context_excerpt(scenario),
        structure_facts=_render_structure_facts(record.get("task_files", {})),
        task_files=_render_task_files(record.get("task_files", {})),
    )


def normalize_file_readability(
    value: Mapping[str, Any],
    *,
    scenario: TaskGuidanceScenario,
    record: Mapping[str, Any],
) -> dict[str, Any]:
    """Normalize one parsed readability response into the saved shape."""

    assessment = value.get("assessment")
    if not isinstance(assessment, Mapping):
        raise ValueError("readability response has no assessment object")
    scenario_id = value.get("scenario_id")
    if scenario_id != scenario.scenario_id:
        raise ValueError(
            f"readability assessment scenario {scenario_id!r} does not"
            f" match {scenario.scenario_id!r}"
        )
    raw = assessment.get("sections")
    if not isinstance(raw, Mapping):
        raise ValueError("readability assessment has no sections object")
    expected = expected_section_keys(record.get("task_files", {}))
    if not expected:
        raise ValueError("readability assessment requires sections to judge")
    if set(raw) != set(expected):
        missing = sorted(set(expected) - set(raw))
        extra = sorted(set(raw) - set(expected))
        raise ValueError(
            f"readability sections do not match the files:"
            f" missing={missing}, unexpected={extra}"
        )
    sections: dict[str, Any] = {}
    for title in expected:
        entry = raw[title]
        if not isinstance(entry, Mapping):
            raise ValueError(f"readability section {title!r} is not an object")
        grade = entry.get("grade")
        if grade not in READABILITY_SECTION_GRADES:
            raise ValueError(
                f"readability section {title!r} grade {grade!r} not in"
                f" {READABILITY_SECTION_GRADES}"
            )
        findings = _normalize_findings(entry, context=f"readability {title!r}")
        _require_findings_for_grade(
            findings, grade, READABILITY_SECTION_GRADES[0], f"readability {title!r}"
        )
        sections[title] = {"grade": grade, "findings": findings}
    navigation = assessment.get("navigation")
    if not isinstance(navigation, Mapping):
        raise ValueError("readability assessment has no navigation object")
    nav_grade = navigation.get("grade")
    if nav_grade not in READABILITY_NAVIGATION_GRADES:
        raise ValueError(
            f"readability navigation grade {nav_grade!r} not in"
            f" {READABILITY_NAVIGATION_GRADES}"
        )
    nav_findings = _normalize_findings(navigation, context="readability navigation")
    _require_findings_for_grade(
        nav_findings,
        nav_grade,
        READABILITY_NAVIGATION_GRADES[0],
        "readability navigation",
    )
    mistakes = assessment.get("mistakes", [])
    if not isinstance(mistakes, list):
        raise ValueError("readability mistakes must be a list")
    return {
        "schema_version": FILE_READABILITY_RECORD_VERSION,
        "scenario_id": scenario_id,
        "sections": sections,
        "navigation": {"grade": nav_grade, "findings": nav_findings},
        "mistakes": _render_findings(mistakes),
        "summary": str(assessment.get("summary", "")).strip(),
    }


def validate_file_readability(value: Mapping[str, Any]) -> None:
    """Assert the normalized readability assessment is complete."""

    if value.get("schema_version") != FILE_READABILITY_RECORD_VERSION:
        raise ValueError("unexpected readability assessment schema version")
    sections = value.get("sections")
    navigation = value.get("navigation")
    if not isinstance(sections, Mapping) or not sections:
        raise ValueError("readability sections do not match the contract")
    if not isinstance(navigation, Mapping):
        raise ValueError("readability navigation does not match the contract")
    for title, entry in sections.items():
        if entry["grade"] not in READABILITY_SECTION_GRADES:
            raise ValueError(f"readability section {title!r} has an invalid grade")
        if entry["grade"] != READABILITY_SECTION_GRADES[0] and not entry["findings"]:
            raise ValueError(
                f"readability section {title!r} non-top grade lacks findings"
            )
    if navigation["grade"] not in READABILITY_NAVIGATION_GRADES:
        raise ValueError("readability navigation has an invalid grade")
    if (
        navigation["grade"] != READABILITY_NAVIGATION_GRADES[0]
        and not navigation["findings"]
    ):
        raise ValueError("readability navigation non-top grade lacks findings")


def file_readability_record(
    scenario: TaskGuidanceScenario,
    subject: ProducerSubject,
    assessment: Mapping[str, Any],
) -> dict[str, Any]:
    """The saved per-subject readability record with attribution."""

    return {
        "schema_version": FILE_READABILITY_RECORD_VERSION,
        "scenario_id": scenario.scenario_id,
        "subject": {
            "profile": subject.profile,
            "reasoning_effort": subject.effort,
            "sample_index": subject.sample_index,
        },
        "assessment": dict(assessment),
        "summary": _readability_summary(assessment),
    }


def _readability_summary(assessment: Mapping[str, Any]) -> str:
    sections = assessment.get("sections", {})
    top = sum(
        1
        for entry in sections.values()
        if entry.get("grade") == READABILITY_SECTION_GRADES[0]
    )
    navigation = (assessment.get("navigation") or {}).get("grade")
    mistakes = len(assessment.get("mistakes", ()))
    return (
        f"sections {top}/{len(sections)} readable; navigation {navigation};"
        f" mistakes={mistakes}"
    )


def aggregate_file_readability(
    assessments: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    """Aggregate readability grades and mistake counts across subjects."""

    if not assessments:
        return {
            "assessment_count": 0,
            "section_grades": {},
            "navigation": {},
            "mistake_count": 0,
        }
    section_counts: Counter = Counter()
    section_total = 0
    for assessment in assessments:
        for entry in (assessment.get("sections") or {}).values():
            section_counts[str(entry.get("grade"))] += 1
            section_total += 1
    navigation_counts = Counter(
        str((assessment.get("navigation") or {}).get("grade"))
        for assessment in assessments
    )
    top_share = (
        round(section_counts.get(READABILITY_SECTION_GRADES[0], 0) / section_total, 3)
        if section_total
        else None
    )
    return {
        "assessment_count": len(assessments),
        "section_grades": dict(section_counts),
        "section_top_share": top_share,
        "navigation": dict(navigation_counts),
        "mistake_count": sum(
            len(assessment.get("mistakes", ())) for assessment in assessments
        ),
    }
