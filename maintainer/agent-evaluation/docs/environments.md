# Environments and Customization

## Generic environment contract

`AgentEval` delegates execution-specific behavior to one `RunEnvironment`:

```python
class RunEnvironment(Protocol[Context]):
    def fingerprint(self) -> object: ...

    def open(
        self,
        *,
        services: RunServices,
        workspace: Path | None,
        parent_snapshot: object | None,
    ) -> AbstractContextManager[Context]: ...

    def snapshot(self, context: Context) -> object | None: ...

    def finalize(self, context: Context) -> object: ...
```

Replacing the environment replaces the complete context model. An alternate
environment does not need to implement Crystal Lattice requests, messages,
tool loops, projections, or presentations.

## Complete alternate environment

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
    def fingerprint(self) -> object:
        return {"type": "replay", "schema": 1}

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
            responses=[
                "Specifications describe the target.",
                "Requirements track live state.",
            ],
            position=position,
        )

    def snapshot(self, context: ReplayContext) -> object:
        return ReplaySnapshot(position=context.position)

    def finalize(self, context: ReplayContext) -> object:
        return {"responses_consumed": context.position}


def run_replay(tmp_path: Path) -> None:
    with AgentEval(
        default_environment=ReplayEnvironment(),
        artifact_root=tmp_path / "artifacts",
        cache_root=tmp_path / "cache",
    ) as evaluation:
        first = evaluation.run(
            "first",
            lambda context: context.next_response(
                "What does a specification describe?"
            ),
        )
        second = evaluation.run(
            "second",
            lambda context: context.next_response(
                "What tracks live state?"
            ),
            continue_from=first,
        )

        assert first.value == "Specifications describe the target."
        assert second.value == "Requirements track live state."
```

This environment reuses the generic run, continuation, cache, artifact, and
error lifecycle without importing Crystal Lattice.

## Crystal Lattice environment

```python
environment = CrystalLatticeEnvironment.from_config(
    config_path,
    environment={"WORKING_DIR": str(workspace)},
    config_env={"OPTIONAL_VALUE": "value"},
    default_agent="optional-agent-id",
)
```

The environment:

- creates an isolated session store for each uncached run;
- constructs a real `AgentApplication` and `AgentCore`;
- restores a compatible parent session;
- closes application resources after snapshot/finalization;
- removes temporary runtime files;
- writes the final session and normalized observation under `raw/`.

Environment and configuration values are represented by hashes in the
fingerprint. Secret values are not written into the fingerprint artifact.

## Context access

After `context.start(agent_id)`, these properties expose the live production
objects:

```python
context.application
context.core
context.session
context.base_config
context.workspace
context.services
context.evidence
```

`context.config` is a mutable dictionary of default request overrides. It is
combined with per-request overrides and used to rebuild the runtime through
`AgentApplication.load_session(..., overrides=...)`.

```python
context.config["temperature"] = 0
context.config["skills_enabled"] = False

context.request(
    overrides={"reasoning": {"effort": "high"}},
)
```

Per-request values win over context defaults.

For lower-level work, use the application/core objects directly and call
`context.replace_runtime(...)` with the resulting immutable session.

## Messages and requests

```python
context.start("agent-id")
context.add_message("system", "Additional test instruction")
context.add_message("user", "Investigate the repository")

outcome = context.request(
    stream=False,
)
```

`CrystalRequestOutcome` contains:

- final core, session, and base configuration;
- all observed application events;
- final assistant messages;
- completion, cancellation, and error state;
- tool-event and caller-classified mutation counts;
- stop reason and duration;
- `final_response`.

## Observers, mutation classification, and stopping

```python
def observe(event):
    print(event.get("type"))


def classify_mutation(event):
    return event.get("type") == "tool_results"


def stop_after_checkpoint(progress):
    return (
        progress.mutation_count >= 1
        and progress.event.get("type") == "session_checkpoint"
    )


outcome = context.request(
    observers=(observe,),
    mutation_classifier=classify_mutation,
    stop_when=stop_after_checkpoint,
)
```

The production driver calls `AgentApplication.cancel_request()` before closing
an intentionally stopped request iterator. Stop after a persisted checkpoint
when later code needs the corresponding session state.

`max_events` provides a simple event-count guard. Custom drivers may implement
entirely different stopping semantics.

## Custom request drivers

A driver receives one `CrystalRequest` and returns one
`CrystalRequestOutcome`:

```python
def direct_driver(request):
    session = request.core.add_message(
        request.session,
        "assistant",
        "deterministic response",
    )
    session = request.context.application.save_session(session)

    return CrystalRequestOutcome(
        core=request.core,
        session=session,
        base_config=request.base_config,
        events=({"type": "deterministic"},),
        final_messages=(
            {
                "role": "assistant",
                "content": "deterministic response",
            },
        ),
        request_id=request.request_id,
        completed=True,
        cancelled=False,
        error_messages=(),
        tool_event_count=0,
        mutation_count=0,
        stop_reason=None,
        duration_seconds=0.0,
    )


outcome = context.request(driver=direct_driver)
```

The callback can also bypass `context.request()` and operate on
`AgentApplication` or `AgentCore` directly.

## Snapshots

The environment's continuation snapshot contains:

- the immutable session;
- the source workspace root;
- default request overrides.

It uses deterministic JSON serialization.

Programs may create named snapshots for evidence:

```python
context.create_snapshot(
    "session",
    using=application_session_snapshot,
)

context.create_snapshot(
    "selected-facts",
    using=lambda current: {
        "response": current.final_response(),
    },
)
```

Named custom snapshots are artifacts and evidence. The environment's final
continuation snapshot remains a `CrystalLatticeSnapshot`.

## Evaluation and presentation

Evaluation is an arbitrary callable:

```python
score = context.evaluate(
    "response-length",
    context.final_response(),
    using=len,
)
```

It may call another model and return booleans, scores, rankings, findings, or a
test-owned structured type. The framework records input and result but does not
interpret the verdict.

Presentation is also caller-owned:

```python
context.present(
    "manual-review",
    {"response": context.final_response()},
    using=lambda value, artifacts: artifacts.record(
        "manual-review",
        value,
    ),
)
```

Use different evidence selections for deterministic assertions, AI
evaluation, and manual review.