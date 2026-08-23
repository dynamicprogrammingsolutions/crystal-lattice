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
- The current `Transport` contract is request-shaped and should remain
  independent from lifecycle methods.
- Bridge transports already expose connect/disconnect/resume and must remain
  behaviorally intact, including opt-in WebSocket/HTTP/hybrid selection and no
  automatic fallback.
- Cloud transport currently differs from direct/bridge non-success response
  behavior and needs normalized validation semantics.
- Desktop's local multiple-open hook is useful behavior evidence but lacks
  stale-completion authority and supports only manual records.

## Execution plan
Status: Draft

Define portable lifecycle types and a controller in the shared frontend SDK.
Keep pure state transitions separately testable from adapter side effects.
Expose a subscription/snapshot or equivalent host-neutral API; add React
bindings only where consuming hosts need them.

Introduce connection-kind adapters around existing transport factories. The
controller creates a candidate, validates it, checks operation authority,
promotes it, and then applies host runtime policy. Adapter close is idempotent,
and cancellation invalidates logical authority before physical abort/close.

Use per-connection generations so independent connections can progress
concurrently. A conflicting operation for one connection supersedes only that
connection's older attempt unless an explicit one-runtime host policy closes a
different promoted runtime.

Return typed outcomes for user-intent hosts. Do not navigate or present alerts
inside the shared controller.

### Implementation decisions and open questions

- **Recommendation:** Put lifecycle types/controller/adapters under
  `packages/frontend-sdk/src/connections/`; put React subscription hooks under
  `packages/frontend-sdk-react` only if a thin `useSyncExternalStore`-style
  binding is useful.
- **Recommendation:** Keep adapter validation endpoint selection configurable
  or backend-semantic rather than making the demo `/api/data` route part of the
  lifecycle contract.
- **Decision:** Logical generation checks remain required even when an
  `AbortSignal` is available.
- **Decision:** Cancellation/supersession are typed terminal outcomes, not
  user-visible errors.
- **Question for plan approval:** Whether the first implementation should also
  migrate desktop to the controller or only verify a compatibility consumer.
  Recommendation: keep full desktop migration deferred, but exercise shared
  behavior through one desktop-compatible unit consumer to avoid a
  mobile-only abstraction.

### Documentation

- Update `packages/frontend-sdk/docs/development/index.md` and add a focused
  current implementation page for the lifecycle controller/adapters.
- Update `packages/frontend-sdk-react` development documentation if a public
  binding is added.
- Update `requirements.md` only for behavior actually implemented and
  verified.
- Do not change bridge transport user documentation unless its current
  observable contract changes.

### Task checklist

- [ ] Inspect current host factories and define bounded adapter inputs.
- [ ] Add portable lifecycle state, error, attempt, and result types.
- [ ] Implement pure state transitions and per-connection generations.
- [ ] Implement side-effect coordinator and owned-resource disposal.
- [ ] Add direct/discovery, bridge, and cloud adapters.
- [ ] Normalize cloud/non-success validation behavior.
- [ ] Add deterministic deferred-promise race/cancellation tests.
- [ ] Add focused adapter contract and compatibility tests.
- [ ] Update current package development documentation and requirement evidence.
- [ ] Run shared SDK, React binding, affected mobile, and affected desktop
  checks.

### Requirement verification

- `FCL-001`–`FCL-005`: deterministic state/controller tests cover stable
  identity, separation, authority, cancellation, and candidate promotion.
- `FCL-006`–`FCL-008`: adapter tests cover status/error normalization and
  lifecycle recovery outcomes for each connection kind.
- `FCL-012`: two independent fake adapters remain open and recover
  independently; close-during-open cannot late-reopen.
- `FCL-013`: typed connection-targeted outcomes resolve a matching open
  runtime without implicit focus.
- `FCL-014`: any shared persisted controller preference introduced here has an
  explicit hydration barrier; broader cache hydration remains in subtask 040.

### Additional implementation verification

- Existing bridge transport unit and integration tests remain unchanged and
  passing.
- Existing frontend SDK backend/transport tests pass.
- Type checks demonstrate that runtime resources are not serializable saved
  record fields.
- No credential values appear in lifecycle diagnostics.