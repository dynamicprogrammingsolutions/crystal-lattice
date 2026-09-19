from __future__ import annotations

import os
from collections.abc import Iterator

import pytest

from .requirement_quality import (
    PRODUCER_CASES,
    SCENARIOS,
    RequirementQualityScenario,
    load_target,
)
from .requirement_quality_evaluator import (
    EVALUATOR_PROMPT_VERSION,
    build_evaluator_prompt,
    calibration_findings,
    dataset_records_for_scenario,
    dataset_sha256,
    load_accepted_anchors,
    load_accepted_dataset,
    load_candidate_task_dataset,
    load_candidate_v2_task_dataset,
    load_candidate_v3_task_dataset,
    load_compiled_guidance_dataset,
    load_root_guidance_dataset,
    load_task_dataset,
    parse_evaluator_response_with_repairs,
    task_quality_findings,
    validate_evaluator_result,
)
from .support import (
    AssertionFinding,
    DocumentationEvaluationHarness,
    PROFILES,
    RUNNER_DEFAULT_SYSTEM_MESSAGE,
    assert_findings,
    basic_run_findings,
    enforce_real_model_gate,
    require_run_value,
)


pytestmark = [pytest.mark.agent_eval, pytest.mark.requirement_semantic]


def _selected_dataset(
    scenario: RequirementQualityScenario,
) -> tuple[dict, bool]:
    name = os.getenv(
        "AGENT_EVAL_SEMANTIC_DATASET",
        "accepted",
    ).strip()
    if name == "accepted":
        return load_accepted_dataset(), False
    if name == "task-current":
        return load_task_dataset(), True
    if name == "task-candidate":
        return load_candidate_task_dataset(), True
    if name == "task-candidate-v2":
        return load_candidate_v2_task_dataset(), True
    if name == "task-candidate-v3":
        requested = tuple(
            item.strip()
            for item in os.getenv(
                "AGENT_EVAL_SEMANTIC_CANDIDATES",
                "",
            ).split(",")
            if item.strip()
        )
        valid_ids = {
            f"{profile}-{effort}": (profile, effort)
            for profile, effort in PRODUCER_CASES
        }
        unknown = set(requested).difference(valid_ids)
        if unknown:
            raise ValueError(
                "unknown AGENT_EVAL_SEMANTIC_CANDIDATES: "
                f"{sorted(unknown)!r}"
            )
        producer_cases = tuple(
            valid_ids[candidate_id] for candidate_id in requested
        ) or PRODUCER_CASES
        return (
            load_candidate_v3_task_dataset(
                scenario_ids=(scenario.scenario_id,),
                producer_cases=producer_cases,
            ),
            True,
        )
    if name == "root-guidance":
        variant = os.getenv(
            "AGENT_EVAL_ROOT_GUIDANCE_VARIANT",
            "baseline",
        ).strip()
        mode = os.getenv(
            "AGENT_EVAL_ROOT_GUIDANCE_MODE",
            "root-only",
        ).strip()
        requested = tuple(
            item.strip()
            for item in os.getenv(
                "AGENT_EVAL_ROOT_GUIDANCE_CANDIDATES",
                "",
            ).split(",")
            if item.strip()
        )
        valid_ids = {
            f"{profile}-{effort}": (profile, effort)
            for profile, effort in PRODUCER_CASES
        }
        unknown = set(requested).difference(valid_ids)
        if unknown:
            raise ValueError(
                "unknown AGENT_EVAL_ROOT_GUIDANCE_CANDIDATES: "
                f"{sorted(unknown)!r}"
            )
        producer_cases = tuple(
            valid_ids[candidate_id] for candidate_id in requested
        ) or PRODUCER_CASES
        return (
            load_root_guidance_dataset(
                variant=variant,
                mode=mode,
                scenario_ids=(scenario.scenario_id,),
                producer_cases=producer_cases,
            ),
            True,
        )
    if name == "compiled-guidance":
        mode = os.getenv(
            "AGENT_EVAL_ROOT_GUIDANCE_MODE",
            "root-only",
        ).strip()
        requested = tuple(
            item.strip()
            for item in os.getenv(
                "AGENT_EVAL_ROOT_GUIDANCE_CANDIDATES",
                "",
            ).split(",")
            if item.strip()
        )
        valid_ids = {
            f"{profile}-{effort}": (profile, effort)
            for profile, effort in PRODUCER_CASES
        }
        unknown = set(requested).difference(valid_ids)
        if unknown:
            raise ValueError(
                "unknown AGENT_EVAL_ROOT_GUIDANCE_CANDIDATES: "
                f"{sorted(unknown)!r}"
            )
        producer_cases = tuple(
            valid_ids[candidate_id] for candidate_id in requested
        ) or PRODUCER_CASES
        return (
            load_compiled_guidance_dataset(
                mode=mode,
                scenario_ids=(scenario.scenario_id,),
                producer_cases=producer_cases,
                repeat_variant=os.getenv(
                    "AGENT_EVAL_ROOT_GUIDANCE_PRODUCER_VARIANT",
                    "",
                ).strip()
                or None,
                require_valid_producers=True,
            ),
            True,
        )
    raise ValueError(
        "AGENT_EVAL_SEMANTIC_DATASET must be accepted, task-current, "
        "task-candidate, task-candidate-v2, task-candidate-v3, or "
        "root-guidance, or compiled-guidance"
    )


@pytest.fixture(scope="session")
def semantic_evaluator_harness() -> Iterator[DocumentationEvaluationHarness]:
    profile = PROFILES["glm"]
    enforce_real_model_gate(profile)
    harness = DocumentationEvaluationHarness(
        profile,
        runner_mode=RUNNER_DEFAULT_SYSTEM_MESSAGE,
    )
    yield harness
    harness.close()


@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda value: value.scenario_id)
@pytest.mark.requirements(
    "DOCGUIDE-005",
    "DOCGUIDE-006",
    "DOCVAL-010",
    "DOCVAL-011",
    "DOCVAL-012",
)
def test_requirement_quality_semantic_evaluator(
    semantic_evaluator_harness: DocumentationEvaluationHarness,
    scenario: RequirementQualityScenario,
) -> None:
    dataset, assess_testing = _selected_dataset(scenario)
    candidates = dataset_records_for_scenario(dataset, scenario)
    target = load_target(scenario)
    prompt = build_evaluator_prompt(
        dataset_id=dataset["dataset_id"],
        scenario=scenario,
        target=target,
        candidates=candidates,
        assess_testing=assess_testing,
    )
    dataset_hash = dataset_sha256(
        {
            **dataset,
            "records": candidates,
        }
    )
    repeat_variant = os.getenv(
        "AGENT_EVAL_SEMANTIC_CACHE_VARIANT",
        "",
    ).strip()
    run = semantic_evaluator_harness.fresh_prompt(
        test_id=(
            f"requirement-semantic-{dataset['dataset_id']}-"
            f"{scenario.scenario_id}"
        ),
        prompt=prompt,
        reasoning_effort="max",
        cache_variant=(
            f"{EVALUATOR_PROMPT_VERSION}-{dataset_hash[:16]}:"
            f"{repeat_variant or 'default'}"
        ),
    )
    value = require_run_value(run)
    try:
        result, response_repairs = parse_evaluator_response_with_repairs(
            value.response
        )
        validate_evaluator_result(
            result,
            dataset_id=dataset["dataset_id"],
            scenario=scenario,
            target=target,
            candidate_ids=[
                candidate["candidate_id"] for candidate in candidates
            ],
            assess_testing=assess_testing,
        )
    except Exception as error:
        run.record(
            "semantic-evaluation-error.json",
            {
                "dataset_id": dataset["dataset_id"],
                "scenario_id": scenario.scenario_id,
                "error_type": type(error).__name__,
                "error": str(error),
                "response": value.response,
                "repeat_variant": repeat_variant or "default",
            },
        )
        raise

    findings = basic_run_findings(run) + (
        AssertionFinding(
            "semantic evaluator did not mutate its workspace",
            not run.changed_paths,
            repr(run.changed_paths),
        ),
    )
    if assess_testing:
        findings += task_quality_findings(result)
    else:
        findings += calibration_findings(
            result,
            anchors=load_accepted_anchors(),
            scenario=scenario,
        )
    run.record(
        "semantic-evaluation.json",
        {
            "schema_version": 1,
            "dataset_id": dataset["dataset_id"],
            "dataset_sha256": dataset_hash,
            "evaluator": {
                "profile": semantic_evaluator_harness.profile.name,
                "agent_id": semantic_evaluator_harness.profile.agent_id,
                "model": semantic_evaluator_harness.profile.model,
                "reasoning_effort": "max",
                "prompt_version": EVALUATOR_PROMPT_VERSION,
            },
            "scenario_id": scenario.scenario_id,
            "candidate_sources": [
                {
                    "candidate_id": candidate["candidate_id"],
                    "source_run_id": candidate["source_run_id"],
                    "source_record_sha256": candidate["source_record_sha256"],
                }
                for candidate in candidates
            ],
            "result": result,
            "response_repairs": list(response_repairs),
            "repeat_variant": repeat_variant or "default",
            "findings": [finding.__dict__ for finding in findings],
        },
    )
    run.record("assertions.json", [finding.__dict__ for finding in findings])
    assert_findings(findings)