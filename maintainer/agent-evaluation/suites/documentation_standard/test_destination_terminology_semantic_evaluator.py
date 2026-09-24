from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

from .destination_terminology_evaluator import (
    EVALUATOR_PROMPT_VERSION,
    anchor_findings,
    build_evaluator_prompt,
    dataset_sha256,
    load_anchor_dataset,
    load_producer_dataset,
    load_target,
    parse_evaluator_response,
    producer_findings,
    validate_evaluator_result,
)
from .support import (
    RUNNER_DEFAULT_SYSTEM_MESSAGE,
    AssertionFinding,
    DocumentationEvaluationHarness,
    PROFILES,
    assert_findings,
    basic_run_findings,
    enforce_real_model_gate,
    require_run_value,
)


pytestmark = [
    pytest.mark.agent_eval,
    pytest.mark.destination_terminology,
    pytest.mark.destination_terminology_semantic,
]


@pytest.fixture(scope="session")
def semantic_harness() -> Iterator[DocumentationEvaluationHarness]:
    profile = PROFILES["glm"]
    enforce_real_model_gate(profile)
    harness = DocumentationEvaluationHarness(
        profile,
        runner_mode=RUNNER_DEFAULT_SYSTEM_MESSAGE,
    )
    yield harness
    harness.close()


def _selected_dataset() -> tuple[dict, bool]:
    name = os.getenv(
        "AGENT_EVAL_DESTINATION_TERMINOLOGY_SEMANTIC_DATASET",
        "anchors",
    ).strip()
    if name == "anchors":
        return load_anchor_dataset(), True
    if name == "producers":
        return load_producer_dataset(), False
    raise ValueError(
        "AGENT_EVAL_DESTINATION_TERMINOLOGY_SEMANTIC_DATASET must be "
        "anchors or producers"
    )


@pytest.mark.requirements("DOCGUIDE-009", "DOCVAL-015", "DSEVAL-004")
def test_destination_terminology_semantic_evaluator(
    semantic_harness: DocumentationEvaluationHarness,
) -> None:
    """Assess confirmation-before-cleanup responses after producer validity.

    Anchor mode calibrates five distinct response patterns. Producer mode loads
    only repeat-pinned Test 38 records whose deterministic findings all passed.
    The judge must return every candidate and semantic dimension in the
    versioned JSON schema. Schema validity, parser repairs, workspace
    immutability, and model provenance are asserted separately from the
    semantic verdicts.
    """

    dataset, anchors = _selected_dataset()
    target = load_target()
    prompt = build_evaluator_prompt(dataset=dataset, target=target)
    dataset_hash = dataset_sha256(dataset)
    repeat_variant = os.getenv(
        "AGENT_EVAL_DESTINATION_TERMINOLOGY_SEMANTIC_CACHE_VARIANT",
        "",
    ).strip()
    run = semantic_harness.fresh_prompt(
        test_id=("destination-terminology-semantic-" f"{dataset['dataset_id']}"),
        prompt=prompt,
        reasoning_effort="max",
        cache_variant=(
            f"{EVALUATOR_PROMPT_VERSION}-{dataset_hash[:16]}:"
            f"{repeat_variant or 'default'}"
        ),
    )
    value = require_run_value(run)
    try:
        result, repairs = parse_evaluator_response(value.response)
        validate_evaluator_result(
            result,
            dataset=dataset,
            target=target,
        )
    except Exception as error:
        run.record(
            "destination-terminology-semantic-error.json",
            {
                "dataset_id": dataset["dataset_id"],
                "error_type": type(error).__name__,
                "error": str(error),
                "response": value.response,
                "repeat_variant": repeat_variant or "default",
            },
        )
        raise

    findings = (
        basic_run_findings(run)
        + (
            AssertionFinding(
                "semantic evaluator does not mutate its workspace",
                not run.changed_paths,
                repr(run.changed_paths),
            ),
        )
        + (
            anchor_findings(result, dataset=dataset)
            if anchors
            else producer_findings(result)
        )
    )
    run.record(
        "destination-terminology-semantic.json",
        {
            "schema_version": 1,
            "dataset_id": dataset["dataset_id"],
            "dataset_sha256": dataset_hash,
            "evaluator": {
                "profile": semantic_harness.profile.name,
                "agent_id": semantic_harness.profile.agent_id,
                "model": semantic_harness.profile.model,
                "reasoning_effort": "max",
                "prompt_version": EVALUATOR_PROMPT_VERSION,
            },
            "candidate_sources": [
                {
                    "candidate_id": item["candidate_id"],
                    "source_run_id": item.get("source_run_id"),
                    "source_record_sha256": item.get("source_record_sha256"),
                }
                for item in dataset["candidates"]
            ],
            "result": result,
            "response_repairs": list(repairs),
            "repeat_variant": repeat_variant or "default",
            "findings": [finding.__dict__ for finding in findings],
        },
    )
    run.record(
        "assertions.json",
        [finding.__dict__ for finding in findings],
    )
    assert_findings(findings)
