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
notification controllers can hydrate an authoritative owner snapshot before
polling from a cursor captured before that snapshot. Revision-aware merge
prevents stale events from replacing newer snapshot records. Display envelopes
classify connection and session ownership independently from presentation.

`RestAgentBackend` exposes application/session list and dismiss operations.
Mobile enables snapshot hydration and applies successful server dismissal
responses immediately. Dismissal events are retained in the event contract but
are not forced onto another already-open presentation.

Local revision suppression remains available for transient action displays and
for hosts that have not yet adopted server dismissal. It is not the
authoritative notification record.

Tests should distinguish portable contract coverage from TypeScript-specific
details such as backend-keyed subscriptions and controller ownership.