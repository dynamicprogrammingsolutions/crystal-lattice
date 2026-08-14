# Notification Stable-Key Publication and Revision-Scoped Dismissal

Simplify the plugin-facing notification contract so producers publish by stable
key without managing revisions, while dismissal remains revision-scoped for
user-facing mutations. Remove the dismissibility dead-end that long-running
operation notifications can currently reach.

## Requirements checklist

- [ ] Plugin-facing notification publication uses stable keys and does not
  require the caller to supply or track `expected_revision`.
- [ ] The notification service owns revision assignment and increment as an
  internal contract for producer publication.
- [ ] Dismissal remains revision-scoped for user and client mutations and
  accepts optional `expected_revision` and `reason` fields.
- [ ] A stale dismissal cannot hide a newer revision or a later stable-key
  occurrence.
- [ ] Publishing a stable key with no active occurrence creates a new lifecycle
  occurrence, including after dismissal, resolution, or expiration of an
  earlier occurrence.
- [ ] A late update from a superseded operation occurrence does not overwrite a
  newer operation using the same stable key.
- [ ] Persistent operation-progress notifications are dismissible by default;
  nondismissible presentation requires an explicit product reason and is not
  used as a substitute for operation ownership or update coordination.
- [ ] The OpenAI Responses native compaction notification uses one stable
  compaction key per session, dismissible progress, and no plugin-side revision
  tracking.
- [ ] Notification revision semantics, durable refresh invalidation, and
  one-shot action-response refresh behavior remain consistent with the
  existing notification specification.

## Open requirement questions

1. Should a dismissed compaction banner reappear on the next routine heartbeat
   publication, or should only meaningful phase changes create a new occurrence?
   - The stable-key/new-occurrence model naturally causes the next heartbeat
     after dismissal to create a new pending occurrence and re-present the
     banner.
   - If only meaningful phase changes should reappear, the producer contract
     needs to distinguish routine heartbeat refreshes from material state
     changes, or the frontend needs key-level suppression. This is a product
     decision that should be resolved before implementation.
   - Recommendation: start with the natural model (any publication after
     dismissal creates a new occurrence) and observe whether the resulting
     15-second reappearance is acceptable before adding a heartbeat/phase
     distinction.

2. Should `update_session_notification` and `update_application_notification`
   by ID retain an optional `expected_revision` parameter for producer
   updates, or should producers always use update-by-key?
   - The by-ID methods remain useful when a producer has the notification ID
     but not the key.
   - Recommendation: retain the parameter as optional on the by-ID methods but
     remove it from producer-facing documentation examples. Producers should
     prefer update-by-key; by-ID updates without `expected_revision` apply to
     the current authoritative revision.

3. Should the operation-occurrence guard be part of the notification service
   contract or remain a plugin-owned convention?
   - The guard prevents a late update from an older compaction occurrence from
     overwriting a newer compaction using the same stable key.
   - Recommendation: the notification service should accept an optional
     operation identifier in the publication payload and reject updates whose
     operation identifier does not match the current active occurrence. This
     keeps the guard inside the atomic upsert transaction rather than relying
     on plugin cooperation.

## Supporting facts

### Current behavior

- The notification service already supports `create`, `update by ID`,
  `update by key`, `resolve`, `dismiss`, `expire`, and `list/history`.
- `expected_revision` is currently accepted on all mutations. A stale revision
  raises `NotificationRevisionConflictError`.
- Creating with the key of an active notification updates that item in place.
  Creating with the key of a terminal record creates a new occurrence.
- The compaction process currently retains `_notification["revision"]` and
  passes `expected_revision` on every heartbeat, success, failure, and
  interruption update. It implements revision-conflict retries that stop when
  the notification is no longer pending or belongs to a different operation.
- The compaction notification key currently includes the unique operation ID,
  so a later compaction creates a new notification instead of replacing a stale
  one. If the process disappears before publishing a terminal revision, the
  banner remains `pending` with `dismissible: false` and no viable recovery
  action.
- `display.dismissible: false` is honored by the shared React Native
  notification banner. The server would allow dismissal; only the frontend flag
  prevents it.

### Proposed model

- **Producer publication** (plugin create, update, resolve, expire): uses a
  stable key; the notification service performs an atomic upsert against the
  current active occurrence; revision is assigned and incremented internally;
  no `expected_revision` is accepted.
- **Frontend lifecycle mutation** (dismissal): targets a specific notification
  ID and optional `expected_revision`; a stale revision returns the current
  record rather than hiding a newer revision.
- **Atomic upsert**: active key exists → update that occurrence; only terminal
  exists → create a new occurrence; no occurrence exists → create a new
  occurrence.
- **Operation-occurrence guard**: the stable key identifies the notification
  stream; a unique operation ID identifies one execution; a late update from
  an older occurrence is rejected as superseded.
- **Dismissability**: `dismissible: false` is an exceptional producer decision
  for permanent status displays or active interactions that must remain
  discoverable. Long-running operation progress should not use `false` merely
  to preserve a Cancel action. Dismissing progress does not cancel the
  operation; Cancel remains an explicit action.

### Affected artifacts

- `docs/development/specifications/notifications/product-spec.md`
- `docs/development/specifications/notifications/technical-spec.md`
- `docs/development/specifications/notifications/frontend-behavior.md`
- `docs/development/specifications/notifications/requirements.md`
- `docs/development/specifications/notifications/index.md`
- `docs/development/specifications/action-display/technical-spec.md`
- `docs/development/specifications/action-display/requirements.md`
- `plugins/docs/notifications-and-action-displays.md`
- `plugins/docs/application-plugins.md`
- `plugins/openai_responses/README.md`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_native_compaction_process.py`
  and related notification helpers (code changes are out of scope for this
  documentation-only step)

### Related tasks and commits

- `tasks/20260802-openai-responses-background-compaction.md` — the background
  compaction task that introduced the current notification behavior.
- `tasks/20260814-notification-ui-effect-specification.md` — the prior
  notification specification amendment for durable refresh invalidation.
- Commit `6601e48a` (`Make notification refresh invalidations durable`) —
  implemented revision-scoped `ui_effects` and durable frontend invalidation.
- Commit `25091040` (`Specify notification refresh invalidation semantics`) —
  captured that behavior in the notification specification.

## Execution plan

Status: Draft

This plan documents the proposed contract change. It is not approved for
execution. The specification and documentation updates described below are
being applied as uncommitted documentation changes so the user can review the
target contract before any code modifications arrive. The documentation will
describe the target state; code changes to the notification service and the
compaction plugin will follow under a separately approved execution of this
plan.

### Server changes

- Add an atomic publish/upsert operation to the notification service that
  accepts a stable key and payload, finds the current active occurrence,
  applies the patch, increments revision internally, and publishes the new
  revision. If the previous occurrence is terminal or absent, create a new
  occurrence.
- Accept an optional operation identifier in the publication payload. Reject
  updates whose operation identifier does not match the current active
  occurrence for that key. This replaces the plugin's manual revision-conflict
  recovery for producer updates.
- Remove `expected_revision` from the producer-facing publication path
  (create, update-by-key, resolve, expire). Retain `expected_revision` as an
  optional parameter on by-ID updates and lifecycle operations that are
  user/client-initiated (dismissal).
- Keep `expected_revision` on dismissal routes. A stale dismissal returns the
  current record (HTTP 409) rather than hiding a newer revision.

### Plugin changes

- Simplify the OpenAI Responses native compaction notification to use one
  stable compaction key per session instead of a per-operation key.
- Stop retaining `_notification["revision"]` and stop passing
  `expected_revision` on heartbeat, success, failure, and interruption
  updates.
- Stop implementing revision-conflict retries for producer updates. Let the
  notification service apply updates to the current authoritative occurrence.
- Keep the unique operation ID in the structured `operation` mapping and in
  Cancel follow-up action parameters so the operation-occurrence guard can
  reject late updates from a superseded occurrence.
- Omit `dismissible: false` on progress notifications. Use `dismissible: true`
  (or omit the field) so the user can dismiss the banner at any time. Cancel
  remains an explicit follow-up action.
- Retain `dismissible: false` only for genuinely permanent notifications such
  as status indicators whose dismissal would remove the only path to a
  required response.

### Frontend changes

- Dismissal targets the displayed notification ID and the optional expected
  revision. A stale dismissal cannot hide a newer revision or a later
  stable-key occurrence.
- The frontend never retargets a dismissal to a newer revision or occurrence.
- The failed-dismissal cache remains revision-scoped. A newer pending
  publication for the same stable key removes the obsolete cache entry and is
  presented normally.

### Specification and documentation changes

Apply the target contract to the notification and action-display
specifications and to the plugin-authoring documentation. These changes are
uncommitted and describe the target state at the time the code changes are
committed.

### Implementation decisions and open questions

- Decision: the notification service owns revision assignment and increment
  for producer publication. Producers do not supply or track `expected_revision`.
- Decision: dismissal retains `expected_revision` as an optional field because
  it prevents a stale user gesture from hiding a newer revision.
- Decision: the operation-occurrence guard belongs in the notification service
  atomic upsert rather than in plugin cooperation.
- Decision: `dismissible: false` remains in the action-display contract but is
  recommended only for deliberately exceptional cases.
- Open question 1: whether a dismissed compaction banner should reappear on
  the next routine heartbeat or only on meaningful phase changes. See the open
  requirement questions above.
- Open question 2: whether by-ID update methods should retain an optional
  `expected_revision` parameter for producer use. See the open requirement
  questions above.
- Open question 3: whether the compaction notification key should be
  session-scoped (`openai_responses:native_compaction`) or include the session
  ID. Session notifications are already session-scoped, so the key itself does
  not need the session ID.

### Documentation

- Update the notification product, technical, frontend-behavior, and
  requirements specification pages.
- Update the action-display technical specification and requirements with the
  restrained `dismissible` guidance and `DSP-010`.
- Update `plugins/docs/notifications-and-action-displays.md` to remove
  `expected_revision` from producer examples and present stable-key
  publication as the normal producer API.
- Update `plugins/docs/application-plugins.md` to present stable-key
  publish/upsert as the normal producer API.
- Update `plugins/openai_responses/README.md` to document one stable
  compaction notification key per session and dismissible progress.
- Update the notification specification index to reference this task.

### Task checklist

- [x] Create this task file with the follow-up plan as Draft.
- [x] Update the notification product specification.
- [x] Update the notification technical specification.
- [x] Update the notification frontend-behavior specification.
- [x] Update the notification requirements.
- [x] Update the action-display technical specification.
- [x] Update the action-display requirements.
- [x] Update `plugins/docs/notifications-and-action-displays.md`.
- [x] Update `plugins/docs/application-plugins.md`.
- [x] Update `plugins/openai_responses/README.md`.
- [x] Update the notification specification index.
- [x] Validate the documentation build and requirement ID uniqueness.
- [ ] Obtain user approval before any code changes.

### Requirement verification

Each requirement maps to concrete automated tests that must be changed or
added. Existing tests that assert the old `expected_revision`-on-producer
contract must be updated; new tests cover the stable-key publication,
operation-occurrence guard, and dismissibility behavior.

#### Requirements 1–3 — producer publication, service-owned revision, revision-scoped dismissal

Core session notification tests (`core/python/tests/test_session_notifications.py`):

- Change `test_update_by_id_and_key` to assert that `update_session_notification`
  without `expected_revision` applies to the current authoritative revision and
  increments revision internally. Assert that `update_session_notification_by_key`
  remains revisionless at the caller level.
- Change `test_revision_conflict_and_terminal_transition_are_rejected` to assert
  that `expected_revision` is only accepted on dismissal, and that producer
  update/resolve/expire no longer accept or require it.
- Add `test_producer_publication_by_key_updates_active_occurrence` — publish by
  stable key twice; assert the occurrence keeps its ID, revision increments, and
  `updated_at` advances.
- Add `test_producer_publication_by_key_creates_new_occurrence_after_dismissal` —
  dismiss the active occurrence, publish by the same stable key, assert a new
  occurrence with a new ID and revision 1 is created and presented.
- Add `test_producer_publication_by_key_creates_new_occurrence_after_resolution`
  and `..._after_expiration` — same shape for resolve and expire.
- Add `test_producer_resolve_and_expire_do_not_require_expected_revision` —
  call `resolve_session_notification` and `expire_session_notification` without
  `expected_revision`; assert success and revision increment.
- Add `test_dismissal_with_stale_expected_revision_returns_current_record` —
  publish revision 2, dismiss with `expected_revision=1`; assert
  `NotificationRevisionConflictError` carries the current revision 2 record.

Core application notification tests
(`core/python/tests/test_application_notifications.py`):

- Change `test_application_notification_validation_and_revision_conflicts` to
  remove `expected_revision` from producer update/resolve/expire calls and
  assert the service applies them to the current authoritative revision.
- Add `test_application_producer_publication_by_key_creates_new_occurrence_after_terminal` —
  dismiss or resolve an application notification, publish by the same stable
  key, assert a new occurrence is created.

Public HTTP notification contract tests
(`application/python/tests/test_notification_demo_plugins_http.py`):

- Change `test_demo_plugins_exercise_public_notification_and_display_contract`
  to assert that producer update/resolve/expire requests omit
  `expected_revision` and that dismissal requests may include it.
- Add `test_public_dismissal_with_stale_expected_revision_returns_409` —
  POST dismissal with a stale `expected_revision`; assert HTTP 409 and that the
  response body carries the current record.

#### Requirements 4–6 — stale dismissal rejection, new occurrence creation, operation-occurrence guard

Core session notification tests (`core/python/tests/test_session_notifications.py`):

- Add `test_stale_dismissal_does_not_hide_newer_revision` — publish revision 2,
  dismiss with `expected_revision=1`; assert revision 2 remains in the active
  list and the dismissal is rejected.
- Add `test_dismissed_occurrence_does_not_suppress_later_publication` —
  dismiss occurrence A, publish by the same stable key; assert occurrence B is
  active and presented, and A remains terminal in history.
- Add `test_operation_occurrence_guard_rejects_late_update_from_older_operation` —
  create a notification with `operation.id = "op-1"`, publish an update with
  `operation.id = "op-2"` (new occurrence takes over the stable key), then
  attempt to publish with `operation.id = "op-1"`; assert the late update is
  rejected and occurrence B's content is unchanged.
- Add `test_operation_occurrence_guard_allows_same_operation_update` —
  repeated publications with the same `operation.id` update the same
  occurrence.

Core application notification tests
(`core/python/tests/test_application_notifications.py`):

- Add `test_application_operation_occurrence_guard_rejects_superseded_operation` —
  equivalent guard behavior for application-scoped notifications.

#### Requirement 7 — dismissible by default; nondismissible only with explicit reason

Action-display and notification validation tests:

- Add `test_nondismissible_progress_notification_requires_explicit_flag` in
  `core/python/tests/test_session_notifications.py` — assert that the default
  `dismissible` value is `true` when omitted, and that `dismissible: false` is
  accepted but does not change lifecycle or dismissal authority.
- Add `test_dismissing_progress_does_not_cancel_operation` in the compaction
  app test file (see Requirement 8) — assert that dismissing the progress
  banner leaves the operation registered and running.

#### Requirement 8 — compaction uses one stable key, dismissible progress, no plugin-side revision tracking

OpenAI Responses compaction tests
(`plugins/openai_responses/tests/test_openai_responses_native_compaction_app.py`):

- Change `test_background_action_returns_promptly_and_publishes_heartbeats` to:
  - assert `notification["display"]["dismissible"] is True` for the progress
    banner (currently asserts `False`);
  - assert the notification key is stable across heartbeats (one key per
    session, not per-operation);
  - assert the process does not retain or pass `expected_revision` on
    heartbeat updates.
- Change `test_cancel_action_interrupts_transport_and_discards_result` to
  assert that cancellation does not implement revision-conflict retries for
  producer updates.
- Add `test_dismissing_progress_banner_does_not_cancel_operation` — dismiss
  the progress notification, assert the operation remains registered and the
  transport is still running, then release the transport and assert the
  success notification appears.
- Add `test_next_heartbeat_after_dismissal_creates_new_occurrence` — dismiss
  the progress banner, wait for the next heartbeat, assert a new pending
  occurrence with a new ID is created and presented (the banner reappears).
- Add `test_late_update_from_superseded_compaction_is_rejected` — start
  compaction A, let it publish heartbeats, start compaction B after A is
  superseded (e.g. by application replacement), attempt to publish a late
  update from A; assert the update is rejected and B's notification is
  unchanged.
- Add `test_compaction_uses_one_stable_key_per_session` — start two
  sequential compactions in the same session; assert both use the same
  notification key and the second replaces the first's active occurrence if
  the first was terminal, or updates it if still active.

#### Requirement 9 — consistency with existing revision-scoped `ui_effects` and durable invalidation

Frontend SDK tests (`packages/frontend-sdk/src/notifications/`):

- Change `notificationDismissalCache.test.ts` to assert that a cached
  dismissal for occurrence A revision 5 is removed when a newer pending
  occurrence B for the same stable key arrives, and that B is presented.
- Add a test in `notificationDismissalCache.test.ts` asserting that a stale
  dismissal never suppresses a later stable-key publication, even when the
  newer occurrence carries the same display payload.
- Add a test asserting that the dismissal cache never retargets to a newer
  revision or occurrence.

Frontend SDK backend tests
(`packages/frontend-sdk/src/backend/restBackend.notifications.test.ts`):

- Add a test asserting that a dismissal request with a stale
  `expected_revision` returns 409 and leaves the newer revision active.
- Add a test asserting that a producer publication arriving after dismissal
  creates a new occurrence that is presented by the frontend.

Mobile and desktop notification component tests:

- Add a mobile component test asserting that dismissing a progress banner
  with `dismissible: true` hides the banner locally without sending a
  cancellation, and that the next heartbeat revision re-presents the banner.
- Add a desktop component test with the same assertion for the desktop
  notification rail.

#### Cross-cutting verification

- Run `pytest core/python/tests/test_session_notifications.py -q` and
  `pytest core/python/tests/test_application_notifications.py -q` and assert
  all updated and new tests pass.
- Run `pytest application/python/tests/test_notification_demo_plugins_http.py -q`
  and assert the public HTTP contract tests pass.
- Run `pytest plugins/openai_responses/tests/test_openai_responses_native_compaction_app.py -q`
  and assert the compaction plugin tests pass.
- Run `npm --workspace @crystal-lattice/frontend-sdk test` and assert the
  frontend SDK notification tests pass.
- Run focused mobile and desktop notification component test suites and
  assert they pass.

### Additional implementation verification

- MkDocs preparation and build pass.
- Requirement IDs are unique within the specification tree.
- Documentation diff and whitespace checks pass.
- No code changes are made under this Draft plan.