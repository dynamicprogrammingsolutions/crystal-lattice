from __future__ import annotations

import hashlib
import json
import os
import shutil
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, cast

from agent_eval import AgentEval, Run
from agent_eval.crystal_lattice import (
    CrystalLatticeContext,
    CrystalLatticeEnvironment,
)
from agent_eval.services import RunServices
from maintainer.guidance import compile_guidance

from .fixtures import (
    AssessmentWorkspaceFactory,
    REPOSITORY_ROOT,
    TaskGuidanceWorkspaceFactory,
    selected_bundle,
)
from .harness import collect_tool_calls
from .handoffs import CanonicalHandoffWorkspaceFactory, PLAN_PROMPT
from .scenarios import TaskGuidanceScenario


PACKAGE_ROOT = REPOSITORY_ROOT / "maintainer" / "agent-evaluation"
DEFAULT_CONFIG_ROOT = (
    REPOSITORY_ROOT
    / "application"
    / "python"
    / "agent_terminal_app"
    / "default_config"
)
CRYSTAL_LATTICE_TARGET = (
    REPOSITORY_ROOT
    / "maintainer"
    / "guidance"
    / "targets"
    / "crystal-lattice"
)
PLUGIN_RUNTIME_CONSTRAINTS = PACKAGE_ROOT / "constraints" / "plugin-runtime.txt"
RUNNER_VERSION = "v1"


@dataclass(frozen=True)
class ModelProfile:
    name: str
    agent_id: str
    model: str
    auth_mode: str | None
    tool_fragment: str
    provider_fragments: tuple[str, ...]

    def request_overrides(
        self,
        workspace: Path,
        *,
        reasoning_effort: str,
        include_tasks: bool = True,
    ) -> dict[str, object]:
        values: dict[str, object] = {
            "model": self.model,
            "working_directory": str(workspace),
            "allowed_paths": [str(workspace)],
            "include_tasks": include_tasks,
            "skills_enabled": False,
            "mcp_enabled": False,
            "web_search_enabled": False,
        }
        if self.name == "glm":
            values["request_options"] = {"reasoning_effort": reasoning_effort}
        else:
            values["reasoning_effort"] = reasoning_effort
            values["reasoning_summary"] = "detailed"
        if self.auth_mode is not None:
            values["auth_mode"] = self.auth_mode
        if self.name == "gpt":
            state_root = Path(
                os.getenv("CHATGPT_TEST_STATE_DIR", str(Path.home() / ".crystal"))
            ).expanduser()
            values["chatgpt_credentials_path"] = str(
                state_root / "auth" / "chatgpt-auth.json"
            )
        return values


PROFILES = {
    "glm": ModelProfile(
        name="glm",
        agent_id="glm-ollama",
        model="glm-5.3-flash:cloud",
        auth_mode=None,
        tool_fragment="/claude-tools",
        provider_fragments=(
            "/feature-request-options",
            "/feature-system-message",
            "/reference-openai-compatible-provider",
        ),
    ),
    "gpt": ModelProfile(
        name="gpt",
        agent_id="codex-openai",
        model="gpt-5.6-luna",
        auth_mode="chatgpt",
        tool_fragment="/codex-tools",
        provider_fragments=(
            "/feature-request-options",
            "/feature-system-message",
            "/openai_responses",
            "/chatgpt-auth-app",
        ),
    ),
}


@dataclass(frozen=True)
class TaskRunValue:
    prompt: str
    response: str
    completed: bool
    cancelled: bool
    errors: tuple[str, ...]
    duration_seconds: float
    tool_event_count: int
    mutation_count: int
    task_files: Mapping[str, str]
    tool_calls: tuple[Mapping[str, Any], ...]
    tool_metrics: Mapping[str, int]
    delivery: Mapping[str, Any]


@dataclass(frozen=True)
class AssessmentRunValue:
    prompt: str
    response: str
    completed: bool
    cancelled: bool
    errors: tuple[str, ...]
    duration_seconds: float


@dataclass(frozen=True)
class PlanRunValue:
    prompt: str
    response: str
    completed: bool
    cancelled: bool
    errors: tuple[str, ...]
    duration_seconds: float
    tool_event_count: int
    mutation_count: int
    tool_calls: tuple[Mapping[str, Any], ...]
    tool_metrics: Mapping[str, int]
    delivery: Mapping[str, Any]
    task_files: Mapping[str, str]


class WorkspaceAwareEnvironment(CrystalLatticeEnvironment):
    @contextmanager
    def open(
        self,
        *,
        services: RunServices,
        workspace: Path | None,
        parent_snapshot: object | None,
    ) -> Iterator[CrystalLatticeContext]:
        if workspace is None:
            raise ValueError("task-guidance evaluations require a workspace")
        dynamic = CrystalLatticeEnvironment(
            config_path=self.config_path,
            env_overrides={
                **self.env_overrides,
                "WORKING_DIR": str(workspace),
                "REPO_ROOT": str(workspace),
            },
            config_env=self.config_env,
            core_factory=self.core_factory,
            application_factory=self.application_factory,
            default_agent=self.default_agent,
            request_driver=self.request_driver,
            snapshotter=self.snapshotter,
        )
        with dynamic.open(
            services=services,
            workspace=workspace,
            parent_snapshot=parent_snapshot,
        ) as context:
            yield context


class TaskGuidanceHarness:
    def __init__(
        self,
        profile: ModelProfile,
        *,
        bundle: Path | None = None,
    ) -> None:
        self.profile = profile
        self.bundle = (bundle or selected_bundle()).resolve()
        artifact_root = Path(
            os.getenv(
                "AGENT_EVAL_ARTIFACT_ROOT",
                str(
                    REPOSITORY_ROOT
                    / "tmp"
                    / "agent-evaluation"
                    / "task-guidance"
                ),
            )
        ).expanduser()
        runtime_config = _runtime_config_root(
            bundle=self.bundle,
            artifact_root=artifact_root,
        )
        projected_config = _project_config_for_profile(
            runtime_config / "config.json",
            artifact_root=artifact_root,
            profile=profile,
        )
        environment = WorkspaceAwareEnvironment.from_config(
            projected_config,
            environment={
                "CONFIG_DIR": str(runtime_config),
                "CHATGPT_TEST_STATE_DIR": str(
                    Path(
                        os.getenv(
                            "CHATGPT_TEST_STATE_DIR",
                            str(Path.home() / ".crystal"),
                        )
                    ).expanduser()
                ),
                "BUILTIN_PLUGINS": str(REPOSITORY_ROOT / "plugins"),
                "PIP_CONSTRAINT": str(PLUGIN_RUNTIME_CONSTRAINTS),
                "OLLAMA_OPENAI_BASE_URL": os.getenv(
                    "OLLAMA_OPENAI_BASE_URL",
                    "http://localhost:11434/v1",
                ),
            },
        )
        self.runtime_config = runtime_config
        self.evaluation = AgentEval(
            default_environment=environment,
            artifact_root=artifact_root / profile.name,
            cache_root=artifact_root / "cache" / profile.name,
        )

    def close(self) -> None:
        self.evaluation.close()

    def run_task_creation(
        self,
        *,
        scenario: TaskGuidanceScenario,
        reasoning_effort: str,
        cache_variant: str,
    ) -> Run[TaskRunValue]:
        workspace = TaskGuidanceWorkspaceFactory(
            scenario=scenario,
            bundle=self.bundle,
        )
        target_hash = hashlib.sha256(scenario.target_path.read_bytes()).hexdigest()
        cache_key = (
            f"task-guidance:{RUNNER_VERSION}:{self.profile.name}:"
            f"{self.profile.model}:{scenario.scenario_id}:{reasoning_effort}:"
            f"{workspace.fingerprint()}:{target_hash}:{cache_variant}:"
            f"{os.getenv('AGENT_EVAL_CACHE_NONCE', '').strip()}"
        )
        return self.evaluation.run(
            f"task-guidance-{scenario.scenario_id}-{reasoning_effort}",
            lambda context: self._task_creation_turn(
                context,
                scenario=scenario,
                reasoning_effort=reasoning_effort,
            ),
            workspace=workspace,
            cache_key=cache_key,
        )

    def run_assessment(
        self,
        *,
        test_id: str,
        prompt: str,
        reasoning_effort: str,
        cache_variant: str,
    ) -> Run[AssessmentRunValue]:
        workspace = AssessmentWorkspaceFactory()
        cache_key = (
            f"task-guidance-assessment:{RUNNER_VERSION}:{self.profile.name}:"
            f"{self.profile.model}:{test_id}:{reasoning_effort}:"
            f"{hashlib.sha256(prompt.encode('utf-8')).hexdigest()}:"
            f"{cache_variant}:"
            f"{os.getenv('AGENT_EVAL_CACHE_NONCE', '').strip()}"
        )
        return self.evaluation.run(
            test_id,
            lambda context: self._assessment_turn(
                context,
                prompt=prompt,
                reasoning_effort=reasoning_effort,
            ),
            workspace=workspace,
            cache_key=cache_key,
        )

    def run_plan_from_handoff(
        self,
        *,
        scenario: TaskGuidanceScenario,
        variant: str,
        reasoning_effort: str,
        cache_variant: str,
    ) -> Run[PlanRunValue]:
        workspace = CanonicalHandoffWorkspaceFactory(
            scenario=scenario,
            variant=variant,
            bundle=self.bundle,
        )
        cache_key = (
            f"task-guidance-handoff:{RUNNER_VERSION}:{self.profile.name}:"
            f"{self.profile.model}:{scenario.scenario_id}:{variant}:"
            f"{reasoning_effort}:{workspace.fingerprint()}:{cache_variant}"
        )
        return self.evaluation.run(
            f"task-guidance-handoff-{scenario.scenario_id}-{variant}",
            lambda context: self._plan_turn(
                context,
                reasoning_effort=reasoning_effort,
            ),
            workspace=workspace,
            cache_key=cache_key,
        )

    def continue_same_agent_plan(
        self,
        *,
        parent: Run[TaskRunValue],
        scenario: TaskGuidanceScenario,
        reasoning_effort: str,
    ) -> Run[PlanRunValue]:
        if parent.workspace is None:
            raise ValueError("task-creation parent has no workspace")
        return self.evaluation.run(
            f"task-guidance-same-agent-{scenario.scenario_id}",
            lambda context: self._plan_turn(
                context,
                reasoning_effort=reasoning_effort,
            ),
            continue_from=parent,
            workspace=parent.workspace,
        )

    def _task_creation_turn(
        self,
        context: CrystalLatticeContext,
        *,
        scenario: TaskGuidanceScenario,
        reasoning_effort: str,
    ) -> TaskRunValue:
        if context.workspace is None:
            raise ValueError("missing task-guidance workspace")
        if context.session_or_none is None:
            context.start(self.profile.agent_id)
        context.config.update(
            self.profile.request_overrides(
                context.workspace,
                reasoning_effort=reasoning_effort,
            )
        )
        _reload_context_with_defaults(context)
        delivery = compiled_delivery_evidence(
            context,
            profile=self.profile,
            runtime_config=self.runtime_config,
        )
        context.services.record(
            "task_guidance.profile",
            {
                "name": self.profile.name,
                "agent_id": self.profile.agent_id,
                "model": self.profile.model,
                "auth_mode": self.profile.auth_mode,
                "reasoning_effort": reasoning_effort,
            },
        )
        context.services.record(
            "task_guidance.scenario",
            {
                "scenario_id": scenario.scenario_id,
                "category": scenario.category,
                "target": scenario.target,
            },
        )
        context.services.record("task_guidance.delivery", delivery)
        context.add_message("user", scenario.prompt)
        outcome = context.request(
            stream=True,
            max_events=_optional_int("AGENT_EVAL_MAX_EVENTS"),
        )
        task_files = {
            str(path.relative_to(context.workspace)): path.read_text(
                encoding="utf-8",
                errors="replace",
            )
            for path in sorted((context.workspace / "tasks").rglob("*.md"))
        } if (context.workspace / "tasks").is_dir() else {}
        calls = tuple(collect_tool_calls(context.session))
        metrics = tool_metrics(calls)
        context.services.record("task_guidance.tool_metrics", metrics)
        context.services.record(
            "task_guidance.task_files",
            {
                "paths": sorted(task_files),
                "count": len(task_files),
            },
        )
        return TaskRunValue(
            prompt=scenario.prompt,
            response=outcome.final_response,
            completed=outcome.completed,
            cancelled=outcome.cancelled,
            errors=outcome.error_messages,
            duration_seconds=outcome.duration_seconds,
            tool_event_count=outcome.tool_event_count,
            mutation_count=outcome.mutation_count,
            task_files=task_files,
            tool_calls=calls,
            tool_metrics=metrics,
            delivery=delivery,
        )

    def _assessment_turn(
        self,
        context: CrystalLatticeContext,
        *,
        prompt: str,
        reasoning_effort: str,
    ) -> AssessmentRunValue:
        if context.workspace is None:
            raise ValueError("missing assessment workspace")
        if context.session_or_none is None:
            context.start(self.profile.agent_id)
        context.config.update(
            self.profile.request_overrides(
                context.workspace,
                reasoning_effort=reasoning_effort,
                include_tasks=False,
            )
        )
        context.services.record(
            "task_guidance.assessment_profile",
            {
                "name": self.profile.name,
                "model": self.profile.model,
                "reasoning_effort": reasoning_effort,
            },
        )
        context.add_message("user", prompt)
        outcome = context.request(
            stream=True,
            max_events=_optional_int("AGENT_EVAL_MAX_EVENTS"),
        )
        return AssessmentRunValue(
            prompt=prompt,
            response=outcome.final_response,
            completed=outcome.completed,
            cancelled=outcome.cancelled,
            errors=outcome.error_messages,
            duration_seconds=outcome.duration_seconds,
        )

    def _plan_turn(
        self,
        context: CrystalLatticeContext,
        *,
        reasoning_effort: str,
    ) -> PlanRunValue:
        if context.workspace is None:
            raise ValueError("missing handoff workspace")
        if context.session_or_none is None:
            context.start(self.profile.agent_id)
        context.config.update(
            self.profile.request_overrides(
                context.workspace,
                reasoning_effort=reasoning_effort,
            )
        )
        _reload_context_with_defaults(context)
        delivery = compiled_delivery_evidence(
            context,
            profile=self.profile,
            runtime_config=self.runtime_config,
        )
        parent_message_count = len(context.session.messages)
        context.add_message("user", PLAN_PROMPT)
        outcome = context.request(
            stream=True,
            max_events=_optional_int("AGENT_EVAL_MAX_EVENTS"),
        )
        calls = tuple(
            call
            for call in collect_tool_calls(context.session)
            if int(call.get("message_index", -1)) >= parent_message_count
        )
        metrics = tool_metrics(calls)
        context.services.record("task_guidance.tool_metrics", metrics)
        task_files = _workspace_task_files(context.workspace)
        return PlanRunValue(
            prompt=PLAN_PROMPT,
            response=outcome.final_response,
            completed=outcome.completed,
            cancelled=outcome.cancelled,
            errors=outcome.error_messages,
            duration_seconds=outcome.duration_seconds,
            tool_event_count=outcome.tool_event_count,
            mutation_count=outcome.mutation_count,
            tool_calls=calls,
            tool_metrics=metrics,
            delivery=delivery,
            task_files=task_files,
        )


def selected_profile() -> ModelProfile:
    name = os.getenv("AGENT_EVAL_PROFILE", "").strip().lower()
    if name not in PROFILES:
        raise ValueError(
            "AGENT_EVAL_PROFILE must be one of: " + ", ".join(sorted(PROFILES))
        )
    return PROFILES[name]


def compiled_delivery_evidence(
    context: CrystalLatticeContext,
    *,
    profile: ModelProfile,
    runtime_config: Path,
) -> dict[str, Any]:
    effective = cast(dict[str, Any], context.effective_config())
    active = context.core.get_plugins_for_config(effective)
    tool_schemas = context.core.get_tool_schemas(effective)
    _, result = context.core.execute_session_action(
        context.session,
        effective,
        plugin_id="system_message",
        action_id="show_compiled_system_message",
        params={},
    )
    display = result.get("display")
    if not isinstance(display, dict):
        raise ValueError("compiled system-message action returned no display")
    body = display.get("body")
    if not isinstance(body, str) or not body.strip():
        raise ValueError("compiled system-message action returned no content")
    agents = context.workspace / "AGENTS.md" if context.workspace else None
    if agents is None or not agents.is_file():
        raise ValueError("compiled workspace AGENTS.md is missing")
    tasks = runtime_config / "TASKS_v7.md"
    if not tasks.is_file():
        raise ValueError("runtime TASKS_v7.md is missing")

    tools: list[dict[str, object]] = []
    for schema in tool_schemas:
        function = schema.get("function")
        value = function if isinstance(function, dict) else schema
        parameters = value.get("parameters") or value.get("input_schema") or {}
        properties = parameters.get("properties", {}) if isinstance(parameters, dict) else {}
        command = properties.get("command", {}) if isinstance(properties, dict) else {}
        tools.append(
            {
                "name": value.get("name"),
                "command_type": command.get("type") if isinstance(command, dict) else None,
            }
        )
    expected_tool = (
        {"name": "shell", "command_type": "array"}
        if profile.name == "gpt"
        else {"name": "Bash", "command_type": "string"}
    )
    return {
        "runner": "default-system-message",
        "model_family": "codex" if profile.name == "gpt" else "claude",
        "model": profile.model,
        "include_tasks": True,
        "compiled_sha256": hashlib.sha256(body.encode("utf-8")).hexdigest(),
        "agents_sha256": hashlib.sha256(agents.read_bytes()).hexdigest(),
        "tasks_sha256": hashlib.sha256(tasks.read_bytes()).hexdigest(),
        "agents_occurrences": body.count(agents.read_text(encoding="utf-8").strip()),
        "tasks_occurrences": body.count(tasks.read_text(encoding="utf-8").strip()),
        "active_tools": active.get("tools", []),
        "tool_interfaces": tools,
        "tool_family_matches": expected_tool in tools,
        "suite_wrapper_absent": "<repository-guidance" not in body,
    }


def tool_metrics(calls: tuple[Mapping[str, Any], ...]) -> dict[str, int]:
    metrics = {
        "total": len(calls),
        "mutation": 0,
        "read": 0,
        "search": 0,
        "list": 0,
        "shell": 0,
        "other": 0,
    }
    for call in calls:
        name = str(call.get("tool_name") or "").lower()
        if call.get("is_mutation"):
            metrics["mutation"] += 1
        if name in {"read", "read_file", "view", "view_file"}:
            metrics["read"] += 1
        elif name in {"grep", "glob", "rg", "search", "find"}:
            metrics["search"] += 1
        elif name in {"ls", "list", "list_files"}:
            metrics["list"] += 1
        elif name in {"shell", "bash", "shell_command"}:
            metrics["shell"] += 1
        else:
            metrics["other"] += 1
    return metrics


def _runtime_config_root(*, bundle: Path, artifact_root: Path) -> Path:
    compilation = compile_guidance(
        bundle=bundle,
        target=CRYSTAL_LATTICE_TARGET,
        repository_root=REPOSITORY_ROOT,
    )
    digest = str(compilation.lock["compilation_sha256"])
    target = artifact_root / "runtime-config" / digest[:20]
    if not target.is_dir():
        shutil.copytree(
            DEFAULT_CONFIG_ROOT,
            target,
            ignore=shutil.ignore_patterns(
                ".plugin_cache",
                "auth",
                "__pycache__",
            ),
        )
    tasks = compilation.outputs["agents/TASKS-v7.md"]
    task_path = target / "TASKS_v7.md"
    if not task_path.exists() or task_path.read_bytes() != tasks:
        task_path.write_bytes(tasks)
    return target


def _project_config_for_profile(
    source: Path,
    *,
    artifact_root: Path,
    profile: ModelProfile,
) -> Path:
    raw = json.loads(source.read_text(encoding="utf-8"))
    agents = raw.get("agents")
    plugins = raw.get("plugins")
    if not isinstance(agents, dict) or not isinstance(plugins, list):
        raise ValueError("default config is missing agents or plugins")
    selected = agents.get(profile.agent_id)
    if not isinstance(selected, dict):
        raise KeyError(f"default config has no agent {profile.agent_id!r}")
    fragments = (
        profile.tool_fragment,
        *profile.provider_fragments,
    )
    selected_plugins = [
        item
        for item in plugins
        if isinstance(item, str)
        and (
            not item.startswith(("path:", "bash:", "node:"))
            or any(fragment in item for fragment in fragments)
        )
    ]
    for item in selected.get("plugins", []):
        if isinstance(item, str) and any(
            fragment in item for fragment in fragments
        ) and item not in selected_plugins:
            selected_plugins.append(item)
    missing = [
        fragment
        for fragment in fragments
        if not any(fragment in item for item in selected_plugins)
    ]
    if missing:
        raise ValueError(f"default config is missing profile plugins: {missing}")
    projected_agent = {**selected, "plugins": list(selected.get("plugins") or [])}
    if profile.auth_mode is not None:
        projected_agent["auth_mode"] = profile.auth_mode
    if profile.name == "gpt":
        state_root = Path(
            os.getenv("CHATGPT_TEST_STATE_DIR", str(Path.home() / ".crystal"))
        ).expanduser()
        projected_agent["chatgpt_credentials_path"] = str(
            state_root / "auth" / "chatgpt-auth.json"
        )
    projected = {
        **raw,
        "agents": {profile.agent_id: projected_agent},
        "plugins": selected_plugins,
        "plugin_cache_dir": str(
            artifact_root / "plugin-cache" / profile.name / RUNNER_VERSION
        ),
    }
    config_root = artifact_root / "projected-config"
    config_root.mkdir(parents=True, exist_ok=True)
    target = config_root / f"{profile.name}-{RUNNER_VERSION}.json"
    rendered = json.dumps(projected, indent=2, sort_keys=True) + "\n"
    if not target.exists() or target.read_text(encoding="utf-8") != rendered:
        target.write_text(rendered, encoding="utf-8")
    return target


def _reload_context_with_defaults(context: CrystalLatticeContext) -> None:
    loaded = context.application.load_session(
        context.session.session_id,
        overrides=context.config,
    )
    if loaded is None:
        raise RuntimeError("failed to reload task-guidance evaluation session")
    core, base_config, session = loaded
    context.replace_runtime(
        core=core,
        base_config=base_config,
        session=session,
    )


def _optional_int(name: str) -> int | None:
    raw = os.getenv(name, "").strip()
    return int(raw) if raw else None


def _workspace_task_files(workspace: Path) -> dict[str, str]:
    root = workspace / "tasks"
    if not root.is_dir():
        return {}
    return {
        str(path.relative_to(workspace)): path.read_text(
            encoding="utf-8",
            errors="replace",
        )
        for path in sorted(root.rglob("*.md"))
    }