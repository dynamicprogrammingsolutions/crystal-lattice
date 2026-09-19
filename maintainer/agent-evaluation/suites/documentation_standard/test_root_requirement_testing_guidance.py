from __future__ import annotations

import hashlib
import os
import re

import pytest

from .requirement_quality import (
    PRODUCER_CASES,
    ROOT_GUIDANCE_MODES,
    SCENARIOS,
    RequirementQualityScenario,
    load_target,
    scenario_root_plan_prompt,
    scenario_task_file_prompt,
    target_sha256,
)
from .compiled_guidance import (
    compilation_evidence,
    compile_scenario_guidance,
    dataset_identity,
    guidance_source,
)
from .support import (
    AssertionFinding,
    DocumentationEvaluationHarness,
    RUNNER_DEFAULT_SYSTEM_MESSAGE,
    assert_findings,
    basic_run_findings,
    enforce_real_model_gate,
    require_run_value,
    selected_profile,
)
from .test_consumers import _evidence_value


pytestmark = [pytest.mark.agent_eval, pytest.mark.root_requirement_testing]
RECORD_NAME = "root-guidance-requirement-quality.json"


def _selected_root_dataset(
    scenario: RequirementQualityScenario,
) -> tuple[str, str, str, object, object]:
    mode = os.getenv(
        "AGENT_EVAL_ROOT_GUIDANCE_MODE",
        "root-only",
    ).strip()
    if mode not in ROOT_GUIDANCE_MODES:
        raise ValueError(
            "AGENT_EVAL_ROOT_GUIDANCE_MODE must be one of: "
            + ", ".join(sorted(ROOT_GUIDANCE_MODES))
        )
    compilation = compile_scenario_guidance(scenario)
    dataset_id, test_prefix = dataset_identity(compilation, mode=mode)
    return (
        dataset_id,
        test_prefix,
        mode,
        guidance_source(compilation, mode=mode),
        compilation,
    )


def _selected_candidate_ids() -> set[str]:
    return {
        item.strip()
        for item in os.getenv(
            "AGENT_EVAL_ROOT_GUIDANCE_CANDIDATES",
            "",
        ).split(",")
        if item.strip()
    }


@pytest.fixture(scope="session")
def root_guidance_profile():
    profile = selected_profile()
    enforce_real_model_gate(profile)
    return profile


def _changed_task_files(run) -> dict[str, str]:
    values: dict[str, str] = {}
    for relative in run.changed_paths:
        if not relative.startswith("tasks/") or not relative.endswith(".md"):
            continue
        live = run.workspace / relative if run.workspace is not None else None
        retained = (
            run.artifact_dir
            / "raw"
            / "workspace"
            / "untracked"
            / relative
        )
        source = live if live is not None and live.is_file() else retained
        if not source.is_file():
            continue
        values[relative] = source.read_text(
            encoding="utf-8",
            errors="replace",
        )
    return values


def _task_structure_findings(
    files: dict[str, str],
) -> tuple[AssertionFinding, ...]:
    if len(files) != 1:
        return (
            AssertionFinding(
                "exactly one task file produced",
                False,
                repr(tuple(files)),
            ),
        )
    path, text = next(iter(files.items()))
    requirements = text.find("## Requirements checklist")
    plan_match = re.search(r"(?m)^## Execution plan\s*$", text)
    plan_tail = text[plan_match.end() :].lstrip() if plan_match else ""
    first_plan_line = plan_tail.splitlines()[0].strip() if plan_tail else ""
    headings = (
        "### Implementation decisions and open questions",
        "### Documentation",
        "### Task checklist",
        "### Requirement verification",
    )
    positions: list[int] = []
    search_start = plan_match.end() if plan_match is not None else 0
    for heading in headings:
        match = re.search(
            rf"(?m)^{re.escape(heading)}\s*$",
            text[search_start:],
        )
        if match is None:
            positions.append(-1)
            continue
        position = search_start + match.start()
        positions.append(position)
        search_start += match.end()
    return (
        AssertionFinding(
            "exactly one task file produced",
            True,
            path,
        ),
        AssertionFinding(
            "task contains requirements",
            requirements > 0 and "- [" in text[requirements:],
            path,
        ),
        AssertionFinding(
            "task has a Draft execution plan",
            plan_match is not None and first_plan_line == "Status: Draft",
            path,
        ),
        AssertionFinding(
            "plan closing sections are present and ordered",
            all(position >= 0 for position in positions)
            and positions == sorted(positions),
            repr(positions),
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
    "DOCAGENT-003",
    "DOCAGENT-004",
    "DOCVAL-013",
)
def test_root_requirement_testing_guidance(
    root_guidance_profile,
    scenario: RequirementQualityScenario,
    producer_profile: str,
    reasoning_effort: str,
) -> None:
    profile = root_guidance_profile
    candidate_id = f"{producer_profile}-{reasoning_effort}"
    if profile.name != producer_profile:
        pytest.skip(f"run with AGENT_EVAL_PROFILE={producer_profile}")
    selected_ids = _selected_candidate_ids()
    if selected_ids and candidate_id not in selected_ids:
        pytest.skip(f"{candidate_id} is not in the focused candidate set")

    (
        dataset_id,
        test_prefix,
        mode,
        guidance,
        compilation,
    ) = _selected_root_dataset(scenario)
    target = load_target(scenario)
    target_hash = target_sha256(scenario)
    task_mode = mode == "task"
    prompt_heading = (
        "## Exact task-file user prompt"
        if task_mode
        else "## Exact root-plan user prompt"
    )
    prompt = (
        scenario_task_file_prompt(scenario)
        if task_mode
        else scenario_root_plan_prompt(scenario)
    )
    repeat_variant = os.getenv(
        "AGENT_EVAL_ROOT_GUIDANCE_CACHE_VARIANT",
        "",
    ).strip()
    run_attempt = os.getenv(
        "AGENT_EVAL_ROOT_GUIDANCE_RUN_ATTEMPT",
        "",
    ).strip()
    harness = DocumentationEvaluationHarness(
        profile,
        guidance=guidance,
        runner_mode=RUNNER_DEFAULT_SYSTEM_MESSAGE,
    )
    try:
        run = harness.fresh_scenario(
            test_id=(
                f"{test_prefix}-{scenario.scenario_id}-{reasoning_effort}"
            ),
            spec_file=scenario.spec_file,
            fixture_id=scenario.fixture_id,
            reasoning_effort=reasoning_effort,
            cache_variant=(
                f"{dataset_id}-{target_hash[:16]}:"
                f"{repeat_variant or 'default'}:"
                f"{run_attempt or 'initial'}"
            ),
            prompt_heading=prompt_heading,
            include_tasks=task_mode,
            inspect_system_message=True,
        )
    finally:
        harness.close()
    value = require_run_value(run)
    files = (
        _changed_task_files(run)
        if task_mode
        else {"response.md": value.response}
    )
    profile_evidence = _evidence_value(run, "documentation_standard.profile")
    recorded_profile = profile_evidence if isinstance(profile_evidence, dict) else {}
    injection = _evidence_value(
        run,
        "documentation_standard.guidance_injection",
    )
    injection_value = injection if isinstance(injection, dict) else {}
    compiled = _evidence_value(
        run,
        "documentation_standard.compiled_system_message",
    )
    compiled_value = compiled if isinstance(compiled, dict) else {}
    source_rows = compiled_value.get("sources")
    sources = source_rows if isinstance(source_rows, list) else []

    mode_findings: tuple[AssertionFinding, ...]
    if task_mode:
        mode_findings = _task_structure_findings(files) + (
            AssertionFinding(
                "mutation remains one task file",
                len(run.changed_paths) == 1
                and len(files) == 1
                and all(
                    path.startswith("tasks/")
                    for path in run.changed_paths
                ),
                repr(run.changed_paths),
            ),
        )
    else:
        mode_findings = (
            AssertionFinding(
                "root-only planning does not mutate the workspace",
                not run.changed_paths,
                repr(run.changed_paths),
            ),
            AssertionFinding(
                "root-only planning returns substantive requirements and plan",
                len(value.response.strip()) >= 200,
                f"{len(value.response.strip())} characters",
            ),
        )

    findings = (
        basic_run_findings(run)
        + mode_findings
        + (
            AssertionFinding(
                "suite guidance injection is disabled",
                injection_value.get("injected") is False
                and injection_value.get("paths") == [],
                repr(injection_value),
            ),
            AssertionFinding(
                "default model-family system message is compiled",
                compiled_value.get("runner")
                == RUNNER_DEFAULT_SYSTEM_MESSAGE
                and compiled_value.get("family")
                == ("codex" if profile.name == "gpt" else "claude")
                and compiled_value.get("suite_wrapper_absent") is True,
                repr(compiled_value),
            ),
            AssertionFinding(
                "compiled sources have exact occurrence counts",
                bool(sources)
                and all(
                    isinstance(item, dict)
                    and item.get("observed_occurrences")
                    == item.get("expected_occurrences")
                    for item in sources
                ),
                repr(sources),
            ),
            AssertionFinding(
                "normal TASKS condition matches mode",
                compiled_value.get("include_tasks") is task_mode,
                repr(compiled_value.get("include_tasks")),
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
    compiled_message = str(compiled_value.get("compiled_message", ""))
    record = {
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
        "mode": mode,
        "repeat_variant": repeat_variant or "default",
        "run_attempt": run_attempt or "initial",
        "guidance_compilation": compilation_evidence(
            compilation,
            mode=mode,
        ),
        "producer": {
            "profile": profile.name,
            "agent_id": profile.agent_id,
            "model": profile.model,
            "auth_mode": profile.auth_mode,
            "reasoning_effort": reasoning_effort,
        },
        "guidance": {
            **guidance.metadata(),
            "injected_paths": [],
            "effective_message_sha256": hashlib.sha256(
                compiled_message.encode("utf-8")
            ).hexdigest(),
            "effective_message": compiled_message,
        },
        "instruction_delivery": compiled_value,
        "changed_paths": run.changed_paths,
        "generated_files": files,
        "response": value.response,
        "findings": [finding.__dict__ for finding in findings],
    }
    run.record("assertions.json", record["findings"])
    run.record(RECORD_NAME, record)
    assert_findings(findings)