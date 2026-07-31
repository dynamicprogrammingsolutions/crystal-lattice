# Notification components

Shared notification components provide:

- semantic info/success/warning/error banners;
- normal-flow banner rails;
- session notification metadata/event merging;
- inline-renderer injection;
- banner and modal routing callbacks;
- revision-aware current local dismissal;
- accessibility labels and action semantics.

Maintainer entry points:

- `src/notifications/NotificationBanner.tsx`
- `src/notifications/NotificationBannerHost.tsx`
- `src/notifications/SessionNotificationsHost.tsx`

Components do not choose application/session ownership or platform modal
fallback. Mobile and desktop hosts supply those policies.