# Subtask: Session metadata single source of truth (list + messages)

Unify the “session metadata” used by the sessions list and the per-session chat tab so that:

- Session list has a metadata object per session.
- Individual session views also receive the same metadata.
- Both `GET /sessions` and `GET /sessions/{id}/messages` expose the same session summary metadata format.
- Desktop tabs/chat header derive title/subtitle from this metadata (shared code), and automatically update when either the sessions list or the session view is refetched.

This supersedes the temporary subtitle plumbing added in `081`.

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/070-desktop-sessions-pane.md`
- `tasks/20260202-desktop-macos-frontend/080-desktop-chat-tabs-and-chat-pane.md`

## Status

- [ ] Not started

## Current status (what exists today)

### Server

- `GET /sessions` already returns a rich per-session “summary” object:
  - base fields: `session_id`, `modified`, `preview`, `metadata` (strips `native_messages`), and `pinned`
  - plus optional plugin-derived computed fields via application actions triggered on `session_list`
  - Implementation: `application/python/agent_terminal_app/server.py` (`@app.get("/sessions")`).

- `GET /sessions/{session_id}/messages` currently returns only:
  - `messages`, `cursor_event_id`, `active_request_id`
  - Implementation: `application/python/agent_terminal_app/server.py` (`@app.get("/sessions/{session_id}/messages")`).

### Frontend SDK

- `SessionSummary` exists (`packages/frontend-sdk/src/types/sessions.ts`) and is used by `listSessions()`.
- `listMessages()` returns `ListMessagesResult` which does not include session metadata today (`packages/frontend-sdk/src/backend/backend.ts`).
- `ChatController.reloadMessages()` only updates message history + cursors; it has no place to store session summary metadata (`packages/frontend-sdk/src/chat/chatController.ts`).

### Desktop app

- Sessions list renders title/subtitle using `deriveSessionListPresentationFromGroups(...)` (shared SDK function).
- Chat tabs store `title` in local tab state at open time; it can drift from updated session list data.
- Temporary drift reduction: `081` passes subtitle and pushes list-derived presentation into open tabs, but it is not a true single source of truth.

## Goal state (deliverables)

### 1) Server: include session summary in messages response

Add a `session` field to the response of:

- `GET /sessions/{session_id}/messages`

Response shape (additive):

```json
{
  "session": { "session_id": "...", "modified": 0, "preview": "...", "metadata": { }, "pinned": false, "...": "plugin fields" },
  "messages": [ ... ],
  "cursor_event_id": "...",
  "active_request_id": "..."
}
```

Implementation guidance:

- Factor out a helper in `application/python/agent_terminal_app/server.py` that builds the same per-session summary object used by `GET /sessions`.
- Reuse the existing `SessionListCache` so both endpoints share cached summaries.
- Ensure the same “trigger actions” used by `GET /sessions` are applied when building the `session` object for messages.

### 2) Frontend SDK: plumb session summary through `listMessages`

- Extend `ListMessagesResult` in `packages/frontend-sdk/src/backend/backend.ts` with `session?: SessionSummary`.
- Update `packages/frontend-sdk/src/backend/restBackend.ts` to parse and return the `session` field.
- Update the session summary typing to tolerate plugin-added computed fields:
  - either widen `SessionSummary` with an index signature (`[key: string]: any`), or introduce a dedicated “session record” type used by list/messages.

### 3) SDK ChatController: store the session summary

- Add `sessionSummary: SessionSummary | null` to `ChatControllerState`.
- In `ChatController.reloadMessages()`, when `backend.listMessages()` returns a session summary, store it on the snapshot.

Rationale: chat panes should be able to derive title/subtitle without relying on out-of-band props.

### 4) Desktop: unify cache + update tabs by session id

Add a desktop-level “session summary index” keyed by `(connectionId, sessionId)` and keep it updated from both sources:

- Source A: sessions list refresh (`GET /sessions`)
- Source B: per-session messages refresh (`GET /sessions/{id}/messages`)

Implementation guidance:

- Extend `desktop/crystal-lattice-control-desktop-rn/src/cache/useSessionsCache.ts` with an `upsertSessionSummary(connectionId, summary)` API.
- When `SessionsPanel` loads sessions, continue to store the list, but also ensure that open tabs can subscribe to changes by session id.
- When a `ChatPane` loads messages and receives `chatState.sessionSummary`, call `upsertSessionSummary`.
- Update tab title/subtitle rendering to derive from cached session summary using the shared SDK function:
  - `packages/frontend-sdk/src/sessions/sessionListPresentation.ts` (`deriveSessionListPresentationFromGroups`)

### 5) Ensure plugin-driven title/subtitle fields are available

Title/subtitle derivation depends on `sessionListFields` (plugin-provided). Options:

- Wrap chat panes (tab content) in `ApplicationPluginsProvider` and read `sessionListFields` in the chat header/tab strip.
- Or lift plugin field state up to `DesktopRoot` per connection and pass down.

Prefer the first approach to align with `086` (plugin actions in chat) and keep connection-scoped plugin state consistent.

## Verification

- Open a session tab; verify title/subtitle come from session summary metadata.
- Refresh sessions list; verify open tab titles/subtitles update without manually reopening.
- Reload messages in an open tab; verify it updates session summary cache and the sessions list view stays consistent.
- Confirm plugin-provided fields affect both list and chat header consistently.
