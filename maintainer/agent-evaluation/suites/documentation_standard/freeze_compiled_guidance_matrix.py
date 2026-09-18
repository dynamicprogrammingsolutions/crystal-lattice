from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .analyze_root_guidance_full_matrix import analyze_full_matrix
from .compiled_guidance import compile_scenario_guidance
from .requirement_quality import PRODUCER_CASES, ROOT_GUIDANCE_MODES, SCENARIOS
from .requirement_quality_evaluator import (
    DEFAULT_ARTIFACT_ROOT,
    record_generated_files,
)


RESULT_ROOT = Path(__file__).resolve().parent / "fixtures" / "results"
OUTPUT_PATH = RESULT_ROOT / "compiled_guidance_20260918_results.json"
ANALYSIS_PATH = RESULT_ROOT / "compiled_guidance_20260918_analysis.json"
SEMANTIC_REPEAT_VARIANT = "compiled-matrix-r1"
QUALITY_REPEAT_VARIANTS = (
    "compiled-documentation-r2",
    "compiled-documentation-r1",
)
PRODUCER_REPEAT_VARIANT = "compiled-documentation-r1"
VARIANT_BUNDLES = {
    "baseline": "maintainer/guidance/current",
    "combined-v2": (
        "maintainer/guidance/candidates/root-requirements-testing-v2"
    ),
}
RECORD_NAME = "root-guidance-requirement-quality.json"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain one JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _producer_record_path(
    artifact_root: Path,
    *,
    test_prefix: str,
    scenario_id: str,
    profile: str,
    effort: str,
    compilation_sha256: str,
) -> Path:
    pattern = (
        f"*{test_prefix}-{scenario_id}-{effort}-*/"
        f"records/{RECORD_NAME}"
    )
    matching: list[Path] = []
    for path in sorted((artifact_root / profile / "runs").glob(pattern)):
        value = _read_json(path)
        producer = value.get("producer")
        lock = value.get("guidance_compilation")
        if (
            value.get("scenario_id") == scenario_id
            and value.get("repeat_variant") == PRODUCER_REPEAT_VARIANT
            and isinstance(producer, dict)
            and producer.get("profile") == profile
            and producer.get("reasoning_effort") == effort
            and isinstance(lock, dict)
            and lock.get("compilation_sha256") == compilation_sha256
        ):
            matching.append(path)
    if not matching:
        raise FileNotFoundError(
            "missing compiled producer for "
            f"{test_prefix}/{scenario_id}/{profile}-{effort}/"
            f"{compilation_sha256}"
        )
    return matching[-1]


def _frozen_producer(
    path: Path,
    *,
    variant: str,
    mode: str,
) -> dict[str, Any]:
    value = _read_json(path)
    guidance = dict(value["guidance"])
    guidance.pop("effective_message", None)
    producer = value["producer"]
    delivery = value.get("instruction_delivery")
    if not isinstance(delivery, dict):
        result_path = path.parents[1] / "result.json"
        result = _read_json(result_path)
        delivery = next(
            (
                item["value"]
                for item in result.get("evidence", [])
                if isinstance(item, dict)
                and item.get("kind")
                == "documentation_standard.guidance_injection"
                and isinstance(item.get("value"), dict)
            ),
            {},
        )
    return {
        "dataset_id": value["dataset_id"],
        "variant": variant,
        "mode": mode,
        "scenario_id": value["scenario_id"],
        "candidate_id": (
            f"{producer['profile']}-{producer['reasoning_effort']}"
        ),
        "project": value["project"],
        "target_sha256": value["target_sha256"],
        "prompt": value["prompt"],
        "producer": producer,
        "guidance": guidance,
        "instruction_delivery": delivery,
        "guidance_compilation": value["guidance_compilation"],
        "changed_paths": value["changed_paths"],
        "generated_files": record_generated_files(path, value),
        "response": value["response"],
        "findings": value["findings"],
        "source_run_id": path.parents[1].name,
        "source_record_sha256": _sha256(path),
    }


def freeze_producers(
    artifact_root: Path,
) -> tuple[list[dict[str, Any]], dict[tuple[str, str, str, str], dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    by_identity: dict[tuple[str, str, str, str], dict[str, Any]] = {}
    for variant, bundle in VARIANT_BUNDLES.items():
        for mode in sorted(ROOT_GUIDANCE_MODES):
            for scenario in SCENARIOS:
                compilation = compile_scenario_guidance(
                    scenario,
                    bundle=bundle,
                )
                test_prefix = (
                    f"requirement-compiled-{compilation.bundle_id}-{mode}"
                )
                for profile, effort in PRODUCER_CASES:
                    path = _producer_record_path(
                        artifact_root,
                        test_prefix=test_prefix,
                        scenario_id=scenario.scenario_id,
                        profile=profile,
                        effort=effort,
                        compilation_sha256=compilation.lock[
                            "compilation_sha256"
                        ],
                    )
                    record = _frozen_producer(
                        path,
                        variant=variant,
                        mode=mode,
                    )
                    identity = (
                        variant,
                        mode,
                        scenario.scenario_id,
                        record["candidate_id"],
                    )
                    records.append(record)
                    by_identity[identity] = record
    records.sort(
        key=lambda item: (
            item["variant"],
            item["mode"],
            item["scenario_id"],
            item["candidate_id"],
        )
    )
    return records, by_identity


def _semantic_paths(
    artifact_root: Path,
    *,
    dataset_id: str,
    scenario_id: str,
) -> list[Path]:
    pattern = (
        f"*requirement-semantic-{dataset_id}-{scenario_id}-*/"
        "records/semantic-evaluation.json"
    )
    return sorted((artifact_root / "glm" / "runs").glob(pattern))


def freeze_semantics(
    artifact_root: Path,
    producers: dict[tuple[str, str, str, str], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    records: list[dict[str, Any]] = []
    missing: list[dict[str, str]] = []
    for variant in VARIANT_BUNDLES:
        for mode in sorted(ROOT_GUIDANCE_MODES):
            for scenario in SCENARIOS:
                expected = {
                    candidate_id: producers[
                        (variant, mode, scenario.scenario_id, candidate_id)
                    ]["source_record_sha256"]
                    for profile, effort in PRODUCER_CASES
                    for candidate_id in (f"{profile}-{effort}",)
                }
                dataset_id = (
                    f"compiled-guidance-"
                    f"{producers[(variant, mode, scenario.scenario_id, next(iter(expected)))]['guidance_compilation']['bundle']['id']}"
                    f"-{mode}-20260917"
                )
                matching: list[Path] = []
                for path in _semantic_paths(
                    artifact_root,
                    dataset_id=dataset_id,
                    scenario_id=scenario.scenario_id,
                ):
                    value = _read_json(path)
                    actual = {
                        item["candidate_id"]: item["source_record_sha256"]
                        for item in value.get("candidate_sources", [])
                    }
                    if (
                        value.get("repeat_variant") == SEMANTIC_REPEAT_VARIANT
                        and actual == expected
                    ):
                        matching.append(path)
                if not matching:
                    missing.extend(
                        {
                            "variant": variant,
                            "mode": mode,
                            "scenario_id": scenario.scenario_id,
                            "candidate_id": candidate_id,
                        }
                        for candidate_id in sorted(expected)
                    )
                    continue
                path = matching[-1]
                value = _read_json(path)
                sources = {
                    item["candidate_id"]: item
                    for item in value["candidate_sources"]
                }
                for assessment in value["result"]["assessments"]:
                    candidate_id = assessment["candidate_id"]
                    records.append(
                        {
                            "dataset_id": value["dataset_id"],
                            "variant": variant,
                            "mode": mode,
                            "scenario_id": scenario.scenario_id,
                            "candidate_id": candidate_id,
                            "assessment": assessment,
                            "evaluator": value["evaluator"],
                            "response_repairs": value.get(
                                "response_repairs",
                                [],
                            ),
                            "candidate_source": sources[candidate_id],
                            "source_run_id": path.parents[1].name,
                            "source_record_sha256": _sha256(path),
                        }
                    )
    records.sort(
        key=lambda item: (
            item["variant"],
            item["mode"],
            item["scenario_id"],
            item["candidate_id"],
        )
    )
    return records, missing


def freeze_quality(
    artifact_root: Path,
    producers: dict[tuple[str, str, str, str], dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[dict[str, str]]]:
    records: list[dict[str, Any]] = []
    missing: list[dict[str, str]] = []
    paths = sorted(
        (artifact_root / "glm" / "runs").glob(
            "*/records/root-guidance-pairwise-quality.json"
        )
    )
    for mode in sorted(ROOT_GUIDANCE_MODES):
        for scenario in SCENARIOS:
            for profile, effort in PRODUCER_CASES:
                candidate_id = f"{profile}-{effort}"
                expected = {
                    variant: {
                        "source_record_sha256": producers[
                            (variant, mode, scenario.scenario_id, candidate_id)
                        ]["source_record_sha256"],
                        "compilation_sha256": producers[
                            (variant, mode, scenario.scenario_id, candidate_id)
                        ]["guidance_compilation"]["compilation_sha256"],
                    }
                    for variant in VARIANT_BUNDLES
                }
                matching: list[Path] = []
                for path in paths:
                    value = _read_json(path)
                    actual_sources = value.get("producer_sources")
                    sources_match = (
                        isinstance(actual_sources, dict)
                        and all(
                            isinstance(actual_sources.get(variant), dict)
                            and actual_sources[variant].get(
                                "source_record_sha256"
                            )
                            == expected[variant]["source_record_sha256"]
                            and actual_sources[variant].get(
                                "compilation_sha256"
                            )
                            == expected[variant]["compilation_sha256"]
                            for variant in VARIANT_BUNDLES
                        )
                    )
                    if (
                        value.get("repeat_variant") in QUALITY_REPEAT_VARIANTS
                        and value.get("mode") == mode
                        and value.get("scenario_id") == scenario.scenario_id
                        and value.get("candidate_id") == candidate_id
                        and sources_match
                    ):
                        matching.append(path)
                if not matching:
                    missing.append(
                        {
                            "mode": mode,
                            "scenario_id": scenario.scenario_id,
                            "candidate_id": candidate_id,
                        }
                    )
                    continue
                path = matching[-1]
                records.append(
                    {
                        **_read_json(path),
                        "source_run_id": path.parents[1].name,
                        "source_record_sha256": _sha256(path),
                    }
                )
    records.sort(
        key=lambda item: (
            item["mode"],
            item["scenario_id"],
            item["candidate_id"],
        )
    )
    return records, missing


def freeze_quality_errors(
    artifact_root: Path,
    valid_records: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    valid = {
        (
            item["scenario_id"],
            item["mode"],
            item["candidate_id"],
        )
        for item in valid_records
    }
    records: list[dict[str, Any]] = []
    for path in sorted(
        (artifact_root / "glm" / "runs").glob(
            "*/records/root-guidance-pairwise-quality-error.json"
        )
    ):
        value = _read_json(path)
        identity = (
            value.get("scenario_id"),
            value.get("mode"),
            value.get("candidate_id"),
        )
        if (
            value.get("repeat_variant") not in QUALITY_REPEAT_VARIANTS
            or identity in valid
        ):
            continue
        response = str(value.pop("response", ""))
        records.append(
            {
                **value,
                "response_chars": len(response),
                "response_sha256": hashlib.sha256(
                    response.encode("utf-8")
                ).hexdigest(),
                "response_excerpt": response[:500],
                "source_run_id": path.parents[1].name,
                "source_record_sha256": _sha256(path),
            }
        )
    return records


def freeze_matrix(
    artifact_root: Path = DEFAULT_ARTIFACT_ROOT,
) -> dict[str, Any]:
    producer_records, producers = freeze_producers(artifact_root)
    semantic_records, missing_semantics = freeze_semantics(
        artifact_root,
        producers,
    )
    quality_records, missing_quality = freeze_quality(
        artifact_root,
        producers,
    )
    quality_errors = freeze_quality_errors(artifact_root, quality_records)
    revisions = {
        record["guidance_compilation"]["bundle"]["git"]["revision"]
        for record in producer_records
    }
    return {
        "schema_version": 1,
        "dataset_id": "compiled-guidance-portable-matrix-20260918",
        "description": (
            "Portable baseline and combined-v2 matrix using fixture-owned "
            "targets and explicit root-only versus root-plus-TASKS delivery."
        ),
        "source_revisions": sorted(revisions),
        "semantic_repeat_variant": SEMANTIC_REPEAT_VARIANT,
        "quality_repeat_variants": list(QUALITY_REPEAT_VARIANTS),
        "producer_records": producer_records,
        "semantic_assessments": semantic_records,
        "semantic_errors": [],
        "missing_semantic_assessments": missing_semantics,
        "pairwise_quality_records": quality_records,
        "pairwise_quality_errors": quality_errors,
        "missing_pairwise_quality": missing_quality,
    }


def main() -> None:
    value = freeze_matrix(DEFAULT_ARTIFACT_ROOT.resolve())
    analysis = analyze_full_matrix(value)
    RESULT_ROOT.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    ANALYSIS_PATH.write_text(
        json.dumps(analysis, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"wrote {len(value['producer_records'])} producers, "
        f"{len(value['semantic_assessments'])} semantics, "
        f"{len(value['pairwise_quality_records'])} pairwise reviews, "
        f"{len(value['missing_semantic_assessments'])} missing semantics, "
        f"and {len(value['missing_pairwise_quality'])} missing reviews"
    )


if __name__ == "__main__":
    main()