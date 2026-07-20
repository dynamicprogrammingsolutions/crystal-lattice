from __future__ import annotations

import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from types import SimpleNamespace
from typing import Any, Iterable, Iterator, Mapping


ROOT = Path(__file__).resolve().parents[2]
APP_PY = ROOT / "application" / "python"
CORE_PY = ROOT / "core" / "python"
for import_root in (ROOT, APP_PY, CORE_PY):
    if str(import_root) not in sys.path:
        sys.path.insert(0, str(import_root))

from agent_app.application_future import AgentApplication  # noqa: E402
from agent_app.events import InMemoryEventStore  # noqa: E402
from agent_core import Session  # noqa: E402
from agent_core.tool_interop import DEFAULT_TOOL_INTEROP_REGISTRY  # noqa: E402


DEFAULT_CONFIG_DIR = (
    ROOT / "application" / "python" / "agent_terminal_app" / "default_config"
)
DEFAULT_GUIDANCE_PATH = ROOT / "agents" / "TASKS-v7.md"
FIXTURE_DIR = (
    ROOT / "test" / "fixture" / "task-guidance" / "codex-mdm-deny-read"
)
PREMADE_TASK_TEMPLATE = FIXTURE_DIR / "premade-task.md"
REVIEW_TEMPLATE = FIXTURE_DIR / "review-template.md"

CODEX_REPOSITORY = "https://github.com/openai/codex.git"
CODEX_COMMIT = "9f42c89c0112771dc29100a6f3fc904049b2655f"
EVAL_ROOT = ROOT / "tmp" / "task-guidance-eval"
SHARED_PLUGIN_CACHE = EVAL_ROOT / "plugin-cache"

DEFAULT_CHATGPT_MODEL = "gpt-5.6-luna"
DEFAULT_OLLAMA_AGENT = "glm-ollama"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"
DEFAULT_MUTATION_CALL_LIMIT = 3
DEFAULT_TOOL_LOOP_LIMIT = 60

TASK_PROMPT = """\
Please inspect this repository and outline a plan to fix this behavior:

On macOS, requirements delivered through the managed-preferences
`requirements_toml_base64` path do not resolve home-relative entries such as
`~/.ssh` in `permissions.filesystem.deny_read`, while equivalent
filesystem-delivered requirements do. The two delivery paths should produce
consistent resolved deny-read paths without regressing existing absolute-path,
relative-path, glob, or malformed-input behavior.

Plan only, do not implement.
"""

CREATE_TASK_PROMPT = "OK, create a single task file."


@dataclass(frozen=True)
class ModelCase:
    case_id: str
    agent_id: str
    model: str
    auth_mode: str


@dataclass(frozen=True)
class PreparedCase:
    scenario: str
    model_case: ModelCase
    run_id: str
    case_dir: Path
    workspace: Path
    config_dir: Path
    config_path: Path
    session_root: Path
    guidance_path: Path
    base_commit: str
    premade_task_path: Path | None = None


@dataclass
class MutationBudget:
    limit: int
    calls: list[dict[str, Any]] = field(default_factory=list)
    _core_class: type[Any] | None = field(default=None, init=False, repr=False)
    _original: Any = field(default=None, init=False, repr=False)
    _wrapper: Any = field(default=None, init=False, repr=False)

    def install(self, core: Any) -> None:
        core_class = type(core)
        original = core_class.iter_tool_messages

        def limited_iter_tool_messages(
            core_instance: Any,
            tool_calls: list[dict[str, Any]],
            config: dict[str, Any],
            *args: Any,
            **kwargs: Any,
        ) -> Iterator[dict[str, Any]]:
            for call in tool_calls:
                descriptor = describe_tool_call(call)
                if descriptor["is_mutation"]:
                    self.calls.append(descriptor)
                    if len(self.calls) > self.limit:
                        raise RuntimeError(
                            "Task guidance mutation-call limit exceeded: "
                            f"{len(self.calls)} > {self.limit}"
                        )
            yield from original(
                core_instance,
                tool_calls,
                config,
                *args,
                **kwargs,
            )

        self._core_class = core_class
        self._original = original
        self._wrapper = limited_iter_tool_messages
        core_class.iter_tool_messages = limited_iter_tool_messages

    def uninstall(self) -> None:
        if (
            self._core_class is not None
            and self._original is not None
            and self._core_class.iter_tool_messages is self._wrapper
        ):
            self._core_class.iter_tool_messages = self._original
        self._core_class = None
        self._original = None
        self._wrapper = None


@dataclass(frozen=True)
class RunningAgent:
    app: AgentApplication
    core: Any
    base_config: dict[str, Any]
    session: Session
    mutation_budget: MutationBudget


@dataclass(frozen=True)
class TurnResult:
    session: Session
    response: str
    events: list[dict[str, Any]]


def current_run_id() -> str:
    configured = os.getenv("TASK_GUIDANCE_RUN_ID")
    if configured and configured.strip():
        return configured.strip()
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")


def guidance_path() -> Path:
    configured = os.getenv("TASK_GUIDANCE_FILE")
    path = Path(configured).expanduser() if configured else DEFAULT_GUIDANCE_PATH
    path = path if path.is_absolute() else ROOT / path
    if not path.is_file():
        raise AssertionError(f"task guidance file does not exist: {path}")
    return path.resolve()


def chatgpt_state_dir() -> Path:
    configured = os.getenv("CHATGPT_TEST_STATE_DIR")
    if configured and configured.strip():
        return Path(configured).expanduser().resolve()
    return (Path.home() / ".crystal").resolve()


def chatgpt_credentials_path() -> Path:
    return chatgpt_state_dir() / "auth" / "chatgpt-auth.json"


def model_cases() -> list[ModelCase]:
    return [
        ModelCase(
            case_id="chatgpt-gpt-5.6-luna",
            agent_id="codex-openai",
            model=os.getenv("TASK_GUIDANCE_CHATGPT_MODEL")
            or DEFAULT_CHATGPT_MODEL,
            auth_mode="chatgpt",
        ),
        ModelCase(
            case_id="ollama-glm-5.2",
            agent_id=DEFAULT_OLLAMA_AGENT,
            model=os.getenv("TASK_GUIDANCE_OLLAMA_MODEL") or "",
            auth_mode="ollama",
        ),
    ]


def mutation_call_limit() -> int:
    return int(
        os.getenv("TASK_GUIDANCE_MUTATION_CALL_LIMIT")
        or DEFAULT_MUTATION_CALL_LIMIT
    )


def tool_loop_limit() -> int:
    return int(os.getenv("TASK_GUIDANCE_TOOL_LOOP_LIMIT") or DEFAULT_TOOL_LOOP_LIMIT)


def ensure_codex_cache() -> Path:
    cache_root = EVAL_ROOT / "repo-cache"
    cache_root.mkdir(parents=True, exist_ok=True)
    checkout = cache_root / "codex"
    if not (checkout / ".git").is_dir():
        _run(
            [
                "git",
                "clone",
                "--filter=blob:none",
                "--no-checkout",
                CODEX_REPOSITORY,
                str(checkout),
            ],
            cwd=ROOT,
            timeout=600,
        )
    _run(
        ["git", "fetch", "--depth=1", "origin", CODEX_COMMIT],
        cwd=checkout,
        timeout=600,
    )
    return checkout


def prepare_case(
    *,
    scenario: str,
    model_case: ModelCase,
    run_id: str,
    with_premade_task: bool,
) -> PreparedCase:
    case_dir = EVAL_ROOT / "runs" / run_id / scenario / model_case.case_id
    if case_dir.exists():
        raise AssertionError(
            f"case artifact directory already exists; choose another run id: {case_dir}"
        )
    case_dir.mkdir(parents=True)

    cache = ensure_codex_cache()
    workspace = case_dir / "workspace"
    _run(
        ["git", "worktree", "add", "--detach", str(workspace), CODEX_COMMIT],
        cwd=cache,
        timeout=600,
    )
    checked_out = _git(workspace, "rev-parse", "HEAD").strip()
    if checked_out != CODEX_COMMIT:
        raise AssertionError(f"unexpected checkout: {checked_out}")

    selected_guidance = guidance_path()
    config_dir = case_dir / "config"
    shutil.copytree(
        DEFAULT_CONFIG_DIR,
        config_dir,
        ignore=shutil.ignore_patterns(".plugin_cache", "auth", "__pycache__"),
    )
    shutil.copy2(selected_guidance, config_dir / "TASKS_v6.md")

    session_root = case_dir / "sessions"
    session_root.mkdir()
    config_path = config_dir / "config.json"
    _configure_case(
        config_path=config_path,
        config_dir=config_dir,
        workspace=workspace,
        model_case=model_case,
    )

    premade_task_path = None
    base_commit = CODEX_COMMIT
    if with_premade_task:
        date_prefix = datetime.now().strftime("%Y%m%d")
        premade_task_path = (
            workspace
            / "tasks"
            / f"{date_prefix}-mdm-deny-read-home-path-resolution.md"
        )
        premade_task_path.parent.mkdir(parents=True)
        shutil.copy2(PREMADE_TASK_TEMPLATE, premade_task_path)
        _run(["git", "add", str(premade_task_path.relative_to(workspace))], cwd=workspace)
        _run(
            [
                "git",
                "-c",
                "user.name=Task Guidance Evaluation",
                "-c",
                "user.email=task-guidance@example.invalid",
                "commit",
                "-m",
                "Add task guidance evaluation fixture",
            ],
            cwd=workspace,
        )
        base_commit = _git(workspace, "rev-parse", "HEAD").strip()
        parent = _git(workspace, "rev-parse", "HEAD^").strip()
        if parent != CODEX_COMMIT:
            raise AssertionError(f"fixture commit has unexpected parent: {parent}")

    shutil.copy2(REVIEW_TEMPLATE, case_dir / "review-template.md")
    prepared = PreparedCase(
        scenario=scenario,
        model_case=model_case,
        run_id=run_id,
        case_dir=case_dir,
        workspace=workspace,
        config_dir=config_dir,
        config_path=config_path,
        session_root=session_root,
        guidance_path=selected_guidance,
        base_commit=base_commit,
        premade_task_path=premade_task_path,
    )
    write_json(
        case_dir / "metadata.json",
        {
            "scenario": scenario,
            "agent_id": model_case.agent_id,
            "model": resolved_model(prepared),
            "auth_mode": model_case.auth_mode,
            "repository": CODEX_REPOSITORY,
            "repository_commit": CODEX_COMMIT,
            "case_base_commit": base_commit,
            "guidance_path": str(selected_guidance),
            "guidance_sha256": _sha256(selected_guidance),
            "mutation_call_limit": mutation_call_limit(),
            "tool_loop_limit": tool_loop_limit(),
        },
    )
    return prepared


def resolved_model(prepared: PreparedCase) -> str:
    if prepared.model_case.model:
        return prepared.model_case.model
    config = json.loads(prepared.config_path.read_text(encoding="utf-8"))
    return str(config["agents"][prepared.model_case.agent_id]["model"])


def environment_for_case(prepared: PreparedCase) -> dict[str, str]:
    return {
        "CONFIG_DIR": str(prepared.config_dir),
        "BUILTIN_PLUGINS": str((ROOT / "plugins").resolve()),
        "PLUGIN_CACHE_DIR": str(SHARED_PLUGIN_CACHE),
        "WORKING_DIR": str(prepared.workspace),
        "CLOUD_RUNTIME_BUILD_CONTEXT": str(
            prepared.case_dir / "cloud-runtime-context"
        ),
        "OPENROUTER_API_KEY": os.getenv("OPENROUTER_API_KEY", "unused"),
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY", "unused"),
        "GEMINI_API_KEY": os.getenv("GEMINI_API_KEY", "unused"),
        "TAVILY_API_KEY": os.getenv("TAVILY_API_KEY", "unused"),
        "FIREWORKS_API_KEY": os.getenv("FIREWORKS_API_KEY", "unused"),
        "ZAI_API_KEY": os.getenv("ZAI_API_KEY", "unused"),
        "CLOUD_ORCHESTRATOR_URL": os.getenv(
            "CLOUD_ORCHESTRATOR_URL", "http://cloud-orchestrator.invalid"
        ),
        "CLOUD_ORCHESTRATOR_TOKEN": os.getenv(
            "CLOUD_ORCHESTRATOR_TOKEN", "unused"
        ),
    }


def start_agent(prepared: PreparedCase) -> RunningAgent:
    _evict_stale_attr_modules()
    app = AgentApplication(
        str(prepared.config_path),
        str(prepared.session_root),
        event_store=InMemoryEventStore(),
    )
    errors = app.get_config_errors()
    if errors:
        raise AssertionError(f"default config failed to load: {errors}")
    app._tool_loop_cfg = SimpleNamespace(max_loops=tool_loop_limit())

    core, base_config, session = app.create_session(prepared.model_case.agent_id)
    actual_model = base_config.get("model")
    expected_model = resolved_model(prepared)
    if actual_model != expected_model:
        raise AssertionError(
            f"unexpected model for {prepared.model_case.agent_id}: "
            f"{actual_model!r} != {expected_model!r}"
        )
    if base_config.get("include_tasks") is not True:
        raise AssertionError("task guidance is not enabled in the effective config")

    budget = MutationBudget(limit=mutation_call_limit())
    budget.install(core)
    return RunningAgent(
        app=app,
        core=core,
        base_config=base_config,
        session=session,
        mutation_budget=budget,
    )


def send_turn(
    running: RunningAgent,
    prepared: PreparedCase,
    *,
    prompt: str,
    session: Session | None = None,
) -> TurnResult:
    current = session or running.session
    current = running.core.add_message(
        current,
        "user",
        prompt,
        metadata=None,
        config=running.base_config,
    )
    current = running.app.save_session(current)

    overrides: dict[str, Any] = {
        "model": resolved_model(prepared),
        "working_directory": str(prepared.workspace),
        "allowed_paths": [str(prepared.workspace)],
        "include_tasks": True,
        "skills_enabled": False,
        "mcp_enabled": False,
        "web_search_enabled": False,
        "timeout": 600,
        "max_output_chars": 20_000,
    }
    if prepared.model_case.auth_mode == "chatgpt":
        overrides.update(
            {
                "auth_mode": "chatgpt",
                "chatgpt_credentials_path": str(chatgpt_credentials_path()),
                "reasoning_effort": "medium",
                "reasoning_summary": "detailed",
            }
        )
    else:
        overrides["request_options"] = {"reasoning_effort": "max"}

    events = list(
        running.app.send_request(
            running.core,
            current,
            running.base_config,
            overrides=overrides,
            stream=True,
        )
    )
    failures = [
        event
        for event in events
        if event.get("type") in {"error", "request_cancelled"}
    ]
    if failures:
        raise AssertionError(f"agent request failed: {failures[-1]}")
    checkpoints = [
        event for event in events if event.get("type") == "session_checkpoint"
    ]
    if not checkpoints:
        raise AssertionError("expected a session checkpoint")
    final_session = checkpoints[-1].get("session")
    if not isinstance(final_session, Session):
        raise AssertionError("session checkpoint did not contain a Session")
    response = last_assistant_response(final_session)
    return TurnResult(session=final_session, response=response, events=events)


def last_assistant_response(session: Session) -> str:
    for message in reversed(session.messages):
        if message.role != "assistant":
            continue
        metadata = message.metadata if isinstance(message.metadata, dict) else {}
        if metadata.get("tool_calls"):
            continue
        if isinstance(message.content, str):
            return message.content
    raise AssertionError("expected a final assistant response")


def write_turn_artifacts(
    prepared: PreparedCase,
    *,
    turn_number: int,
    prompt: str,
    result: TurnResult,
    mutation_budget: MutationBudget,
) -> None:
    prepared.case_dir.joinpath(f"prompt-{turn_number}.md").write_text(
        prompt.rstrip() + "\n",
        encoding="utf-8",
    )
    prepared.case_dir.joinpath(f"response-{turn_number}.md").write_text(
        result.response.rstrip() + "\n",
        encoding="utf-8",
    )
    write_json(
        prepared.case_dir / f"events-{turn_number}.json",
        jsonable(result.events),
    )
    write_json(
        prepared.case_dir / f"session-{turn_number}.json",
        result.session.to_dict(),
    )
    write_json(
        prepared.case_dir / "tool-calls.json",
        collect_tool_calls(result.session),
    )
    write_json(
        prepared.case_dir / "mutation-calls.json",
        mutation_budget.calls,
    )
    write_git_artifacts(prepared, turn_number=turn_number)


def write_final_task_artifact(prepared: PreparedCase, task_path: Path) -> None:
    relative = task_path.relative_to(prepared.workspace)
    target = prepared.case_dir / "task-file.md"
    target.write_text(task_path.read_text(encoding="utf-8"), encoding="utf-8")
    write_json(
        prepared.case_dir / "task-file.json",
        {"relative_path": relative.as_posix()},
    )


def write_git_artifacts(
    prepared: PreparedCase,
    *,
    turn_number: int | None = None,
) -> None:
    status = git_status(prepared.workspace)
    suffix = f"-{turn_number}" if turn_number is not None else ""
    prepared.case_dir.joinpath("git-status.txt").write_text(
        "\n".join(status) + ("\n" if status else ""),
        encoding="utf-8",
    )
    prepared.case_dir.joinpath(f"git-status{suffix}.txt").write_text(
        "\n".join(status) + ("\n" if status else ""),
        encoding="utf-8",
    )
    diff = _git(prepared.workspace, "diff", "--binary", prepared.base_commit)
    prepared.case_dir.joinpath("git-diff.patch").write_text(diff, encoding="utf-8")
    prepared.case_dir.joinpath(f"git-diff{suffix}.patch").write_text(
        diff,
        encoding="utf-8",
    )


def git_status(workspace: Path) -> list[str]:
    output = _git(
        workspace,
        "status",
        "--porcelain=v1",
        "--untracked-files=all",
    )
    return [line for line in output.splitlines() if line]


def changed_paths(workspace: Path) -> list[str]:
    paths: list[str] = []
    for line in git_status(workspace):
        raw = line[3:]
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        paths.append(raw)
    return paths


def assert_only_changed_paths(workspace: Path, expected: Iterable[str]) -> None:
    actual = sorted(changed_paths(workspace))
    wanted = sorted(expected)
    if actual != wanted:
        raise AssertionError(f"unexpected changed paths: {actual!r} != {wanted!r}")


def find_single_created_task(workspace: Path) -> Path:
    candidates = [
        path
        for path in changed_paths(workspace)
        if path.startswith("tasks/") and path.endswith(".md")
    ]
    if len(candidates) != 1:
        raise AssertionError(f"expected one created task file, found {candidates}")
    relative = PurePosixPath(candidates[0])
    if len(relative.parts) != 2:
        raise AssertionError(f"expected a single top-level task file: {relative}")
    if not re.fullmatch(r"\d{8}-[a-z0-9]+(?:-[a-z0-9]+)*\.md", relative.name):
        raise AssertionError(f"unexpected task filename: {relative.name}")
    return workspace / Path(*relative.parts)


def assert_task_prefix(text: str) -> None:
    lines = text.splitlines()
    nonempty = [index for index, line in enumerate(lines) if line.strip()]
    if not nonempty or not lines[nonempty[0]].startswith("# "):
        raise AssertionError("task must begin with a title")
    try:
        requirements_index = lines.index("## Requirements checklist")
    except ValueError as exc:
        raise AssertionError("task is missing ## Requirements checklist") from exc
    earlier_h2 = [
        index
        for index, line in enumerate(lines[:requirements_index])
        if line.startswith("## ")
    ]
    if earlier_h2:
        raise AssertionError("requirements checklist must be the first H2 section")
    description = "\n".join(lines[nonempty[0] + 1 : requirements_index]).strip()
    if not description:
        raise AssertionError("task is missing its short description")
    if re.search(r"(?m)^Status:", description):
        raise AssertionError(
            "status metadata appeared before the requirements checklist"
        )
    requirements = requirements_section(text)
    if "- [ ]" not in requirements and "- [x]" not in requirements:
        raise AssertionError("requirements checklist has no checkbox items")


def requirements_section(text: str) -> str:
    marker = "## Requirements checklist"
    start = text.find(marker)
    if start < 0:
        raise AssertionError(f"missing {marker}")
    following = text.find("\n## ", start + len(marker))
    end = len(text) if following < 0 else following
    return text[start:end].strip()


def assert_no_execution_plan(text: str) -> None:
    if re.search(
        r"(?im)^##\s+(?:(?:execution|implementation)\s+plan|plan(?:\s*\([^)]*\))?)\s*$",
        text,
    ):
        raise AssertionError(
            "default task creation unexpectedly included an execution plan"
        )


def assert_draft_execution_plan(text: str) -> None:
    match = re.search(r"(?im)^##\s+execution\s+plan\s*$", text)
    if match is None:
        raise AssertionError("missing ## Execution plan")
    plan = text[match.start() :]
    if not re.search(r"(?m)^Status:\s*Draft\s*$", plan):
        raise AssertionError("execution plan is not marked Draft")
    for heading in (
        "### Requirement verification",
        "### Documentation",
        "### Task checklist",
    ):
        if heading not in plan:
            raise AssertionError(f"execution plan is missing {heading}")
    task_checklist = plan[plan.index("### Task checklist") :]
    if "- [ ]" not in task_checklist:
        raise AssertionError("task checklist has no incomplete execution tasks")
    if re.search(
        r"(?im)^#{2,6}\s+(?:implementation|completion)\s+notes\b",
        plan,
    ):
        raise AssertionError("planning-only response added implementation/completion notes")


def assert_approval_response(response: str) -> None:
    lower = response.lower()
    if "approv" not in lower:
        raise AssertionError("response does not request or mention approval")
    if not any(word in lower for word in ("begin", "start", "execute", "execution")):
        raise AssertionError(
            "response does not connect approval to beginning execution"
        )


def collect_tool_calls(session: Session) -> list[dict[str, Any]]:
    collected: list[dict[str, Any]] = []
    for index, message in enumerate(session.messages):
        metadata = message.metadata if isinstance(message.metadata, dict) else {}
        raw_calls = metadata.get("tool_calls")
        if not isinstance(raw_calls, list):
            continue
        for call in raw_calls:
            if not isinstance(call, dict):
                continue
            collected.append(
                {
                    "message_index": index,
                    **describe_tool_call(call),
                    "raw": jsonable(call),
                }
            )
    return collected


def describe_tool_call(call: Mapping[str, Any]) -> dict[str, Any]:
    try:
        inspected = DEFAULT_TOOL_INTEROP_REGISTRY.inspect_call(dict(call))
        name = inspected.tool_name or ""
        payload = inspected.payload
    except Exception:
        function = call.get("function")
        function = function if isinstance(function, Mapping) else {}
        name = str(call.get("name") or function.get("name") or "")
        payload = call.get("input") or function.get("arguments") or call.get("arguments")

    payload_text = json.dumps(jsonable(payload), sort_keys=True)
    normalized_name = name.lower()
    direct_mutations = {
        "apply_patch",
        "edit",
        "write",
        "edit_file",
        "write_file",
        "mcp__filesystem__edit_file",
        "mcp__filesystem__write_file",
    }
    shell_apply_patch = normalized_name in {"shell", "shell_command", "bash"} and (
        "apply_patch" in payload_text
    )
    mutation_kind = ""
    if normalized_name in direct_mutations:
        mutation_kind = normalized_name
    elif shell_apply_patch:
        mutation_kind = "apply_patch_via_shell"
    return {
        "tool_name": name,
        "payload": jsonable(payload),
        "is_mutation": bool(mutation_kind),
        "mutation_kind": mutation_kind or None,
    }


def jsonable(value: Any) -> Any:
    if isinstance(value, Session):
        return value.to_dict()
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, Mapping):
        return {str(key): jsonable(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [jsonable(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if hasattr(value, "to_dict"):
        try:
            return jsonable(value.to_dict())
        except Exception:
            pass
    return repr(value)


def write_json(path: Path, payload: Any) -> None:
    path.write_text(
        json.dumps(jsonable(payload), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _configure_case(
    *,
    config_path: Path,
    config_dir: Path,
    workspace: Path,
    model_case: ModelCase,
) -> None:
    config = json.loads(config_path.read_text(encoding="utf-8"))
    agent = config["agents"][model_case.agent_id]
    selected_tool_plugin = (
        "path:${env:BUILTIN_PLUGINS}/codex-tools"
        if model_case.auth_mode == "chatgpt"
        else "path:${env:BUILTIN_PLUGINS}/claude-tools"
    )
    config["plugins"] = [
        selected_tool_plugin,
        "plugins.tool_gating_feature.ToolGatingFeature",
        "path:${env:BUILTIN_PLUGINS}/feature-request-options",
        "path:${env:BUILTIN_PLUGINS}/feature-system-message",
        "path:${env:BUILTIN_PLUGINS}/feature-file-context",
        "path:${env:BUILTIN_PLUGINS}/reference-openai-compatible-provider",
        "path:${env:BUILTIN_PLUGINS}/openai_responses",
    ]
    config["agents"] = {model_case.agent_id: agent}
    agent["plugins"] = []
    if model_case.model:
        agent["model"] = model_case.model
    agent.update(
        {
            "include_tasks": True,
            "skills_enabled": False,
            "mcp_enabled": False,
            "web_search_enabled": False,
            "working_directory": str(workspace),
            "allowed_paths": [str(workspace)],
        }
    )

    if model_case.auth_mode == "chatgpt":
        credentials_path = chatgpt_credentials_path()
        agent.update(
            {
                "auth_mode": "chatgpt",
                "chatgpt_credentials_path": str(credentials_path),
                "enable_flex_processing": False,
            }
        )
        config["providers"]["openai"].update(
            {
                "auth_mode": "chatgpt",
                "chatgpt_credentials_path": str(credentials_path),
                "enable_flex_processing": False,
            }
        )
    else:
        model = model_case.model or str(agent["model"])
        agent["model"] = model
        config["providers"]["ollama"]["base_url"] = os.getenv(
            "OLLAMA_OPENAI_BASE_URL", DEFAULT_OLLAMA_BASE_URL
        )

    config["plugin_cache_dir"] = str(SHARED_PLUGIN_CACHE / "plugins")
    config_path.write_text(
        json.dumps(config, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _evict_stale_attr_modules() -> None:
    for module_name in list(sys.modules):
        if module_name in {"attr", "attrs"} or module_name.startswith(
            ("attr.", "attrs.")
        ):
            sys.modules.pop(module_name, None)


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _git(workspace: Path, *args: str) -> str:
    return _run(["git", *args], cwd=workspace).stdout


def _run(
    command: list[str],
    *,
    cwd: Path,
    timeout: int = 120,
) -> subprocess.CompletedProcess[str]:
    result = subprocess.run(
        command,
        cwd=str(cwd),
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )
    if result.returncode != 0:
        raise AssertionError(
            f"command failed ({result.returncode}): {command!r}\n"
            f"stdout:\n{result.stdout}\n"
            f"stderr:\n{result.stderr}"
        )
    return result
