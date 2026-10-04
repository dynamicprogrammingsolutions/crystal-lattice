"""One-command parallel runner for the task-guidance evaluation.

Runs the whole evaluation (or any slice) with a single command instead
of one pytest invocation per stage::

    python -m suites.task_guidance.run --label b1v4-r1
    python -m suites.task_guidance.run --label b1v4-r1 \\
        --stages task-creation,handoff-plan --scenarios tg01,tg02
    python -m suites.task_guidance.run --label probe --dry-run

Cases, prompts, validity checks, and records come from the same shared
recipes the parametrized live tests use (:mod:`evaluation.execution`),
so the CLI path and the pytest path cannot drift. Execution respects
every stage dependency by construction: stage groups run in dependency
order (independent producers first, dependent stages next, assessments
last, reading the records the earlier groups wrote under the same
label), and within a group every case may run in parallel up to the
configured per-agent maximum parallelism.

Per-agent parallelism comes from a JSON file mapping agent names to
maximum concurrency (for example ``{"glm": 2, "gpt": 4}``), given with
``--parallelism``; without it each agent runs serially while different
agents still run concurrently. Raise a agent's cap only after verifying
its run machinery tolerates concurrent runs under one label.
"""

from __future__ import annotations

import argparse
import json
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from pathlib import Path
from typing import Mapping

from .configuration import AGENTS, selected_artifact_root, selected_bundle
from .evaluation import execution
from .evaluation.matrix import (
    continuation_cases,
    file_fidelity_cases,
    file_readability_cases,
    generated_plan_cases,
    handoff_assessment_cases,
    handoff_plan_cases,
    negative_control_cases,
    plan_content_cases,
    planning_session_cases,
    task_creation_assessment_cases,
    task_creation_cases,
    task_creation_from_plan_cases,
)
from .runner import TaskGuidanceHarness

# Stage groups in dependency order: every group only needs the records
# (or in-process runs) of the groups before it.
STAGE_GROUPS: tuple[tuple[str, ...], ...] = (
    ("task-creation", "planning-session", "handoff-plan", "negative-control"),
    ("task-creation-from-plan", "continuation", "generated-plan"),
    (
        "task-creation-assessment",
        "handoff-assessment",
        "plan-content-assessment",
        "file-fidelity-assessment",
        "file-readability-assessment",
    ),
)
ALL_STAGES: tuple[str, ...] = tuple(stage for group in STAGE_GROUPS for stage in group)

_STAGE_EXECUTORS = {
    "task-creation": execution.execute_task_creation,
    "planning-session": execution.execute_planning_session,
    "task-creation-from-plan": execution.execute_task_creation_from_plan,
    "handoff-plan": execution.execute_handoff_plan,
    "continuation": execution.execute_continuation,
    "generated-plan": execution.execute_generated_plan,
    "negative-control": execution.execute_negative_control,
    "task-creation-assessment": execution.execute_task_creation_assessment,
    "handoff-assessment": execution.execute_handoff_assessment,
    "plan-content-assessment": execution.execute_plan_content_assessment,
    "file-fidelity-assessment": execution.execute_file_fidelity_assessment,
    "file-readability-assessment": execution.execute_file_readability_assessment,
}

_STAGE_CASES = {
    "task-creation": task_creation_cases,
    "planning-session": planning_session_cases,
    "task-creation-from-plan": task_creation_from_plan_cases,
    "handoff-plan": handoff_plan_cases,
    "continuation": continuation_cases,
    "generated-plan": generated_plan_cases,
    "negative-control": negative_control_cases,
    "task-creation-assessment": task_creation_assessment_cases,
    "handoff-assessment": handoff_assessment_cases,
    "plan-content-assessment": plan_content_cases,
    "file-fidelity-assessment": file_fidelity_cases,
    "file-readability-assessment": file_readability_cases,
}


@dataclass(frozen=True)
class CaseOutcome:
    stage: str
    case_id: str
    agent: str
    status: str  # ok | skipped | failed
    detail: str = ""


def selected_stages(requested: str) -> tuple[str, ...]:
    """Expand a stage selection into dependency-safe ordered stages."""

    if requested == "all":
        return ALL_STAGES
    wanted = [item.strip() for item in requested.split(",") if item.strip()]
    unknown = [stage for stage in wanted if stage not in ALL_STAGES]
    if unknown:
        raise SystemExit(f"unknown stages: {unknown}; known: {list(ALL_STAGES)}")
    # Keep only the requested stages, but preserve dependency order.
    return tuple(stage for stage in ALL_STAGES if stage in wanted)


def plan_cases(
    stages: tuple[str, ...],
    *,
    scenarios: set[str] | None = None,
    agents: set[str] | None = None,
) -> list[tuple[str, object]]:
    """Every (stage, case) to run, in stage-group order."""

    jobs: list[tuple[str, object]] = []
    for stage in stages:
        for case in _STAGE_CASES[stage]():
            if scenarios is not None and case.scenario_id not in scenarios:
                continue
            if stage in {
                "task-creation-assessment",
                "file-fidelity-assessment",
                "file-readability-assessment",
            }:
                job_agent = _assessment_agent(case)
            else:
                job_agent = case.agent
            if agents is not None and job_agent not in agents:
                continue
            jobs.append((stage, case))
    return jobs


def _assessment_agent(case) -> str:
    from .configuration import assessment_cell
    from .scenarios import scenario_by_id

    scenario = scenario_by_id(case.scenario_id)
    judge, _effort = assessment_cell(
        scenario.category, _assessment_stage_for(case.stage)
    )
    return judge


_ASSESSMENT_STAGE_NAMES = {
    "task-creation-assessment": "task-creation-assessment",
    "handoff-assessment": "handoff-assessment",
    "plan-content-assessment": "plan-content-assessment",
    "file-fidelity-assessment": "file-fidelity-assessment",
    "file-readability-assessment": "file-readability-assessment",
}


def _assessment_stage_for(stage: str) -> str:
    return _ASSESSMENT_STAGE_NAMES[stage]


def load_parallelism(path: Path | None) -> dict[str, int]:
    """Per-agent maximum concurrency; absent agents run serially."""

    if path is None:
        return {agent: 1 for agent in AGENTS}
    config = json.loads(path.read_text(encoding="utf-8"))
    caps: dict[str, int] = {}
    for agent, value in config.items():
        if agent not in AGENTS:
            raise SystemExit(f"unknown agent in parallelism config: {agent!r}")
        cap = int(value)
        if cap < 1:
            raise SystemExit(f"parallelism for {agent!r} must be >= 1")
        caps[agent] = cap
    return {agent: caps.get(agent, 1) for agent in AGENTS}


def run_evaluation(
    *,
    label: str,
    stages: tuple[str, ...],
    scenarios: set[str] | None,
    agents: set[str] | None,
    fresh: bool,
    samples: int,
    parallelism: Mapping[str, int],
    dry_run: bool = False,
) -> list[CaseOutcome]:
    """Execute every selected case, honoring per-agent parallelism."""

    jobs = plan_cases(stages, scenarios=scenarios, agents=agents)
    if dry_run:
        return [
            CaseOutcome(
                stage=stage,
                case_id=case.id,
                agent=_job_agent(stage, case),
                status="dry-run",
            )
            for stage, case in jobs
        ]

    options = {"fresh": fresh, "samples": samples}
    harnesses: dict[tuple[str, str], TaskGuidanceHarness] = {}
    harness_lock = threading.Lock()

    def harness_factory(
        agent_name: str, *, thinking: str = "default"
    ) -> TaskGuidanceHarness:
        key = (agent_name, thinking)
        with harness_lock:
            if key not in harnesses:
                harnesses[key] = TaskGuidanceHarness(
                    agent_name,
                    label=label,
                    thinking=thinking,
                )
            return harnesses[key]

    semaphores = {
        agent: threading.Semaphore(max(1, int(parallelism.get(agent, 1))))
        for agent in AGENTS
    }
    outcomes: list[CaseOutcome] = []
    outcomes_lock = threading.Lock()

    def run_job(stage: str, case) -> CaseOutcome:
        executor = _STAGE_EXECUTORS[stage]
        agent = _job_agent(stage, case)
        semaphore = semaphores[agent]
        semaphore.acquire()
        try:
            executor(harness_factory, label, options, case)
        except execution.CaseSkipped as skip:
            return CaseOutcome(stage, case.id, agent, "skipped", str(skip))
        except Exception as error:  # noqa: BLE001 - report, keep other cases
            return CaseOutcome(
                stage, case.id, agent, "failed", f"{type(error).__name__}: {error}"
            )
        finally:
            semaphore.release()
        return CaseOutcome(stage, case.id, agent, "ok")

    max_workers = max(1, sum(int(parallelism.get(agent, 1)) for agent in AGENTS))
    with ThreadPoolExecutor(max_workers=max_workers) as pool:
        futures = [
            (stage, case, pool.submit(run_job, stage, case)) for stage, case in jobs
        ]
        for stage, case, future in futures:
            outcome = future.result()
            with outcomes_lock:
                outcomes.append(outcome)
            marker = {"ok": ".", "skipped": "s", "failed": "F"}[outcome.status]
            print(f"{marker} {outcome.stage}:{outcome.case_id}", flush=True)
            if outcome.status == "failed":
                print(f"    {outcome.detail}", flush=True)

    for harness in harnesses.values():
        harness.close()
    return outcomes


def _job_agent(stage: str, case) -> str:
    if stage in _ASSESSMENT_STAGE_NAMES:
        return _assessment_agent(case)
    return case.agent


def _parse_set(raw: str | None) -> set[str] | None:
    if raw is None:
        return None
    return {item.strip() for item in raw.split(",") if item.strip()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m suites.task_guidance.run",
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--label", required=True, help="run label for provenance")
    parser.add_argument(
        "--stages",
        default="all",
        help="comma-separated stages, or 'all' (dependency order is preserved)",
    )
    parser.add_argument(
        "--scenarios", default=None, help="comma-separated scenario ids"
    )
    parser.add_argument("--agents", default=None, help="comma-separated agent names")
    parser.add_argument(
        "--fresh", action="store_true", help="re-execute cached requests"
    )
    parser.add_argument(
        "--samples", type=int, default=1, help="variance samples per request"
    )
    parser.add_argument(
        "--parallelism",
        type=Path,
        default=None,
        help="JSON file mapping agent names to maximum concurrency",
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="list cases without running"
    )
    args = parser.parse_args(argv)

    stages = selected_stages(args.stages)
    scenarios = _parse_set(args.scenarios)
    agents = _parse_set(args.agents)
    if agents is not None:
        unknown = [agent for agent in agents if agent not in AGENTS]
        if unknown:
            raise SystemExit(f"unknown agents: {unknown}; known: {list(AGENTS)}")
    parallelism = load_parallelism(args.parallelism)

    print(f"bundle: {selected_bundle()}")
    print(f"artifacts: {selected_artifact_root()}")
    print(f"label: {args.label} | stages: {', '.join(stages)}")
    print(f"parallelism: {parallelism}")

    outcomes = run_evaluation(
        label=args.label,
        stages=stages,
        scenarios=scenarios,
        agents=agents,
        fresh=args.fresh,
        samples=args.samples,
        parallelism=parallelism,
        dry_run=args.dry_run,
    )

    counts: dict[str, int] = {}
    for outcome in outcomes:
        counts[outcome.status] = counts.get(outcome.status, 0) + 1
    print(
        f"\n{len(outcomes)} cases: "
        + ", ".join(f"{count} {status}" for status, count in sorted(counts.items()))
    )
    return 1 if counts.get("failed") else 0


if __name__ == "__main__":
    sys.exit(main())
