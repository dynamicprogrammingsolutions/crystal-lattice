"""Fixture mini-evaluation: a small suite built on the run-model layer.

The fixture emulates a realistic evaluation shape — a matrix of producer
cells over two agents and two scenarios, a per-subject assessment stage, and
deterministic echo "models" with injectable provider failures — while every
run flows through the reusable run model. It exists so the layer's mechanism
(labels, request identity, samples, natural retries, consolidation) can be
verified end-to-end in short-running tests without any real model.
"""

from __future__ import annotations

import hashlib
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

from agent_eval import AgentEval, Run, RunEnvironment, RunServices
from agent_eval.runner import RunModel, request_identity


PRODUCE_PROMPT = "produce the mini artifact"
ASSESS_PROMPT = "assess the mini artifact"
PRODUCER_RECORD_NAME = "mini-producer.json"
ASSESSMENT_RECORD_NAME = "mini-assessment.json"


@dataclass(frozen=True)
class MiniAgent:
    """Declared fixture agent: the configuration the matrix derives from."""

    name: str
    model: str
    efforts: tuple[str, ...]


MINI_AGENTS: dict[str, MiniAgent] = {
    "alpha": MiniAgent(name="alpha", model="echo-alpha", efforts=("low", "high")),
    "beta": MiniAgent(name="beta", model="echo-beta", efforts=("low",)),
}
MINI_SCENARIOS: tuple[str, ...] = ("mini-one", "mini-two")
ASSESSOR_AGENT = "alpha"


@dataclass(frozen=True)
class EchoValue:
    """Completed echo turn; provider failures surface as value errors."""

    prompt: str
    response: str
    completed: bool
    errors: tuple[str, ...]
    request_count: int


class EchoContext:
    def __init__(
        self,
        services: RunServices,
        *,
        agent: str,
        request_count: int,
        failures: list[str],
    ) -> None:
        self.services = services
        self.agent = agent
        self.request_count = request_count
        self.failures = failures

    def respond(self, prompt: str) -> EchoValue:
        self.services.record("echo.request", {"agent": self.agent, "prompt": prompt})
        if self.failures:
            return EchoValue(
                prompt=prompt,
                response="",
                completed=False,
                errors=(self.failures.pop(0),),
                request_count=self.request_count,
            )
        return EchoValue(
            prompt=prompt,
            response=f"echo:{self.agent}:{prompt}#{self.request_count}",
            completed=True,
            errors=(),
            request_count=self.request_count,
        )


class EchoEnvironment(RunEnvironment[EchoContext]):
    """Deterministic echo provider with injectable provider failures.

    ``request_count`` increments once per genuine execution, so repeated
    executions of the same request yield different responses — the echo
    equivalent of model nondeterminism. Cache replays never open the
    environment and therefore never increment it.
    """

    def __init__(self, *, agent: str, failures: Sequence[str] = ()) -> None:
        self.agent = agent
        self.failures = list(failures)
        self.request_count = 0

    def fingerprint(self) -> object:
        return {"type": "echo", "agent": self.agent, "schema": 1}

    @contextmanager
    def open(
        self,
        *,
        services: RunServices,
        workspace: Path | None,
        parent_snapshot: object | None,
    ) -> Iterator[EchoContext]:
        self.request_count += 1
        yield EchoContext(
            services,
            agent=self.agent,
            request_count=self.request_count,
            failures=self.failures,
        )

    def snapshot(self, context: EchoContext) -> object | None:
        return None

    def finalize(self, context: EchoContext) -> object:
        return {"agent": self.agent, "request_count": context.request_count}


def produce_identity(agent: MiniAgent, *, scenario: str, effort: str) -> str:
    return request_identity(
        namespace="mini-evaluation",
        version="v1",
        components={
            "stage": "produce",
            "agent": agent.name,
            "model": agent.model,
            "scenario": scenario,
            "effort": effort,
            "prompt": PRODUCE_PROMPT,
        },
    )


def assess_identity(*, subject_response: str) -> str:
    assessor = MINI_AGENTS[ASSESSOR_AGENT]
    return request_identity(
        namespace="mini-evaluation",
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
    return f"{record['scenario']}:{record['agent']}:{record['effort']}"


def expected_produce_cells() -> set[str]:
    """The mini matrix, derived from the fixture configuration."""

    return {
        f"{scenario}:{agent.name}:{effort}"
        for scenario in MINI_SCENARIOS
        for agent in MINI_AGENTS.values()
        for effort in agent.efforts
    }


class MiniHarness:
    """Fixture evaluation harness: suite-shaped glue over the run model."""

    def __init__(
        self,
        artifact_root: Path,
        *,
        label: str | None = None,
        failures: Mapping[str, Sequence[str]] | None = None,
        environments: Mapping[str, EchoEnvironment] | None = None,
    ) -> None:
        self.artifact_root = artifact_root
        # Shared environments let later batches continue the echo counters,
        # emulating model nondeterminism across invocations.
        self.environments = (
            dict(environments)
            if environments
            else {
                name: EchoEnvironment(
                    agent=name,
                    failures=(failures or {}).get(name, ()),
                )
                for name in MINI_AGENTS
            }
        )
        self.evaluation = AgentEval(
            default_environment=self.environments[ASSESSOR_AGENT],
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
        effort: str,
        fresh: bool = False,
        samples: int = 1,
    ) -> tuple[Run[EchoValue], ...]:
        spec = MINI_AGENTS[agent]
        if effort not in spec.efforts:
            raise ValueError(f"effort {effort!r} is not declared for {agent!r}")
        identity = produce_identity(spec, scenario=scenario, effort=effort)
        name = f"mini-produce-{scenario}-{agent}-{effort}"

        def program(context: EchoContext) -> EchoValue:
            return context.respond(
                f"{PRODUCE_PROMPT}|scenario={scenario}|effort={effort}"
            )

        if samples > 1:
            runs = self.model.run_samples(
                name,
                program,
                identity=identity,
                count=samples,
                environment=self.environments[agent],
            )
        else:
            runs = (
                self.model.run(
                    name,
                    program,
                    identity=identity,
                    environment=self.environments[agent],
                    fresh=fresh,
                ),
            )
        for run in runs:
            run.record(
                PRODUCER_RECORD_NAME,
                {
                    "schema": 1,
                    "stage": "produce",
                    "scenario": scenario,
                    "agent": agent,
                    "effort": effort,
                    "model": spec.model,
                    "response": run.value.response,
                    "completed": run.value.completed,
                    "errors": list(run.value.errors),
                    "score": float(run.value.request_count),
                },
            )
        return runs

    def assess(self, *, subject: Mapping[str, Any]) -> Run[EchoValue]:
        cell = producer_cell(subject)
        identity = assess_identity(subject_response=str(subject["response"]))
        name = f"mini-assess-{cell}"

        def program(context: EchoContext) -> EchoValue:
            return context.respond(f"{ASSESS_PROMPT}|subject={subject['response']}")

        run = self.model.run(
            name,
            program,
            identity=identity,
            environment=self.environments[ASSESSOR_AGENT],
        )
        run.record(
            ASSESSMENT_RECORD_NAME,
            {
                "schema": 1,
                "stage": "assess",
                "subject_cell": cell,
                "response": run.value.response,
                "completed": run.value.completed,
                "score": float(run.value.request_count),
            },
        )
        return run
