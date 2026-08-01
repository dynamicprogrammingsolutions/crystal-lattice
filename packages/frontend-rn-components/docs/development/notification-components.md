# Notification components

Shared notification components provide:

- semantic info/success/warning/error banners;
- normal-flow banner rails;
- session notification metadata/event merging;
- inline-renderer injection;
- banner and modal routing callbacks;
- optional owner-provided asynchronous dismissal;
- immediate local suppression only after successful owner dismissal;
- local fallback for hosts that have not adopted server dismissal;
- terminal-snapshot protection against stale event resurrection;
- accessibility labels and action semantics.

Maintainer entry points:

- `src/notifications/NotificationBanner.tsx`
- `src/notifications/NotificationBannerHost.tsx`
- `src/notifications/SessionNotificationsHost.tsx`

Components do not choose application/session ownership or platform modal
fallback. Mobile and desktop hosts supply those policies.