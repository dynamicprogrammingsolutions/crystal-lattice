# Shared connection lifecycle controller

Implement the portable lifecycle foundation that separates saved records,
focused workspaces, runtime resources, and attempts while normalizing direct,
discovery, bridge, and cloud connection outcomes.

## Requirements checklist

- [ ] A shared multi-runtime-capable state/controller model represents
  connection focus, per-connection runtime status, attempts, errors, and
  resources without persisting runtime objects.
- [ ] Open, reconnect, validate, pair, repair, cancel, supersede, and close
  operations enforce attempt identity and generation authority after every
  asynchronous boundary.
- [ ] Candidate validation is non-destructive and promotes atomically before a
  one-runtime host closes the replaced runtime.
- [ ] Direct, discovery, bridge, and cloud adapters return normalized success,
  cancellation, repair, and error outcomes without changing existing
  transport routing or replay behavior.
- [ ] Closing or cancelling disposes owned resources idempotently and cannot be
  reversed by a late completion.
- [ ] Deterministic automated tests demonstrate the shared lifecycle races and
  adapter-specific normalization at their appropriate boundaries.

Parent Task: `tasks/20260823-frontend-connection-lifecycle/000-main.md`

Depends On: `tasks/20260823-frontend-connection-lifecycle/010-connection-lifecycle-specification.md`

## Supporting details

- Normative requirements: `FCL-001`–`FCL-008`, `FCL-012`–`FCL-014`.
- **Fact:** The current `Transport` contract is request-shaped and should remain
  independent from lifecycle methods.
- **Fact:** Shared controllers already extend `SimpleSubscribable`, and
  `frontend-sdk-react` already exports a generic `useSubscribableSnapshot`.
  A lifecycle-specific React package API is not needed merely to observe a
  controller.
- **Fact:** Bridge transports already expose connect/disconnect/resume and must remain
  behaviorally intact, including opt-in WebSocket/HTTP/hybrid selection and no
  automatic fallback.
- **Fact:** `FetchTransport` and HTTP bridge requests reject non-success HTTP
  responses, while `CloudTransport` currently returns them as successful
  transport results. `RestAgentBackend` assumes transport failures are
  rejected.
- **Fact:** Desktop validates manual connections through
  `RestAgentBackend.listAgents()` and already presents several open runtimes.
  Its local hook is useful behavior evidence but lacks
  stale-completion authority and supports only manual records.
- **Fact:** Mobile owns connection-specific timeout rules and transport
  factories. Shared adapters therefore need factory injection rather than
  importing application constants.
- **Constraint:** Mobile adoption, connection wizard presentation, and saved
  bridge repair record updates belong to subtask 030.
- **Constraint:** Full desktop migration to all connection kinds is outside
  this task set, but one real compatibility consumer is required for the new
  shared helper.

## Execution plan
Status: Draft

Implement a headless `SimpleSubscribable` lifecycle controller under the
frontend SDK connection domain. Keep saved-record persistence outside the
controller: it receives records for operations, owns transient attempts and
runtime resources, and exposes focus as non-persistent workspace state that
subtask 040 can later hydrate.

The controller will be multi-runtime-capable and use immutable snapshots.
Runtime presence, attempt progress, focus, and last lifecycle error remain
separate state dimensions. A host can derive Closed, Opening, Open,
Reconnecting, Unavailable, Repair required, or Error without discarding an
existing runtime merely because another candidate is opening.

### Controller and state boundary

Define exported portable types for:

- lifecycle error category, retryability, recovery action, and redacted
  diagnostics;
- attempt kind, phase, ID, scope, generation, and terminal result;
- candidate/runtime resource containing connection identity, kind, transport,
  backend, opened timestamp, and non-sensitive adapter metadata;
- controller snapshot containing focused connection ID, runtime map, active
  attempt map, and connection-scoped last errors;
- typed Open/Reconnect/Cancel/Close results.

The controller provides host-neutral equivalents of:

- focus or clear focus without opening/closing;
- open/reconnect a saved record with an optional runtime to replace only after
  promotion;
- close one or all runtimes;
- cancel/supersede one operation scope;
- obtain the runtime/backend for any connection ID;
- begin an interactive attempt for a multi-step pairing/repair flow;
- dispose all attempt and runtime resources.

No controller method navigates, presents alerts, edits saved records, or
persists runtime objects.

### Attempt authority and resource ownership

Use a monotonically increasing generation per operation scope. A scope is a
saved connection ID for ordinary lifecycle work or a temporary wizard/repair
scope supplied by the host. Independent scopes can progress concurrently.

Starting a conflicting attempt invalidates its predecessor. Closing a
connection and disposing the controller also invalidate applicable attempts.
Every controller-owned await checks the lease before publishing state,
promoting resources, returning a navigation-eligible success, or recording an
error.

An attempt lease owns:

- attempt ID, scope, kind, generation, and optional connection ID;
- an `AbortSignal` where the runtime supports physical abort;
- candidate resources registered with idempotent disposers;
- an authority check used before/after each host-driven interactive step;
- phase updates and terminal success/failure/cancel/supersede completion.

The public interactive-attempt API supports bridge discovery/request-code/
submit-code pipelines in subtask 030 without embedding bridge UI or allowing a
cancelled host callback to commit through the controller. Physical abort is a
resource optimization; generation authority remains decisive.

Opening is transactional:

1. select the adapter and begin an attempt;
2. create and immediately register the candidate disposer;
3. validate the candidate;
4. confirm authority;
5. publish the candidate as the connection runtime;
6. atomically remove an explicitly replaced runtime from the snapshot;
7. dispose the replaced runtime after the promoted runtime is available.

Failure, cancellation, or supersession disposes only the candidate and leaves
an existing runtime intact.

### Connection-kind adapters and errors

Define an adapter registry keyed by `ConnectionKind`. Standard adapter builders
are parameterized by host-supplied transport factories and validation options
so mobile/desktop retain their timeout rules and test injection.

- Manual and discovery adapters derive/use direct HTTP record addresses,
  construct `FetchTransport` + `RestAgentBackend`, and validate through an
  injected readiness function whose default is `backend.listAgents()`.
- The bridge adapter constructs the selected unchanged
  `BridgeConnectionTransport`, registers `disconnect()` before awaiting
  `connect()`, preserves saved WebSocket/HTTP/hybrid mode and pairing fields,
  and maps known pairing/server/capability failures without fallback. A saved
  record with no pairing credential returns Repair required without promotion;
  a successful connect must remain paired to the expected server ID.
- The cloud adapter constructs `CloudTransport` + `RestAgentBackend` and uses
  the same injectable readiness boundary as direct HTTP.
- Unsupported/malformed records fail as `invalid_configuration` without
  creating runtime state.

Align `CloudTransport` with the request behavior assumed by
`RestAgentBackend`: parse the response body, then reject non-success HTTP
responses with status/method/path/detail while preserving successful response
shapes. Add direct tests for authorization/server errors and keep successful
cloud integration behavior unchanged.

Central error normalization maps known timeout, network, HTTP auth,
bridge-pairing, identity-mismatch, unavailable-server, unsupported-capability,
and invalid-configuration causes to `ConnectionLifecycleError`. Diagnostic
metadata excludes bridge/cloud tokens, pairing codes, authorization headers,
and request bodies.

### Real consumer and compatibility boundary

Migrate desktop's manual-only `useOpenConnections` implementation to own one
shared controller instance and observe it through the existing generic
subscribable hook. Preserve the hook's local return API and current
ConnectionsPanel status vocabulary, while deriving it from controller state.

This limited consumer migration:

- proves that the shared controller supports multiple real open connections;
- fixes close/cancel during a pending desktop open;
- keeps desktop manual-only behavior and current UI unchanged;
- does not add bridge, discovery, or cloud editing/opening to desktop.

Do not add a lifecycle-specific `frontend-sdk-react` hook unless implementation
finds that the generic subscribable hook cannot correctly own/dispose the
controller. Mobile adoption remains entirely in subtask 030.

### Verification strategy

Shared controller tests use deferred fake adapters and explicit disposer
spies. They own the complete ordering matrix once:

- attempt A is superseded by B, then resolves/rejects late;
- close/cancel happens while creation or validation is pending;
- replacement validation fails while an old runtime remains open;
- a new runtime promotes before the replaced runtime is disposed;
- two connection scopes open/recover independently;
- interactive pairing phases cannot commit after cancellation;
- controller disposal terminates every candidate/runtime exactly once.

Adapter tests cover only kind-specific construction, readiness, disposal, and
error mapping. Cloud transport tests cover HTTP non-success behavior. A
desktop hook test uses a delayed real wrapper/fake fetch boundary to verify
that Close during Connecting remains closed after late resolution.

Add one focused production-adapter integration using the existing bridge Docker
harness, preferably opening a saved bridge record through the controller and
calling `listAgents()`. Run one existing successful local cloud integration
slice after changing `CloudTransport`. Hosted provider tests are not necessary
because this work does not change provider behavior.

### Implementation decisions and open questions

- **Recommendation for approval:** Put lifecycle types, controller, attempt
  lease, error normalization, and adapter builders under
  `packages/frontend-sdk/src/connections/`.
- **Recommendation for approval:** Reuse the existing generic
  `useSubscribableSnapshot`; do not add a dedicated React package API in this
  subtask.
- **Recommendation for approval:** Include the limited desktop manual-hook
  migration as the real consumer, while deferring full desktop connection-kind
  support.
- **Recommendation for approval:** Use injectable readiness validation with
  `backend.listAgents()` as the direct/cloud default. Bridge saved-record open
  retains transport `connect()` as its required pairing/resume validation and
  may opt into an application readiness probe at the host boundary.
- **Recommendation for approval:** Make non-success `CloudTransport` responses
  reject like direct/HTTP bridge responses. This is a shared transport
  consistency correction and may expose previously silent cloud failures to
  callers.
- **Recommendation for approval:** Expose a controlled interactive-attempt
  lease for subtask 030 rather than putting bridge pairing UI/state in the
  shared controller.
- **Decision:** Logical generation checks remain required even when an
  `AbortSignal` is available.
- **Decision:** Cancellation/supersession are typed terminal outcomes, not
  user-visible errors.
- No unresolved requirement question remains if the recommendations above are
  accepted with this plan.

### Documentation

- Add `packages/frontend-sdk/docs/development/connection-lifecycle-implementation.md`
  and route it from the package development index. Document current state
  ownership, adapter injection, attempt authority, redacted errors, and test
  entry points without copying the cross-package target.
- Update desktop development documentation only for the delivered manual-hook
  consumption and its continued connection-kind limitation.
- Do not create frontend-sdk-react documentation unless that package changes.
- Update the root `requirements.md` with partial implementation/evidence only;
  020 does not make mobile-wide `FCL-*` requirements complete.
- Do not change bridge transport user documentation unless its current
  observable contract changes.
- Document the corrected current CloudTransport non-success behavior in
  package development/user reference only if an existing page presents its
  response semantics.

### Task checklist

- [x] Inspect current controller/export patterns, host factories, transport
  semantics, and desktop consumer boundary.
- [ ] Add portable lifecycle state, error, attempt, and result types.
- [ ] Implement the subscribable controller, operation leases, and
  per-scope generations.
- [ ] Implement candidate registration, promotion, replacement, cancellation,
  close, and idempotent disposal.
- [ ] Add factory-driven direct/discovery, bridge, and cloud adapters.
- [ ] Add lifecycle error normalization and credential-safe diagnostics.
- [ ] Make CloudTransport reject non-success HTTP responses consistently.
- [ ] Export the shared lifecycle API from the frontend SDK.
- [ ] Add deterministic controller and interactive-attempt tests.
- [ ] Add focused adapter and CloudTransport contract tests.
- [ ] Migrate desktop's manual `useOpenConnections` wrapper without UI/API
  expansion.
- [ ] Add desktop close-during-open and multi-open consumer tests.
- [ ] Add one controller-backed bridge integration and run one successful
  cloud integration slice.
- [ ] Update current package development documentation and requirement evidence.
- [ ] Run shared SDK tests/typecheck, affected desktop tests/typecheck,
  integration slices, documentation tests/build, and diff checks.

### Requirement verification

- `FCL-001`–`FCL-002`: snapshot tests keep focus, runtime, and attempts
  independent under one stable saved ID; full cross-frontend completion
  remains with later subtasks.
- `FCL-003`–`FCL-005`: deferred-promise tests cover authority after each
  boundary, terminal cancellation/supersession, candidate-only cleanup,
  non-destructive failure, and promotion-before-replacement disposal.
- `FCL-006`–`FCL-007`: adapter/error tests cover every connection kind,
  readiness, malformed records, cloud non-success, and bridge
  missing-pairing/server-identity/capability categories.
- `FCL-008`: shared reconnect operations are generation-safe and return state
  only; native foreground orchestration remains with subtask 030.
- `FCL-012`: shared and desktop consumer tests keep two runtimes open
  independently and prove close-during-open cannot late-reopen.
- `FCL-013`: typed connection-targeted lookup/outcomes can use any matching
  open runtime without changing focus; deep-link host adoption remains later.
- `FCL-014`: runtime objects are absent from persistence APIs. Focus/cache
  hydration remains explicitly assigned to subtask 040.

### Additional implementation verification

- `npm --workspace @crystal-lattice/frontend-sdk test`
- `npx tsc -p packages/frontend-sdk/tsconfig.json --noEmit`
- focused desktop Jest test for the migrated hook, followed by the desktop
  fast suite and TypeScript check;
- the controller-backed bridge scenario selected through the frontend SDK
  `integration:bridge` script;
- the existing successful CloudTransport workspace scenario selected through
  the frontend SDK `integration:cloud` script;
- documentation preparation tests, preparation, normal MkDocs build, and
  `git diff --check`;
- inspect exported snapshots/diagnostics to confirm runtime resources are not
  persisted and credentials are not present.