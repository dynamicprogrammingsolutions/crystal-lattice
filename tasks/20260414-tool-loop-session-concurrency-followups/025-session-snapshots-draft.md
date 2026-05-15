# Session Snapshots Draft

Draft a first-class snapshot design for session history so destructive edits and conflict backups can be stored, browsed, restored, and kept read-only without overloading the normal live session model.

Parent Task: tasks/20260414-tool-loop-session-concurrency-followups/000-main.md
Depends On: tasks/20260414-tool-loop-session-concurrency-followups/010-tool-loop-session-settings-concurrency.md

## Requirements checklist

- [ ] Define a first-class snapshot store format and API in the application layer.
- [ ] Keep snapshot loading and browsing as close as possible to existing read-only session flows.
- [ ] Keep snapshots read-only at low-level write/send gates, not only in the frontend.
- [ ] Support snapshot creation, listing, loading, deletion, and restore.
- [ ] Ensure restore automatically snapshots the replaced live session when there is meaningful difference.
- [ ] Identify which destructive actions should automatically create snapshots.
- [ ] Keep this task draft-level so the design can still evolve before implementation.

## Problem statement

The current reconciliation path can save a backup file when a conflict is detected, but that backup is ad hoc and not part of a discoverable session history model.

What is missing:

- no first-class way to list backups/snapshots for a session
- no standard metadata such as timestamp and creation reason
- no readonly browsing flow
- no built-in restore operation
- no automatic snapshot policy for common destructive actions

The follow-up goal is to turn backups into a supported snapshot feature.

## Current code shape

### Session persistence

- Sessions are stored as one JSON file per session in `core/python/agent_app/sessions.py`.
- `FilesystemSessionStore` currently supports:
  - `load(session_id)`
  - `save(session)`
  - `delete(session_id)`
  - `get_file_state(session_id)`
  - `save_backup(session, request_id=..., suffix=...)`
- `save_backup(...)` already proves the store can write session-like sidecar files without affecting the main live session file.

### Application layer

- `AgentApplication` exposes live session operations in `core/python/agent_app/application_future.py`:
  - `load_session(...)`
  - `load_session_record(...)`
  - `save_session(...)`
  - `delete_session(...)`
  - `send_request(...)`
- Recent reconciliation work already added:
  - strict save-time/session-start conflict detection
  - shared conflict backup creation
  - explicit file-state helpers

This means snapshots can build on an already-centralized persistence layer rather than being bolted onto plugins individually.

### Server and frontend coupling

The current server and frontend are strongly keyed by `session_id`:

- session list: `GET /sessions`
- read-only message load: `GET /sessions/{session_id}/messages`
- settings/config/plugins reads:
  - `GET /sessions/{session_id}/overrides`
  - `GET /sessions/{session_id}/config/base`
  - `GET /sessions/{session_id}/config/schema`
  - `GET /sessions/{session_id}/plugins`
  - `GET /sessions/{session_id}/ui-schema`
  - `GET /sessions/{session_id}/application/ui-schema`
- events polling filters by `session_id`
- frontend cache keys and navigation also use `session_id`

This matters because any design that overloads snapshot identity into `session_id` will ripple through many places, not only the snapshot viewer.

## Findings from investigation

### 1. Snapshot files must not leak into the normal session list

Both terminal and server session lists scan `*.json` in the session root:

- `application/python/agent_terminal_app/terminal_app.py`
- `application/python/agent_terminal_app/server.py`

If snapshots live beside sessions as JSON files, the list code must explicitly filter them out.

### 2. Encoding snapshot identity into `session_id` is possible but costly

The transport layer simply URL-encodes session ids, so a composite id could work mechanically.

However, that composite form would also affect:

- event polling and session filtering
- request recovery and active request tracking
- frontend caches
- navigation state
- asset/session attachment paths

That makes it a risky primary backend model.

### 3. Read-only endpoint reuse is attractive

The user’s suggestion is good: for read-only endpoints, adding `snapshot_id` as a query param is likely simpler than duplicating endpoints.

Good candidates:

- `GET /sessions/{session_id}/messages?snapshot_id=...`
- `GET /sessions/{session_id}/overrides?snapshot_id=...`
- `GET /sessions/{session_id}/config/base?snapshot_id=...`
- `GET /sessions/{session_id}/config/schema?snapshot_id=...`
- `GET /sessions/{session_id}/plugins?snapshot_id=...`
- `GET /sessions/{session_id}/ui-schema?snapshot_id=...`
- `GET /sessions/{session_id}/application/ui-schema?snapshot_id=...`

This preserves much of the existing frontend/backend read path while keeping writes gated.

### 4. Read-only gating must happen at the lowest reasonable layer

The following should reject snapshot targets, even if a frontend forgets:

- `save_session(...)`
- `send_request(...)`
- append/modify/delete message flows
- mutating actions and session actions

### 5. Mobile built-in session actions are a natural UI entry point

Mobile already has built-in session actions outside the plugin action system:

- `packages/frontend-rn-components/src/sessionActions.ts`
- `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`

This is a good place to add:

- `Snapshots`
- `Restore snapshot`
- `Delete snapshot`

without forcing the feature through application plugins just for placement.

## Draft design

### 1. Make snapshots first-class in the session store

Add snapshot support to `FilesystemSessionStore`.

Suggested file pattern:

- `<session_id>.snapshot.<timestamp>.<snapshot_id>.json`

Suggested stored payload:

```json
{
  "snapshot": {
    "snapshot_id": "snap_...",
    "session_id": "session-123",
    "created_at": "2026-04-14T12:34:56Z",
    "reason": "compaction",
    "metadata": {
      "request_id": "req_...",
      "source_action": "compact_range"
    }
  },
  "session": { "... exported session ..." }
}
```

Suggested store methods:

- `create_snapshot(session, *, reason, metadata=None) -> SessionSnapshotRecord`
- `list_snapshots(session_id) -> list[SessionSnapshotRecord]`
- `load_snapshot(session_id, snapshot_id) -> Session`
- `delete_snapshot(session_id, snapshot_id) -> bool`

Suggested snapshot record fields:

- `snapshot_id`
- `session_id`
- `created_at`
- `reason`
- `metadata`
- maybe `path`

### 2. Keep explicit snapshot ids in the backend model

Recommended backend model:

- live session id remains unchanged
- snapshot identity is separate
- snapshot APIs take `(session_id, snapshot_id)`

Why:

- keeps persistence and event semantics clean
- avoids spreading composite-id parsing into unrelated code
- still allows the frontend to build a session-like snapshot viewer if useful

### 3. Reuse read-only session endpoints via query param

Instead of duplicating read-only endpoints, extend existing reads with an optional query parameter:

- `snapshot_id`

Proposed rule:

- when `snapshot_id` is omitted, current live session behavior stays unchanged
- when `snapshot_id` is present, the endpoint loads the snapshot session instead of the live one

Likely first wave:

- `GET /sessions/{session_id}/messages?snapshot_id=...`
- `GET /sessions/{session_id}/overrides?snapshot_id=...`
- `GET /sessions/{session_id}/config/base?snapshot_id=...`
- `GET /sessions/{session_id}/config/schema?snapshot_id=...`
- `GET /sessions/{session_id}/plugins?snapshot_id=...`
- `GET /sessions/{session_id}/ui-schema?snapshot_id=...`
- `GET /sessions/{session_id}/application/ui-schema?snapshot_id=...`

This should let the frontend reuse most current readonly data-loading flows.

### 4. Add explicit snapshot management endpoints

Separate endpoints still make sense for snapshot management itself:

- `GET /sessions/{session_id}/snapshots`
- `POST /sessions/{session_id}/snapshots`
- `DELETE /sessions/{session_id}/snapshots/{snapshot_id}`
- `POST /sessions/{session_id}/snapshots/{snapshot_id}/restore`

Possible response for listing:

```json
{
  "snapshots": [
    {
      "snapshot_id": "snap_1",
      "created_at": "2026-04-14T12:34:56Z",
      "reason": "delete range"
    }
  ]
}
```

### 5. Restore should snapshot the replaced live session first

`restore_snapshot(session_id, snapshot_id)` should:

1. load the current live session
2. load the requested snapshot session
3. compare whether they differ meaningfully
4. if yes, create a new snapshot of the current live session before replacing it
5. save the restored content back to the live session id

Reason:

- restore should not destroy the currently live state without giving it an undo point

Suggested snapshot reasons:

- restored live preimage: `before restore`
- explicit/manual snapshot: `manual`

### 6. Only meaningful differences should create restore-preimage snapshots

Avoid creating redundant snapshots when the live session already matches the snapshot.

Suggested comparison:

- same `session_id`
- same messages
- same metadata

No need to create a pre-restore snapshot when there is no meaningful change.

### 7. Gate writes at low level for snapshot targets

Snapshots are readonly by design.

Recommended low-level rule:

- any attempt to treat a snapshot as a writable session should fail with a clear error

This should apply to:

- app-layer save/send helpers
- mutating server endpoints
- session/plugin/action mutations

Even if read-only endpoints reuse existing code with `snapshot_id`, mutating endpoints should not accept `snapshot_id` in phase 1 unless there is a carefully defined semantics. Simpler is:

- read-only endpoints may accept `snapshot_id`
- write endpoints ignore or reject `snapshot_id`
- restore/delete/create have dedicated snapshot operations

### 8. Automatically snapshot destructive operations

Likely first wave of auto-snapshotting:

- summarize range
- gemini compaction
- provider-extension session actions that rewrite history
- delete message range

Possible later additions:

- agent switch
- plugin list changes
- selected metadata changes

Recommendation:

- start with message-history-rewriting actions
- add snapshot creation in app-owned orchestration where possible
- avoid pushing snapshot responsibility into each plugin when the application layer can own it

## Frontend draft

### Built-in mobile session action

Add a built-in action such as:

- `Snapshots`

Possible flow:

1. open a snapshot list modal/screen
2. show:
   - timestamp
   - reason
3. select a snapshot
4. open a readonly session-like viewer
5. offer:
   - restore
   - delete

### Reusing existing chat/settings views

To minimize change:

- keep live session id as the main route/session key
- add `snapshot_id` as viewer state
- call the same read-only backend methods with `snapshot_id`

Examples:

- message list uses `listMessages(sessionId, { ... , snapshotId })` after a small backend/client extension
- settings/config readers do the same

This should avoid a separate snapshot-only message/settings UI implementation.

### Readonly banner

Recommended UX:

- when `snapshot_id` is active, show a banner like:
  - `Viewing snapshot · read-only`

The viewer should suppress or disable:

- send
- append
- message edit/delete
- settings save

But the backend should still enforce readonly behavior regardless.

## Suggested implementation order

1. Add snapshot store primitives in `FilesystemSessionStore`.
2. Filter snapshot files out of normal session list code.
3. Add app-layer snapshot helpers on `AgentApplication`.
4. Extend read-only endpoints with optional `snapshot_id`.
5. Add dedicated snapshot list/create/delete/restore endpoints.
6. Add low-level readonly gating.
7. Add auto-snapshot creation to one or two destructive actions first.
8. Add a built-in mobile snapshot browser using the existing read-only session views plus `snapshot_id`.

## Test plan

### Store/application tests

- create/list/load/delete snapshot
- snapshot file names do not leak into normal session list
- restore creates a pre-restore snapshot when live session differs
- restore skips redundant pre-restore snapshot when identical

### Endpoint tests

- `GET /sessions/{session_id}/messages?snapshot_id=...` returns snapshot messages
- config/settings/plugins/UI-schema endpoints respect `snapshot_id`
- write/send operations against snapshot targets are rejected
- list/create/delete/restore snapshot endpoints work

### Action tests

- summarize range auto-creates snapshot before rewrite
- compaction auto-creates snapshot before rewrite
- delete range auto-creates snapshot before rewrite

### Frontend/mobile tests

- snapshot list shows timestamp and reason
- opening a snapshot reuses the existing read-only view flow
- readonly banner appears
- restore and delete actions behave correctly

## Open questions

- Should snapshot metadata live in the same JSON payload as the exported session, or should there be a small sidecar manifest per snapshot?
- Should snapshot reasons be free text or a short controlled vocabulary plus optional detail text?
- Should manual snapshot creation be exposed immediately in the UI, or only restore/delete/list at first?
- Should restore publish a dedicated event type such as `session_restored_from_snapshot`?
- Should delete-range be included in phase 1 auto-snapshotting, even though it currently runs under a single lock and is less conflict-prone than long-running actions?