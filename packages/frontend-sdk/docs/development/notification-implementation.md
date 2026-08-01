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
Mobile enables snapshot hydration and uses
`NotificationDismissalCache` over a host-provided `KeyValueStore`. The cache
stores connection/scope/session/notification identity plus the exact dismissed
revision, but no notification content.

Application notification controllers hide a cached exact revision, retry its
unchanged dismissal during hydration or observation, and remove the cache after
server convergence. A newer authoritative revision invalidates the older
cache entry and is presented; the controller never rewrites the cached expected
revision. Dismissal events remain in the event contract but are not forced onto
another already-open presentation.

Direct action-display close remains transient and does not enter the
notification dismissal cache. The cache is synchronization state, not the
authoritative notification record.

Tests should distinguish portable contract coverage from TypeScript-specific
details such as backend-keyed subscriptions and controller ownership.