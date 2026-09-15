from __future__ import annotations

import re
from collections.abc import Iterator
from pathlib import Path

import pytest

from .requirement_quality import (
    PRODUCER_CASES,
    SCENARIOS,
    RequirementQualityScenario,
    load_target,
    requirement_minimal_guidance_source,
    scenario_prompt,
    target_sha256,
)
from .support import (
    AssertionFinding,
    DocumentationEvaluationHarness,
    assert_findings,
    basic_run_findings,
    enforce_real_model_gate,
    matching_paths,
    require_run_value,
    selected_profile,
)
from .test_consumers import _evidence_value


pytestmark = [pytest.mark.agent_eval, pytest.mark.requirement_baseline]

@pytest.fixture(scope="session")
def requirement_baseline_harness() -> Iterator[DocumentationEvaluationHarness]:
    profile = selected_profile()
    enforce_real_model_gate(profile)
    harness = DocumentationEvaluationHarness(
        profile,
        guidance=requirement_minimal_guidance_source(),
    )
    yield harness
    harness.close()


def _changed_documentation(run) -> dict[str, str]:
    if run.workspace is None:
        return {}
    values: dict[str, str] = {}
    for relative in matching_paths(run, "docs/development"):
        if relative not in run.changed_paths:
            continue
        path = run.workspace / relative
        values[relative] = path.read_text(encoding="utf-8", errors="replace")
    return values


def _has_specification_and_requirements(files: dict[str, str]) -> bool:
    rendered = "\n".join(files.values()).lower()
    paths = tuple(path.lower() for path in files)
    has_specification = (
        any("spec" in Path(path).name for path in paths)
        or "specification" in rendered
        or "# target" in rendered
    )
    has_requirements = (
        any("requirement" in Path(path).name for path in paths)
        or re.search(r"\n#{1,4}\s+[^\n]*requirements\b", rendered) is not None
    )
    return has_specification and has_requirements


@pytest.mark.parametrize(
    ("producer_profile", "reasoning_effort"),
    PRODUCER_CASES,
    ids=lambda value: value,
)
@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda value: value.scenario_id)
@pytest.mark.requirements("DOCGUIDE-005", "DOCVAL-010", "DOCVAL-011")
def test_requirement_quality_baseline(
    requirement_baseline_harness: DocumentationEvaluationHarness,
    scenario: RequirementQualityScenario,
    producer_profile: str,
    reasoning_effort: str,
) -> None:
    profile = requirement_baseline_harness.profile
    if profile.name != producer_profile:
        pytest.skip(f"run with AGENT_EVAL_PROFILE={producer_profile}")

    target = load_target(scenario)
    target_hash = target_sha256(scenario)
    run = requirement_baseline_harness.fresh_scenario(
        test_id=f"requirement-baseline-{scenario.scenario_id}-{reasoning_effort}",
        spec_file=scenario.spec_file,
        fixture_id=scenario.fixture_id,
        reasoning_effort=reasoning_effort,
        cache_variant=f"baseline-v1-{target_hash[:16]}",
    )
    value = require_run_value(run)
    files = _changed_documentation(run)
    profile_evidence = _evidence_value(run, "documentation_standard.profile")
    recorded_profile = profile_evidence if isinstance(profile_evidence, dict) else {}
    findings = basic_run_findings(run) + (
        AssertionFinding(
            "specification and requirements produced",
            _has_specification_and_requirements(files),
            repr(tuple(files)),
        ),
        AssertionFinding(
            "mutation remains specification-only",
            bool(run.changed_paths)
            and all(
                path.startswith(scenario.package_prefix)
                for path in run.changed_paths
            ),
            repr(run.changed_paths),
        ),
        AssertionFinding(
            "producer model recorded",
            recorded_profile.get("model") == profile.model,
            repr(recorded_profile),
        ),
        AssertionFinding(
            "producer effort recorded",
            recorded_profile.get("reasoning_effort") == reasoning_effort,
            repr(recorded_profile),
        ),
        AssertionFinding(
            "GPT producer uses configured ChatGPT login",
            profile.name != "gpt" or profile.auth_mode == "chatgpt",
            f"profile={profile.name!r}, configured_auth_mode={profile.auth_mode!r}",
        ),
    )
    run.record("assertions.json", [finding.__dict__ for finding in findings])
    run.record(
        "requirement-baseline.json",
        {
            "scenario_id": scenario.scenario_id,
            "project": {
                "name": scenario.project_name,
                "kind": scenario.project_kind,
                "upstream": scenario.upstream,
                "revision": scenario.upstream_revision,
            },
            "target": target,
            "target_sha256": target_hash,
            "prompt": scenario_prompt(scenario),
            "producer": {
                "profile": profile.name,
                "agent_id": profile.agent_id,
                "model": profile.model,
                "auth_mode": profile.auth_mode,
                "reasoning_effort": reasoning_effort,
            },
            "changed_paths": run.changed_paths,
            "generated_files": files,
            "response": value.response,
            "findings": [finding.__dict__ for finding in findings],
        },
    )
    assert_findings(findings)