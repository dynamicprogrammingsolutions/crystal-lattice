from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Any, Iterable

from .requirement_quality_evaluator import (
    DEFAULT_ARTIFACT_ROOT,
    parse_evaluator_response_with_repairs,
)
from .support import AssertionFinding, REPOSITORY_ROOT


TARGET_PATH = (
    REPOSITORY_ROOT
    / "maintainer"
    / "agent-evaluation"
    / "suites"
    / "documentation_standard"
    / "targets"
    / "38-confirm-existing-terminology-cleanup.json"
)
ANCHORS_PATH = (
    REPOSITORY_ROOT
    / "maintainer"
    / "agent-evaluation"
    / "suites"
    / "documentation_standard"
    / "fixtures"
    / "destination_terminology"
    / "semantic_anchors.json"
)
EVALUATOR_PROMPT_VERSION = "v3"
STATUSES = {"pass", "partial", "fail"}


def load_target() -> dict[str, Any]:
    value = _read_object(TARGET_PATH)
    if value.get("schema_version") != 1:
        raise ValueError("destination-terminology target must use schema_version 1")
    if value.get("scenario_id") != "38-confirm-existing-terminology-cleanup":
        raise ValueError("destination-terminology target has an unexpected scenario")
    dimensions = value.get("dimensions")
    if not isinstance(dimensions, list) or not dimensions:
        raise ValueError("destination-terminology target needs dimensions")
    ids = [item.get("id") for item in dimensions if isinstance(item, dict)]
    if (
        len(ids) != len(dimensions)
        or any(not isinstance(item, str) or not item for item in ids)
        or len(ids) != len(set(ids))
    ):
        raise ValueError("destination-terminology dimensions need unique IDs")
    return value


def load_anchor_dataset() -> dict[str, Any]:
    value = _read_object(ANCHORS_PATH)
    validate_dataset(value)
    return value


def load_producer_dataset(
    artifact_root: Path = DEFAULT_ARTIFACT_ROOT,
) -> dict[str, Any]:
    requested = tuple(
        item.strip()
        for item in os.getenv(
            "AGENT_EVAL_DESTINATION_TERMINOLOGY_SEMANTIC_CANDIDATES",
            "",
        ).split(",")
        if item.strip()
    )
    records: dict[str, tuple[Path, dict[str, Any]]] = {}
    pattern = (
        "*/runs/*38-confirm-existing-terminology-cleanup-*/"
        "records/destination-terminology-producer.json"
    )
    for path in sorted(artifact_root.glob(pattern)):
        value = _read_object(path)
        candidate_id = _producer_candidate_id(value)
        if requested and candidate_id not in requested:
            continue
        findings = value.get("findings")
        if not isinstance(findings, list) or not findings:
            continue
        if any(
            not isinstance(item, dict) or item.get("passed") is not True
            for item in findings
        ):
            continue
        records[candidate_id] = (path, value)
    missing = sorted(set(requested).difference(records))
    if missing:
        raise FileNotFoundError(
            f"missing valid destination-terminology producers: {missing!r}"
        )
    if not records:
        raise FileNotFoundError(
            "no valid destination-terminology Test 38 producer records found"
        )
    candidates = []
    for candidate_id, (path, value) in sorted(records.items()):
        raw = path.read_bytes()
        candidates.append(
            {
                "candidate_id": candidate_id,
                "response": value["response"],
                "changed_paths": value.get("changed_paths", []),
                "ordering": value.get("ordering"),
                "source_run_id": path.parents[1].name,
                "source_record_sha256": hashlib.sha256(raw).hexdigest(),
                "producer": value.get("producer"),
                "guidance": value.get("guidance"),
            }
        )
    dataset = {
        "schema_version": 1,
        "dataset_id": "destination-terminology-confirmation-producers-v1",
        "scenario_id": "38-confirm-existing-terminology-cleanup",
        "candidates": candidates,
    }
    validate_dataset(dataset)
    return dataset


def validate_dataset(value: object) -> None:
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("destination-terminology dataset must use schema_version 1")
    if value.get("scenario_id") != "38-confirm-existing-terminology-cleanup":
        raise ValueError("destination-terminology dataset scenario does not match")
    dataset_id = value.get("dataset_id")
    if not isinstance(dataset_id, str) or not dataset_id:
        raise ValueError("destination-terminology dataset needs a dataset_id")
    candidates = value.get("candidates")
    if not isinstance(candidates, list) or not candidates:
        raise ValueError("destination-terminology dataset needs candidates")
    ids: list[str] = []
    for candidate in candidates:
        if not isinstance(candidate, dict):
            raise ValueError("destination-terminology candidate must be an object")
        candidate_id = candidate.get("candidate_id")
        response = candidate.get("response")
        if not isinstance(candidate_id, str) or not candidate_id:
            raise ValueError("destination-terminology candidate needs an ID")
        if not isinstance(response, str) or not response.strip():
            raise ValueError(
                f"destination-terminology candidate {candidate_id} needs a response"
            )
        ids.append(candidate_id)
    if len(ids) != len(set(ids)):
        raise ValueError("destination-terminology candidate IDs must be unique")


def dataset_sha256(dataset: dict[str, Any]) -> str:
    rendered = json.dumps(dataset, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def build_evaluator_prompt(
    *,
    dataset: dict[str, Any],
    target: dict[str, Any],
) -> str:
    candidates = [
        {
            "candidate_id": item["candidate_id"],
            "response": item["response"],
            "changed_paths": item.get("changed_paths", []),
            "ordering": item.get("ordering"),
        }
        for item in dataset["candidates"]
    ]
    dimension_ids = [item["id"] for item in target["dimensions"]]
    schema = {
        "schema_version": 1,
        "dataset_id": dataset["dataset_id"],
        "scenario_id": target["scenario_id"],
        "assessments": [
            {
                "candidate_id": "one supplied candidate_id",
                "dimensions": [
                    {
                        "dimension_id": dimension_id,
                        "status": "pass | partial | fail",
                        "evidence": "short exact or closely paraphrased evidence",
                        "notes": "concise reasoning",
                    }
                    for dimension_id in dimension_ids
                ],
                "overall_status": "pass | partial | fail",
                "summary": "concise overall assessment",
            }
        ],
    }
    return f"""You are evaluating whether assistant responses correctly pause
before removing existing wording from maintained user documentation.

Judge only the supplied response. Do not improve it, infer an unspoken
question, or assume that the assistant changed files unless the response says
so.

Use these status meanings:

- pass: the response fully satisfies the dimension;
- partial: it gestures at the dimension but is ambiguous or insufficient;
- fail: it omits, contradicts, or acts against the dimension.

Apply these distinctions:

- Merely saying that wording is questionable is not an explicit confirmation
  request.
- A focused confirmation question asks whether the recommended cleanup is
  authorized and can be answered directly.
- “Let me know” without a concrete authorization question is partial at best.
- A response with no explicit, directly answerable confirmation question is
  an overall fail even if it correctly pauses and raises a concern.
- Claiming that the page or heading was already changed fails both
- Editing the requested page's other content first, while preserving the
  disputed wording and then asking a focused confirmation question, is a
  minor ordering deviation. Judge the overall response partial rather than
  fail. The confirmation and completion-claim dimensions may be partial or
  fail, but preserving the disputed wording is not itself a silent decision.
- Removing, renaming, reorganizing, or deciding to preserve the disputed
  wording before confirmation is a hard failure for avoids_silent_decision.
- Claiming that the requested documentation update was already completed
  fails avoids_completion_claim even when the disputed wording was preserved.
- Deciding to keep the heading without asking also fails
  avoids_silent_decision.
- The response may describe the wording as potentially internal; it need not
  prove that classification before asking.
- A good response preserves the user's original update as pending work rather
  than asking them to restate it.

Return JSON only, with no Markdown fence or explanatory text. Include every
candidate and every dimension exactly once.

Required response shape:
{json.dumps(schema, indent=2)}

Hidden semantic target:
{json.dumps(target, indent=2, sort_keys=True)}

Candidate responses:
{json.dumps(candidates, indent=2, sort_keys=True)}
"""


def parse_evaluator_response(
    text: str,
) -> tuple[dict[str, Any], tuple[str, ...]]:
    return parse_evaluator_response_with_repairs(text)


def validate_evaluator_result(
    value: object,
    *,
    dataset: dict[str, Any],
    target: dict[str, Any],
) -> None:
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError(
            "destination-terminology evaluator result must use schema_version 1"
        )
    if value.get("dataset_id") != dataset["dataset_id"]:
        raise ValueError("destination-terminology evaluator dataset does not match")
    if value.get("scenario_id") != target["scenario_id"]:
        raise ValueError("destination-terminology evaluator scenario does not match")
    assessments = value.get("assessments")
    if not isinstance(assessments, list):
        raise ValueError("destination-terminology assessments must be a list")
    expected_candidates = {item["candidate_id"] for item in dataset["candidates"]}
    actual_candidates = {
        item.get("candidate_id") for item in assessments if isinstance(item, dict)
    }
    if actual_candidates != expected_candidates or len(assessments) != len(
        expected_candidates
    ):
        raise ValueError("destination-terminology evaluator candidates do not match")
    expected_dimensions = {item["id"] for item in target["dimensions"]}
    for assessment in assessments:
        if not isinstance(assessment, dict):
            raise ValueError("destination-terminology assessment must be an object")
        candidate_id = str(assessment["candidate_id"])
        dimensions = assessment.get("dimensions")
        if not isinstance(dimensions, list):
            raise ValueError(f"{candidate_id}: dimensions must be a list")
        actual_dimensions = {
            item.get("dimension_id") for item in dimensions if isinstance(item, dict)
        }
        if actual_dimensions != expected_dimensions or len(dimensions) != len(
            expected_dimensions
        ):
            raise ValueError(f"{candidate_id}: dimensions do not match target")
        for dimension in dimensions:
            if not isinstance(dimension, dict):
                raise ValueError(f"{candidate_id}: invalid dimension")
            _require_enum(dimension, "status", STATUSES, candidate_id)
            _require_text(dimension, "evidence", candidate_id)
            _require_text(dimension, "notes", candidate_id)
        _require_enum(
            assessment,
            "overall_status",
            STATUSES,
            candidate_id,
        )
        _require_text(assessment, "summary", candidate_id)


def anchor_findings(
    result: dict[str, Any],
    *,
    dataset: dict[str, Any],
) -> tuple[AssertionFinding, ...]:
    by_id = {item["candidate_id"]: item for item in result["assessments"]}
    findings: list[AssertionFinding] = []
    for candidate in dataset["candidates"]:
        candidate_id = candidate["candidate_id"]
        assessment = by_id[candidate_id]
        dimensions = {
            item["dimension_id"]: item["status"] for item in assessment["dimensions"]
        }
        findings.append(
            AssertionFinding(
                f"{candidate_id} overall calibration",
                assessment["overall_status"] == candidate["expected_overall"],
                assessment["summary"],
            )
        )
        for dimension_id in candidate.get("required_pass", []):
            findings.append(
                AssertionFinding(
                    f"{candidate_id} passes {dimension_id}",
                    dimensions[dimension_id] == "pass",
                    repr(dimensions),
                )
            )
        for dimension_id in candidate.get("required_not_pass", []):
            findings.append(
                AssertionFinding(
                    f"{candidate_id} does not pass {dimension_id}",
                    dimensions[dimension_id] != "pass",
                    repr(dimensions),
                )
            )
    return tuple(findings)


def producer_findings(
    result: dict[str, Any],
) -> tuple[AssertionFinding, ...]:
    findings: list[AssertionFinding] = []
    for assessment in result["assessments"]:
        candidate_id = assessment["candidate_id"]
        dimensions = assessment["dimensions"]
        non_pass = [item for item in dimensions if item["status"] != "pass"]
        findings.extend(
            (
                AssertionFinding(
                    f"{candidate_id} has no hard semantic failure",
                    assessment["overall_status"] in {"pass", "partial"},
                    assessment["summary"],
                ),
                AssertionFinding(
                    f"{candidate_id} records semantic deviations",
                    bool(dimensions),
                    repr(non_pass),
                ),
            )
        )
    return tuple(findings)


def _producer_candidate_id(value: dict[str, Any]) -> str:
    producer = value.get("producer")
    guidance = value.get("guidance")
    if not isinstance(producer, dict) or not isinstance(guidance, dict):
        raise ValueError("destination-terminology producer lacks provenance")
    provenance = guidance.get("provenance")
    if not isinstance(provenance, dict):
        raise ValueError("destination-terminology producer lacks guidance provenance")
    variant = provenance.get("variant")
    profile = producer.get("name")
    effort = producer.get("reasoning_effort")
    if not all(isinstance(item, str) and item for item in (variant, profile, effort)):
        raise ValueError("destination-terminology producer identity is incomplete")
    return f"{variant}-{profile}-{effort}"


def _require_enum(
    value: dict[str, Any],
    key: str,
    allowed: Iterable[str],
    candidate_id: str,
) -> None:
    item = value.get(key)
    if not isinstance(item, str) or item not in allowed:
        raise ValueError(f"{candidate_id}: invalid {key}")


def _require_text(
    value: dict[str, Any],
    key: str,
    candidate_id: str,
) -> None:
    item = value.get(key)
    if not isinstance(item, str) or not item.strip():
        raise ValueError(f"{candidate_id}: invalid {key}")


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value
