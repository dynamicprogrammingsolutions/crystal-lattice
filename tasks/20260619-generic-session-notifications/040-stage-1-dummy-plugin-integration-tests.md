# Stage 1 Dummy Plugin Integration Tests

Prove the generic notification platform with simplistic dummy plugins and real backend integration tests before MCP consumes it.

## Requirements checklist

- [ ] Add a dummy application plugin that emits a notification through an action.
- [ ] Add a dummy tool plugin or tool fixture that emits a notification during tool preparation/execution.
- [ ] Add SDK real-backend integration coverage.
- [ ] Add React Native real-backend integration coverage.
- [ ] Ensure tests use generic names and do not reference MCP/Figma/OAuth.

Parent Task: `tasks/20260619-generic-session-notifications/000-main.md`

Depends On:

- `tasks/20260619-generic-session-notifications/020-stage-1-backend-notification-substrate.md`
- `tasks/20260619-generic-session-notifications/030-stage-1-sdk-and-rn-notification-ui.md`

## Dummy Plugins

Add or reuse lightweight test plugins that exercise the platform feature:

1. Dummy application plugin:
   - action: `emit_dummy_notification`
   - action: `resolve_dummy_notification`
   - action: `dummy_followup_action`
   - emits `ActionDisplayPayload` with a `run_action` follow-up

2. Dummy tool plugin:
   - emits a notification from `prepare`/`prepare_async` or `execute_tool`
   - request should continue and complete
   - notification should be persisted and evented

Place fixtures where they fit existing test conventions:

- core/application test fixtures for Python tests
- `plugins/` only if a reusable first-party dummy plugin is needed for SDK/RN integration

## SDK Real-Backend Integration

Follow the pattern in:

`packages/frontend-sdk/src/integration/__tests__/actionDeepLinks.integration.test.ts`

Create a test such as:

`packages/frontend-sdk/src/integration/__tests__/sessionNotifications.integration.test.ts`

Test flow:

1. Start backend with deterministic provider and dummy notification plugin.
2. Create a session.
3. Execute dummy action or send a request that triggers dummy tool notification.
4. Poll `/events` or use `RestAgentBackend.listEvents`.
5. Assert `session_notification_created` is present.
6. Assert session summary metadata includes the notification.
7. Execute the notification follow-up action.
8. Assert `session_notification_updated` or `session_notification_resolved` is emitted.

## React Native Real-Backend Integration

Follow the pattern in:

- `mobile/crystal-lattice-control-rn/__integration__/ServerSettingsModal.realBackend.integration.test.tsx`
- `mobile/crystal-lattice-control-rn/__integration__/SessionSettingsModal.realBackend.integration.test.tsx`

Create a test such as:

`mobile/crystal-lattice-control-rn/__integration__/SessionNotifications.realBackend.integration.test.tsx`

Test flow:

1. Start backend with dummy notification plugin.
2. Create a session.
3. Trigger notification.
4. Render notification host/chat-slice with real backend data.
5. Assert notification title/body/action are visible.
6. Press notification action.
7. Assert backend action result/resolution occurred.

Use real backend, not mocked network, for the integration case.