# Authoritative Dismissal, Retention, History, and Interaction Readiness

Replace the current frontend-local notification dismissal model with
server-authoritative lifecycle state, add bounded retention and user-visible
history/replay, and generalize the Stage 1 contract so Stage 2 interactions can
build on it without replacing the notification substrate.

## Requirements checklist

- [x] A session notification and its dismissal state are stored together in
  the owning session.
- [x] An application notification and its dismissal state are stored together
  in the server-side application notification store.
- [ ] The frontend that dismisses a notification updates immediately after a
  successful server response.
- [ ] Other already-open frontends are not required to reconcile the dismissal
  immediately, but a newly opened, reconnected, or explicitly refreshed
  frontend does not present a server-dismissed notification.
- [x] Ordinary notification lifecycle supports at least `pending`,
  `dismissed`, `resolved`, and `expired` terminal behavior with validated
  transitions.
- [x] Notification records have an explicit monotonic revision used for stale
  mutation detection and event/snapshot ordering.
- [x] Stable-key deduplication applies to active records; creating with the key
  of a terminal record creates a new lifecycle occurrence.
- [ ] Retention supports an extensible policy object with initial policies for
  explicit resolution, TTL, request completion, and server lifetime.
- [ ] Active and terminal/history limits are distinct; active interactions are
  never silently pruned.
- [x] Application notifications expose an authoritative current-state
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
- [x] Direct action displays remain transient displays unless the producer
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
- [x] Root specifications remain the only normative explanation; package docs
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
Only one lettered stage is planned in implementation detail at a time.
Backend-only stages may end at an automated gate; stages with user-visible
behavior stop for the specified mobile or desktop manual checkpoint before the
next stage is planned.

## Execution plan

Status: Approved

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

Automated completion gate A:

- exercise create, update, dismiss, resolve, expire, and list through unit and
  public HTTP integration tests;
- verify persisted session terminal records and owner-memory application
  terminal records;
- verify existing notification/reload suites remain green.

Stage A has no human checkpoint because its deterministic backend behavior is
fully automatable and current frontends intentionally do not consume it yet.

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
- Detox only if inspection identifies native-only behavior that cannot be
  established reliably through production component and real-backend tests.

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
- The lettered checkpoint sequence was approved on August 1, 2026.
- Detailed implementation planning is intentionally limited to the next
  approved lettered stage.
- If a stage requires materially more complexity or crosses an approved
  backend/plugin/frontend ownership boundary, stop and ask before expanding
  scope.
- Stage C and Stage G require explicit approval before native macOS test
  execution.
- Stage A uses platform-owned HTTP list/dismiss operations rather than exposing
  notification creation/update/resolve as generic public CRUD:
  - `GET /application/notifications`
  - `POST /application/notifications/{notification_id}/dismiss`
  - `GET /sessions/{session_id}/notifications`
  - `POST /sessions/{session_id}/notifications/{notification_id}/dismiss`
- New records begin at integer `revision: 1`; each mutation increments it.
  Existing records without `revision` accept `updated_at` as a compatibility
  expected-revision token and gain an integer revision on first mutation.
- Dismiss, resolve, and expire return the current record without a new event
  when the record is already in the requested terminal state. Stale revisions
  and incompatible terminal transitions are conflicts.
- Dismiss and expire use explicit lifecycle event types. Existing frontends may
  ignore them until Stage B/C; authoritative list/session state remains the
  source of truth.
- HTTP snapshot/list responses return active records by default and accept
  `include_terminal=true`. Existing Python list methods retain compatibility
  for current plugin callers and tests.
- Stage A ends at an automated gate. Terminal/curl smoke steps are not counted
  as manual verification.
- Stage B uses optional notification-lifecycle methods on the shared
  `AgentBackend` interface for source compatibility with existing mock and
  alternate backends. `RestAgentBackend` implements them and the production
  mobile path requires them for notification dismissal.
- Application hydration captures the latest event cursor before loading the
  authoritative snapshot, then polls from that cursor. Revision-aware merging
  makes duplicate snapshot/event records harmless and prevents stale events
  from replacing newer state.
- Mobile local suppression is applied only after a successful server mutation
  and exists solely to make the initiating frontend update immediately.
  Backend state remains authoritative after navigation or reconnect.
- Direct action-display dismissal remains frontend-local.
- Stage B will use production component and real-backend integration tests for
  persistence and rehydration. Existing Detox coverage already validates
  notification placement; new Detox is required only if a native-only gap is
  found during implementation.

### Documentation

Each stage updates the root notification/action-display requirements and only
the package implementation pages affected by that stage. User-facing plugin
documentation must describe current runtime behavior and must not expose a
planned API as available before its implementation stage completes.

### Task checklist

- [x] Approve the lettered stage/checkpoint sequence.
- [x] Plan and execute Stage A.
- [x] Complete automated gate A.
- [x] Plan and execute Stage B.
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

## Implementation Notes

### Stage A — backend lifecycle, revision, and snapshot foundation

Implemented on August 1, 2026:

- added integer notification revisions and legacy `updated_at` compatibility
  tokens;
- added active/terminal classification and pending/dismissed/resolved/expired
  transition validation;
- made stable-key creation update active records only;
- added expected-revision conflicts carrying the current record;
- added idempotent dismiss/resolve/expire transitions;
- added session and application dismiss/expire methods and explicit
  dismiss/expire events;
- added active-only application/session HTTP snapshots with
  `include_terminal=true`;
- added platform-owned HTTP dismissal routes;
- added non-default application/session demo actions for manually expiring
  notifications through the existing action system;
- retained existing mobile and desktop local Dismiss behavior for Stage B/C;
- updated root, API, package-development, application README, and plugin
  authoring documentation.

Automated evidence:

- focused Core notification/owner tests: `16 passed`;
- real HTTP demo-plugin integration: `1 passed`;
- demo application/session plugin package tests: `2 passed`;
- full fast Core suite: `422 passed, 26 deselected, 1 xfailed`;
- full fast Application suite: `315 passed, 90 deselected`;
- modified Core Python files pass Ruff;
- full `server.py` Ruff remains blocked only by the five pre-existing F841/F811
  findings outside the notification routes.
- normal prepared documentation build passes with only the repository's
  existing Griffe/autoreference warnings.

Automated gate A is complete. The first human checkpoint is mobile checkpoint
B.

### Stage B — shared SDK and mobile authoritative dismissal

Implemented on August 1, 2026:

- expanded SDK notification types and event guards for integer revisions and
  dismissed/resolved/expired terminal states;
- added revision-token and revision-aware merge helpers;
- added optional application/session notification list and dismiss operations
  to `AgentBackend` and implemented them in `RestAgentBackend`;
- added explicit notification revision ownership to display envelopes;
- added opt-in authoritative application snapshot hydration using
  cursor-before-snapshot ordering;
- enabled snapshot hydration only on mobile so desktop remains on the approved
  Stage C boundary;
- changed mobile application notification dismissal to use the controller's
  server mutation response;
- changed mobile session inline, banner, and modal dismissal to use the server
  mutation routes;
- retained local close behavior for direct action displays;
- retained successful-response local suppression only to update the initiating
  frontend immediately;
- deliberately ignored remote dismissal events for live presentation so
  another already-open frontend is not forced to dismiss immediately;
- refreshed active mobile session context after inline session dismissal;
- fixed stale-event reconciliation so an old created event cannot resurrect a
  newer terminal session record;
- updated the root, SDK, shared component, mobile, API, and plugin
  documentation.

Automated evidence:

- frontend SDK: `275 passed`;
- shared React Native components: `7 passed`;
- frontend SDK React bindings: `20 passed`;
- mobile TypeScript: passed;
- full mobile Jest suite: `106 passed`;
- focused mobile dismissal/rehydration tests: `11 passed`;
- real-backend mobile component integration: `3 passed`; application and
  session dismissal survive production component recreation;
- focused desktop compatibility test: `1 passed`;
- no new Detox scenario was added because persistence/rehydration crosses the
  HTTP/backend boundary but has no native-only behavior; existing Detox
  coverage continues to own visual placement.

Manual mobile checkpoint B remains open.