# Specify Notification UI-Effect Invalidation Semantics

Record the implemented notification UI-effect and frontend invalidation
lifecycle in the existing notification specification so the normative contract
matches current behavior.

## Requirements checklist

- [ ] The notification specification defines when a notification revision
  requests a UI effect and prevents lifecycle-only or terminal revisions from
  repeating an earlier effect.
- [ ] The notification specification defines connection-scoped refresh
  invalidation behavior for active, inactive, cached, and later-mounted
  frontend consumers.
- [ ] The notification specification defines successful reload
  acknowledgment, failed reload retry, and duplicate in-flight reload
  prevention.
- [ ] The specification distinguishes the refresh semantics shared by
  notifications and action responses from behavior that remains action-only,
  such as navigation and mutation-derived policy.
- [ ] Specification requirements and evidence trace the implemented behavior,
  tests, producer documentation, and frontend SDK implementation.

## Documentation gap

Fact:

- Commit `6601e48a` (`Make notification refresh invalidations durable`)
  implemented and documented behavior that is not yet represented in the
  formal notification specification.
- Producer-facing documentation now describes the behavior in:
  - `plugins/docs/notifications-and-action-displays.md`;
  - `plugins/docs/actions.md`;
  - `plugins/openai_responses/README.md`.
- Implementation and verification evidence is recorded in
  `tasks/20260802-openai-responses-background-compaction.md`.
- Package implementation guidance exists in
  `packages/frontend-sdk/docs/development/notification-implementation.md`,
  but it does not yet describe UI-effect invalidation.

The missing normative coverage is in the existing specification under
`docs/development/specifications/notifications/`:

- `product-spec.md`;
- `technical-spec.md`;
- `frontend-behavior.md`;
- `requirements.md`.

The current specification defines notification revisions, terminal lifecycle,
authoritative reconnect state, and dismissal caches, but does not define
notification `ui_effects`, revision-scoped effect commands, or durable frontend
refresh invalidation.

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

## Proposed specification requirements

The following stable requirements are recommended for addition to
`docs/development/specifications/notifications/requirements.md`. The exact IDs
should be confirmed against the specification at execution time.

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

## Recommendations

These recommendations are not an approved execution plan, and this task does
not authorize specification edits.

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

## Open questions

- Should refresh effects remain part of the notification specification only,
  with the action-display specification linking to it, or should the common
  refresh-field vocabulary be owned by the action-display specification and
  imported by notifications?
  - Recommendation: keep durable invalidation and notification revision
    semantics in the notification specification; place only genuinely shared
    field definitions in the action-display specification if duplication
    becomes material.
- Should the specification promise immediate background reload for inactive
  mounted consumers?
  - Recommendation: no. Require eventual authoritative convergence and no lost
    invalidation, allowing each frontend to reload immediately or defer until
    activation.