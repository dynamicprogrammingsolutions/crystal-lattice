from __future__ import annotations

from collections import Counter
from typing import Any, Iterable


HIGH_ASSURANCE_EFFORTS = {"high", "xhigh", "max"}
EFFORT_POLICIES = {
    "low": {
        "require_complete_requirements": False,
        "maximum_expansion": "medium",
        "require_complete_testing": False,
        "require_real_crossing": False,
        "description": (
            "Completeness shortfalls are descriptive; material scope "
            "invention and unusable testing remain failures."
        ),
    },
    "medium": {
        "require_complete_requirements": True,
        "maximum_expansion": "medium",
        "require_complete_testing": False,
        "require_real_crossing": True,
        "description": (
            "Requirements should be complete and safe; testing may be "
            "partial but should select the real boundary."
        ),
    },
    "high": {
        "require_complete_requirements": True,
        "maximum_expansion": "low",
        "require_complete_testing": True,
        "require_real_crossing": True,
        "description": (
            "Complete, focused requirements and decisive verification are "
            "expected."
        ),
    },
    "xhigh": {
        "require_complete_requirements": True,
        "maximum_expansion": "low",
        "require_complete_testing": True,
        "require_real_crossing": True,
        "description": (
            "Complete, focused requirements and decisive verification are "
            "expected."
        ),
    },
    "max": {
        "require_complete_requirements": True,
        "maximum_expansion": "low",
        "require_complete_testing": True,
        "require_real_crossing": True,
        "description": (
            "Complete, focused requirements and decisive verification are "
            "expected."
        ),
    },
}

_EXPANSION_RANK = {"none": 0, "low": 1, "medium": 2, "high": 3}
_COVERAGE_SCORE = {"complete": 100, "partial": 60, "missing": 0}
_SCOPE_SCORE = {"none": 100, "low": 85, "medium": 55, "high": 10}
_TESTING_COVERAGE_SCORE = {"complete": 40, "partial": 20, "missing": 0}
_TESTING_LAYER_SCORE = {"appropriate": 25, "mixed": 12, "poor": 0}
_TESTING_CROSSING_SCORE = {"present": 20, "not_required": 20, "missing": 0}
_TESTING_FOCUS_SCORE = {"focused": 10, "mixed": 4, "bloated": 0}
_TESTING_DEGREE_SCORE = {"none": 3, "minor": 1, "material": 0}


def score_semantic_assessment(
    assessment: dict[str, Any],
    *,
    effort: str,
) -> dict[str, Any]:
    if effort not in EFFORT_POLICIES:
        raise ValueError(f"unknown effort policy: {effort}")
    requirement = assessment["requirement_assessment"]
    testing = assessment["testing_plan_assessment"]
    if not isinstance(testing, dict):
        raise ValueError("root-guidance scoring requires a testing assessment")
    policy = EFFORT_POLICIES[effort]

    material_additions = sum(
        item.get("severity") == "material"
        for item in requirement["added_obligations"]
    )
    minor_additions = sum(
        item.get("severity") == "minor"
        for item in requirement["added_obligations"]
    )
    material_grouping = sum(
        item.get("severity") == "material"
        for item in requirement["grouping"]
        if item.get("kind") != "valid_decomposition"
    )
    minor_grouping = sum(
        item.get("severity") == "minor"
        for item in requirement["grouping"]
        if item.get("kind") != "valid_decomposition"
    )

    coverage_score = _COVERAGE_SCORE[requirement["coverage_status"]]
    scope_score = max(
        0,
        _SCOPE_SCORE[requirement["expansion_severity"]]
        - 35 * material_additions
        - 25 * material_grouping
        - 5 * minor_additions
        - 3 * minor_grouping,
    )
    testing_score = min(
        100,
        (
            _TESTING_COVERAGE_SCORE[testing["overall_coverage"]]
            + _TESTING_LAYER_SCORE[testing["layer_selection"]]
            + _TESTING_CROSSING_SCORE[testing["important_crossing"]]
            + _TESTING_FOCUS_SCORE[testing["verification_focus"]]
            + _TESTING_DEGREE_SCORE[testing["duplication"]]
            + _TESTING_DEGREE_SCORE[testing["combinatorial_expansion"]]
        ),
    )

    requirements_complete = requirement["coverage_status"] == "complete"
    expansion_within_policy = (
        _EXPANSION_RANK[requirement["expansion_severity"]]
        <= _EXPANSION_RANK[str(policy["maximum_expansion"])]
    )
    scope_safe = (
        expansion_within_policy
        and material_additions == 0
        and material_grouping == 0
    )
    requirement_expectation_met = scope_safe and (
        requirements_complete
        or not bool(policy["require_complete_requirements"])
    )

    crossing_present = testing["important_crossing"] in {
        "present",
        "not_required",
    }
    if bool(policy["require_complete_testing"]):
        testing_expectation_met = (
            testing["overall_coverage"] == "complete"
            and testing["layer_selection"] == "appropriate"
            and crossing_present
            and testing["verification_focus"] == "focused"
            and testing["duplication"] != "material"
            and testing["combinatorial_expansion"] != "material"
        )
    else:
        testing_expectation_met = (
            testing["overall_coverage"] != "missing"
            and testing["layer_selection"] != "poor"
            and testing["verification_focus"] != "bloated"
            and (
                crossing_present
                or not bool(policy["require_real_crossing"])
            )
            and testing["duplication"] != "material"
            and testing["combinatorial_expansion"] != "material"
        )

    return {
        "effort": effort,
        "effort_tier": (
            "high_assurance"
            if effort in HIGH_ASSURANCE_EFFORTS
            else "exploratory" if effort == "low" else "standard"
        ),
        "coverage_score": coverage_score,
        "scope_score": scope_score,
        "testing_score": testing_score,
        "requirement_expectation_met": requirement_expectation_met,
        "testing_expectation_met": testing_expectation_met,
        "effort_expectation_met": (
            requirement_expectation_met and testing_expectation_met
        ),
        "material_added_obligations": material_additions,
        "material_grouping_issues": material_grouping,
    }


def aggregate_scored_cells(
    cells: Iterable[dict[str, Any]],
) -> dict[str, Any]:
    values = list(cells)
    if not values:
        raise ValueError("cannot aggregate an empty score set")

    def average(key: str) -> float:
        return round(
            sum(float(item["scores"][key]) for item in values) / len(values),
            1,
        )

    return {
        "cells": len(values),
        "average_coverage_score": average("coverage_score"),
        "average_scope_score": average("scope_score"),
        "average_testing_score": average("testing_score"),
        "requirement_expectation_met": sum(
            bool(item["scores"]["requirement_expectation_met"])
            for item in values
        ),
        "testing_expectation_met": sum(
            bool(item["scores"]["testing_expectation_met"])
            for item in values
        ),
        "effort_expectation_met": sum(
            bool(item["scores"]["effort_expectation_met"])
            for item in values
        ),
        "coverage_statuses": dict(
            Counter(
                item["assessment"]["requirement_assessment"][
                    "coverage_status"
                ]
                for item in values
            )
        ),
        "expansion_severities": dict(
            Counter(
                item["assessment"]["requirement_assessment"][
                    "expansion_severity"
                ]
                for item in values
            )
        ),
        "testing_coverage": dict(
            Counter(
                item["assessment"]["testing_plan_assessment"][
                    "overall_coverage"
                ]
                for item in values
            )
        ),
        "testing_layers": dict(
            Counter(
                item["assessment"]["testing_plan_assessment"][
                    "layer_selection"
                ]
                for item in values
            )
        ),
        "important_crossings": dict(
            Counter(
                item["assessment"]["testing_plan_assessment"][
                    "important_crossing"
                ]
                for item in values
            )
        ),
    }