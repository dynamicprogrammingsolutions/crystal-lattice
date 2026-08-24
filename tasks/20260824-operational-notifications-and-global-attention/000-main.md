# Persistent Operational Notifications, Global Attention, And Request Status

Make important backend failures and request lifecycle state authoritative and
persistent, while allowing selected notifications to request temporary
attention across the frontend without changing their real connection/session
ownership or dismissal lifecycle.

## Requirements checklist

- [ ] Terminal request and operational action failures that reach the server
  are persisted as notifications belonging to their actual session or
  connection.
- [ ] Validation, connection-lifecycle, transport-local, and short-lived
  frontend failures remain ephemeral when persistence would be misleading or
  unavailable.
- [ ] A notification may request temporary frontend-global attention while
  retaining its authoritative connection/session scope and lifecycle.
- [ ] Global attention can inform the user about important work in another
  session or open connection, and an explicit View action can navigate to the
  owning workspace.
- [ ] Closing, timing out, or swiping away a global attention banner does not
  dismiss the authoritative notification in its owning session or
  connection.
- [ ] Request lifecycle state is represented through a persisted portable
  operation/status contract that frontends can recover after navigation,
  reconnect, or restart.
- [ ] Users can configure which request lifecycle transitions request global
  attention without changing the persisted request lifecycle itself.
- [ ] Streaming events remain the real-time transport for request output and
  notification updates, while persisted notification state is authoritative
  for recovery and history.
- [ ] Frontend-local loading state such as HTTP fetches and short UI mutations
  remains separate from persisted server operation status.

## Scope and sequencing

This task has four implementation workstreams:

1. persist selected request and action failures with the current notification
   ownership model;
2. define global attention semantics and authoritative cross-session delivery;
3. standardize persisted request-operation and status-display records;
4. integrate global attention across mobile and desktop open connection
   runtimes.

The final frontend integration consumes the connection/runtime model owned by
`tasks/20260823-frontend-connection-lifecycle/`. It does not create a second
connection manager or redefine focus, runtime opening, deep-link authority, or
offline workspace behavior.

Generic notification history UI remains in
`tasks/20260619-generic-session-notifications/045-stage-1-authoritative-dismissal-retention-history-and-interaction-readiness.md`.
This task must leave records and compact projections suitable for that later
history work.

## Open requirement questions

1. Where should request-attention preferences be persisted?
   - Recommendation: device-local initially, because mobile and desktop may
     reasonably use different attention behavior. A later user-profile
     contract could synchronize them explicitly.

## Subtasks

- [ ] `tasks/20260824-operational-notifications-and-global-attention/010-persistent-request-and-action-errors.md`
- [ ] `tasks/20260824-operational-notifications-and-global-attention/020-global-attention-contract-and-delivery.md`
- [ ] `tasks/20260824-operational-notifications-and-global-attention/030-request-operation-notifications-and-status.md`
- [ ] `tasks/20260824-operational-notifications-and-global-attention/040-global-attention-frontend-integration.md`

## Supporting details

- **Fact:** Request errors currently reach frontends primarily through
  session event streams and are reconstructed from the latest observed
  events.
- **Fact:** Action failures currently return direct error envelopes and are
  commonly rendered as short-lived frontend alerts.
- **Fact:** Session and application notifications already provide durable
  lifecycle state, revisions, events, dismissal, resolution, retention,
  follow-up actions, and future history compatibility.
- **Fact:** The shared request coordinator in
  `core/python/agent_app/request_execution.py` provides one application-owned
  request-start boundary.
- **Fact:** Mobile multi-open runtime ownership and cross-runtime backend
  lookup are planned in
  `tasks/20260823-frontend-connection-lifecycle/060-mobile-multiple-open-connections.md`.
- **Fact:** Desktop shared-controller convergence is planned in
  `tasks/20260823-frontend-connection-lifecycle/070-desktop-connection-workspace-ux.md`.
- **Decision:** Notification ownership remains authoritative. Global
  attention is a temporary local presentation, not a third notification
  scope.
- **Decision:** Connection open/reconnect/pairing/repair failures remain under
  the connection-lifecycle error contract rather than becoming server
  notifications.
- **Decision:** Request events remain available during migration and for
  streaming; persisted request-operation state becomes the recovery
  authority.
- **Decision:** The portable operation/status-display shape should also be
  usable by long-running operations such as OpenAI Responses native
  compaction.

## Execution plan

Status: Draft

Execute the four subtasks in dependency order. Backend error persistence,
attention contracts, and request-operation records may proceed before mobile
multi-open work is delivered. Final cross-connection frontend integration
waits for the connection-lifecycle dependencies declared by subtask 040.

Each subtask has its own automated verification. Manual checkpoints are for
visual, interaction, and real-device/native validation and do not replace
automated unit, integration, SDK, component, or native UI coverage.

Stop and request approval if implementation requires changing notification
ownership, connection-lifecycle semantics, message/model visibility, or
frontend navigation beyond the boundaries recorded here.

### Implementation decisions and open questions

- **Decided:** Persistent server-side failures use the same authoritative
  notification store as their owning scope.
- **Decided:** Global attention acknowledgement is frontend-local and does not
  invoke notification dismissal.
- **Decided:** A global attention banner never changes focus automatically.
  View is an explicit navigation intent.
- **Decided:** A producer marks a notification transition as attention
  eligible; frontend preferences may suppress eligible transitions.
- **Decided:** In-app global attention covers currently open runtimes. It does
  not introduce operating-system push delivery or implicitly open saved
  connections.
- **Decided:** Request operation state, connection runtime state, cache
  freshness, and frontend-local loading remain independent dimensions.
- **Open:** Resolve device-local versus server/user-scoped request-attention
  preferences before implementing the settings surface.

### Documentation

- Update the cross-package notification product, technical, frontend, and
  requirement pages for persistent operational errors, attention semantics,
  operation/status metadata, and recovery authority.
- Update application development documentation for error classification and
  request-operation publication.
- Update frontend SDK development documentation for attention controllers,
  operation selectors, compact projections, and migration fallback.
- Update mobile and desktop user/development documentation only when the
  corresponding behavior is delivered.
- Update plugin-authoring documentation so producers can mark an eligible
  important notification without controlling frontend navigation or local
  preference policy.
- Cross-link the background-compaction task where it consumes the common
  operation/status-display contract.

### Task checklist

- [ ] Resolve the preference-persistence requirement question and approve the
  Draft plans.
- [ ] Execute and verify subtask 010.
- [ ] Execute and verify subtask 020.
- [ ] Execute and verify subtask 030.
- [ ] Confirm the connection-lifecycle dependencies for subtask 040 are
  delivered.
- [ ] Execute and verify subtask 040.
- [ ] Complete mobile and desktop visual/native checkpoints.
- [ ] Reconcile notification specifications, requirement evidence, and
  current documentation.
- [ ] Record completion notes in the main task and completed subtasks.

### Requirement verification

- Persistent error requirements: public application/request/action tests prove
  the correct failures persist in the correct scope and excluded failures
  remain ephemeral.
- Global attention requirements: backend/SDK tests prove attention eligibility,
  expiry, authoritative hydration, and local acknowledgement without
  notification dismissal.
- Request status requirements: request coordinator, persistence, reconnect,
  restart, and frontend selector tests prove authoritative lifecycle recovery
  with event fallback.
- Cross-connection requirements: production mobile and desktop hosts receive
  attention from unfocused open runtimes, retain labels, and navigate only
  after an explicit View action.
- Compatibility: existing request streaming, action responses, notifications,
  connection lifecycle, session caches, and ordinary frontend-local loading
  remain functional.

### Additional implementation verification

- Notification/session-list payload growth remains bounded when many request
  operation records exist.
- Event cursor expiry and reconnect recover eligible attention without
  replaying stale banners.
- Multiple open runtimes do not share attention acknowledgement keys or
  request-operation selectors.
- Cached offline session state does not claim a stale running operation is
  current without authoritative refresh.
