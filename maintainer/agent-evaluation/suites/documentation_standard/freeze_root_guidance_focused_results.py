from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path
from typing import Any

from .requirement_quality_evaluator import DEFAULT_ARTIFACT_ROOT


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"
OUTPUT_PATH = FIXTURE_ROOT / "root_guidance_focused_results.json"
PROMPT_VERSION = "v4"

FocusedKey = tuple[str, str, str]
ProducerCase = tuple[str, str]

FOCUSED_CASES: dict[FocusedKey, tuple[ProducerCase, ...]] = {
    ("baseline", "root-only", "33-eleventy-archive-pagination"): (
        ("gpt", "max"),
    ),
    ("baseline", "root-only", "34-fastapi-notes-pagination"): (
        ("glm", "low"),
        ("glm", "high"),
        ("glm", "max"),
        ("gpt", "high"),
        ("gpt", "xhigh"),
    ),
    ("baseline", "root-only", "35-flask-vue-book-filter"): (
        ("glm", "low"),
        ("glm", "high"),
        ("glm", "max"),
        ("gpt", "medium"),
        ("gpt", "xhigh"),
    ),
    ("requirements", "root-only", "34-fastapi-notes-pagination"): (
        ("glm", "low"),
        ("gpt", "xhigh"),
    ),
    ("requirements", "root-only", "35-flask-vue-book-filter"): (
        ("glm", "low"),
        ("glm", "high"),
    ),
    ("testing", "root-only", "34-fastapi-notes-pagination"): (
        ("glm", "low"),
        ("glm", "high"),
        ("gpt", "high"),
        ("gpt", "xhigh"),
    ),
    ("testing", "root-only", "35-flask-vue-book-filter"): (
        ("glm", "max"),
        ("gpt", "medium"),
        ("gpt", "xhigh"),
    ),
    ("combined", "root-only", "33-eleventy-archive-pagination"): (
        ("gpt", "max"),
    ),
    ("combined", "root-only", "34-fastapi-notes-pagination"): (
        ("glm", "low"),
        ("glm", "high"),
        ("glm", "max"),
        ("gpt", "high"),
        ("gpt", "xhigh"),
    ),
    ("combined", "root-only", "35-flask-vue-book-filter"): (
        ("glm", "low"),
        ("glm", "high"),
        ("glm", "max"),
        ("gpt", "medium"),
        ("gpt", "xhigh"),
    ),
    ("requirements-v2", "root-only", "34-fastapi-notes-pagination"): (
        ("glm", "low"),
        ("gpt", "xhigh"),
    ),
    ("requirements-v2", "root-only", "35-flask-vue-book-filter"): (
        ("glm", "low"),
        ("glm", "high"),
    ),
    ("testing-v2", "root-only", "34-fastapi-notes-pagination"): (
        ("glm", "low"),
        ("gpt", "high"),
    ),
    ("testing-v2", "root-only", "35-flask-vue-book-filter"): (
        ("glm", "max"),
        ("gpt", "medium"),
    ),
    ("combined-v2", "root-only", "33-eleventy-archive-pagination"): (
        ("gpt", "max"),
    ),
    ("combined-v2", "root-only", "34-fastapi-notes-pagination"): (
        ("glm", "low"),
        ("glm", "high"),
        ("glm", "max"),
        ("gpt", "high"),
        ("gpt", "xhigh"),
    ),
    ("combined-v2", "root-only", "35-flask-vue-book-filter"): (
        ("glm", "low"),
        ("glm", "high"),
        ("glm", "max"),
        ("gpt", "medium"),
        ("gpt", "xhigh"),
    ),
    ("baseline", "task", "34-fastapi-notes-pagination"): (
        ("glm", "low"),
        ("glm", "high"),
        ("gpt", "high"),
        ("gpt", "xhigh"),
    ),
    ("baseline", "task", "35-flask-vue-book-filter"): (
        ("glm", "high"),
        ("gpt", "medium"),
        ("gpt", "xhigh"),
    ),
    ("combined-v2", "task", "34-fastapi-notes-pagination"): (
        ("glm", "low"),
        ("glm", "high"),
        ("gpt", "high"),
        ("gpt", "xhigh"),
    ),
    ("combined-v2", "task", "35-flask-vue-book-filter"): (
        ("glm", "high"),
        ("gpt", "medium"),
        ("gpt", "xhigh"),
    ),
}


def dataset_id(variant: str, mode: str) -> str:
    return f"root-guidance-{variant}-{mode}-20260917"


def test_prefix(variant: str, mode: str) -> str:
    return f"requirement-root-{variant}-{mode}"


def _read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(value, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _finding_passed(record: dict[str, Any], name: str) -> bool:
    return any(
        isinstance(item, dict)
        and item.get("name") == name
        and item.get("passed") is True
        for item in record.get("findings", [])
    )


def _producer_paths(
    artifact_root: Path,
    *,
    variant: str,
    mode: str,
    scenario_id: str,
    profile: str,
    effort: str,
) -> list[Path]:
    prefix = test_prefix(variant, mode)
    pattern = (
        f"*{prefix}-{scenario_id}-{effort}-*/"
        "records/root-guidance-requirement-quality.json"
    )
    paths: list[Path] = []
    expected_dataset = dataset_id(variant, mode)
    for path in sorted((artifact_root / profile / "runs").glob(pattern)):
        value = _read_json(path)
        producer = value.get("producer")
        if (
            value.get("dataset_id") == expected_dataset
            and value.get("scenario_id") == scenario_id
            and isinstance(producer, dict)
            and producer.get("profile") == profile
            and producer.get("reasoning_effort") == effort
        ):
            paths.append(path)
    return paths


def _frozen_producer(
    path: Path,
    *,
    variant: str,
    mode: str,
) -> dict[str, Any]:
    value = _read_json(path)
    guidance = dict(value["guidance"])
    guidance.pop("effective_message", None)
    return {
        "dataset_id": value["dataset_id"],
        "variant": variant,
        "mode": mode,
        "scenario_id": value["scenario_id"],
        "candidate_id": (
            f"{value['producer']['profile']}-"
            f"{value['producer']['reasoning_effort']}"
        ),
        "producer": value["producer"],
        "prompt": value["prompt"],
        "guidance": guidance,
        "changed_paths": value["changed_paths"],
        "generated_files": value["generated_files"],
        "response": value["response"],
        "findings": value["findings"],
        "source_run_id": path.parents[1].name,
        "source_record_sha256": _sha256(path),
    }


def freeze_producers(
    artifact_root: Path,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    records: list[dict[str, Any]] = []
    failed_attempts: list[dict[str, Any]] = []
    for (variant, mode, scenario_id), cases in FOCUSED_CASES.items():
        for profile, effort in cases:
            paths = _producer_paths(
                artifact_root,
                variant=variant,
                mode=mode,
                scenario_id=scenario_id,
                profile=profile,
                effort=effort,
            )
            if not paths:
                raise FileNotFoundError(
                    "missing focused producer record for "
                    f"{variant}/{mode}/{scenario_id}/{profile}-{effort}"
                )
            values = [(path, _read_json(path)) for path in paths]
            completed = [
                (path, value)
                for path, value in values
                if _finding_passed(value, "run completed")
            ]
            selected_path = (completed or values)[-1][0]
            records.append(
                _frozen_producer(
                    selected_path,
                    variant=variant,
                    mode=mode,
                )
            )
            for path, value in values:
                if path == selected_path or _finding_passed(
                    value,
                    "run completed",
                ):
                    continue
                failed_attempts.append(
                    {
                        "dataset_id": value["dataset_id"],
                        "variant": variant,
                        "mode": mode,
                        "scenario_id": scenario_id,
                        "candidate_id": f"{profile}-{effort}",
                        "findings": value["findings"],
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
    failed_attempts.sort(
        key=lambda item: (
            item["variant"],
            item["mode"],
            item["scenario_id"],
            item["candidate_id"],
            item["source_run_id"],
        )
    )
    return records, failed_attempts


def _semantic_paths(
    artifact_root: Path,
    *,
    variant: str,
    mode: str,
    scenario_id: str,
) -> list[Path]:
    expected_dataset = dataset_id(variant, mode)
    pattern = (
        f"*requirement-semantic-{expected_dataset}-{scenario_id}-*/"
        "records/semantic-evaluation.json"
    )
    paths: list[Path] = []
    for path in sorted((artifact_root / "glm" / "runs").glob(pattern)):
        value = _read_json(path)
        evaluator = value.get("evaluator")
        if (
            value.get("dataset_id") == expected_dataset
            and value.get("scenario_id") == scenario_id
            and isinstance(evaluator, dict)
            and evaluator.get("prompt_version") == PROMPT_VERSION
        ):
            paths.append(path)
    return paths


def _semantic_error_paths(
    artifact_root: Path,
    *,
    variant: str,
    mode: str,
    scenario_id: str,
) -> list[Path]:
    expected_dataset = dataset_id(variant, mode)
    pattern = (
        f"*requirement-semantic-{expected_dataset}-{scenario_id}-*/"
        "records/semantic-evaluation-error.json"
    )
    return sorted((artifact_root / "glm" / "runs").glob(pattern))


def freeze_semantics(
    artifact_root: Path,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, str]],
]:
    selected: dict[
        tuple[str, str, str, str],
        dict[str, Any],
    ] = {}
    errors: list[dict[str, Any]] = []
    missing: list[dict[str, str]] = []
    grouped_keys = sorted({key for key in FOCUSED_CASES})
    for variant, mode, scenario_id in grouped_keys:
        wanted = {
            f"{profile}-{effort}"
            for profile, effort in FOCUSED_CASES[
                (variant, mode, scenario_id)
            ]
        }
        for path in _semantic_paths(
            artifact_root,
            variant=variant,
            mode=mode,
            scenario_id=scenario_id,
        ):
            value = _read_json(path)
            assessments = value.get("result", {}).get("assessments", [])
            sources = {
                item["candidate_id"]: item
                for item in value.get("candidate_sources", [])
                if isinstance(item, dict) and "candidate_id" in item
            }
            for assessment in assessments:
                if not isinstance(assessment, dict):
                    continue
                candidate_id = assessment.get("candidate_id")
                if candidate_id not in wanted:
                    continue
                selected[(variant, mode, scenario_id, candidate_id)] = {
                    "dataset_id": value["dataset_id"],
                    "variant": variant,
                    "mode": mode,
                    "scenario_id": scenario_id,
                    "candidate_id": candidate_id,
                    "assessment": assessment,
                    "evaluator": value["evaluator"],
                    "response_repairs": value.get("response_repairs", []),
                    "candidate_source": sources.get(candidate_id),
                    "source_run_id": path.parents[1].name,
                    "source_record_sha256": _sha256(path),
                }
        for path in _semantic_error_paths(
            artifact_root,
            variant=variant,
            mode=mode,
            scenario_id=scenario_id,
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
        for candidate_id in sorted(wanted):
            if (variant, mode, scenario_id, candidate_id) not in selected:
                missing.append(
                    {
                        "variant": variant,
                        "mode": mode,
                        "scenario_id": scenario_id,
                        "candidate_id": candidate_id,
                    }
                )
    records = [
        selected[key]
        for key in sorted(selected)
    ]
    errors.sort(
        key=lambda item: (
            item["variant"],
            item["mode"],
            item["scenario_id"],
            item["source_run_id"],
        )
    )
    return records, errors, missing


def freeze_focused_results(
    artifact_root: Path = DEFAULT_ARTIFACT_ROOT,
) -> dict[str, Any]:
    producers, producer_failures = freeze_producers(artifact_root)
    semantics, semantic_errors, missing_semantics = freeze_semantics(
        artifact_root
    )
    revision = subprocess.run(
        ["git", "rev-parse", "HEAD"],
        cwd=Path(__file__).resolve().parents[4],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()
    return {
        "schema_version": 1,
        "dataset_id": "root-guidance-focused-20260917",
        "description": (
            "Focused root Requirements and Testing baseline, isolated "
            "candidates, and root-plus-TASKS comparisons."
        ),
        "source_revision": revision,
        "selection": [
            {
                "variant": variant,
                "mode": mode,
                "scenario_id": scenario_id,
                "candidate_ids": [
                    f"{profile}-{effort}"
                    for profile, effort in cases
                ],
            }
            for (variant, mode, scenario_id), cases in sorted(
                FOCUSED_CASES.items()
            )
        ],
        "producer_records": producers,
        "producer_failed_attempts": producer_failures,
        "semantic_assessments": semantics,
        "semantic_errors": semantic_errors,
        "missing_semantic_assessments": missing_semantics,
    }


def main() -> None:
    value = freeze_focused_results(DEFAULT_ARTIFACT_ROOT.resolve())
    OUTPUT_PATH.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"wrote {len(value['producer_records'])} producer records, "
        f"{len(value['semantic_assessments'])} semantic assessments, "
        f"{len(value['producer_failed_attempts'])} failed producer attempts, "
        f"{len(value['semantic_errors'])} semantic errors, and "
        f"{len(value['missing_semantic_assessments'])} missing assessments"
    )


if __name__ == "__main__":
    main()