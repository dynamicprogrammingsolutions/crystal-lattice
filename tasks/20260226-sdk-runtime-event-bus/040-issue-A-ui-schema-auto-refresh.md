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
