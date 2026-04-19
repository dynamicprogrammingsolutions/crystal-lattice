# Session Snapshots Server-Selected View Draft

Draft a snapshot design that keeps frontend changes small by storing snapshots separately, managing snapshot selection on the server, and letting ordinary read endpoints keep working against the selected readonly snapshot view.

Parent Task: tasks/20260414-tool-loop-session-concurrency-followups/000-main.md
Depends On: tasks/20260414-tool-loop-session-concurrency-followups/010-tool-loop-session-settings-concurrency.md

## Requirements checklist

- [x] Keep the original snapshot draft intact and capture this as a revised alternative.
- [x] Minimize frontend changes by letting ordinary read-only session flows continue to work after snapshot selection.
- [x] Store snapshots outside the live session directory.
- [x] Persist selected-snapshot state through a separate snapshot-selection component, not through the session store.
- [x] Reject writes and sends when a readonly snapshot view is selected.
- [x] Support snapshot list/create/select/clear/restore/delete operations through explicit snapshot endpoints.
- [x] Define how event behavior changes while a readonly snapshot view is selected.
- [x] Expose snapshot state on loaded sessions with readable top-level fields such as `snapshot_id` and `readonly`.
- [x] Keep this task draft-level so the design can still evolve before implementation.

## Task checklist

- [x] Add snapshot persistence primitives and explicit snapshot CRUD to the session store.
- [x] Add a separate filesystem-backed snapshot selection store and inject it into server-side `AgentApplication` instances.
- [x] Make app-layer reads resolve the selected snapshot while writes and sends reject readonly snapshot views.
- [x] Add server snapshot endpoints plus snapshot-selection event publishing and event suppression.
- [x] Add a minimal mobile snapshot browser and readonly banner.
- [x] Add focused core and server regression tests for selection isolation, restore behavior, and readonly snapshot reads.

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
  - `sessions/.snapshots/<session_id>.<timestamp>.json`
- snapshot selection files:
  - `sessions/.snapshots/<session_id>.selected.json`

Benefits:

- no accidental leakage into live session list code
- snapshot management becomes explicit
- the live session directory stays simple

### 2. Keep snapshot selection separate from snapshot persistence

Snapshot persistence and snapshot selection should be handled by different classes.

Recommended split:

- `FilesystemSessionStore`
  - persists live sessions
  - persists snapshots
  - loads explicit snapshots when given `snapshot_id`
- `SnapshotSelectionStore` or similar
  - manages which snapshot, if any, is selected for a live `session_id`
  - can persist that selection however it wants
  - is injected into `AgentApplication`

This keeps the session store stateless with respect to selection.

Suggested first implementation:

- snapshot files in:
  - `sessions/.snapshots/<session_id>.<timestamp>.json`
- selection files in the same directory:
  - `sessions/.snapshots/<session_id>.selected.json`

Suggested selection file contents:

```json
{
  "selected_snapshot_id": "snap_123",
  "selected_at": "2026-04-14T12:34:56Z"
}
```

Rules:

- no selection file or empty state means the live session is selected
- selection is opt-in per `AgentApplication` instance
- one app instance can select a snapshot while another still sees the live session
- terminal should therefore keep seeing the live session even if the server selected a snapshot

### 3. Let ordinary read endpoints resolve the selected snapshot transparently

When a snapshot is selected for a session id:

- `AgentApplication.load_session(...)` and `load_session_record(...)` should consult the injected selection component
- if a snapshot is selected, the app layer should load that snapshot through the session store
- existing read endpoints can keep calling the same app-layer APIs with minimal changes

This keeps the existing frontend contract mostly stable:

- frontend selects a snapshot through a snapshot endpoint
- frontend reloads the session
- ordinary reads now show snapshot content

### 3a. Expose readonly snapshot state directly on loaded sessions

To keep the frontend simple, loaded snapshot sessions should expose readable top-level fields rather than a private-looking nested marker.

Recommended fields on loaded snapshot sessions:

- `snapshot_id`
- `readonly`

These should be easy for the frontend to inspect and can also be used by the backend for fast checks.

Snapshot files themselves should remain ordinary session JSON exports, with additional easy-to-read top-level snapshot fields when stored, such as:

- `snapshot_id`
- `readonly`
- `snapshot_created_at`
- `snapshot_reason`

This keeps snapshot files human-manageable and easy to inspect manually.

### 3b. Treat snapshot selection as a view change, not a live session mutation stream

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

- routes can inspect the loaded session's `readonly` flag and fail before starting expensive work

Additional recommended guard:

- reject snapshot selection while a live request is actively running for that session

Reason:

- otherwise one side may still be producing live request events while the selected snapshot view is meant to be frozen and readonly

### 5. Snapshot management remains explicit through dedicated endpoints

Recommended endpoints:

- `GET /sessions/{session_id}/snapshots`
- `POST /sessions/{session_id}/snapshots`
- `GET /sessions/{session_id}/snapshots/selected`
- `POST /sessions/{session_id}/snapshots/{snapshot_id}/select`
- `DELETE /sessions/{session_id}/snapshots/selected`
- `POST /sessions/{session_id}/snapshots/{snapshot_id}/restore`
- `DELETE /sessions/{session_id}/snapshots/{snapshot_id}`

Frontend responsibilities stay narrow:

- list snapshots
- create snapshot
- get selected snapshot
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
6. clear selected snapshot selection

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

Suggested loaded-session fields:

- `readonly: true`
- `selected_snapshot_id`
- `snapshot_reason`
- `snapshot_created_at`

Suggested frontend banner:

- `Viewing snapshot · read-only`

## Store/application layer changes

### Session store

Add first-class snapshot methods to `FilesystemSessionStore`:

- `create_snapshot(session, *, reason, metadata=None) -> SessionSnapshotRecord`
- `list_snapshots(session_id) -> list[SessionSnapshotRecord]`
- `load(session_id, *, snapshot_id=None) -> Session | None`
- `delete_snapshot(session_id, snapshot_id) -> bool`

Suggested snapshot record fields:

- `snapshot_id`
- `session_id`
- `created_at`
- `reason`
- `metadata`

Important constraint:

- the session store should not remember selected snapshot state
- `snapshot_id` should be passed explicitly on every store load that wants a snapshot

### Snapshot selection store

Add a separate selection component with CRUD-like selection methods:

- `get_selected_snapshot(session_id) -> str | None`
- `select_snapshot(session_id, snapshot_id) -> None`
- `clear_selected_snapshot(session_id) -> None`

The implementation can decide how selection is persisted.

Suggested first implementation:

- filesystem-backed
- uses `sessions/.snapshots/<session_id>.selected.json`
- injected into `AgentApplication`

### AgentApplication

Add explicit snapshot helpers:

- `create_session_snapshot(...)`
- `list_session_snapshots(...)`
- `get_selected_session_snapshot(...)`
- `select_session_snapshot(...)`
- `clear_selected_session_snapshot(...)`
- `restore_session_snapshot(...)`
- `delete_session_snapshot(...)`

The main app-layer read helpers should:

- consult the selection store
- pass `snapshot_id` explicitly into the session store when needed

The main app-layer write helpers should:

- reject when the currently loaded session is readonly
- explicitly use the live session when creating snapshots or restoring snapshots

## Server changes

Minimal route changes outside the new snapshot endpoints:

- ordinary read endpoints should continue to work because session loading resolves through selected snapshot state
- mutating endpoints may optionally perform an early `readonly` check on the loaded session for better errors before expensive work starts

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
- readonly banner driven by loaded session fields such as `readonly` and `snapshot_id`

## Test plan

### Store/application tests

- create/list/load/delete snapshot in separate snapshot directory
- select/get/clear selected snapshot through the selection component
- ordinary live session load still works when no snapshot is selected
- app instance with snapshot selection sees snapshot content while another app instance without selection still sees live content
- write/send/save are rejected when readonly snapshot view is selected
- restore snapshots current live session first when meaningfully different

### Server tests

- snapshot list/create/select/clear/restore/delete endpoints
- selected-snapshot endpoint returns the current selection id or null
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
- keeps snapshot selection separate from snapshot persistence
- keeps snapshot selection opt-in per application instance
- avoids snapshot files polluting normal live session listing
- keeps low-level readonly gating in the backend where it belongs
- gives snapshot view a clear event model instead of mixing frozen snapshot content with live request events

## Open questions

- Should selection survive server restart indefinitely, or should the first filesystem-backed selector be treated as only one possible persistence strategy?
- Should restore always clear selection, or is there any useful case for remaining inside the same snapshot view after restore?
- Should `delete range` be in phase 1 auto-snapshotting, or should phase 1 focus only on the long-running destructive actions first?
- Should the server suppress all ordinary session events while snapshot view is active, or only the message/history-mutating ones?

## Execution plan

Added during completion after user approval.

### 1. Add snapshot persistence primitives to the session store

In `core/python/agent_app/sessions.py`:

- add `SessionSnapshotRecord`
- add snapshot-path helpers under `sessions/.snapshots/`
- implement:
  - `create_snapshot(session, *, reason, metadata=None)`
  - `list_snapshots(session_id)`
  - `load(session_id, *, snapshot_id=None)`
  - `delete_snapshot(session_id, snapshot_id)`

Implementation notes:

- snapshot files should be stored as plain session JSON
- snapshot-specific fields should be easy-to-read top-level fields such as:
  - `snapshot_id`
  - `readonly`
  - `snapshot_created_at`
  - `snapshot_reason`
- the session store must remain stateless with respect to selection

### 2. Add a separate snapshot-selection component

In `core/python/agent_app`, add a small selection interface and a first filesystem-backed implementation.

Suggested interface:

- `get_selected_snapshot(session_id) -> str | None`
- `select_snapshot(session_id, snapshot_id) -> None`
- `clear_selected_snapshot(session_id) -> None`

Suggested first implementation:

- stores files in `sessions/.snapshots/<session_id>.selected.json`
- stores:
  - `selected_snapshot_id`
  - `selected_at`

### 3. Inject the selection component into `AgentApplication`

Update `AgentApplication` construction so it can receive a selection component.

Behavior:

- if no selection component is provided, default to one that always returns `None`
- this keeps snapshot selection opt-in and per-application-instance

This is important because:

- server can select a snapshot
- terminal can still see the live session

### 4. Make `AgentApplication` resolve selected snapshots on read

Update:

- `load_session(...)`
- `load_session_record(...)`

to:

1. ask the selection component for the selected snapshot id
2. if none, load the live session
3. if present, call the session store with `snapshot_id=...`

Also add a helper for explicit live-session access, for example:

- `load_live_session_record(session_id)`

This is needed for restore and destructive operations.

### 5. Enforce readonly gating on write paths

In `AgentApplication`:

- reject writes when the effective loaded session has `readonly: true`
- enforce this in:
  - `save_session(...)`
  - `send_request(...)`
  - mutating session action flows

Routes may also do an earlier check by inspecting the loaded session’s `readonly` field to avoid expensive work before failure.

### 6. Add snapshot management APIs to `AgentApplication`

Add:

- `create_session_snapshot(...)`
- `list_session_snapshots(...)`
- `get_selected_session_snapshot(...)`
- `select_session_snapshot(...)`
- `clear_selected_session_snapshot(...)`
- `restore_session_snapshot(...)`
- `delete_session_snapshot(...)`

Important restore semantics:

- always load the live session explicitly
- if the live session differs meaningfully, snapshot it first with reason like `before restore`
- overwrite the live session
- clear selected snapshot selection

### 7. Add server endpoints for snapshot management

In `application/python/agent_terminal_app/server.py`, add:

- `GET /sessions/{session_id}/snapshots`
- `POST /sessions/{session_id}/snapshots`
- `GET /sessions/{session_id}/snapshots/selected`
- `POST /sessions/{session_id}/snapshots/{snapshot_id}/select`
- `DELETE /sessions/{session_id}/snapshots/selected`
- `POST /sessions/{session_id}/snapshots/{snapshot_id}/restore`
- `DELETE /sessions/{session_id}/snapshots/{snapshot_id}`

Normal read routes should stay mostly unchanged because they use `load_session(...)`.

### 8. Add event behavior for selection/clear/restore

Publish dedicated events such as:

- `session_snapshot_selected`
- `session_snapshot_cleared`
- `session_restored_from_snapshot`

While the selecting application instance has a snapshot selected:

- ordinary live session progression events should be suppressed in `/events` for that session

This suppression should be based on that app instance’s selection state, not on global session state.

### 9. Add minimal frontend support

In the frontend SDK and mobile app:

- add snapshot API methods
- add a built-in `Snapshots` action
- implement:
  - list snapshots
  - create snapshot
  - get selected snapshot
  - select snapshot
  - clear selected snapshot
  - restore snapshot
  - delete snapshot
- after snapshot-related operations, reload the session
- show a readonly banner when the loaded session includes:
  - `readonly: true`
  - `snapshot_id`

### 10. Add auto-snapshotting to destructive actions

First-wave targets:

- summarize range
- gemini compaction
- provider-extension session actions that rewrite history

Optional same-pass target:

- delete range

These should snapshot the live session, not the selected snapshot view.

### 11. Test in layers

Store/application tests:

- create/list/load/delete snapshots
- selection component CRUD
- per-application-instance selection isolation
- readonly write rejection
- restore preimage snapshot behavior

Server tests:

- snapshot endpoints
- selected snapshot endpoint
- ordinary reads resolve selected snapshot on the server
- ordinary writes fail when readonly snapshot selected
- selection/clear/restore events
- ordinary live event suppression while selected

Frontend/mobile tests:

- snapshot list action
- select and reload
- readonly banner
- clear and restore returning to live session

## Completion Notes

Added during completion.

- Implemented snapshot persistence in `FilesystemSessionStore` under `sessions/.snapshots/`, with snapshot files stored as readable session JSON plus snapshot metadata fields.
- Added a separate `FilesystemSnapshotSelectionStore` and wired it only into server-side `AgentApplication` construction so terminal instances still default to the live session.
- Updated `AgentApplication` to resolve selected snapshots on reads, reject writes and sends while a snapshot is selected, and support create/list/get-selected/select/clear/restore/delete snapshot helpers.
- Added server endpoints for snapshot management, published `session_snapshot_selected`, `session_snapshot_cleared`, and `session_restored_from_snapshot` events, and suppressed ordinary live events for sessions with a selected snapshot on that server instance.
- Extended `GET /sessions/{session_id}/messages` to return top-level `readonly` and `snapshot_id` fields for the frontend banner.
- Added a minimal mobile `Snapshots` action that lists snapshots, creates/selects/restores/deletes them, reloads the session after snapshot actions, and shows a readonly banner while a snapshot is selected.
- Added focused tests in `core/python/tests/test_application_session_snapshots.py` and `application/python/tests/test_agent_terminal_app_server.py`.