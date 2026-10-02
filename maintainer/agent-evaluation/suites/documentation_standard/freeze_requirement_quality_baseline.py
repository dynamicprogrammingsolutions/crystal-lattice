from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any

from .requirement_quality import PRODUCER_CASES, SCENARIOS, load_target, target_sha256
from .support import REPOSITORY_ROOT


DEFAULT_ARTIFACT_ROOT = (
    REPOSITORY_ROOT / "tmp" / "agent-evaluation" / "documentation-standard"
)
DEFAULT_OUTPUT = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "accepted_requirement_quality_baseline.json"
)
PRODUCT_TARGET_KEYS = (
    "schema_version",
    "scenario_id",
    "title",
    "task_summary",
    "project",
    "required_outcomes",
    "compatibility_constraints",
    "acceptable_grouping",
    "supporting_details",
    "optional_adjacent_work",
    "not_prescribed",
    "open_questions",
)


def _product_target(value: dict[str, Any]) -> dict[str, Any]:
    return {key: value.get(key) for key in PRODUCT_TARGET_KEYS}


def _record_path(
    artifact_root: Path,
    *,
    scenario_id: str,
    profile: str,
    effort: str,
) -> Path:
    pattern = (
        f"*requirement-baseline-{scenario_id}-{effort}-*/"
        "records/requirement-baseline.json"
    )
    paths = sorted((artifact_root / profile / "runs").glob(pattern))
    if not paths:
        raise FileNotFoundError(
            f"missing baseline record for {scenario_id}/{profile}/{effort}"
        )
    matching: list[Path] = []
    for path in paths:
        value = json.loads(path.read_text(encoding="utf-8"))
        producer = value.get("producer")
        if (
            isinstance(producer, dict)
            and producer.get("profile") == profile
            and producer.get("reasoning_effort") == effort
        ):
            matching.append(path)
    if not matching:
        raise ValueError(
            f"no matching producer record for {scenario_id}/{profile}/{effort}"
        )
    return matching[-1]


def freeze_baseline(artifact_root: Path) -> dict[str, Any]:
    records: list[dict[str, Any]] = []
    for scenario in SCENARIOS:
        for profile, effort in PRODUCER_CASES:
            source = _record_path(
                artifact_root,
                scenario_id=scenario.scenario_id,
                profile=profile,
                effort=effort,
            )
            raw = source.read_bytes()
            value = json.loads(raw)
            source_target = value.get("target")
            current_target = load_target(scenario)
            if (
                not isinstance(source_target, dict)
                or _product_target(source_target) != _product_target(current_target)
            ):
                raise ValueError(
                    f"product target changed for {scenario.scenario_id}: {source}"
                )
            generated_files = value.get("generated_files")
            if not isinstance(generated_files, dict) or not generated_files:
                raise ValueError(f"record has no generated files: {source}")
            records.append(
                {
                    "candidate_id": f"{profile}-{effort}",
                    "scenario_id": scenario.scenario_id,
                    "producer": value["producer"],
                    "generated_files": generated_files,
                    "changed_paths": value["changed_paths"],
                    "source_run_id": source.parents[1].name,
                    "source_record_sha256": hashlib.sha256(raw).hexdigest(),
                    "source_target_sha256": value.get("target_sha256"),
                    "current_target_sha256": target_sha256(scenario),
                }
            )
    return {
        "schema_version": 1,
        "dataset_id": "initial-minimal-guidance-20260914",
        "description": (
            "Immutable candidate documentation from the user-accepted "
            "September 14, 2026 requirement-quality baseline."
        ),
        "records": records,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--artifact-root",
        type=Path,
        default=DEFAULT_ARTIFACT_ROOT,
    )
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()

    value = freeze_baseline(args.artifact_root.resolve())
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        json.dumps(value, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"wrote {len(value['records'])} records to {args.output}")


if __name__ == "__main__":
    main()