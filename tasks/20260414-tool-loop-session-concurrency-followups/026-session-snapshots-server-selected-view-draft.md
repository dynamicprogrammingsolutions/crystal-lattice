# Session Snapshots Server-Selected View Draft

Draft a snapshot design that keeps frontend changes small by storing snapshots separately, managing snapshot selection on the server, and letting ordinary read endpoints keep working against the selected readonly snapshot view.

Parent Task: tasks/20260414-tool-loop-session-concurrency-followups/000-main.md
Depends On: tasks/20260414-tool-loop-session-concurrency-followups/010-tool-loop-session-settings-concurrency.md

## Requirements checklist

- [ ] Keep the original snapshot draft intact and capture this as a revised alternative.
- [ ] Minimize frontend changes by letting ordinary read-only session flows continue to work after snapshot selection.
- [ ] Store snapshots outside the live session directory.
- [ ] Persist selected-snapshot state on the server side.
- [ ] Reject writes and sends when a readonly snapshot view is selected.
- [ ] Support snapshot list/create/select/clear/restore/delete operations through explicit snapshot endpoints.
- [ ] Define how event behavior changes while a readonly snapshot view is selected.
- [ ] Keep this task draft-level so the design can still evolve before implementation.

## Relationship to the earlier draft

This is a revised alternative to:

- `tasks/20260414-tool-loop-session-concurrency-followups/025-session-snapshots-draft.md`

The earlier draft emphasized explicit backend snapshot ids plus frontend-driven snapshot-aware read endpoints. This version keeps explicit snapshot ids for management endpoints, but moves selected-snapshot state onto the server so the frontend can keep using ordinary session reads after selection.

## Why this revision

The earlier snapshot draft would still require the frontend to thread `snapshot_id` through many read-only data-loading paths:

- messages
- overrides
- config
- plugins
- UI schema

That is workable, but broader than necessary.

This revised design aims for:

- mostly server/internal changes
- explicit snapshot endpoints only for snapshot management
- ordinary session reads continuing to work after a snapshot is selected
- the frontend only needing to:
  - list snapshots
  - create/select/clear/restore/delete snapshots
  - reload the session after snapshot-related operations

## Current code shape relevant to this design

### Sessions are file-backed and session-id-centric

The current application layer stores live sessions as one JSON file per session in:

- `core/python/agent_app/sessions.py`

The app layer exposes:

- `load_session(...)`
- `load_session_record(...)`
- `save_session(...)`
- `send_request(...)`

in:

- `core/python/agent_app/application_future.py`

### The server and frontend expect ordinary session reads

Today the frontend reads session state through ordinary endpoints such as:

- `GET /sessions/{session_id}/messages`
- `GET /sessions/{session_id}/overrides`
- `GET /sessions/{session_id}/config/base`
- `GET /sessions/{session_id}/config/schema`
- `GET /sessions/{session_id}/plugins`
- `GET /sessions/{session_id}/ui-schema`
- `GET /sessions/{session_id}/application/ui-schema`

Those are consumed by:

- frontend chat/message controllers
- session settings controllers
- plugin/action schema loaders

This makes “server-selected snapshot view” attractive, because it avoids widening those client interfaces.

### Session list code scans JSON files directly

Normal session lists currently scan `*.json` in the live session root in:

- `application/python/agent_terminal_app/server.py`
- `application/python/agent_terminal_app/terminal_app.py`

So snapshot files should not live in the same directory as live sessions unless they are very carefully filtered.

### Built-in mobile session actions already exist

The mobile UI already has built-in non-plugin session actions in:

- `packages/frontend-rn-components/src/sessionActions.ts`
- `mobile/crystal-lattice-control-rn/src/SessionsScreen.tsx`
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`

This gives a clean place to add snapshot browsing with minimal frontend plumbing.

## Draft design

### 1. Store snapshots in a separate directory

Do not place snapshot JSON files beside live session files.

Suggested layout:

- live sessions:
  - `sessions/<session_id>.json`
- snapshots:
  - `sessions/.snapshots/<session_id>/<snapshot_id>.json`
- selected-view state:
  - `sessions/.views/<session_id>.json`

Benefits:

- no accidental leakage into live session list code
- snapshot management becomes explicit
- the live session directory stays simple

### 2. Persist selected snapshot state on the server

Add a small per-session view-state record, for example:

- `sessions/.views/<session_id>.json`

Suggested contents:

```json
{
  "selected_snapshot_id": "snap_123",
  "selected_at": "2026-04-14T12:34:56Z",
  "readonly": true
}
```

Rules:

- no file or empty state means the live session is selected
- when a snapshot is selected, read operations resolve through that snapshot
- snapshot selection is server-owned, not frontend-owned

### 3. Let ordinary read endpoints resolve the selected snapshot transparently

When a snapshot is selected for a session id:

- `load_session(...)` or a nearby read helper should resolve to snapshot content for read-only use
- existing read endpoints can keep calling the same app-layer APIs with minimal changes

This keeps the existing frontend contract mostly stable:

- frontend selects a snapshot through a snapshot endpoint
- frontend reloads the session
- ordinary reads now show snapshot content

### 3a. Treat snapshot selection as a view change, not a live session mutation stream

While a snapshot is selected, the user should be looking at a frozen readonly view.

That means normal live session events must not keep mutating the visible chat state underneath the user.

Recommended event behavior:

- selecting a snapshot publishes a dedicated view-change event, for example:
  - `session_snapshot_selected`
  - or a generic `session_view_changed` with:
    - `view_kind: "snapshot"`
    - `snapshot_id`
- clearing snapshot selection publishes:
  - `session_snapshot_cleared`
  - or `session_view_changed` with `view_kind: "live"`
- restoring from a snapshot publishes:
  - `session_restored_from_snapshot`
  - and/or a final `session_view_changed` back to live mode

While snapshot view is active:

- normal live request/message/tool events for that `session_id` should be suppressed for ordinary session polling
- the frontend that selected the snapshot can simply reload after the snapshot endpoint call completes
- other attached clients can notice the dedicated view-change event and reload too

This keeps snapshot view frozen and avoids the confusing case where the user opens a readonly snapshot but incoming live events continue altering the visible conversation.

### 4. Keep write/send gating at the app/session-store boundary

When a snapshot is selected, mutating operations must fail.

Primary enforcement points:

- `save_session(...)`
- `send_request(...)`
- app/session action mutation flows

Optional earlier guard:

- routes can read a lightweight readonly/view-state helper and fail before starting expensive work

Additional recommended guard:

- reject snapshot selection while a live request is actively running for that session

Reason:

- otherwise one side may still be producing live request events while the selected snapshot view is meant to be frozen and readonly

Recommended app-layer helper:

- `get_session_view_state(session_id) -> { readonly: bool, selected_snapshot_id: str | None }`

This keeps `load_session(...)` shape stable while still allowing early rejection.

### 5. Snapshot management remains explicit through dedicated endpoints

Recommended endpoints:

- `GET /sessions/{session_id}/snapshots`
- `POST /sessions/{session_id}/snapshots`
- `POST /sessions/{session_id}/snapshots/{snapshot_id}/select`
- `DELETE /sessions/{session_id}/snapshots/selected`
- `POST /sessions/{session_id}/snapshots/{snapshot_id}/restore`
- `DELETE /sessions/{session_id}/snapshots/{snapshot_id}`

Frontend responsibilities stay narrow:

- list snapshots
- create snapshot
- select snapshot
- clear selected snapshot
- restore snapshot
- delete snapshot
- reload session after selection/clear/restore

### 6. Restore targets the live session and clears snapshot selection

`restore_snapshot(session_id, snapshot_id)` should:

1. load the live session
2. load the target snapshot
3. compare for meaningful difference
4. if different, create a snapshot of the current live session first
5. overwrite the live session with the restored snapshot content
6. clear selected snapshot view state

This ensures:

- restore is reversible
- after restore, normal session reading shows the restored live session

### 7. Automatic snapshotting still applies to destructive actions

This part still matches the earlier draft.

Likely first-wave auto-snapshot operations:

- summarize range
- gemini compaction
- provider-extension session actions that rewrite history
- possibly delete range

These actions should snapshot the live session before mutation.

### 8. Snapshot browsing should show a readonly banner

Even though the frontend keeps using normal session reads after selection, it should still visibly indicate that the user is viewing a snapshot.

Suggested server-exposed view state:

- `readonly: true`
- `selected_snapshot_id`
- maybe `selected_snapshot_reason`
- maybe `selected_snapshot_created_at`

Suggested frontend banner:

- `Viewing snapshot · read-only`

## Store/application layer changes

### Session store

Add first-class snapshot methods to `FilesystemSessionStore`:

- `create_snapshot(session, *, reason, metadata=None) -> SessionSnapshotRecord`
- `list_snapshots(session_id) -> list[SessionSnapshotRecord]`
- `load_snapshot(session_id, snapshot_id) -> Session`
- `delete_snapshot(session_id, snapshot_id) -> bool`
- `get_selected_snapshot_id(session_id) -> str | None`
- `select_snapshot(session_id, snapshot_id) -> None`
- `clear_selected_snapshot(session_id) -> None`

Suggested snapshot record fields:

- `snapshot_id`
- `session_id`
- `created_at`
- `reason`
- `metadata`

### AgentApplication

Add explicit snapshot helpers:

- `create_session_snapshot(...)`
- `list_session_snapshots(...)`
- `select_session_snapshot(...)`
- `clear_selected_session_snapshot(...)`
- `restore_session_snapshot(...)`
- `delete_session_snapshot(...)`
- `get_session_view_state(...)`

The main app-layer write helpers should also consult selected view state and reject readonly operations.

## Server changes

Minimal route changes outside the new snapshot endpoints:

- ordinary read endpoints should continue to work because session loading resolves through selected snapshot state
- mutating endpoints may optionally perform an early readonly check for better errors before expensive work starts

This is much smaller than threading `snapshot_id` through every frontend/backend read call.

## Frontend draft

### Built-in session action

Add a built-in session action:

- `Snapshots`

Flow:

1. user opens the snapshot list
2. frontend fetches snapshots from the explicit snapshot endpoint
3. user selects one
4. frontend calls snapshot-select endpoint
5. frontend reloads the session
6. the ordinary session screen now shows snapshot content

Other actions:

- `Restore`
- `Delete`
- `Back to live session` or `Exit snapshot`

### Minimal frontend behavior change

The frontend does not need to thread `snapshot_id` through all ordinary session reads.

It mainly needs:

- snapshot list UI
- snapshot action calls
- reload after snapshot-related calls
- readonly banner driven by server-provided session view state

## Test plan

### Store/application tests

- create/list/load/delete snapshot in separate snapshot directory
- select/clear selected snapshot view state
- ordinary live session load still works when no snapshot is selected
- selected snapshot causes read path to resolve snapshot content
- write/send/save are rejected when readonly snapshot view is selected
- restore snapshots current live session first when meaningfully different

### Server tests

- snapshot list/create/select/clear/restore/delete endpoints
- after selecting a snapshot, ordinary `GET /sessions/{id}/messages` returns snapshot messages
- after clearing selection, ordinary reads return live session again
- write endpoints fail clearly while snapshot view is selected
- selecting a snapshot emits a dedicated view-change event
- while snapshot view is active, ordinary live chat events are suppressed for that session view
- clearing selection/restoring emits view-change events that let clients reload back to the live view

### Frontend/mobile tests

- built-in snapshot action opens list
- selecting a snapshot and reloading shows snapshot content
- readonly banner appears
- clearing selection returns to live session view

## Benefits of this version

- keeps frontend changes much smaller
- avoids widening many read-only client APIs
- keeps snapshot selection server-owned and durable
- avoids snapshot files polluting normal live session listing
- keeps low-level readonly gating in the backend where it belongs
- gives snapshot view a clear event model instead of mixing frozen snapshot content with live request events

## Open questions

- Should ordinary read endpoints expose snapshot/view metadata directly in their existing payloads, or should there be one small `GET /sessions/{session_id}/view-state` endpoint for the banner?
- Should snapshot selection survive server restart indefinitely, or should it be treated more like a temporary server-side view preference?
- Should restore always clear selection, or is there any useful case for remaining inside the same snapshot view after restore?
- Should `delete range` be in phase 1 auto-snapshotting, or should phase 1 focus only on the long-running destructive actions first?
- Should the server suppress all ordinary session events while snapshot view is active, or only the message/history-mutating ones?