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
- [x] Application notifications and their terminal history survive
  `AgentApplicationOwner` and server-process restart through a configurable
  durable store.
- [x] The frontend that dismisses a notification updates immediately after a
  successful server response.
- [ ] Other already-open frontends are not required to reconcile the dismissal
  immediately, but a newly opened, reconnected, or explicitly refreshed
  frontend does not present a server-dismissed notification.
- [x] A frontend can persist a revision-scoped local dismissal when the server
  mutation fails, keep that exact revision hidden, and retry the unchanged
  dismissal when that revision is observed again.
- [x] A cached dismissal never changes its expected revision: when a newer
  pending revision is authoritative, the old cache entry is removed and the
  newer revision is eligible for presentation.
- [x] Ordinary notification lifecycle supports at least `pending`,
  `dismissed`, `resolved`, and `expired` terminal behavior with validated
  transitions.
- [x] Notification records have an explicit monotonic revision used for stale
  mutation detection and event/snapshot ordering.
- [x] Stable-key deduplication applies to active records; creating with the key
  of a terminal record creates a new lifecycle occurrence.
- [x] Retention supports an extensible policy object with initial policies for
  explicit resolution, TTL, request completion, and server lifetime.
- [x] Active and terminal/history limits are distinct; active interactions are
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

### Failed-dismissal cache

The frontend may optimistically persist and hide a notification revision before
the server confirms dismissal. A failed mutation leaves that exact revision in
the local dismissal cache and does not restore it or show a blocking error.

The cache is revision-scoped:

- the same notification ID and revision remains hidden and may resend the
  unchanged dismissal request;
- a newer pending revision makes the cached dismissal obsolete, removes it,
  and is presented normally;
- the expected revision is never rewritten automatically;
- a terminal or missing server record removes the cache entry;
- a new lifecycle occurrence with a new ID is presented normally.

The local cache is synchronization state only. Durable server notification
history remains authoritative.

### Durable application history

Application notification records, including terminal records, are stored
durably at a path selected by application configuration. They survive
`AgentApplication` replacement, owner reconstruction, and server-process
restart until retention removes them.

The persistent store provides the source records needed by the later
notification history query and UI stages. It does not make the event store
durable.

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

- Session notification records and dismissal are persisted in session
  metadata.
- Application notification records and dismissal are authoritative in the
  runtime-injected durable `ApplicationNotificationStore`.
- Mobile and desktop use server-authoritative dismissal and authoritative
  application/session snapshot hydration.
- Mobile stores an exact-revision dismissal entry in AsyncStorage, hides the
  selected notification immediately, and does not show a blocking error when
  synchronization fails.
- Mobile retries only the unchanged cached revision during
  reconnect/rehydration. A newer authoritative revision removes the obsolete
  cache and is presented.
- Application terminal records survive application/owner/process
  reconstruction and remain listable for the later history UI.
- Session pruning keeps every `pending` record, so the current item limit is
  not a strict bound when unresolved notifications accumulate.
- Backend normalization and SDK selectors support ordinary
  pending/dismissed/resolved/expired notification records; interaction records
  remain future work.
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

Stages A through C were approved and implemented on August 1, 2026. Stage C's
manual and native checkpoints are postponed. Only one uncompleted stage is
planned in implementation detail at a time. Backend-only stages may end at an
automated gate; stages with user-visible behavior stop for the specified
mobile or desktop manual checkpoint before the next stage is planned.

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

### Stage B-1 — Durable application notification store and history foundation

- replace owner-memory application notification authority with a configurable
  durable store owned by `AgentApplicationOwner`;
- preserve application notification IDs, revisions, lifecycle state, display
  payloads, and terminal history across owner and server-process restart;
- keep event delivery best-effort and separate from durable notification
  state;
- make status mutations atomic with expected-revision validation;
- retain the existing active snapshot/list contract;
- provide the durable records needed by the later paginated history-query
  stage without implementing the history UI yet;
- define safe startup behavior for owner-lifetime pending records.

Recommended implementation:

- an `ApplicationNotificationStore` protocol;
- an in-memory test implementation;
- a SQLite production implementation using Python's standard library;
- a store path defined by application configuration and resolved through the
  runtime layout;
- runtime composition creates and closes the long-lived store;
- every `AgentApplication` generation receives the same injected store;
- `AgentApplication` owns the public notification contract and lifecycle event
  publication;
- `ApplicationControl` contains reload coordination only;
- `AgentApplicationOwner` emits reload notifications through the current
  `AgentApplication`.

The store path is owner-startup configuration. The recommended minimal rule is
that changing `application.notifications.store.path` requires reconstructing
the owning process or `AgentApplicationOwner`; an inner `AgentApplication`
reload continues using the already-open store. Live database switching or
migration is outside B-1.

Automated boundary:

- store contract tests;
- atomic revision and stable-key concurrency tests;
- process close/reopen persistence tests;
- owner reload/reconstruction tests;
- real HTTP active/terminal listing after restart;
- configuration/default-path tests.

Manual mobile checkpoint B-1:

- create an application notification from mobile;
- restart the Python server and reconnect mobile;
- confirm the active notification remains;
- dismiss it, restart the server again, and confirm it remains absent;
- emit the same key again and confirm a new occurrence appears.

Stop after checkpoint B-1.

### Stage B-2 — Revision-scoped mobile dismissal cache

- add a small portable dismissal-cache model to the frontend SDK;
- persist mobile cache entries in AsyncStorage using connection, scope,
  optional session, notification ID, and exact dismissed revision;
- hide the selected revision immediately before the server request completes;
- keep the exact revision hidden when the request fails and avoid a blocking
  dismissal error;
- resend the unchanged expected-revision request when the same active revision
  is observed again or the connection is rehydrated;
- remove the cache entry after successful dismissal, terminal/missing server
  state, or an authoritative newer pending revision;
- never update a cached expected revision automatically;
- present a newer revision or new lifecycle occurrence normally;
- keep direct action-display close outside the notification cache.

This stage intentionally excludes:

- operation IDs or a general mutation outbox;
- periodic background scheduling;
- cross-device cache synchronization;
- notification body/content storage in the cache.

Automated boundary:

- SDK cache state-machine and storage-adapter tests;
- mobile component tests for optimistic hide, failed mutation, retry, and
  obsolete-revision removal;
- real-backend reconnect tests;
- validation that only identifiers/revision metadata are stored locally.

Manual mobile checkpoint B-2:

- dismiss an application notification while the server is available and
  confirm it disappears immediately without an error;
- navigate away and back, then restart/reopen mobile, and confirm the
  successfully dismissed notification remains absent;
- repeat the online happy path for session inline, banner, and modal
  notifications;
- emit the same stable key after a terminal dismissal and confirm the new
  lifecycle occurrence is presented normally.

Stop after checkpoint B-2.

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
required by the desktop testing policy. Reassess whether desktop also needs a
platform-local adapter for the B-2 cache after the mobile checkpoint.

### Stage D — Retention lifetimes and bounded history

Stage D adds retention to the existing notification authorities. It does not
add a background scheduler, history UI, generic action/request coupling, or a
new owner-level notification service.

#### D1 — Small retention contract

- add one shared validator used by session and application notifications;
- normalize new records to a versioned retention object:
  - `{"version": 1, "policy": "until_resolved"}`;
  - `{"version": 1, "policy": "ttl", "expires_at": "<RFC3339 UTC>"}`;
  - `{"version": 1, "policy": "until_request_complete"}`;
  - `{"version": 1, "policy": "until_server_restart",
    "owner_epoch": "<runtime-owned>"}`;
- treat legacy records without retention as `until_resolved` and materialize
  the normalized policy on their next mutation;
- require an authoritative request ID for `until_request_complete`;
- reject unknown policies, malformed versions, invalid timestamps,
  producer-supplied foreign owner epochs, and request-completion retention
  without a request ID;
- provide a small portable deadline helper so backend and frontend tests can
  use an injected current time without sleeping.

TTL is based on the explicit `expires_at` instant. Updating an active record
retains its existing deadline unless the producer supplies a new valid
retention object.

#### D2 — TTL is a fresh-presentation rule

- do not add a server timer, event-poll reconciliation, or automatic TTL
  expiration event;
- do not remove a TTL notification merely because its deadline passes while
  it is already displayed;
- when a frontend host first observes or rehydrates a notification, suppress
  it if its TTL deadline has already passed;
- keep a notification that was accepted before its deadline visible in that
  mounted host until it is explicitly dismissed, resolved, otherwise
  terminal, or the host/application is reconstructed;
- retain accepted notification identities only in frontend memory; reopening
  the application, reconnecting, or reconstructing the owning notification
  host performs the TTL eligibility check again;
- add the same initial-eligibility behavior to application controllers and
  session notification hosts on mobile and desktop;
- leave the stored lifecycle record unchanged solely because wall-clock TTL
  elapsed. TTL therefore does not increment revision or publish an expiration
  event in Stage D.

This deliberately treats TTL as a presentation lifetime rather than a live
server-driven removal timer. Dismissal and resolution remain authoritative
server lifecycle transitions.

#### D3 — Request and server lifetime boundaries

- expire `until_request_complete` records from the central
  `AgentApplication.send_request` completion boundary on success, handled
  error, cancellation, preparation failure, and session-conflict completion;
- reuse the existing runtime owner epoch for `until_server_restart`;
- proactively reconcile application records at runtime startup;
- reconcile persisted session records lazily on their first authoritative
  read after restart rather than scanning every session file at startup;
- publish the existing application/session `*_notification_expired` event for
  request-completion expiration with reason `request_completed`;
- preserve the current owner-restart expiration behavior with reason
  `owner_restarted`.

These two policies have explicit server lifecycle boundaries and therefore
remain server-authoritative. They do not require time polling.

#### D4 — Bounded inactive history

- replace the session-only combined `max_items` pruning rule with
  `application.notifications.history_limit`;
- apply the history limit independently per session and once for the
  application notification store;
- preserve legacy `max_items` as a compatibility alias for
  `history_limit`;
- keep active records unbounded rather than adding active-capacity rejection
  in this stage;
- never silently prune an active record, including a future active
  interaction;
- prune only the oldest terminal records;
- perform application terminal pruning in the store transaction so SQLite and
  in-memory behavior remain atomic;
- use immutable per-operation history settings so one application generation
  does not silently adopt another generation's reloaded limit.

The recommended default is `history_limit: 500`.

An elapsed TTL record remains stored as pending because TTL alone does not
change server lifecycle state. It can still be dismissed, resolved, updated
with a new deadline, or replaced after another terminal transition. This is
the intentional simple model; Stage E history can display its elapsed
presentation deadline without inventing a lifecycle event.

#### D5 — Application and session integration

- keep public notification creation, mutation, list, and event publication on
  `AgentApplication`;
- keep the application store as an injected runtime-owned dependency;
- pass the runtime owner epoch into each application generation without giving
  `ApplicationControl` notification responsibilities;
- centralize request-completion expiration in a small
  `AgentApplication` helper called from every existing completion path;
- add atomic application-store request/owner expiration and terminal-pruning
  operations plus the equivalent locked session-metadata operation;
- preserve revision increments and terminal transition rules for
  request-completion and owner-restart expiration.

#### D6 — Demonstration controls and portable frontend behavior

- extend the non-default application/session notification demo plugins with
  retention selection for `until_resolved`, TTL, and server lifetime;
- let demo forms accept a small TTL duration and translate it into the
  contract's absolute `expires_at`;
- keep request-completion demonstration in an automated tool/request fixture
  rather than adding unreliable application-action access to a concurrently
  running request ID;
- add SDK/shared/mobile/desktop tests proving:
  - a TTL notification already shown remains visible after its deadline;
  - a fresh host does not present the same notification after its deadline;
  - explicit terminal events still remove an already shown notification;
- do not add notification history UI in Stage D; terminal inspection remains
  available through backend/list integration tests until Stage E.

Automated boundary:

- shared policy-validation and deadline-helper tests with controlled time;
- SDK/controller/shared-host tests for fresh TTL suppression and sticky
  already-presented behavior;
- session metadata tests for request completion, lazy server-restart
  reconciliation, revision/event ordering, terminal pruning, and legacy
  migration;
- in-memory and SQLite application-store tests for request/server lifetime,
  transactionality, restart recovery, and terminal history limits;
- `AgentApplication.send_request` tests covering every completion path without
  sleeping;
- public HTTP tests for request/server-lifetime terminal records;
- default-config and config-reload tests for `history_limit`;
- demo-plugin tests for valid retention payloads and invalid input;
- mobile and desktop real-backend/component tests for TTL behavior across host
  reconstruction.

Manual checkpoint D:

- from mobile, create application and session TTL notifications and verify
  they remain visible after the configured deadline while already shown;
- restart/reopen the application or owning notification surface and verify the
  elapsed TTL notifications no longer appear;
- create `until_resolved` controls and verify they remain active across the
  same reopen;
- create server-lifetime application and session notifications, restart the
  server, reconnect/reopen the session, and verify they no longer appear;
- leave request-completion timing and terminal-history inspection to automated
  verification because Stage D does not yet expose notification history UI.

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

- Stages A/B/B-1/B-2/C and their requirements are approved and implemented.
- The B-1/B-2/C requirements and revised sequence were approved on August 1,
  2026.
- Stage C's manual desktop checkpoint was postponed on August 1, 2026 and
  remains required before task completion. The approved native XCUITest was
  completed on August 2, 2026.
- B-1 store ownership was clarified and approved on August 1, 2026: the store
  is a runtime-owned injected dependency, not an `ApplicationControl`
  responsibility. The store path remains runtime-startup configuration and
  does not switch during inner `AgentApplication` reload. Supporting live
  store switching/migration is outside B-1.
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
- Dismiss and expire use explicit lifecycle event types. Mobile applies the
  Stage B policy; desktop may ignore dismissal lifecycle events until C.
  Authoritative list/session state remains the source of truth.
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
- Stage B used production component and real-backend integration tests for
  persistence and rehydration. Existing Detox coverage already validates
  notification placement; new Detox is required only if a native-only gap is
  found during implementation.
- Stage B-1 makes application notification records and terminal history
  durable; the event store remains best-effort and memory-backed.
- Stage B-2 uses a revision-scoped cache rather than a general outbox. A cached
  dismissal is resent only for the exact same revision.
- If a newer pending revision is authoritative, the cached dismissal is
  obsolete and removed. The frontend presents the newer revision and never
  rewrites the expected revision automatically.
- Retry is observation-driven on reconnect/rehydration or receipt of the same
  active revision. Stage B-2 does not add periodic retry scheduling or
  operation IDs.
- Stage D was approved on August 2, 2026 with these material choices:
  - **TTL semantics:** recommend treating TTL as a fresh-presentation
    deadline only. It does not mutate server status, increment revision, emit
    an expiration event, or remove an already displayed notification. An
    elapsed record remains pending in storage and a later stable-key update
    may give that same lifecycle record a new deadline.
  - **History capacity:** recommend only
    `application.notifications.history_limit`, defaulting to `500`.
    Active records remain unbounded and are never silently pruned; only
    terminal history is bounded.
  - **Request-completion demonstration:** recommend automated request/tool
    integration coverage only in Stage D. A mobile application action cannot
    reliably bind itself to a concurrently completing request without adding
    new action/request coordination outside the retention boundary.
- The simplified Stage D plan and all three recommendations were approved on
  August 2, 2026.
- Manual checkpoints are additive visual and real-device validation. They do
  not replace automated verification of important behavior. Each stage must
  first use the appropriate combination of unit tests, public-boundary
  integration tests, production component/UI tests, and simulator/native UI
  automation. Manual testing then covers visual quality, device-specific
  behavior, and experiential issues that automation does not establish
  reliably.
- A postponed manual checkpoint does not satisfy or cancel an automated native
  test. Stage C's native XCUITest is now complete while its manual desktop
  verification remains separate incomplete evidence.

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
- [x] Complete manual checkpoint B.
- [x] Approve the revised B-1/B-2/C sequence.
- [x] Plan and execute Stage B-1.
- [x] Complete manual checkpoint B-1.
- [x] Plan and execute Stage B-2.
- [x] Complete manual checkpoint B-2.
- [x] Plan and execute Stage C.
- [x] Complete Stage C macOS XCUITest.
- [ ] Complete manual checkpoint C.
- [x] Approve the Stage D execution plan.
- [x] Plan and execute Stage D.
- [x] Complete manual checkpoint D.
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

Manual mobile checkpoint B was confirmed on August 1, 2026. Stage B behaves as
intended.

### Stage B-1 — durable application notification store and history foundation

Implemented on August 1, 2026:

- added the runtime-injected `ApplicationNotificationStore` contract;
- added in-memory and SQLite store implementations;
- moved application notification lifecycle, revision validation, stable-key
  updates, terminal history, and owner-lifetime recovery out of
  `AgentApplicationOwner`;
- kept the public notification API and best-effort lifecycle event publication
  on `AgentApplication`;
- reduced `ApplicationControl` to reload coordination;
- changed the owner to create and update reload notifications through the
  current application;
- made the terminal/server runtime create one store and inject it into every
  application generation;
- made application close treat the injected store as borrowed, with runtime
  shutdown closing it after the owner;
- added configurable `application.notifications.store` with a config-adjacent
  SQLite default;
- marked reload notifications with `until_server_restart` owner epochs and
  expire stale pending reload records during startup recovery;
- added durable public HTTP restart coverage and updated root, API,
  implementation, application, and plugin documentation;
- added the explicit SQLite path to the bundled default config and the user's
  `~/.crystal/config.json` for checkpoint testing.

Automated evidence:

- focused Core owner/application/session notification tests: `17 passed`;
- focused real HTTP persistence plus MCP reload cleanup: `2 passed`;
- focused Application owner/terminal/demo HTTP tests: `42 passed`;
- full fast Core suite: `423 passed, 26 deselected, 1 xfailed`;
- full fast Application suite: `316 passed, 90 deselected`;
- modified Python files pass Ruff;
- default and personal config files pass JSON parsing;
- normal prepared documentation build passes with only the repository's
  existing Griffe/autoreference warnings;
- Pyright was not available in the current Python environment.

Manual mobile checkpoint B-1 was confirmed on August 1, 2026:

- an active application notification survived server-process restart;
- a dismissed notification remained absent after another restart;
- emitting the same stable key created a visible new lifecycle occurrence.

### Stage B-2 — revision-scoped mobile dismissal cache

Implemented on August 1, 2026:

- added a portable `NotificationDismissalCache` over the existing
  `KeyValueStore` contract;
- limited persisted entries to connection, scope, optional session,
  notification ID, exact revision, and dismissal time;
- added bounded serialized persistence without notification title/body/display
  content;
- made mobile use one AsyncStorage-backed cache shared through the global
  display layer;
- made application notification dismissal hide immediately, retain failed
  synchronization, and retry the unchanged revision during snapshot/event
  observation;
- made exact cached application revisions remain hidden after component
  reconstruction;
- made newer application revisions invalidate the older cache and remain
  visible without retargeting the dismissal;
- added opt-in optimistic suppression and external revision-key suppression to
  the shared session notification host while retaining its existing default
  behavior for desktop and other hosts;
- applied the same cache semantics to mobile session inline, banner, and modal
  notifications;
- refreshes session authority before removing a successfully synchronized cache
  entry to avoid presentation flash;
- retained transient direct action-display close outside the cache;
- retained the approved absence of periodic retry scheduling, operation IDs,
  and cross-device cache synchronization.

Automated evidence:

- frontend SDK: `281 passed`;
- frontend SDK React bindings: `20 passed`;
- shared React Native components: `7 passed`;
- mobile TypeScript: passed;
- full mobile Jest suite: `109 passed`;
- focused mobile cache/dismissal tests: `14 passed`;
- real-backend mobile component integration: `5 passed`, including exact
  revision retry and a real server revision-conflict response that preserves
  and presents the newer revision;
- focused desktop compatibility test: `1 passed`;
- no Detox scenario was added because B-2 changes persistence/retry rather than
  native layout; actual AsyncStorage process-restart behavior belongs to the
  mobile manual checkpoint.

Manual mobile checkpoint B-2 was confirmed on August 1, 2026. Online
application and session notification dismissal, reopening, and new lifecycle
occurrence behavior work as intended.

### Stage C — desktop authoritative-dismissal parity

Implemented on August 1, 2026:

- enabled authoritative application-notification snapshot hydration for every
  open desktop connection;
- retained one application notification controller per connection and routed
  dismissal through the controller owning the displayed notification;
- preserved connection labels, aggregated message-area placement, and
  per-connection isolation;
- added a focused desktop session notification rail that hydrates the active
  session summary, sends revision-checked server dismissal, refreshes
  authoritative state after success, and retains the notification after
  failure;
- kept desktop `modal` presentation as inline fallback in the common
  message/detail rail;
- retained direct action-display close as frontend-local behavior;
- updated the deterministic macOS notification harness to use authoritative
  application/session backend snapshots and the production desktop session
  rail;
- reassessed the B-2 cache for desktop and kept the simpler success-only
  behavior: desktop does not optimistically hide a failed dismissal, so it
  does not currently require a platform-local failed-dismissal cache.

Automated evidence:

- focused desktop notification component tests: `5 passed`;
- real-backend desktop integration: `2 passed`, covering application and
  session snapshot hydration, revision-checked dismissal, desktop inline
  fallback, authoritative absence after reopen, and server persistence;
- multi-connection component coverage verifies that dismissing one
  connection's notification does not mutate another connection;
- the deterministic native notification harness exercises the production
  Stage C hosts; the focused macOS XCUITest passed on August 2, 2026 and
  retained the `desktop-notification-message-area-rail` screenshot in its
  `.xcresult`;
- desktop TypeScript still reports the three pre-existing errors in
  `ChatPane.tsx` attachment plugin IDs and `ActionResultInlineCard.tsx`
  `theme.shadow`; Stage C adds no TypeScript error;
- full desktop Jest suite: `19 suites, 103 passed`, including elapsed-TTL
  suppression during desktop application hydration;
- the prepared MkDocs site builds successfully with the repository's existing
  nav, Griffe indentation, and autoreference warnings.

Manual desktop checkpoint C was explicitly postponed on August 1, 2026 and
remains incomplete. The macOS XCUITest notification-harness run was completed
successfully on August 2, 2026 after exposing stable accessibility identities
for the actual rendered rail and message-content containers.

### Stage D — retention lifetimes and bounded history

Implemented on August 2, 2026:

- added versioned `until_resolved`, TTL, request-completion, and
  server-lifetime retention validation;
- made TTL a fresh-presentation rule with no server timer, status mutation,
  revision increment, or expiration event;
- made application controllers and shared session hosts retain TTL
  notifications accepted before their deadline for the mounted host lifetime
  and suppress elapsed records after reconstruction;
- added server-authoritative request-completion expiration across normal and
  tool-preparation-failure request completion paths;
- added runtime-owned server-lifetime stamping and lazy session recovery after
  owner restart;
- replaced combined session pruning with terminal-only
  `application.notifications.history_limit`, default `500`, while retaining
  `max_items` as a compatibility alias;
- added atomic terminal-history pruning to in-memory and SQLite application
  stores;
- extended the non-default application/session demo plugins with retention and
  TTL-duration controls;
- kept request-completion demonstration in automated request integration
  rather than expanding application-action/request coordination.

Automated evidence:

- focused backend retention/request tests: `31 passed`;
- full Core suite: `430 passed, 26 deselected, 1 xfailed`;
- application reload-owner regression tests: `4 passed`;
- full Application suite: `316 passed, 90 deselected`;
- frontend SDK: `284 passed`;
- mobile TypeScript: passed;
- full mobile Jest suite: `26 suites, 110 passed`;
- full desktop Jest suite: `19 suites, 102 passed`;
- real-backend mobile component integration: `6 passed`, including visible
  past-deadline TTL behavior and suppression after reconstruction;
- both dummy notification plugin suites: `2 passed` each;
- modified Python files pass Ruff and Black.

No Stage D Detox or XCUITest was added because TTL changes initial data
eligibility rather than native layout, geometry, navigation, or platform
interaction. Controlled-time shared-host tests, production desktop component
coverage, and real-backend mobile reconstruction cover the functional
boundary. The manual checkpoint remains responsible for visual quality and
real-device application restart behavior.

The first full Core run found three owner test-double compatibility failures.
The runtime stamping boundary was corrected, the focused owner suite passed
`3 passed`, and the clean full Core rerun passed.

Manual mobile checkpoint D was confirmed on August 2, 2026. TTL notifications
remain visible after their deadline while already shown and are suppressed
after application/host reconstruction; explicit retention remains visible;
server-lifetime records disappear after full server restart.

Clarifications confirmed during checkpoint D:

- `until_server_restart` refers to the hosting runtime/process lifetime, not
  one `AgentApplication` generation. Inner application reload behavior is a
  host implementation detail and is not a portable expiration guarantee.
- explicit dismissal or resolution has precedence over TTL,
  request-completion, and server-restart retention. Automatic expiration only
  applies while a record is still pending.