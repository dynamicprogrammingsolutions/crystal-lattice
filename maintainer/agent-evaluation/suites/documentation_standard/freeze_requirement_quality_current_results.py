from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from .requirement_quality import SCENARIOS
from .requirement_quality_evaluator import (
    ACCEPTED_BASELINE_PATH,
    DEFAULT_ARTIFACT_ROOT,
    EVALUATOR_PROMPT_VERSION,
    load_task_dataset,
)


FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures"
TASK_DATASET_OUTPUT = (
    FIXTURE_ROOT / "current_task_guidance_requirement_quality_dataset.json"
)
SEMANTIC_RESULTS_OUTPUT = (
    FIXTURE_ROOT / "requirement_quality_semantic_results.json"
)
DATASET_IDS = (
    "initial-minimal-guidance-20260914",
    "current-task-guidance-20260914",
)


def _semantic_record_path(
    *,
    artifact_root: Path,
    dataset_id: str,
    scenario_id: str,
) -> Path:
    pattern = (
        f"*requirement-semantic-{dataset_id}-{scenario_id}-*/"
        "records/semantic-evaluation.json"
    )
    candidates = sorted((artifact_root / "glm" / "runs").glob(pattern))
    matching: list[Path] = []
    for path in candidates:
        value = json.loads(path.read_text(encoding="utf-8"))
        evaluator = value.get("evaluator")
        if (
            value.get("dataset_id") == dataset_id
            and value.get("scenario_id") == scenario_id
            and isinstance(evaluator, dict)
            and evaluator.get("prompt_version") == EVALUATOR_PROMPT_VERSION
        ):
            matching.append(path)
    if not matching:
        raise FileNotFoundError(
            f"missing v2 semantic result for {dataset_id}/{scenario_id}"
        )
    return matching[-1]


def freeze_task_dataset(artifact_root: Path) -> dict[str, Any]:
    dataset = load_task_dataset(artifact_root)
    guidance_values = [record.pop("guidance") for record in dataset["records"]]
    first = guidance_values[0]
    if any(value != first for value in guidance_values[1:]):
        raise ValueError("task dataset records do not share exact guidance")
    dataset["guidance"] = first
    return dataset


def freeze_semantic_results(artifact_root: Path) -> dict[str, Any]:
    values: list[dict[str, Any]] = []
    for dataset_id in DATASET_IDS:
        for scenario in SCENARIOS:
            source = _semantic_record_path(
                artifact_root=artifact_root,
                dataset_id=dataset_id,
                scenario_id=scenario.scenario_id,
            )
            raw = source.read_bytes()
            value = json.loads(raw)
            values.append(
                {
                    **value,
                    "source_run_id": source.parents[1].name,
                    "source_record_sha256": hashlib.sha256(raw).hexdigest(),
                }
            )
    return {
        "schema_version": 1,
        "description": (
            "Calibrated GLM-max semantic results for the accepted initial "
            "baseline and current-guidance task-file dataset."
        ),
        "accepted_dataset_source": str(
            ACCEPTED_BASELINE_PATH.relative_to(Path(__file__).resolve().parent)
        ),
        "results": values,
    }


def _write(path: Path, value: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> None:
    artifact_root = DEFAULT_ARTIFACT_ROOT.resolve()
    task_dataset = freeze_task_dataset(artifact_root)
    semantic_results = freeze_semantic_results(artifact_root)
    _write(TASK_DATASET_OUTPUT, task_dataset)
    _write(SEMANTIC_RESULTS_OUTPUT, semantic_results)
    print(
        f"wrote {len(task_dataset['records'])} task records and "
        f"{len(semantic_results['results'])} semantic batches"
    )


if __name__ == "__main__":
    main()