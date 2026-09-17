from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .requirement_quality import RequirementQualityScenario


QUALITY_PROMPT_VERSION = "v1"
QUALITY_DIMENSIONS = (
    "requirements",
    "testing",
    "plan_usability",
)
QUALITY_METRICS = (
    "target_fidelity",
    "scope_discipline",
    "clarity",
    "testing_decisiveness",
    "testing_proportionality",
    "plan_usability",
    "overall_quality",
)
PREFERENCES = {"A", "B", "tie"}
DIFFERENCES = {"none", "slight", "moderate", "large"}
CONFIDENCE_LEVELS = {"low", "medium", "high"}
LIKELY_CAUSES = {
    "dedicated_requirements_section",
    "evidence_not_requirement",
    "unapproved_behavior_remains_question",
    "internal_mechanism_not_authorized",
    "smallest_reliable_evidence",
    "mock_bypass_not_decisive",
    "real_crossing_rule",
    "existing_coverage_must_prove_behavior",
    "removed_testing_detail",
    "task_guidance_interaction",
    "producer_variance",
    "other",
}


def quality_label_mapping(
    *,
    scenario_id: str,
    mode: str,
    candidate_id: str,
) -> dict[str, str]:
    identity = f"{scenario_id}:{mode}:{candidate_id}".encode("utf-8")
    combined_first = hashlib.sha256(identity).digest()[0] % 2 == 0
    if combined_first:
        return {"A": "combined-v2", "B": "baseline"}
    return {"A": "baseline", "B": "combined-v2"}


def build_quality_prompt(
    *,
    scenario: RequirementQualityScenario,
    target: dict[str, Any],
    mode: str,
    candidate_id: str,
    outputs: dict[str, dict[str, Any]],
    semantic_assessments: dict[str, dict[str, Any]],
    label_mapping: dict[str, str],
) -> str:
    labeled_outputs = {
        label: {
            "producer": outputs[variant]["producer"],
            "generated_files": outputs[variant]["generated_files"],
            "semantic_assessment": semantic_assessments[variant],
        }
        for label, variant in label_mapping.items()
    }
    schema = {
        "schema_version": 1,
        "scenario_id": scenario.scenario_id,
        "candidate_id": candidate_id,
        "dimension_reviews": [
            {
                "dimension": "requirements | testing | plan_usability",
                "preferred": "A | B | tie",
                "difference": "none | slight | moderate | large",
                "rationale": "concise comparison grounded in the supplied outputs",
            }
        ],
        "scores": {
            "A": {metric: "integer 1 through 5" for metric in QUALITY_METRICS},
            "B": {metric: "integer 1 through 5" for metric in QUALITY_METRICS},
        },
        "overall_preference": "A | B | tie",
        "overall_difference": "none | slight | moderate | large",
        "strengths_a": ["concise observed strengths"],
        "strengths_b": ["concise observed strengths"],
        "weaknesses_a": ["concise observed weaknesses"],
        "weaknesses_b": ["concise observed weaknesses"],
        "guidance_effects": [
            {
                "observation": "specific changed behavior",
                "likely_cause": "one allowed cause",
                "confidence": "low | medium | high",
                "rationale": "why the wording could plausibly cause the behavior",
            }
        ],
        "summary": "concise overall comparison",
    }
    return f"""You are comparing two planning outputs for the same small
software task, model, reasoning effort, fixture, and user prompt.

Judge overall practical quality, including outputs that already satisfy the
semantic contract. Do not reward verbosity, requirement count, test count, or
implementation detail by itself. A shorter output can be better when it is
complete and easier to review.

Effort context:

- Low effort is not expected to achieve the same completeness as high effort.
  Still do not reward invented public behavior or material scope expansion.
- Medium effort should normally be complete and usable, but may leave some
  robustness detail for implementation.
- High, xhigh, and max effort should be complete and decisive while keeping
  requirements focused. Extra reasoning does not authorize extra product
  requirements, internal mechanisms, or unnecessary tests.

Use the supplied semantic assessments as correctness evidence, then inspect the
actual outputs for qualities those assessments do not fully capture:

- whether requirements are easy for a human to understand and review;
- whether grouping and wording expose the real completion conditions;
- whether questions and recommendations are clearly non-normative;
- whether the test plan gives decisive, realistic, proportionate evidence;
- whether the plan is actionable without becoming a long implementation essay;
- whether useful passing outputs became clearer or less useful.

Possible wording causes are restricted to:

{json.dumps(sorted(LIKELY_CAUSES), indent=2)}

Treat a wording cause as a hypothesis, not proof. Use low confidence when the
difference could reasonably be producer variance.

Project and target:

{json.dumps({
    "project_name": scenario.project_name,
    "project_kind": scenario.project_kind,
    "mode": mode,
    "producer": candidate_id,
    "target": target,
}, indent=2, sort_keys=True)}

Outputs:

{json.dumps(labeled_outputs, indent=2, sort_keys=True)}

Return only one JSON object matching this schema:

{json.dumps(schema, indent=2, sort_keys=True)}
"""


def validate_quality_result(
    value: object,
    *,
    scenario_id: str,
    candidate_id: str,
) -> None:
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("quality result must use schema_version 1")
    if value.get("scenario_id") != scenario_id:
        raise ValueError("quality result scenario_id does not match")
    if value.get("candidate_id") != candidate_id:
        raise ValueError("quality result candidate_id does not match")

    reviews = value.get("dimension_reviews")
    if not isinstance(reviews, list) or len(reviews) != len(
        QUALITY_DIMENSIONS
    ):
        raise ValueError("quality result must contain three dimension reviews")
    by_dimension = {
        item.get("dimension"): item
        for item in reviews
        if isinstance(item, dict)
    }
    if set(by_dimension) != set(QUALITY_DIMENSIONS):
        raise ValueError("quality result dimensions do not match")
    for dimension, item in by_dimension.items():
        if item.get("preferred") not in PREFERENCES:
            raise ValueError(f"{dimension}: invalid preference")
        if item.get("difference") not in DIFFERENCES:
            raise ValueError(f"{dimension}: invalid difference")
        _require_text(item, "rationale", dimension)

    scores = value.get("scores")
    if not isinstance(scores, dict) or set(scores) != {"A", "B"}:
        raise ValueError("quality result scores must contain A and B")
    for label, values in scores.items():
        if not isinstance(values, dict) or set(values) != set(QUALITY_METRICS):
            raise ValueError(f"{label}: quality score metrics do not match")
        for metric, score in values.items():
            if not isinstance(score, int) or isinstance(score, bool):
                raise ValueError(f"{label}/{metric}: score must be an integer")
            if not 1 <= score <= 5:
                raise ValueError(f"{label}/{metric}: score must be 1 through 5")

    if value.get("overall_preference") not in PREFERENCES:
        raise ValueError("quality result has invalid overall preference")
    if value.get("overall_difference") not in DIFFERENCES:
        raise ValueError("quality result has invalid overall difference")
    for key in ("strengths_a", "strengths_b", "weaknesses_a", "weaknesses_b"):
        items = value.get(key)
        if not isinstance(items, list) or any(
            not isinstance(item, str) or not item.strip() for item in items
        ):
            raise ValueError(f"quality result has invalid {key}")

    effects = value.get("guidance_effects")
    if not isinstance(effects, list):
        raise ValueError("quality result guidance_effects must be a list")
    for item in effects:
        if not isinstance(item, dict):
            raise ValueError("quality result has an invalid guidance effect")
        _require_text(item, "observation", "guidance effect")
        _require_text(item, "rationale", "guidance effect")
        if item.get("likely_cause") not in LIKELY_CAUSES:
            raise ValueError("quality result has an invalid likely cause")
        if item.get("confidence") not in CONFIDENCE_LEVELS:
            raise ValueError("quality result has invalid effect confidence")
    _require_text(value, "summary", "quality result")


def mapped_quality_result(
    value: dict[str, Any],
    *,
    label_mapping: dict[str, str],
) -> dict[str, Any]:
    inverse = {label: variant for label, variant in label_mapping.items()}

    def map_preference(preference: str) -> str:
        return preference if preference == "tie" else inverse[preference]

    return {
        **value,
        "dimension_reviews": [
            {
                **item,
                "preferred": map_preference(item["preferred"]),
            }
            for item in value["dimension_reviews"]
        ],
        "scores": {
            inverse[label]: scores
            for label, scores in value["scores"].items()
        },
        "overall_preference": map_preference(value["overall_preference"]),
        "strengths": {
            inverse["A"]: value["strengths_a"],
            inverse["B"]: value["strengths_b"],
        },
        "weaknesses": {
            inverse["A"]: value["weaknesses_a"],
            inverse["B"]: value["weaknesses_b"],
        },
    }


def _require_text(value: dict[str, Any], key: str, owner: str) -> None:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise ValueError(f"{owner}: {key} must be non-empty text")


def semantic_record_paths(
    artifact_root: Path,
    *,
    variant: str,
    mode: str,
    scenario_id: str,
    repeat_variant: str,
) -> list[Path]:
    dataset_id = f"root-guidance-{variant}-{mode}-20260917"
    pattern = (
        f"*requirement-semantic-{dataset_id}-{scenario_id}-*/"
        "records/semantic-evaluation.json"
    )
    paths: list[Path] = []
    for path in sorted((artifact_root / "glm" / "runs").glob(pattern)):
        value = json.loads(path.read_text(encoding="utf-8"))
        if (
            value.get("dataset_id") == dataset_id
            and value.get("scenario_id") == scenario_id
            and value.get("repeat_variant") == repeat_variant
        ):
            paths.append(path)
    return paths