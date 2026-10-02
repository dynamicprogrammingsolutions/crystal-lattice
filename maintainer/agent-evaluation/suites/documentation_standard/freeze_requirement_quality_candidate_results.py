from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .requirement_quality import SCENARIOS
from .requirement_quality_evaluator import (
    DEFAULT_ARTIFACT_ROOT,
    load_candidate_task_dataset,
    load_candidate_v2_task_dataset,
    load_candidate_v3_task_dataset,
)


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"
VARIANTS = {
    "v1": {
        "dataset_id": "candidate-task-guidance-20260915",
        "prompt_version": "v2",
        "loader": load_candidate_task_dataset,
        "task_output": (
            FIXTURE_ROOT
            / "candidate_task_guidance_requirement_quality_dataset.json"
        ),
        "semantic_output": (
            FIXTURE_ROOT / "requirement_quality_candidate_semantic_results.json"
        ),
    },
    "v2": {
        "dataset_id": "candidate-task-guidance-v2-20260915",
        "prompt_version": "v2",
        "loader": load_candidate_v2_task_dataset,
        "task_output": (
            FIXTURE_ROOT
            / "candidate_v2_task_guidance_requirement_quality_dataset.json"
        ),
        "semantic_output": (
            FIXTURE_ROOT
            / "requirement_quality_candidate_v2_semantic_results.json"
        ),
    },
    "v3": {
        "dataset_id": "candidate-task-guidance-v3-20260915",
        "prompt_version": "v3",
        "loader": load_candidate_v3_task_dataset,
        "task_output": (
            FIXTURE_ROOT
            / "candidate_v3_task_guidance_requirement_quality_dataset.json"
        ),
        "semantic_output": (
            FIXTURE_ROOT
            / "requirement_quality_candidate_v3_semantic_results.json"
        ),
    },
}


def _semantic_record_path(
    artifact_root: Path,
    scenario_id: str,
    dataset_id: str,
    prompt_version: str,
) -> Path:
    pattern = (
        f"*requirement-semantic-{dataset_id}-{scenario_id}-*/"
        "records/semantic-evaluation.json"
    )
    paths = sorted((artifact_root / "glm" / "runs").glob(pattern))
    matching: list[Path] = []
    for path in paths:
        value = json.loads(path.read_text(encoding="utf-8"))
        evaluator = value.get("evaluator")
        if (
            value.get("dataset_id") == dataset_id
            and value.get("scenario_id") == scenario_id
            and isinstance(evaluator, dict)
            and evaluator.get("prompt_version") == prompt_version
        ):
            matching.append(path)
    if not matching:
        raise FileNotFoundError(
            f"missing candidate semantic result for {scenario_id}"
        )
    return matching[-1]


def freeze_candidate_dataset(
    artifact_root: Path,
    *,
    variant: str,
) -> dict[str, Any]:
    dataset = VARIANTS[variant]["loader"](artifact_root)
    guidance_values = [record.pop("guidance") for record in dataset["records"]]
    first = guidance_values[0]
    if any(value != first for value in guidance_values[1:]):
        raise ValueError("candidate records do not share exact guidance")
    dataset["guidance"] = first
    return dataset


def freeze_candidate_semantic_results(
    artifact_root: Path,
    *,
    variant: str,
) -> dict[str, Any]:
    dataset_id = str(VARIANTS[variant]["dataset_id"])
    prompt_version = str(VARIANTS[variant]["prompt_version"])
    results: list[dict[str, Any]] = []
    for scenario in SCENARIOS:
        source = _semantic_record_path(
            artifact_root,
            scenario.scenario_id,
            dataset_id,
            prompt_version,
        )
        raw = source.read_bytes()
        results.append(
            {
                **json.loads(raw),
                "source_run_id": source.parents[1].name,
                "source_record_sha256": hashlib.sha256(raw).hexdigest(),
            }
        )
    return {
        "schema_version": 1,
        "dataset_id": dataset_id,
        "description": (
            "Calibrated semantic requirement/testing results for the "
            "September 15 candidate documentation and TASKS-v7 guidance."
        ),
        "results": results,
    }


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Freeze candidate task and semantic requirement results.",
    )
    parser.add_argument(
        "--variant",
        choices=tuple(VARIANTS),
        default="v2",
    )
    args = parser.parse_args()
    variant = str(args.variant)
    artifact_root = DEFAULT_ARTIFACT_ROOT.resolve()
    dataset = freeze_candidate_dataset(artifact_root, variant=variant)
    semantic = freeze_candidate_semantic_results(
        artifact_root,
        variant=variant,
    )
    _write(Path(VARIANTS[variant]["task_output"]), dataset)
    _write(Path(VARIANTS[variant]["semantic_output"]), semantic)
    print(
        f"wrote {len(dataset['records'])} {variant} candidate task records and "
        f"{len(semantic['results'])} semantic batches"
    )


if __name__ == "__main__":
    main()