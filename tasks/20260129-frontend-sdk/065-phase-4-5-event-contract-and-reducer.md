# Phase 4.5 — Event contract + reducer-driven message state (no full session in events)

Parent Task: `tasks/20260129-frontend-sdk/000-main.md`

Depends On:

- `tasks/20260129-frontend-sdk/050-phase-4-headless-controllers.md`

This phase hardens correctness by making events minimal and reducer-applied.

It is tracked as a standalone task directory because it spans Python + TypeScript SDK + RN UI:

- `tasks/20260129-events-no-full-session/000-main.md`

## Status

- [x] Complete

Notes (implemented via `tasks/20260129-events-no-full-session/000-main.md`):

- Python/HTTP event contract now emits only incremental, index-based events (no embedded full `session`).
- `@crystal-lattice/frontend-sdk` maintains message state via a pure reducer and falls back to reload only when required.
- Mobile UI no longer does unconditional reloads after send/resend or message edits; it relies on events.
- Application action results now distinguish semantic mutations vs explicit UI effects so “updated session” no longer implies “reload now”.

## What this phase does (summary)

- Remove full session payloads from all events.
- Ensure append/modify/delete events include enough information to mutate local session state.
- Add a pure message-history reducer to `@crystal-lattice/frontend-sdk`.
- Add a `dirty` fallback that triggers a manual reload only when incremental apply fails.
- Remove unconditional message reloads from the frontend.

## Implementation notes (what happened vs plan)

- Phase 4.5 was implemented in the standalone task directory (`tasks/20260129-events-no-full-session/`) and then marked complete here for parity with the phase checklist.
- The “no full session in events” requirement forced a strict reducer-based approach; reload/reconcile became a dirty fallback rather than a normal send path.

## Relevant commits

- `eb54c52` Lean events: remove session snapshots; add indices
- `f8603f5` frontend-sdk: add pure reducers and vitest tests
- `33f3f7f` frontend-sdk: typed minimal events and strict history reducer
- `5603124` chat: track dirty + event cursor; mobile remove reloads
- `c78da97` actions: split mutations from ui_effects (no reload on updated)
- `2a44d19` tasks: mark phase 4.5 event contract/reducer complete

## Implemented solutions (high level)

### 1) Minimal event contract (no full session snapshots)

- Event producers no longer embed serialized sessions in event payloads.
- Session/message mutations are communicated via indices:
  - `message_appended`: includes `index` and `message`
  - `message_modified`: includes `index` and `message`
  - `messages_deleted`: includes `indices`
  - `final` / `tool_results`: include `start_index` + `messages`
  - `session_created`: includes `session_id` and optional `agent_id`, `source_session_id`, `fork_upto_index`

### 2) SDK reducer + strict dirty semantics

- Added/updated strict reducer logic in the SDK to apply events by index.
- Missing/mismatched indices mark the session as `dirty`.

### 3) Windowed history + atomic reload + auto-recover

- SDK `ChatController` supports windowed message history (keep last N while preserving global indices).
- Atomic reload (pause polling during reload) and budgeted auto-reload-on-dirty/backfill.

### 4) Mobile no-reload UX

- Mobile chat no longer reloads messages after send/resend/delete/modify.
- On `dirty`, mobile shows a banner with a manual reload button; auto-reload is performed by the SDK budget.

### 5) Application actions: semantic mutations vs UI effects

- `/actions` results now return:
  - `mutations`: `{ created_session_ids, updated_session_ids, deleted_session_ids }`
  - `ui_effects`: `{ navigate_to_session_id, reload_session_ids, reload_sessions_list }`
- The SDK runner emits reload/navigation effects only from `ui_effects`, not from `mutations`.
