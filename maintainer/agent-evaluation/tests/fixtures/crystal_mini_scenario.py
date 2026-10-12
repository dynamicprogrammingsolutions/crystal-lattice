"""Crystal-lattice mini-evaluation: the run model over the real runtime.

The fixture emulates a realistic evaluation shape — a small workspace
under evaluation whose AGENTS.md carries the guidance candidate, a matrix
over agents and scenarios, per-subject assessments, and a mini freeze —
while every run flows through the real Crystal Lattice runtime and the
reusable run model.

Provider labor is divided strictly: the deterministic echo agent answers
everything that needs only a simple response (the no-tool producer
scenario and every per-subject assessment), while the local Ollama models
own every tool call, producing the file-writing scenarios through the
real tool loop with the core read/write tools.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Sequence

from agent_eval import AgentEval, Run
from agent_eval.crystal_lattice import (
    CrystalLatticeContext,
    CrystalLatticeEnvironment,
    CrystalRequestOutcome,
)
from agent_eval.runner import (
    RunModel,
    cell_statistics,
    completeness,
    render_selection,
    request_identity,
    select_cell_records,
)

REPOSITORY_ROOT = Path(__file__).resolve().parents[4]
EVALUATION_ROOT = Path(__file__).resolve().parents[2]
MINI_PLUGIN_CACHE = Path(tempfile.gettempdir()) / "agent-eval-mini-plugin-cache"
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434/v1"

PRODUCER_RECORD_NAME = "mini-crystal-producer.json"
ASSESSMENT_RECORD_NAME = "mini-crystal-assessment.json"

# The evaluated candidate: the guidance rule carried by the workspace.
MINI_GUIDANCE = """# Mini workspace guidance

Every task file starts with `Status: proposed`.
"""

PLANTED_DEFECT = "LIMIT = 10"
FIXED_DEFECT = "LIMIT = 5"

ECHO_AGENT = "echo"
OLLAMA_AGENTS = ("qwen35", "qwen3")
ECHO_SCENARIO = "mini-answer"
TOOL_SCENARIOS = ("mini-task", "mini-fix")

SCENARIO_PROMPTS: dict[str, str] = {
    ECHO_SCENARIO: "Describe the defect in src/app.py in one sentence.",
    "mini-task": (
        "Create the file tasks/fix.md describing the defect in src/app.py "
        "in one sentence. Follow the workspace guidance in AGENTS.md for "
        "how task files must start. Use the write_file tool with the "
        "relative path tasks/fix.md (the working directory is the "
        "repository root)."
    ),
    "mini-fix": (
        "The constant LIMIT in src/app.py is wrong: it must be 5. Read "
        "src/app.py, then fix it. Use the read_file and write_file tools "
        "with relative paths (the working directory is the repository "
        "root)."
    ),
}

ASSESS_PROMPT = (
    "You are assessing a produced artifact against the workspace guidance.\n\n"
    "Guidance rule: every task file starts with 'Status: proposed'.\n\n"
    "Subject:\n{subject}\n\n"
    "Reply with VERDICT: pass or VERDICT: fail and one reason."
)


@dataclass(frozen=True)
class MiniAgent:
    """Declared fixture agent: the configuration the matrix derives from."""

    name: str
    model: str
    provider: str
    tools: bool
    scenarios: tuple[str, ...]


MINI_AGENTS: dict[str, MiniAgent] = {
    "echo": MiniAgent(
        name="echo",
        model="mini-echo-v1",
        provider="echo",
        tools=False,
        scenarios=(ECHO_SCENARIO,),
    ),
    "qwen35": MiniAgent(
        name="qwen35",
        model="qwen3.5:0.8b",
        provider="ollama",
        tools=True,
        scenarios=TOOL_SCENARIOS,
    ),
    "qwen3": MiniAgent(
        name="qwen3",
        model="qwen3:0.6b",
        provider="ollama",
        tools=True,
        scenarios=TOOL_SCENARIOS,
    ),
}

ASSESSOR_AGENT = ECHO_AGENT


@dataclass(frozen=True)
class MiniCrystalValue:
    """One crystal-lattice turn; provider failures surface as errors."""

    prompt: str
    response: str
    completed: bool
    errors: tuple[str, ...]
    tool_event_count: int
    valid: bool
    reasons: tuple[str, ...]
    checks: Mapping[str, bool]
    guidance_sha256: str


def guidance_sha256(guidance: str) -> str:
    return hashlib.sha256(guidance.encode("utf-8")).hexdigest()


def produce_identity(agent: MiniAgent, *, scenario: str, guidance: str) -> str:
    return request_identity(
        namespace="mini-crystal-evaluation",
        version="v1",
        components={
            "stage": "produce",
            "agent": agent.name,
            "model": agent.model,
            "scenario": scenario,
            "prompt": SCENARIO_PROMPTS[scenario],
            "guidance_sha256": guidance_sha256(guidance),
        },
    )


def assess_identity(*, subject_response: str) -> str:
    assessor = MINI_AGENTS[ASSESSOR_AGENT]
    return request_identity(
        namespace="mini-crystal-evaluation",
        version="v1",
        components={
            "stage": "assess",
            "agent": assessor.name,
            "model": assessor.model,
            "subject_sha256": hashlib.sha256(
                subject_response.encode("utf-8")
            ).hexdigest(),
        },
    )


def producer_cell(record: Mapping[str, Any]) -> str:
    return f"{record['scenario']}:{record['agent']}"


def expected_produce_cells(agents: Sequence[str]) -> set[str]:
    """The mini matrix, derived from the fixture configuration."""

    return {
        f"{scenario}:{MINI_AGENTS[name].name}"
        for name in agents
        for scenario in MINI_AGENTS[name].scenarios
    }


def mini_workspace_factory(staging: Path, *, guidance: str = MINI_GUIDANCE) -> Path:
    """Create the tiny repository under evaluation in the staging area."""

    staging.mkdir(parents=True, exist_ok=True)
    (staging / "AGENTS.md").write_text(guidance, encoding="utf-8")
    (staging / "tasks").mkdir(exist_ok=True)
    (staging / "tasks" / "seed.md").write_text(
        "Status: proposed\n\nSeed task.\n", encoding="utf-8"
    )
    (staging / "src").mkdir(exist_ok=True)
    (staging / "src" / "app.py").write_text(f"{PLANTED_DEFECT}\n", encoding="utf-8")
    return staging


def derive_validity(
    scenario: str,
    workspace: Path,
    outcome: CrystalRequestOutcome,
) -> tuple[bool, tuple[str, ...], dict[str, bool]]:
    """Derive validity from the workspace state after the request."""

    checks: dict[str, bool] = {
        "completed": outcome.completed,
        "no_errors": not outcome.error_messages,
    }
    if scenario == ECHO_SCENARIO:
        checks["responded"] = bool(outcome.final_response)
    elif scenario == "mini-task":
        task_file = workspace / "tasks" / "fix.md"
        content = task_file.read_text(encoding="utf-8") if task_file.is_file() else ""
        checks["task_file_created"] = task_file.is_file()
        checks["guidance_followed"] = content.startswith("Status: proposed")
    elif scenario == "mini-fix":
        content = (workspace / "src" / "app.py").read_text(encoding="utf-8")
        checks["defect_fixed"] = FIXED_DEFECT in content
    else:
        raise ValueError(f"unknown mini scenario: {scenario!r}")
    valid = all(checks.values())
    reasons = tuple(name for name, passed in checks.items() if not passed)
    return valid, reasons, checks


def verdict_from_response(response: str) -> str:
    marker = "VERDICT: "
    index = response.find(marker)
    if index < 0:
        return "unparsed"
    verdict = response[index + len(marker) :].split(":", 1)[0].strip().lower()
    return verdict or "unparsed"


def mini_environment_values(*, include_ollama: bool) -> dict[str, str]:
    values: dict[str, str] = {}
    if include_ollama:
        values.update(
            {
                "BUILTIN_PLUGINS": str(REPOSITORY_ROOT / "plugins"),
                "PIP_CONSTRAINT": str(
                    EVALUATION_ROOT / "constraints" / "plugin-runtime.txt"
                ),
                "OLLAMA_OPENAI_BASE_URL": os.environ.get(
                    "OLLAMA_OPENAI_BASE_URL", DEFAULT_OLLAMA_BASE_URL
                ),
            }
        )
    return values


def write_mini_config(config_path: Path, *, agents: Sequence[str]) -> None:
    include_ollama = any(MINI_AGENTS[name].provider == "ollama" for name in agents)
    providers: dict[str, object] = {
        "echo": {
            "provider": "agent_eval_test_provider",
            "model": MINI_AGENTS[ECHO_AGENT].model,
        },
    }
    plugins: list[str] = [
        "fixtures.crystal_plugins.EvaluationProvider",
        "fixtures.crystal_plugins.GuidanceSystemMessage",
    ]
    if include_ollama:
        providers["ollama"] = {
            "provider": "reference_openai_compatible",
            "base_url": "${env:OLLAMA_OPENAI_BASE_URL}",
            "model": MINI_AGENTS["qwen3"].model,
            "reasoning_field": "reasoning",
            "timeout": 120,
        }
        plugins.append(
            "path:${env:BUILTIN_PLUGINS}/reference-openai-compatible-provider"
        )
    agents_config: dict[str, object] = {}
    for name in agents:
        spec = MINI_AGENTS[name]
        agent_config: dict[str, object] = {
            "provider": spec.provider,
            "model": spec.model,
        }
        if spec.tools:
            agent_config["plugins"] = [
                "plugins.file_reader_tool.FileReaderTool",
                "plugins.file_writer_tool.FileWriterTool",
            ]
        agents_config[name] = agent_config
    config = {
        "plugin_cache_dir": str(MINI_PLUGIN_CACHE),
        # The evaluation runtime never lists sessions, and the derived
        # session-list cache is the runtime's only SQLite user; keeping
        # it off keeps forked isolated workers free of SQLite state.
        "application": {
            "cached_background_session_list": {
                "persistent_cache_enabled": False,
            }
        },
        "providers": providers,
        "plugins": plugins,
        "agents": agents_config,
    }
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(json.dumps(config, indent=2), encoding="utf-8")


class MiniCrystalHarness:
    """Mini evaluation harness: suite-shaped glue over the run model."""

    def __init__(
        self,
        artifact_root: Path,
        *,
        agents: Sequence[str] = (ECHO_AGENT,),
        label: str | None = None,
        guidance: str = MINI_GUIDANCE,
    ) -> None:
        self.artifact_root = artifact_root
        self.agents = tuple(agents)
        self.guidance = guidance
        self.config_path = artifact_root / "config.json"
        include_ollama = any(
            MINI_AGENTS[name].provider == "ollama" for name in self.agents
        )
        write_mini_config(self.config_path, agents=self.agents)
        self.environment = CrystalLatticeEnvironment.from_config(
            self.config_path,
            environment=mini_environment_values(include_ollama=include_ollama),
        )
        self.evaluation = AgentEval(
            default_environment=self.environment,
            artifact_root=artifact_root / "artifacts",
            cache_root=artifact_root / "cache",
        )
        self.model = RunModel(self.evaluation, label=label)

    def close(self) -> None:
        self.evaluation.close()

    def produce(
        self,
        *,
        agent: str,
        scenario: str,
        fresh: bool = False,
        mode: str = "echo",
        response_text: str | None = None,
        error_message: str | None = None,
    ) -> Run[MiniCrystalValue]:
        spec = MINI_AGENTS[agent]
        if scenario not in spec.scenarios:
            raise ValueError(
                f"scenario {scenario!r} is not declared for agent {agent!r}"
            )
        identity = produce_identity(spec, scenario=scenario, guidance=self.guidance)
        name = f"mini-crystal-produce-{scenario}-{agent}"

        def program(context: CrystalLatticeContext) -> MiniCrystalValue:
            context.start(agent)
            overrides: dict[str, object] = {
                "model": spec.model,
                "guidance_file": str(context.workspace / "AGENTS.md"),
            }
            if spec.provider == "echo":
                overrides["response_mode"] = mode
                if response_text is not None:
                    overrides["response_text"] = response_text
                if error_message is not None:
                    overrides["error_message"] = error_message
            if spec.tools:
                overrides["working_directory"] = str(context.workspace)
                overrides["allowed_paths"] = [str(context.workspace)]
            context.config.update(overrides)
            context.add_message("user", SCENARIO_PROMPTS[scenario])
            outcome = context.request()
            valid, reasons, checks = derive_validity(
                scenario, context.workspace, outcome
            )
            return MiniCrystalValue(
                prompt=SCENARIO_PROMPTS[scenario],
                response=outcome.final_response,
                completed=outcome.completed,
                errors=tuple(outcome.error_messages),
                tool_event_count=outcome.tool_event_count,
                valid=valid,
                reasons=reasons,
                checks=checks,
                guidance_sha256=guidance_sha256(self.guidance),
            )

        def workspace_factory(staging: Path) -> Path:
            return mini_workspace_factory(staging, guidance=self.guidance)

        run = self.model.run(
            name,
            program,
            identity=identity,
            workspace=workspace_factory,
            fresh=fresh,
        )
        run.record(
            PRODUCER_RECORD_NAME,
            {
                "schema": 1,
                "stage": "produce",
                "scenario": scenario,
                "agent": agent,
                "model": spec.model,
                "response": run.value.response,
                "completed": run.value.completed,
                "errors": list(run.value.errors),
                "tool_event_count": run.value.tool_event_count,
                "valid": run.value.valid,
                "reasons": list(run.value.reasons),
                "checks": dict(run.value.checks),
                "score": 1.0 if run.value.valid else 0.0,
            },
        )
        return run

    def assess(
        self,
        *,
        subject: Mapping[str, Any],
        verdict: str = "pass",
    ) -> Run[MiniCrystalValue]:
        cell = producer_cell(subject)
        subject_response = str(subject["response"])
        identity = assess_identity(subject_response=subject_response)
        name = f"mini-crystal-assess-{cell}"
        prompt = ASSESS_PROMPT.format(subject=subject_response)

        def program(context: CrystalLatticeContext) -> MiniCrystalValue:
            context.start(ASSESSOR_AGENT)
            context.config.update(
                {
                    "model": MINI_AGENTS[ASSESSOR_AGENT].model,
                    "guidance_file": str(context.workspace / "AGENTS.md"),
                    "response_text": (
                        f"VERDICT: {verdict}: the subject follows the "
                        "workspace guidance"
                    ),
                }
            )
            context.add_message("user", prompt)
            outcome = context.request()
            checks = {
                "completed": outcome.completed,
                "no_errors": not outcome.error_messages,
                "responded": bool(outcome.final_response),
            }
            return MiniCrystalValue(
                prompt=prompt,
                response=outcome.final_response,
                completed=outcome.completed,
                errors=tuple(outcome.error_messages),
                tool_event_count=outcome.tool_event_count,
                valid=all(checks.values()),
                reasons=tuple(name for name, passed in checks.items() if not passed),
                checks=checks,
                guidance_sha256=guidance_sha256(self.guidance),
            )

        def workspace_factory(staging: Path) -> Path:
            return mini_workspace_factory(staging, guidance=self.guidance)

        run = self.model.run(
            name,
            program,
            identity=identity,
            workspace=workspace_factory,
        )
        parsed = verdict_from_response(run.value.response)
        run.record(
            ASSESSMENT_RECORD_NAME,
            {
                "schema": 1,
                "stage": "assess",
                "subject_cell": cell,
                "prompt": prompt,
                "response": run.value.response,
                "completed": run.value.completed,
                "verdict": parsed,
                "score": 1.0 if parsed == "pass" else 0.0,
            },
        )
        return run


def freeze_mini_dataset(
    artifact_root: Path,
    *,
    agents: Sequence[str],
    labels: Sequence[str] | None = None,
) -> dict[str, Any]:
    """Mini freeze adapter: consolidation over the produced records."""

    cells = select_cell_records(
        artifact_root,
        record_name=PRODUCER_RECORD_NAME,
        cell_identity=producer_cell,
        labels=labels,
    )
    statistics = cell_statistics(cells, metric=lambda value: value["score"])
    status = completeness(expected_produce_cells(agents), cells)
    return {
        "schema": 1,
        "labels": list(labels) if labels is not None else None,
        "selection": render_selection(cells),
        "statistics": statistics,
        "completeness": status,
    }


def render_mini_report(dataset: Mapping[str, Any]) -> str:
    status = dataset["completeness"]
    lines = [
        "# Mini crystal-lattice evaluation",
        "",
        str(dataset["selection"]),
        "",
        (
            f"expected: {status['expected']} present: {status['present']} "
            f"missing: {len(status['missing'])}"
        ),
        "",
    ]
    for cell, statistics in sorted(dataset["statistics"].items()):
        lines.append(
            f"- {cell}: mean={statistics['mean']:.2f} "
            f"count={statistics['count']} spread={statistics['spread']:.2f}"
        )
    return "\n".join(lines)
