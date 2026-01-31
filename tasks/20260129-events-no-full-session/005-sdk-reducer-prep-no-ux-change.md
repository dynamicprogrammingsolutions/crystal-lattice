# Prep: add SDK reducers (message history + streaming state) + tests

Parent Task: `tasks/20260129-events-no-full-session/000-main.md`

Add pure reducers to `@crystal-lattice/frontend-sdk` and wire them into `ChatController` so later subtasks can expand event handling (delete/modify/dirty) without rewriting controller logic.

This is a preparatory refactor that makes later subtasks easier to implement (event contract changes, dirty fallback, removing reloads) and provides an early test point for the new architecture.

## Status

- [x] Completed

## Goals

- Introduce a single place where “apply event → update state” lives.
- Keep behavior broadly consistent while accepting that some events are still ignored (delete/modify/dirty comes later).
- Make follow-up work smaller by moving per-event logic out of `ChatController`.

## Implemented

### 1) Add pure reducer modules

- `packages/frontend-sdk/src/chat/messageHistoryReducer.ts`
  - `reduceMessageHistory(messages, event) -> messages`
  - Handles `final`, `tool_results`, and `message_appended` (append-only, index-based via last known index)

- `packages/frontend-sdk/src/chat/streamingStateReducer.ts`
  - `reduceStreamingState(state, event) -> state`
  - Handles `request_started`, `assistant_message` (start), `partial`, `final` (clears streamingRow), `error`, `request_completed`/`request_cancelled`

Both reducers accept all events and no-op for unhandled types.

### 2) Wire `ChatController` to use reducers

`packages/frontend-sdk/src/chat/chatController.ts`

- `applyEvents()` now applies every event through both reducers:
  - `messages = reduceMessageHistory(messages, ev)`
  - `{streamingRow, activeRequestId, requestError} = reduceStreamingState(..., ev)`
- Removed the previous per-event imperative helpers (`applyFinalEvent`, `applyToolResultsEvent`, etc.)

### 3) Add tests (Vitest)

- Added Vitest harness for the SDK:
  - `packages/frontend-sdk/vitest.config.ts`
  - `packages/frontend-sdk/package.json` scripts: `test`, `test:watch`
- Added reducer tests (stable invariants; avoids brittle snapshots):
  - `packages/frontend-sdk/src/chat/__tests__/messageHistoryReducer.test.ts`
  - `packages/frontend-sdk/src/chat/__tests__/streamingStateReducer.test.ts`
  - `packages/frontend-sdk/src/chat/__tests__/reducers.integration.test.ts`

## Non-goals (still)

- Do not change event payload shapes.
- Do not add `dirty` semantics yet.
- Do not add delete/modify history handling yet.

## Why this is useful

Once this reducer exists and is used in `ChatController`, later tasks can focus on:

- expanding the reducer to handle `messages_deleted` / `message_modified`
- switching from append-at-end heuristics to index-based application
- adding `dirty` fallback and removing reloads

…without rewriting the controller again.

## How to verify

- Run tests: `npm -w @crystal-lattice/frontend-sdk test`
