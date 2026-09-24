from __future__ import annotations

import json
from pathlib import Path

import pytest

from suites.documentation_standard.destination_terminology_evaluator import (
    anchor_findings,
    build_evaluator_prompt,
    dataset_sha256,
    load_anchor_dataset,
    load_producer_dataset,
    load_target,
    parse_evaluator_response,
    producer_findings,
    validate_dataset,
    validate_evaluator_result,
)


def _assessment(
    candidate_id: str,
    dimension_ids: list[str],
    *,
    overall: str = "pass",
    statuses: dict[str, str] | None = None,
) -> dict:
    values = statuses or {}
    return {
        "candidate_id": candidate_id,
        "dimensions": [
            {
                "dimension_id": dimension_id,
                "status": values.get(dimension_id, "pass"),
                "evidence": f"evidence for {dimension_id}",
                "notes": f"notes for {dimension_id}",
            }
            for dimension_id in dimension_ids
        ],
        "overall_status": overall,
        "summary": f"summary for {candidate_id}",
    }


def _result_for_dataset(dataset: dict, target: dict) -> dict:
    dimension_ids = [item["id"] for item in target["dimensions"]]
    assessments = []
    for candidate in dataset["candidates"]:
        statuses = {
            dimension_id: "fail"
            for dimension_id in candidate.get("required_not_pass", [])
        }
        assessments.append(
            _assessment(
                candidate["candidate_id"],
                dimension_ids,
                overall=candidate.get("expected_overall", "pass"),
                statuses=statuses,
            )
        )
    return {
        "schema_version": 1,
        "dataset_id": dataset["dataset_id"],
        "scenario_id": target["scenario_id"],
        "assessments": assessments,
    }


def test_destination_terminology_target_and_anchors_are_valid() -> None:
    target = load_target()
    dataset = load_anchor_dataset()

    assert len(target["dimensions"]) == 7
    assert len(dataset["candidates"]) == 5
    assert len(dataset_sha256(dataset)) == 64
    assert dataset["scenario_id"] == target["scenario_id"]


def test_destination_terminology_prompt_contains_complete_schema() -> None:
    target = load_target()
    dataset = load_anchor_dataset()
    prompt = build_evaluator_prompt(dataset=dataset, target=target)

    for candidate in dataset["candidates"]:
        assert candidate["candidate_id"] in prompt
        encoded_response = json.dumps(candidate["response"])[1:-1]
        assert encoded_response in prompt
    for dimension in target["dimensions"]:
        assert dimension["id"] in prompt
    assert "Return JSON only" in prompt
    assert "Let me know" in prompt
    assert "no explicit, directly answerable confirmation question" in prompt


def test_destination_terminology_result_validation_and_anchor_findings() -> None:
    target = load_target()
    dataset = load_anchor_dataset()
    result = _result_for_dataset(dataset, target)

    validate_evaluator_result(
        result,
        dataset=dataset,
        target=target,
    )
    findings = anchor_findings(result, dataset=dataset)

    assert findings
    assert all(finding.passed for finding in findings)


def test_destination_terminology_result_rejects_missing_dimension() -> None:
    target = load_target()
    dataset = load_anchor_dataset()
    result = _result_for_dataset(dataset, target)
    result["assessments"][0]["dimensions"].pop()

    with pytest.raises(ValueError, match="dimensions do not match"):
        validate_evaluator_result(
            result,
            dataset=dataset,
            target=target,
        )


def test_destination_terminology_parser_records_trailing_comma_repair() -> None:
    text = """```json
{
  "schema_version": 1,
  "dataset_id": "dataset",
  "scenario_id": "scenario",
  "assessments": [],
}
```"""

    value, repairs = parse_evaluator_response(text)

    assert value["dataset_id"] == "dataset"
    assert repairs
    assert "trailing comma" in repairs[0]


def test_destination_terminology_producer_findings_allow_partial_outcome() -> None:
    target = load_target()
    dataset = {
        "schema_version": 1,
        "dataset_id": "producer",
        "scenario_id": target["scenario_id"],
        "candidates": [
            {
                "candidate_id": "abstract-glm-high",
                "response": "response",
            }
        ],
    }
    result = _result_for_dataset(dataset, target)
    result["assessments"][0]["dimensions"][0]["status"] = "partial"

    validate_dataset(dataset)
    validate_evaluator_result(result, dataset=dataset, target=target)
    findings = producer_findings(result)

    assert len(findings) == 2
    assert findings[0].passed
    assert findings[1].passed


def test_destination_terminology_producer_loader_uses_valid_records_only(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    valid = (
        tmp_path
        / "glm"
        / "runs"
        / "20260919T000000Z-38-confirm-existing-terminology-cleanup-valid"
        / "records"
    )
    invalid = (
        tmp_path
        / "gpt"
        / "runs"
        / "20260919T000001Z-38-confirm-existing-terminology-cleanup-invalid"
        / "records"
    )
    valid.mkdir(parents=True)
    invalid.mkdir(parents=True)
    base = {
        "schema_version": 1,
        "scenario_id": "38-confirm-existing-terminology-cleanup",
        "producer": {
            "name": "glm",
            "reasoning_effort": "high",
        },
        "guidance": {
            "provenance": {
                "variant": "abstract-specific",
            }
        },
        "response": "May I remove the existing internal heading?",
        "changed_paths": [],
        "ordering": {
            "status": "ideal",
            "ideal": True,
            "minor_deviation": False,
            "existing_label_preserved": True,
        },
    }
    valid.joinpath("destination-terminology-producer.json").write_text(
        json.dumps(
            {
                **base,
                "findings": [{"name": "valid", "passed": True}],
            }
        ),
        encoding="utf-8",
    )
    invalid.joinpath("destination-terminology-producer.json").write_text(
        json.dumps(
            {
                **base,
                "producer": {
                    "name": "gpt",
                    "reasoning_effort": "high",
                },
                "findings": [{"name": "invalid", "passed": False}],
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv(
        "AGENT_EVAL_DESTINATION_TERMINOLOGY_SEMANTIC_CANDIDATES",
        "abstract-specific-glm-high",
    )

    dataset = load_producer_dataset(tmp_path)

    assert [candidate["candidate_id"] for candidate in dataset["candidates"]] == [
        "abstract-specific-glm-high"
    ]
    assert dataset["candidates"][0]["source_record_sha256"]
