# Agent evaluation framework technical specification

## Architecture

The target has four layers:

```text
Layer 1: generic evaluation kernel
  AgentEval, Run, RunServices
  run identity, workspace, cache, parent linkage, artifacts, errors

Layer 2: replaceable run environment
  RunEnvironment[Context]
  fingerprint, open/restore, snapshot, finalize

Layer 3: environment-specific context
  CrystalLatticeEnvironment -> CrystalLatticeContext
  or an alternate environment and context

Layer 4: optional environment-specific operations
  request drivers, stop conditions, snapshotters, observers,
  projections, evaluations, presenters, and later recipes
```

The generic kernel never needs to understand an agent session or tool loop.
The Crystal Lattice environment provides those capabilities as its first
complete implementation.

Replacing the run environment may bypass all Crystal Lattice-specific
lower-layer operations. This permits a deterministic replay environment or
another agent framework to reuse the generic run, workspace, cache, artifact,
and error lifecycle without conforming to Crystal Lattice semantics.

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
│   │       ├── environment.py
│   │       ├── services.py
│   │       ├── evidence.py
│   │       ├── workspace.py
│   │       ├── artifacts.py
│   │       └── crystal_lattice/
│   │           ├── environment.py
│   │           ├── context.py
│   │           ├── requests.py
│   │           ├── snapshots.py
│   │           └── presentation.py
│   ├── suites/
│   │   └── test_documentation_standard.py
│   └── tests/
└── specifications/
    └── agent-evaluation-framework/
```

The exact internal module split is reversible. The public contracts and
extension boundaries are authoritative.

The distribution and import name are:

```text
distribution directory: maintainer/agent-evaluation
Python import: agent_eval
```

The Crystal Lattice environment depends on the repository's Core and
Application packages. The generic kernel should not import
`AgentApplication`, `AgentCore`, or provider-specific types.

## Generic kernel API

The first stable execution contract is:

```python
class AgentEval:
    def run(
        self,
        name: str,
        program: Callable[[C], T],
        *,
        environment: RunEnvironment[C] | None = None,
        continue_from: Run[object] | None = None,
        workspace: Path | WorkspaceFactory | None = None,
        cache_key: str | None = None,
    ) -> Run[T]:
        ...
```

The constructor supplies:

- a default run environment;
- artifact root;
- optional cache root;
- framework-wide local infrastructure such as locks, clocks, and
  serialization helpers.

The inputs are deliberately limited:

| Input | Justification |
|---|---|
| `name` | Stable human-readable and filesystem-safe run identity |
| `program` | Arbitrary test-owned behavior |
| `environment` | Optional complete execution-environment replacement |
| `continue_from` | Restore compatible state from a previous run |
| `workspace` | Optional isolated filesystem/repository context |
| `cache_key` | Explicit opt-in to expensive run reuse |

The API does not contain prompt, agent, model, system/developer message,
guidance, skills, tools, reviewer, parser, tool-loop limit, mutation limit,
assertion, score, or presentation inputs.

## Run services

The kernel provides environment-independent services:

```python
class RunServices:
    run_id: str
    name: str
    artifact_dir: Path
    workspace: Path | None
    parent: Run[object] | None
    evidence: EvidenceJournal
    artifacts: ArtifactWriter

    def record(
        self,
        kind: str,
        value: object,
        *,
        metadata: Mapping[str, object] | None = None,
        visibility: EvidenceVisibility = EvidenceVisibility.CANONICAL,
    ) -> EvidenceReference:
        ...
```

`RunServices` does not expose agent methods. A run environment may use all,
some, or none of its evidence facilities, but it always receives the
environment-independent artifact and parent context.

## Run environment

The one broad replacement seam is:

```python
class RunEnvironment(Protocol, Generic[C]):
    def fingerprint(self) -> object:
        ...

    def open(
        self,
        *,
        services: RunServices,
        workspace: Path | None,
        parent_snapshot: object | None,
    ) -> AbstractContextManager[C]:
        ...

    def snapshot(self, context: C) -> object | None:
        ...

    def finalize(self, context: C) -> object:
        ...
```

### `fingerprint`

Returns deterministic serializable data describing compatibility-relevant
environment behavior, such as:

- environment type and schema;
- application configuration;
- plugin and provider identity;
- model/request defaults when relevant to restored state;
- snapshot format compatibility.

Credentials and transient runtime values are excluded.

### `open`

Creates a fresh context or restores `parent_snapshot`. It receives:

- generic run services;
- prepared workspace;
- parent environment snapshot, when supplied.

It owns environment startup and cleanup.

### `snapshot`

Returns reusable environment state or `None`.

An environment returning `None` supports ordinary runs but cannot be used as a
continuation parent. The snapshot remains opaque to the kernel except for
serialization, hashing, and storage through the environment's supported
codec.

If an environment requires a separate codec, it may encapsulate version and
serialization behavior in the snapshot object or an internal environment
service. A second public snapshot protocol is not required initially.

### `finalize`

Returns the environment-specific normalized observation used in `Run`.

It may also write raw artifacts through `RunServices.artifacts`.

The generic kernel does not interpret the returned observation.

## Program callback

`program` is ordinary Python:

```python
def program(context: C) -> T:
    ...
```

It may:

- perform zero, one, or many environment operations;
- access environment-specific objects;
- read or mutate the workspace;
- parse responses;
- invoke another evaluation;
- record custom evidence or artifacts;
- return any Python value.

The kernel does not inspect callback meaning or source. It records errors and
the final value when safely serializable.

## Run result

The generic result is:

```python
@dataclass(frozen=True)
class Run(Generic[T]):
    name: str
    value: T
    snapshot: object | None
    environment: object
    environment_fingerprint: object
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

`value` is exactly the program return value. The kernel does not convert it
into a verdict.

`environment` is the result of `RunEnvironment.finalize()`.

`snapshot` is opaque reusable environment state. It may be `None`.

## Generic lifecycle

For every uncached run:

1. Validate the run name and allocate an artifact directory.
2. Prepare or restore the workspace.
3. Select the default or per-run environment.
4. Validate the environment fingerprint against the parent run.
5. Create `RunServices`.
6. Open the environment with the parent snapshot.
7. Execute the program.
8. Preserve program exceptions and continue safe evidence collection.
9. Ask the environment for its snapshot and finalized observation.
10. Capture changed paths and Git diff/status when applicable.
11. Write canonical and raw run artifacts.
12. Close environment and workspace resources.
13. Publish a complete cache entry when requested.
14. Return `Run[T]`.

Runtime, provider, tool, program, parsing, snapshot, finalize, and artifact
failures are recorded with a phase, type, and message.

When a result can be returned safely, `Run.error` is populated and
`raise_for_error()` raises an exception carrying the run. Failures before a
`Run` can be constructed still leave a failure artifact directory.

Pytest assertion failures occur after `run()` returns. The canonical runtime
artifact therefore already exists.

## Generic cache and continuation

Caching is explicit through `cache_key`.

The effective cache identity combines:

- caller-provided cache key;
- environment fingerprint;
- workspace/repository fingerprint;
- parent snapshot hash, when applicable;
- framework cache schema version.

The kernel does not hash or introspect program source. Callers version their
cache key when program semantics change.

Cache entries contain:

- environment fingerprint;
- snapshot hash and serialized snapshot when present;
- workspace fingerprint;
- parent identity;
- generic run metadata;
- canonical and raw artifact references;
- completion marker.

Cache publication uses safe atomic writes and locking. Partial entries are
never returned as hits.

`continue_from` requires:

- a non-null parent snapshot;
- compatible environment fingerprints;
- supported snapshot serialization;
- a compatible workspace baseline when the environment requires one.

Cross-environment continuation is rejected unless the target environment
explicitly recognizes the source snapshot and fingerprint.

## Workspace

`workspace` accepts:

- an existing `Path`; or
- a callable receiving a run-owned staging directory and returning a `Path`.

A `git_workspace()` helper may:

- clone or reuse a repository cache;
- prepare a detached clean worktree at a pinned revision;
- apply a caller-owned fixture hook;
- provide a reproducible fingerprint;
- record baseline revision, status, changed paths, and diff.

The helper is optional. Custom workspace fixtures remain ordinary callables.

Worktrees may be removed after artifacts are finalized. The revision, fixture
evidence, and diff must be sufficient to reconstruct the result.

## Evidence journal

The generic kernel provides an optional append-only journal:

```python
@dataclass(frozen=True)
class Evidence:
    kind: str
    source: str
    value: object
    metadata: Mapping[str, object]
    timestamp: datetime
    visibility: EvidenceVisibility
```

```python
class EvidenceJournal:
    def emit(
        self,
        *args: object,
        **kwargs: object,
    ) -> EvidenceReference:
        ...

    def select(
        self,
        predicate: Callable[[Evidence], bool],
    ) -> tuple[Evidence, ...]:
        ...

    def project(
        self,
        name: str,
        *,
        using: Callable[["EvidenceJournal"], T],
    ) -> T:
        ...
```

The journal is a shared observability spine, not a mandatory agent event
schema. Environments and programs choose their own `kind` values and
projections.

Alternate environments may use only generic `record()` calls and ignore
Crystal Lattice evidence helpers.

## Crystal Lattice environment

`CrystalLatticeEnvironment` is the first complete `RunEnvironment`.

It wraps:

- `AgentApplication`;
- `AgentCore`;
- immutable sessions;
- effective configuration;
- application request and tool-loop events;
- provider/plugin preparation;
- runtime environment cleanup.

Construction accepts normal Crystal Lattice configuration inputs, including a
config path or caller-owned config factory and environment overrides.

It does not expose evaluation-specific prompt, guidance, skill, or scoring
configuration.

## Crystal Lattice context

The context preserves high-level convenience and low-level access:

```python
class CrystalLatticeContext:
    application: AgentApplication
    core: AgentCore
    session: Session
    config: dict[str, object]
    workspace: Path | None
    services: RunServices
    evidence: EvidenceJournal

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
        messages: object | None = None,
        overrides: dict[str, object] | None = None,
        driver: RequestDriver | None = None,
        observers: tuple[RequestObserver, ...] = (),
    ) -> CrystalRequestOutcome:
        ...

    def create_snapshot(
        self,
        name: str,
        *,
        using: CrystalSnapshotter | None = None,
    ) -> object:
        ...

    def evaluate(
        self,
        name: str,
        value: object,
        *,
        using: Callable[[object], T],
    ) -> T:
        ...

    def present(
        self,
        name: str,
        value: object,
        *,
        using: Callable[[object, ArtifactWriter], None],
    ) -> None:
        ...

    def final_response(self) -> str:
        ...
```

These operations are conveniences. Direct properties remain the escape hatch.

The context does not introduce special methods for system guidance, task
guidance, skills, or reviewer prompts. Tests use normal messages,
configuration, plugins, actions, and request overrides.

## Crystal Lattice application lifecycle

Configuration must be customizable at all relevant phases:

- before application creation through a config factory;
- during creation through environment and plugin configuration;
- after application creation through context/application access;
- before each request through request overrides or request transforms;
- during execution through a custom request driver and observers;
- after each request through program logic and evidence records;
- before close through environment-owned cleanup/finalization.

Simple tests use environment defaults. Advanced tests may supply explicit
configuration or use lower-level application/core calls directly.

No universal `ConfigurationStrategy` is required initially.

## Request driver and tool-loop control

Crystal Lattice request execution is replaceable per request:

```python
RequestDriver = Callable[
    [CrystalRequestContext, EvidenceSink],
    CrystalRequestOutcome,
]
```

The default driver wraps the production `AgentApplication` request/tool-loop
path.

A custom driver may control:

- request preparation;
- streaming versus buffered execution;
- tool-call dispatch;
- mutation gates;
- retry behavior;
- maximum loops;
- stop conditions;
- cancellation;
- event observation;
- partial-result handling.

Stop conditions may be helper callables used by the default driver or may be
implemented entirely inside a custom driver. A separate required stop-policy
abstraction is not necessary.

## Crystal Lattice snapshots

The environment supplies a default session snapshotter compatible with its
restore behavior.

Per-run programs may create named custom snapshots:

```python
snapshot = context.create_snapshot(
    "neutral-investigation",
    using=custom_snapshotter,
)
```

A snapshotter may preserve:

- complete session;
- normalized workspace references;
- selected application metadata;
- multiple sessions;
- a portable knowledge capsule;
- custom continuation state.

The environment's final `snapshot()` decides which state becomes
`Run.snapshot`. A program-created named snapshot may be selected explicitly or
recorded only as an artifact.

## Crystal Lattice observation and projections

The environment records, when available:

- visible messages;
- request boundaries and effective configuration hashes;
- compiled request provenance;
- tool calls and mutation classification;
- runtime errors and cancellations;
- timing;
- token/usage information exposed by the provider;
- workspace changes;
- named snapshots;
- custom program records.

A projection explicitly selects evidence for one consumer:

```python
ai_input = context.evidence.project(
    "ai-input",
    using=select_ai_material,
)
```

Different projections may feed:

- deterministic assertions;
- AI scoring;
- pairwise comparison;
- human review;
- failure diagnosis;
- canonical summary.

The complete journal is never implicitly sent to an AI evaluator.

## Evaluation and scoring

`context.evaluate()` records an explicit input, operation identity, output, and
failure state. The supplied callable may:

- use no model;
- invoke another `AgentEval` run;
- call a Crystal Lattice model;
- return `bool`;
- return pass/fail plus reasons;
- return numerical scores;
- return ranked alternatives;
- return issue lists;
- return arbitrary structured data.

The framework does not interpret the returned value. Pytest or human review
does.

## Presentation

`context.present()` writes audience-specific artifacts without assigning a
verdict.

Presenters may produce:

- compact Markdown;
- JSON;
- HTML;
- comparison tables;
- a directory of primary files;
- terminal summaries;
- score reports;
- manual-review checklists.

The generic kernel always produces a minimal canonical run artifact. The
environment and program may add richer presentations.

## Optional recipes

Repeated Crystal Lattice components may later be bundled:

```python
recipe = CrystalLatticeRecipe(
    request_driver=...,
    snapshotter=...,
    observers=(...),
    canonical_projection=...,
    presenters=(...),
)
```

A recipe is only shorthand over lower operations. Every component remains
overridable or bypassable.

Do not stabilize a required recipe abstraction in the first implementation
unless the first consumers already demonstrate substantial repetition and the
helper remains optional.

## Artifacts

Every run produces:

```text
<artifact-root>/runs/<run-id>/<name>/
├── result.md
├── result.json
├── records/
└── raw/
    ├── environment/
    ├── workspace/
    └── error.txt
```

`result.md` and `result.json` are deterministic generic artifacts containing:

- run, parent, cache, environment, and workspace identity;
- program return value when safely renderable;
- environment-finalized concise observation;
- changed paths and primary workspace summary;
- error phase and message;
- links and hashes for raw evidence;
- named projections, evaluations, and presentations where recorded.

Raw artifacts preserve complete environment state, events, compiled requests,
tool payloads, Git evidence, and diagnostics when configured.

Routine AI and human review uses explicit canonical or audience-specific
projections rather than raw context.

Artifact roots are ignored local outputs by default. Environments must not copy
credentials or authentication state. Sensitive evaluations configure
additional redaction or retention through the environment and artifact
services.

## Pytest suites

Pytest is the initial runner:

- a test module is a suite;
- fixtures provide shared cached investigations;
- parametrization varies programs, environments, configuration, plugins,
  models, or repetitions;
- ordinary assertions define acceptance;
- arbitrary return values support structured scoring;
- markers map important tests to requirement IDs.

Real-model tests use a registered `agent_eval` marker and are excluded from
default test commands. Hosted or paid execution requires an explicit gate.
Skipped gated tests are reported as not run.

Initial real-model execution does not use pytest-xdist. Deterministic kernel
and environment tests remain part of the package's normal fast test suite.

A separate CLI is not required initially. A later thin CLI may inspect,
compare, rescore, or bundle saved runs through the same library without
defining a second scenario language.

## First consumer: documentation-standard instructions

The first real consumers are pytest tests under the framework package. They
verify application of:

- `DOCGEN-001`–`DOCGEN-007`;
- `DOCREP-001`–`DOCREP-006`;
- `DOCVAL-005`.

The documentation-standard specification owns the detailed
[agent-behavior verification scenarios](../documentation-and-specification-standard/agent-behavior-verification/index.md).
The framework specification owns their execution, continuation, evidence, and
artifact mechanics.

The initial suite uses `CrystalLatticeEnvironment`. Each scenario-family seed
uses a pinned repository baseline or clean fixture and establishes a narrow
task-specific base without exposing the candidate instruction through the
warm-up context. Most seeds are read-only factual investigations; a seed may
perform an explicitly bounded operation when its completed state is the common
base for follow-up tasks. A guidance-neutral seed may feed multiple closely
related clean continuations and may be reused across candidate-guidance
revisions.

Coverage includes:

1. Applying proportional package profiles, ownership, source-of-truth,
   incremental-adoption, and generated-output rules to ordinary documentation
   tasks.
2. Distinguishing target specifications, live requirements, task approval, and
   current documentation.
3. Assigning package-owned and package-specific refinement specifications.
4. Avoiding duplicate normative contracts and preserving discoverability.
5. Applying repository paths and package profiles proportionally.
6. Distinguishing shared plugin guidance from individual plugin ownership.
7. Keeping root documentation and maintainer boundaries narrow.
8. Distinguishing applying standards from maintaining them.

Tests may exercise the same rules through user-message text, application
configuration, plugins, or skills. The kernel does not privilege one injection
method.

The candidate guidance is supplied through the normal AGENTS and routed-file
mechanism. User prompts describe ordinary work and do not repeat the rules
being evaluated.

Deterministic assertions inspect changed paths, generated files, responses, and
provenance. Optional model calls may return structured scorecards or semantic
findings. Model judgment is supporting behavioral evidence, not the sole proof
of static documentation requirements or human verification.

Every real-model artifact records exact environment/configuration identity,
model, candidate instruction hash, prompt, seed, response, tool summary,
projections, evaluations, presentations, and failure state.

## Post-run suite calibration

The initially approved seed and test matrix is deliberately broader than the
expected long-term suite. After implementation and representative real-model
runs, maintainers perform a separate calibration review using observed cost,
runtime, variance, failures, artifact usefulness, and requirement coverage.

The review identifies:

- seeds or tests that add little information beyond another case;
- cases whose setup cost is disproportionate to their diagnostic value;
- prompts or assertions that do not isolate guidance clarity;
- missing task types or branch variations that would reveal additional useful
  information about the guidance;
- cases that should remain manual or occasional rather than routine.

The review produces a concrete keep/remove/replace/add proposal with run
evidence. It does not alter the approved specification or implemented suite
until the user approves the proposed changes.

The first calibrated documentation-standard proposal keeps all seeds and
scenarios while separating execution frequency:

- **Routine:** Tests 01–07, 10, 11, 13, and the premature-current-documentation
  pressure case.
- **Extended:** Tests 08, 09, 12, 14, and the failed-generation pressure case,
  in addition to the routine group when a complete run is requested.

Ordinary guidance changes run the routine group on the lower-cost supported
model and use a second-model sentinel set for quickstart quality, generated
output, package ownership, substantial-specification approval, and
current/audience boundaries. Material changes and final behavioral
verification run all scenarios on at least one supported model. A complete
second-model matrix is used only when the change or observed variance justifies
its cost.

Scenario specifications, executable selection, and the exact sentinel set
remain reviewable task-owned decisions. Changes based on later run evidence
return through the same approval boundary.

Guidance-clarity changes use paired variants. The consumer selects an explicit
guidance source whose identity participates in branch cache keys and artifacts:

- a pinned committed baseline from before the proposed guidance change;
- the current concise candidate;
- optional expanded candidates introduced only when the concise wording does
  not correct the observed behavior.

Seeds remain guidance-neutral and reusable across variants. Each candidate
reuses the same seed, prompt, fixture, assertions, and model profile. The
baseline runs first; candidate runs are not improvement evidence until the
targeted behavior appears in representative baseline artifacts. Mixed outcomes
remain visible and may trigger focused repetition, but prompts and assertions
are not relaxed to manufacture a clean comparison.

## Existing task-guidance evaluator

The implementation under `test/task_guidance/` remains a reference prototype
during this task. Subtask 015 does not move it or require it to use the new
library.

Subtask 068 later:

- moves task-guidance evaluation into the maintainer domain;
- adopts the generic kernel and Crystal Lattice environment where they reduce
  duplicated infrastructure;
- preserves task-specific deterministic assertions and review behavior;
- updates existing commands and consumers;
- removes obsolete specialized framework code only after equivalent behavior
  is verified.