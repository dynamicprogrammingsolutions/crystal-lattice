# Integrate reducer into ChatController; add dirty state; fix cursors + persistence

Parent Task: `tasks/20260129-events-no-full-session/000-main.md`

Depends On:

- `tasks/20260129-events-no-full-session/050-sdk-pure-reducer.md`

Update `ChatController` to apply events via the pure reducer, track whether the session is "dirty", and avoid reloads unless necessary.

## Status

- [ ] Not started

## Current controller behavior to change

File: `packages/frontend-sdk/src/chat/chatController.ts`

- It applies several events by appending with `lastIndex + 1` rather than using event-provided indices:
  - `final`: `packages/frontend-sdk/src/chat/chatController.ts:278`
  - `message_appended`: `packages/frontend-sdk/src/chat/chatController.ts:293`
  - `tool_results`: `packages/frontend-sdk/src/chat/chatController.ts:305`

- It does not handle `messages_deleted` or `message_modified` events at all.
- It does not track `dirty`.

## Required controller changes

### A) State extensions

Add fields to `ChatControllerState`:

- `eventsCursorId: string | null` (poll cursor)
- `listCursorEventId: string | null` (from listMessages)
- `dirty: boolean`
- `dirtyReason: string | null`

### B) Cursor semantics (important)

- Poll cursor (`eventsCursorId`) advances to the last processed `event_id` regardless of whether an event was applied.
- If an event cannot be applied, mark `dirty` but still advance cursor to avoid infinite replay.

### C) Apply events via reducer

- For each relevant event, call `reduceMessageHistory(current.messages, event)`.
- Update `messages` accordingly or set dirty.
- Keep streaming state updates (`partial`, `assistant_message`) separate from message-history reducer.

### D) Persistence hooks

Because full reloads are removed, persistence must store the controller-derived snapshot:

- messages
- poll cursor (`eventsCursorId`)
- activeRequestId
- updatedAtMs

### E) Dirty handling policy

- If `dirty === true`, expose a method like `reloadFromServer()` (calls `listMessages()` once) and clears dirty.
- Otherwise, do not trigger reload automatically.

## Work checklist

- [ ] Update controller state shape
- [ ] Integrate reducer
- [ ] Handle `message_modified` and `messages_deleted`
- [ ] Fix cursor semantics split (poll cursor vs list cursor)
- [ ] Add persistence-friendly snapshot getter
