from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import sys
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

import requests


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from harness import (  # noqa: E402
    DEFAULT_CHATGPT_MODEL,
    DEFAULT_GUIDANCE_PATH,
    DEFAULT_OLLAMA_AGENT,
    DEFAULT_OLLAMA_BASE_URL,
    EVAL_ROOT,
    OMIT_PLAN_PROMPT,
    PREMADE_TASK_TEMPLATE,
    RETAIN_PLAN_PROMPT,
    ROOT,
    TASK_PROMPT,
    ModelCase,
    PreparedCase,
    Session,
    assistant_text_after_last_user,
    changed_paths,
    collect_tool_calls,
    current_run_id,
    environment_for_case,
    prepare_case,
    send_turn,
    start_agent,
    write_final_task_artifact,
    write_git_artifacts,
    write_json,
    write_turn_artifacts,
)
from prepare_review_bundle import (  # noqa: E402
    assertions_markdown,
    discover_case_dirs,
    evaluate_case,
    final_session_path,
    load_json,
    prepare_review_bundle,
)


REQUIREMENT_IDS = ("R1", "R2", "R3", "R4", "R5")
RESEARCH_MARKERS = (
    "AbsolutePathBufGuard",
    "parse_managed_requirements_base64",
    "load_managed_admin_requirements_toml",
)
RUN_STEPS = (
    "plan",
    "retain-plan",
    "omit-plan",
    "existing-task-plan",
)

EXAMPLES = """\
Examples:

  Reuse an existing GLM planning session and run both forks:

    python test/task_guidance/task_guidance_eval.py run \\
      --steps retain-plan,omit-plan \\
      --provider ollama \\
      --source-case tmp/task-guidance-eval/runs/20260721-tasks-v7-revision-6/create-task-after-plan/ollama-glm-5.2 \\
      --run-id task-guidance-fork-smoke \\
      --assert

  Run a fresh plan and both forks:

    python test/task_guidance/task_guidance_eval.py run \\
      --steps plan,retain-plan,omit-plan \\
      --provider ollama \\
      --run-id task-guidance-fresh

  Run the existing-task planning scenario:

    python test/task_guidance/task_guidance_eval.py run \\
      --steps existing-task-plan \\
      --provider ollama \\
      --run-id task-guidance-existing

  Use the ChatGPT account:

    python test/task_guidance/task_guidance_eval.py run \\
      --steps plan,retain-plan,omit-plan \\
      --provider chatgpt \\
      --model gpt-5.6-luna \\
      --credentials-dir "$HOME/.crystal" \\
      --run-id task-guidance-chatgpt

  Assert, review, and bundle an existing run:

    python test/task_guidance/task_guidance_eval.py assert \\
      --run-dir tmp/task-guidance-eval/runs/<run-id>

    python test/task_guidance/task_guidance_eval.py review \\
      --run-dir tmp/task-guidance-eval/runs/<run-id>

    python test/task_guidance/task_guidance_eval.py bundle \\
      --run-dir tmp/task-guidance-eval/runs/<run-id>
"""


def _csv_steps(raw: str) -> list[str]:
    values = [item.strip() for item in raw.split(",") if item.strip()]
    unknown = sorted(set(values) - set(RUN_STEPS))
    if unknown:
        raise argparse.ArgumentTypeError(
            f"unknown steps {unknown}; choose from {', '.join(RUN_STEPS)}"
        )
    if not values:
        raise argparse.ArgumentTypeError("at least one step is required")
    return values


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "default"


def _default_ollama_model() -> str:
    config_path = (
        ROOT / "application" / "python" / "agent_terminal_app"
        / "default_config" / "config.json"
    )
    config = json.loads(config_path.read_text(encoding="utf-8"))
    return str(config["agents"][DEFAULT_OLLAMA_AGENT]["model"])


def _model_case(args: argparse.Namespace) -> ModelCase:
    if args.provider == "chatgpt":
        agent_id = args.agent or "codex-openai"
        model = args.model or DEFAULT_CHATGPT_MODEL
        auth_mode = "chatgpt"
    else:
        agent_id = args.agent or DEFAULT_OLLAMA_AGENT
        model = args.model or _default_ollama_model()
        auth_mode = "ollama"
    return ModelCase(
        case_id=f"{args.provider}-{_slug(model)}",
        agent_id=agent_id,
        model=model,
        auth_mode=auth_mode,
    )


@contextmanager
def _configured_environment(args: argparse.Namespace) -> Iterator[None]:
    updates = {
        "TASK_GUIDANCE_FILE": str(args.guidance.expanduser().resolve()),
        "OLLAMA_OPENAI_BASE_URL": args.ollama_base_url,
        "CHATGPT_TEST_STATE_DIR": str(args.credentials_dir.expanduser().resolve()),
    }
    previous = {key: os.environ.get(key) for key in updates}
    os.environ.update(updates)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value


@contextmanager
def _case_environment(prepared: PreparedCase) -> Iterator[None]:
    updates = environment_for_case(prepared)
    previous = {key: os.environ.get(key) for key in updates}
    os.environ.update(updates)
    try:
        yield
    finally:
        for key, value in previous.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        from agent_app.runtime_env import RuntimeEnvOverlay

        RuntimeEnvOverlay._reset_for_tests()


def _session_sha256(session: Session) -> str:
    payload = json.dumps(
        session.to_dict(),
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def _load_source_session(source_case: Path) -> Session:
    path = source_case.expanduser().resolve() / "session-1.json"
    if not path.is_file():
        raise FileNotFoundError(f"source planning session does not exist: {path}")
    return Session.from_dict(load_json(path))


def _last_visible_message(session: Session, role: str) -> str:
    for message in reversed(session.messages):
        if message.role == role and isinstance(message.content, str):
            if message.content.strip():
                return message.content
    return ""


def _copy_parent_artifacts(
    *,
    target: PreparedCase,
    parent_session: Session,
    source_case: Path | None,
) -> None:
    write_json(target.case_dir / "session-1.json", parent_session.to_dict())
    target.case_dir.joinpath("prompt-1.md").write_text(
        _last_visible_message(parent_session, "user").rstrip() + "\n",
        encoding="utf-8",
    )
    target.case_dir.joinpath("response-1.md").write_text(
        _last_visible_message(parent_session, "assistant").rstrip() + "\n",
        encoding="utf-8",
    )
    target.case_dir.joinpath("git-status-1.txt").write_text(
        "",
        encoding="utf-8",
    )
    write_json(
        target.case_dir / "shared-tool-calls.json",
        collect_tool_calls(parent_session),
    )
    if source_case is not None:
        target.case_dir.joinpath("source-case.txt").write_text(
            str(source_case.expanduser().resolve()) + "\n",
            encoding="utf-8",
        )


def _update_metadata(case_dir: Path, **updates: Any) -> None:
    path = case_dir / "metadata.json"
    payload = load_json(path)
    payload.update(updates)
    write_json(path, payload)


def _capture_task_if_available(prepared: PreparedCase) -> None:
    candidates = [
        prepared.workspace / path
        for path in changed_paths(prepared.workspace)
        if path.startswith("tasks/") and path.endswith(".md")
    ]
    if len(candidates) == 1 and candidates[0].is_file():
        write_final_task_artifact(prepared, candidates[0])


def _close_running(running: Any) -> None:
    if running is None:
        return
    running.prompt_capture.uninstall()
    running.mutation_budget.uninstall()
    running.app.close()


def _run_seed(
    *,
    model_case: ModelCase,
    run_id: str,
) -> tuple[Session, Path]:
    prepared = prepare_case(
        scenario="planning-seed",
        model_case=model_case,
        run_id=run_id,
        with_premade_task=False,
    )
    running = None
    try:
        with _case_environment(prepared):
            running = start_agent(prepared)
            result = send_turn(running, prepared, prompt=TASK_PROMPT)
        write_turn_artifacts(
            prepared,
            turn_number=1,
            prompt=TASK_PROMPT,
            result=result,
            mutation_budget=running.mutation_budget,
        )
        _update_metadata(
            prepared.case_dir,
            role="planning-seed",
            expected_requirement_ids=list(REQUIREMENT_IDS),
            research_markers=list(RESEARCH_MARKERS),
        )
        return result.session, prepared.case_dir
    except BaseException as exc:
        prepared.case_dir.joinpath("failure.txt").write_text(
            f"{type(exc).__name__}: {exc}\n",
            encoding="utf-8",
        )
        write_git_artifacts(prepared)
        raise
    finally:
        _close_running(running)


def _run_fork(
    *,
    scenario: str,
    prompt: str,
    model_case: ModelCase,
    run_id: str,
    parent_session: Session,
    source_case: Path | None,
) -> Path:
    prepared = prepare_case(
        scenario=scenario,
        model_case=model_case,
        run_id=run_id,
        with_premade_task=False,
    )
    parent_hash = _session_sha256(parent_session)
    _copy_parent_artifacts(
        target=prepared,
        parent_session=parent_session,
        source_case=source_case,
    )
    source_has_ids = all(
        requirement_id in json.dumps(parent_session.to_dict())
        for requirement_id in REQUIREMENT_IDS
    )
    _update_metadata(
        prepared.case_dir,
        role="fork",
        fork_parent_session_sha256=parent_hash,
        source_case=str(source_case.resolve()) if source_case else None,
        expected_requirement_ids=list(REQUIREMENT_IDS) if source_has_ids else [],
        research_markers=list(RESEARCH_MARKERS),
    )

    running = None
    try:
        with _case_environment(prepared):
            running = start_agent(prepared)
            result = send_turn(
                running,
                prepared,
                prompt=prompt,
                session=parent_session,
            )
        write_turn_artifacts(
            prepared,
            turn_number=2,
            prompt=prompt,
            result=result,
            mutation_budget=running.mutation_budget,
        )
        parent_message_count = len(parent_session.messages)
        branch_calls = [
            call
            for call in collect_tool_calls(result.session)
            if int(call.get("message_index", -1)) >= parent_message_count
        ]
        write_json(prepared.case_dir / "branch-tool-calls.json", branch_calls)
        _capture_task_if_available(prepared)
        return prepared.case_dir
    except BaseException as exc:
        prepared.case_dir.joinpath("failure.txt").write_text(
            f"{type(exc).__name__}: {exc}\n",
            encoding="utf-8",
        )
        write_git_artifacts(prepared)
        raise
    finally:
        _close_running(running)


def _run_existing_task(
    *,
    model_case: ModelCase,
    run_id: str,
) -> Path:
    prepared = prepare_case(
        scenario="plan-existing-task",
        model_case=model_case,
        run_id=run_id,
        with_premade_task=True,
    )
    assert prepared.premade_task_path is not None
    relative = prepared.premade_task_path.relative_to(prepared.workspace).as_posix()
    prompt = f"Please prepare an execution plan for `{relative}`."
    _update_metadata(
        prepared.case_dir,
        role="existing-task-plan",
        expected_requirement_ids=list(REQUIREMENT_IDS),
        research_markers=list(RESEARCH_MARKERS),
    )

    running = None
    try:
        with _case_environment(prepared):
            running = start_agent(prepared)
            result = send_turn(running, prepared, prompt=prompt)
        write_turn_artifacts(
            prepared,
            turn_number=1,
            prompt=prompt,
            result=result,
            mutation_budget=running.mutation_budget,
        )
        write_final_task_artifact(prepared, prepared.premade_task_path)
        return prepared.case_dir
    except BaseException as exc:
        prepared.case_dir.joinpath("failure.txt").write_text(
            f"{type(exc).__name__}: {exc}\n",
            encoding="utf-8",
        )
        write_git_artifacts(prepared)
        raise
    finally:
        _close_running(running)


def run_command(args: argparse.Namespace) -> int:
    model_case = _model_case(args)
    run_id = args.run_id or current_run_id()
    run_dir = EVAL_ROOT / "runs" / run_id
    steps = args.steps
    if any(step in steps for step in ("retain-plan", "omit-plan")):
        if "plan" not in steps and args.source_case is None:
            raise SystemExit(
                "retain-plan and omit-plan require either the plan step or "
                "--source-case"
            )

    with _configured_environment(args):
        parent_session: Session | None = None
        source_case: Path | None = None
        if "plan" in steps:
            parent_session, source_case = _run_seed(
                model_case=model_case,
                run_id=run_id,
            )
        elif args.source_case is not None:
            source_case = args.source_case.expanduser().resolve()
            parent_session = _load_source_session(source_case)

        errors: list[str] = []
        if "retain-plan" in steps and parent_session is not None:
            try:
                _run_fork(
                    scenario="create-task-retain-plan",
                    prompt=RETAIN_PLAN_PROMPT,
                    model_case=model_case,
                    run_id=run_id,
                    parent_session=parent_session,
                    source_case=source_case,
                )
            except BaseException as exc:
                errors.append(f"retain-plan: {type(exc).__name__}: {exc}")
        if "omit-plan" in steps and parent_session is not None:
            try:
                _run_fork(
                    scenario="create-task-omit-plan",
                    prompt=OMIT_PLAN_PROMPT,
                    model_case=model_case,
                    run_id=run_id,
                    parent_session=parent_session,
                    source_case=source_case,
                )
            except BaseException as exc:
                errors.append(f"omit-plan: {type(exc).__name__}: {exc}")
        if "existing-task-plan" in steps:
            try:
                _run_existing_task(model_case=model_case, run_id=run_id)
            except BaseException as exc:
                errors.append(
                    f"existing-task-plan: {type(exc).__name__}: {exc}"
                )

    print(f"Run artifacts: {run_dir}")
    if args.run_assertions:
        assertion_status = assert_run(run_dir, case_name=None)
        if assertion_status:
            errors.append("mechanical assertions failed")
        _print_review_next(run_dir)
    else:
        print(
            "Next:\n"
            f"  python test/task_guidance/task_guidance_eval.py assert "
            f"--run-dir {run_dir}"
        )
    if errors:
        print("\nRun problems:")
        for error in errors:
            print(f"- {error}")
        return 1
    return 0


def _selected_cases(run_dir: Path, case_name: str | None) -> list[Path]:
    cases = discover_case_dirs(run_dir)
    if case_name is None:
        return cases
    selected = [
        case
        for case in cases
        if case_name in {case.name, str(load_json(case / "metadata.json").get("scenario"))}
    ]
    if not selected:
        raise FileNotFoundError(f"no case matching {case_name!r} under {run_dir}")
    return selected


def assert_run(run_dir: Path, *, case_name: str | None) -> int:
    run_dir = run_dir.expanduser().resolve()
    failures = 0
    for case_dir in _selected_cases(run_dir, case_name):
        metadata = load_json(case_dir / "metadata.json")
        session = load_json(final_session_path(case_dir))
        results = evaluate_case(case_dir, metadata, session)
        write_json(
            case_dir / "assertions.json",
            [result.__dict__ for result in results],
        )
        case_dir.joinpath("assertions.md").write_text(
            assertions_markdown(results),
            encoding="utf-8",
        )
        case_failures = [result for result in results if result.status == "FAIL"]
        failures += len(case_failures)
        print(
            f"{metadata.get('scenario')} / {metadata.get('model')}: "
            f"{len(results) - len(case_failures)} passed or manual, "
            f"{len(case_failures)} failed"
        )
        for result in case_failures:
            print(f"  FAIL: {result.name}: {result.detail}")
    return 1 if failures else 0


def _print_review_next(run_dir: Path) -> None:
    print(
        "Next:\n"
        f"  python test/task_guidance/task_guidance_eval.py review "
        f"--run-dir {run_dir}"
    )


def assert_command(args: argparse.Namespace) -> int:
    status = assert_run(args.run_dir, case_name=args.case)
    if args.review:
        review_args = argparse.Namespace(
            run_dir=args.run_dir,
            case=args.case,
            model=args.review_model or _default_ollama_model(),
            ollama_base_url=args.ollama_base_url,
            bundle=False,
        )
        review_status = review_command(review_args)
        return status or review_status
    _print_review_next(args.run_dir.expanduser().resolve())
    return status


def _review_prompt(
    *,
    case_dir: Path,
    metadata: Mapping[str, Any],
) -> str:
    task_text = (
        case_dir.joinpath("task-file.md").read_text(encoding="utf-8")
        if case_dir.joinpath("task-file.md").is_file()
        else "(No task-file artifact.)"
    )
    session = load_json(final_session_path(case_dir))
    response = assistant_text_after_last_user(Session.from_dict(session))
    assertions = (
        case_dir.joinpath("assertions.md").read_text(encoding="utf-8")
        if case_dir.joinpath("assertions.md").is_file()
        else "(Mechanical assertions have not been run.)"
    )
    requirements = PREMADE_TASK_TEMPLATE.read_text(encoding="utf-8")
    return f"""\
Review this task-guidance evaluation artifact for instruction clarity and
compliance only. This is an empirical review for a human; do not modify files
and do not treat your judgment as an automated test result.

Scenario: {metadata.get("scenario")}
Model under review: {metadata.get("model")}

Evaluate only understanding of the task-file instructions:
- whether requirements are outcomes or constraints rather than execution tasks;
- whether supporting details explain requirements without becoming hidden
  requirements or relabeled execution steps;
- whether the requested retain-plan or omit-plan handoff is followed in
  substance, not only by heading names;
- whether requirement verification states the requirement or group, evidence
  type, and test boundary without overwhelming the user with internal tests;
- whether documentation is presented separately with its audience and intended
  use, or explicitly declared unnecessary;
- whether the user-facing response is self-contained and easier to review than
  the full stored plan.

Do not judge whether repository findings are correct, whether the implementation
approach is good, whether tests are technically sufficient, whether the plan
actually satisfies the requirements, or whether the model identified the best
design decisions. Record such observations separately as outside this review
and do not use them in the overall guidance-compliance judgment.

Return Markdown with: Overall guidance compliance, Requirements versus tasks,
Supporting details versus plan, Verification and documentation presentation,
Guidance ambiguities, Model reasoning issues outside this review, and Human
follow-up.

Reference task fixture:

{requirements}

Generated task:

{task_text}

Final assistant response:

{response}

Mechanical assertions:

{assertions}
"""


def _ollama_review(
    *,
    base_url: str,
    model: str,
    prompt: str,
) -> tuple[str, Mapping[str, Any]]:
    payload = {
        "model": model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "You are reviewing an agent task handoff for a human "
                    "developer. Be precise, evidence-based, and concise."
                ),
            },
            {"role": "user", "content": prompt},
        ],
        "stream": False,
        "temperature": 0,
    }
    response = requests.post(
        f"{base_url.rstrip('/')}/chat/completions",
        json=payload,
        timeout=600,
    )
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("Ollama review response has no choices")
    message = choices[0].get("message")
    if not isinstance(message, Mapping):
        raise RuntimeError("Ollama review response has no message")
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise RuntimeError("Ollama review response has no text content")
    return content, data


def review_command(args: argparse.Namespace) -> int:
    run_dir = args.run_dir.expanduser().resolve()
    for case_dir in _selected_cases(run_dir, args.case):
        metadata = load_json(case_dir / "metadata.json")
        if metadata.get("scenario") == "planning-seed":
            continue
        prompt = _review_prompt(case_dir=case_dir, metadata=metadata)
        content, response = _ollama_review(
            base_url=args.ollama_base_url,
            model=args.model,
            prompt=prompt,
        )
        case_dir.joinpath("empirical-review-prompt.md").write_text(
            prompt.rstrip() + "\n",
            encoding="utf-8",
        )
        case_dir.joinpath("empirical-review.md").write_text(
            content.rstrip() + "\n",
            encoding="utf-8",
        )
        write_json(case_dir / "empirical-review-response.json", response)
        print(
            f"Empirical review: {case_dir / 'empirical-review.md'}"
        )
    if args.bundle:
        return bundle_run(run_dir, force=True)
    print(
        "Next:\n"
        f"  python test/task_guidance/task_guidance_eval.py bundle "
        f"--run-dir {run_dir}"
    )
    return 0


def bundle_run(run_dir: Path, *, force: bool) -> int:
    run_dir = run_dir.expanduser().resolve()
    output = EVAL_ROOT / "review-bundles" / run_dir.name
    prepared = prepare_review_bundle(run_dir, output, force=force)
    print(f"Review bundle: {prepared}")
    print(f"Open: {prepared / 'README.md'}")
    return 0


def bundle_command(args: argparse.Namespace) -> int:
    return bundle_run(args.run_dir, force=args.force)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run, assert, empirically review, and bundle task-guidance "
            "evaluation scenarios."
        ),
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run = subparsers.add_parser(
        "run",
        help="Run selected model steps and save artifacts.",
        description="Run selected task-guidance model steps and save artifacts.",
        epilog=EXAMPLES,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    run.add_argument(
        "--steps",
        type=_csv_steps,
        required=True,
        help=f"Comma-separated steps: {', '.join(RUN_STEPS)}.",
    )
    run.add_argument("--provider", choices=("ollama", "chatgpt"), default="ollama")
    run.add_argument("--agent", help="Agent id from the copied default config.")
    run.add_argument("--model", help="Model override.")
    run.add_argument(
        "--credentials-dir",
        type=Path,
        default=Path.home() / ".crystal",
        help="ChatGPT account state directory; defaults to ~/.crystal.",
    )
    run.add_argument(
        "--ollama-base-url",
        default=DEFAULT_OLLAMA_BASE_URL,
        help="Ollama OpenAI-compatible base URL.",
    )
    run.add_argument(
        "--guidance",
        type=Path,
        default=DEFAULT_GUIDANCE_PATH,
        help="Task guidance file to compile into requests.",
    )
    run.add_argument("--run-id", help="Artifact run id; defaults to a timestamp.")
    run.add_argument(
        "--source-case",
        type=Path,
        help="Existing case containing session-1.json for fork-only runs.",
    )
    run.add_argument(
        "--assert",
        dest="run_assertions",
        action="store_true",
        help="Run mechanical assertions immediately after the model steps.",
    )
    run.set_defaults(func=run_command)

    assertion = subparsers.add_parser(
        "assert",
        help="Run deterministic assertions against saved artifacts.",
        epilog="""\
Example:
  python test/task_guidance/task_guidance_eval.py assert \\
    --run-dir tmp/task-guidance-eval/runs/<run-id>

Add --review to run the GLM empirical review afterward.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    assertion.add_argument("--run-dir", type=Path, required=True)
    assertion.add_argument("--case", help="Scenario or case directory name.")
    assertion.add_argument(
        "--review",
        action="store_true",
        help="Run the GLM empirical review after assertions finish.",
    )
    assertion.add_argument("--review-model", help="GLM review model override.")
    assertion.add_argument(
        "--ollama-base-url",
        default=DEFAULT_OLLAMA_BASE_URL,
    )
    assertion.set_defaults(func=assert_command)

    review = subparsers.add_parser(
        "review",
        help="Run a separate GLM empirical review for human inspection.",
        epilog="""\
Example:
  python test/task_guidance/task_guidance_eval.py review \\
    --run-dir tmp/task-guidance-eval/runs/<run-id>

Add --bundle to prepare the review bundle afterward.""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    review.add_argument("--run-dir", type=Path, required=True)
    review.add_argument("--case", help="Scenario or case directory name.")
    review.add_argument(
        "--model",
        default=_default_ollama_model(),
        help="GLM model used for empirical review.",
    )
    review.add_argument(
        "--ollama-base-url",
        default=DEFAULT_OLLAMA_BASE_URL,
    )
    review.add_argument(
        "--bundle",
        action="store_true",
        help="Prepare the review bundle after empirical review.",
    )
    review.set_defaults(func=review_command)

    bundle = subparsers.add_parser(
        "bundle",
        help="Prepare an easy-to-review artifact bundle.",
        epilog="""\
Example:
  python test/task_guidance/task_guidance_eval.py bundle \\
    --run-dir tmp/task-guidance-eval/runs/<run-id>""",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    bundle.add_argument("--run-dir", type=Path, required=True)
    bundle.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing bundle.",
    )
    bundle.set_defaults(func=bundle_command)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())