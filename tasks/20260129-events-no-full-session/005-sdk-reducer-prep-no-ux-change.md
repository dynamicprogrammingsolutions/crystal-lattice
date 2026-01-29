# Prep: add SDK message-history reducer skeleton (no UX change)

Parent Task: `tasks/20260129-events-no-full-session/000-main.md`

Add a pure message-history reducer to `@crystal-lattice/frontend-sdk` and wire it into `ChatController` *without changing external behavior yet*.

This is a preparatory refactor that makes later subtasks easier to implement (event contract changes, dirty fallback, removing reloads) and provides an early test point for the new architecture.

## Status

- [ ] Not started

## Goals

- Introduce a single place where “apply event → update message list” lives.
- Keep current user-visible behavior identical:
  - same messages shown
  - same ordering
  - no new reload behavior
  - no new dirty state exposed
- Make follow-up work smaller:
  - Phase 4.5 reducer/dirty work becomes incremental instead of a rewrite.

## Scope (safe refactor only)

### 1) Add reducer module (skeleton)

- Add a new module in the SDK (example path):
  - `packages/frontend-sdk/src/chat/messageHistoryReducer.ts`

Initial reducer supports *only* what the controller already does today, using the same heuristics:

- `final`: append `event.messages` at end
- `tool_results`: append `event.messages` at end
- `message_appended`: append `event.message` at end

Do not add delete/modify handling yet unless it can be proven no behavior changes.

### 2) Wire `ChatController` to use reducer internally

Replace the per-event “append messages” code paths with reducer calls, but preserve outputs.

Targets:

- `packages/frontend-sdk/src/chat/chatController.ts`:
  - replace `applyFinalEvent`, `applyToolResultsEvent`, `applyMessageAppendedEvent` with reducer usage

### 3) Add a “verification point” without UX change

Choose one conservative verification mechanism:

- **Option A (preferred):** in dev builds/logging mode, compute both (old logic) and reducer output and assert equality.
- **Option B:** add a small exported helper function (`debugReduceMessageHistory`) and update a dev-only path in RN debug UI.

Avoid adding new test infrastructure if the repo doesn’t already have it.

## Non-goals

- Do not change event payload shapes.
- Do not add/remove message reloads.
- Do not introduce a `dirty` flag or any user-visible out-of-sync UI.
- Do not change cursor semantics.

## Why this is useful

Once this reducer exists and is used in `ChatController`, later tasks can focus on:

- expanding the reducer to handle `messages_deleted` / `message_modified`
- switching from append-at-end heuristics to index-based application
- adding `dirty` fallback and removing reloads

…without rewriting the controller again.
