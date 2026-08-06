# Agent evaluation framework product specification

## Purpose

Maintainers need to verify that an agent understands and applies instructions,
prompts, tools, skills, configuration, and repository context. These
evaluations often require an expensive repository investigation followed by
many cheaper continuations with different inputs.

The repository already has a task-guidance evaluator that demonstrates
conversation reuse, clean fork workspaces, exact prompt provenance,
deterministic assertions, empirical review, and human-readable artifacts. Its
current implementation is specialized and exposes too much scenario-specific
machinery to be reused comfortably.

The target is a small Python library with:

- a generic kernel for run identity, workspaces, caching, artifacts, parent
  relationships, and error preservation;
- one broad `RunEnvironment` replacement seam;
- a first `CrystalLatticeEnvironment` implementation;
- optional lower-level Crystal Lattice strategies for request execution,
  snapshots, evidence selection, evaluation, and presentation;
- ordinary Python and pytest as the evaluation language.

## Users

### Evaluation authors

Evaluation authors write ordinary Python and pytest tests. They need to:

- execute arbitrary test programs;
- use Crystal Lattice configuration, plugins, skills, providers, and tools
  without framework-specific prompt inputs;
- customize tool-loop execution, observation, and stopping;
- customize conversation snapshots and restoration;
- alter configuration before, during, and after requests;
- cache a costly investigation;
- fork many continuations from the same run;
- select exactly what evidence is given to an AI evaluator;
- return booleans, scores, rankings, issue lists, or arbitrary Python values;
- choose what is presented for manual review;
- replace the complete run environment when a non-Crystal-Lattice execution
  model is useful.

### Human and AI reviewers

Reviewers need compact deterministic artifacts containing the useful visible
interaction, primary outputs, tool activity, failures, assertions or scores,
and provenance selected for that audience.

They should not need to inspect multi-megabyte event streams or complete
runtime state during ordinary review. Raw evidence remains available for
diagnosis and reproduction.

### Framework maintainers

Framework maintainers need:

- a narrow generic kernel;
- one explicit environment contract rather than many speculative framework
  abstractions;
- deterministic tests around caching, forking, artifacts, and errors;
- a rich Crystal Lattice environment that remains internally customizable;
- the ability to add optional recipes only after repeated consumer patterns
  are observed;
- real consumers that demonstrate value without becoming mandatory framework
  semantics.

## Target experience

At the simplest level:

```python
run = evaluation.run(
    "simple-answer",
    exercise,
)
```

For repository reuse:

```python
run = evaluation.run(
    "mobile-specification-ownership",
    exercise,
    continue_from=repository_investigation,
)
```

For a different execution model:

```python
run = evaluation.run(
    "alternate-runtime",
    exercise,
    environment=alternate_environment,
)
```

The callback receives the context created by the selected environment. A
Crystal Lattice callback may use convenience methods or access the underlying
`AgentApplication`, `AgentCore`, session, and configuration directly.

The kernel does not ask whether text is guidance, a system message, a user
message, a skill, or a reviewer prompt. It also does not require a particular
tool loop, snapshot format, assertion style, scoring model, or manual report.

## Goals

- Provide a generic programmatic evaluation kernel.
- Use arbitrary Python execution callbacks rather than declarative scenarios.
- Make `RunEnvironment` the single broad replacement seam.
- Provide Crystal Lattice as the first complete environment.
- Keep all lower-level strategies optional and environment-specific.
- Support fresh runs, cached runs, and clean continuations from previous runs.
- Preserve exact compatibility and provenance for reused state.
- Support isolated repositories and arbitrary workspace factories.
- Return arbitrary Python values from an evaluation.
- Capture normalized observations and complete raw evidence.
- Produce audience-specific compact artifacts for human and AI review.
- Use pytest as the initial suite discovery, fixture, parametrization, and
  assertion framework.
- Verify the documentation-standard instructions as the first consumers.
- Preserve the existing task-guidance evaluator until its owning task adopts
  the library.

## Non-goals

- Defining a declarative YAML or TOML evaluation language.
- Defining `Case`, `Suite`, `Check`, `Reviewer`, `Score`, or `RunPolicy` as
  required public abstractions.
- Defining one universal agent, message, request, tool-loop, snapshot, or
  observation interface for every environment.
- Hardcoding prompt roles, instruction injection, guidance files, model
  selection, skills, tools, provider options, scoring, or review.
- Replacing Crystal Lattice configuration and plugins within the Crystal
  Lattice environment.
- Replacing pytest assertion semantics.
- Requiring every evaluation to return pass/fail.
- Treating model-based evaluation as deterministic proof or human approval.
- Building a general benchmark, leaderboard, dataset, or hosted evaluation
  service in the first version.
- Moving the existing task-guidance evaluator in this task.
- Running real-model suites as part of ordinary default package tests.

## Complete proposed usage examples

These examples define the intended usability of the public contract. Exact
module decomposition may change during implementation, but the examples should
remain possible without framework-specific evaluation DSLs.

### Example 1: simple Crystal Lattice response assertion

This is the lowest-customization path. The default environment owns
application lifecycle, normal request execution, default snapshotting, and
canonical artifacts. Pytest owns the assertion.

```python
from __future__ import annotations

from pathlib import Path

import pytest

from agent_eval import AgentEval
from agent_eval.crystal_lattice import (
    CrystalLatticeContext,
    CrystalLatticeEnvironment,
)


ROOT = Path(__file__).resolve().parents[3]


@pytest.fixture(scope="session")
def evaluation() -> AgentEval:
    environment = CrystalLatticeEnvironment.from_config(
        ROOT / "application/python/agent_terminal_app/default_config/config.json",
        environment={
            "BUILTIN_PLUGINS": str(ROOT / "plugins"),
        },
    )
    instance = AgentEval(
        default_environment=environment,
        artifact_root=ROOT / "tmp/agent-evaluation",
        cache_root=ROOT / "tmp/agent-evaluation/cache",
    )
    try:
        yield instance
    finally:
        instance.close()


@pytest.mark.agent_eval
def test_agent_explains_specification_target(
    evaluation: AgentEval,
) -> None:
    def exercise(context: CrystalLatticeContext) -> str:
        context.start("codex-openai")
        context.add_message(
            "user",
            (
                "Explain the difference between a target specification and "
                "a requirements ledger in two short paragraphs."
            ),
        )
        context.request()
        return context.final_response()

    run = evaluation.run(
        "explain-specification-target",
        exercise,
    )

    run.raise_for_error()

    answer = run.value.lower()
    assert "target" in answer
    assert "implementation" in answer
    assert "verification" in answer
```

### Example 2: cached repository investigation with customized Crystal Lattice execution

This example uses:

- a cached neutral repository investigation;
- a fresh continuation workspace;
- instructions placed in a user message;
- a custom request driver and stop condition;
- a custom snapshotter;
- separate AI and human evidence projections;
- structured model scoring;
- ordinary pytest assertions.

None of those choices changes the generic kernel.

```python
from __future__ import annotations

from pathlib import Path

import pytest
from pydantic import BaseModel, Field

from agent_eval import AgentEval, Run, git_workspace
from agent_eval.crystal_lattice import (
    CrystalLatticeContext,
    CrystalLatticeEnvironment,
    application_session_snapshot,
    application_tool_loop,
)


ROOT = Path(__file__).resolve().parents[3]

STANDARD_FILES = (
    ROOT / "docs/development/standards/documentation.md",
    ROOT / "docs/development/standards/specifications.md",
    ROOT / "docs/development/repository/documentation.md",
    ROOT / "docs/development/repository/specifications.md",
)


class DocumentationScore(BaseModel):
    ownership: int = Field(ge=1, le=5)
    target_vs_current: int = Field(ge=1, le=5)
    duplication_avoidance: int = Field(ge=1, le=5)
    explanation: str


@pytest.fixture(scope="session")
def evaluation() -> AgentEval:
    environment = CrystalLatticeEnvironment.from_config(
        ROOT / "application/python/agent_terminal_app/default_config/config.json",
        environment={
            "BUILTIN_PLUGINS": str(ROOT / "plugins"),
        },
    )
    instance = AgentEval(
        default_environment=environment,
        artifact_root=ROOT / "tmp/agent-evaluation",
        cache_root=ROOT / "tmp/agent-evaluation/cache",
    )
    try:
        yield instance
    finally:
        instance.close()


@pytest.fixture(scope="session")
def repository_investigation(
    evaluation: AgentEval,
) -> Run[str]:
    repository = git_workspace(
        source=ROOT,
        revision="395a3828",
    )

    def investigate(context: CrystalLatticeContext) -> str:
        context.start("codex-openai")
        context.add_message(
            "user",
            (
                "Investigate the package boundaries, shared frontend "
                "packages, mobile package, documentation ownership, and "
                "existing specification locations. Report facts only and "
                "do not modify files."
            ),
        )
        context.request(
            overrides={
                "include_tasks": False,
                "skills_enabled": False,
                "mcp_enabled": False,
                "web_search_enabled": False,
            }
        )
        context.create_snapshot(
            "neutral-investigation",
            using=application_session_snapshot,
        )
        return context.final_response()

    run = evaluation.run(
        "documentation-repository-investigation",
        investigate,
        workspace=repository,
        cache_key="documentation-repository-investigation-v1",
    )

    run.raise_for_error()
    assert run.changed_paths == ()
    assert run.environment.mutation_calls == ()
    return run


@pytest.mark.agent_eval
@pytest.mark.requirements("DOCGEN-003", "DOCGEN-005", "DOCREP-004")
def test_mobile_specific_specification_is_package_owned(
    evaluation: AgentEval,
    repository_investigation: Run[str],
) -> None:
    standard = "\n\n".join(
        path.read_text(encoding="utf-8")
        for path in STANDARD_FILES
    )

    def stop_after_expected_mutation(outcome) -> bool:
        return outcome.completed and outcome.mutation_count >= 1

    custom_driver = application_tool_loop(
        stop_when=stop_after_expected_mutation,
        max_iterations=20,
    )

    def create_specification(
        context: CrystalLatticeContext,
    ) -> DocumentationScore:
        context.add_message(
            "user",
            f"""\
Repository documentation rules:

{standard}

Requested work:

Create a substantial mobile-only conversation-composer UX specification.
The shared frontend SDK owns portable messaging behavior. The mobile app adds
keyboard, safe-area, touch-target, and screen-transition requirements.
I approve creating the package-owned specification. Do not implement it.
""",
        )

        context.request(driver=custom_driver)

        context.create_snapshot(
            "created-specification",
            using=application_session_snapshot,
        )

        ai_material = context.evidence.project(
            "ai-assessment",
            using=lambda evidence: {
                "instruction_hash": evidence.require("instruction.hash"),
                "user_prompt": evidence.require("request.user_message"),
                "assistant_response": evidence.require("response.final"),
                "changed_files": evidence.values("workspace.changed_file"),
                "generated_markdown": evidence.values("workspace.markdown"),
                "tool_summary": evidence.require("tools.summary"),
            },
        )

        score = context.evaluate(
            "documentation-score",
            ai_material,
            using=lambda material: score_documentation_result(
                evaluation=evaluation,
                material=material,
            ),
        )

        context.present(
            "human-review",
            context.evidence,
            using=render_documentation_review,
        )

        return score

    run = evaluation.run(
        "mobile-specific-specification-ownership",
        create_specification,
        continue_from=repository_investigation,
    )

    run.raise_for_error()

    created = [
        Path(path)
        for path in run.changed_paths
        if path.endswith(".md")
    ]

    assert created
    assert all(
        path.parts[:2] == (
            "mobile",
            "crystal-lattice-control-rn",
        )
        for path in created
    )
    assert run.value.ownership >= 4
    assert run.value.target_vs_current >= 4
    assert run.value.duplication_avoidance >= 4


def score_documentation_result(
    *,
    evaluation: AgentEval,
    material: object,
) -> DocumentationScore:
    scoring_environment = CrystalLatticeEnvironment.from_config(
        ROOT / "application/python/agent_terminal_app/default_config/config.json",
    )

    def score(context: CrystalLatticeContext) -> DocumentationScore:
        context.start("glm-ollama")
        context.add_message(
            "user",
            (
                "Score this documentation result from 1 to 5 for ownership, "
                "target-versus-current separation, and duplication avoidance. "
                "Return only JSON matching DocumentationScore.\n\n"
                f"{material}"
            ),
        )
        context.request(
            overrides={
                "skills_enabled": False,
                "mcp_enabled": False,
                "web_search_enabled": False,
            }
        )
        return DocumentationScore.model_validate_json(
            context.final_response()
        )

    scoring_run = evaluation.run(
        "score-mobile-specification",
        score,
        environment=scoring_environment,
    )
    scoring_run.raise_for_error()
    return scoring_run.value


def render_documentation_review(evidence, artifacts) -> None:
    artifacts.write_markdown(
        "manual-review.md",
        title="Documentation-standard manual review",
        sections={
            "Result": evidence.require("response.final"),
            "Changed files": evidence.values("workspace.changed_file"),
            "Tool summary": evidence.require("tools.summary"),
            "Questions": (
                "Does the package own this UX contract?",
                "Does the specification refine rather than duplicate the "
                "portable contract?",
            ),
        },
    )
```

The implementation may refine helper names, but it must preserve the ability
to select custom drivers, snapshots, projections, evaluations, and
presentations at the point of use.

### Example 3: replace the complete run environment

This example demonstrates that Option 3-style Crystal Lattice operations are
not imposed by the generic kernel. The alternate environment has its own
context and snapshot model.

```python
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from agent_eval import AgentEval, RunEnvironment, RunServices


@dataclass
class ReplayContext:
    services: RunServices
    transcript: list[str]
    position: int = 0

    def next_response(self, prompt: str) -> str:
        self.services.record(
            "replay.prompt",
            prompt,
        )
        response = self.transcript[self.position]
        self.position += 1
        self.services.record(
            "replay.response",
            response,
        )
        return response


@dataclass(frozen=True)
class ReplaySnapshot:
    position: int


class ReplayEnvironment(RunEnvironment[ReplayContext]):
    def __init__(self, transcript: list[str]) -> None:
        self._transcript = transcript

    def fingerprint(self) -> object:
        return {
            "type": "replay",
            "transcript": self._transcript,
            "schema": 1,
        }

    @contextmanager
    def open(
        self,
        *,
        services: RunServices,
        workspace: Path | None,
        parent_snapshot: object | None,
    ) -> Iterator[ReplayContext]:
        position = (
            parent_snapshot.position
            if isinstance(parent_snapshot, ReplaySnapshot)
            else 0
        )
        context = ReplayContext(
            services=services,
            transcript=list(self._transcript),
            position=position,
        )
        yield context

    def snapshot(
        self,
        context: ReplayContext,
    ) -> ReplaySnapshot:
        return ReplaySnapshot(position=context.position)

    def finalize(
        self,
        context: ReplayContext,
    ) -> object:
        return {
            "responses_consumed": context.position,
            "responses_remaining": (
                len(context.transcript) - context.position
            ),
        }


def test_generic_kernel_accepts_an_alternate_environment(
    tmp_path: Path,
) -> None:
    evaluation = AgentEval(
        default_environment=ReplayEnvironment(
            transcript=[
                "Specifications describe the target.",
                "Requirements track the live state.",
            ]
        ),
        artifact_root=tmp_path / "artifacts",
        cache_root=tmp_path / "cache",
    )

    def first(context: ReplayContext) -> str:
        return context.next_response("What does a specification describe?")

    first_run = evaluation.run(
        "replay-first",
        first,
        cache_key="replay-first-v1",
    )

    assert first_run.value == "Specifications describe the target."

    def second(context: ReplayContext) -> str:
        return context.next_response("What tracks live state?")

    second_run = evaluation.run(
        "replay-second",
        second,
        continue_from=first_run,
    )

    assert second_run.value == "Requirements track the live state."
    assert second_run.environment["responses_consumed"] == 2
```

This alternate environment does not implement Crystal Lattice request drivers,
tool loops, message projections, or AI evaluation helpers. It only satisfies
the broad run-environment lifecycle required by the generic kernel.

## Acceptance examples

### Cached repository investigation

A pytest session fixture investigates a pinned repository with a default
Crystal Lattice Codex or Claude configuration. The investigation is
guidance-neutral, performs no mutations, and is reused by several
continuations.

### Configuration or plugin variation

A test constructs a Crystal Lattice configuration that injects candidate rules
through a feature plugin, skill, user message, or another supported mechanism.
The generic kernel does not change.

### Multi-turn interaction

One execution callback asks for a plan, sends a confirmation, and returns both
assistant responses. The environment snapshots the final conversation.

### Structured scoring

A second run asks a model for a JSON scorecard. The callback validates the JSON
into a test-owned type and returns that object. Pytest decides whether to assert
a threshold, record the score only, or leave the result for manual review.

### Alternate environment

A deterministic replay or another agent framework supplies its own
`RunEnvironment` and context. It reuses the generic workspace, cache, artifact,
parent-run, and error lifecycle without adopting Crystal Lattice's lower-level
strategy model.

### Documentation-standard verification

Tests fork a shared repository investigation and exercise package ownership,
package-specific refinements, specification target versus current state,
anti-duplication, discoverability, plugin documentation, package profiles, and
maintainer routing. Results map to `DOCGEN-*` and `DOCREP-*` requirements while
human verification remains separate.