# Stage 1 SDK And React Native Notification UI

Add SDK types/selectors and React Native rendering for generic session notifications, reusing existing action display components.

## Requirements checklist

- [x] Add SDK notification/event types in `packages/frontend-sdk/src/types/notifications.ts`.
- [x] Add selector utilities in `packages/frontend-sdk/src/notifications/sessionNotifications.ts`.
- [x] Export new types and selectors from `packages/frontend-sdk/src/index.ts`.
- [x] Add `SessionNotificationsHost` RN component.
- [x] Mount the host in `SessionChatScreen`.
- [x] Route `banner`, `inline`, and `modal` consistently for session
  notifications, application notifications, and direct action responses.
- [x] Render every desktop banner source in the same connection-aware top
  notification rail.
- [x] Support mobile global hosts and React Native macOS inline/window hosts.
- [x] Support notification follow-up actions through the existing `runApplicationAction` runner.
- [x] Support local dismiss (frontend-only) without corrupting persisted state.
- [x] Add focused SDK unit tests.
- [x] Add RN component tests.

Parent Task: `tasks/20260619-generic-session-notifications/000-main.md`

Depends On: `tasks/20260619-generic-session-notifications/010-stage-1-notification-design.md`

Overlap:
`tasks/20260729-staged-application-config-and-full-reload.md`

Completed Via:
`tasks/20260729-staged-application-config-and-full-reload.md`

## SDK Work

### Types

New file `packages/frontend-sdk/src/types/notifications.ts`:

```typescript
import type { ActionDisplayPayload } from './plugins';
import type { BaseEvent } from './events';

export type SessionNotificationStatus = 'pending' | 'resolved';
export type SessionNotificationSeverity = 'info' | 'success' | 'warning' | 'error';
export type SessionNotificationModelVisibility = 'hidden';

export interface SessionNotificationSource {
  plugin: string;
  [k: string]: any;
}

export interface SessionNotificationResolution {
  action_id: string;
  values?: Record<string, any>;
  resolved_at: string;
}

export interface SessionNotification {
  id: string;
  key: string;
  kind: 'notification';
  status: SessionNotificationStatus;
  severity: SessionNotificationSeverity;
  title: string;
  body: string;
  created_at: string;
  updated_at: string;
  request_id?: string | null;
  source: SessionNotificationSource;
  display: ActionDisplayPayload;
  resolution?: SessionNotificationResolution | null;
  model_visibility: SessionNotificationModelVisibility;
}

export interface SessionNotificationCreatedEvent extends BaseEvent {
  type: 'session_notification_created';
  notification: SessionNotification;
}
export interface SessionNotificationUpdatedEvent extends BaseEvent {
  type: 'session_notification_updated';
  notification: SessionNotification;
}
export interface SessionNotificationResolvedEvent extends BaseEvent {
  type: 'session_notification_resolved';
  notification: SessionNotification;
}
```

Add these to the `Event` union in `types/events.ts`.

### Selectors

New file `packages/frontend-sdk/src/notifications/sessionNotifications.ts`:

```typescript
export function selectSessionNotifications(
  sessionSummaryOrMetadata: SessionSummary | Record<string, any> | null | undefined,
): SessionNotification[];

export function selectPendingSessionNotifications(
  sessionSummaryOrMetadata: SessionSummary | Record<string, any> | null | undefined,
): SessionNotification[];

export function mergeNotificationEvent(
  current: SessionNotification[],
  event: SessionNotificationCreatedEvent | SessionNotificationUpdatedEvent | SessionNotificationResolvedEvent,
): SessionNotification[];

export function resolveNotificationLocally(
  current: SessionNotification[],
  notificationId: string,
  resolution: SessionNotificationResolution,
): SessionNotification[];
```

Behavior:
- `selectSessionNotifications` reads `metadata.notifications.items`, validates each item (skips malformed), returns a stable-order list.
- `selectPendingSessionNotifications` filters to `status === 'pending'`.
- `mergeNotificationEvent` applies a lifecycle event to the current list: `created`/`updated` upserts by `id`; `resolved` marks `status: 'resolved'` and stores `resolution`.
- `resolveNotificationLocally` is a frontend-only helper for local dismiss: marks the notification resolved in the local view without a backend roundtrip.

These do not depend on MCP.

## React Native Work

### New component

New file `mobile/crystal-lattice-control-rn/src/components/SessionNotificationsHost.tsx`:

```typescript
interface SessionNotificationsHostProps {
  sessionSummary: SessionSummary | null;
  events: SessionNotificationCreatedEvent | SessionNotificationUpdatedEvent | SessionNotificationResolvedEvent[];
  onFollowupAction: (action: ActionDisplayFollowupAction, notification: SessionNotification) => void;
  onDismiss: (notification: SessionNotification) => void;
  activeActionId?: string | null;
}
```

Behavior:
- Reads pending notifications via `selectPendingSessionNotifications(sessionSummary)`.
- Merges live updates from `events` via `mergeNotificationEvent`.
- Renders each notification's `display` using `ActionResultInlineCard` (reuses existing card; no new visual code).
- Follow-up actions route through `onFollowupAction` → existing `runApplicationAction` path (same as `SessionChatScreen`'s `presentActionDisplay`).
- Local dismiss calls `onDismiss`, which uses `resolveNotificationLocally` to hide the notification from the local view. No backend roundtrip.

### Mount point

Mount `SessionNotificationsHost` in `SessionChatScreen` above the transcript (or in a banner area), passing:
- `sessionSummary` from the current session.
- `events` from the event subscription (filtered to notification event types).
- `onFollowupAction` wired to the existing `runApplicationAction` + `presentActionDisplay` flow.
- `onDismiss` wired to a local state update that removes the notification from the view.

The host avoids duplicating visual/action logic from action result displays.

## Tests

### SDK unit tests

Add `packages/frontend-sdk/src/notifications/__tests__/sessionNotifications.test.ts`:

- `selectSessionNotifications` returns pending notifications from metadata.
- `selectSessionNotifications` ignores malformed notifications (missing `id`, missing `status`, wrong `kind`).
- `selectPendingSessionNotifications` filters to `status === 'pending'`.
- `mergeNotificationEvent` upserts on `created`/`updated`.
- `mergeNotificationEvent` marks resolved on `resolved`.
- `resolveNotificationLocally` hides the notification from the local view.

### RN component tests

Add `mobile/crystal-lattice-control-rn/src/components/__tests__/SessionNotificationsHost.test.tsx`:

- Renders a notification title/body.
- Renders action buttons.
- Pressing a `run_action` button calls `onFollowupAction` with the action and notification.
- Pressing `dismiss` calls `onDismiss` and the notification disappears from the view.
- Pressing `copy_text` calls the existing copy path.

Keep tests generic with dummy notification data. Do not use MCP/Figma names in platform tests.

## Completion Notes

- Completed via
  `tasks/20260729-staged-application-config-and-full-reload.md`.
- SDK selectors, event merge, display routing, mobile hosts, desktop hosts,
  local dismissal, and follow-up action routing are covered.
- The focused mobile Detox test was added for native overlay z-order/touch
  behavior but was not run at this checkpoint.