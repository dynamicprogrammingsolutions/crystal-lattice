# Crystal Lattice evaluation environment technical specification

This specification owns the Crystal Lattice implementation of the generic
`RunEnvironment` contract.

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

## Reusable review projection

The Crystal Lattice integration owns the interpretation of Crystal Lattice
sessions, application requests, effective configuration, tool events, and
provider usage. It may provide a reusable review projection for result-package
and other evaluation consumers.

The projection represents, when available:

- delivered system and developer instructions plus their provenance;
- user and visible assistant messages;
- effective request configuration and model/effort identity;
- tool-call intent, status, concise failures, and mutation summaries;
- request boundaries and continuation relationships;
- runtime and provider errors;
- aggregate provider usage exposed or estimated by provider plugins.

The projection is designed for review rather than session restoration. It is
lean and human-readable, omits encrypted reasoning and unrestricted tool
results, and redacts authentication or secret configuration. Complete local
diagnostics may remain in the run directory.

The projection records whether important information was captured directly,
reconstructed from saved inputs, inherited from a lineage parent such as the
producer run of a continuation, or unavailable. Reconstructed content is
verified only when it matches an independently recorded identity such as a
hash.

This representation is reusable across Crystal Lattice-backed suites. It does
not define task files, documentation pages, semantic scores, assessment
prompts, or suite stages.

## Relationship to the kernel

The adapter may expose Crystal Lattice application, session, tool-loop,
snapshot, observation, evaluation, and presentation facilities. Alternate
environments are not required to implement these concepts.
