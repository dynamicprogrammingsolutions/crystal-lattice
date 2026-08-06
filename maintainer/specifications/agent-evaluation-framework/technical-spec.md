# Agent evaluation framework technical specification

## Architecture

The first version has one generic framework, one runtime strategy boundary,
and ordinary Python tests:

```text
pytest test
  -> AgentEval.run(name, execute, ...)
    -> workspace preparation and cache lookup
    -> RuntimeAdapter opens fresh or restored runtime
    -> arbitrary execute(context) Python
    -> adapter snapshot and observation
    -> workspace observation
    -> canonical and raw artifacts
    -> Run[T]
  -> ordinary pytest assertions
```

The framework owns evaluation lifecycle. The runtime adapter owns Crystal
Lattice execution. The callback owns evaluation behavior.

## Target source structure

```text
maintainer/
├── agent-evaluation/
│   ├── README.md
│   ├── pyproject.toml
│   ├── src/
│   │   └── agent_eval/
│   │       ├── __init__.py
│   │       ├── eval.py
│   │       ├── result.py
│   │       ├── repository.py
│   │       ├── artifacts.py
│   │       └── crystal_lattice.py
│   ├── suites/
│   │   └── test_documentation_standard.py
│   └── tests/
└── specifications/
    └── agent-evaluation-framework/
```

The exact internal module split is reversible. The public contract is more
important than matching this illustrative inventory.

The distribution and import name are:

```text
distribution directory: maintainer/agent-evaluation
Python import: agent_eval
```

The package depends on the repository's Crystal Lattice Core and Application
packages. It does not depend on the terminal UI or HTTP server merely to run
application-layer evaluations.

## Minimal public API

The first stable execution contract is:

```python
class AgentEval:
    def run(
        self,
        name: str,
        execute: Callable[[C], T],
        *,
        adapter: RuntimeAdapter[C] | None = None,
        continue_from: Run[object] | None = None,
        workspace: Path | WorkspaceFactory | None = None,
        cache_key: str | None = None,
    ) -> Run[T]:
        ...
```

The constructor supplies:

- a default runtime adapter;
- artifact root;
- optional cache root;
- framework-wide local infrastructure such as locks or clocks.

The run inputs are deliberately limited:

| Input | Justification |
|---|---|
| `name` | Stable human-readable and filesystem-safe run identity |
| `execute` | Arbitrary test-owned behavior |
| `adapter` | Optional runtime/configuration variation; otherwise use the default |
| `continue_from` | Restore and fork a previous conversation |
| `workspace` | Optional isolated filesystem/repository context |
| `cache_key` | Explicit opt-in to expensive run reuse |

The API does not contain prompt, agent, model, system/developer message,
guidance, skills, tools, reviewer, parser, mutation limit, or assertion inputs.

## Execution callback

`execute` is ordinary Python:

```python
def execute(context: CrystalLatticeContext) -> ResultType:
    ...
```

It may:

- start or select an agent;
- add any supported message role and content;
- send one or several requests;
- call application actions;
- use custom plugins, tools, skills, or features;
- read or mutate the workspace;
- parse responses into any type;
- record custom artifacts;
- return any Python value.

The framework does not inspect callback meaning. It records execution through
the adapter and workspace observers.

## Runtime adapter

The only required strategy abstraction is:

```python
class RuntimeAdapter(Protocol, Generic[C]):
    def fingerprint(self) -> object:
        ...

    def open(
        self,
        *,
        workspace: Path | None,
        artifact_dir: Path,
        snapshot: object | None,
    ) -> AbstractContextManager[C]:
        ...

    def snapshot(self, context: C) -> object:
        ...

    def observation(self, context: C) -> object:
        ...
```

This boundary is justified because:

- generic caching and artifacts should not know provider/application details;
- Crystal Lattice configuration and plugins should remain authoritative;
- restored conversation state is runtime-specific;
- another runtime can be supported later without changing test lifecycle.

No additional public strategy types are required initially. Workspace helpers
may be callables. Scoring and review remain callbacks.

## Crystal Lattice application adapter

The initial adapter wraps `AgentApplication`, `AgentCore`, sessions, request
events, effective configuration, and cleanup.

Construction accepts normal Crystal Lattice configuration inputs, including a
config path or caller-owned config factory and environment overrides. It does
not expose evaluation-specific configuration keys.

The callback context provides:

```python
class CrystalLatticeContext:
    application: AgentApplication
    core: AgentCore
    session: Session
    config: dict[str, object]
    workspace: Path | None

    def start(self, agent_id: str) -> None:
        ...

    def add_message(
        self,
        role: str,
        content: object,
        *,
        metadata: dict[str, object] | None = None,
    ) -> None:
        ...

    def request(
        self,
        *,
        overrides: dict[str, object] | None = None,
    ) -> list[dict[str, object]]:
        ...

    def final_response(self) -> str:
        ...

    def record(self, name: str, value: object) -> Path:
        ...
```

Convenience methods update the current immutable session and capture request
events. Direct properties remain available as an escape hatch.

The context does not introduce separate methods for system guidance, task
guidance, skills, scoring, or review. Tests use normal messages,
configuration, plugins, actions, and request overrides.

## Run result

The generic result is:

```python
@dataclass(frozen=True)
class Run(Generic[T]):
    name: str
    value: T
    snapshot: object
    runtime: object
    workspace: Path | None
    changed_paths: tuple[str, ...]
    artifact_dir: Path
    error: RunError | None

    def raise_for_error(self) -> None:
        ...

    def canonical_text(self) -> str:
        ...

    def record(self, name: str, value: object) -> Path:
        ...
```

`value` is exactly the callback return value. The framework does not convert
it into a verdict.

`runtime` is the adapter-specific normalized observation. The Crystal Lattice
observation includes, when available:

- visible messages;
- request boundaries;
- final assistant responses;
- tool calls and mutation classification;
- runtime errors and cancellations;
- timing;
- token/usage information exposed by the provider;
- hashes and references for raw request/session evidence.

## Lifecycle and errors

For every uncached run:

1. Allocate a run artifact directory.
2. Prepare or restore the workspace.
3. Validate a parent snapshot when `continue_from` is supplied.
4. Open the selected runtime adapter.
5. Execute the callback.
6. Capture callback exceptions without losing runtime/workspace evidence.
7. Ask the adapter for a reusable snapshot and normalized observation.
8. Capture changed paths and Git diff/status when applicable.
9. Write canonical and raw artifacts.
10. Close the adapter and workspace resources.
11. Return `Run[T]`.

Runtime, provider, tool, callback, parsing, and artifact failures are recorded
with a phase, type, and message. When a result can be returned safely,
`Run.error` is populated and `raise_for_error()` raises an exception carrying
the run. Failures before a `Run` can be created still leave a failure artifact
directory.

Pytest assertion failures occur after `run()` returns. The canonical runtime
artifact therefore already exists.

## Conversation continuation

`continue_from` restores the parent adapter snapshot into a new runtime.

For repository-backed runs, the default behavior is a fresh workspace at the
same baseline revision. The adapter or framework rebases absolute workspace
references in the restored state when required by the runtime.

The parent snapshot remains immutable and hash-verified. A continuation records:

- parent run identity;
- parent snapshot hash;
- runtime snapshot format version;
- source and target workspace fingerprints;
- any workspace reference rebuilding or rebasing performed.

Cross-runtime or cross-model restoration is rejected unless the adapter
explicitly declares compatibility.

## Cache

Caching is explicit through `cache_key`.

The effective cache identity combines:

- caller-provided cache key;
- adapter fingerprint;
- workspace/repository fingerprint;
- parent snapshot hash, when applicable;
- framework cache schema version.

The framework does not hash or introspect callback source. Callers version
their cache key when callback semantics change.

Cached runs preserve the same `Run` contract and provenance. Cache lookup uses
a lock so parallel processes cannot create a partially written entry. Initial
real-model suites run without pytest process parallelism until locking and
provider behavior are verified.

## Workspace

`workspace` accepts:

- an existing `Path`; or
- a callable receiving a run-owned staging directory and returning a `Path`.

A `git_workspace()` helper may clone/cache a repository, create a detached
worktree at a pinned revision, and provide a reproducible fingerprint. The
helper is optional; custom fixtures remain ordinary callables.

For Git workspaces, the framework records:

- baseline revision;
- status;
- changed paths;
- diff;
- optional fixture/setup commit.

Worktrees may be removed after artifacts are finalized. The revision and diff
must be sufficient to reconstruct the result.

## Artifacts and observability

Every run produces:

```text
<artifact-root>/runs/<run-id>/<name>/
├── result.md
├── result.json
├── records/
└── raw/
    ├── runtime/
    ├── workspace/
    └── error.txt
```

`result.md` and `result.json` are deterministic canonical artifacts intended
for routine human and AI inspection. They contain:

- run, parent, cache, adapter, and workspace identity;
- callback return value when safely renderable;
- adapter-provided concise observations;
- changed paths and primary workspace summary;
- error phase and message;
- links and hashes for raw evidence.

Raw artifacts preserve complete sessions, events, compiled requests, tool
payloads, Git evidence, and adapter-specific diagnostics when configured.
Routine reviewer prompts use canonical artifacts rather than raw context.

Artifact roots are ignored local outputs by default. Adapters must not copy
credentials or authentication state into artifacts. Tests using sensitive
repository data configure additional redaction or retention through the
runtime and artifact environment rather than through prompt-specific
framework parameters.

## Pytest suites

Pytest is the initial runner:

- a test module is a suite;
- fixtures provide shared cached investigations;
- parametrization varies prompts, application configurations, plugins, models,
  or repetitions;
- ordinary assertions define acceptance;
- custom return values support arbitrary structured scoring;
- markers map important tests to requirement IDs.

Real-model tests use a registered `agent_eval` marker and are excluded from
default test commands. Hosted or paid execution requires an explicit gate.
Skipped gated tests are reported as not run.

Initial real-model execution does not use pytest-xdist. Deterministic framework
tests remain part of the package's normal fast test suite.

A separate CLI is not required initially. A later thin CLI may inspect,
compare, score, or bundle saved runs through the library without defining a
second scenario language.

## First consumer: documentation-standard instructions

The first real consumers are pytest tests under the framework package. They
verify agent application of:

- `DOCGEN-001`–`DOCGEN-005`;
- `DOCREP-001`–`DOCREP-005`;
- `DOCVAL-005`.

The suite uses a pinned repository baseline that does not expose the candidate
instruction through the warm-up context. One guidance-neutral investigation
may feed multiple clean continuations.

Coverage includes:

1. Applying generic package-neutral rules without leaking Crystal Lattice
   terms.
2. Distinguishing target specifications, live requirements, task approval, and
   current documentation.
3. Assigning package-owned and package-specific refinement specifications.
4. Avoiding duplicate normative contracts and preserving discoverability.
5. Applying repository paths and package profiles proportionally.
6. Distinguishing shared plugin guidance from individual plugin ownership.
7. Keeping root documentation and maintainer boundaries narrow.
8. Distinguishing applying standards from maintaining them.

Tests may exercise the same rules through user-message text, application
configuration, or plugins. The framework does not privilege one injection
method.

Deterministic assertions inspect changed paths, generated files, responses, and
provenance. Optional model calls may return structured scorecards or semantic
findings. Model judgment is supporting behavioral evidence, not the sole proof
of static documentation requirements or human verification.

Every real-model artifact records exact model/configuration identity, candidate
instruction hash, prompt, seed, response, tool summary, and failure state.

## Existing task-guidance evaluator

The implementation under `test/task_guidance/` remains a reference prototype
during this task. Subtask 015 does not move it or require it to use the new
library.

Subtask 068 later:

- moves task-guidance evaluation into the maintainer domain;
- adopts the library where it reduces duplicated infrastructure;
- preserves its deterministic assertions and review behavior;
- updates existing commands and consumers;
- removes obsolete specialized framework code only after equivalent behavior
  is verified.