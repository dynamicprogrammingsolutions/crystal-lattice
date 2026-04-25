# A1: SDK Local Invalidation For Session UI Schema

Parent Task: `tasks/20260306-session-ui-reload/000-main.md`

## Relation

COMPLETED VIA: `tasks/20260306-session-ui-reload/050-session-settings-controller.md` — SDK invalidation mechanism implemented as part of the session settings controller (see `packages/frontend-sdk/src/uiSchema/sessionUiSchemaInvalidation.ts`).

## Status

- [x] Completed (via 050-session-settings-controller)

Description:
Implement an SDK-level invalidation mechanism so that when this client updates per-session settings (config overrides) or session plugin enablement, the session-specific UI schema cache is invalidated and reloaded automatically.

Scope / requirements:
- Mandatory.
- Do not rely on server-published events.
- Apply to both mobile and desktop via shared frontend SDK + React hook.
- Minimal/no app-level frontend code changes (mobile/desktop screens ideally unchanged).
- Avoid major refactor; keep changes additive.

Relevant code:
- UI schema caching: `packages/frontend-sdk/src/uiSchema/sessionUiSchemaController.ts`
- React hook: `packages/frontend-sdk-react/src/useSessionUiSchemaController.ts`
- REST backend mutations:
  - `packages/frontend-sdk/src/backend/restBackend.ts`:
    - `patchSessionOverrides(...)`
    - `deleteSessionOverride(...)`
    - `setSessionPlugins(...)`
    - `clearSessionPlugins(...)`

Proposed implementation:
- Add a small in-memory pub/sub keyed by `(backend instance, sessionId)` in `packages/frontend-sdk`.
- On successful completion of the above mutation methods, emit a `sessionUiSchemaInvalidated` signal.
- In `useSessionUiSchemaController`, subscribe when enabled and call:
  - `controller.invalidate()`
  - `controller.load()`

Acceptance criteria:
- After changing a session override or session plugins, the chat UI (composer attachments/footer/etc.) updates without requiring manual refresh.
- Works in both mobile and desktop since both use `useSessionUiSchemaController`.
- Unit tests cover that successful mutations emit invalidation.

## Completion notes (added during verification)

### Implementation status

This subtask was implemented as part of `tasks/20260306-session-ui-reload/050-session-settings-controller.md`.

### What was implemented

1. **Session UI schema invalidation mechanism** in `packages/frontend-sdk/src/uiSchema/sessionUiSchemaInvalidation.ts`:
   - `SessionUiSchemaInvalidationEvent` interface
   - `subscribeSessionUiSchemaInvalidated(backend, sessionId, listener)` 
   - `emitSessionUiSchemaInvalidated(backend, sessionId, options)`

2. **Integration with REST backend mutations** in `packages/frontend-sdk/src/backend/restBackend.ts`:
   - `setSessionPlugins(...)` emits `session_plugins_updated`
   - `clearSessionPlugins(...)` emits `session_plugins_updated`
   - `patchSessionOverrides(...)` emits `session_overrides_updated`
   - `deleteSessionOverride(...)` emits `session_overrides_updated`

3. **Controller integration**:
   - `SessionUiSchemaController.invalidate()` method
   - `SessionSettingsController.invalidate()` method
   - Both controllers subscribe to invalidation events and reload

### Files touched

- `packages/frontend-sdk/src/uiSchema/sessionUiSchemaInvalidation.ts`
- `packages/frontend-sdk/src/backend/restBackend.ts`
- `packages/frontend-sdk/src/uiSchema/sessionUiSchemaController.ts`
- `packages/frontend-sdk/src/sessionSettings/sessionSettingsController.ts`
- `packages/frontend-sdk/src/backend/restBackend.sessionUiSchemaInvalidation.test.ts`
