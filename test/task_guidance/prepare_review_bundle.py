from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import sys
import tempfile
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping


HERE = Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))

from harness import (  # noqa: E402
    ROOT,
    PREMADE_TASK_TEMPLATE,
    _evict_stale_attr_modules,
    _system_message_text,
    assert_approval_response,
    assert_draft_execution_plan,
    assert_no_execution_approval,
    assert_no_execution_plan,
    assert_no_lifecycle_notes,
    assert_task_prefix,
    chatgpt_credentials_path,
    compiled_system_message,
    describe_tool_call,
    requirements_section,
)


@dataclass(frozen=True)
class AssertionResult:
    name: str
    status: str
    detail: str


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def final_session_path(case_dir: Path) -> Path:
    candidates: list[tuple[int, Path]] = []
    for path in case_dir.glob("session-*.json"):
        match = re.fullmatch(r"session-(\d+)\.json", path.name)
        if match:
            candidates.append((int(match.group(1)), path))
    if not candidates:
        raise FileNotFoundError(f"no session-N.json artifact in {case_dir}")
    return max(candidates)[1]


def discover_case_dirs(run_dir: Path) -> list[Path]:
    cases: list[Path] = []
    for metadata_path in run_dir.rglob("metadata.json"):
        case_dir = metadata_path.parent
        try:
            metadata = load_json(metadata_path)
        except Exception:
            continue
        if not isinstance(metadata, dict):
            continue
        if not isinstance(metadata.get("scenario"), str):
            continue
        if not isinstance(metadata.get("model"), str):
            continue
        cases.append(case_dir)
    return sorted(cases)


def render_messages_markdown(
    session: Mapping[str, Any],
    metadata: Mapping[str, Any],
) -> str:
    raw_messages = session.get("messages")
    messages = raw_messages if isinstance(raw_messages, list) else []
    visible: list[tuple[int, Mapping[str, Any]]] = []
    tool_calls_by_index: dict[int, list[str]] = {}

    for index, raw_message in enumerate(messages):
        if not isinstance(raw_message, Mapping):
            continue
        role = raw_message.get("role")
        if role == "assistant":
            raw_metadata = raw_message.get("metadata")
            message_metadata = (
                raw_metadata if isinstance(raw_metadata, Mapping) else {}
            )
            calls = message_metadata.get("tool_calls")
            if isinstance(calls, list):
                names = [
                    str(describe_tool_call(call).get("tool_name") or "unknown")
                    for call in calls
                    if isinstance(call, Mapping)
                ]
                if names:
                    tool_calls_by_index[index] = names
        if role not in {"user", "assistant"}:
            continue
        content = raw_message.get("content")
        if isinstance(content, str) and content.strip():
            visible.append((index, raw_message))

    total_tool_calls = sum(len(names) for names in tool_calls_by_index.values())
    lines = [
        "# Exported conversation",
        "",
        f"- Scenario: `{metadata.get('scenario', 'unknown')}`",
        f"- Agent: `{metadata.get('agent_id', 'unknown')}`",
        f"- Model: `{metadata.get('model', 'unknown')}`",
        f"- Total tool calls: **{total_tool_calls}**",
        "",
        (
            "Tool-only assistant protocol entries and tool results are omitted; "
            "their calls are counted between the surrounding visible messages. "
            "The complete raw session is available as `session.json`."
        ),
        "",
    ]

    for position, (message_index, message) in enumerate(visible):
        next_index = (
            visible[position + 1][0]
            if position + 1 < len(visible)
            else len(messages)
        )
        interval_names: list[str] = []
        for index in range(message_index, next_index):
            interval_names.extend(tool_calls_by_index.get(index, []))

        role = str(message.get("role"))
        raw_metadata = message.get("metadata")
        message_metadata = (
            raw_metadata if isinstance(raw_metadata, Mapping) else {}
        )
        if role == "user":
            label = "User"
        elif message_metadata.get("phase") == "commentary" or interval_names:
            label = "Assistant commentary"
        else:
            label = "Assistant"

        lines.extend(
            [
                f"## {position + 1}. {label}",
                "",
                str(message.get("content") or "").rstrip(),
                "",
            ]
        )
        counts = Counter(interval_names)
        if counts:
            summary = ", ".join(
                f"`{name}` × {count}" for name, count in sorted(counts.items())
            )
            lines.append(
                f"Tool calls before the next exported message: "
                f"**{len(interval_names)}** ({summary})"
            )
        else:
            lines.append("Tool calls before the next exported message: **0**")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


def assistant_text_after_last_user(session: Mapping[str, Any]) -> str:
    raw_messages = session.get("messages")
    messages = raw_messages if isinstance(raw_messages, list) else []
    last_user_index = -1
    for index, message in enumerate(messages):
        if isinstance(message, Mapping) and message.get("role") == "user":
            last_user_index = index
    parts: list[str] = []
    for message in messages[last_user_index + 1 :]:
        if not isinstance(message, Mapping) or message.get("role") != "assistant":
            continue
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            parts.append(content)
    return "\n\n".join(parts)


def evaluate_case(
    case_dir: Path,
    metadata: Mapping[str, Any],
    session: Mapping[str, Any],
) -> list[AssertionResult]:
    results: list[AssertionResult] = []

    def check(name: str, action: Callable[[], Any]) -> None:
        try:
            action()
        except BaseException as exc:
            results.append(AssertionResult(name, "FAIL", f"{type(exc).__name__}: {exc}"))
        else:
            results.append(AssertionResult(name, "PASS", ""))

    def manual(name: str, detail: str) -> None:
        results.append(AssertionResult(name, "MANUAL", detail))

    check(
        "A complete final session artifact exists",
        lambda: bool(session.get("messages"))
        or (_ for _ in ()).throw(AssertionError("session-N.json is missing or empty")),
    )

    guidance_path = case_dir / "TASKS.md"
    if not guidance_path.is_file():
        guidance_path = case_dir / "config" / "TASKS_v6.md"

    def guidance_matches_metadata() -> None:
        expected = metadata.get("guidance_sha256")
        actual = hashlib.sha256(guidance_path.read_bytes()).hexdigest()
        if expected != actual:
            raise AssertionError(f"guidance hash {actual} != {expected}")

    check("The exact task-guidance version is present and hash-matched", guidance_matches_metadata)

    scenario = metadata.get("scenario")
    mutation_path = case_dir / "mutation-calls.json"

    def mutation_budget() -> None:
        calls = load_json(mutation_path)
        limit = int(metadata.get("mutation_call_limit") or 0)
        if not isinstance(calls, list):
            raise AssertionError("mutation-calls.json is not a list")
        if not calls and scenario != "planning-seed":
            raise AssertionError("no task-file mutation was recorded")
        if len(calls) > limit:
            raise AssertionError(f"{len(calls)} mutation calls exceeded limit {limit}")

    if mutation_path.is_file():
        check(
            "Task-file mutation calls stay within the configured limit",
            mutation_budget,
        )

    task_path = case_dir / "task-file.md"
    task_text = task_path.read_text(encoding="utf-8") if task_path.is_file() else ""
    if scenario != "planning-seed":
        check(
            "A reviewable final task-file artifact exists",
            lambda: task_path.is_file()
            or (_ for _ in ()).throw(AssertionError("task-file.md is missing")),
        )
    if task_text:
        check(
            "Task starts with title, description, and requirements",
            lambda: assert_task_prefix(task_text),
        )
    if scenario != "planning-seed" and (case_dir / "git-status.txt").is_file():

        def only_task_file_changed() -> None:
            status_path = case_dir / "git-status.txt"
            lines = [
                line
                for line in status_path.read_text(encoding="utf-8").splitlines()
                if line.strip()
            ]
            paths = []
            for line in lines:
                path = line[3:]
                if " -> " in path:
                    path = path.split(" -> ", 1)[1]
                paths.append(path)
            if len(paths) != 1 or not (
                paths[0].startswith("tasks/") and paths[0].endswith(".md")
            ):
                raise AssertionError(f"unexpected changed paths: {paths}")

        check("Only the requested task file changed", only_task_file_changed)
    elif scenario != "planning-seed":
        results.append(
            AssertionResult(
                "Only the requested task file changed",
                "UNAVAILABLE",
                "Older artifact does not contain git-status.txt.",
            )
        )

    response_text = assistant_text_after_last_user(session)
    expected_ids = [
        str(value)
        for value in metadata.get("expected_requirement_ids", [])
        if isinstance(value, str)
    ]
    research_markers = [
        str(value)
        for value in metadata.get("research_markers", [])
        if isinstance(value, str)
    ]

    def requirement_ids_present(source: str) -> None:
        missing = [value for value in expected_ids if value not in source]
        if missing:
            raise AssertionError(f"missing requirement ids: {missing}")

    def research_is_retained() -> None:
        if not research_markers:
            return
        found = [marker for marker in research_markers if marker in task_text]
        required = min(2, len(research_markers))
        if len(found) < required:
            raise AssertionError(
                f"found {len(found)} research markers, expected at least "
                f"{required}: {research_markers}"
            )

    def requirement_verification_text() -> str:
        match = re.search(
            r"(?ims)^###\s+Requirement verification\s*$"
            r"(?P<body>.*?)(?=^###\s+|^##\s+|\Z)",
            task_text,
        )
        if match is None:
            raise AssertionError("missing ### Requirement verification")
        return match.group("body")

    def fork_parent_matches() -> None:
        expected = metadata.get("fork_parent_session_sha256")
        parent_path = case_dir / "session-1.json"
        if not isinstance(expected, str) or not expected:
            raise AssertionError("fork parent hash is missing")
        payload = json.dumps(
            load_json(parent_path),
            sort_keys=True,
            separators=(",", ":"),
        ).encode("utf-8")
        actual = hashlib.sha256(payload).hexdigest()
        if actual != expected:
            raise AssertionError(f"fork parent hash {actual} != {expected}")

    if scenario == "planning-seed":
        first_status = case_dir / "git-status-1.txt"
        check(
            "The initial plan-only turn leaves the repository unchanged",
            lambda: not first_status.read_text(encoding="utf-8").strip()
            or (_ for _ in ()).throw(
                AssertionError(first_status.read_text(encoding="utf-8").strip())
            ),
        )
    elif scenario in {
        "create-task-retain-plan",
        "create-task-omit-plan",
    }:
        check("Fork uses the recorded planning session", fork_parent_matches)
        if task_text:
            check(
                "Expected high-level requirements are retained",
                lambda: requirement_ids_present(requirements_section(task_text)),
            )
            check("Factual research is retained", research_is_retained)
            check(
                "Planning-only task creation has no implementation/completion notes",
                lambda: assert_no_lifecycle_notes(task_text),
            )
        check(
            "Task creation does not infer plan or execution approval",
            lambda: assert_no_execution_approval(response_text),
        )

        if scenario == "create-task-retain-plan" and task_text:
            check(
                "Retained plan is a separate Draft execution plan",
                lambda: assert_draft_execution_plan(task_text),
            )
            check(
                "Requirement verification references every requirement id",
                lambda: requirement_ids_present(requirement_verification_text()),
            )
            manual(
                "Retained plan follows the requirements",
                (
                    "Confirm the plan satisfies each requirement without "
                    "broadening, narrowing, or reinterpreting it."
                ),
            )
        elif scenario == "create-task-omit-plan" and task_text:
            check(
                "Omit-plan handoff has no execution plan or plan status",
                lambda: assert_no_execution_plan(task_text),
            )

            def no_execution_task_checklist() -> None:
                if re.search(r"(?im)^###\s+Task checklist\s*$", task_text):
                    raise AssertionError(
                        "omit-plan handoff contains an execution task checklist"
                    )

            check(
                "Omit-plan handoff has no execution task checklist",
                no_execution_task_checklist,
            )
            manual(
                "Omit-plan handoff excludes plan content in substance",
                (
                    "Confirm proposed approach, ordered work, planned tests and "
                    "documentation were not relabeled under another heading."
                ),
            )
        manual(
            "Questions and decisions are classified correctly",
            (
                "Confirm requirement questions are not silently answered and "
                "material design decisions are exposed for human review."
            ),
        )
    elif scenario == "create-task-after-plan":
        if task_text:
            check(
                "Legacy task creation does not preserve a plan or plan status",
                lambda: assert_no_execution_plan(task_text),
            )
            check(
                "Planning-only task creation has no implementation/completion notes",
                lambda: assert_no_lifecycle_notes(task_text),
            )
        check(
            "Task creation does not infer plan or execution approval",
            lambda: assert_no_execution_approval(response_text),
        )

        first_status = case_dir / "git-status-1.txt"
        if first_status.is_file():
            check(
                "The initial plan-only turn leaves the repository unchanged",
                lambda: not first_status.read_text(encoding="utf-8").strip()
                or (_ for _ in ()).throw(
                    AssertionError(first_status.read_text(encoding="utf-8").strip())
                ),
            )
        else:
            results.append(
                AssertionResult(
                    "The initial plan-only turn leaves the repository unchanged",
                    "UNAVAILABLE",
                    "Older artifact does not contain git-status-1.txt.",
                )
            )
    elif scenario == "plan-existing-task":
        if task_text:
            original_requirements = requirements_section(
                PREMADE_TASK_TEMPLATE.read_text(encoding="utf-8")
            )
            check(
                "Existing requirements are preserved byte-for-byte",
                lambda: requirements_section(task_text) == original_requirements
                or (_ for _ in ()).throw(
                    AssertionError("requirements checklist changed")
                ),
            )
            check(
                "Draft execution plan has the required status and sections",
                lambda: assert_draft_execution_plan(task_text),
            )
            check(
                "Requirement verification references every requirement id",
                lambda: requirement_ids_present(requirement_verification_text()),
            )
        check(
            "Response requests approval before execution",
            lambda: assert_approval_response(response_text),
        )
        manual(
            "Questions and decisions are classified correctly",
            (
                "Confirm requirement questions are not silently answered and "
                "material design decisions are exposed with a recommendation "
                "and relevant tradeoffs."
            ),
        )
        manual(
            "Stored plan follows every requirement",
            (
                "Confirm the plan satisfies R1-R5 without broadening, narrowing, "
                "or reinterpreting them."
            ),
        )
    else:
        results.append(
            AssertionResult(
                "Scenario-specific assertions",
                "UNAVAILABLE",
                f"Unknown scenario: {scenario!r}",
            )
        )

    return results


def assertions_markdown(results: list[AssertionResult]) -> str:
    lines = [
        "# Assertions and review checks",
        "",
        "| Status | Check | Detail |",
        "|---|---|---|",
    ]
    for result in results:
        detail = result.detail.replace("|", "\\|").replace("\n", "<br>")
        name = result.name.replace("|", "\\|")
        lines.append(f"| {result.status} | {name} | {detail} |")
    return "\n".join(lines).rstrip() + "\n"


def extract_compiled_from_session(
    session: Mapping[str, Any],
) -> tuple[str, str] | None:
    raw_messages = session.get("messages")
    messages = raw_messages if isinstance(raw_messages, list) else []
    sections: list[tuple[str, str]] = []
    for message in messages:
        if not isinstance(message, Mapping):
            continue
        role = message.get("role")
        if role not in {"system", "developer"}:
            continue
        metadata = message.get("metadata")
        content = ""
        if isinstance(metadata, Mapping):
            compiled = metadata.get("compiled_content")
            if isinstance(compiled, str):
                content = compiled
        if not content:
            raw_content = message.get("content")
            if isinstance(raw_content, str):
                content = raw_content
        if content.strip():
            sections.append((str(role), content))
    if sections:
        if len(sections) == 1:
            return "session.messages compiled_content", sections[0][1]
        return (
            "session.messages compiled_content",
            "\n\n".join(
                f"## {role}\n\n{content.rstrip()}" for role, content in sections
            ),
        )

    session_metadata = session.get("metadata")
    native_messages = (
        session_metadata.get("native_messages")
        if isinstance(session_metadata, Mapping)
        else None
    )
    content = _system_message_text(
        native_messages,
        prefer_compiled_metadata=True,
    )
    if content:
        return "session.metadata.native_messages", content
    return None


def reconstruct_compiled_system_message(
    case_dir: Path,
    metadata: Mapping[str, Any],
) -> tuple[str, str]:
    app_python = ROOT / "application" / "python"
    core_python = ROOT / "core" / "python"
    for import_root in (ROOT, app_python, core_python):
        if str(import_root) not in sys.path:
            sys.path.insert(0, str(import_root))

    from agent_app.application_future import AgentApplication
    from agent_app.runtime_env import RuntimeEnvOverlay

    _evict_stale_attr_modules()
    workspace = case_dir / "workspace"
    config_dir = case_dir / "config"
    env = {
        "CONFIG_DIR": str(config_dir),
        "BUILTIN_PLUGINS": str((ROOT / "plugins").resolve()),
        "PLUGIN_CACHE_DIR": str(
            (ROOT / "tmp" / "task-guidance-eval" / "plugin-cache").resolve()
        ),
        "WORKING_DIR": str(workspace),
        "CLOUD_RUNTIME_BUILD_CONTEXT": str(case_dir / "cloud-runtime-context"),
        "OPENROUTER_API_KEY": "unused",
        "OPENAI_API_KEY": "unused",
        "GEMINI_API_KEY": "unused",
        "TAVILY_API_KEY": "unused",
        "FIREWORKS_API_KEY": "unused",
        "ZAI_API_KEY": "unused",
        "CLOUD_ORCHESTRATOR_URL": "http://cloud-orchestrator.invalid",
        "CLOUD_ORCHESTRATOR_TOKEN": "unused",
    }
    app: Any = None
    try:
        with tempfile.TemporaryDirectory() as session_root:
            app = AgentApplication(
                config_dir / "config.json",
                session_root,
                env_overrides=env,
            )
            agent_id = str(metadata["agent_id"])
            core, base_config, session = app.create_session_ephemeral(agent_id)
            prompt = case_dir.joinpath("prompt-1.md").read_text(encoding="utf-8")
            session = core.add_message(
                session,
                "user",
                prompt,
                metadata=None,
                config=base_config,
            )
            overrides: dict[str, Any] = {
                "model": str(metadata["model"]),
                "working_directory": str(workspace),
                "allowed_paths": [str(workspace)],
                "include_tasks": True,
                "skills_enabled": False,
                "mcp_enabled": False,
                "web_search_enabled": False,
                "timeout": 600,
                "max_output_chars": 20_000,
            }
            if metadata.get("auth_mode") == "chatgpt":
                overrides.update(
                    {
                        "auth_mode": "chatgpt",
                        "chatgpt_credentials_path": str(
                            chatgpt_credentials_path()
                        ),
                        "reasoning_effort": "medium",
                        "reasoning_summary": "detailed",
                    }
                )
            else:
                overrides["request_options"] = {"reasoning_effort": "max"}

            config = app.resolve_effective_config(
                base_config,
                session,
                overrides,
            )
            core.prepare_tools(config)
            provider, extensions, features, tools, tags = (
                core._resolve_plugins_for_config(config)
            )
            provider.set_active_extensions(extensions)
            prepared = core._pre_request(
                session,
                config,
                provider,
                features,
                tools,
                tags=tags,
                models=core._get_models_for_config(provider, config),
                context={},
            )
            captured = compiled_system_message(prepared[1], prepared[2])
            if captured is None:
                raise RuntimeError("request preparation produced no system message")
            source, content = captured
            return f"reconstructed from preserved artifacts via {source}", content
    finally:
        if app is not None:
            app.close()
        RuntimeEnvOverlay._reset_for_tests()


def compiled_system_for_case(
    case_dir: Path,
    metadata: Mapping[str, Any],
    session: Mapping[str, Any],
) -> tuple[str, str]:
    captured_path = case_dir / "compiled-system-message.md"
    if captured_path.is_file():
        return (
            "captured from the actual request-time provider state",
            captured_path.read_text(encoding="utf-8"),
        )
    extracted = extract_compiled_from_session(session)
    if extracted is not None:
        return extracted
    return reconstruct_compiled_system_message(case_dir, metadata)


def guidance_for_case(case_dir: Path) -> Path:
    direct = case_dir / "TASKS.md"
    if direct.is_file():
        return direct
    fallback = case_dir / "config" / "TASKS_v6.md"
    if fallback.is_file():
        return fallback
    raise FileNotFoundError(f"no task-guidance snapshot in {case_dir}")


def prepare_case_bundle(case_dir: Path, output_dir: Path) -> dict[str, Any]:
    metadata = load_json(case_dir / "metadata.json")
    try:
        session_path = final_session_path(case_dir)
    except FileNotFoundError:
        session_path = None
        session: Mapping[str, Any] = {"messages": [], "metadata": {}}
    else:
        session = load_json(session_path)
    output_dir.mkdir(parents=True)

    shutil.copy2(guidance_for_case(case_dir), output_dir / "TASKS.md")
    if session_path is not None:
        shutil.copy2(session_path, output_dir / "session.json")
    else:
        output_dir.joinpath("session-unavailable.md").write_text(
            "# Session unavailable\n\n"
            "This case directory was created, but no `session-N.json` artifact "
            "was completed.\n",
            encoding="utf-8",
        )
    shutil.copy2(case_dir / "metadata.json", output_dir / "metadata.json")

    output_dir.joinpath("messages.md").write_text(
        render_messages_markdown(session, metadata),
        encoding="utf-8",
    )

    try:
        provenance, compiled = compiled_system_for_case(case_dir, metadata, session)
    except BaseException as exc:
        provenance = (
            "unavailable because reconstruction failed: "
            f"{type(exc).__name__}: {exc}"
        )
        compiled = (
            "# Compiled system message unavailable\n\n"
            "The case did not retain a request-time prompt and reconstruction "
            "from its partial artifacts failed."
        )
    output_dir.joinpath("compiled-system-message.md").write_text(
        compiled.rstrip() + "\n",
        encoding="utf-8",
    )
    output_dir.joinpath("system-message-provenance.md").write_text(
        "# System-message provenance\n\n"
        f"{provenance.rstrip()}.\n",
        encoding="utf-8",
    )

    results = evaluate_case(case_dir, metadata, session)
    output_dir.joinpath("assertions.md").write_text(
        assertions_markdown(results),
        encoding="utf-8",
    )
    output_dir.joinpath("assertions.json").write_text(
        json.dumps(
            [result.__dict__ for result in results],
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )

    failure_path = case_dir / "failure.txt"
    raw_failure = (
        failure_path.read_text(encoding="utf-8").rstrip()
        if failure_path.is_file()
        else ""
    )
    output_dir.joinpath("failure.md").write_text(
        "# Raw run failure\n\n"
        + (
            f"```text\n{raw_failure}\n```\n"
            if raw_failure
            else "No raw run failure was captured for this case.\n"
        ),
        encoding="utf-8",
    )

    optional_files = (
        "task-file.md",
        "tool-calls.json",
        "mutation-calls.json",
        "git-diff.patch",
        "git-status.txt",
        "review.md",
        "review-template.md",
        "empirical-review.md",
        "empirical-review-prompt.md",
        "empirical-review-response.json",
        "shared-tool-calls.json",
        "branch-tool-calls.json",
        "source-case.txt",
    )
    for name in optional_files:
        source = case_dir / name
        if source.is_file():
            shutil.copy2(source, output_dir / name)

    counts = Counter(result.status for result in results)
    return {
        "scenario": metadata.get("scenario"),
        "model": metadata.get("model"),
        "agent_id": metadata.get("agent_id"),
        "relative_output": output_dir,
        "pass": counts.get("PASS", 0),
        "fail": counts.get("FAIL", 0),
        "manual": counts.get("MANUAL", 0),
        "unavailable": counts.get("UNAVAILABLE", 0),
        "raw_failure": bool(raw_failure),
    }


def prepare_review_bundle(
    run_dir: Path,
    output_dir: Path,
    *,
    force: bool = False,
) -> Path:
    run_dir = run_dir.resolve()
    output_dir = output_dir.resolve()
    cases = discover_case_dirs(run_dir)
    if not cases:
        raise FileNotFoundError(f"no task-guidance case artifacts under {run_dir}")
    if output_dir.exists():
        if not force:
            raise FileExistsError(
                f"output directory already exists; pass --force: {output_dir}"
            )
        shutil.rmtree(output_dir)
    output_dir.mkdir(parents=True)

    root_guidance = run_dir / "TASKS.md"
    if root_guidance.is_file():
        shutil.copy2(root_guidance, output_dir / "TASKS.md")
    else:
        shutil.copy2(guidance_for_case(cases[0]), output_dir / "TASKS.md")

    summaries: list[dict[str, Any]] = []
    for case_dir in cases:
        metadata = load_json(case_dir / "metadata.json")
        scenario = str(metadata["scenario"])
        model_id = case_dir.name
        case_output = output_dir / "cases" / scenario / model_id
        summaries.append(prepare_case_bundle(case_dir, case_output))

    guidance_hash = hashlib.sha256(
        output_dir.joinpath("TASKS.md").read_bytes()
    ).hexdigest()
    lines = [
        "# Task-guidance evaluation review bundle",
        "",
        f"- Source run: `{run_dir}`",
        f"- Guidance SHA-256: `{guidance_hash}`",
        f"- Cases: **{len(summaries)}**",
        "",
        "| Scenario | Agent/model | Mechanical results | Raw run failure |",
        "|---|---|---|---|",
    ]
    for summary in summaries:
        relative = Path(summary["relative_output"]).relative_to(output_dir)
        result_text = (
            f"{summary['pass']} pass, {summary['fail']} fail, "
            f"{summary['manual']} manual, {summary['unavailable']} unavailable"
        )
        lines.append(
            f"| [{summary['scenario']}]({relative.as_posix()}/) "
            f"| `{summary['agent_id']}` / `{summary['model']}` "
            f"| {result_text} "
            f"| {'yes' if summary['raw_failure'] else 'no'} |"
        )
    lines.extend(
        [
            "",
            "Each case contains:",
            "",
            "- `messages.md`: all visible user, assistant commentary, and final "
            "assistant messages with intervening tool-call counts.",
            "- `TASKS.md`: the exact guidance version used by the case.",
            "- `compiled-system-message.md`: the complete compiled system or "
            "developer message.",
            "- `assertions.md` and `assertions.json`: mechanical and manual review "
            "checks.",
            "- `failure.md`: the raw run failure, when one was captured.",
            "- `task-file.md`, `session.json`, tool telemetry, and Git artifacts "
            "when available.",
            "",
        ]
    )
    output_dir.joinpath("README.md").write_text(
        "\n".join(lines),
        encoding="utf-8",
    )
    return output_dir


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Prepare an easy-to-review task-guidance evaluation bundle."
    )
    parser.add_argument(
        "run_dir",
        type=Path,
        help="Artifact run directory under tmp/task-guidance-eval/runs/.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        help=(
            "Destination directory. Defaults to "
            "tmp/task-guidance-eval/review-bundles/<run-id>."
        ),
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Replace an existing output directory.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    run_dir = args.run_dir.resolve()
    output = args.output
    if output is None:
        output = (
            ROOT
            / "tmp"
            / "task-guidance-eval"
            / "review-bundles"
            / run_dir.name
        )
    prepared = prepare_review_bundle(run_dir, output, force=args.force)
    print(prepared)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())