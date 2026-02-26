# Subtask: Issue Set B — Session summary/metadata single source of truth (list + chat)

Parent Task: `tasks/20260226-sdk-runtime-event-bus/000-main.md`

Depends On:

- `tasks/20260226-sdk-runtime-event-bus/010-sdk-runtime-and-event-bus.md`
- `tasks/20260226-sdk-runtime-event-bus/020-evented-backend-wrapper.md`
- `tasks/20260226-sdk-runtime-event-bus/030-resource-rule-pattern-and-docs.md`

## Description

Implement a connection-scoped SDK resource that provides a single source of truth for per-session summary/metadata, keeping sessions list and chat views consistent.

Requirements:

- Session list reload updates chat title/subtitle (and any other session-field UI).
- Chat reload updates the session list (only the affected sessionId; no forced full list reload).
- Changes should apply even to cached/inactive views because the store lives at connection/runtime scope.

This subtask incorporates the concrete changes listed in:

- `tasks/20260202-desktop-macos-frontend/089-session-metadata-single-source-of-truth.md`

but implements them in the SDK so desktop/mobile can share it.

## Existing code references

### Server endpoints

In `application/python/agent_terminal_app/server.py`:

- `GET /sessions` returns rich session summaries (with metadata + plugin-derived computed fields).
- `GET /sessions/{session_id}/messages` currently returns only messages + cursors (no session summary).

Ref: `tasks/20260202-desktop-macos-frontend/089-session-metadata-single-source-of-truth.md`.

### SDK

- `SessionSummary` type: `packages/frontend-sdk/src/types/sessions.ts`
- `listSessions()` returns `SessionSummary[]`.
- `listMessages()` returns `ListMessagesResult` which currently has:
  - `messages`, `cursorEventId`, `activeRequestId`
  - no session summary.
  Ref: `packages/frontend-sdk/src/backend/backend.ts`.

### ChatController

- `ChatControllerState` does not include session summary today.
- `reloadMessages()` has no way to update summary.
  Ref: `packages/frontend-sdk/src/chat/chatController.ts`.

## Implementation plan

### 1) Server: include session summary in messages response (from task 089)

Update `GET /sessions/{session_id}/messages` to also return:

```json
{
  "session": { ...same shape as entries in GET /sessions... },
  "messages": [...],
  "cursor_event_id": "...",
  "active_request_id": "..."
}
```

Implementation notes (from 089):

- Factor out helper that builds the per-session summary object, shared by `/sessions` and `/sessions/{id}/messages`.
- Ensure plugin-derived computed fields are applied consistently (same triggers as list).

### 2) SDK backend plumbing: `listMessages()` returns `session?: SessionSummary`

In `packages/frontend-sdk/src/backend/backend.ts`:

- Extend `ListMessagesResult` with `session?: SessionSummary`.

In `packages/frontend-sdk/src/backend/restBackend.ts`:

- Parse `session` field if present.

### 3) ChatController: store session summary

In `packages/frontend-sdk/src/chat/chatController.ts`:

- Add `sessionSummary: SessionSummary | null` to `ChatControllerState`.
- In `reloadMessages()`, if `listMessages()` returns `session`, set it on snapshot.

### 4) SDK resource: SessionSummariesStore (connection-scoped)

Add a new resource under `packages/frontend-sdk/src/sessions/`:

- `sessionSummariesStore.ts`

Shape:

- `SessionSummariesStore` extends `SimpleSubscribable<...>`
- Snapshot includes:
  - `byId: Record<string, SessionSummary>`
  - optional `updatedAtMs` or per-id timestamps

Methods:

- `upsertMany(list: SessionSummary[])`
- `upsertOne(summary: SessionSummary)`
- `get(sessionId: string): SessionSummary | null`

Store should optionally emit a bus event `session.summary.upserted` (non-mutation) for observers. Do not have any resources auto-refetch based on this event.

Required semantics (see Subtask 030 for README requirements):

- Default: emit notification-only event `{ type: 'session.summary.upserted', scopeKey, sessionId }` and keep the data only in the store.
- Optional alternative (targeted only): allow emitting a payload-carrying variant for single-session updates (e.g. chat reload), but avoid payload emission for bulk list loads.

### 5) Wire store updates from both sources

#### Sessions list path

Update `SessionsController.load()` (`packages/frontend-sdk/src/sessions/sessionsController.ts`) to upsert loaded sessions into the runtime store (if using runtime) or expose an integration point.

Design options:

- Preferred: `SessionsController` constructed with runtime (or store instance).
- Minimal: runtime provides a helper `runtime.sessionSummaries.upsertMany(...)` and frontends call it after load.

Goal for reusability is the preferred option: SDK controller does it automatically.

#### Chat path

When `ChatController.reloadMessages()` sets `sessionSummary`, also upsert into runtime store.

### 6) Frontend bindings

Add to `frontend-sdk-react`:

- `useSessionSummariesStore(runtime)` or `useSessionSummary(runtime, sessionId)`.

Update desktop/mobile chat header/tab title logic to prefer store-derived summary.

Notes:

- Existing shared rendering helper `deriveSessionListPresentationFromGroups(...)` is in SDK:
  - `packages/frontend-sdk/src/sessions/sessionListPresentation.ts`

So both list and chat should derive title/subtitle from the same `SessionSummary` object using the same function.

### 7) Optional: targeted refresh for "dirty" summary

If there are mutations that change summary but do not naturally go through `GET /sessions/{id}/messages` soon, add:

- `GET /sessions/{id}/summary` (or `GET /sessions/{id}`) to refresh one summary cheaply.

Then resources can choose to refresh summary for a sessionId on specific bus mutation events.

This is optional for initial rollout; the core win comes from plumbing summary through messages response.

## Tests

### Server

- Add a server test (if present test harness exists) verifying `/sessions/{id}/messages` includes `session` with expected shape.

### SDK

1) `restBackend.listMessages` parsing test:
   - mock transport returning `{ session: {...}, messages: [...] }`
   - verify `ListMessagesResult.session` populated.

2) `ChatController` state update test:
   - mock backend.listMessages returning `{ session: {...}, messages: [...] }`
   - after `loadMessages`, verify `controller.getSnapshot().sessionSummary`.

3) `SessionSummariesStore` tests:
   - `upsertMany` and `upsertOne` update byId
   - subscribers notified once per call

4) Integration test (SDK-only):
   - sessions list load upserts store
   - chat load upserts same store and updates one session
   - verify store has latest values for that id

## Docs

Update `packages/frontend-sdk/README.md`:

- Document SessionSummariesStore, how list + chat keep it updated.
- Document recommended frontend usage:
  - list renders from sessions controller
  - chat header/tab renders from store by sessionId

Also update/supersede the desktop task:

- Add a note to `tasks/20260202-desktop-macos-frontend/089-session-metadata-single-source-of-truth.md` that the SDK implementation supersedes it (or link to this task directory).

## Acceptance criteria

- `GET /sessions/{id}/messages` includes `session` summary.
- SDK plumbs summary through `listMessages` and stores it on `ChatControllerState`.
- Runtime-level SessionSummariesStore exists and is updated from both sessions list and chat reload.
- Desktop/mobile can render consistent titles/subtitles without drift.
- Tests cover plumbing + store behavior.
