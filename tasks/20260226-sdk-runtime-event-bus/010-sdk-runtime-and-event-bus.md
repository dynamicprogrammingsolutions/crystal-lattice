# Subtask: SDK Runtime + Generic Event Bus (connection-scoped)

Create a connection-scoped `SdkRuntime` and a typed generic `SdkEventBus` in `packages/frontend-sdk`.

Parent Task: `tasks/20260226-sdk-runtime-event-bus/000-main.md`

## Description

Implement a small framework core that other SDK layers can build on:

- A **generic event bus**: anyone can subscribe; events are *typed* and include `scopeKey`.
- A **runtime** object created per connection (`scopeKey = connectionId/cacheKey`).
- The runtime is the integration point for frontends (mobile/desktop/web): create once, pass down.

This subtask does **not** yet emit events from backend methods. It only defines the bus + runtime container.

## Requirements / constraints

- Avoid circular updates and "max update depth" problems:
  - Bus should be **push-only**; no implicit fan-out dependency graph.
  - Resources decide which events to react to.
- Must support multiple simultaneous connections (desktop).

## Proposed API

### SDK events

Define a minimal event union (extend later):

```ts
export type SdkEvent =
  | { type: 'session.plugins.changed'; scopeKey: string; sessionId: string }
  | { type: 'session.overrides.changed'; scopeKey: string; sessionId: string }
  | { type: 'session.agent.changed'; scopeKey: string; sessionId: string }
  // Observational notification: indicates SessionSummariesStore has already applied an update.
  // Consumers should read the data from the store.
  | { type: 'session.summary.upserted'; scopeKey: string; sessionId: string };
```

Notes:
- `*.changed` events are "write succeeded" mutation notifications.
- `session.summary.upserted` is optional but useful for observers; it must **not** be used to trigger reload of summary itself.
  See Subtask 030 for the required documentation pattern and the payload-carrying alternative.

### Bus

The bus can be built on `SimpleSubscribable`:

```ts
export interface SdkEventBusSnapshot {
  seq: number;
  lastEvent: SdkEvent | null;
}

export class SdkEventBus extends SimpleSubscribable<SdkEventBusSnapshot> {
  emit(ev: SdkEvent): void;
}
```

This keeps the bus very small and compatible with React `useSyncExternalStore`.

### Runtime

```ts
export class SdkRuntime {
  readonly scopeKey: string;
  readonly bus: SdkEventBus;
  // backend wrapper is added in Subtask 020
  // resource singletons (stores/controllers) are added later
}
```

## Implementation steps

1) Add new module(s) to `packages/frontend-sdk/src/runtime/`:

- `sdkEventBus.ts`
- `sdkEvents.ts`
- `sdkRuntime.ts`

2) Export from `packages/frontend-sdk/src/index.ts` so all frontends can import.

3) Add a small unit test suite in `packages/frontend-sdk/src/runtime/__tests__/`:

- `sdkEventBus.test.ts`
  - verifies `emit()` increments `seq`
  - verifies subscribers fire exactly once per emit
  - verifies unsubscribe works

## Docs

Add a section to the new SDK README (created in Subtask 030, but this subtask should add content text):

- Explain runtime-per-connection concept
- Explain event bus: push-only, resources subscribe explicitly

## Acceptance criteria

- `SdkEventBus` implemented and tested.
- `SdkRuntime` implemented (bus + scopeKey).
- Types exported from SDK entrypoint.

## Execution Plan (added during completion on 2026-02-28)

1. Add `packages/frontend-sdk/src/runtime/sdkEvents.ts` with a typed `SdkEvent` union for mutation notifications and observational summary upsert notifications.
2. Add `packages/frontend-sdk/src/runtime/sdkEventBus.ts` implementing:
   - `SdkEventBusSnapshot` (`seq`, `lastEvent`)
   - `SdkEventBus` extending `SimpleSubscribable`
   - `emit()` semantics that increment `seq` and publish `lastEvent`.
3. Add `packages/frontend-sdk/src/runtime/sdkRuntime.ts` with connection-scoped runtime shape (`scopeKey`, `bus`) and constructor wiring that remains compatible with later backend wrapping.
4. Export new runtime types/classes from `packages/frontend-sdk/src/index.ts`.
5. Add unit tests in `packages/frontend-sdk/src/runtime/__tests__/sdkEventBus.test.ts` covering:
   - sequence increments
   - one notification per emit
   - unsubscribe behavior.

## Completion Notes (added during completion on 2026-02-28)

- Added runtime event model and bus primitives:
  - `packages/frontend-sdk/src/runtime/sdkEvents.ts`
  - `packages/frontend-sdk/src/runtime/sdkEventBus.ts`
  - `packages/frontend-sdk/src/runtime/sdkRuntime.ts`
- `SdkEvent` now supports known typed events plus extensible generic event objects so new event types can be introduced without changing bus/framework internals.
- `SdkRuntime` is now connection-scoped with `scopeKey` + `bus`, and prepared for backend integration.
- Exported runtime types/classes from `packages/frontend-sdk/src/index.ts`.
- Added tests:
  - `packages/frontend-sdk/src/runtime/__tests__/sdkEventBus.test.ts`
- Verification:
  - `npm test` (from `packages/frontend-sdk`) passes, including the new runtime tests.

## Completion Notes Addendum (added during completion on 2026-02-28)

- Runtime event typing was split to enforce separation of concerns:
  - removed `packages/frontend-sdk/src/runtime/sdkEvents.ts`
  - added generic `packages/frontend-sdk/src/runtime/sdkEvent.ts` (`SdkEvent` only)
- `SdkEventBus` remains in runtime and now uses the generic runtime event type.
- `SdkRuntime` remains connection-scoped, but no longer auto-composes domain middlewares internally; composition moved to runtime factory modules.
