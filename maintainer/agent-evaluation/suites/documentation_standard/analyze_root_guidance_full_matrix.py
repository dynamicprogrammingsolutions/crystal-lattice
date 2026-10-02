from __future__ import annotations

import json
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Callable

from .freeze_root_guidance_full_matrix import OUTPUT_PATH as MATRIX_PATH
from .root_guidance_scoring import (
    EFFORT_POLICIES,
    aggregate_scored_cells,
    score_semantic_assessment,
)


ANALYSIS_PATH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "root_guidance_full_matrix_analysis.json"
)


def _candidate_effort(candidate_id: str) -> str:
    return candidate_id.split("-", 1)[1]


def _grouped_scores(
    cells: list[dict[str, Any]],
    key: Callable[[dict[str, Any]], tuple[str, ...]],
) -> list[dict[str, Any]]:
    grouped: dict[tuple[str, ...], list[dict[str, Any]]] = defaultdict(list)
    for cell in cells:
        grouped[key(cell)].append(cell)
    return [
        {
            "group": list(group),
            **aggregate_scored_cells(values),
        }
        for group, values in sorted(grouped.items())
    ]


def analyze_full_matrix(value: dict[str, Any]) -> dict[str, Any]:
    scored: list[dict[str, Any]] = []
    for record in value["semantic_assessments"]:
        effort = _candidate_effort(record["candidate_id"])
        scored.append(
            {
                "variant": record["variant"],
                "mode": record["mode"],
                "scenario_id": record["scenario_id"],
                "candidate_id": record["candidate_id"],
                "effort": effort,
                "assessment": record["assessment"],
                "scores": score_semantic_assessment(
                    record["assessment"],
                    effort=effort,
                ),
            }
        )

    by_identity = {
        (
            item["variant"],
            item["mode"],
            item["scenario_id"],
            item["candidate_id"],
        ): item
        for item in scored
    }
    paired_deltas: list[dict[str, Any]] = []
    for mode, scenario_id, candidate_id in sorted(
        {
            (
                item["mode"],
                item["scenario_id"],
                item["candidate_id"],
            )
            for item in scored
        }
    ):
        baseline = by_identity[
            ("baseline", mode, scenario_id, candidate_id)
        ]
        candidate = by_identity[
            ("combined-v2", mode, scenario_id, candidate_id)
        ]
        paired_deltas.append(
            {
                "mode": mode,
                "scenario_id": scenario_id,
                "candidate_id": candidate_id,
                "effort": baseline["effort"],
                "coverage_delta": (
                    candidate["scores"]["coverage_score"]
                    - baseline["scores"]["coverage_score"]
                ),
                "scope_delta": (
                    candidate["scores"]["scope_score"]
                    - baseline["scores"]["scope_score"]
                ),
                "testing_delta": (
                    candidate["scores"]["testing_score"]
                    - baseline["scores"]["testing_score"]
                ),
                "baseline_expectation_met": baseline["scores"][
                    "effort_expectation_met"
                ],
                "combined_v2_expectation_met": candidate["scores"][
                    "effort_expectation_met"
                ],
            }
        )

    quality = value["pairwise_quality_records"]

    def preference_counts(
        records: list[dict[str, Any]],
        *,
        dimension: str | None = None,
    ) -> dict[str, int]:
        if dimension is None:
            values = [
                item["result"]["overall_preference"]
                for item in records
            ]
        else:
            values = [
                next(
                    review["preferred"]
                    for review in item["result"]["dimension_reviews"]
                    if review["dimension"] == dimension
                )
                for item in records
            ]
        return dict(Counter(values))

    quality_groups: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(
        list
    )
    for record in quality:
        quality_groups[("candidate", record["candidate_id"])].append(record)
        quality_groups[
            ("effort", _candidate_effort(record["candidate_id"]))
        ].append(record)
        quality_groups[("mode", record["mode"])].append(record)
        quality_groups[("scenario", record["scenario_id"])].append(record)

    pairwise_groups = []
    for group, records in sorted(quality_groups.items()):
        pairwise_groups.append(
            {
                "group": list(group),
                "cells": len(records),
                "overall_preferences": preference_counts(records),
                "requirements_preferences": preference_counts(
                    records,
                    dimension="requirements",
                ),
                "testing_preferences": preference_counts(
                    records,
                    dimension="testing",
                ),
                "plan_usability_preferences": preference_counts(
                    records,
                    dimension="plan_usability",
                ),
                "average_scores": {
                    variant: {
                        metric: round(
                            sum(
                                item["result"]["scores"][variant][metric]
                                for item in records
                            )
                            / len(records),
                            2,
                        )
                        for metric in next(
                            iter(records)
                        )["result"]["scores"][variant]
                    }
                    for variant in ("baseline", "combined-v2")
                },
            }
        )

    effects = Counter(
        effect["likely_cause"]
        for record in quality
        for effect in record["result"]["guidance_effects"]
    )

    producer_failures = [
        {
            "variant": record["variant"],
            "mode": record["mode"],
            "scenario_id": record["scenario_id"],
            "candidate_id": record["candidate_id"],
            "failed_findings": [
                finding
                for finding in record["findings"]
                if not finding["passed"]
            ],
        }
        for record in value["producer_records"]
        if any(not finding["passed"] for finding in record["findings"])
    ]

    return {
        "schema_version": 1,
        "dataset_id": value["dataset_id"],
        "effort_policies": EFFORT_POLICIES,
        "counts": {
            "producer_records": len(value["producer_records"]),
            "semantic_assessments": len(value["semantic_assessments"]),
            "pairwise_quality_records": len(
                value["pairwise_quality_records"]
            ),
            "producer_failures": len(producer_failures),
            "semantic_errors": len(value["semantic_errors"]),
            "missing_semantic_assessments": len(
                value["missing_semantic_assessments"]
            ),
            "pairwise_quality_errors": len(
                value["pairwise_quality_errors"]
            ),
            "missing_pairwise_quality": len(
                value["missing_pairwise_quality"]
            ),
        },
        "score_groups": {
            "variant": _grouped_scores(
                scored,
                lambda item: (item["variant"],),
            ),
            "variant_mode": _grouped_scores(
                scored,
                lambda item: (item["variant"], item["mode"]),
            ),
            "variant_candidate": _grouped_scores(
                scored,
                lambda item: (
                    item["variant"],
                    item["candidate_id"],
                ),
            ),
            "variant_effort": _grouped_scores(
                scored,
                lambda item: (item["variant"], item["effort"]),
            ),
            "variant_scenario": _grouped_scores(
                scored,
                lambda item: (
                    item["variant"],
                    item["scenario_id"],
                ),
            ),
        },
        "paired_score_deltas": paired_deltas,
        "pairwise_quality": {
            "overall_preferences": preference_counts(quality),
            "requirements_preferences": preference_counts(
                quality,
                dimension="requirements",
            ),
            "testing_preferences": preference_counts(
                quality,
                dimension="testing",
            ),
            "plan_usability_preferences": preference_counts(
                quality,
                dimension="plan_usability",
            ),
            "groups": pairwise_groups,
            "likely_cause_counts": dict(effects),
        },
        "producer_failures": producer_failures,
    }


def main() -> None:
    value = json.loads(MATRIX_PATH.read_text(encoding="utf-8"))
    analysis = analyze_full_matrix(value)
    ANALYSIS_PATH.write_text(
        json.dumps(analysis, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(
        f"wrote analysis for {analysis['counts']['semantic_assessments']} "
        "semantic cells and "
        f"{analysis['counts']['pairwise_quality_records']} quality pairs"
    )


if __name__ == "__main__":
    main()