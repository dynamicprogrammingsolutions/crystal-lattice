# Subtask: Resource rule pattern + SDK README

Parent Task: `tasks/20260226-sdk-runtime-event-bus/000-main.md`

Depends On:

- `tasks/20260226-sdk-runtime-event-bus/010-sdk-runtime-and-event-bus.md`
- `tasks/20260226-sdk-runtime-event-bus/020-evented-backend-wrapper.md`

## Description

Define the reusable *pattern* for resources/controllers to subscribe to the bus and implement explicit invalidation rules.

Also create SDK documentation:

- Add `packages/frontend-sdk/README.md` (requested).
- Document the runtime/bus framework and best practices.

This subtask is framework-only; it should not yet implement the concrete Issue Set A or B behaviors (those are in Subtasks 040 and 050).

## Resource rule pattern

### Problem

We want resources to react to mutation events without introducing:

- hidden dependency fan-out
- circular update chains
- "max update depth" loops

### Pattern

Each resource/controller chooses:

1) which event types it cares about
2) which events result in:
   - local cache invalidation
   - a reload (optional, usually when active/enabled)
3) deduping / re-entrancy rules

### Implementation guidance

Add a small helper used by resources:

```ts
export function isEventForSession(ev: SdkEvent, scopeKey: string, sessionId: string): boolean
```

Optionally, add a tiny base class mixin to reduce boilerplate:

```ts
export abstract class BusAwareController<T> extends SimpleSubscribable<T> {
  protected readonly scopeKey: string;
  protected readonly bus: SdkEventBus;
  protected disposeBusSub?: () => void;
  dispose(): void;
}
```

Notes:

- Controllers that subscribe to bus must expose `dispose()` and frontends must call it on unmount (pattern exists already for `ChatController.dispose()`; see `packages/frontend-sdk/src/chat/chatController.ts`).
- If a controller has no long-lived resources (only cache), it may not need subscription; it can rely on runtime-wide shared store instead.

### Dedupe / loop avoidance rules

Require each resource rule to follow:

- Never emit mutation events from inside resource reloads.
  - mutation events must come from evented backend wrapper only.
- Use simple dedupe:
  - if currently loading, set `stale=true` and reload once after completion.
  - track `lastHandledBusSeq` to avoid repeated handling.

## Docs: `packages/frontend-sdk/README.md`

Create a new README describing:

- What `frontend-sdk` provides (controllers, backend clients, runtime)
- `SimpleSubscribable` and React bindings (brief)
- `SdkRuntime` per connection
- Event bus semantics
- Evented backend wrapper (which methods emit)
- Resource rule pattern (how to subscribe + invalidate)

### Required: Document the "data upsert notification" pattern

We want to optionally notify observers when a resource/store has already been updated with fresh data, without introducing fetch loops.

Document this pattern explicitly:

#### Notification-only upsert events (recommended default)

- The **resource/store is the source of truth** (e.g. `SessionSummariesStore`).
- When the store successfully applies an upsert, it may emit an *observational* bus event such as:

  ```ts
  { type: 'session.summary.upserted', scopeKey, sessionId }
  ```

- This event does **not** carry the updated data. Consumers who care must read it from the store:

  - subscribe to the store (preferred)
  - or use `store.get(sessionId)` / `store.getSnapshot()` and react

Rationale:

- avoids duplicating data across bus + store
- avoids large event payloads (especially during bulk upserts)
- avoids circular patterns where event causes fetch which triggers more events

#### Alternative: Payload-carrying upsert events (allowed, targeted only)

If (and only if) a consumer cannot easily access the store, allow an alternative event form that includes a payload:

```ts
{ type: 'session.summary.upserted', scopeKey, sessionId, summary: SessionSummary }
```

Constraints / performance guidance:

- Only use payload events for **targeted single-session updates** (e.g. from chat reload or a single-session refresh).
- Avoid emitting payload events for bulk list loads (`GET /sessions`) if the list can be large.
- If bulk observers are needed, prefer subscribing to the store or emitting a lightweight batch notification (no payload) such as:

  ```ts
  { type: 'session.summary.batchUpserted', scopeKey, sessionIds: string[] }
  ```

This keeps bus overhead bounded.

Also add a short section: "How to add a new dependency":

- Identify mutation source backend method
- Add emission mapping (or wrapper logic)
- In target resource, add rule to handle event
- Add unit test

## Tests

Add tests for helper(s) or base class if introduced.

- Ensure `dispose()` unsubscribes bus listener.

## Acceptance criteria

- Resource rule pattern codified (helper/base class optional but recommended).
- `packages/frontend-sdk/README.md` created and linked from repo root docs if appropriate.
- Tests for framework utilities.

## Execution Plan (added during completion on 2026-02-28)

1. Add `packages/frontend-sdk/src/runtime/resourceRules.ts` to codify the rule pattern with:
   - `isEventForSession(ev, scopeKey, sessionId)` helper
   - `BusAwareController<T>` base class for bus subscription lifecycle + disposal.
2. Implement lightweight dedupe support in `BusAwareController` (`lastHandledBusSeq`) so resource handlers can ignore already-processed bus snapshots.
3. Add tests in `packages/frontend-sdk/src/runtime/__tests__/resourceRules.test.ts` for:
   - scope/session matching helper behavior
   - `dispose()` unsubscribes bus listeners
   - dedupe behavior by bus sequence.
4. Create `packages/frontend-sdk/README.md` documenting:
   - runtime-per-connection model
   - push-only event bus semantics
   - evented backend mutation mapping
   - resource invalidation/reload rule pattern
   - required "data upsert notification" guidance including notification-only and payload-carrying variants.
5. Export new resource-rule utilities from `packages/frontend-sdk/src/index.ts`.

## Completion Notes (added during completion on 2026-02-28)

- Added resource-rule utilities:
  - `packages/frontend-sdk/src/runtime/resourceRules.ts`
  - `isEventForSession(ev, scopeKey, sessionId)`
  - `BusAwareController<T>` with bus lifecycle management, sequence-based dedupe guard, and `dispose()` unsubscribe.
- Exported utilities from `packages/frontend-sdk/src/index.ts`.
- Added tests:
  - `packages/frontend-sdk/src/runtime/__tests__/resourceRules.test.ts`
  - Covers scope/session filtering, no replay of old events after subscribe, and bus unsubscribe on dispose.
- Created SDK docs file:
  - `packages/frontend-sdk/README.md`
  - Includes runtime-per-connection, push-only bus semantics, backend emission mapping, middleware-based extension model, resource-rule guidance, and required data-upsert notification pattern.
- Verification:
  - `npm test` (from `packages/frontend-sdk`) passes with new resource-rule tests.

## Completion Notes Addendum (added during completion on 2026-02-28)

- Runtime resource utility was split to keep runtime generic:
  - removed `packages/frontend-sdk/src/runtime/resourceRules.ts`
  - added generic `packages/frontend-sdk/src/runtime/busAwareController.ts`
- Session-scoped rule helper moved into domain module:
  - `packages/frontend-sdk/src/sessionMutations/sessionMutationRules.ts` (`isEventForSession`)
- Tests were reorganized by concern:
  - added `packages/frontend-sdk/src/runtime/__tests__/busAwareController.test.ts`
  - added `packages/frontend-sdk/src/sessionMutations/__tests__/sessionMutationRules.test.ts`
  - removed `packages/frontend-sdk/src/runtime/__tests__/resourceRules.test.ts`
- SDK README updated to document runtime/domain/factory separation and default-vs-custom runtime composition.
