from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import pytest


SUITE_ROOT = Path(__file__).resolve().parents[1]
if str(SUITE_ROOT) not in sys.path:
    sys.path.insert(0, str(SUITE_ROOT))

from prepare_review_bundle import evaluate_case  # noqa: E402
from task_guidance_eval import (  # noqa: E402
    _csv_steps,
    _investigation_profile,
    _load_source_session,
    _ollama_review,
    _profile_sha256,
    _rebase_parent_session_workspace,
    _review_prompt,
    _session_sha256,
    build_parser,
)
from harness import ModelCase  # noqa: E402


def _write_json(path: Path, payload: object) -> None:
    path.write_text(
        json.dumps(payload, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _base_case(
    tmp_path: Path,
    *,
    scenario: str,
    task_text: str,
    response: str,
) -> tuple[Path, dict[str, object], dict[str, object]]:
    case_dir = tmp_path / scenario / "ollama-glm"
    case_dir.mkdir(parents=True)
    guidance = "# Guidance\n"
    guidance_hash = hashlib.sha256(guidance.encode("utf-8")).hexdigest()
    case_dir.joinpath("TASKS.md").write_text(guidance, encoding="utf-8")
    case_dir.joinpath("task-file.md").write_text(task_text, encoding="utf-8")
    case_dir.joinpath("git-status.txt").write_text(
        "?? tasks/20260721-demo.md\n",
        encoding="utf-8",
    )
    _write_json(case_dir / "mutation-calls.json", [{"tool_name": "apply_patch"}])
    parent = {
        "session_id": "parent",
        "messages": [
            {"role": "user", "content": "Plan this."},
            {"role": "assistant", "content": "Plan.", "metadata": {}},
        ],
        "metadata": {},
    }
    _write_json(case_dir / "session-1.json", parent)
    session = {
        "session_id": "parent",
        "messages": [
            *parent["messages"],
            {"role": "user", "content": "Create the task."},
            {"role": "assistant", "content": response, "metadata": {}},
        ],
        "metadata": {},
    }
    metadata: dict[str, object] = {
        "scenario": scenario,
        "agent_id": "glm-ollama",
        "model": "glm",
        "guidance_sha256": guidance_hash,
        "mutation_call_limit": 3,
        "expected_requirement_ids": ["R1", "R2"],
        "research_markers": [
            "AbsolutePathBufGuard",
            "parse_managed_requirements_base64",
        ],
    }
    metadata["fork_parent_session_sha256"] = hashlib.sha256(
        json.dumps(parent, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    _write_json(case_dir / "metadata.json", metadata)
    _write_json(case_dir / "session-2.json", session)
    case_dir.joinpath("assertions.md").write_text(
        "# Assertions\n",
        encoding="utf-8",
    )
    return case_dir, metadata, session


def test_help_contains_copyable_workflow_commands() -> None:
    help_text = build_parser().format_help()

    assert "task_guidance_eval.py run" in help_text
    assert "task_guidance_eval.py assert" in help_text
    assert "task_guidance_eval.py review" in help_text
    assert "task_guidance_eval.py bundle" in help_text


def test_run_parser_accepts_combined_steps_and_assertion_flag() -> None:
    args = build_parser().parse_args(
        [
            "run",
            "--steps",
            "plan,retain-plan,omit-plan",
            "--provider",
            "ollama",
            "--assert",
        ]
    )

    assert args.steps == ["plan", "retain-plan", "omit-plan"]
    assert args.run_assertions is True
    assert _csv_steps("existing-task-plan") == ["existing-task-plan"]


def test_session_hash_is_stable_for_serialized_round_trip() -> None:
    from agent_core import Session

    session = Session.from_dict(
        {
            "session_id": "demo",
            "messages": [{"role": "user", "content": "Plan this."}],
            "metadata": {"key": "value"},
        }
    )
    restored = Session.from_dict(json.loads(json.dumps(session.to_dict())))

    assert _session_sha256(session) == _session_sha256(restored)


def test_guidance_neutral_source_profile_can_be_reused(tmp_path: Path) -> None:
    from agent_core import Session

    model_case = ModelCase(
        case_id="ollama-glm",
        agent_id="glm-ollama",
        model="glm-test",
        auth_mode="ollama",
    )
    profile = _investigation_profile(model_case)
    session = Session.from_dict(
        {
            "session_id": "source",
            "messages": [
                {"role": "user", "content": "Investigate."},
                {"role": "assistant", "content": "Findings."},
            ],
            "metadata": {},
        }
    )
    source = tmp_path / "source"
    source.mkdir()
    _write_json(source / "session-1.json", session.to_dict())
    _write_json(
        source / "metadata.json",
        {
            "investigation_task_guidance_enabled": False,
            "investigation_profile": profile,
            "investigation_fingerprint": _profile_sha256(profile),
            "investigation_session_sha256": _session_sha256(session),
        },
    )

    loaded, metadata = _load_source_session(source, model_case=model_case)

    assert loaded.to_dict() == session.to_dict()
    assert metadata["investigation_profile"] == profile

    incompatible_model = ModelCase(
        case_id="ollama-other",
        agent_id="glm-ollama",
        model="other-model",
        auth_mode="ollama",
    )
    with pytest.raises(ValueError, match="incompatible"):
        _load_source_session(source, model_case=incompatible_model)


def test_reused_session_workspace_is_rebased_without_changing_source(
    tmp_path: Path,
) -> None:
    from agent_core import Session

    source_workspace = tmp_path / "source-case" / "workspace"
    target_workspace = tmp_path / "fork-case" / "workspace"
    session = Session.from_dict(
        {
            "session_id": "source",
            "messages": [
                {
                    "role": "system",
                    "content": (
                        f"Primary working directory: {source_workspace}. "
                        f"Write only under {source_workspace}."
                    ),
                    "metadata": {
                        "working_directory": str(source_workspace),
                    },
                },
                {
                    "role": "assistant",
                    "content": "Investigation findings.",
                },
            ],
            "metadata": {
                "native_messages": [{"role": "system", "content": "cached"}],
                "native_messages_integrity": "cached",
            },
        }
    )

    rebased, replacement_count = _rebase_parent_session_workspace(
        session,
        source_workspace=source_workspace,
        target_workspace=target_workspace,
    )

    assert replacement_count == 3
    assert str(source_workspace) in json.dumps(session.to_dict())
    assert str(source_workspace) not in json.dumps(rebased.to_dict())
    assert json.dumps(rebased.to_dict()).count(str(target_workspace)) == 3
    assert "native_messages" in session.metadata
    assert "native_messages" not in rebased.metadata
    assert "native_messages_integrity" not in rebased.metadata


def test_guided_or_incompatible_source_is_rejected(tmp_path: Path) -> None:
    model_case = ModelCase(
        case_id="ollama-glm",
        agent_id="glm-ollama",
        model="glm-test",
        auth_mode="ollama",
    )
    source = tmp_path / "source"
    source.mkdir()
    _write_json(
        source / "session-1.json",
        {
            "session_id": "source",
            "messages": [{"role": "assistant", "content": "Findings."}],
            "metadata": {},
        },
    )
    _write_json(
        source / "metadata.json",
        {"investigation_task_guidance_enabled": True},
    )

    with pytest.raises(ValueError, match="not guidance-neutral"):
        _load_source_session(source, model_case=model_case)


@pytest.mark.parametrize(
    ("scenario", "metadata_key", "enabled"),
    [
        ("planning-seed", "investigation_task_guidance_enabled", False),
        (
            "create-task-retain-plan",
            "task_creation_task_guidance_enabled",
            True,
        ),
    ],
)
def test_compiled_request_records_expected_guidance_inclusion(
    tmp_path: Path,
    scenario: str,
    metadata_key: str,
    enabled: bool,
) -> None:
    task = """\
# Demo

Description.

## Requirements checklist

- [ ] R1: Resolve home paths.
- [ ] R2: Preserve existing behavior.

## Research

`AbsolutePathBufGuard` is absent from `parse_managed_requirements_base64`.

## Execution plan

Status: Draft

Apply the selected boundary.

### Implementation decisions and open questions

No open implementation questions.

### Documentation

No change.

### Task checklist

- [ ] Implement.

### Requirement verification

- R1: Acceptance evidence.
- R2: Acceptance evidence.
"""
    case_dir, metadata, session = _base_case(
        tmp_path,
        scenario=scenario,
        task_text=task,
        response="Created the requested task.",
    )
    metadata[metadata_key] = enabled
    compiled = "Base system prompt.\n"
    if enabled:
        compiled += case_dir.joinpath("TASKS.md").read_text(encoding="utf-8")
    case_dir.joinpath("compiled-system-message.md").write_text(
        compiled,
        encoding="utf-8",
    )
    if scenario == "planning-seed":
        case_dir.joinpath("git-status-1.txt").write_text("", encoding="utf-8")

    results = evaluate_case(case_dir, metadata, session)

    inclusion = next(
        result
        for result in results
        if result.name == "Task guidance is included only for the intended model turn"
    )
    assert inclusion.status == "PASS"


def test_ollama_review_returns_text_without_judging_exit_status(
    monkeypatch,
) -> None:
    class Response:
        def raise_for_status(self) -> None:
            return None

        def json(self) -> dict[str, object]:
            return {
                "choices": [
                    {"message": {"content": "# Overall judgment\n\nReview me."}}
                ]
            }

    captured: dict[str, object] = {}

    def post(url: str, *, json: object, timeout: int):
        captured.update({"url": url, "json": json, "timeout": timeout})
        return Response()

    monkeypatch.setattr("task_guidance_eval.requests.post", post)

    content, raw = _ollama_review(
        base_url="http://ollama.invalid/v1",
        model="glm-test",
        prompt="Review this.",
    )

    assert content.startswith("# Overall judgment")
    assert raw["choices"]
    assert captured["url"] == "http://ollama.invalid/v1/chat/completions"
    assert captured["timeout"] == 600


def test_retain_plan_case_has_only_minimal_mechanical_checks(
    tmp_path: Path,
) -> None:
    task = """\
# Demo

Description.

## Requirements checklist

- [ ] R1: Resolve home paths.
- [ ] R2: Preserve existing behavior.

## Research

`AbsolutePathBufGuard` is absent from `parse_managed_requirements_base64`.

## Execution plan

Status: Draft

Apply the selected boundary.

### Implementation decisions and open questions

No open implementation questions.

### Documentation

No user-facing documentation change.

### Task checklist

- [ ] Implement the approved direction.

### Requirement verification

- R1: macOS integration test.
- R2: regression coverage.
"""
    case_dir, metadata, session = _base_case(
        tmp_path,
        scenario="create-task-retain-plan",
        task_text=task,
        response="Created the task with the requested draft plan.",
    )

    results = evaluate_case(case_dir, metadata, session)

    assert not [result for result in results if result.status == "FAIL"]
    assert any(
        result.name == "Requirements and execution tasks are kept conceptually separate"
        and result.status == "MANUAL"
        for result in results
    )
    assert any(
        result.name == "Execution plan free-form body supports continuation"
        and result.status == "MANUAL"
        for result in results
    )
    assert any(
        result.name == "Requirement verification is acceptance-focused"
        and result.status == "MANUAL"
        for result in results
    )


def test_requirement_traceability_stops_before_additional_verification(
    tmp_path: Path,
) -> None:
    task = """\
# Demo

Description.

## Requirements checklist

- [ ] R1: Resolve home paths.
- [ ] R2: Preserve existing behavior.

## Research

`AbsolutePathBufGuard` is absent from `parse_managed_requirements_base64`.

## Execution plan

Status: Draft

Apply the selected boundary.

### Implementation decisions and open questions

No open implementation questions.

### Documentation

No user-facing documentation change.

### Task checklist

- [ ] Implement the approved direction.

### Requirement verification

#### Delivery behavior

- R1: Public-boundary acceptance scenario.
- R2: Public-boundary regression scenario.

### Additional implementation verification

- R1 and R2: Internal parser and cleanup tests.
"""
    case_dir, metadata, session = _base_case(
        tmp_path,
        scenario="create-task-retain-plan",
        task_text=task,
        response="Created the task with the requested draft plan.",
    )

    passing = evaluate_case(case_dir, metadata, session)

    assert not [result for result in passing if result.status == "FAIL"]

    task_without_acceptance_ids = task.replace(
        "- R1: Public-boundary acceptance scenario.\n"
        "- R2: Public-boundary regression scenario.",
        "- Home paths: Public-boundary acceptance scenario.\n"
        "- Existing behavior: Public-boundary regression scenario.",
    )
    case_dir.joinpath("task-file.md").write_text(
        task_without_acceptance_ids,
        encoding="utf-8",
    )

    failing = evaluate_case(case_dir, metadata, session)

    traceability = next(
        result
        for result in failing
        if result.name == "Requirement verification references every requirement id"
    )
    assert traceability.status == "FAIL"


def test_omit_plan_case_retains_context_without_plan(
    tmp_path: Path,
) -> None:
    task = """\
# Demo

Description.

## Requirements checklist

- [ ] R1: Resolve home paths.
- [ ] R2: Preserve existing behavior.

## Research

`AbsolutePathBufGuard` is absent from `parse_managed_requirements_base64`.

## Open questions

- Requirement question: should ordinary relative MDM paths remain rejected?
"""
    case_dir, metadata, session = _base_case(
        tmp_path,
        scenario="create-task-omit-plan",
        task_text=task,
        response="Created the task with requirements and supporting context.",
    )

    results = evaluate_case(case_dir, metadata, session)

    assert not [result for result in results if result.status == "FAIL"]
    assert any(
        result.name == "Omit-plan handoff excludes plan content in substance"
        and result.status == "MANUAL"
        for result in results
    )


def test_empirical_prompt_excludes_model_quality_judgments(
    tmp_path: Path,
) -> None:
    task = """\
# Demo

Description.

## Requirements checklist

- [ ] R1: Resolve home paths.
- [ ] R2: Preserve existing behavior.

## Supporting details

`AbsolutePathBufGuard` is absent from `parse_managed_requirements_base64`.
"""
    case_dir, metadata, _ = _base_case(
        tmp_path,
        scenario="create-task-retain-plan",
        task_text=task,
        response="Created the requested handoff.",
    )

    prompt = _review_prompt(case_dir=case_dir, metadata=metadata)
    normalized = " ".join(prompt.split())

    assert "instruction clarity and compliance only" in normalized
    assert (
        "requirements are outcomes or constraints rather than execution tasks"
        in normalized
    )
    assert (
        "observable acceptance evidence at a user-relevant or public boundary"
        in normalized
    )
    assert (
        "implementation-specific robustness checks, when present, are kept "
        "separate" in normalized
    )
    assert "substantive free-form body after status" in normalized
    assert (
        "important implementation decisions and open implementation questions "
        "are collected immediately before documentation" in normalized
    )
    assert "requirement questions and decisions changing scope" in normalized
    assert (
        "human-facing sections are concise while supporting details preserve"
        in normalized
    )
    assert "Do not judge whether repository findings are correct" in normalized
    assert "whether the plan satisfies R1-R5" not in prompt


def test_empirical_prompt_treats_omit_plan_verification_as_plan_content(
    tmp_path: Path,
) -> None:
    task = """\
# Demo

Description.

## Requirements checklist

- [ ] R1: Resolve home paths.
- [ ] R2: Preserve existing behavior.

## Supporting details

Existing tests document the current behavior.
"""
    case_dir, metadata, _ = _base_case(
        tmp_path,
        scenario="create-task-omit-plan",
        task_text=task,
        response="Created the requested handoff.",
    )

    normalized = " ".join(_review_prompt(case_dir=case_dir, metadata=metadata).split())

    assert "because this is an omit-plan handoff" in normalized
    assert (
        "do not require requirement verification, planned tests, documentation, "
        "implementation details" in normalized
    )
    assert (
        "do not penalize the handoff merely because separate verification" in normalized
    )
    assert "whether requirement verification maps each requirement" not in normalized
