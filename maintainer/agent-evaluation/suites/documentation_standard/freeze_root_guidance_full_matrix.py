from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from .requirement_quality import (
    PRODUCER_CASES,
    ROOT_GUIDANCE_MODES,
    SCENARIOS,
)
from .requirement_quality_evaluator import DEFAULT_ARTIFACT_ROOT
from .root_guidance_quality import QUALITY_PROMPT_VERSION


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"
OUTPUT_PATH = FIXTURE_ROOT / "root_guidance_full_matrix_results.json"
PRODUCER_REPEAT_VARIANT = "full-matrix-r1"
SEMANTIC_REPEAT_VARIANT = "full-matrix-r1"
QUALITY_REPEAT_VARIANT = "full-matrix-r1"
VARIANTS = ("baseline", "combined-v2")
MODES = tuple(sorted(ROOT_GUIDANCE_MODES))


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _producer_path(
    artifact_root: Path,
    *,
    variant: str,
    mode: str,
    scenario_id: str,
    profile: str,
    effort: str,
) -> Path:
    dataset_id = f"root-guidance-{variant}-{mode}-20260917"
    test_prefix = f"requirement-root-{variant}-{mode}"
    pattern = (
        f"*{test_prefix}-{scenario_id}-{effort}-*/"
        "records/root-guidance-requirement-quality.json"
    )
    matching: list[Path] = []
    for path in sorted((artifact_root / profile / "runs").glob(pattern)):
        value = _read_json(path)
        producer = value.get("producer")
        if (
            value.get("dataset_id") == dataset_id
            and value.get("repeat_variant") == PRODUCER_REPEAT_VARIANT
            and isinstance(producer, dict)
            and producer.get("profile") == profile
            and producer.get("reasoning_effort") == effort
        ):
            matching.append(path)
    if not matching:
        raise FileNotFoundError(
            "missing full-matrix producer record for "
            f"{variant}/{mode}/{scenario_id}/{profile}-{effort}"
        )
    return matching[-1]


def _freeze_producer(
    path: Path,
    *,
    variant: str,
    mode: str,
) -> dict[str, Any]:
    value = _read_json(path)
    guidance = dict(value["guidance"])
    guidance.pop("effective_message", None)
    producer = value["producer"]
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
        "changed_paths": value["changed_paths"],
        "generated_files": value["generated_files"],
        "response": value["response"],
        "findings": value["findings"],
        "source_run_id": path.parents[1].name,
        "source_record_sha256": _sha256(path),
    }


def freeze_producers(artifact_root: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for variant in VARIANTS:
        for mode in MODES:
            for scenario in SCENARIOS:
                for profile, effort in PRODUCER_CASES:
                    path = _producer_path(
                        artifact_root,
                        variant=variant,
                        mode=mode,
                        scenario_id=scenario.scenario_id,
                        profile=profile,
                        effort=effort,
                    )
                    records.append(
                        _freeze_producer(
                            path,
                            variant=variant,
                            mode=mode,
                        )
                    )
    records.sort(
        key=lambda item: (
            item["variant"],
            item["mode"],
            item["scenario_id"],
            item["candidate_id"],
        )
    )
    return records


def _semantic_paths(
    artifact_root: Path,
    *,
    variant: str,
    mode: str,
    scenario_id: str,
    record_name: str,
) -> list[Path]:
    dataset_id = f"root-guidance-{variant}-{mode}-20260917"
    pattern = (
        f"*requirement-semantic-{dataset_id}-{scenario_id}-*/"
        f"records/{record_name}"
    )
    matching: list[Path] = []
    for path in sorted((artifact_root / "glm" / "runs").glob(pattern)):
        value = _read_json(path)
        if (
            value.get("dataset_id") == dataset_id
            and value.get("scenario_id") == scenario_id
            and value.get("repeat_variant") == SEMANTIC_REPEAT_VARIANT
        ):
            matching.append(path)
    return matching


def freeze_semantics(
    artifact_root: Path,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, str]],
]:
    records: dict[
        tuple[str, str, str, str],
        dict[str, Any],
    ] = {}
    errors: list[dict[str, Any]] = []
    missing: list[dict[str, str]] = []
    for variant in VARIANTS:
        for mode in MODES:
            for scenario in SCENARIOS:
                for path in _semantic_paths(
                    artifact_root,
                    variant=variant,
                    mode=mode,
                    scenario_id=scenario.scenario_id,
                    record_name="semantic-evaluation.json",
                ):
                    value = _read_json(path)
                    sources = {
                        item["candidate_id"]: item
                        for item in value.get("candidate_sources", [])
                    }
                    for assessment in value["result"]["assessments"]:
                        candidate_id = assessment["candidate_id"]
                        records[
                            (
                                variant,
                                mode,
                                scenario.scenario_id,
                                candidate_id,
                            )
                        ] = {
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
                            "candidate_source": sources.get(candidate_id),
                            "source_run_id": path.parents[1].name,
                            "source_record_sha256": _sha256(path),
                        }
                for path in _semantic_paths(
                    artifact_root,
                    variant=variant,
                    mode=mode,
                    scenario_id=scenario.scenario_id,
                    record_name="semantic-evaluation-error.json",
                ):
                    value = _read_json(path)
                    response = str(value.pop("response", ""))
                    errors.append(
                        {
                            **value,
                            "variant": variant,
                            "mode": mode,
                            "response_chars": len(response),
                            "response_sha256": hashlib.sha256(
                                response.encode("utf-8")
                            ).hexdigest(),
                            "response_excerpt": response[:500],
                            "source_run_id": path.parents[1].name,
                            "source_record_sha256": _sha256(path),
                        }
                    )
                for profile, effort in PRODUCER_CASES:
                    candidate_id = f"{profile}-{effort}"
                    key = (
                        variant,
                        mode,
                        scenario.scenario_id,
                        candidate_id,
                    )
                    if key not in records:
                        missing.append(
                            {
                                "variant": variant,
                                "mode": mode,
                                "scenario_id": scenario.scenario_id,
                                "candidate_id": candidate_id,
                            }
                        )
    return (
        [records[key] for key in sorted(records)],
        sorted(
            errors,
            key=lambda item: (
                item["variant"],
                item["mode"],
                item["scenario_id"],
                item["source_run_id"],
            ),
        ),
        missing,
    )


def _quality_paths(
    artifact_root: Path,
    *,
    scenario_id: str,
    mode: str,
    candidate_id: str,
    record_name: str,
) -> list[Path]:
    pattern = (
        f"*root-guidance-quality-{scenario_id}-{mode}-{candidate_id}-*/"
        f"records/{record_name}"
    )
    matching: list[Path] = []
    for path in sorted((artifact_root / "glm" / "runs").glob(pattern)):
        value = _read_json(path)
        evaluator = value.get("evaluator")
        if (
            value.get("scenario_id") == scenario_id
            and value.get("mode") == mode
            and value.get("candidate_id") == candidate_id
            and value.get("repeat_variant") == QUALITY_REPEAT_VARIANT
            and (
                record_name.endswith("-error.json")
                or (
                    isinstance(evaluator, dict)
                    and evaluator.get("prompt_version")
                    == QUALITY_PROMPT_VERSION
                )
            )
        ):
            matching.append(path)
    return matching


def freeze_quality(
    artifact_root: Path,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, str]],
]:
    records: list[dict[str, Any]] = []
    errors: list[dict[str, Any]] = []
    missing: list[dict[str, str]] = []
    for mode in MODES:
        for scenario in SCENARIOS:
            for profile, effort in PRODUCER_CASES:
                candidate_id = f"{profile}-{effort}"
                paths = _quality_paths(
                    artifact_root,
                    scenario_id=scenario.scenario_id,
                    mode=mode,
                    candidate_id=candidate_id,
                    record_name="root-guidance-pairwise-quality.json",
                )
                if paths:
                    path = paths[-1]
                    records.append(
                        {
                            **_read_json(path),
                            "source_run_id": path.parents[1].name,
                            "source_record_sha256": _sha256(path),
                        }
                    )
                else:
                    missing.append(
                        {
                            "mode": mode,
                            "scenario_id": scenario.scenario_id,
                            "candidate_id": candidate_id,
                        }
                    )
                for path in _quality_paths(
                    artifact_root,
                    scenario_id=scenario.scenario_id,
                    mode=mode,
                    candidate_id=candidate_id,
                    record_name="root-guidance-pairwise-quality-error.json",
                ):
                    value = _read_json(path)
                    response = str(value.pop("response", ""))
                    errors.append(
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
    records.sort(
        key=lambda item: (
            item["mode"],
            item["scenario_id"],
            item["candidate_id"],
        )
    )
    errors.sort(
        key=lambda item: (
            item["mode"],
            item["scenario_id"],
            item["candidate_id"],
            item["source_run_id"],
        )
    )
    return records, errors, missing


def freeze_full_matrix(
    artifact_root: Path = DEFAULT_ARTIFACT_ROOT,
) -> dict[str, Any]:
    producers = freeze_producers(artifact_root)
    semantics, semantic_errors, missing_semantics = freeze_semantics(
        artifact_root
    )
    quality, quality_errors, missing_quality = freeze_quality(artifact_root)
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(__file__).resolve().parents[4],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {
        "schema_version": 1,
        "dataset_id": "root-guidance-full-matrix-20260917",
        "description": (
            "Fresh full paired baseline and combined-v2 matrix across "
            "three scenarios, seven model/effort profiles, and two guidance "
            "delivery modes."
        ),
        "source_revision": revision,
        "producer_repeat_variant": PRODUCER_REPEAT_VARIANT,
        "semantic_repeat_variant": SEMANTIC_REPEAT_VARIANT,
        "quality_repeat_variant": QUALITY_REPEAT_VARIANT,
        "producer_records": producers,
        "semantic_assessments": semantics,
        "semantic_errors": semantic_errors,
        "missing_semantic_assessments": missing_semantics,
        "pairwise_quality_records": quality,
        "pairwise_quality_errors": quality_errors,
        "missing_pairwise_quality": missing_quality,
    }


def main() -> None:
    value = freeze_full_matrix(DEFAULT_ARTIFACT_ROOT.resolve())
    OUTPUT_PATH.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"wrote {len(value['producer_records'])} producers, "
        f"{len(value['semantic_assessments'])} semantics, and "
        f"{len(value['pairwise_quality_records'])} pairwise reviews"
    )


if __name__ == "__main__":
    main()