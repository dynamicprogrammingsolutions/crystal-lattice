Parent Task: tasks/20260801-duration-and-stats-tracking/000-main.md

Depends On:
- tasks/20260801-duration-and-stats-tracking/010-framework-stats-infrastructure.md

# LLM Duration Stats Relocation

Move per-turn and total LLM duration from being stamped only on the last assistant message into the session stats metadata key, while keeping per-message duration on assistant messages for footer display.

## Requirements checklist

- [ ] Per-message LLM duration remains on assistant message metadata for message-footer display.
- [ ] Per-turn LLM duration is stored in the session stats metadata key, not only on the last assistant message.
- [ ] Total LLM duration (sum across all turns in a session) is computed and stored in the session stats metadata.
- [ ] LLM duration stats appear on the first session save after the change; old sessions are not backfilled.
- [ ] Session-list UI can surface LLM duration totals from the session stats metadata via a `session_list_field` element.
- [ ] The existing `turn_duration_ms` field name and semantics on assistant messages are preserved (LLM-only).

## Supporting details

### Current state

- `DurationExtension` (`plugins/timestamp-extension/src/timestamp_extension/duration_extension.py`) stamps `duration_ms`, `turn_duration_ms`, `turn_duration_formatted`, `turn_tps`, `turn_tps_formatted` on the "owner" assistant message's `_metadata` and mirrors them to core message `metadata`.
- The per-message fields survive native-history rebuilds because they live in `_metadata` on native messages.
- There is no `total_duration_ms` (session-wide cumulative) today; only per-turn `turn_duration_ms`.
- The session stats metadata key is configurable (default `stats`), defined in subtask 010.

### Constraints

- Per-message `metadata.duration_ms` and `metadata.turn_duration_ms` on assistant messages must remain — they are needed for footers and native-history rebuild survival.
- The relocation adds session-level totals; it does not remove per-message fields.
- No backward compatibility: old sessions without `stats` metadata are not backfilled. Stats appear on the first save after the change.
- The session stats metadata key is read from config, not hardcoded.

## Execution plan

Status: Draft

### Approach

1. Extend `DurationExtension` (or create a companion app plugin `plugins/llm-duration-stats-app/`) with a `session_save_prepare` lifecycle action that:
   - Reads the latest `turn_duration_ms` from the last assistant message's metadata.
   - Reads the existing `session.metadata["stats"]["llm_duration_ms"]` total (or 0 if missing).
   - Computes the new total by adding the latest turn's duration (avoiding double-counting turns already summed).
   - Writes `turn_duration_ms` and `llm_duration_ms` (total) into `session.metadata["stats"]`.
2. To avoid double-counting, track which turns have been counted. Options:
   - Store a `last_counted_turn_id` in the stats metadata (if turn ids are available from the usage extension).
   - Or compute the total from scratch by summing all assistant `duration_ms` values in the session on each save (simpler, O(n) per save).
   - *Recommendation*: compute from scratch on each save for correctness simplicity; the session message count is typically small enough that O(n) is acceptable. If performance becomes a concern, switch to incremental tracking later.

### Session-list surfacing

1. Add a `session_list_field` UI element: `{"ui_type": "session_list_field", "id": "llm_duration_total", "data": "metadata.stats.llm_duration_ms", "template": "LLM: {{data}}", "metadata": {"format": "duration_ms"}}`.
2. Gate it behind a config toggle `duration_extension_show_total_in_list` (default false).

### Implementation decisions and open questions

- **Where to implement**: extend `DurationExtension` (feature plugin) vs. new application plugin. `DurationExtension` is a feature plugin and does not have access to `AgentApplication` capabilities. A `session_save_prepare` lifecycle action needs application-layer dispatch. *Recommendation*: create a new `plugins/llm-duration-stats-app/` application plugin that depends on `DurationExtension` having stamped per-message fields, and handles the session-level aggregation. This keeps the feature plugin focused on per-message stamping and the app plugin focused on session-level stats.
- **Total computation**: sum-from-scratch vs. incremental. *Recommendation*: sum-from-scratch for v1 (simple, correct); revisit if large sessions cause performance issues.
- **Turn vs. total in stats**: store both `turn_duration_ms` (latest turn) and `llm_duration_ms` (session total) in `session.metadata["stats"]`.

### Documentation

- Update `plugins/timestamp-extension/README.md` to describe the session-level totals.
- `plugins/llm-duration-stats-app/README.md` for the new app plugin.

### Task checklist

- [ ] Create `plugins/llm-duration-stats-app/` package structure
- [ ] Implement `session_save_prepare` action that computes and writes LLM totals to session stats
- [ ] Add `session_list_field` UI element with config toggle
- [ ] Write unit tests (total computation, first-save appearance, no backfill)
- [ ] Write integration test verifying session-list field surfaces the total
- [ ] Write `README.md`

### Requirement verification

| Requirement | Verification evidence |
|---|---|
| Per-message LLM duration remains | Test that assistant messages still carry `metadata.duration_ms` and `metadata.turn_duration_ms` after the change |
| Per-turn LLM duration in session stats | Test that `session.metadata["stats"]["turn_duration_ms"]` is present after a request |
| Total LLM duration in session stats | Test that `session.metadata["stats"]["llm_duration_ms"]` equals the sum of all assistant `duration_ms` values across multiple turns |
| Stats appear on first save | Test with a fresh session: after first `save_session`, stats metadata is present |
| No backfill | Test that loading an old session without stats metadata does not trigger backfill; stats appear only after the next save |
| Session-list field surfaces total | UI-schema test confirming `session_list_field` with `metadata.stats.llm_duration_ms` is present |
| Existing `turn_duration_ms` preserved | Test that the per-message `turn_duration_ms` field name and value are unchanged on assistant messages |