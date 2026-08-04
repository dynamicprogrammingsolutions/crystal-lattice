# Frontend SDK and Shared Component Implementation Documentation

Document how the TypeScript SDK, React bindings, and shared React Native
components implement the portable frontend and cross-package contracts.

## Requirements checklist

- [ ] Frontend SDK development documentation maps current event types,
  selectors, polling, controller, display envelope, subscriptions, and action
  invalidation to `NTF-*`, `DSP-*`, and `FNT-*`.
- [x] The documentation clearly labels backend-keyed WeakMaps/subscriptions,
  polling implementation, and TypeScript types as current implementation
  choices rather than portable frontend requirements.
- [x] Shared React Native documentation describes notification banner/rail,
  session host, inline renderer extension, accessibility, theme semantics, and
  per-connection bounds.
- [x] Shared action-menu documentation describes stable keys, built-in/plugin
  composition, pin-model boundaries, and platform surface injection.
- [ ] Shared server-settings form/model behavior is documented at its owning
  package boundary.
- [x] Package READMEs or docs indexes route users and contributors to the new
  substantive pages.

Parent Task:
`tasks/20260730-runtime-notification-specification-documentation/000-main.md`

Depends On:

- `tasks/20260730-runtime-notification-specification-documentation/010-notification-and-action-display-contracts.md`
- `tasks/20260730-runtime-notification-specification-documentation/020-portable-frontend-behavior-specifications.md`

## Proposed artifacts

```text
packages/frontend-sdk/docs/development/
└── notification-implementation.md

packages/frontend-rn-components/docs/development/
├── notification-components.md
└── actions-menu-components.md
```

## Frontend SDK content

- TypeScript notification and event types.
- Runtime validation/skipping malformed session metadata.
- session selector and event merge behavior.
- application notification controller lifecycle and application-scope polling.
- cursor bootstrap/expiration expectations inherited from polling source.
- reload success/failure invalidating application actions.
- display envelope fields, source kinds, defaults, and validation.
- backend-instance keyed presentation subscriptions.
- authoritative dismissal mutation, revision-aware upsert, hydration, history
  selectors, and connection identity.
- form-value propagation through every notification follow-up host.
- public exports and compatibility implications.
- tests that prove portable requirements versus TypeScript internals.

Add a separate frontend-sdk-react page only when that package has substantive
notification/settings controller behavior that is not already explained by
the SDK or consuming application.

Primary references:

- `packages/frontend-sdk/src/types/notifications.ts`
- `packages/frontend-sdk/src/types/applicationNotifications.ts`
- `packages/frontend-sdk/src/notifications/`
- `packages/frontend-sdk/src/plugins/displayPresentation.ts`
- `packages/frontend-sdk/src/plugins/actionDisplayPolicy.ts`
- `packages/frontend-sdk/src/events/pollingEventSource.ts`

## React/shared component content

- `ApplicationNotificationsController` React ownership where applicable.
- shared `useServerSettingsForm` model versus platform rendering.
- `NotificationBanner` semantic variants and accessibility.
- `NotificationBannerHost` connection grouping and maximum visible count.
- `SessionNotificationsHost` metadata/event merge, server-dismiss callback,
  interaction nondismissibility, and `renderInline`.
- compact notification history and historical replay components.
- action/follow-up callbacks and form-capable inline rendering.
- `ActionsMenuBar` reusable model, pin callbacks, and injected menu surface.
- why pin persistence remains in mobile/desktop consumers.
- unit/component test boundaries and native-host mocking conventions.

## Documentation boundary

Do not tell a new frontend implementer to reproduce WeakMaps, React hooks,
context providers, or React Native component trees. Those readers use the root
portable frontend specifications. This subtask serves maintainers and consumers
of the current TypeScript packages.

## Status audit — August 3, 2026

The SDK notification and shared notification/action-menu pages exist.

Incomplete work within the approved current-state scope:

- add a concise `NTF-*`/`DSP-*`/`FNT-*` implementation mapping;
- document shared server-settings form/model ownership substantively rather
  than relying on consumer pages.

Explicit scope decision:

- decide whether documentation for future notification-history
  controllers/components stays in this documentation task until Stage E is
  implemented or is completed by the Stage E implementation work. Those
  components do not exist yet and are not a missing description of current
  runtime behavior.
