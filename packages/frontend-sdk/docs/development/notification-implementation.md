# Frontend SDK notification implementation

The SDK provides TypeScript types, runtime selectors, event merge behavior,
application notification polling, display ownership classification, and
action execution helpers.

Maintainer entry points:

- `src/types/notifications.ts`
- `src/types/applicationNotifications.ts`
- `src/notifications/`
- `src/plugins/displayPresentation.ts`
- `src/plugins/actionDisplayPolicy.ts`
- `src/plugins/actionRunner.ts`
- `src/events/pollingEventSource.ts`

Session selectors validate metadata and skip malformed records. Application
notification controllers poll owner-scoped events. Display envelopes classify
connection and session ownership independently from presentation.

The current implementation tracks dismissal in frontend state by lifecycle
revision. This is an implementation of `FNT-005`, not a general SDK storage
primitive.

Tests should distinguish portable contract coverage from TypeScript-specific
details such as backend-keyed subscriptions and controller ownership.