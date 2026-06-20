# Stage 1 SDK And React Native Notification UI

Add SDK types/selectors and React Native rendering for generic session notifications, reusing existing action display components.

## Requirements checklist

- [ ] Add SDK notification/event types.
- [ ] Add selector utilities for pending/resolved notifications from session metadata and events.
- [ ] Add React Native notification rendering using existing `ActionDisplayPayload` UI.
- [ ] Support notification follow-up actions through the existing action runner.
- [ ] Add focused SDK/RN component tests.

Parent Task: `tasks/20260619-generic-session-notifications/000-main.md`

Depends On: `tasks/20260619-generic-session-notifications/010-stage-1-notification-design.md`

## SDK Work

Add types in `packages/frontend-sdk/src/types/events.ts` for:

- `SessionNotificationCreatedEvent`
- `SessionNotificationUpdatedEvent`
- `SessionNotificationResolvedEvent`

Add notification types, likely near session or plugin types:

- `SessionNotification`
- `SessionNotificationStatus`
- `SessionNotificationSource`

Add selector utilities, for example:

```ts
selectSessionNotifications(sessionSummaryOrMetadata)
mergeNotificationEvent(currentNotifications, event)
selectPendingSessionNotifications(...)
```

These should not depend on MCP.

## React Native Work

React Native already has:

- `ActionDisplayCard`
- `ActionResultInlineCard`
- `ActionResultModal`
- `runApplicationAction`
- generic follow-up action handling in `SessionChatScreen`

Add a small notification host that:

- reads pending notifications from current session summary metadata
- updates from notification events if the chat screen is streaming events
- renders each notification's `display` using `ActionResultInlineCard` or a thin wrapper around `ActionDisplayCard`
- executes follow-up actions with existing `runApplicationAction`

The notification host should avoid duplicating visual/action logic from action result displays.

## Tests

Add SDK unit tests:

- selector returns pending notifications from metadata
- selector ignores malformed notifications
- event reducer updates/merges notification state

Add RN component tests:

- render a notification title/body
- render action buttons
- pressing a `run_action` button calls the existing action runner path
- dismissing a notification hides it locally if dismissible, without corrupting persisted state

Keep these tests generic with dummy notification data. Do not use MCP/Figma names in platform tests.