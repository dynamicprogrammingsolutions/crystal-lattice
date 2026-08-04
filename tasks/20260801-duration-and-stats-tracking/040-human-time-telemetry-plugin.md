Parent Task: tasks/20260801-duration-and-stats-tracking/000-main.md

Depends On:
- tasks/20260801-duration-and-stats-tracking/010-framework-stats-infrastructure.md

# Human Time Telemetry Plugin

An application plugin that accepts frontend-reported per-session usage activity events, stores them in a file-backed JSONL buffer under the session-level storage directory, and exposes a server setting that tells frontends which plugin id handles telemetry.

## Requirements checklist

- [ ] An application plugin exposes an action that accepts frontend-reported per-session usage activity events.
- [ ] The action accepts events describing at least: session viewing, scroll activity, and message composition activity.
- [ ] A server setting configures which plugin id handles usage telemetry.
- [ ] The server setting is discoverable via the server-settings UI schema so frontends can read it.
- [ ] The telemetry plugin stores received events in a file-backed JSONL buffer under the session-level storage directory.
- [ ] The JSONL file supports efficient appending of new events without rewriting the whole file.
- [ ] Each event in the JSONL file carries a unique, monotonic event id for consumer read-pointer tracking.
- [ ] The telemetry plugin does not compute human time stats; that is the tracking plugin's responsibility.
- [ ] The telemetry plugin is registered and active only when configured via the server setting.
- [ ] The action is idempotent for repeated events (same event id does not double-count).

## Supporting details

### Current state

- Frontends already call `executeAction({pluginId, actionId, inputs})` via the `AgentBackend` interface (`packages/frontend-sdk/src/backend/backend.ts`). No new SDK method is needed.
- Server settings are stored at `runtime/server_settings.json` and exposed via `GET /server/settings` and `GET /server/settings/ui-schema` (see `plugins/session-status-app` for an example of a server-scoped config element).
- The session-level storage directory is defined in subtask 010 (`stats.session_dir`, env `STATS_SESSION_DIR`).
- `AgentApplication.get_session_stats_dir(session_id)` returns the per-session subdirectory.

### Constraints

- The frontend owns the collection implementation; this plugin only defines the ingestion contract.
- The JSONL file must be append-only to support efficient writes and incremental reads.
- Event ids must be monotonic (e.g. line number + a per-session counter) so consumers can store a read pointer.
- The plugin must not compute human time; it only stores raw events for the tracking plugin (subtask 050).
- File writes must be atomic per line (append-only JSONL with a single `write` call per event line).

## Execution plan

Status: Draft

### Plugin structure

1. Create `plugins/usage-telemetry-app/` (application plugin) with:
   - `agent_plugin.json` registering the plugin class.
   - `src/usage_telemetry_app/__init__.py` implementing `UsageTelemetryAppPlugin`.
   - `tests/` with unit tests.

### Server setting

1. Expose a server-scoped config element: `{"ui_type": "config", "scope": "server", "key": "usage_telemetry_plugin_id", "type": "string", "label": "Usage telemetry plugin id", "description": "Plugin id that receives frontend usage activity events."}`.
2. The plugin reads this setting in `get_ui_elements` (context `server_settings`) and in `execute_action` to verify it is the configured handler.
3. If the setting is empty or does not match this plugin's id, the action returns a disabled result without storing events.

### Action contract

1. Action `record_usage_activity` with inputs:
   - `session_id: string` (required)
   - `events: array` (required) of event objects with:
     - `type: string` — one of `session_viewed`, `scroll`, `compose_typing`, `message_composed` (extensible)
     - `timestamp: string` — ISO 8601 UTC
     - `event_id: string` — unique per-session, monotonic (frontend-generated or plugin-assigned)
     - `details: object` (optional) — e.g. scroll position, compose text length
2. The action validates inputs, assigns sequential event ids if the frontend does not provide them, and appends each event as a JSON line to the JSONL file.

### JSONL storage

1. Path: `<session_stats_dir>/<session_id>/telemetry/usage_telemetry.jsonl` (the plugin owns the `telemetry/` subdir and the file name).
2. Append each event as a single JSON object on one line: `{"event_id": "...", "session_id": "...", "type": "...", "timestamp": "...", "details": {...}, "received_at": "..."}\n`.
3. Use a per-session lock (or `acquire_session_lock`) to avoid concurrent-write corruption.
4. Assign monotonic event ids as `<session_id>:<line_number>` if the frontend does not provide ids.

### Idempotency

1. If an event with the same `event_id` already exists in the file, skip it. To check efficiently, the plugin can read the last line's event id and compare, or maintain a small in-memory cache of recently seen ids.
2. For v1, a simple approach: trust the frontend to send monotonic ids and deduplicate by checking the last line's id. If a gap or duplicate is detected, log a warning and skip duplicates.

### Implementation decisions and open questions

- **Event id assignment**: frontend-assigned vs. plugin-assigned. *Recommendation*: accept both — if the frontend provides `event_id`, use it; otherwise assign `<session_id>:<next_line_number>`.
- **File rotation**: for long-running sessions, the JSONL file could grow large. *Recommendation*: no rotation for v1; address in a follow-up if file size becomes a problem. The read-pointer mechanism (subtask 050) means consumers only read new lines.
- **Concurrency**: multiple frontend instances (e.g. mobile + desktop) could send events for the same session. *Recommendation*: use `acquire_session_lock` during append to serialize writes.
- **Open question**: should the plugin expose a `read_telemetry` action for tracking plugins, or should tracking plugins read the JSONL file directly? *Recommendation*: tracking plugins read the file directly (they own their read pointer); the telemetry plugin only writes.

### Documentation

- `plugins/usage-telemetry-app/README.md` describing the action contract, event types, JSONL format, and server setting.
- Update `plugins/docs/application-plugins.md` with the telemetry plugin pattern and the server-setting-for-plugin-id convention.

### Task checklist

- [ ] Create `plugins/usage-telemetry-app/` package structure
- [ ] Implement `record_usage_activity` action with JSONL append
- [ ] Add server setting `usage_telemetry_plugin_id` with UI-schema element
- [ ] Implement event id assignment and idempotency
- [ ] Write unit tests (append, idempotency, server-setting gating, event validation)
- [ ] Write `README.md`

### Requirement verification

| Requirement | Verification evidence |
|---|---|
| Action accepts usage events | Unit test calling `execute_action` with events and verifying they are stored |
| Accepts session viewing, scroll, compose events | Unit test with all three event types |
| Server setting for plugin id | UI-schema test confirming `usage_telemetry_plugin_id` appears in server-settings UI schema |
| Server setting discoverable by frontends | Test that `GET /server/settings/ui-schema` includes the element |
| File-backed JSONL under session-level dir | Unit test verifying file exists at `<session_stats_dir>/<session_id>/telemetry/usage_telemetry.jsonl` after action |
| Efficient appending | Test that appending new events does not rewrite existing lines (file size grows by line count) |
| Monotonic event ids | Test that event ids are sequential and unique within a session |
| Plugin does not compute human time | Code inspection: no `human_time` or aggregation logic in the telemetry plugin |
| Active only when configured | Test that the action returns disabled when `usage_telemetry_plugin_id` does not match |
| Idempotent for repeated events | Test that sending the same event_id twice results in one line in the file |