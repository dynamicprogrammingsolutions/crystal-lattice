# Frontend SDK

Connection-scoped frontend primitives for Crystal Lattice clients.

This package provides:

- backend clients (`RestAgentBackend`, bridge transport support)
- subscribable controllers/stores (`SimpleSubscribable` based)
- generic runtime infrastructure (`SdkRuntime`, `SdkEventBus`, backend middleware pipeline)
- domain modules that define event contracts and middleware composition

The runtime/event-bus layer is intentionally push-only and explicit: resources choose what to react to.

## Runtime Per Connection

Create one runtime per active connection:

```ts
import { RestAgentBackend, createDefaultSdkRuntime } from '@crystal-lattice/frontend-sdk';

const rawBackend = new RestAgentBackend({ transport });
const runtime = createDefaultSdkRuntime({
  scopeKey: connectionId,
  backend: rawBackend,
});
```

`createDefaultSdkRuntime(...)` composes SDK-provided domain middlewares (currently session mutation middlewares).

If you want full control, instantiate `SdkRuntime` directly with your own `backendMiddlewares` list.

Runtime fields:

- `runtime.scopeKey`: connection identity used by events.
- `runtime.bus`: generic SDK event bus.
- `runtime.backend`: evented backend wrapper (preferred for app code).
- `runtime.rawBackend`: original backend (escape hatch/debug).

## Subscribables

`SimpleSubscribable<T>` is the SDK store primitive:

- synchronous `getSnapshot()`
- `subscribe(listener)` with unsubscribe callback

React bindings are in `@crystal-lattice/frontend-sdk-react` via `useSyncExternalStore`.

## React Runtime Context

`@crystal-lattice/frontend-sdk-react` uses runtime context for controller hooks.

Wrap each connection subtree:

```tsx
import {
  ApplicationPluginsProvider,
  SdkRuntimeProvider,
} from '@crystal-lattice/frontend-sdk-react';

<SdkRuntimeProvider runtime={runtime}>
  <ApplicationPluginsProvider>
    {/* screens/components using frontend-sdk-react hooks */}
  </ApplicationPluginsProvider>
</SdkRuntimeProvider>
```

Notes:

- In single-connection apps, one provider near app root is enough.
- In multi-connection apps (desktop tabs/windows), use one provider per connection subtree.
- Hooks such as `useChatController`, `useSessionsController`, `useAgentsController`, `useSessionUiSchemaController`, and `useSessionPluginsController` read backend/scopeKey from this context.

## Event Bus Semantics

`SdkEventBus` stores a minimal snapshot:

- `seq`: monotonic sequence number
- `lastEvent`: most recently emitted event

The bus is notification-only. It is not a dependency graph and does not trigger automatic fan-out.

Resources/controllers should subscribe explicitly and decide whether to invalidate, reload, or ignore.

## Evented Backend Wrapper

`createEventedBackend` is generic runtime infrastructure. It does not know about session/plugin/override semantics.

The wrapper is middleware-driven. Core framework code is generic and does not hardcode per-event branching.

Generic extension point:

- add `BackendMiddleware` for lifecycle hooks (`before`, `after success`, `after error`, `finally`)
- add domain-specific middleware modules outside `runtime/`

Emission rules:

- emit only after awaited call succeeds
- do not emit on errors

### Runtime vs Domain Separation

- `src/runtime/*`: only generic bus/runtime/backend middleware primitives
- `src/sessionMutations/*`: session mutation event types, rules, and middleware mappings
- `src/runtimeFactory/*`: default runtime composition factory

### Extending With Middleware

Use backend middleware for full lifecycle control (`before`, `after success`, `after error`, `finally`).

```ts
import {
  SdkRuntime,
  type BackendMiddleware,
  createDefaultBackendMiddlewares,
} from '@crystal-lattice/frontend-sdk';

const lifecycleMiddleware: BackendMiddleware = async (ctx, next) => {
  ctx.bus.emit({
    type: 'backend.call.before',
    scopeKey: ctx.scopeKey,
    method: ctx.method,
  });

  try {
    const result = await next();
    ctx.bus.emit({
      type: 'backend.call.success',
      scopeKey: ctx.scopeKey,
      method: ctx.method,
    });
    return result;
  } catch (error) {
    ctx.bus.emit({
      type: 'backend.call.error',
      scopeKey: ctx.scopeKey,
      method: ctx.method,
      message: error instanceof Error ? error.message : 'Unknown error',
    });
    throw error;
  } finally {
    ctx.bus.emit({
      type: 'backend.call.finally',
      scopeKey: ctx.scopeKey,
      method: ctx.method,
    });
  }
};

const runtime = new SdkRuntime({
  scopeKey: connectionId,
  backend: rawBackend,
  backendMiddlewares: createDefaultBackendMiddlewares({
    extraBackendMiddlewares: [lifecycleMiddleware],
  }),
});
```

### Session Mutation Module

Session-specific helpers are in `sessionMutations`:

- `SESSION_MUTATION_EVENT_TYPES`
- `createSessionScopedSuccessEventMiddleware(...)`
- `createDefaultSessionMutationMiddlewares()`
- `isEventForSession(...)`

### Session UI Schema Auto-Refresh

`SessionUiSchemaController` can listen to runtime bus events and auto-refresh when session-level mutation calls succeed.

Invalidation events:

- `session.plugins.changed`
- `session.overrides.changed`
- `session.agent.changed`

Recommended wiring is through runtime:

```ts
import { SessionUiSchemaController } from '@crystal-lattice/frontend-sdk';

const controller = new SessionUiSchemaController({
  backend: runtime.backend,
  cacheKey: runtime.scopeKey,
  scopeKey: runtime.scopeKey,
  sessionId,
  bus: runtime.bus,
  enabled: true,
});
```

In `@crystal-lattice/frontend-sdk-react`, use `useSessionUiSchemaController(...)` inside `SdkRuntimeProvider`.

With runtime context, the hook call is minimal:

```ts
const { state } = useSessionUiSchemaController({
  sessionId,
  enabled: true,
});
```

## Resource Rule Pattern

Recommended pattern for SDK resources/controllers:

1. Subscribe to `runtime.bus`.
2. Filter events by explicit rules (scope + entity, e.g. session id).
3. Invalidate local cache state.
4. Reload only when active/enabled.
5. Deduplicate by bus sequence and avoid re-entrant reload loops.

Utilities:

- `isEventForSession(ev, scopeKey, sessionId)` from `sessionMutations/sessionMutationRules`
- `BusAwareController<T>` base class with bus lifecycle/dispose support

### Building Bus-Aware Controllers

For most controllers, bus listening should be a small amount of code by extending `BusAwareController<T>`.

```ts
import { BusAwareController, type SdkEvent, type SdkEventBus } from '@crystal-lattice/frontend-sdk';

interface ExampleState {
  loading: boolean;
  value: string | null;
}

class ExampleController extends BusAwareController<ExampleState> {
  constructor(options: { scopeKey: string; bus?: SdkEventBus | null }) {
    super({
      initialSnapshot: { loading: false, value: null },
      scopeKey: options.scopeKey,
      bus: options.bus,
    });

    this.subscribeToBus((event) => {
      if (!this.shouldHandleEvent(event)) {
        return;
      }
      void this.reload();
    });
  }

  private shouldHandleEvent(event: SdkEvent): boolean {
    return event.scopeKey === this.scopeKey && event.type === 'example.changed';
  }

  async reload(): Promise<void> {
    // fetch/update snapshot
  }
}
```

Recommended controller checklist:

- Keep event filtering explicit (`scopeKey`, entity id, and event type).
- Keep backend writes and bus emission in backend middleware, not in controller reload code.
- Add a small coalescing guard (`inFlight` + `needsReload`) only if reload can overlap.
- Expose/retain `dispose()` so React hooks can unsubscribe on unmount.

In React hooks, always clean up:

```ts
useEffect(() => {
  return () => controller?.dispose();
}, [controller]);
```

Loop-avoidance rules:

- mutation events come from backend wrapper only
- resource reloads must not emit mutation events
- when needed, coalesce in-flight reloads with a simple `stale` flag and one follow-up reload

## Data Upsert Notification Pattern

When a store has already applied fresh data, it may emit an observational event.

### Notification-only upsert events (default)

- The store is the source of truth.
- Event is lightweight notification:

```ts
{ type: 'session.summary.upserted', scopeKey, sessionId }
```

- Consumers read data from the store (`subscribe`, `get`, `getSnapshot`).

Why default to this pattern:

- avoids duplicating state across store + event payload
- keeps bus events small
- avoids circular fetch/event cascades

### Payload-carrying upsert events (allowed, targeted only)

If a consumer cannot reasonably read from the store, payload events are allowed for targeted single-item updates:

```ts
{ type: 'session.summary.upserted', scopeKey, sessionId, summary }
```

Constraints:

- use for targeted single-session updates only
- avoid payload emission for bulk list upserts
- for bulk notifications, prefer store subscription or a lightweight batch notification without payload

## Adding New Dependencies

When wiring a new invalidation dependency:

1. Identify the backend mutation method(s).
2. Add domain middleware mapping in the appropriate domain module (not in `runtime/`).
3. Add explicit handling rules in the dependent resource/controller.
4. Add unit tests for both emission and resource reaction behavior.
