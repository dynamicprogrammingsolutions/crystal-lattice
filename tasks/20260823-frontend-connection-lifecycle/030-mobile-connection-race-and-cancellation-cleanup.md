# Mobile connection race and cancellation cleanup

Adopt the shared lifecycle foundation in mobile and correct stale completion,
repair cancellation, destructive switching, foreground recovery, and
connection-driven navigation across all supported connection kinds.

## Requirements checklist

- [ ] Cancelling manual, discovery, bridge discovery/pairing/repair, cloud, or
  saved reconnect prevents every late state, alert, credential, and navigation
  effect and disposes temporary resources.
- [ ] Starting or completing a newer connection or navigation intent prevents
  an older attempt or foreground recovery from replacing it.
- [ ] A failed candidate leaves an existing usable runtime and workspace
  intact.
- [ ] Bridge repair preserves the saved connection ID, cache ownership,
  selected transport mode, and rollback behavior without duplicating records.
- [ ] Mobile connection rows and wizards present connection-scoped status,
  errors, and recovery actions instead of relying on one global loading state.
- [ ] Connection/session navigation and component/cache callbacks remain
  scoped to the intended connection after switching.
- [ ] Production mobile tests cover the reported cancel/stuck-server-list and
  late-timeout navigation regressions.

Parent Task: `tasks/20260823-frontend-connection-lifecycle/000-main.md`

Depends On: `tasks/20260823-frontend-connection-lifecycle/020-shared-connection-lifecycle-controller.md`

## Supporting details

- Normative requirements: `FCL-001`–`FCL-013`, `FCL-021`.
- Current bridge repair awaits connection/server discovery before clearing and
  replacing global state, so a late repair can disrupt a newer connection.
- Current wizard cancellation clears visible fields without logically
  cancelling the attempt or disconnecting the temporary bridge transport.
- Saved connection selection disconnects the current transport before the
  candidate validates.
- `ConnectedRoot` navigates to Sessions after an attempt function resolves,
  even when that function handled a failure or entered repair.
- The bridge WebSocket compatibility default and explicit HTTP/hybrid mode
  behavior must remain unchanged.

## Execution plan
Status: Draft

Replace mobile's connection-operation booleans and global temporary bridge
state with the shared lifecycle controller and explicit wizard-attempt state.
Retain `App.tsx` as the host for native AppState, linking, and transport
factories while extracting connection UI coordination into focused hooks or
components.

Make connection selection focus-aware but keep full offline presentation in
subtask 040. Opening creates and validates a candidate; mobile's initial
one-runtime policy closes the old runtime only after successful promotion.

Bridge repair carries the original connection ID and updates that record after
authoritative pairing. Cancel invalidates the attempt, disconnects temporary
resources, clears repair presentation, and returns to the prior workspace.

Move navigation decisions to typed current user-intent outcomes. Key session
screens and callbacks by connection/session, and ensure foreground recovery
updates only its owning runtime status.

### Implementation decisions and open questions

- **Decision:** Mobile may retain one open runtime in this subtask, but it
  consumes the multi-runtime-capable shared model.
- **Recommendation:** Separate tapping/focusing a connection row from its
  Open/Retry control in preparation for subtask 040; if one gesture does both,
  focus must still survive open failure.
- **Decision:** Repair updates the original bridge record rather than creating
  a new ID.
- **Decision:** Do not add automatic transport fallback or change saved bridge
  mode defaults.
- No unresolved requirement question blocks planning.

### Documentation

- Update mobile development documentation with the current lifecycle host,
  controller boundary, repair ownership, and test entry points.
- Update mobile user guidance only for delivered visible status/cancel/repair
  behavior.
- Update `FCL-*` and affected `BRG-013` evidence only when behavior is
  implemented and verified; do not restate bridge routing.

### Task checklist

- [ ] Add mobile lifecycle-controller host and connection-kind adapter wiring.
- [ ] Replace global attempt/loading behavior with per-connection/wizard state.
- [ ] Implement authoritative cancel and temporary-resource disposal.
- [ ] Implement candidate promotion and post-promotion one-runtime policy.
- [ ] Implement stable-ID bridge repair and clean repair restart.
- [ ] Make foreground recovery generation-safe and non-navigating.
- [ ] Scope selected session, screen identity, and callbacks by connection.
- [ ] Add portable status/error/recovery presentation and stable selectors.
- [ ] Add deterministic component regression tests.
- [ ] Run production-screen iOS and Android cancellation/race scenarios.
- [ ] Run mobile typecheck/Jest and focused bridge compatibility tests.
- [ ] Update current docs and requirement evidence.

### Requirement verification

- `FCL-003`–`FCL-005`, `FCL-010`: deferred-operation tests reverse A/B
  completion order, cancel before completion, and confirm old runtime/focus
  preservation.
- `FCL-001`, `FCL-007`: bridge repair uses the same record ID and all three
  bridge modes preserve their existing routing/default contract.
- `FCL-006`, `FCL-021`: component/native tests observe scoped statuses,
  actions, accessible labels, and stable selectors.
- `FCL-008`: foreground recovery for A finishing after focus moves to B cannot
  navigate, clear B, or apply A's credential to B.
- `FCL-011`: same session IDs under two connection IDs retain independent
  components, callbacks, and cached state.

### Additional implementation verification

- Repeated repair open/cancel/open starts with a current server list and no
  leaked temporary bridge socket.
- Discovery results from a cancelled scan cannot populate a later wizard.
- Cloud authentication/non-success validation cannot promote a runtime.
- Existing app deep-link and notification flows retain explicit
  connection/session scope.