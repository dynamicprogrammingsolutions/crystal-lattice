# Agent Evaluation

`agent_eval` is a small programmatic evaluation kernel. It owns run identity,
workspaces, compatible state reuse, artifacts, and error preservation while a
`RunEnvironment` supplies execution-specific context, snapshots, and
observations.

The current implementation covers the generic kernel and alternate-environment
contract. The Crystal Lattice environment and real-model documentation
standard suites are delivered by later checkpoints of the approved task.

Specification:

- `maintainer/specifications/agent-evaluation-framework/index.md`

Task:

- `tasks/20260728-package-local-documentation-standard/015-agent-evaluation-framework.md`

## Installation

From the repository root:

```bash
python -m pip install -e "maintainer/agent-evaluation[dev]"
```

## Minimal API

```python
run = evaluation.run(
    "run-name",
    program,
    environment=environment,
    continue_from=previous_run,
    workspace=workspace_factory,
    cache_key="optional-cache-key",
)
```

Only `name` and `program` are required when the evaluator has a default
environment.

- `program(context)` is arbitrary Python and may return any value.
- `environment` replaces the complete execution context.
- `continue_from` restores a compatible parent snapshot.
- `workspace` is an existing path or a factory receiving a run-owned staging
  directory.
- `cache_key` opts a completed run into compatible local reuse.

The kernel does not define prompts, message roles, models, tool loops,
assertions, scores, or presentations.

## Complete deterministic example

```python
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from agent_eval import AgentEval, RunEnvironment, RunServices


@dataclass
class ReplayContext:
    services: RunServices
    responses: list[str]
    position: int = 0

    def next_response(self, prompt: str) -> str:
        self.services.record("replay.prompt", prompt)
        response = self.responses[self.position]
        self.position += 1
        self.services.record("replay.response", response)
        return response


@dataclass(frozen=True)
class ReplaySnapshot:
    position: int


class ReplayEnvironment(RunEnvironment[ReplayContext]):
    def __init__(self, responses: list[str]) -> None:
        self.responses = responses

    def fingerprint(self) -> object:
        return {
            "type": "replay",
            "schema": 1,
            "responses": self.responses,
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
        yield ReplayContext(
            services=services,
            responses=list(self.responses),
            position=position,
        )

    def snapshot(self, context: ReplayContext) -> object:
        return ReplaySnapshot(position=context.position)

    def finalize(self, context: ReplayContext) -> object:
        return {
            "responses_consumed": context.position,
            "responses_remaining": len(context.responses) - context.position,
        }


def evaluate(tmp_path: Path) -> None:
    environment = ReplayEnvironment(
        [
            "Specifications describe the target.",
            "Requirements track live implementation.",
        ]
    )

    with AgentEval(
        default_environment=environment,
        artifact_root=tmp_path / "artifacts",
        cache_root=tmp_path / "cache",
    ) as evaluation:
        first = evaluation.run(
            "first",
            lambda context: context.next_response("What is a specification?"),
            cache_key="first-v1",
        )
        first.raise_for_error()

        second = evaluation.run(
            "second",
            lambda context: context.next_response("What tracks live state?"),
            continue_from=first,
        )
        second.raise_for_error()

        assert first.value == "Specifications describe the target."
        assert second.value == "Requirements track live implementation."
```

## Workspaces

Pass an existing path:

```python
run = evaluation.run(
    "existing-workspace",
    program,
    workspace=Path("/path/to/workspace"),
)
```

Existing paths are not assumed to be safely reusable for continuation.

Use a clean pinned Git worktree:

```python
from agent_eval import git_workspace


repository = git_workspace(
    source="/path/to/repository",
    revision="abc123",
)

run = evaluation.run(
    "pinned-repository",
    program,
    workspace=repository,
)
```

Reusable workspace factories allow a child run to create a fresh compatible
workspace automatically.

## Cache

Caching is explicit:

```python
run = evaluation.run(
    "expensive-investigation",
    program,
    workspace=repository,
    cache_key="investigation-v1",
)
```

The effective key also includes:

- environment fingerprint;
- workspace fingerprint;
- parent snapshot hash;
- cache schema.

The program source is not introspected. Change the versioned caller key when
program semantics change.

Cache entries are local trusted artifacts and use Python pickle for arbitrary
program values, environment observations, and snapshots. Do not load a cache
root supplied by an untrusted party.

## Artifacts

Each invocation writes:

```text
<artifact-root>/runs/<run-id>/
├── result.md
├── result.json
├── records/
└── raw/
    ├── environment/
    ├── errors/
    ├── evidence.json
    └── workspace/
```

`result.md` and `result.json` are the compact routine review surface. Raw
artifacts preserve serialized values, snapshots, observations, evidence,
errors, Git status, and Git diff when available.

JSON artifacts redact fields whose keys look like credentials, secrets,
passwords, tokens, or API keys. Environments remain responsible for not writing
authentication state into raw artifacts.

## Tests

Run the deterministic package tests:

```bash
pytest maintainer/agent-evaluation/tests -q
```

Real-agent suites will use the `agent_eval` marker and remain excluded from the
package's default pytest configuration.