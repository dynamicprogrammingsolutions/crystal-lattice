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
from agent_eval.runner import RunModel, request_identity
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
from .handoffs import (
    CanonicalHandoffWorkspaceFactory,
    GeneratedTaskWorkspaceFactory,
    PLAN_PROMPT,
)
from .scenarios import TaskGuidanceScenario, scenario_by_id


PACKAGE_ROOT = REPOSITORY_ROOT / "maintainer" / "agent-evaluation"
DEFAULT_CONFIG_ROOT = (
    REPOSITORY_ROOT / "application" / "python" / "agent_terminal_app" / "default_config"
)
PLUGIN_RUNTIME_CONSTRAINTS = PACKAGE_ROOT / "constraints" / "plugin-runtime.txt"
RUNNER_VERSION = "v1"
IDENTITY_NAMESPACE = "task-guidance"

# Two-stage pipeline variants (subtask 125). The planning arm selects
# whether the tasks guidance is compiled into the planning turn's system
# message (the fixture workspace's AGENTS.md has no tasks slot, so the
# per-request flag is the whole difference between the arms). The creation
# variant selects the writing ask: the standard guidance-following
# continuation, or the instructed execution-plan omission.
PLANNING_VARIANTS = ("guided", "unguided")
CREATION_VARIANTS = ("standard", "omit-plan")
# Reasoning-state variants for the two-stage cells (subtask 125): the
# harness maps the behavioral name onto the per-provider mechanism —
# ollama strips inline thinking with the interleaved-thinking plugin
# (a config variant), zai preserves server-side thinking with a request
# option, and gpt keeps provider-default behavior either way.
THINKING_VARIANTS = ("default", "preserve", "strip")
PLANNING_SESSION_SUFFIX = (
    "\n\nInvestigate the repository first. Then present your implementation "
    "plan for the request above as your response. Do not implement anything "
    "and do not create or modify any file: present the plan only."
)
FROM_PLAN_PROMPTS = {
    "standard": (
        "Proceed with the plan you presented: create the task file(s) for it "
        "under tasks/ now, following the task guidance in full."
    ),
    "omit-plan": (
        "Proceed with the plan you presented: create the task file(s) for it "
        "under tasks/ now, following the task guidance in full — but do not "
        "include an execution-plan section in the task file(s)."
    ),
}


def task_creation_identity(
    *,
    agent_name: str,
    scenario: TaskGuidanceScenario,
    reasoning_effort: str,
    workspace_fingerprint: object,
    target_sha256: str,
) -> str:
    """The cache identity of one task-creation request."""

    return request_identity(
        namespace=IDENTITY_NAMESPACE,
        version=RUNNER_VERSION,
        components={
            "stage": "task-creation",
            "agent": agent_name,
            "model": AGENTS[agent_name]["model"],
            "scenario": scenario.scenario_id,
            "effort": reasoning_effort,
            "workspace_fingerprint": workspace_fingerprint,
            "target_sha256": target_sha256,
        },
    )


def handoff_plan_identity(
    *,
    agent_name: str,
    scenario: TaskGuidanceScenario,
    variant: str,
    reasoning_effort: str,
    workspace_fingerprint: object,
) -> str:
    """The cache identity of one fresh-agent planning request."""

    return request_identity(
        namespace=IDENTITY_NAMESPACE,
        version=RUNNER_VERSION,
        components={
            "stage": "handoff-plan",
            "agent": agent_name,
            "model": AGENTS[agent_name]["model"],
            "scenario": scenario.scenario_id,
            "variant": variant,
            "effort": reasoning_effort,
            "workspace_fingerprint": workspace_fingerprint,
        },
    )


def planning_session_identity(
    *,
    agent_name: str,
    scenario: TaskGuidanceScenario,
    variant: str,
    reasoning_effort: str,
    workspace_fingerprint: object,
    thinking: str = "default",
) -> str:
    """The cache identity of one planning-session request."""

    return request_identity(
        namespace=IDENTITY_NAMESPACE,
        version=RUNNER_VERSION,
        components={
            "stage": "planning-session",
            "agent": agent_name,
            "model": AGENTS[agent_name]["model"],
            "scenario": scenario.scenario_id,
            "variant": variant,
            "effort": reasoning_effort,
            "workspace_fingerprint": workspace_fingerprint,
            "thinking": thinking,
        },
    )


def from_plan_identity(
    *,
    agent_name: str,
    scenario: TaskGuidanceScenario,
    variant: str,
    reasoning_effort: str,
    parent_identity: str,
    thinking: str = "default",
) -> str:
    """The cache identity of one plan-continuing creation request.

    The planning run's identity is a component, so a regenerated plan
    invalidates the creation cache even though the creation request
    material itself is unchanged.
    """

    return request_identity(
        namespace=IDENTITY_NAMESPACE,
        version=RUNNER_VERSION,
        components={
            "stage": "task-creation-from-plan",
            "agent": agent_name,
            "model": AGENTS[agent_name]["model"],
            "scenario": scenario.scenario_id,
            "variant": variant,
            "effort": reasoning_effort,
            "parent_identity": parent_identity,
            "thinking": thinking,
        },
    )


def continuation_identity(
    *,
    agent_name: str,
    scenario: TaskGuidanceScenario,
    reasoning_effort: str,
    parent_identity: str,
) -> str:
    """The cache identity of one same-agent continuation request.

    The parent's identity is a component, so a re-produced task-creation
    run invalidates the continuation cache even though the continuation
    request material itself is unchanged.
    """

    return request_identity(
        namespace=IDENTITY_NAMESPACE,
        version=RUNNER_VERSION,
        components={
            "stage": "continuation",
            "agent": agent_name,
            "model": AGENTS[agent_name]["model"],
            "scenario": scenario.scenario_id,
            "effort": reasoning_effort,
            "parent_identity": parent_identity,
        },
    )


def generated_plan_identity(
    *,
    agent_name: str,
    scenario: TaskGuidanceScenario,
    reasoning_effort: str,
    parent_identity: str,
) -> str:
    """The cache identity of one fresh-agent generated-file planning request.

    The producing run's identity is a component, so a re-produced task
    set invalidates the plan cache even though the planning request
    material itself is unchanged.
    """

    return request_identity(
        namespace=IDENTITY_NAMESPACE,
        version=RUNNER_VERSION,
        components={
            "stage": "generated-plan",
            "agent": agent_name,
            "model": AGENTS[agent_name]["model"],
            "scenario": scenario.scenario_id,
            "effort": reasoning_effort,
            "parent_identity": parent_identity,
        },
    )


def assessment_identity(
    *,
    agent_name: str,
    test_id: str,
    prompt: str,
    reasoning_effort: str,
) -> str:
    """The cache identity of one assessment request."""

    return request_identity(
        namespace=IDENTITY_NAMESPACE,
        version=RUNNER_VERSION,
        components={
            "stage": "assessment",
            "agent": agent_name,
            "model": AGENTS[agent_name]["model"],
            "test_id": test_id,
            "effort": reasoning_effort,
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest(),
        },
    )


def run_identity(run: Run[object]) -> str:
    """The recorded request identity of one executed run."""

    provenance = run.artifact_dir / "records" / "run-model.json"
    value = json.loads(provenance.read_text(encoding="utf-8"))
    identity = value.get("identity")
    if not isinstance(identity, str) or not identity:
        raise ValueError(f"run {run.run_id!r} has no recorded identity")
    return identity


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
class PlanningRunValue:
    prompt: str
    response: str
    variant: str
    completed: bool
    cancelled: bool
    errors: tuple[str, ...]
    duration_seconds: float
    tool_event_count: int
    mutation_count: int
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
        label: str | None = None,
        thinking: str = "default",
    ) -> None:
        if thinking not in THINKING_VARIANTS:
            raise ValueError(f"unknown thinking variant {thinking!r}")
        self.agent_name = agent_name
        self.agent = AGENTS[agent_name]
        self.thinking = thinking
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
            thinking=thinking,
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
        self.model = RunModel(self.evaluation, label=label)

    def close(self) -> None:
        self.evaluation.close()

    def run_task_creation(
        self,
        *,
        scenario: TaskGuidanceScenario,
        reasoning_effort: str,
        fresh: bool = False,
        samples: int = 1,
    ) -> tuple[Run[TaskRunValue], ...]:
        workspace = TaskGuidanceWorkspaceFactory(
            scenario=scenario,
            bundle=self.bundle,
        )
        identity = task_creation_identity(
            agent_name=self.agent_name,
            scenario=scenario,
            reasoning_effort=reasoning_effort,
            workspace_fingerprint=workspace.fingerprint(),
            target_sha256=hashlib.sha256(scenario.target_path.read_bytes()).hexdigest(),
        )
        return self._execute(
            f"task-guidance-{scenario.scenario_id}-{reasoning_effort}",
            lambda context: self._task_creation_turn(
                context,
                scenario=scenario,
                reasoning_effort=reasoning_effort,
            ),
            identity=identity,
            workspace=workspace,
            fresh=fresh,
            samples=samples,
        )

    def run_planning_session(
        self,
        *,
        scenario: TaskGuidanceScenario,
        variant: str,
        reasoning_effort: str,
        fresh: bool = False,
        samples: int = 1,
    ) -> tuple[Run[PlanningRunValue], ...]:
        """One planning turn: the scenario request plus the plan-only ask.

        ``variant`` selects the planning arm: ``guided`` compiles the
        tasks guidance into the planning turn's system message;
        ``unguided`` compiles none. The run writes no files — its
        response is the presented plan the continuation and the
        plan-content gate consume.
        """

        if variant not in PLANNING_VARIANTS:
            raise ValueError(f"unknown planning variant {variant!r}")
        workspace = TaskGuidanceWorkspaceFactory(
            scenario=scenario,
            bundle=self.bundle,
        )
        identity = planning_session_identity(
            agent_name=self.agent_name,
            scenario=scenario,
            variant=variant,
            reasoning_effort=reasoning_effort,
            workspace_fingerprint=workspace.fingerprint(),
            thinking=self.thinking,
        )
        return self._execute(
            f"task-guidance-planning-{scenario.scenario_id}-{variant}",
            lambda context: self._planning_turn(
                context,
                scenario=scenario,
                variant=variant,
                reasoning_effort=reasoning_effort,
            ),
            identity=identity,
            workspace=workspace,
            fresh=fresh,
            samples=samples,
        )

    def run_task_creation_from_plan(
        self,
        *,
        parent: Run[PlanningRunValue],
        scenario: TaskGuidanceScenario,
        variant: str,
        reasoning_effort: str,
        fresh: bool = False,
        samples: int = 1,
    ) -> tuple[Run[TaskRunValue], ...]:
        """The writing turn that continues a planning session.

        The run continues the parent planning session (its workspace and
        session prefix); the tasks guidance is compiled into the writing
        turn's system message regardless of the planning arm. ``variant``
        selects the creation ask: ``standard`` follows the guidance in
        full; ``omit-plan`` additionally instructs the agent to leave the
        execution-plan section out of the task file(s).
        """

        if variant not in CREATION_VARIANTS:
            raise ValueError(f"unknown creation variant {variant!r}")
        if parent.workspace is None:
            raise ValueError("planning-session parent has no workspace")
        identity = from_plan_identity(
            agent_name=self.agent_name,
            scenario=scenario,
            variant=variant,
            reasoning_effort=reasoning_effort,
            parent_identity=run_identity(parent),
            thinking=self.thinking,
        )
        return self._execute(
            f"task-guidance-from-plan-{scenario.scenario_id}-{variant}",
            lambda context: self._from_plan_turn(
                context,
                scenario=scenario,
                variant=variant,
                reasoning_effort=reasoning_effort,
            ),
            identity=identity,
            workspace=parent.workspace,
            continue_from=parent,
            fresh=fresh,
            samples=samples,
        )

    def run_assessment(
        self,
        *,
        test_id: str,
        prompt: str,
        reasoning_effort: str,
        fresh: bool = False,
        samples: int = 1,
    ) -> tuple[Run[AssessmentRunValue], ...]:
        identity = assessment_identity(
            agent_name=self.agent_name,
            test_id=test_id,
            prompt=prompt,
            reasoning_effort=reasoning_effort,
        )
        return self._execute(
            test_id,
            lambda context: self._assessment_turn(
                context,
                prompt=prompt,
                reasoning_effort=reasoning_effort,
            ),
            identity=identity,
            workspace=AssessmentWorkspaceFactory(),
            fresh=fresh,
            samples=samples,
        )

    def run_plan_from_handoff(
        self,
        *,
        scenario: TaskGuidanceScenario,
        variant: str,
        reasoning_effort: str,
        fresh: bool = False,
        samples: int = 1,
    ) -> tuple[Run[PlanRunValue], ...]:
        workspace = CanonicalHandoffWorkspaceFactory(
            scenario=scenario,
            variant=variant,
            bundle=self.bundle,
        )
        identity = handoff_plan_identity(
            agent_name=self.agent_name,
            scenario=scenario,
            variant=variant,
            reasoning_effort=reasoning_effort,
            workspace_fingerprint=workspace.fingerprint(),
        )
        return self._execute(
            f"task-guidance-handoff-{scenario.scenario_id}-{variant}",
            lambda context: self._plan_turn(
                context,
                reasoning_effort=reasoning_effort,
            ),
            identity=identity,
            workspace=workspace,
            fresh=fresh,
            samples=samples,
        )

    def run_plan_from_generated(
        self,
        *,
        parent: Run[TaskRunValue],
        scenario: TaskGuidanceScenario,
        reasoning_effort: str,
        fresh: bool = False,
        samples: int = 1,
    ) -> tuple[Run[PlanRunValue], ...]:
        parent_value = parent.value
        if parent_value is None:
            raise ValueError("task-creation parent produced no value")
        workspace = GeneratedTaskWorkspaceFactory(
            scenario=scenario,
            bundle=self.bundle,
            task_files=parent_value.task_files,
        )
        identity = generated_plan_identity(
            agent_name=self.agent_name,
            scenario=scenario,
            reasoning_effort=reasoning_effort,
            parent_identity=run_identity(parent),
        )
        return self._execute(
            f"task-guidance-generated-{scenario.scenario_id}-{reasoning_effort}",
            lambda context: self._plan_turn(
                context,
                reasoning_effort=reasoning_effort,
            ),
            identity=identity,
            workspace=workspace,
            fresh=fresh,
            samples=samples,
        )

    def continue_same_agent_plan(
        self,
        *,
        parent: Run[TaskRunValue],
        scenario: TaskGuidanceScenario,
        reasoning_effort: str,
        fresh: bool = False,
        samples: int = 1,
    ) -> tuple[Run[PlanRunValue], ...]:
        if parent.workspace is None:
            raise ValueError("task-creation parent has no workspace")
        identity = continuation_identity(
            agent_name=self.agent_name,
            scenario=scenario,
            reasoning_effort=reasoning_effort,
            parent_identity=run_identity(parent),
        )
        return self._execute(
            f"task-guidance-same-agent-{scenario.scenario_id}",
            lambda context: self._plan_turn(
                context,
                reasoning_effort=reasoning_effort,
            ),
            identity=identity,
            workspace=parent.workspace,
            continue_from=parent,
            fresh=fresh,
            samples=samples,
        )

    def run_negative_control(
        self,
        *,
        category: str,
        fresh: bool = False,
        samples: int = 1,
    ) -> tuple[Run[PlanRunValue], ...]:
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
            fresh=fresh,
            samples=samples,
        )

    def _execute(
        self,
        name: str,
        program: object,
        *,
        identity: str,
        workspace: object,
        continue_from: Run[object] | None = None,
        fresh: bool = False,
        samples: int = 1,
    ) -> tuple[Run[object], ...]:
        """Execute one stage request through the run model.

        A single sample is cache-aware (``fresh`` forces re-execution);
        multiple samples are always genuine executions of the identical
        request identity, recorded under the invocation's run label.
        """

        if samples > 1:
            return self.model.run_samples(
                name,
                program,
                identity=identity,
                count=samples,
                workspace=workspace,
                continue_from=continue_from,
            )
        run = self.model.run(
            name,
            program,
            identity=identity,
            workspace=workspace,
            continue_from=continue_from,
            fresh=fresh,
        )
        return (run,)

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
        outcome = context.request(stream=True)
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

    def _planning_turn(
        self,
        context: CrystalLatticeContext,
        *,
        scenario: TaskGuidanceScenario,
        variant: str,
        reasoning_effort: str,
    ) -> PlanningRunValue:
        if context.workspace is None:
            raise ValueError("missing task-guidance workspace")
        if context.session_or_none is None:
            context.start(self.agent["agent_id"])
        include_tasks = variant == "guided"
        prompt = scenario.prompt + PLANNING_SESSION_SUFFIX
        context.config.update(
            request_overrides(
                self.agent_name,
                context.workspace,
                reasoning_effort=reasoning_effort,
                include_tasks=include_tasks,
                thinking=self.thinking,
            )
        )
        _reload_context_with_defaults(context)
        delivery = compiled_delivery_evidence(
            context,
            agent_name=self.agent_name,
            runtime_config=self.runtime_config,
            include_tasks=include_tasks,
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
        context.services.record(
            "task_guidance.planning",
            {
                "variant": variant,
                "include_tasks": include_tasks,
                "thinking": self.thinking,
            },
        )
        context.services.record("task_guidance.delivery", delivery)
        context.add_message("user", prompt)
        outcome = context.request(stream=True)
        calls = tuple(collect_tool_calls(context.session))
        metrics = tool_metrics(calls)
        context.services.record("task_guidance.tool_metrics", metrics)
        return PlanningRunValue(
            prompt=prompt,
            response=outcome.final_response,
            variant=variant,
            completed=outcome.completed,
            cancelled=outcome.cancelled,
            errors=outcome.error_messages,
            duration_seconds=outcome.duration_seconds,
            tool_event_count=outcome.tool_event_count,
            mutation_count=outcome.mutation_count,
            tool_calls=calls,
            tool_metrics=metrics,
            delivery=delivery,
        )

    def _from_plan_turn(
        self,
        context: CrystalLatticeContext,
        *,
        scenario: TaskGuidanceScenario,
        variant: str,
        reasoning_effort: str,
    ) -> TaskRunValue:
        if context.workspace is None:
            raise ValueError("missing task-guidance workspace")
        if context.session_or_none is None:
            raise ValueError("from-plan turn continues a planning session")
        prompt = FROM_PLAN_PROMPTS[variant]
        # The planning turn's overrides are stored on the session; this
        # update shallow-merges over them, flipping include_tasks back on
        # for the writing turn whatever the planning arm was.
        context.config.update(
            request_overrides(
                self.agent_name,
                context.workspace,
                reasoning_effort=reasoning_effort,
                thinking=self.thinking,
            )
        )
        _reload_context_with_defaults(context)
        delivery = compiled_delivery_evidence(
            context,
            agent_name=self.agent_name,
            runtime_config=self.runtime_config,
        )
        parent_message_count = len(context.session.messages)
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
        context.services.record(
            "task_guidance.from_plan",
            {
                "variant": variant,
                "parent_messages": parent_message_count,
                "thinking": self.thinking,
            },
        )
        context.services.record("task_guidance.delivery", delivery)
        context.add_message("user", prompt)
        outcome = context.request(stream=True)
        task_files = _workspace_task_files(context.workspace)
        calls = tuple(
            call
            for call in collect_tool_calls(context.session)
            if int(call.get("message_index", -1)) >= parent_message_count
        )
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
            prompt=prompt,
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
        outcome = context.request(stream=True)
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
        outcome = context.request(stream=True)
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


def _selected_provider(agent_name: str) -> str:
    """The provider connection an agent resolves to (configuration env)."""

    if agent_name != "glm":
        return "openai"
    raw = os.getenv("TASK_GUIDANCE_GLM_PROVIDER") or AGENTS[agent_name].get("provider")
    return str(raw or "").lower()


def request_overrides(
    agent_name: str,
    workspace: Path,
    *,
    reasoning_effort: str,
    include_tasks: bool = True,
    thinking: str = "default",
) -> dict[str, object]:
    """Per-request settings layered over the agent's pinned runtime config.

    The runtime config fixture pins the plugin wiring and the
    authentication method; only the model, the workspace, the guidance
    toggles, the reasoning-effort shape, and the reasoning-state variant
    vary per request. Preserve is a request option on zai (the provider
    keeps reasoning server-side when ``clear_thinking`` is false);
    ollama preserves by default and strips through the config-variant
    plugin, so no request option applies there.
    """

    if thinking not in THINKING_VARIANTS:
        raise ValueError(f"unknown thinking variant {thinking!r}")
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
        options: dict[str, object] = {"reasoning_effort": reasoning_effort}
        if thinking == "preserve" and _selected_provider(agent_name) == "zai":
            options["thinking"] = {"type": "enabled", "clear_thinking": False}
        values["request_options"] = options
    else:
        values["reasoning_effort"] = reasoning_effort
        values["reasoning_summary"] = "detailed"
    return values


def compiled_delivery_evidence(
    context: CrystalLatticeContext,
    *,
    agent_name: str,
    runtime_config: Path,
    include_tasks: bool = True,
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
        "include_tasks": include_tasks,
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
