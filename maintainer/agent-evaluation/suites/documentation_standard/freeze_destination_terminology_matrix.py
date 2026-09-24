from __future__ import annotations

import hashlib
import json
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .requirement_quality_evaluator import DEFAULT_ARTIFACT_ROOT


RESULT_ROOT = Path(__file__).resolve().parent / "fixtures" / "results"
OUTPUT_PATH = RESULT_ROOT / "destination_terminology_20260920_results.json"
REVIEW_RECORD = "semantic-assessment-input.json"
VARIANTS = (
    "current",
    "abstract-specific",
    "explicit-contexts-specific",
)
PROFILES = (
    ("glm", "high"),
    ("glm", "max"),
    ("gpt", "high"),
    ("gpt", "xhigh"),
)
SCENARIOS = (
    "04-destination-terminology-package-owned-refinement",
    "13-destination-terminology-prevention",
    "14-destination-terminology-portable-contract-owner",
    "36-source-terms-in-specification-records-task-number",
    "36-source-terms-in-specification-records-sequence-label",
    "36-source-terms-in-specification-records-evaluative-wording",
    "37-source-terms-in-code-and-tests-task-number",
    "37-source-terms-in-code-and-tests-sequence-label",
    "37-source-terms-in-code-and-tests-evaluative-wording",
    "38-confirm-existing-terminology-cleanup",
)
MATRIX_CACHE_VARIANTS = {
    ("current", "glm", "high"): {"current-matrix-r1"},
    ("abstract-specific", "glm", "high"): {"dt-full-abstract-glm-high-v1"},
    ("explicit-contexts-specific", "glm", "high"): {"explicit-matrix-r1"},
    ("current", "glm", "max"): {"dt-full-current-glm-max-v1"},
    ("abstract-specific", "glm", "max"): {
        "dt-full-abstract-glm-max-v1",
        "dt-retry-abstract-glm-max-task-number-r1",
    },
    ("explicit-contexts-specific", "glm", "max"): {"dt-full-explicit-glm-max-v1"},
    ("current", "gpt", "high"): {"dt-full-current-gpt-high-v1"},
    ("abstract-specific", "gpt", "high"): {"dt-full-abstract-gpt-high-v1"},
    ("explicit-contexts-specific", "gpt", "high"): {"dt-full-explicit-gpt-high-v1"},
    ("current", "gpt", "xhigh"): {"dt-full-current-gpt-xhigh-v1"},
    ("abstract-specific", "gpt", "xhigh"): {
        "dt-full-abstract-gpt-xhigh-v1",
        "dt-retry-abstract-gpt-xhigh-task-number-r1",
    },
    ("explicit-contexts-specific", "gpt", "xhigh"): {
        "dt-full-explicit-gpt-xhigh-v1",
        "dt-retry-explicit-gpt-xhigh-sequence-r1",
        "dt-retry-explicit-gpt-xhigh-evaluative-r1",
    },
}
SEMANTIC_REPEAT_VARIANT = "matrix-20260920-v1"
ANCHOR_REPEAT_VARIANT = "partial-anchor-v4"


def _read_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _evidence_values(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, list):
        raise ValueError(f"{path} must contain a JSON list")
    return {
        item["kind"]: item.get("value")
        for item in value
        if isinstance(item, dict) and isinstance(item.get("kind"), str)
    }


def _candidate_record(
    path: Path,
) -> tuple[tuple[str, str, str, str], str, dict[str, Any]] | None:
    run_root = path.parents[1]
    evidence_path = run_root / "raw" / "evidence.json"
    result_path = run_root / "result.json"
    if not evidence_path.is_file() or not result_path.is_file():
        return None
    evidence = _evidence_values(evidence_path)
    profile = evidence.get("documentation_standard.profile")
    guidance = evidence.get("documentation_standard.guidance")
    cache_variant = evidence.get("documentation_standard.branch_cache_variant")
    if not isinstance(profile, dict) or not isinstance(guidance, dict):
        return None
    provenance = guidance.get("provenance")
    if not isinstance(provenance, dict):
        return None
    variant = provenance.get("variant")
    profile_name = profile.get("name")
    effort = profile.get("reasoning_effort")
    if not all(
        isinstance(item, str) and item
        for item in (variant, profile_name, effort, cache_variant)
    ):
        return None
    matrix_key = (variant, profile_name, effort)
    if cache_variant not in MATRIX_CACHE_VARIANTS.get(matrix_key, set()):
        return None
    result = _read_object(result_path)
    scenario = result.get("name")
    if not isinstance(scenario, str) or scenario not in SCENARIOS:
        return None
    identity = (variant, profile_name, effort, scenario)
    return (
        identity,
        cache_variant,
        {
            "path": path,
            "run_root": run_root,
            "evidence": evidence,
            "result": result,
            "profile": profile,
            "guidance": guidance,
        },
    )


def _select_producers(
    artifact_root: Path,
) -> dict[tuple[str, str, str, str], tuple[str, dict[str, Any]]]:
    selected: dict[
        tuple[str, str, str, str],
        tuple[str, dict[str, Any]],
    ] = {}
    pattern = f"*/runs/*/records/{REVIEW_RECORD}"
    for path in sorted(artifact_root.glob(pattern)):
        candidate = _candidate_record(path)
        if candidate is None:
            continue
        identity, cache_variant, details = candidate
        previous = selected.get(identity)
        if (
            previous is None
            or path.stat().st_mtime > previous[1]["path"].stat().st_mtime
        ):
            selected[identity] = (cache_variant, details)
    expected = {
        (variant, profile, effort, scenario)
        for variant in VARIANTS
        for profile, effort in PROFILES
        for scenario in SCENARIOS
    }
    missing = sorted(expected.difference(selected))
    unexpected = sorted(set(selected).difference(expected))
    if missing or unexpected:
        raise ValueError(
            "destination-terminology matrix selection mismatch: "
            f"missing={missing!r}, unexpected={unexpected!r}"
        )
    return selected


def _freeze_producer(
    identity: tuple[str, str, str, str],
    cache_variant: str,
    details: dict[str, Any],
) -> dict[str, Any]:
    variant, profile, effort, scenario = identity
    path = details["path"]
    review = _read_object(path)
    findings = review.get("findings")
    if not isinstance(findings, list) or not findings:
        raise ValueError(f"{path} has no findings")
    invalid = {
        "run completed",
        "assistant response",
        "provider errors",
        "producer profile matches selection",
        "reasoning effort matches selection",
    }
    failed_names = {
        item.get("name")
        for item in findings
        if isinstance(item, dict) and item.get("passed") is not True
    }
    invalid_findings = sorted(invalid.intersection(failed_names))
    if invalid_findings:
        raise ValueError(f"{path} is not a valid producer: {invalid_findings!r}")
    result = details["result"]
    result_value = result.get("value")
    producer_path = (
        details["run_root"] / "records" / "destination-terminology-producer.json"
    )
    ordering = None
    if producer_path.is_file():
        ordering = _read_object(producer_path).get("ordering")
    frozen_findings = []
    for item in findings:
        if not isinstance(item, dict):
            raise ValueError(f"{path} has an invalid finding")
        finding = {
            "name": item.get("name"),
            "passed": item.get("passed"),
        }
        if item.get("passed") is not True:
            finding["detail"] = item.get("detail")
        frozen_findings.append(finding)
    return {
        "variant": variant,
        "profile": profile,
        "model": details["profile"].get("model"),
        "reasoning_effort": effort,
        "scenario_id": scenario,
        "cache_variant": cache_variant,
        "passed": all(item.get("passed") is True for item in findings),
        "changed_paths": review.get("changed_paths"),
        "prompt": review.get("prompt"),
        "response": review.get("response"),
        "review_content": review.get("requirements"),
        "findings": frozen_findings,
        "ordering": ordering,
        "guidance": details["guidance"],
        "run_status": result.get("status"),
        "cache_hit": result.get("cache_hit"),
        "provider_errors": (
            result_value.get("provider_errors")
            if isinstance(result_value, dict)
            else None
        ),
        "source_run_id": details["run_root"].name,
        "source_record_sha256": _sha256(path),
    }


def _latest_semantic_record(
    artifact_root: Path,
    *,
    dataset_id: str,
    repeat_variant: str,
) -> tuple[Path, dict[str, Any]]:
    pattern = (
        "glm/runs/*destination-terminology-semantic-"
        f"{dataset_id}-*/records/destination-terminology-semantic.json"
    )
    matching: list[tuple[Path, dict[str, Any]]] = []
    for path in artifact_root.glob(pattern):
        value = _read_object(path)
        if value.get("repeat_variant") == repeat_variant:
            matching.append((path, value))
    if not matching:
        raise FileNotFoundError(
            f"missing semantic record for {dataset_id}/{repeat_variant}"
        )
    return max(matching, key=lambda item: item[0].stat().st_mtime)


def freeze(artifact_root: Path = DEFAULT_ARTIFACT_ROOT) -> dict[str, Any]:
    selected = _select_producers(artifact_root)
    producers = [
        _freeze_producer(identity, cache_variant, details)
        for identity, (cache_variant, details) in sorted(selected.items())
    ]
    producer_semantic_path, producer_semantic = _latest_semantic_record(
        artifact_root,
        dataset_id="destination-terminology-confirmation-producers-v1",
        repeat_variant=SEMANTIC_REPEAT_VARIANT,
    )
    anchor_path, anchor = _latest_semantic_record(
        artifact_root,
        dataset_id="destination-terminology-confirmation-anchors-v1",
        repeat_variant=ANCHOR_REPEAT_VARIANT,
    )
    summary: dict[str, Any] = {}
    for variant in VARIANTS:
        records = [item for item in producers if item["variant"] == variant]
        summary[variant] = {
            "passed": sum(item["passed"] for item in records),
            "total": len(records),
            "failed_findings": dict(
                Counter(
                    finding["name"]
                    for item in records
                    for finding in item["findings"]
                    if not finding["passed"]
                )
            ),
            "test_38_ordering": dict(
                Counter(
                    item["ordering"]["status"]
                    for item in records
                    if item["scenario_id"] == "38-confirm-existing-terminology-cleanup"
                    and isinstance(item["ordering"], dict)
                )
            ),
        }
    return {
        "schema_version": 1,
        "dataset_id": "destination-terminology-matrix-20260920",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "variants": list(VARIANTS),
        "profiles": [
            {"profile": profile, "reasoning_effort": effort}
            for profile, effort in PROFILES
        ],
        "scenarios": list(SCENARIOS),
        "summary": summary,
        "producers": producers,
        "semantic": {
            "producer_assessment": producer_semantic,
            "producer_source_run_id": producer_semantic_path.parents[1].name,
            "producer_source_record_sha256": _sha256(producer_semantic_path),
            "anchor_calibration": anchor,
            "anchor_source_run_id": anchor_path.parents[1].name,
            "anchor_source_record_sha256": _sha256(anchor_path),
        },
    }


def main() -> None:
    value = freeze()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(OUTPUT_PATH)


if __name__ == "__main__":
    main()
