# Notification History And Safe Replay

Expose compact, scope-correct application and session notification history with
safe local replay of stored rich displays across mobile and desktop.

## Requirements checklist

### Functional requirements

- [ ] Application and session notification history can be queried through
  stable paginated public APIs.
- [ ] A reusable Notifications action is available in relevant pinnable action
  surfaces.
- [ ] History supports useful status, severity, time, scope, notification type,
  and operation-state filtering.
- [ ] Mobile shows connection/application history from its connection-level
  surface and exact-session history from Chat.
- [ ] Desktop can aggregate connection history with connection labels and show
  active-session history at the message/detail location.
- [ ] Stored inline and modal content can be shown again locally without
  reactivating the notification.
- [ ] Safe non-mutating historical actions remain available where valid.
- [ ] Mutating or stale historical actions are disabled unless explicitly
  declared replayable and validated by the server.
- [ ] Request and background-operation notifications have clear compact
  history representation.
- [ ] Interaction records can be represented without being normalized into
  ordinary notification statuses.

### Non-functional requirements

- [ ] History queries do not load every session or place complete notification
  arrays in generic session-list payloads.
- [ ] Active and terminal retention remain independently bounded.
- [ ] Viewing or replaying history does not increment revisions, reactivate
  records, or publish lifecycle events.
- [ ] Pagination remains stable while notifications are concurrently updated.
- [ ] Unknown future notification, operation, and interaction fields remain
  inspectable without breaking current clients.
- [ ] Shared SDK and React Native components remain portable while platform
  navigation and window conventions stay host-owned.

Parent Task:
`tasks/20260619-generic-session-notifications/000-main.md`

Depends On:

- `tasks/20260619-generic-session-notifications/020-stage-1-backend-notification-substrate.md`
- `tasks/20260619-generic-session-notifications/030-stage-1-sdk-and-rn-notification-ui.md`
- `tasks/20260619-generic-session-notifications/040-stage-1-dummy-plugin-integration-tests.md`
- `tasks/20260824-operational-notifications-and-global-attention/020-global-attention-contract-and-delivery.md`
- `tasks/20260824-operational-notifications-and-global-attention/030-request-operation-notifications-and-status.md`
- `tasks/20260823-frontend-connection-lifecycle/060-mobile-multiple-open-connections.md`
- `tasks/20260823-frontend-connection-lifecycle/070-desktop-connection-workspace-ux.md`

## Open requirement questions

1. Should request/background operation records appear in the default history
   filter?
   - Recommendation: yes, with a type filter and compact operation-specific
     status, because they are authoritative notification occurrences.
2. Which historical actions are replayable by default?
   - Recommendation: only local Show again, `copy_text`, and explicitly safe
     `open_url`; `run_action` requires current server validation and an
     explicit replayable declaration.

## Supporting facts

- Session and application stores retain active and terminal notification
  records with revisions, timestamps, scope, display, retention, and history
  bounds.
- Application history is durable across application and server restart.
- Existing list routes focus on current hydration rather than paginated
  history.
- The previous Stage E plan predates generic request-operation notification
  records and must be reconciled before implementation.
- Multiple-open mobile and converged desktop runtime ownership are prerequisites
  for correct cross-connection production hosting.

## Execution plan

Status: Draft

Define dedicated application and session history query endpoints with stable
scope filters, limits, and opaque cursors. Implement filtering/pagination at
the owning notification store/application boundary rather than scanning
frontend caches.

Add a frontend SDK history model and controller that handles scope changes,
pagination, refresh, filtering, and local replay state. Build portable compact
rows, filters, list states, and replay hosts in shared React Native components.

Integrate production mobile and desktop surfaces only after the relevant
connection lifecycle tasks are complete. Keep replay read-only by default and
route any allowed action through current action validation.

### Implementation decisions and open questions

- Decision: history is the notification projection, including specialized
  operation and interaction records; it is not a second operation audit log.
- Decision: Show again is local presentation state.
- Decision: dedicated history queries remain separate from compact Sessions
  projections.
- Open: approve default operation visibility and historical action allowlist.

### Documentation

- Update notification product, technical, frontend, and requirement
  specifications for history query, cursor, filtering, and replay.
- Update HTTP/API, SDK, shared component, mobile, and desktop documentation.
- Update plugin guidance to distinguish current follow-ups from historical
  replay.

### Task checklist

- [ ] Approve operation visibility and replay policy.
- [ ] Define history query/filter/cursor contracts.
- [ ] Implement application and session history APIs.
- [ ] Implement SDK history types and controller.
- [ ] Implement shared rows, filters, paging, and replay hosts.
- [ ] Integrate mobile action surfaces and scope ownership.
- [ ] Integrate desktop aggregate and active-session history.
- [ ] Add backend, SDK, component, Detox, and macOS tests.
- [ ] Complete mobile/desktop visual and real-device checkpoints.
- [ ] Update specifications and documentation.

### Requirement verification

- Paginated queries return stable, scope-correct active and terminal records.
- Mobile and desktop expose history only at the owning connection/session
  surfaces.
- Show again reproduces stored rich content without changing server state.
- Unsafe historical actions remain unavailable or fail current validation.
- Operation and future interaction records retain their specialized state.

### Additional implementation verification

- Cursor behavior remains deterministic when records update between pages.
- History limits and pagination prevent unbounded memory or payload growth.
- Connection switching cannot replay a display or action against another
  backend.