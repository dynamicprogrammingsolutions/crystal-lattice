# SDK Runtime + Event Bus + Resource Invalidation Framework

Build a reusable, connection-scoped framework in `packages/frontend-sdk` that provides:

- **Specific resources** (controllers/stores) with **explicit invalidation rules**.
- A **generic event bus** that anyone can subscribe to.
- A **backend wrapper** that centrally emits mutation events on successful writes.
- A **single-source-of-truth session summary store** to keep session list + chat consistent.

This task also implements two concrete issue sets:

- **(A)** Auto-refresh session UI schema when session plugins / config overrides / agent changes.
- **(B)** Session metadata single source of truth across sessions list and chat, without forcing full reloads.

This work is intended to **supersede** the desktop-only approach in:

- `tasks/20260202-desktop-macos-frontend/089-session-metadata-single-source-of-truth.md`

by moving the core behavior into the SDK (so mobile + desktop + future frontends share the same logic).

## Why this framework (context)

### Existing SDK patterns

- Subscribable external stores are implemented by:
  - `packages/frontend-sdk/src/util/subscribable.ts` (`SimpleSubscribable`)
  - `packages/frontend-sdk-react/src/useSubscribable.ts` (`useSyncExternalStore` binding)

### Existing pain points

1) Session UI schema is cached and does not refetch unless cache is cleared.
   - `SessionUiSchemaController` uses a module-level `CACHE` map keyed by `cacheKey::sessionId`.
   - `load()` returns cached results if present; `invalidate()` must be called manually.
   - Ref: `packages/frontend-sdk/src/uiSchema/sessionUiSchemaController.ts`.

2) Session summary/metadata is not a single source of truth:
   - Sessions list gets rich `SessionSummary` from `GET /sessions`.
   - Chat loads messages via `GET /sessions/{id}/messages` which does **not** currently return the same summary.
   - Frontends pass/lookup session summary via local caches; titles/subtitles can drift.
   - Ref: `tasks/20260202-desktop-macos-frontend/089-session-metadata-single-source-of-truth.md`.

## Subtasks

1. `tasks/20260226-sdk-runtime-event-bus/010-sdk-runtime-and-event-bus.md`
2. `tasks/20260226-sdk-runtime-event-bus/020-evented-backend-wrapper.md`
3. `tasks/20260226-sdk-runtime-event-bus/030-resource-rule-pattern-and-docs.md`
4. `tasks/20260226-sdk-runtime-event-bus/040-issue-A-ui-schema-auto-refresh.md`
5. `tasks/20260226-sdk-runtime-event-bus/050-issue-B-session-summary-single-source-of-truth.md`

## High-level acceptance criteria

- Frontends integrate at **one connection boundary** (create `SdkRuntime`, use `runtime.backend`).
- Resources/controllers may subscribe to the bus and define explicit rules; no global "fan-out" dependency graph.
- UI schema for a session refetches automatically after:
  - plugins change (`PUT/DELETE /sessions/{id}/plugins`)
  - overrides change (`PATCH/DELETE /sessions/{id}/overrides`)
  - agent changes (`PATCH /sessions/{id}/agent`)

- Session summary becomes consistent across sessions list + chat:
  - Sessions list load upserts summaries into SDK store
  - Chat message reload upserts summary (from `GET /sessions/{id}/messages`) into the same store
  - UI can subscribe by sessionId and update without full reload
  - Behavior works for inactive/unmounted views because store lives in runtime

- Tests exist for each layer (bus, backend wrapper emissions, resource invalidation, summary upsert).
- Documentation exists:
  - Create `packages/frontend-sdk/README.md`
  - Update exports/types docs as needed.
