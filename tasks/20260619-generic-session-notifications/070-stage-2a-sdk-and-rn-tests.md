# Stage 2a SDK And React Native Interaction Tests

Add SDK and React Native integration tests for generic interactive notifications after the Stage 2a backend lifecycle exists.

## Requirements checklist

- [ ] Add SDK real-backend interaction tests.
- [ ] Add React Native real-backend interaction tests.
- [ ] Verify action/form response handling through existing action UI.
- [ ] Verify timeout/cancel/resume-visible states where supported.

Parent Task: `tasks/20260619-generic-session-notifications/000-main.md`

Depends On:
- `tasks/20260619-generic-session-notifications/060-stage-2a-backend-wait-only.md`

## SDK Integration Tests

Follow the pattern in `packages/frontend-sdk/src/integration/__tests__/actionDeepLinks.integration.test.ts`.

New test `packages/frontend-sdk/src/integration/__tests__/sessionInteractions.integration.test.ts`:

Test flow:
1. Start a real backend with deterministic provider and dummy interaction plugin (dummy interceptor + dummy tool).
2. Create a session via `RestAgentBackend.createSession`.
3. Send a request that triggers the dummy tool call (which triggers the interceptor).
4. Poll `GET /events` (filtered by `session_id`).
5. Assert `session_notification_created` event with `kind: "interaction"`, `status: "pending_response"`.
6. Extract the `interaction_id` from the event.
7. Execute `respond_to_interaction` action via `backend.executeSessionAction` with `action_id: "approve"`.
8. Assert `session_notification_responded` event is emitted.
9. Assert the request completes and the tool executed (tool result present in final messages).
10. Repeat with `action_id: "deny"` → assert the tool did not execute and a "denied" result is present.
11. Repeat with no response → assert timeout → `default_action_id: "deny"` applied.

## React Native Integration Tests

Follow the pattern in `mobile/crystal-lattice-control-rn/__integration__/SessionSettingsModal.realBackend.integration.test.tsx`.

New test `mobile/crystal-lattice-control-rn/__integration__/SessionInteractions.realBackend.integration.test.tsx`:

Test flow:
1. Start a real backend with dummy interaction plugin via `startMobileComponentBackend`.
2. Create a session.
3. Render `SessionChatScreen` (or `SessionNotificationsHost`) with real backend data.
4. Send a request that triggers the dummy tool call.
5. Assert the interaction prompt text and `Approve` / `Deny` buttons appear.
6. Press `Approve`.
7. Wait for backend state/event resolution.
8. Assert the UI updates to the resolved state (notification disappears or shows resolved state).
9. Assert the tool executed (tool result visible in the transcript).
10. Repeat with `Deny` → assert the tool did not execute.

## Notes

- Use real backend, not mocked network, for the integration case.
- Do not rely on MCP, OAuth, or Figma. MCP should consume the platform feature in its own follow-up after the generic path is stable.
- The dummy interceptor must be a provider extension (so it's discovered by `AgentApplication` from the active provider's extensions) per the interceptor task's provider-scoping requirement.