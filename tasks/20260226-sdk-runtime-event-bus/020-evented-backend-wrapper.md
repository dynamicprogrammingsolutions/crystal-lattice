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
