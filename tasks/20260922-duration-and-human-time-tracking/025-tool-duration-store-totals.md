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

- 020 delivered the stamps: `duration_ms`, `duration_formatted`, `duration_started_at`, `duration_finished_at` on tool-result message metadata, stamped by `DurationExtension` in `finalize_tool_call`. The per-turn tool total (`turn_tool_duration_ms`/`_formatted`) was relocated by the 020 follow-up to the assistant owner message via `DurationExtension.finalize` (native-history scan, `role == "tool"` only, absent for turns without tool results) — it is a message surface, not a recording source for per-call rows.
- The recording plugin is the duration-tracking plugin from 010, hooking `finalize_tool_call` after `DurationExtension`. **Kind constraint (material)**: `DurationExtension` is a `FeaturePlugin` (priority 200) and the hook chain runs extensions before features, so the tracking plugin must be a `FeaturePlugin` with priority > 200 (e.g. 210) to receive the already-stamped message in the same chain — the cost extension's shape (`ProviderExtensionPlugin`, priority 70) would run before `DurationExtension` and see the unstamped message. No new hook or dispatch point is needed.
- The store schema is designed in 010's plan together with this subtask's tool rows (both execute in the same phase): an LLM request-duration table and a tool-call-duration table (or equivalent separation) in the same SQLite DB, with the cost store's dedup pattern (unique index on `tool_call_id`, record-once).
- The store's session-totals query pattern (010) extends naturally: tool totals are the same query shape over tool rows; the extension stamps both total sets at request finalize.
- The cost-tracking report precedent (top sessions/projects, reset-aware windows) is mirrored by 010 for LLM duration; this subtask adds the tool columns to the same report.
- Synthesized-error tool results also carry the stamps (finalize dispatches on those paths with a `tool_error` fact), so failed calls are recorded like successful ones; the `tool_error` fact is available in the context if the schema wants to distinguish them.

### Decisions to pin in this subtask's plan

- Exact tool-row schema (columns mirroring the LLM rows plus `tool_call_id`, `tool_name`, `tool_plugin`) and whether tool rows carry the turn total or only per-call duration.
- Metadata field names for the tool totals (proposal: `tool_duration_session_total`, `tool_duration_session_total_formatted`, `tool_duration_session_calls`, `tool_duration_session_average*`).
- Status-bar element labels and the config choice selecting them (e.g. a `tools:` element; possibly under the same `none/totals/averages`-style config as the LLM totals).
- Whether the tool totals also appear in the summary CSV if 010 adopts one.

## Execution plan

Status: Approved

Executes immediately after 010's chunks, on the same package. Adds the tool half of the store: tool-row store functions, the `finalize_tool_call` recording seam, tool session totals stamped alongside the LLM totals at request finalize, tool status-bar elements under the same breakdown config, and report tool columns. The `tool_durations` table schema already lands with 010's store module (designed once, no migration).

### Approach

- **Recording seam**: `DurationTrackingExtension.finalize_tool_call` — the hook 020 added. It runs after `DurationExtension` (priority 200) in the chain, so the received core message already carries the per-call stamps in `metadata` (`duration_ms`, `duration_formatted`, `duration_started_at`, `duration_finished_at`). Read the stamps plus the context facts (`session_id`, `request_id`, `tool_call_id`, `tool_name`, `tool_plugin`, `tool_error`), record one row, return the message unchanged. Config comes from `context["config"]` (core layer-1 enrichment puts it in the tool context) with a `state["config"]` fallback; `working_directory` via the same helper as 010.
- **No stamping at the tool seam**: tool totals are session aggregates; they are stamped at request finalize alongside the LLM totals (one query pass, one stamp pass), so the status bar updates once per request exactly like the cost totals.
- **Synthesized-error results record too**: they carry stamps and a `tool_error` context fact (020 dispatches finalize on those paths), so failed calls land in the store with the `tool_error` column distinguishing them. Calls with a NULL `tool_call_id` (failed inspection) record without dedup — each occurrence is a distinct event.
- **No history scanning**: the recording reads only the message it receives in the chain (the agreed seam).

### Tool store functions (`duration_store.py` additions)

- `record_tool_duration` — one row per call; returns `False` on `IntegrityError` (composite unique index `(working_directory, session_id, request_id, tool_call_id)` lands with 010's schema).
- `tool_session_totals` — `total_ms`, `call_count` for one `(working_directory, session_id)`.
- `top_sessions` / `top_projects` gain the tool columns (`tool_total_ms`, `tool_call_count`) so the report shows both durations per session/project.

### Tool totals stamping

010's chunk-3 `finalize` extends: after recording the LLM row, query both `session_totals` and `tool_session_totals`, and stamp `tool_duration_session_total`, `tool_duration_session_total_formatted`, `tool_duration_session_calls`, `tool_duration_session_calls_formatted`, `tool_duration_session_average`, `tool_duration_session_average_formatted` next to the `duration_session_*` fields (same attach pattern, same always-stamped-zeros rule). `from_native_messages` promotes the new fields (same prefix-scan, extended key set).

### UI elements

Under the same `duration_breakdown` select: `totals` mode adds `tools: {{data}}` (`metadata.tool_duration_session_total_formatted`) and `tool calls: {{data}}` (`metadata.tool_duration_session_calls_formatted`) after `requests:`; `averages` mode adds `tool average: {{data}}` (`metadata.tool_duration_session_average_formatted`) as well. All fields are always stored; the config selects display only.

### Report columns

`show_duration_report` gains: the overall section adds tool total, tool calls, and tool average; the top sessions and top projects tables gain a `Tools` column. Tool duration stays a separate column everywhere — never merged into the LLM total.

### Test-first chunks

Each chunk: tests first (red), implement, green.

1. **Tool store functions** — red: `test_duration_store_unit.py` additions (`record_tool_duration` composite dedup: the same call id in a different request records, the same tuple twice returns `False`; `tool_session_totals`; tool columns in `top_sessions`/`top_projects`). Green: the store functions.
2. **`finalize_tool_call` recording** — red: `test_duration_tracking_extension_unit.py` additions (a fixture stamped tool message + context records one row; unstamped message → no row; `track_durations=False` → no row; synthesized-error row carries `tool_error`; store failure swallowed and the message returned unchanged; no history access — fixture history present but stale rows must not record). Green: the hook.
3. **Tool totals stamping + projection** — red: totals stamped alongside the LLM totals (zeros for tool-less sessions), `tool_duration_session_*` projected via `native_indices`. Green: extend `finalize` + `from_native_messages`.
4. **UI elements** — red: breakdown modes include the tool elements in order. Green: extend `get_ui_elements`.
5. **Report columns** — red: app plugin tests (overall tool fields, `Tools` column in both top tables). Green: extend the report.
6. **Integration + sweep** — red: extend `test_duration_tracking_agent_application_integration.py` (a tool-calling request records one LLM row plus one tool row per call; two calls in one turn → two tool rows; totals include tool duration; a failed call — no handler — records with `tool_error`). Green; then the full sweep: `pytest plugins/duration-tracking/tests -q` (plus `-m integration` for the integration file), core, application, timestamp-extension suites; ruff/black/pyright.

### Implementation decisions and open questions

- Resolved: composite dedup key includes `request_id` (providers may reuse sequential call ids across requests in a session).
- Resolved: synthesized-error calls record with `tool_error`; NULL-id calls record without dedup.
- Resolved: tool totals stamp at request finalize, not at the tool seam; always stamped, zeros included (mirrors cost and 010).
- Resolved: tool rows are not appended to the summary CSV (010's decision; they live in SQLite and the report).
- Open (minor, pin during chunk 2): whether `tool_session_totals` should also return an `error_count` for the report — cheap to add to the query; include only if the report wants to show it.
- No open contract decisions.

### Documentation

- Extend `plugins/duration-tracking/README.md` and `docs/development/overview.md` with the tool fields, the `finalize_tool_call` seam, tool status-bar elements, and the report columns (040 does the final cross-subtask pass).

### Task checklist

- [x] Obtain plan approval (moved to Approved 2026-09-23; executed together with 010)
- [x] Chunk 1: tool store functions (red/green)
- [x] Chunk 2: `finalize_tool_call` recording
- [x] Chunk 3: tool totals stamping + projection
- [x] Chunk 4: tool UI elements
- [x] Chunk 5: report tool columns
- [x] Chunk 6: integration extension + full sweep (package 80 passed incl. 6 integration; ruff/black/pyright clean; core/application/timestamp suites unchanged since the 010 sweep — no files outside the package changed)
- [x] Update the parent task's requirement checkboxes for the 010/025 scope

### Requirement verification

| Requirement | Evidence |
|---|---|
| Tool rows in the same store, same method, one row per call keyed `(working_directory, session_id)`, deduplicated, best-effort | Store unit tests (composite dedup) + integration test (one row per call across a two-call turn) + fault-injection test (store failure never breaks tool execution or the request) |
| Recording at `finalize_tool_call` from the 020 stamps, no history scanning | Extension unit tests (fixture message + context; stale history present but not recorded) + source inspection |
| Tool totals (total, calls, average — raw + formatted) stamped alongside the LLM totals and projected | Extension unit tests + integration test (public assistant metadata carries both total sets) |
| Tool totals via config-selected status-bar elements and report columns | UI element tests (breakdown modes) + app plugin report tests |
| Tool duration separate from LLM duration in store, fields, and report | Distinct tables and distinct field prefixes asserted; the report renders separate columns; no code path adds tool time into an LLM total |

### Additional implementation verification

- The tool seam never mutates the message (returned unchanged — asserted in unit tests).
- Multiple sequential calls correlate per call id with no cross-call leakage (mirrors the 020 hook tests; re-asserted at the store level).
- Suites after the sweep: duration-tracking (default + integration), core, application, timestamp-extension green; ruff/black clean; pyright introduces no new findings.

## Implementation Notes

- 2026-09-23: Executed chunks 1–6 immediately after 010, test-first per chunk, on the same package. `record_tool_duration`, `tool_session_totals`, and the tool columns in `top_sessions`/`top_projects` (LEFT JOIN over a pre-aggregated `tool_durations` subquery; groups without tool rows report zero) landed in `duration_store.py`; `overall_totals` grew `tool_call_count`/`tool_total_ms` via one four-subquery SELECT.
- The `finalize_tool_call` seam reads the stamps from the core message `metadata` and the call facts from the context (`session_id`, `request_id`, `tool_call_id`, `tool_name`, `tool_plugin`, `tool_error`), config from `context["config"]` with a `state["config"]` fallback, and returns the message and state unchanged. The record-source predicate is the same full stamp triple as the LLM seam.
- Plan deviation (chunk 6): the integration "failed call" scenario uses an unregistered tool name instead of the no-handler-after-inspection path. Framework reality: the inspect-failure path provides no timing facts, so `DurationExtension` stamps nothing (no fabricated values) and the tracker correctly records no row — the integration test `test_unregistered_call_records_no_tool_row` asserts exactly this end-to-end (error tool message present, no stamps, no row, tool totals count only the measured call). The stampable failure path (registered-but-unresolved handler, which carries facts + `tool_error`) is covered at unit level with the real context fact shape (`test_finalize_tool_call_records_error_rows`); arranging it in the integration harness would need a registered-but-disabled tool.
- Open question resolved: `tool_session_totals` does not return an `error_count` — the report does not surface an error count in v1; the `tool_error` column stays queryable in SQLite.
- Tool totals stamp at request finalize alongside the LLM totals (one query pass each, one stamp pass), zeros included; the average and formatted call count only appear when calls exist (mirroring the LLM fields and cost).
- UI element order: `totals` mode = total, requests, tools, tool calls; `averages` mode = total, requests, average, tools, tool calls, tool average.
- Suite results: package 80 passed (74 default + 6 integration), pyright 0 errors, ruff/black clean. Core (569), application (422 + 1 known pre-existing failure), and timestamp-extension (26) results stand from the 010 sweep — `git status` confirmed no files outside `plugins/duration-tracking` and the task files changed in between.

## Completion Notes

- Outcome: 025 complete (2026-09-23). Tool-call duration rows record into the same store (`tool_durations`, composite-unique on `(working_directory, session_id, request_id, tool_call_id)`, best-effort, synthesized-error rows carry `tool_error`, NULL-id calls record without dedup), recorded at `finalize_tool_call` from the 020 stamps with no history access. Store-backed tool session totals (`tool_duration_session_total`, `_calls`, `_average` — raw + formatted) stamp alongside the LLM totals at request finalize and project through `from_native_messages`. The `duration_breakdown` config selects the tool status-bar elements (`tools:`, `tool calls:`, `tool average:`), and the report renders overall tool lines plus a separate `Tools` column in both top tables — tool time is never merged into an LLM total.
- Requirement evidence: all five requirements verified per the plan's verification table — store unit tests (composite dedup, per-session filtering, coercion), extension unit tests (recording from stamps, unstamped/disabled/best-effort negatives, error rows, unchanged message+state), UI element tests (both breakdown modes with tool elements in order), app plugin report tests (overall tool lines, `Tools` columns, zero-tool sessions), and 3 integration tests through the real `AgentApplication.send_request` path (one LLM + one tool row per single-call turn; two calls → two rows with matching stamps and aggregated totals; unregistered call → no stamps, no fabricated row).
- Verification performed: package suite + pyright + ruff/black after the final chunk; the core/application/timestamp suites stand from the 010 sweep (no files outside the package changed). Nothing blocked.
- Plan deviations and findings: the failed-call integration scenario (recorded in Implementation Notes) — the no-fabrication contract is what the public path actually guarantees for unregistered calls.
- Unresolved/deferred: none for 025. Phase 2 (010 + 025) is complete; 030 (human time telemetry, report-only) is next, then 040 (docs pass).

## Task relations

- Split out of `tasks/20260922-duration-and-human-time-tracking/020-tool-call-duration.md` (user decision, 2026-09-22) so only the store-dependent scope depends on 010.