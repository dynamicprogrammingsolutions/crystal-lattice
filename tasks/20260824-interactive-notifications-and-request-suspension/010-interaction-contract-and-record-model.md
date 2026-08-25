# Interaction Contract And Record Model

Extend existing session notification records, stores, events, actions, and
history projections with a response-oriented interaction lifecycle.

## Requirements checklist

### Functional requirements

- [ ] Notification records preserve `kind: interaction` and interaction
  lifecycle states without ordinary-notification normalization.
- [ ] Active and terminal interaction states cover pending response,
  suspended, responded, resolved, expired, and cancelled behavior as needed by
  approved execution modes.
- [ ] Interaction records can store plugin-defined choices, forms, timeout,
  default response, request/tool correlation, and submitted response.
- [ ] Response and cancel operations target an exact interaction ID and
  expected revision.
- [ ] Interaction creation, response, cancellation, expiry, and resolution
  publish authoritative lifecycle events.
- [ ] Active interactions expose compact waiting-for-input projections.
- [ ] Interaction records remain available to notification history.

### Non-functional requirements

- [ ] Existing notification storage and application APIs remain the
  authoritative persistence boundary.
- [ ] Active interactions cannot be ordinarily dismissed or silently pruned.
- [ ] Lifecycle transitions are atomic, revisioned, and reject stale or
  duplicate responses safely.
- [ ] Plugin-defined response values are validated and stored without exposing
  unrelated sensitive context.
- [ ] Ordinary notification behavior remains compatible.
- [ ] Unknown future interaction fields remain forward-compatible.

Parent Task:
`tasks/20260824-interactive-notifications-and-request-suspension/000-main.md`

Depends On:

- `tasks/20260619-generic-session-notifications/020-stage-1-backend-notification-substrate.md`
- `tasks/20260619-generic-session-notifications/030-stage-1-sdk-and-rn-notification-ui.md`
- `tasks/20260619-generic-session-notifications/040-stage-1-dummy-plugin-integration-tests.md`
- `tasks/20260824-operational-notifications-and-global-attention/030-request-operation-notifications-and-status.md`

## Open requirement questions

1. Should interaction response be a generic notification mutation endpoint or
   a platform action bound to an application service?
   - Recommendation: use a generic revision-safe application operation that
     standard follow-up actions invoke, keeping plugin response semantics in
     stored action definitions/handlers.

## Execution plan

Status: Draft

Extend notification validation and transition services with `interaction`
kind/state, structured interaction metadata, exact-revision response/cancel
operations, and interaction lifecycle events. Reuse the same session metadata
storage, locking, persistence, event publication, current-list, and history
boundaries.

Add one non-default dummy interaction plugin that creates choices/forms and
handles response without waiting or restarting a request. Use it to establish
backend, public HTTP, SDK type, and action-follow-up contracts before execution
subtasks add waiters.

### Implementation decisions and open questions

- Decision: no second interaction store.
- Decision: response is authoritative server state, not frontend-local action
  completion.
- Decision: active interactions have no ordinary Dismiss operation.
- Open: approve generic response operation boundary.

### Documentation

- Update notification product, technical, frontend, and requirements pages.
- Update plugin authoring guide with non-blocking interaction examples.
- Update SDK types and current/history documentation.

### Task checklist

- [ ] Approve lifecycle states and response operation.
- [ ] Extend validation and persisted record model.
- [ ] Add atomic response/cancel/expire/resolve transitions.
- [ ] Add interaction lifecycle events and compact projections.
- [ ] Add dummy interaction producer/actions.
- [ ] Add core, application, HTTP, and SDK tests.
- [ ] Update specifications and plugin docs.

### Requirement verification

- An interaction survives session reload with exact kind/state/display/form.
- Exact-revision response stores values and terminal/next state.
- Stale/duplicate response is rejected or idempotently reported.
- Ordinary Dismiss is unavailable while active.
- Existing ordinary notification tests remain compatible.

### Additional implementation verification

- Active interaction retention cannot prune unresolved records.
- Response values cannot inject unsupported display/action fields.
- History preserves specialized interaction status.