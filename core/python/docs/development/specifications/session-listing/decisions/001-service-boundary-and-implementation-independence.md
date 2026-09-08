# Decision: session-list service boundary and implementation independence

## Context

`SessionListService` already owns the shared application result consumed by
Python, terminal, and HTTP callers. It composes store records, complete
sessions, application-plugin actions, presentation declarations, ordering,
filters, limits, and diagnostics.

The current process-local cache cannot avoid rebuilding every summary in a new
runtime. A local cached/background resolver can address slow on-demand files,
but future stores may provide a remote index, database projection, cloud
metadata, or another materially different resolution model. Concepts such as
a local cache root or foreground scan timeout do not apply universally.

Exposing the first implementation's cache, scanner, future, generation,
placeholder state, worker settings, or persistence backend would turn a
replaceable correction into a public platform commitment.

## Decision

Keep `SessionListService` as the sole stable application-facing session-list
boundary. Preserve its existing public methods and summary return shape.

The service may receive opaque application context. The selected
implementation interprets only the configuration it needs. Common application
wiring does not introduce a shared implementation-specific configuration
model.

Resolution, reuse, persistence, deadlines, placeholders, scheduling,
concurrency, and cleanup remain private implementation behavior. The service
may contain this behavior directly or delegate to package-private classes; no
public strategy or backend interface is required.

Metadata-only entries use the ordinary summary shape and do not expose a
client-visible scan or placeholder marker. HTTP and terminal adapters continue
to delegate to `AgentApplication`.

The initial implementation may use persistent local derived state, a bounded
foreground interval, and private background work. A later implementation may
replace all of those mechanisms while preserving the service contract.

## Consequences

- Existing application and adapter call sites remain stable.
- Client packages do not need scan-state or polling changes.
- Implementation-specific settings can evolve with their owner instead of
  becoming universal session-list keys.
- A cloud-backed implementation can avoid meaningless local-cache and timeout
  concepts.
- Tests for the stable contract use `SessionListService` and
  `AgentApplication`; focused tests may exercise private implementation
  classes without making them supported extension points.
- The initial implementation must infer internally which entries are complete
  or metadata-only in order to apply its temporary ordering and filtering
  behavior.
- Operators cannot depend on cache paths, storage formats, worker internals, or
  scan progress as public APIs.