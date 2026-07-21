from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from prepare_review_bundle import evaluate_case  # noqa: E402
from task_guidance_eval import (  # noqa: E402
    _csv_steps,
    _ollama_review,
    _review_prompt,
    _session_sha256,
    build_parser,
)


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

### Requirement verification

- R1: macOS integration test.
- R2: regression coverage.

### Documentation

No user-facing documentation change.

### Task checklist

- [ ] Implement the approved direction.
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
        scenario="create-task-omit-plan",
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
    assert "Do not judge whether repository findings are correct" in normalized
    assert "whether the plan satisfies R1-R5" not in prompt