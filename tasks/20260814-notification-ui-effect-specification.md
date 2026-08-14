# Specify Notification UI-Effect Invalidation Semantics

Record the implemented notification UI-effect and frontend invalidation
lifecycle in the existing notification specification so the normative contract
matches current behavior.

## Requirements checklist

- [x] The notification specification defines when a notification revision
  requests a UI effect and prevents lifecycle-only or terminal revisions from
  repeating an earlier effect.
- [x] The notification specification defines connection-scoped refresh
  invalidation behavior for active, inactive, cached, and later-mounted
  frontend consumers.
- [x] The notification specification defines successful reload
  acknowledgment, failed reload retry, and duplicate in-flight reload
  prevention.
- [x] The specification distinguishes the refresh semantics shared by
  notifications and action responses from behavior that remains action-only,
  such as navigation and mutation-derived policy.
- [x] Specification requirements and evidence trace the implemented behavior,
  tests, producer documentation, and frontend SDK implementation.

## Documentation gap at task creation

Fact:

- Commit `6601e48a` (`Make notification refresh invalidations durable`)
  implemented and documented behavior that was not represented in the formal
  notification specification when this task was created.
- Producer-facing documentation now describes the behavior in:
  - `plugins/docs/notifications-and-action-displays.md`;
  - `plugins/docs/actions.md`;
  - `plugins/openai_responses/README.md`.
- Implementation and verification evidence is recorded in
  `tasks/20260802-openai-responses-background-compaction.md`.
- Package implementation guidance existed in
  `packages/frontend-sdk/docs/development/notification-implementation.md`,
  but did not yet describe UI-effect invalidation.

The missing normative coverage is in the existing specification under
`docs/development/specifications/notifications/`:

- `product-spec.md`;
- `technical-spec.md`;
- `frontend-behavior.md`;
- `requirements.md`.

At task creation, the specification defined notification revisions, terminal
lifecycle, authoritative reconnect state, and dismissal caches, but did not
define notification `ui_effects`, revision-scoped effect commands, or durable
frontend refresh invalidation.

## Implemented behavior to capture

- `ui_effects` belongs only to the notification revision that explicitly
  supplies it.
- An update that omits `ui_effects` does not inherit an earlier revision's
  effects.
- Dismissed, resolved, and expired revisions do not execute effects, including
  compatibility handling for older terminal records that retained them.
- A newer pending revision may deliberately request the same effect again.
- Refresh effects are scoped to the backend connection that receives them.
- Session and session-list invalidations remain pending until authoritative
  reload succeeds.
- Application-action invalidation remains pending until the plugin registry
  refresh succeeds.
- An inactive or unavailable consumer may defer work without losing the
  invalidation; a later active or mounted consumer can receive it.
- Failed reload attempts leave the invalidation pending.
- Successful reload acknowledges the matching invalidation revision.
- Backend-scoped in-flight claims prevent rerender or resubscription from
  starting duplicate reloads for the same invalidation.
- A newer invalidation is not cleared by late acknowledgment of an older one.
- Notification refresh effects never navigate to another session.

## Specification requirements recorded

The following stable requirements were added to
`docs/development/specifications/notifications/requirements.md`:

- `NTF-015`: Notification UI effects are revision-scoped commands. Only a
  pending revision that explicitly supplies an effect requests execution, and
  lifecycle-only or terminal revisions do not inherit or repeat it.
- `FNT-011`: A notification refresh effect invalidates data only on its owning
  connection and remains observable until an appropriate frontend consumer
  successfully reloads authoritative state.
- `FNT-012`: Active, inactive, cached, and later-mounted consumers converge on
  authoritative state without notification-driven navigation.
- `FNT-013`: Frontend delivery prevents duplicate concurrent reloads for one
  invalidation, retains failed or deferred invalidations for retry, and does
  not let acknowledgment of an older invalidation clear a newer one.
- `NTF-016`: Notifications and application-action responses share explicit
  refresh field meanings, while notification effects exclude action-only
  navigation and mutation-derived behavior.

## Accepted recommendations

These recommendations were initially recorded without an approved execution
plan. The user approved applying them on August 14, 2026.

- Extend the existing notification specification rather than creating another
  specification directory or a separate multi-file specification.
- Use `product-spec.md` for the user-visible convergence outcome: completed
  background work refreshes affected data even when a frontend used cached
  state or was inactive.
- Use `technical-spec.md` for revision-scoped command semantics,
  connection-keyed invalidation state, acknowledgment, retries, in-flight
  claims, and stale-acknowledgment protection.
- Use `frontend-behavior.md` for active, inactive, unmounted, reconnecting, and
  cache-hydrated consumer behavior across mobile and desktop.
- Add the stable requirements and concrete evidence to `requirements.md`.
- Update
  `packages/frontend-sdk/docs/development/notification-implementation.md` with
  TypeScript-specific ownership and maintainer entry points after the
  normative specification is updated.
- Add a narrow cross-reference in the action-display specification only if
  needed to explain that action responses and notifications share refresh
  field meanings. Keep notification lifecycle and durable invalidation
  ownership in the notification specification.
- Treat commit `6601e48a` and its focused core, SDK, component, HTTP, and iOS
  simulator tests as implementation evidence, while independently verifying
  the final specification wording against current code.

## Resolved decisions

- Durable invalidation and notification revision semantics remain in the
  notification specification. No action-display specification change was
  needed because refresh effects are not display payloads.
- The specification requires eventual authoritative convergence and no lost
  invalidation. It does not require immediate background reload for every
  inactive mounted consumer.

## Execution plan

Status: Approved

Update the existing notification specification in place. Keep notification
revision semantics and durable invalidation ownership in the notification
specification, describe only the shared refresh-field meaning relative to
action responses, and avoid creating another specification directory.

This plan was approved by the user's August 14, 2026 instruction to update the
documentation immediately when ownership was straightforward.

### Implementation decisions and open questions

- Decision: `docs/development/specifications/notifications/` owns the behavior.
- Decision: notification refresh delivery guarantees eventual authoritative
  convergence, not immediate background reload for every inactive consumer.
- Decision: action responses share refresh field meanings but remain one-shot;
  notification revision and replay semantics do not apply to them.
- Open questions: none blocking this documentation update.

### Documentation

- Update notification product behavior, technical contract, portable frontend
  behavior, and stable requirements.
- Align the frontend SDK implementation document.
- Correct producer documentation if it implies that one-shot action responses
  receive notification-style durable replay.

### Task checklist

- [x] Record the user-visible convergence behavior.
- [x] Record revision-scoped notification effect semantics.
- [x] Record frontend invalidation, acknowledgment, retry, and concurrency
  behavior.
- [x] Add stable requirements and evidence.
- [x] Align implementation and producer documentation.
- [x] Validate the documentation build and links.

### Requirement verification

- Requirements 1–4: inspect the product, technical, and frontend specification
  pages for complete normative coverage.
- Requirement 5: inspect stable requirement rows and evidence references
  against commit `6601e48a` and its documented verification.

### Additional implementation verification

- Build the prepared MkDocs site.
- Run repository diff checks for malformed Markdown or whitespace.

## Implementation Notes

- The existing notification specification was the clear owner because
  revision semantics, authoritative reconnect state, and frontend lifecycle
  already live there.
- The action-display specification was left unchanged. It owns display
  payloads, while `ui_effects` coordinates refresh outside the display
  payload.
- Producer documentation was corrected to distinguish durable
  notification-delivered invalidation from one-shot action-response effects.

## Completion Notes

Completed August 14, 2026.

Outcome:

- added product-level refresh convergence behavior;
- added the revision-scoped `ui_effects` and frontend invalidation technical
  contract;
- added portable active, inactive, cached, later-mounted, retry,
  acknowledgment, and concurrency behavior;
- added requirements `NTF-015`, `NTF-016`, and `FNT-011` through `FNT-013`
  with implementation and verification evidence;
- updated the frontend SDK notification implementation guide;
- corrected the application-action authoring documentation so one-shot action
  responses do not imply notification-style replay.

Verification:

- the prepared MkDocs site built successfully;
- requirement IDs are unique within the current specification tree;
- documentation diff and whitespace checks passed;
- existing MkDocs navigation and API-reference warnings remain unrelated to
  this task.