# Quickstart

This page builds one small evaluation and explains the objects involved. For
the overall mental model, start with the [documentation home](index.md).

## Install the package

From the repository root:

```bash
python -m pip install -e "maintainer/agent-evaluation[crystal-lattice,dev]"
```

## Prepare a Crystal Lattice configuration

Use an ordinary Crystal Lattice configuration containing the provider,
plugins, and agent you want to exercise. The evaluation library does not have
a separate prompt, model, skill, or tool configuration format.

The configuration answers “what agent runtime should exist?” The Python
evaluation program answers “what should this test ask that runtime to do, and
what result should the test inspect?”

## Run an evaluation

```python
from pathlib import Path

from agent_eval import AgentEval
from agent_eval.crystal_lattice import (
    CrystalLatticeContext,
    CrystalLatticeEnvironment,
)


ROOT = Path(__file__).resolve().parents[1]

environment = CrystalLatticeEnvironment.from_config(
    ROOT / "config.json",
    environment={
        "BUILTIN_PLUGINS": str(ROOT / "plugins"),
    },
)

with AgentEval(
    default_environment=environment,
    artifact_root=ROOT / "tmp/agent-evaluation",
    cache_root=ROOT / "tmp/agent-evaluation/cache",
) as evaluation:
    def exercise(context: CrystalLatticeContext) -> dict[str, object]:
        context.start("codex-openai")
        context.add_message(
            "user",
            "Explain which package owns the requested behavior.",
        )
        outcome = context.request()
        return {
            "response": outcome.final_response,
            "events": len(outcome.events),
        }

    run = evaluation.run("package-ownership", exercise)
    run.raise_for_error()

    print(run.value)
    print(run.canonical_text())
```

The example creates four important objects:

- `CrystalLatticeEnvironment` describes how to construct and restore the
  Crystal Lattice runtime.
- `AgentEval` manages the generic lifecycle around that runtime.
- `CrystalLatticeContext` is the live application/session handle passed to
  `exercise`.
- `Run` is the durable result returned after the callback and environment have
  finished.

Inside the callback:

1. `start()` creates the agent session.
2. `add_message()` immutably adds and persists a user message.
3. `request()` executes the production application request and tool loop.
4. The callback returns a small test-owned value instead of the complete
   runtime transcript.

The callback may perform multiple requests and return any Python value. The
framework does not convert that value into pass/fail.

## Assert with pytest

```python
def test_package_ownership(evaluation: AgentEval) -> None:
    def exercise(context: CrystalLatticeContext) -> str:
        context.start("codex-openai")
        context.add_message(
            "user",
            "Where should a mobile-only UX specification be owned?",
        )
        context.request()
        return context.final_response()

    run = evaluation.run("mobile-specification-owner", exercise)
    run.raise_for_error()

    assert "mobile" in run.value.lower()
```

Pytest owns assertions and parametrization. A program can instead return a
score, issue list, ranking, or structured model response.

`run.raise_for_error()` reports failures that happened inside the environment
or callback. A later failed pytest assertion is separate: the run itself may
have completed correctly even though its behavior did not satisfy the test.

## Cache an expensive investigation

```python
from agent_eval import git_workspace


repository = git_workspace(
    source=ROOT,
    revision="abc123",
)

seed = evaluation.run(
    "repository-investigation",
    investigate_repository,
    workspace=repository,
    cache_key="repository-investigation-v1",
)
seed.raise_for_error()
```

The effective key also includes the environment, workspace, parent snapshot,
and cache schema.

## Continue from the investigation

```python
continuation = evaluation.run(
    "apply-documentation-rules",
    apply_rules,
    continue_from=seed,
)
continuation.raise_for_error()
```

A reusable workspace factory creates a fresh compatible workspace. The
Crystal Lattice environment restores the session and rebases occurrences of
the previous workspace root in stored session data.

This is a continuation, not a cache hit: `apply_rules` executes. The snapshot
only supplies its starting state.

## Inspect the result

The normal review surface is:

```text
<artifact-dir>/result.md
<artifact-dir>/result.json
```

Complete diagnostics, sessions, events, snapshots, Git status, diffs, and
serialization fallbacks live under:

```text
<artifact-dir>/raw/
```

See [Artifacts and evidence](artifacts-and-evidence.md) before sending result
material to another model or a human reviewer.