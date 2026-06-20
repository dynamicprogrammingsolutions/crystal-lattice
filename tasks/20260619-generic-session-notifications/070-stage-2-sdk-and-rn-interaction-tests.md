# Stage 2 SDK And React Native Interaction Tests

Add SDK and React Native integration tests for generic interactive notifications after the Stage 2 backend lifecycle exists.

## Requirements checklist

- [ ] Add SDK real-backend interaction tests.
- [ ] Add React Native real-backend interaction tests.
- [ ] Verify action/form response handling through existing action UI.
- [ ] Verify timeout/cancel/resume-visible states where supported.

Parent Task: `tasks/20260619-generic-session-notifications/000-main.md`

Depends On:

- `tasks/20260619-generic-session-notifications/060-stage-2-backend-interaction-lifecycle.md`

## SDK Integration Tests

Follow:

`packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts`

Add a test that:

1. Starts a real backend with dummy interaction plugin.
2. Creates a session.
3. Starts a request/action that emits an interaction.
4. Observes interaction event.
5. Submits a response through the generic action/response API.
6. Asserts the request/tool outcome matches the dummy plugin semantics.
7. Asserts notification state is persisted as responded/resolved.

## React Native Integration Tests

Follow:

- `mobile/crystal-lattice-control-rn/__integration__/ServerSettingsModal.realBackend.integration.test.tsx`
- `mobile/crystal-lattice-control-rn/__integration__/SessionSettingsModal.realBackend.integration.test.tsx`

Add a test that:

1. Starts a real backend with dummy interaction plugin.
2. Renders the notification/interaction UI.
3. Asserts prompt text and buttons/forms appear.
4. Presses a choice.
5. Waits for backend state/event resolution.
6. Asserts the UI updates to the resolved state.

## Notes

This should not rely on MCP, OAuth, or Figma. MCP should consume the platform feature in its own follow-up after the generic path is stable.