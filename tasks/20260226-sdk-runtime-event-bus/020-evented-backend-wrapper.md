# Subtask: Evented backend wrapper (central mutation event emission)

Parent Task: `tasks/20260226-sdk-runtime-event-bus/000-main.md`

Depends On:

- `tasks/20260226-sdk-runtime-event-bus/010-sdk-runtime-and-event-bus.md`

## Description

Implement a backend wrapper/proxy that emits `SdkEvent` mutation events on successful writes.

This is the key centralization mechanism: instead of sprinkling invalidation calls in UIs, all code paths that call backend mutation methods automatically trigger a bus event.

## Existing call sites / why this matters

Mobile and desktop call backend mutations directly in many places, e.g.:

- Agent switch:
  - Mobile sessions list: `mobile/.../SessionsScreen.tsx` calls `backend.switchSessionAgent(...)`.
  - Mobile chat: `mobile/.../SessionChatScreen.tsx` calls `backend.switchSessionAgent(...)`.
  - Desktop: `desktop/.../DesktopRoot.tsx` calls `backend.switchSessionAgent(...)`.

- Overrides mutations:
  - Mobile settings modal calls `backend.patchSessionOverrides(...)` and `backend.deleteSessionOverride(...)`.

- Session plugins:
  - React hook `useSessionPluginsController` calls `backend.setSessionPlugins(...)` and `backend.clearSessionPlugins(...)`.

Backend methods exist in the SDK interface:

- `packages/frontend-sdk/src/backend/backend.ts`

REST implementation:

- `switchSessionAgent`: `packages/frontend-sdk/src/backend/restBackend.ts` (~280)
- `patchSessionOverrides`: (~376)
- `deleteSessionOverride`: (~390)
- `setSessionPlugins`: (~67)
- `clearSessionPlugins`: (~81)

## Proposed API

Add to runtime:

```ts
export function createEventedBackend(options: {
  backend: AgentBackend;
  scopeKey: string;
  bus: SdkEventBus;
}): AgentBackend;
```

Implementation details:

- Return an object implementing `AgentBackend` that delegates to the underlying backend.
- For mutation methods, emit on success:

  - `setSessionPlugins(sessionId, ...)` and `clearSessionPlugins(sessionId, ...)`
    - emit `{ type: 'session.plugins.changed', scopeKey, sessionId }`

  - `patchSessionOverrides(sessionId, ...)` and `deleteSessionOverride(sessionId, ...)`
    - emit `{ type: 'session.overrides.changed', scopeKey, sessionId }`

  - `switchSessionAgent(sessionId, ...)`
    - emit `{ type: 'session.agent.changed', scopeKey, sessionId }`

Important:
- Emit **only after** awaited call succeeds.
- Do not emit on error.

Wire runtime:

- `SdkRuntime` should accept `backend` and expose `runtime.backend` as evented wrapper.

## Tests

Add unit tests under `packages/frontend-sdk/src/runtime/__tests__/eventedBackend.test.ts`:

- Use a fake backend with methods implemented as `vi.fn()` (Vitest).
- Verify:
  - calling `runtime.backend.switchSessionAgent('s1','a')` emits exactly one event with matching payload.
  - calling mutation that throws emits nothing.
  - non-mutation methods do not emit.

Also update existing REST backend tests if needed:
- For example, keep `restBackend.sessionPlugins.test.ts` focused on HTTP calls; event emission is wrapper responsibility.

## Docs

- Add to SDK README:
  - "Always pass around `runtime.backend` rather than raw backend" (or provide guidance for migration).
  - Explain which backend methods emit which events.

## Acceptance criteria

- Evented backend wrapper exists and is used by `SdkRuntime`.
- Tests cover emission semantics.

## Execution Plan (added during completion on 2026-02-28)

1. Add `packages/frontend-sdk/src/runtime/eventedBackend.ts` exporting `createEventedBackend({ backend, scopeKey, bus })`.
2. Implement wrapper semantics so mutation methods emit only after successful completion:
   - `setSessionPlugins` / `clearSessionPlugins` -> `session.plugins.changed`
   - `patchSessionOverrides` / `deleteSessionOverride` -> `session.overrides.changed`
   - `switchSessionAgent` -> `session.agent.changed`
3. Ensure non-mutation methods delegate without emissions and thrown errors do not emit events.
4. Update `SdkRuntime` to accept an optional raw backend and expose `runtime.backend` as the wrapped backend.
5. Add tests in `packages/frontend-sdk/src/runtime/__tests__/eventedBackend.test.ts` validating:
   - single emission on successful mutation
   - zero emission on failed mutation
   - no emission for non-mutation calls.

## Completion Notes (added during completion on 2026-02-28)

- Implemented evented backend wrapper:
  - `packages/frontend-sdk/src/runtime/eventedBackend.ts`
- Mutation event emission mapping implemented exactly as specified and emitted only after successful await.
- Refactored wrapper to middleware/interceptor architecture:
  - added generic `BackendMiddleware` contract with `context` + `next`
  - supports full lifecycle control (`before`, `after success`, `after error`, `finally`) via async middleware
  - default mutation emissions are now composed from separate per-method middleware entries
  - removed event-rule API and method-specific branching from wrapper internals
- `SdkRuntime` now accepts a raw backend and exposes:
  - `runtime.rawBackend`
  - `runtime.backend` (evented wrapper)
- `SdkRuntime` supports extension through one path:
  - `backendMiddlewares` (appended after SDK default mutation-event middleware)
- Added tests:
  - `packages/frontend-sdk/src/runtime/__tests__/eventedBackend.test.ts`
  - Covers default success emission semantics, no emission on failed default mutations, and custom middleware lifecycle handling (success/error/finally).
- Verification:
  - `npm test` (from `packages/frontend-sdk`) passes with the new wrapper tests.

## Completion Notes Addendum (added during completion on 2026-02-28)

- Enforced separation of concerns for runtime vs domain logic:
  - `packages/frontend-sdk/src/runtime/eventedBackend.ts` now contains generic middleware pipeline and generic method-success middleware helper only.
  - session-specific middleware logic moved to:
    - `packages/frontend-sdk/src/sessionMutations/createSessionScopedSuccessEventMiddleware.ts`
    - `packages/frontend-sdk/src/sessionMutations/sessionMutationMiddlewares.ts`
- `SdkRuntime` no longer injects default middlewares.
- Added default composition factory layer:
  - `packages/frontend-sdk/src/runtimeFactory/createDefaultBackendMiddlewares.ts`
  - `packages/frontend-sdk/src/runtimeFactory/createDefaultSdkRuntime.ts`
- Frontends can now choose:
  - `createDefaultSdkRuntime(...)` for package defaults
  - `new SdkRuntime(...)` with fully custom middleware lists
