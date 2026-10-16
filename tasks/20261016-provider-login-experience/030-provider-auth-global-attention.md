# Provider Authentication Global Attention

Surface selected provider-authentication transitions as temporary
application-global attention after core login and owning notifications are
complete.

## Requirements checklist

- [ ] Authentication-required, revoked-credential, refresh-failure, and
  login-needs-intervention transitions can request global attention according
  to user preferences.
- [ ] Attention retains the owning connection and optional session identity
  while the user views another open connection or screen.
- [ ] The attention presentation offers explicit View or Sign in behavior and
  never navigates automatically.
- [ ] Closing, timing out, or swiping away attention acknowledges only the
  temporary presentation and does not dismiss the owning auth notification.
- [ ] Repeated provider failures with the same lifecycle occurrence do not
  create attention spam.
- [ ] Expired, already acknowledged, or superseded auth attention does not
  reappear after reconnect or host reconstruction.
- [ ] Core login, callback completion, refresh, logout, and owning
  notifications remain functional when attention is disabled or unavailable.
- [ ] This task does not add OS push delivery or automatically reopen closed
  connections.

Parent Task:
`tasks/20261016-provider-login-experience/000-main.md`

Depends On:

- `tasks/20261016-provider-login-experience/020-provider-login-notifications-and-anthropic-adoption.md`
- `tasks/20260824-operational-notifications-and-global-attention/020-global-attention-contract-and-delivery.md`
- `tasks/20260824-operational-notifications-and-global-attention/040-global-attention-frontend-integration.md`

## Open requirement questions

1. Should successful login request attention only when the owning connection
   is not visible, or remain owning-surface-only by default?
2. Which auth transitions are user-configurable versus fixed high-priority
   defaults?
3. Should View and Sign in both be offered from the overlay when the provider
   can start login without first navigating?

## Supporting details

- The practical purpose is to reveal an auth event from another open
  connection or session while preserving its real owner.
- The global-attention platform owns aggregation, expiry, acknowledgement,
  queueing, cross-connection source labels, and View navigation.
- Provider plugins own only the auth lifecycle and the decision that a
  transition is eligible.

## Execution plan

Status: Draft

Map a small set of provider-auth notification transitions onto the generic
attention metadata after the shared attention backend and frontend are
complete. Reuse owning notification identity and lifecycle tokens rather than
creating an auth-specific global store.

Default to attention for conditions requiring user action. Avoid routine
attention for login started, polling progress, successful refresh, or logout.
Treat successful login as a preference or visibility-sensitive policy to be
approved before implementation.

### Implementation decisions and open questions

- Decision: global attention is presentation only and never auth authority.
- Decision: arrival never changes the focused connection or session.
- Decision: local attention acknowledgement never dismisses the owning
  notification.
- Decision: provider auth attention does not introduce push notifications.
- Open: approve success-transition and preference defaults.

### Documentation

- Document auth-transition eligibility and default preference behavior.
- Document View, Sign in, Close, timeout, and swipe semantics.
- Link to owning notification and connection lifecycle documentation rather
  than duplicating those contracts.

### Task checklist

- [ ] Define auth transition eligibility and stable attention tokens.
- [ ] Add Codex auth attention publication.
- [ ] Add Anthropic auth attention publication.
- [ ] Add preference and visibility filtering.
- [ ] Add cross-connection View and Sign in integration tests.
- [ ] Add expiry, acknowledgement, deduplication, and reconnect tests.
- [ ] Complete mobile and desktop visual/native checkpoints.
- [ ] Update provider-auth and global-attention documentation.

### Requirement verification

- An auth-required event from connection B can appear while connection A is
  focused without changing focus.
- View explicitly navigates to B; Sign in executes B's provider action.
- Close, timeout, or swipe hides only the attention presentation.
- Repeated failures do not duplicate attention while the persistent owning
  notification remains accessible.

### Additional implementation verification

- Identical provider and session IDs on different connections remain
  independently routed and acknowledged.
- Closing an open runtime stops its attention subscription without mutating
  server auth state.
