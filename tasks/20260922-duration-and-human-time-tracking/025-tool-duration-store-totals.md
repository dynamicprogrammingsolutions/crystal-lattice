Parent Task: tasks/20260922-duration-and-human-time-tracking/000-main.md

Depends On:
- tasks/20260922-duration-and-human-time-tracking/010-session-duration-store.md
- tasks/20260922-duration-and-human-time-tracking/020-tool-call-duration.md

# Tool Duration Store Totals

Record tool call duration rows in the duration store from the stamps subtask 020 created, and surface store-backed tool-duration session totals alongside the LLM totals. This is the store-dependent half of the original tool-call-duration scope, split out so the framework capability and message stamping could land first (phase 1) without a store.

## Requirements checklist

- [ ] Tool call duration rows are recorded in the same store as session duration with the same method: one row per call keyed by `(working_directory, session_id)`, deduplicated per tool call, best-effort so recording failures never break tool execution or the request pipeline.
- [ ] Recording happens at the tool-call act-point (`finalize_tool_call`) from the message metadata stamped in 020 — no history scanning.
- [ ] Store-backed tool-duration session totals (total, call count, average — raw and formatted) are stamped alongside the LLM duration totals on the request's assistant message metadata and projected to public metadata.
- [ ] Tool totals surface via config-selected status-bar elements and report columns, mirroring the LLM totals pattern.
- [ ] Tool duration stays separate from LLM duration in the store schema, metadata fields, and the report; the two are never merged into one number.

## Supporting details

### Facts

- 020 delivers the stamps: `duration_ms`, `duration_formatted`, `duration_started_at`, `duration_finished_at`, `turn_tool_duration_ms` on tool-result message metadata, stamped by `DurationExtension` in `finalize_tool_call` (recommended owner; confirm at 020 plan approval).
- The recording plugin is the duration-tracking extension from 010, hooking `finalize_tool_call` after `DurationExtension` — priority order guarantees it receives the already-stamped message, the cost pattern (usage extension stamps, cost extension records). No new hook or dispatch point is needed.
- The store schema is designed in 010's plan together with this subtask's tool rows (both execute in the same phase): an LLM request-duration table and a tool-call-duration table (or equivalent separation) in the same SQLite DB, with the cost store's dedup pattern (unique index on `tool_call_id`, record-once).
- The store's session-totals query pattern (010) extends naturally: tool totals are the same query shape over tool rows; the extension stamps both total sets at request finalize.
- The cost-tracking report precedent (top sessions/projects, reset-aware windows) is mirrored by 010 for LLM duration; this subtask adds the tool columns to the same report.

### Decisions to pin in this subtask's plan

- Exact tool-row schema (columns mirroring the LLM rows plus `tool_call_id`, `tool_name`, `tool_plugin`) and whether tool rows carry the turn total or only per-call duration.
- Metadata field names for the tool totals (proposal: `tool_duration_session_total`, `tool_duration_session_total_formatted`, `tool_duration_session_calls`, `tool_duration_session_average*`).
- Status-bar element labels and the config choice selecting them (e.g. a `tools:` element; possibly under the same `none/totals/averages`-style config as the LLM totals).
- Whether the tool totals also appear in the summary CSV if 010 adopts one.

## Task relations

- Split out of `tasks/20260922-duration-and-human-time-tracking/020-tool-call-duration.md` (user decision, 2026-09-22) so only the store-dependent scope depends on 010.