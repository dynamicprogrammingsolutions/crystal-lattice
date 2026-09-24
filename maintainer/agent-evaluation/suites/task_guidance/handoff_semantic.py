from __future__ import annotations

import json
import re
from pathlib import Path
from string import Template
from typing import Any, Mapping, Sequence

from agent_eval.runner import select_cell_records

from .configuration import negative_control, plan_variants, producer_cells
from .scenarios import TaskGuidanceScenario
from .semantic import (
    continuation_cell_identity,
    handoff_cell_identity,
    _latest_sample,
)
from .stages import STAGES


def load_handoff_records(
    artifact_root: Path,
    *,
    scenario: TaskGuidanceScenario,
    labels: Sequence[str] | None,
    allow_partial: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    """The scenario's handoff records under the given run labels.

    Selection delegates to the consolidation core; each cell contributes
    its latest sample. Returns the fresh-agent plans plus the negative
    control, and the same-agent continuations.
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
    handoff_cells = producer_cells(scenario.category)
    expected_fresh = {
        f"{scenario.scenario_id}:{variant}:{profile}:{effort}"
        for variant in plan_variants(scenario.category)
        for profile, effort in handoff_cells
    }
    expected_same = {
        f"{scenario.scenario_id}:{profile}:{effort}"
        for profile, effort in handoff_cells
    }
    control = negative_control(scenario.category)
    expected_negative = (
        {
            f"{control['scenario']}:{control['variant']}:"
            f"{control['agent']}:{control['effort']}"
        }
        if control is not None and scenario.scenario_id == control["scenario"]
        else set()
    )
    missing = [
        *(f"fresh:{item}" for item in sorted(expected_fresh - set(fresh))),
        *(f"same:{item}" for item in sorted(expected_same - set(same))),
        *(f"negative:{item}" for item in sorted(expected_negative - set(negative))),
    ]
    if missing and not allow_partial:
        raise FileNotFoundError(
            f"missing handoff records for {scenario.scenario_id}: {missing}"
        )
    fresh_records = [_latest_sample(fresh[key]).value for key in sorted(fresh)]
    negative_records = [_latest_sample(negative[key]).value for key in sorted(negative)]
    same_records = [_latest_sample(same[key]).value for key in sorted(same)]
    return [*fresh_records, *negative_records], same_records


def _scenario_cells(
    cells: Mapping[str, tuple[Any, ...]],
    scenario_id: str,
) -> dict[str, tuple[Any, ...]]:
    prefix = f"{scenario_id}:"
    return {key: records for key, records in cells.items() if key.startswith(prefix)}


# The fixed instruction part of the assessment prompt. Per-evaluation
# material is substituted into the $-placeholders; the template itself
# is extracted verbatim into the scenarios export.
HANDOFF_ASSESSMENT_PROMPT_TEMPLATE = Template(
    """\
Assess whether each task handoff and resulting plan would let another agent
continue correctly without the original conversation or broad rediscovery.

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

Return JSON only:

{
  "schema_version": 1,
  "scenario_id": "$scenario_id",
  "assessments": [
    {
      "stage": "fresh-agent|same-agent",
      "variant": "retain|omit|incomplete|generated-task",
      "producer": {"profile": "glm|gpt", "reasoning_effort": "..."},
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
  ]
}

Scores are integers from 0 through 100. `broad_rediscovery` is true only when
the agent repeated substantial investigation that a complete task should have
made unnecessary.

Reviewed target:

$target_json

Handoff and plan records:

$records_json
"""
)


def handoff_semantic_prompt(
    scenario: TaskGuidanceScenario,
    fresh: list[dict[str, Any]],
    same: list[dict[str, Any]],
) -> str:
    records: list[dict[str, Any]] = []
    for item in fresh:
        if item.get("valid") is not True:
            continue
        records.append(
            {
                "stage": "fresh-agent",
                "variant": item["variant"],
                "producer": item["producer"],
                "task_files": item["task_files"],
                "plan_response": item["response"],
                "tool_metrics": item["tool_metrics"],
            }
        )
    for item in same:
        if item.get("valid") is not True:
            continue
        records.append(
            {
                "stage": "same-agent",
                "variant": "generated-task",
                "producer": item["producer"],
                "task_files": item["task_files"],
                "plan_response": item["response"],
                "tool_metrics": item["continuation_tool_metrics"],
                "task_creation_tool_metrics": item["task_creation_tool_metrics"],
            }
        )
    if not records:
        raise ValueError("handoff semantic assessment has no valid records")
    return HANDOFF_ASSESSMENT_PROMPT_TEMPLATE.substitute(
        scenario_id=scenario.scenario_id,
        target_json=json.dumps(scenario.target, indent=2, sort_keys=True),
        records_json=json.dumps(records, indent=2, sort_keys=True),
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
    expected_count: int,
) -> None:
    if value.get("schema_version") != 1:
        raise ValueError("handoff semantic schema_version must be 1")
    if value.get("scenario_id") != scenario.scenario_id:
        raise ValueError("handoff semantic scenario_id mismatch")
    assessments = value.get("assessments")
    if not isinstance(assessments, list) or len(assessments) != expected_count:
        raise ValueError(f"handoff semantic assessment count must be {expected_count}")
    identities: set[tuple[str, str, str, str]] = set()
    for item in assessments:
        if not isinstance(item, dict):
            raise ValueError("handoff assessment must be an object")
        producer = item.get("producer")
        if not isinstance(producer, dict):
            raise ValueError("handoff producer must be an object")
        identity = (
            str(item.get("stage")),
            str(item.get("variant")),
            str(producer.get("profile")),
            str(producer.get("reasoning_effort")),
        )
        if identity in identities:
            raise ValueError(f"duplicate handoff assessment: {identity}")
        identities.add(identity)
        _choice(item, "stage", {"fresh-agent", "same-agent"})
        _choice(
            item,
            "variant",
            {"retain", "omit", "incomplete", "generated-task"},
        )
        _choice(item, "plan_coverage", {"complete", "partial", "poor"})
        _choice(item, "testing_boundary", {"decisive", "partial", "poor"})
        _choice(
            item,
            "documentation_boundary",
            {"appropriate", "partial", "poor"},
        )
        for key in (
            "missing_outcomes",
            "lost_facts_or_decisions",
            "invented_scope_or_decisions",
        ):
            if not isinstance(item.get(key), list):
                raise ValueError(f"handoff {key} must be a list")
        for key in ("task_self_contained", "broad_rediscovery"):
            if not isinstance(item.get(key), bool):
                raise ValueError(f"handoff {key} must be boolean")
        score = item.get("handoff_quality_score")
        if not isinstance(score, int) or not 0 <= score <= 100:
            raise ValueError("handoff_quality_score must be 0..100")
        for key in ("efficiency_interpretation", "summary"):
            if not isinstance(item.get(key), str):
                raise ValueError(f"handoff {key} must be a string")


def _choice(value: Mapping[str, Any], key: str, choices: set[str]) -> None:
    selected = value.get(key)
    if selected not in choices:
        raise ValueError(f"handoff {key} must be one of {sorted(choices)}")
