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

from .configuration import (
    AGENTS,
    GUIDANCE_TARGET,
    agent_config_file,
    negative_control,
    selected_artifact_root,
    selected_bundle,
)
from .fixtures import (
    AssessmentWorkspaceFactory,
    REPOSITORY_ROOT,
    TaskGuidanceWorkspaceFactory,
)
from .harness import collect_tool_calls
from .handoffs import CanonicalHandoffWorkspaceFactory, PLAN_PROMPT
from .scenarios import TaskGuidanceScenario, scenario_by_id


PACKAGE_ROOT = REPOSITORY_ROOT / "maintainer" / "agent-evaluation"
DEFAULT_CONFIG_ROOT = (
    REPOSITORY_ROOT / "application" / "python" / "agent_terminal_app" / "default_config"
)
PLUGIN_RUNTIME_CONSTRAINTS = PACKAGE_ROOT / "constraints" / "plugin-runtime.txt"
RUNNER_VERSION = "v1"


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
        agent_name: str,
        *,
        bundle: Path | None = None,
    ) -> None:
        self.agent_name = agent_name
        self.agent = AGENTS[agent_name]
        self.bundle = (bundle or selected_bundle()).resolve()
        artifact_root = selected_artifact_root()
        runtime_config = _runtime_config_root(
            bundle=self.bundle,
            artifact_root=artifact_root,
        )
        agent_config = agent_config_file(
            agent_name,
            artifact_root=artifact_root,
            version=RUNNER_VERSION,
        )
        environment = WorkspaceAwareEnvironment.from_config(
            agent_config,
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
        self.runtime_agent = json.loads(agent_config.read_text(encoding="utf-8"))[
            "agents"
        ][self.agent["agent_id"]]
        self.evaluation = AgentEval(
            default_environment=environment,
            artifact_root=artifact_root / agent_name,
            cache_root=artifact_root / "cache" / agent_name,
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
            f"task-guidance:{RUNNER_VERSION}:{self.agent_name}:"
            f"{self.agent['model']}:{scenario.scenario_id}:{reasoning_effort}:"
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
            f"task-guidance-assessment:{RUNNER_VERSION}:{self.agent_name}:"
            f"{self.agent['model']}:{test_id}:{reasoning_effort}:"
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
            f"task-guidance-handoff:{RUNNER_VERSION}:{self.agent_name}:"
            f"{self.agent['model']}:{scenario.scenario_id}:{variant}:"
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

    def run_negative_control(
        self,
        *,
        category: str,
        cache_variant: str,
    ) -> Run[PlanRunValue]:
        """The designated negative-control run for one scenario category."""

        control = negative_control(category)
        if control is None:
            raise ValueError(f"category {category!r} declares no negative control")
        if self.agent_name != control["agent"]:
            raise ValueError(
                f"negative control is designated for {control['agent']!r},"
                f" not {self.agent_name!r}"
            )
        scenario = scenario_by_id(control["scenario"])
        return self.run_plan_from_handoff(
            scenario=scenario,
            variant=control["variant"],
            reasoning_effort=control["effort"],
            cache_variant=cache_variant,
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
            context.start(self.agent["agent_id"])
        context.config.update(
            request_overrides(
                self.agent_name,
                context.workspace,
                reasoning_effort=reasoning_effort,
            )
        )
        _reload_context_with_defaults(context)
        delivery = compiled_delivery_evidence(
            context,
            agent_name=self.agent_name,
            runtime_config=self.runtime_config,
        )
        context.services.record(
            "task_guidance.profile",
            {
                "name": self.agent_name,
                "agent_id": self.agent["agent_id"],
                "model": self.agent["model"],
                "auth_mode": self.runtime_agent.get("auth_mode"),
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
        task_files = (
            {
                str(path.relative_to(context.workspace)): path.read_text(
                    encoding="utf-8",
                    errors="replace",
                )
                for path in sorted((context.workspace / "tasks").rglob("*.md"))
            }
            if (context.workspace / "tasks").is_dir()
            else {}
        )
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
            context.start(self.agent["agent_id"])
        context.config.update(
            request_overrides(
                self.agent_name,
                context.workspace,
                reasoning_effort=reasoning_effort,
                include_tasks=False,
            )
        )
        context.services.record(
            "task_guidance.assessment_profile",
            {
                "name": self.agent_name,
                "model": self.agent["model"],
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
            context.start(self.agent["agent_id"])
        context.config.update(
            request_overrides(
                self.agent_name,
                context.workspace,
                reasoning_effort=reasoning_effort,
            )
        )
        _reload_context_with_defaults(context)
        delivery = compiled_delivery_evidence(
            context,
            agent_name=self.agent_name,
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


def selected_agent() -> str:
    """The agent the live matrix runs (``AGENT_EVAL_PROFILE``)."""

    name = os.getenv("AGENT_EVAL_PROFILE", "").strip().lower()
    if name not in AGENTS:
        raise ValueError(
            "AGENT_EVAL_PROFILE must be one of: " + ", ".join(sorted(AGENTS))
        )
    return name


def request_overrides(
    agent_name: str,
    workspace: Path,
    *,
    reasoning_effort: str,
    include_tasks: bool = True,
) -> dict[str, object]:
    """Per-request settings layered over the agent's pinned runtime config.

    The runtime config fixture pins the plugin wiring and the
    authentication method; only the model, the workspace, the guidance
    toggles, and the reasoning-effort shape vary per request.
    """

    values: dict[str, object] = {
        "model": AGENTS[agent_name]["model"],
        "working_directory": str(workspace),
        "allowed_paths": [str(workspace)],
        "include_tasks": include_tasks,
        "skills_enabled": False,
        "mcp_enabled": False,
        "web_search_enabled": False,
    }
    if agent_name == "glm":
        values["request_options"] = {"reasoning_effort": reasoning_effort}
    else:
        values["reasoning_effort"] = reasoning_effort
        values["reasoning_summary"] = "detailed"
    return values


def compiled_delivery_evidence(
    context: CrystalLatticeContext,
    *,
    agent_name: str,
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
        properties = (
            parameters.get("properties", {}) if isinstance(parameters, dict) else {}
        )
        command = properties.get("command", {}) if isinstance(properties, dict) else {}
        tools.append(
            {
                "name": value.get("name"),
                "command_type": (
                    command.get("type") if isinstance(command, dict) else None
                ),
            }
        )
    expected_tool = (
        {"name": "shell", "command_type": "array"}
        if agent_name == "gpt"
        else {"name": "Bash", "command_type": "string"}
    )
    return {
        "runner": "default-system-message",
        "model_family": "codex" if agent_name == "gpt" else "claude",
        "model": AGENTS[agent_name]["model"],
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
        target=GUIDANCE_TARGET,
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
