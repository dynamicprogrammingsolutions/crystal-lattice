Parent Task: tasks/20260801-duration-and-stats-tracking/000-main.md

Depends On:
- tasks/20260801-duration-and-stats-tracking/010-framework-stats-infrastructure.md
- tasks/20260801-duration-and-stats-tracking/040-human-time-telemetry-plugin.md

# Human Time Tracking Plugin

A plugin that consumes the JSONL telemetry buffer using a read pointer, computes human review time and human message composition time with a configurable max-idle threshold, and stores per-message, per-turn, and total stats in the session stats metadata and on user messages.

## Requirements checklist

- [ ] A tracking plugin consumes buffered usage activity events from the telemetry JSONL file.
- [ ] The plugin maintains a read pointer (line count + last consumed event id) so it only processes new events on each aggregation pass, avoiding re-reading the entire file.
- [ ] Human time is split into at least two categories: human review time and human message composition time.
- [ ] A configurable max-idle-duration threshold is applied: gaps between activities longer than the threshold do not count toward human time.
- [ ] Per-session human time totals (review, composition, combined) are stored in the session stats metadata.
- [ ] Per-turn human time is tracked where relevant (e.g. composition time before a user message send).
- [ ] Per-message human composition time is stored on the corresponding user message metadata and in the session stats metadata.
- [ ] Total human time (review + composition) is stored in the session stats metadata.
- [ ] The tracking plugin writes stats on the first opportunity (session save or request complete); old sessions are not backfilled.
- [ ] Session-list UI can surface human time totals from the session stats metadata via `session_list_field` elements.
- [ ] The max-idle-duration threshold is configurable via server settings or application config.

## Supporting details

### Current state

- The telemetry plugin (subtask 040) writes events to `<session_stats_dir>/<session_id>/telemetry/usage_telemetry.jsonl` with monotonic event ids.
- `request_complete` and `session_save_prepare` lifecycle triggers are the natural write points for session stats.
- The session stats metadata key is configurable (default `stats`), defined in subtask 010.
- User messages are `Message(role="user", content=..., metadata=...)`; composition time can be stored in `metadata.human_composition_ms`.

### Constraints

- The tracking plugin must use `acquire_session_lock` before writing to `session.metadata["stats"]` to avoid clobbering concurrent request-driven stats updates.
- The read pointer must be persisted between aggregation passes so the plugin does not re-process old events.
- The read pointer file is owned by the tracking plugin (not the telemetry plugin).
- No backward compatibility: old sessions without telemetry files or stats are not backfilled; stats appear on the first save after telemetry events exist.

## Execution plan

Status: Draft

### Plugin structure

1. Create `plugins/human-time-tracking-app/` (application plugin) with:
   - `agent_plugin.json` registering the plugin class.
   - `src/human_time_tracking_app/__init__.py` implementing `HumanTimeTrackingAppPlugin`.
   - `tests/` with unit tests.

### Read pointer

1. The plugin stores its read pointer in `<session_stats_dir>/<session_id>/human_time_tracking/read_pointer.json`:
   ```json
   {"last_line": 42, "last_event_id": "sess-1:42", "updated_at": "..."}
   ```
2. On each aggregation pass, the plugin:
   - Reads the pointer file (or starts at line 0 if missing).
   - Opens the telemetry JSONL file, seeks to the last-read line, and reads new lines.
   - Processes each new event to update human-time accumulators.
   - Writes the updated pointer.

### Human time computation

1. **Event classification**:
   - `session_viewed` and `scroll` events count toward **review time**.
   - `compose_typing` events count toward **composition time**.
   - `message_composed` events mark the end of a composition segment and can attribute the composition duration to the corresponding user message.
2. **Max-idle rule**: if the gap between two consecutive events exceeds the configurable threshold (default 60 seconds), the gap is not counted. The threshold is read from `application.human_time_max_idle_seconds` (config) or a server setting.
3. **Composition time**: measured from the first `compose_typing` event after a review/idle period to the `message_composed` event. Attributed to the user message that was composed.
4. **Review time**: measured as the active span of `session_viewed`/`scroll` events, minus idle gaps.

### Stats storage

1. Per-message: store `human_composition_ms` and `human_composition_formatted` on the user message metadata (the message that was composed).
2. Per-session totals in `session.metadata["stats"]`:
   - `human_review_ms` — total review time
   - `human_composition_ms` — total composition time
   - `human_time_ms` — combined total
   - `human_review_formatted`, `human_composition_formatted`, `human_time_formatted`
3. Per-turn: store `turn_human_composition_ms` (composition time before the user message that started the turn) in the session stats metadata, keyed by turn or message index.

### Lifecycle hooks

1. `trigger: "request_complete"` — after a request, consume new telemetry events and update session stats.
2. `trigger: "session_save_prepare"` — before every save, consume new telemetry events and update session stats (catches saves outside of requests).

### Session-list surfacing

1. Add `session_list_field` elements:
   - `{"ui_type": "session_list_field", "id": "human_time_total", "data": "metadata.stats.human_time_ms", "template": "Human: {{data}}", "metadata": {"format": "duration_ms"}}`
   - Optionally separate review and composition fields.
2. Gate behind a config toggle `human_time_show_in_list` (default false).

### Implementation decisions and open questions

- **Read pointer vs. re-scan**: the read pointer avoids re-reading the full JSONL on every pass. If the pointer is lost (file deleted), the plugin falls back to reading from line 0 and re-computing from scratch (idempotent because stats are absolute, not incremental). *Recommendation*: implement the fallback; it is correct but slower.
- **Attributing composition to a user message**: the `message_composed` event should include the message index or a frontend-generated correlation id. *Recommendation*: the event includes `message_index` (the index of the user message in the session); the plugin uses it to stamp the correct message.
- **Per-turn human time**: "turn" is defined by the user message that starts it. Composition time before a user message is the "turn human composition time." *Recommendation*: store `turn_human_composition_ms` in the stats metadata keyed by the user message index.
- **Open question**: should review time be attributed per-turn (review between assistant response and next user message) or only as a session total? *Recommendation*: track both — per-turn review (between last assistant and next user) and session total.

### Documentation

- `plugins/human-time-tracking-app/README.md` describing the plugin, event classification, max-idle rule, and stats fields.
- Update `plugins/docs/application-plugins.md` with the tracking plugin pattern and read-pointer convention.

### Task checklist

- [ ] Create `plugins/human-time-tracking-app/` package structure
- [ ] Implement read-pointer file read/write
- [ ] Implement JSONL incremental consumption
- [ ] Implement event classification (review vs. composition)
- [ ] Implement max-idle rule
- [ ] Implement per-message composition time on user messages
- [ ] Implement per-turn and per-session totals in session stats metadata
- [ ] Add `request_complete` and `session_save_prepare` lifecycle actions
- [ ] Add `session_list_field` UI elements with config toggle
- [ ] Add max-idle config key to config schema
- [ ] Write unit tests (read pointer, idle rule, classification, per-message, per-turn, total)
- [ ] Write integration test with telemetry plugin (end-to-end: events → stats)
- [ ] Write `README.md`

### Requirement verification

| Requirement | Verification evidence |
|---|---|
| Consumes JSONL telemetry | Unit test: after telemetry plugin writes events, tracking plugin reads and processes them |
| Read pointer avoids re-reading | Unit test: after first pass, second pass with no new events does not re-process old lines (pointer advances) |
| Review vs. composition split | Unit test: `session_viewed`/`scroll` events count toward review; `compose_typing` counts toward composition |
| Max-idle threshold | Unit test: a 120s gap with a 60s threshold does not count toward human time |
| Per-session totals in stats metadata | Unit test: `session.metadata["stats"]["human_review_ms"]`, `human_composition_ms`, `human_time_ms` are present after processing |
| Per-turn human time | Unit test: `turn_human_composition_ms` is attributed to the correct turn |
| Per-message composition on user message | Unit test: the user message `metadata.human_composition_ms` is set after `message_composed` event |
| Total human time in stats | Unit test: `human_time_ms == human_review_ms + human_composition_ms` |
| Writes on first opportunity | Test with a fresh session: after `session_save_prepare`, stats are present |
| No backfill | Test that a session with no telemetry file does not error and has no human-time stats |
| Session-list field surfaces total | UI-schema test confirming `session_list_field` with `metadata.stats.human_time_ms` |
| Max-idle configurable | Test that changing `human_time_max_idle_seconds` changes the computed human time |