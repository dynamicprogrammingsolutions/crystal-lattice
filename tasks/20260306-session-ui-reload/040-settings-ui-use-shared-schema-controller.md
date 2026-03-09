# Settings UI: Use Shared Session UI Schema Controller

Parent Task: `tasks/20260306-session-ui-reload/000-main.md`

Depends On:
- `tasks/20260306-session-ui-reload/010-a1-sdk-local-invalidation.md`

Description:
Update the mobile and desktop session settings UIs to use `useSessionUiSchemaController` for loading session UI schema, so they benefit from cached synchronous hydration and automatic SDK-driven reloads when session UI schema is invalidated.

Motivation:
- The chat screens already load session UI schema and populate the shared SDK cache.
- Settings UIs currently fetch `getSessionUiSchema(sessionId)` directly and therefore do not reuse the cached result or benefit from the new invalidation mechanism.
- Switching to the shared controller gives faster popup opening and live schema updates (for example removing `reasoning_effort` when model changes).

Relevant code:
- Mobile settings modal: `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx`
- Desktop settings window: `desktop/crystal-lattice-control-desktop-rn/src/windows/SessionSettingsWindow.tsx`
- Shared hook: `packages/frontend-sdk-react/src/useSessionUiSchemaController.ts`

Implementation notes:
- Replace direct `backend.getSessionUiSchema(sessionId)` loading with `useSessionUiSchemaController(...)`.
- Use the same `cacheKey` used by chat (`connectionId`) so the settings UI opens from the existing cache when available.
- Keep overrides/base-config/config-schema loading separate.
- Avoid wiping local text-edit state (`pendingTextByKey`) on schema-only refreshes.

Acceptance criteria:
- Opening settings after chat has already loaded UI schema shows settings immediately from cache when possible.
- Changing a setting that alters the session UI schema updates the settings list live.
- Unchanged setting rows do not unnecessarily remount; in-progress text edits are preserved for unaffected keys.
