# Stage 1 Dummy Plugin Integration Tests

Prove the generic notification platform with simplistic dummy plugins and real backend integration tests before MCP consumes it.

## Requirements checklist

- [ ] Add a dummy application plugin (`plugins/dummy-notification-app/`) that emits a notification through an action.
- [ ] Add a dummy tool plugin fixture (`core/python/tests/fixtures/dummy_notification_tool.py`) that emits a notification during tool execution.
- [ ] Add SDK real-backend integration coverage.
- [ ] Add React Native real-backend integration coverage.
- [ ] Ensure tests use generic names and do not reference MCP/Figma/OAuth.

Parent Task: `tasks/20260619-generic-session-notifications/000-main.md`

Depends On:
- `tasks/20260619-generic-session-notifications/020-stage-1-backend-notification-substrate.md`
- `tasks/20260619-generic-session-notifications/030-stage-1-sdk-and-rn-notification-ui.md`

## Dummy Plugins

### Dummy application plugin

New first-party plugin `plugins/dummy-notification-app/` (follows `plugins/generic-callback-app/` pattern):

Actions:
- `emit_dummy_notification` — creates a notification via `app.create_session_notification(...)` with a `run_action` follow-up. Returns a display confirming the notification was emitted.
- `resolve_dummy_notification` — resolves a notification by `id` or `key`. Used by the follow-up action below.
- `dummy_followup_action` — a generic follow-up action that the notification's `run_action` button targets. Returns a display confirming the follow-up ran.

Notification display example:
```json
{
  "format": "markdown",
  "title": "Dummy notification",
  "body": "This is a test notification from the dummy plugin.",
  "variant": "info",
  "presentation": "inline",
  "dismissible": true,
  "actions": [
    {
      "kind": "run_action",
      "id": "dummy-followup",
      "label": "Run follow-up",
      "plugin": "dummy_notification_app",
      "action_id": "dummy_followup_action"
    },
    {
      "kind": "run_action",
      "id": "dummy-resolve",
      "label": "Resolve",
      "plugin": "dummy_notification_app",
      "action_id": "resolve_dummy_notification",
      "fixed_params": { "key": "dummy:action:info" }
    }
  ]
}
```

### Dummy tool plugin fixture

New file `core/python/tests/fixtures/dummy_notification_tool.py`:

- A tool plugin that calls `context["notification_sink"].create({...})` from `execute_tool` (or `prepare`).
- The request continues and completes normally.
- The notification is persisted and evented.

Used by Python unit tests in `core/python/tests/test_session_notifications.py`. If SDK/RN integration tests need a real-backend tool path, promote to `plugins/dummy-notification-tool/` (decision point 4 — start with the fixture, promote only if needed).

## SDK Real-Backend Integration

Follow the pattern in `packages/frontend-sdk/src/integration/__tests__/actionDeepLinks.integration.test.ts`.

New test `packages/frontend-sdk/src/integration/__tests__/sessionNotifications.integration.test.ts`:

Test flow:
1. Start backend with deterministic provider and `dummy-notification-app` plugin.
2. Create a session via `RestAgentBackend.createSession`.
3. Execute `emit_dummy_notification` action via `backend.executeSessionAction`.
4. Poll `GET /events` (filtered by `session_id`) or use `RestAgentBackend.listEvents`.
5. Assert `session_notification_created` event is present with expected payload.
6. Reload session summary; assert `metadata.notifications.items` includes the notification.
7. Execute the notification's follow-up `run_action` (`dummy_followup_action`).
8. Assert the follow-up action result is `ok`.
9. Execute `resolve_dummy_notification` action.
10. Assert `session_notification_resolved` event is emitted and session metadata reflects `status: "resolved"`.

## React Native Real-Backend Integration

Follow the pattern in `mobile/crystal-lattice-control-rn/__integration__/SessionSettingsModal.realBackend.integration.test.tsx`.

New test `mobile/crystal-lattice-control-rn/__integration__/SessionNotifications.realBackend.integration.test.tsx`:

Test flow:
1. Start backend with `dummy-notification-app` plugin via `startMobileComponentBackend`.
2. Create a session.
3. Trigger notification by executing `emit_dummy_notification` action.
4. Render `SessionNotificationsHost` with real backend data (session summary + events).
5. Assert notification title/body/action button are visible.
6. Press the `Run follow-up` action button.
7. Assert the follow-up action result is `ok` (via real backend roundtrip).
8. Press `Resolve`.
9. Assert the notification disappears from the host (resolved notifications are filtered out by `selectPendingSessionNotifications`).

Use real backend, not mocked network, for the integration case.