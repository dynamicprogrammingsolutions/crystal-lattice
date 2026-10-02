from __future__ import annotations

import hashlib
import os
import re
from collections.abc import Iterator

import pytest

from .requirement_quality import (
    PRODUCER_CASES,
    SCENARIOS,
    RequirementQualityScenario,
    candidate_task_guidance_source,
    current_task_guidance_source,
    load_target,
    scenario_task_file_prompt,
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


pytestmark = [pytest.mark.agent_eval, pytest.mark.requirement_task_current]


def _selected_task_dataset():
    name = os.getenv("AGENT_EVAL_TASK_GUIDANCE_VARIANT", "current").strip()
    if name == "current":
        return (
            "current-task-guidance-20260914",
            "requirement-task-current",
            current_task_guidance_source(),
        )
    if name == "candidate-v3":
        return (
            "candidate-task-guidance-v3-20260915",
            "requirement-task-candidate-v3",
            candidate_task_guidance_source(),
        )
    raise ValueError(
        "AGENT_EVAL_TASK_GUIDANCE_VARIANT must be current or candidate-v3"
    )


@pytest.fixture(scope="session")
def requirement_task_harness() -> Iterator[DocumentationEvaluationHarness]:
    profile = selected_profile()
    enforce_real_model_gate(profile)
    _, _, guidance = _selected_task_dataset()
    harness = DocumentationEvaluationHarness(
        profile,
        guidance=guidance,
    )
    yield harness
    harness.close()


def _changed_task_files(run) -> dict[str, str]:
    if run.workspace is None:
        return {}
    values: dict[str, str] = {}
    for relative in matching_paths(run, "tasks"):
        if relative not in run.changed_paths or not relative.endswith(".md"):
            continue
        path = run.workspace / relative
        values[relative] = path.read_text(encoding="utf-8", errors="replace")
    return values


def _task_structure_findings(files: dict[str, str]) -> tuple[AssertionFinding, ...]:
    if len(files) != 1:
        return (
            AssertionFinding(
                "exactly one task file produced",
                False,
                repr(tuple(files)),
            ),
        )
    path, text = next(iter(files.items()))
    lines = text.splitlines()
    requirements = text.find("## Requirements checklist")
    plan_match = re.search(r"(?m)^## Execution plan\s*$", text)
    plan_tail = text[plan_match.end() :].lstrip() if plan_match else ""
    first_plan_line = plan_tail.splitlines()[0].strip() if plan_tail else ""
    immediate_draft = first_plan_line == "Status: Draft"
    headings = (
        "### Implementation decisions and open questions",
        "### Documentation",
        "### Task checklist",
        "### Requirement verification",
    )
    positions: list[int] = []
    heading_ends: list[int] = []
    search_start = plan_match.end() if plan_match is not None else 0
    for heading in headings:
        match = re.search(
            rf"(?m)^{re.escape(heading)}\s*$",
            text[search_start:],
        )
        if match is None:
            positions.append(-1)
            heading_ends.append(-1)
            continue
        absolute_start = search_start + match.start()
        absolute_end = search_start + match.end()
        positions.append(absolute_start)
        heading_ends.append(absolute_end)
        search_start = absolute_end
    ordered = all(position >= 0 for position in positions) and positions == sorted(
        positions
    )
    verification = ""
    if heading_ends[-1] >= 0:
        start = heading_ends[-1]
        end = text.find("\n## ", start)
        verification = text[start:] if end < 0 else text[start:end]
    return (
        AssertionFinding(
            "exactly one task file produced",
            True,
            path,
        ),
        AssertionFinding(
            "task begins with title and requirements",
            bool(lines)
            and lines[0].startswith("# ")
            and requirements > 0
            and "- [" in text[requirements:],
            path,
        ),
        AssertionFinding(
            "task has a Draft execution plan",
            plan_match is not None and immediate_draft,
            path,
        ),
        AssertionFinding(
            "plan closing sections are present and ordered",
            ordered,
            repr(positions),
        ),
        AssertionFinding(
            "requirement verification is populated",
            bool(verification.strip()),
            verification[:300],
        ),
        AssertionFinding(
            "planning output has no implementation or completion notes",
            re.search(r"(?m)^## Implementation Notes\s*$", text) is None
            and re.search(r"(?m)^## Completion Notes\s*$", text) is None,
            path,
        ),
    )


@pytest.mark.parametrize(
    ("producer_profile", "reasoning_effort"),
    PRODUCER_CASES,
    ids=lambda value: value,
)
@pytest.mark.parametrize("scenario", SCENARIOS, ids=lambda value: value.scenario_id)
@pytest.mark.requirements(
    "DOCGUIDE-005",
    "DOCGUIDE-006",
    "DOCVAL-010",
    "DOCVAL-011",
    "DOCVAL-012",
)
def test_requirement_quality_with_current_task_guidance(
    requirement_task_harness: DocumentationEvaluationHarness,
    scenario: RequirementQualityScenario,
    producer_profile: str,
    reasoning_effort: str,
) -> None:
    profile = requirement_task_harness.profile
    if profile.name != producer_profile:
        pytest.skip(f"run with AGENT_EVAL_PROFILE={producer_profile}")

    target = load_target(scenario)
    target_hash = target_sha256(scenario)
    dataset_id, test_prefix, guidance = _selected_task_dataset()
    prompt = scenario_task_file_prompt(scenario)
    repeat_variant = os.getenv(
        "AGENT_EVAL_TASK_CACHE_VARIANT",
        "",
    ).strip()
    run = requirement_task_harness.fresh_scenario(
        test_id=f"{test_prefix}-{scenario.scenario_id}-{reasoning_effort}",
        spec_file=scenario.spec_file,
        fixture_id=scenario.fixture_id,
        reasoning_effort=reasoning_effort,
        cache_variant=(
            f"{dataset_id}-{target_hash[:16]}:"
            f"{repeat_variant or 'default'}"
        ),
        prompt_heading="## Exact task-file user prompt",
    )
    value = require_run_value(run)
    files = _changed_task_files(run)
    profile_evidence = _evidence_value(run, "documentation_standard.profile")
    recorded_profile = profile_evidence if isinstance(profile_evidence, dict) else {}
    findings = (
        basic_run_findings(run)
        + _task_structure_findings(files)
        + (
            AssertionFinding(
                "mutation remains one task file",
                len(run.changed_paths) == 1
                and len(files) == 1
                and all(path.startswith("tasks/") for path in run.changed_paths),
                repr(run.changed_paths),
            ),
            AssertionFinding(
                "producer prompt does not request a testing strategy",
                "testing strategy" not in prompt.lower()
                and "test plan" not in prompt.lower(),
                prompt,
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
                (
                    f"profile={profile.name!r}, "
                    f"configured_auth_mode={profile.auth_mode!r}"
                ),
            ),
        )
    )
    guidance_message = guidance.context_message()
    run.record("assertions.json", [finding.__dict__ for finding in findings])
    run.record(
        f"{test_prefix}.json",
        {
            "schema_version": 1,
            "dataset_id": dataset_id,
            "scenario_id": scenario.scenario_id,
            "project": {
                "name": scenario.project_name,
                "kind": scenario.project_kind,
                "upstream": scenario.upstream,
                "revision": scenario.upstream_revision,
            },
            "target": target,
            "target_sha256": target_hash,
            "prompt": prompt,
            "repeat_variant": repeat_variant or "default",
            "producer": {
                "profile": profile.name,
                "agent_id": profile.agent_id,
                "model": profile.model,
                "auth_mode": profile.auth_mode,
                "reasoning_effort": reasoning_effort,
            },
            "guidance": {
                **guidance.metadata(),
                "effective_message_sha256": hashlib.sha256(
                    guidance_message.encode("utf-8")
                ).hexdigest(),
                "effective_message": guidance_message,
            },
            "changed_paths": run.changed_paths,
            "generated_files": files,
            "response": value.response,
            "findings": [finding.__dict__ for finding in findings],
        },
    )
    assert_findings(findings)