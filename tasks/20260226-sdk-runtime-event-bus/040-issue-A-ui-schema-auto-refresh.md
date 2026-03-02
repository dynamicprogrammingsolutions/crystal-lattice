# Subtask: Issue Set A — Session UI schema auto-refresh

Parent Task: `tasks/20260226-sdk-runtime-event-bus/000-main.md`

Depends On:

- `tasks/20260226-sdk-runtime-event-bus/010-sdk-runtime-and-event-bus.md`
- `tasks/20260226-sdk-runtime-event-bus/020-evented-backend-wrapper.md`
- `tasks/20260226-sdk-runtime-event-bus/030-resource-rule-pattern-and-docs.md`

## Description

Implement the concrete behavior:

> When session plugins are changed (turned on/off) or when session agent / overrides are changed, session UI schema should be invalidated and reloaded automatically.

This should work across all frontends that use the SDK, without requiring per-screen explicit `invalidate()` calls.

## Existing behavior (reference)

`SessionUiSchemaController`:

- caches results in a module-level `CACHE` keyed by `cacheKey::sessionId`
- `load()` returns cached results if present
- `invalidate()` exists but is not automatically called

Ref:

- `packages/frontend-sdk/src/uiSchema/sessionUiSchemaController.ts`

## Implementation plan

### 1) Make SessionUiSchemaController bus-aware

Extend `SessionUiSchemaController` to accept bus + scopeKey (or take `SdkRuntime`).

Recommended direction:

- Prefer passing `SdkRuntime` or `(bus, scopeKey)` into the controller constructor.
- Update React hook `useSessionUiSchemaController` (frontend-sdk-react) to use runtime if available.

Behavior:

- On bus event types:
  - `session.plugins.changed`
  - `session.overrides.changed`
  - `session.agent.changed`
  for same `scopeKey` and `sessionId`:

  1. call `invalidate()` (clears cache)
  2. if controller is enabled/active, call `load()` (deduped)

### 2) Ensure mutation events are emitted

This should already be done by evented backend wrapper (Subtask 020):

- `setSessionPlugins` + `clearSessionPlugins` => `session.plugins.changed`
- `patchSessionOverrides` + `deleteSessionOverride` => `session.overrides.changed`
- `switchSessionAgent` => `session.agent.changed`

### 3) Dedupe and avoid reload storms

Add a minimal mechanism:

- If `load()` is inflight, set `needsReload=true`.
- After load finishes, if `needsReload`, run load again once.

Avoid emitting any bus events from `load()`.

## Tests

Add tests under `packages/frontend-sdk/src/uiSchema/__tests__/sessionUiSchemaController.bus.test.ts`:

- Arrange:
  - fake backend with `getSessionUiSchema` mocked
  - create runtime with bus
  - create controller for `sessionId='s1'`

- Act:
  1) initial `load()` populates cache
  2) emit `session.plugins.changed` event for `s1`

- Assert:
  - controller calls backend again (cache invalidated)
  - elements update

Also test:

- event for other sessionId does nothing
- event for other scopeKey does nothing
- if controller disabled, it invalidates cache but does not immediately reload (depends on chosen semantics)

## Docs

Update `packages/frontend-sdk/README.md`:

- list which events invalidate session UI schema
- document how to construct controllers with runtime

## Acceptance criteria

- UI schema auto-refreshes for session on plugins/agent/overrides changes.
- No frontend code needs to call `SessionUiSchemaController.invalidate()` explicitly.
- Tests cover event-driven invalidation.

## Execution Plan (added during completion on 2026-03-01)

1. Make `SessionUiSchemaController` bus-aware in `packages/frontend-sdk/src/uiSchema/sessionUiSchemaController.ts`:
   - accept optional bus/scope wiring (`bus`, `scopeKey`) plus `enabled`
   - subscribe to bus mutation events (`session.plugins.changed`, `session.overrides.changed`, `session.agent.changed`)
   - for matching `(scopeKey, sessionId)`, invalidate cache and reload only when enabled.
2. Add reload coalescing in `SessionUiSchemaController`:
   - if `load()` is in-flight, mark `needsReload=true`
   - once current load finishes, run at most one follow-up load when needed.
3. Update React hook `packages/frontend-sdk-react/src/useSessionUiSchemaController.ts`:
   - add optional `runtime` input
   - prefer runtime wiring (`runtime.backend`, `runtime.bus`, `runtime.scopeKey`) when provided
   - keep existing `backend + cacheKey` compatibility
   - call `controller.dispose()` on unmount.
4. Wire runtime usage at frontend connection boundaries so evented backend is actually used:
   - mobile app: create default runtime per active connection in `mobile/crystal-lattice-control-rn/App.tsx`, pass runtime through `ConnectedRoot` into `SessionChatScreen`, and pass runtime to `useSessionUiSchemaController`.
   - desktop app: create/store default runtime per open connection in `desktop/crystal-lattice-control-desktop-rn/src/connections/useOpenConnections.ts`, thread runtime lookup through `DesktopRoot` and `ChatPaneTabStack` into `ChatPane`, and pass runtime to `useSessionUiSchemaController`.
5. Add tests in `packages/frontend-sdk/src/uiSchema/__tests__/sessionUiSchemaController.bus.test.ts` for:
   - matching mutation event triggers invalidate + reload
   - non-matching session and non-matching scope do not reload
   - disabled controller invalidates without immediate reload
   - in-flight load coalescing performs one follow-up reload.
6. Update `packages/frontend-sdk/README.md` with explicit UI-schema invalidation events and runtime-oriented controller construction guidance.
7. Run verification:
   - `npm run typecheck` and `npm test` in `packages/frontend-sdk`
   - `npm test` in `packages/frontend-sdk-react`
   - targeted typecheck/lint checks for touched desktop/mobile packages if available.

## Completion Notes (added during completion on 2026-03-01)

- Made `SessionUiSchemaController` bus-aware in `packages/frontend-sdk/src/uiSchema/sessionUiSchemaController.ts`:
  - added optional `bus`, `scopeKey`, and `enabled` inputs
  - added subscription lifecycle (`dispose()`)
  - added explicit handling for:
    - `session.plugins.changed`
    - `session.overrides.changed`
    - `session.agent.changed`
  - matching events now invalidate cache and auto-reload only when enabled.
- Added reload coalescing to avoid reload storms:
  - while `load()` is in-flight, additional `load()` requests mark `needsReload`
  - one follow-up reload runs after current load, bypassing cache when required.
- Updated React hook `packages/frontend-sdk-react/src/useSessionUiSchemaController.ts`:
  - added optional `runtime`
  - uses runtime wiring (`runtime.backend`, `runtime.bus`, `runtime.scopeKey`) when provided
  - keeps existing `backend + cacheKey` compatibility
  - calls `controller.dispose()` on unmount.
- Wired runtime through frontend connection boundaries so mutation events are emitted from shared backend calls:
  - mobile:
    - `mobile/crystal-lattice-control-rn/App.tsx`
    - `mobile/crystal-lattice-control-rn/src/ConnectedRoot.tsx`
    - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
  - desktop:
    - `desktop/crystal-lattice-control-desktop-rn/src/connections/useOpenConnections.ts`
    - `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx`
    - `desktop/crystal-lattice-control-desktop-rn/src/tabs/ChatPaneTabStack.tsx`
    - `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`
- Added SDK tests for event-driven invalidation and coalescing:
  - `packages/frontend-sdk/src/uiSchema/__tests__/sessionUiSchemaController.bus.test.ts`
- Updated docs:
  - `packages/frontend-sdk/README.md` now documents session UI-schema auto-refresh event triggers and runtime wiring guidance.

### Verification

- `npm run typecheck` (packages/frontend-sdk) passed.
- `npm test` (packages/frontend-sdk) passed.
- `npm test` (packages/frontend-sdk-react) passed.
- `npx tsc -p tsconfig.json --noEmit` passed in:
  - `packages/frontend-sdk-react`
  - `desktop/crystal-lattice-control-desktop-rn`
  - `mobile/crystal-lattice-control-rn`

## Completion Notes Addendum (added during completion on 2026-03-01)

- Simplified controller bus wiring by reusing runtime base class:
  - `SessionUiSchemaController` now extends `BusAwareController` instead of duplicating its own bus subscription sequence handling.
  - Removed controller-local bus bookkeeping fields and custom `subscribeToBus` implementation.
- Made `BusAwareController` accept optional bus input (`bus?: SdkEventBus | null`) so controllers can keep compatibility with non-runtime call sites while still sharing one bus lifecycle implementation.
- Expanded `packages/frontend-sdk/README.md` with a concrete "Building Bus-Aware Controllers" section:
  - includes a minimal controller template using `BusAwareController`
  - includes implementation checklist and React unmount cleanup snippet.

### Verification (addendum)

- `npm run typecheck` (packages/frontend-sdk) passed after simplification.
- `npm test` (packages/frontend-sdk) passed after simplification.
- `npm test` (packages/frontend-sdk-react) passed.

## Completion Notes Addendum 2 (added during completion on 2026-03-02)

- Applied runtime-context simplification as a breaking change (no backward-compat path retained):
  - added `SdkRuntimeProvider` and context hooks in `packages/frontend-sdk-react/src/sdkRuntimeContext.tsx`:
    - `useSdkRuntimeContext`
    - `useRuntime`
    - `useBackend`
    - `useConnectionScopeKey`
- Converted `frontend-sdk-react` hooks to runtime-context-driven APIs:
  - `useChatController`
  - `useSessionsController`
  - `useAgentsController`
  - `useSessionUiSchemaController`
  - `useSessionPluginsController`
  - `useSessionEvents`
  - all now resolve backend/scope from `SdkRuntimeProvider` context.
- Converted `ApplicationPluginsProvider` to runtime-context-driven API (no backend/connectionId props).
- Frontend integration changes:
  - mobile:
    - `ConnectedRoot` now wraps subtree with `SdkRuntimeProvider` + `ApplicationPluginsProvider`
    - removed `runtime` prop plumbing into `SessionChatScreen`
    - updated hook callsites to new context-driven signatures.
  - desktop:
    - `SessionsPanel` now receives `runtime` and wraps internals with `SdkRuntimeProvider` + `ApplicationPluginsProvider`
    - `ChatPaneTabStack` tab frames now wrap each chat pane with per-connection `SdkRuntimeProvider` + `ApplicationPluginsProvider`
    - `ChatPane` uses `useRuntime()` for plugin-window coordination and no longer accepts `runtime` prop
    - session plugins window coordination now carries `runtime` (`sessionPluginsCoordinator.ts`), and `SessionPluginsWindow` wraps inner content with `SdkRuntimeProvider`.
- Docs updated:
  - `packages/frontend-sdk/README.md` now documents runtime context usage and minimal hook wiring.

### Verification (addendum 2)

- `npx tsc -p tsconfig.json --noEmit` passed in:
  - `packages/frontend-sdk-react`
  - `desktop/crystal-lattice-control-desktop-rn`
  - `mobile/crystal-lattice-control-rn`
- `npm test` passed in:
  - `packages/frontend-sdk-react`
  - `packages/frontend-sdk`
- `npm run typecheck` passed in:
  - `packages/frontend-sdk`
