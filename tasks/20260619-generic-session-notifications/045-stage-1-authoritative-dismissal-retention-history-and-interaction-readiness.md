# Authoritative Dismissal, Retention, History, and Interaction Readiness

Replace the current frontend-local notification dismissal model with
server-authoritative lifecycle state, add bounded retention and user-visible
history/replay, and generalize the Stage 1 contract so Stage 2 interactions can
build on it without replacing the notification substrate.

## Requirements checklist

- [ ] A session notification and its dismissal state are stored together in
  the owning session.
- [ ] An application notification and its dismissal state are stored together
  in the server-side application notification store.
- [ ] The frontend that dismisses a notification updates immediately after a
  successful server response.
- [ ] Other already-open frontends are not required to reconcile the dismissal
  immediately, but a newly opened, reconnected, or explicitly refreshed
  frontend does not present a server-dismissed notification.
- [ ] Ordinary notification lifecycle supports at least `pending`,
  `dismissed`, `resolved`, and `expired` terminal behavior with validated
  transitions.
- [ ] Notification records have an explicit monotonic revision used for stale
  mutation detection and event/snapshot ordering.
- [ ] Stable-key deduplication applies to active records; creating with the key
  of a terminal record creates a new lifecycle occurrence.
- [ ] Retention supports an extensible policy object with initial policies for
  explicit resolution, TTL, request completion, and server lifetime.
- [ ] Active and terminal/history limits are distinct; active interactions are
  never silently pruned.
- [ ] Application notifications expose an authoritative current-state
  snapshot/list path so event-cursor bootstrap is not the only hydration
  mechanism.
- [ ] A reusable Notifications action is available through the top pinnable
  action surface on relevant mobile and desktop screens.
- [ ] Notification history provides compact, scope-correct views of active and
  terminal records with status/severity/time filtering.
- [ ] Historical inline and modal content can be shown again locally without
  reactivating or mutating the stored notification.
- [ ] Historical action replay is safe by default: mutating `run_action`
  entries require explicit validity and server-side lifecycle/revision
  validation.
- [ ] Direct action displays remain transient displays unless the producer
  explicitly creates a notification; closing a transient display does not
  create notification history.
- [ ] Notification follow-up routing preserves fixed parameters, parameter
  mappings, embedded forms, submitted form values, and connection/session
  ownership on every supported host.
- [ ] The persisted type model can represent `notification` and `interaction`
  records without normalizing interactions back to Stage 1 notification
  statuses.
- [ ] Active interactions are nondismissible and expose response, cancellation,
  timeout, and eventual resolution rather than ordinary dismissal.
- [ ] Session lists/tabs can indicate that a session is waiting for input
  without presenting the complete interaction outside its owning Chat.
- [ ] Wait-only interaction response/cancel operations can later be admitted
  safely while application reload is draining, without admitting arbitrary new
  work.
- [ ] Real-suspend interaction continuation remains owned by an owner-aware
  request scheduler rather than direct plugin calls to the low-level
  `AgentApplication.send_request` iterator.
- [ ] Root specifications remain the only normative explanation; package docs
  map implementation and tests without duplicating lifecycle semantics.
- [ ] Any implementation discovery that requires materially more complex
  architecture or crosses the approved ownership boundaries stops for user
  review before implementation continues.

Parent Task:
`tasks/20260619-generic-session-notifications/000-main.md`

Depends On:

- `tasks/20260619-generic-session-notifications/020-stage-1-backend-notification-substrate.md`
- `tasks/20260619-generic-session-notifications/030-stage-1-sdk-and-rn-notification-ui.md`
- `tasks/20260619-generic-session-notifications/040-stage-1-dummy-plugin-integration-tests.md`
- `tasks/20260730-runtime-notification-specification-documentation/000-main.md`

## Accepted product decisions

### Same-authority persistence

The notification record and its dismissal state have the same authoritative
server-side owner:

- session notification → session metadata;
- application notification → application notification store.

Frontend-local state may cache presentation, but it is not the authoritative
dismissal record.

### Existing-device reconciliation

The dismissing frontend updates immediately from the mutation response. The
server does not need to force immediate removal on every already-open device.
Those devices may retain their current presentation until reconnect,
authoritative refresh, or normal state reload.

A newly opened or rehydrated frontend must load current server state and must
not present a dismissed notification as active.

### Notification history

Terminal notifications remain inspectable until retention removes them.
History is accessed through a reusable Notifications action in the top
pinnable action surface.

The full notification content remains scope-correct:

- application history belongs to the connection/application surface;
- session history belongs to the exact session;
- desktop may aggregate connection history with connection labels.

### Show again

Showing historical rich content again is a local presentation operation. It
does not transition `dismissed`, `resolved`, `expired`, or `cancelled` records
back to an active state and does not publish a new lifecycle event.

Historical content is read-only by default. Safe non-mutating actions may be
available; interaction responses and stale mutating actions are not replayed.

### Stage 2 boundary

This follow-up prepares records, selectors, forms, frontend ownership, and
reload/request boundaries for Stage 2. It does not implement Stage 2a waiting
or Stage 2b real suspension. Those remain in subtasks 050–080.

## Current implementation facts

- Session notifications are stored in session metadata, but dismissal is only
  React/frontend state keyed by `id + updated_at`.
- Application notifications live in owner memory, but their dismissal is also
  frontend-local.
- Reopening a session or restarting a frontend can therefore show a still
  pending dismissed notification again.
- Session pruning keeps every `pending` record, so the current item limit is
  not a strict bound when unresolved notifications accumulate.
- Backend normalization and SDK selectors accept only
  `kind: notification` with `pending`/`resolved`.
- Shared notification follow-up callbacks do not consistently preserve
  submitted form values across every host.
- `send_request` does not hold the session lock for the whole request, so a
  concurrent response action can persist state if a waiter does not hold that
  lock.
- Request cancellation already has live callback support suitable for a future
  wait-only interaction coordinator.
- A wait-only request can conflict with reload draining if response/cancel
  control operations are rejected with ordinary new work.
- The low-level `AgentApplication.send_request` API is not an owner-aware
  background request scheduler and is not sufficient by itself for Stage 2b
  continuation from a plugin action.

## Documentation authority

The intended contract is authored under:

`docs/development/specifications/notifications/`

The action-display boundary is authored under:

`docs/development/specifications/action-display/`

Package-local development pages document implementation mappings only.

## Planning status

The product and technical requirements above were approved on August 1, 2026.
The lettered staging proposal below is Draft until the user confirms the
checkpoint sequence. Only one lettered stage is planned in implementation
detail at a time. After its automated verification passes, stop for the
specified manual checkpoint before planning the next stage.

## Execution plan

Status: Draft

### Stage A — Backend lifecycle, revision, and snapshot foundation

Generalize the backend without changing frontend dismissal behavior yet:

- add explicit monotonic notification revisions with compatibility for records
  that currently have only `updated_at`;
- add ordinary `dismissed` and `expired` terminal states;
- centralize active/terminal classification used by list, deduplication, and
  pruning;
- make same-key creation update only active records and create a new occurrence
  after a terminal record;
- add session/application dismiss and expire operations with expected-revision
  validation;
- add an authoritative application-notification current-state snapshot/list
  boundary;
- retain existing event transport and current frontend-local dismissal until
  Stage B/C.

Automated boundary:

- Python unit tests for transitions, revisions, stale writes, deduplication,
  snapshot/list behavior, locking, metadata reconciliation, and compatibility
  with existing records;
- public HTTP tests for create/update/dismiss/resolve/expire/list;
- existing notification/reload suites remain green.

Manual checkpoint A:

- use the non-default demo plugins or HTTP calls to create, update, dismiss,
  resolve, and list application/session notifications;
- reopen the session and inspect stored terminal records;
- confirm existing mobile/desktop presentation has not otherwise changed.

Stop after checkpoint A. Plan Stage B in detail only after approval.

### Stage B — Shared SDK and mobile authoritative dismissal

- extend SDK types/selectors/event merge for revisions and terminal states;
- hydrate application notifications from the authoritative snapshot;
- route notification dismiss through the server while direct action-display
  close remains frontend-local;
- update the initiating mobile frontend immediately from the mutation response;
- do not require forced immediate removal on another already-open frontend;
- preserve notification ownership across Sessions and exact-session Chat;
- retain current history absence until later stages.

Automated boundary:

- SDK selector/controller tests;
- mobile component and real-backend tests;
- Detox scenarios for dismiss, navigation away/back, frontend restart or
  rehydration, and a later notification occurrence.

Manual checkpoint B:

- dismiss application and session notifications on mobile;
- reopen the relevant surface and restart/reconnect the frontend;
- confirm dismissed records do not reappear after authoritative hydration;
- optionally keep another frontend open and confirm immediate cross-device
  removal is not required.

Stop after checkpoint B.

### Stage C — Desktop authoritative-dismissal parity

- apply the same server dismissal and snapshot hydration to every open desktop
  connection;
- preserve the aggregated connection rail and active-session ownership;
- keep connection labels and desktop inline fallback;
- verify that dismissing on desktop does not require immediate mutation of
  another already-open frontend's presentation.

Automated boundary:

- desktop controller/component and real-backend tests;
- multi-connection isolation and revision tests;
- deterministic native harness updates.

Manual checkpoint C:

- verify application and session dismissal on desktop;
- close/reopen the session or connection and restart the desktop frontend;
- verify server-dismissed records remain absent;
- verify two open connections retain correct labels and isolation.

Stop before the macOS native simulator/XCUITest checkpoint when approval is
required by the desktop testing policy.

### Stage D — Retention, expiration, and bounded storage

- validate extensible retention objects;
- implement `until_resolved`, `ttl`, `until_request_complete`, and
  `until_server_restart`;
- define deterministic expiration evaluation and events;
- separate active-record and terminal-history bounds;
- guarantee that active interactions are not silently pruned;
- add demo-plugin controls for deterministic retention testing.

Automated boundary:

- unit tests with controlled clocks;
- request-completion and owner-restart integration tests;
- pruning and migration tests;
- SDK/mobile/desktop tests proving expired records leave active presentation.

Manual checkpoint D:

- create TTL and request-scoped notifications;
- observe expiration and history status;
- restart the server and verify server-lifetime application notifications end
  while persisted session history remains according to policy.

Stop after checkpoint D.

### Stage E — History query model and shared history components

- add active/terminal history query and filtering contracts;
- add SDK selectors/controllers for status, severity, time, connection, and
  session filtering;
- add shared compact history rows and rich historical replay primitives;
- make historical replay local and non-reactivating;
- default historical content to read-only and validate any explicitly allowed
  mutating action against current lifecycle/revision;
- add the stable Notifications action identity to the reusable pinnable action
  model without hosting it in mobile/desktop yet.

Automated boundary:

- backend/SDK query tests;
- shared component tests;
- replay lifecycle and historical-action safety tests.

Manual checkpoint E:

- use the deterministic component harness to inspect compact active and
  terminal rows, filters, and read-only inline/modal replay.

Stop after checkpoint E.

### Stage F — Mobile notification history

- expose Notifications through the top pinnable action surfaces on relevant
  mobile screens;
- show connection/application history from Sessions and exact-session history
  from Chat;
- add compact filters, active counts, and Show again;
- preserve existing live-notification placement and navigation behavior.

Automated boundary:

- mobile component and real-backend tests;
- focused Detox navigation, layout, action, and screenshot coverage.

Manual checkpoint F:

- inspect application and session history on mobile;
- verify dismissed/resolved/expired records and filters;
- replay rich inline/modal content and confirm lifecycle remains terminal.

Stop after checkpoint F.

### Stage G — Desktop notification history

- expose Notifications through the desktop pinnable action surfaces;
- aggregate connection history with connection labels;
- combine active-session history at the message/detail location;
- use desktop-native menu/window conventions and inline fallback;
- add connection/session filters and historical replay.

Automated boundary:

- desktop component and real-backend tests;
- deterministic native harness and XCUITest additions;
- no new TypeScript errors beyond any explicitly recorded baseline.

Manual checkpoint G:

- inspect multi-connection and active-session history;
- verify filters, labels, terminal states, and replay placement;
- run the native macOS checkpoint only after explicit approval.

Stop after checkpoint G.

### Stage H — Interaction-ready records and frontend behavior

Prepare, but do not implement, Stage 2 execution:

- preserve `kind: interaction` and interaction statuses through backend and SDK
  normalization;
- ensure active interactions are nondismissible;
- propagate fixed parameters, parameter mappings, embedded forms, and submitted
  values through every notification host;
- add compact waiting-for-input indicators that navigate to the owning Chat;
- add non-default demonstration fixtures for interaction rendering and form
  submission contracts;
- document the future drain-safe response/cancel operation class and
  owner-aware continuation scheduler boundary.

Stage H explicitly excludes:

- an in-memory wait-only interaction coordinator;
- blocking an active tool call for user input;
- real request suspension;
- request restart/continuation.

Those remain owned by subtasks 050–080.

Automated boundary:

- backend/SDK union and selector tests;
- mobile/desktop nondismissibility and waiting-indicator tests;
- form-value roundtrip tests on every supported host.

Manual checkpoint H:

- trigger demonstration interactions;
- confirm they cannot be dismissed while active;
- verify waiting indicators navigate to the correct session;
- submit demonstration form values and inspect the resulting action inputs.

Stop after checkpoint H and reassess the Stage 2 design before implementing
wait-only or real-suspend behavior.

### Implementation decisions and open questions

- The requirements and target contract are approved.
- The lettered checkpoint sequence remains Draft pending user confirmation.
- Detailed implementation planning is intentionally limited to the next
  approved lettered stage.
- If a stage requires materially more complexity or crosses an approved
  backend/plugin/frontend ownership boundary, stop and ask before expanding
  scope.
- Stage C and Stage G require explicit approval before native macOS test
  execution.

### Documentation

Each stage updates the root notification/action-display requirements and only
the package implementation pages affected by that stage. User-facing plugin
documentation must describe current runtime behavior and must not expose a
planned API as available before its implementation stage completes.

### Task checklist

- [ ] Approve the lettered stage/checkpoint sequence.
- [ ] Plan and execute Stage A.
- [ ] Complete manual checkpoint A.
- [ ] Plan and execute Stage B.
- [ ] Complete manual checkpoint B.
- [ ] Plan and execute Stage C.
- [ ] Complete manual checkpoint C.
- [ ] Plan and execute Stage D.
- [ ] Complete manual checkpoint D.
- [ ] Plan and execute Stage E.
- [ ] Complete manual checkpoint E.
- [ ] Plan and execute Stage F.
- [ ] Complete manual checkpoint F.
- [ ] Plan and execute Stage G.
- [ ] Complete manual checkpoint G.
- [ ] Plan and execute Stage H.
- [ ] Complete manual checkpoint H.
- [ ] Reassess and plan Stage 2 interaction execution.

### Requirement verification

Each stage maps its completed requirements to:

- backend/public API evidence where state changes;
- SDK/shared component evidence where portable behavior changes;
- production mobile/desktop integration where surfaces change;
- native automation only for behavior that cannot be established reliably
  below the native boundary;
- a separate user-confirmed manual checkpoint.

No requirement is marked complete solely because a lower-level unit test
passes.

### Additional implementation verification

- Run `git diff --check` at every checkpoint.
- Run the normal documentation build whenever contract or user-facing
  documentation changes.
- Keep current demo plugins out of production default configuration.
- Preserve current notification behavior outside the stage being changed.