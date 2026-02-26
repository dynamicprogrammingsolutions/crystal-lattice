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
