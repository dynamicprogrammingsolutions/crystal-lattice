from __future__ import annotations

import hashlib
import json
import os
from collections.abc import Iterator

import pytest

from .requirement_quality import (
    PRODUCER_CASES,
    ROOT_GUIDANCE_MODES,
    SCENARIOS,
    RequirementQualityScenario,
    load_target,
)
from .requirement_quality_evaluator import (
    DEFAULT_ARTIFACT_ROOT,
    load_root_guidance_dataset,
    parse_evaluator_response_with_repairs,
)
from .root_guidance_quality import (
    QUALITY_PROMPT_VERSION,
    build_quality_prompt,
    mapped_quality_result,
    quality_label_mapping,
    semantic_record_paths,
    validate_quality_result,
)
from .support import (
    AssertionFinding,
    DocumentationEvaluationHarness,
    PROFILES,
    assert_findings,
    basic_run_findings,
    enforce_real_model_gate,
    require_run_value,
)


pytestmark = [pytest.mark.agent_eval, pytest.mark.root_guidance_quality]
RECORD_NAME = "root-guidance-pairwise-quality.json"
FULL_MATRIX_REPEAT_VARIANT = "full-matrix-r1"


@pytest.fixture(scope="session")
def quality_evaluator_harness() -> Iterator[DocumentationEvaluationHarness]:
    profile = PROFILES["glm"]
    enforce_real_model_gate(profile)
    harness = DocumentationEvaluationHarness(profile)
    yield harness
    harness.close()


def _selected_modes() -> tuple[str, ...]:
    value = os.getenv("AGENT_EVAL_ROOT_GUIDANCE_QUALITY_MODES", "").strip()
    modes = tuple(item.strip() for item in value.split(",") if item.strip())
    unknown = set(modes).difference(ROOT_GUIDANCE_MODES)
    if unknown:
        raise ValueError(f"unknown root-guidance quality modes: {unknown!r}")
    return modes or tuple(sorted(ROOT_GUIDANCE_MODES))


def _selected_candidate_ids() -> set[str]:
    values = {
        item.strip()
        for item in os.getenv(
            "AGENT_EVAL_ROOT_GUIDANCE_CANDIDATES",
            "",
        ).split(",")
        if item.strip()
    }
    valid = {f"{profile}-{effort}" for profile, effort in PRODUCER_CASES}
    unknown = values.difference(valid)
    if unknown:
        raise ValueError(f"unknown root-guidance quality candidates: {unknown!r}")
    return values


def _producer_record(
    *,
    variant: str,
    mode: str,
    scenario: RequirementQualityScenario,
    producer_case: tuple[str, str],
) -> dict:
    dataset = load_root_guidance_dataset(
        variant=variant,
        mode=mode,
        scenario_ids=(scenario.scenario_id,),
        producer_cases=(producer_case,),
    )
    return dataset["records"][0]


def _semantic_record(
    *,
    variant: str,
    mode: str,
    scenario: RequirementQualityScenario,
    candidate_id: str,
) -> tuple[dict, dict]:
    paths = semantic_record_paths(
        DEFAULT_ARTIFACT_ROOT,
        variant=variant,
        mode=mode,
        scenario_id=scenario.scenario_id,
        repeat_variant=FULL_MATRIX_REPEAT_VARIANT,
    )
    for path in reversed(paths):
        value = json.loads(path.read_text(encoding="utf-8"))
        for assessment in value["result"]["assessments"]:
            if assessment["candidate_id"] == candidate_id:
                return value, {
                    **assessment,
                    "source_run_id": path.parents[1].name,
                    "source_record_sha256": hashlib.sha256(
                        path.read_bytes()
                    ).hexdigest(),
                }
    raise FileNotFoundError(
        "missing full-matrix semantic assessment for "
        f"{variant}/{mode}/{scenario.scenario_id}/{candidate_id}"
    )


@pytest.mark.parametrize("mode", sorted(ROOT_GUIDANCE_MODES))
@pytest.mark.parametrize(
    ("producer_profile", "reasoning_effort"),
    PRODUCER_CASES,
    ids=lambda value: value,
)
@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda value: value.scenario_id)
@pytest.mark.requirements("DOCVAL-013")
def test_root_guidance_pairwise_quality(
    quality_evaluator_harness: DocumentationEvaluationHarness,
    scenario: RequirementQualityScenario,
    producer_profile: str,
    reasoning_effort: str,
    mode: str,
) -> None:
    if mode not in _selected_modes():
        pytest.skip(f"{mode} is not in the selected quality modes")
    candidate_id = f"{producer_profile}-{reasoning_effort}"
    selected_ids = _selected_candidate_ids()
    if selected_ids and candidate_id not in selected_ids:
        pytest.skip(f"{candidate_id} is not in the selected quality candidates")

    producer_case = (producer_profile, reasoning_effort)
    outputs = {
        variant: _producer_record(
            variant=variant,
            mode=mode,
            scenario=scenario,
            producer_case=producer_case,
        )
        for variant in ("baseline", "combined-v2")
    }
    semantic_records = {}
    semantic_assessments = {}
    for variant in ("baseline", "combined-v2"):
        semantic_record, assessment = _semantic_record(
            variant=variant,
            mode=mode,
            scenario=scenario,
            candidate_id=candidate_id,
        )
        semantic_records[variant] = semantic_record
        semantic_assessments[variant] = assessment

    label_mapping = quality_label_mapping(
        scenario_id=scenario.scenario_id,
        mode=mode,
        candidate_id=candidate_id,
    )
    prompt = build_quality_prompt(
        scenario=scenario,
        target=load_target(scenario),
        mode=mode,
        candidate_id=candidate_id,
        outputs=outputs,
        semantic_assessments=semantic_assessments,
        label_mapping=label_mapping,
    )
    prompt_hash = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    repeat_variant = os.getenv(
        "AGENT_EVAL_ROOT_GUIDANCE_QUALITY_CACHE_VARIANT",
        "",
    ).strip()
    run = quality_evaluator_harness.fresh_prompt(
        test_id=(
            f"root-guidance-quality-{scenario.scenario_id}-"
            f"{mode}-{candidate_id}"
        ),
        prompt=prompt,
        reasoning_effort="max",
        cache_variant=(
            f"{QUALITY_PROMPT_VERSION}-{prompt_hash[:16]}:"
            f"{repeat_variant or 'default'}"
        ),
    )
    value = require_run_value(run)
    try:
        result, response_repairs = parse_evaluator_response_with_repairs(
            value.response
        )
        validate_quality_result(
            result,
            scenario_id=scenario.scenario_id,
            candidate_id=candidate_id,
        )
    except Exception as error:
        run.record(
            "root-guidance-pairwise-quality-error.json",
            {
                "scenario_id": scenario.scenario_id,
                "mode": mode,
                "candidate_id": candidate_id,
                "label_mapping": label_mapping,
                "error_type": type(error).__name__,
                "error": str(error),
                "response": value.response,
                "repeat_variant": repeat_variant or "default",
            },
        )
        raise

    findings = basic_run_findings(run) + (
        AssertionFinding(
            "pairwise quality evaluator did not mutate its workspace",
            not run.changed_paths,
            repr(run.changed_paths),
        ),
    )
    run.record(
        RECORD_NAME,
        {
            "schema_version": 1,
            "scenario_id": scenario.scenario_id,
            "mode": mode,
            "candidate_id": candidate_id,
            "evaluator": {
                "profile": quality_evaluator_harness.profile.name,
                "agent_id": quality_evaluator_harness.profile.agent_id,
                "model": quality_evaluator_harness.profile.model,
                "reasoning_effort": "max",
                "prompt_version": QUALITY_PROMPT_VERSION,
            },
            "label_mapping": label_mapping,
            "producer_sources": {
                variant: {
                    "source_run_id": record["source_run_id"],
                    "source_record_sha256": record["source_record_sha256"],
                }
                for variant, record in outputs.items()
            },
            "semantic_sources": {
                variant: {
                    "source_run_id": semantic_assessments[variant][
                        "source_run_id"
                    ],
                    "source_record_sha256": semantic_assessments[variant][
                        "source_record_sha256"
                    ],
                }
                for variant in ("baseline", "combined-v2")
            },
            "result": mapped_quality_result(
                result,
                label_mapping=label_mapping,
            ),
            "raw_result": result,
            "response_repairs": list(response_repairs),
            "repeat_variant": repeat_variant or "default",
            "findings": [finding.__dict__ for finding in findings],
        },
    )
    run.record("assertions.json", [finding.__dict__ for finding in findings])
    assert_findings(findings)