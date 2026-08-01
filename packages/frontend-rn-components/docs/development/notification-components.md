# Notification components

Shared notification components provide:

- semantic info/success/warning/error banners;
- normal-flow banner rails;
- session notification metadata/event merging;
- inline-renderer injection;
- banner and modal routing callbacks;
- optional owner-provided asynchronous dismissal;
- immediate local suppression only after successful owner dismissal;
- opt-in optimistic suppression that remains hidden after synchronization
  failure;
- externally supplied revision keys for a persistent host dismissal cache;
- local fallback for hosts that have not adopted server dismissal;
- terminal-snapshot protection against stale event resurrection;
- accessibility labels and action semantics.

Maintainer entry points:

- `src/notifications/NotificationBanner.tsx`
- `src/notifications/NotificationBannerHost.tsx`
- `src/notifications/SessionNotificationsHost.tsx`

Components do not choose application/session ownership or platform modal
fallback. Mobile supplies optimistic revision-scoped cache policy. Desktop
supplies server-authoritative success-only policy and leaves a notification
visible when owner dismissal fails.