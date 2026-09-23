# Duration and Human Time Tracking

Track session LLM duration, per-tool-call duration, and human time using the store-backed method established by generic cost tracking (`tasks/20260920-generic-cost-tracking.md`): plugin-owned measurement and stats, one SQLite store keyed by `(working_directory, session_id)`, store-backed session totals stamped as separate raw + formatted message metadata fields, status-bar elements selected by config, and app-plugin report actions on the same store.

This task takes over `tasks/20260801-duration-and-stats-tracking/000-main.md` (superseded; kept for reference, its solutions are not authoritative) and replaces the dropped worktree branch `task/20260910-duration-session-total`.

## Requirements checklist

- [x] The framework provides a general plugin act-point around tool calls (execution-scoped hooks plus an append-scoped hook) with context-carried facts, and the timestamp plugin's `to_native_messages` append workaround is retired (subtask 020 — completed 2026-09-22).
- [x] Per-tool-call duration is stamped on tool-result messages and per-turn tool duration on the turn's assistant owner message by the duration measurement plugin, without a store (subtask 020 — completed 2026-09-22; turn total relocated to the assistant message by the approved follow-up).
- [x] Session LLM duration is tracked per session in a SQLite store with the cost-tracking method, replacing the history-scan session total from the dropped worktree branch (subtask 010 — completed 2026-09-23).
- [x] Tool call duration rows are recorded in the same store, and store-backed LLM + tool session totals surface through config-selected status-bar elements and the report action (subtasks 010 and 025 — completed 2026-09-23).
- [ ] Human time (review + composition) is tracked from frontend telemetry events recorded into the same store, with ingestion via a plugin-defined action; human time surfaces through the report action only, without message stamping (subtask 030).
- [ ] Documentation and config schemas cover the new plugin, fields, and any new framework contract (subtask 040).

## Open requirement questions

None. The tool-call act-point mechanism was resolved on 2026-09-22 (Direction C: execution-scoped `prepare_tool_call`/`finalize_tool_call` plus append-scoped `prepare_appended_message`, on both `ProviderExtensionPlugin` and `FeaturePlugin`); the agreed surface and all contract decisions are recorded in the 020 plan. Remaining implementation details are pinned in each subtask's plan before that subtask executes.

## Resolved direction decisions

Approved by the user on 2026-09-22 after the three-item review:

- **Item 1 — drop and reimplement**: the worktree branch `task/20260910-duration-session-total` (base 65 commits behind develop) is dropped. Its history-scan session total is the "stateless per-message cumulative sum" the cost method replaces. Reusable parts are ported: the finalize stamping shape, the `from_native_messages` projection pattern, the independent status-bar config key, and the test scenarios (multi-request tool turns, Responses-style owners, malformed metadata). `DurationExtension` stays the measurement source; a new `plugins/duration-tracking` package (store + tracking extension + app plugin, own SQLite DB) mirrors `plugins/cost-tracking`.
- **Item 2 — plugin-owned measurement and stats**: the framework must not compute tool-call durations, stamp duration fields, or record stats. It provides a general plugin act-point around tool calls (expanding the existing prepare/finalize contracts is the chosen shape) and passes raw facts (e.g. execution timestamps) via context, never by modifying messages directly. The mechanism also retires the `TimestampExtension` single-message `to_native_messages` append workaround. Resolved mechanism: Direction C, the combined contract (see 020).
- **Item 3 — transport via plugin-defined action**: frontend telemetry flows through the existing `executeAction` path; frontends discover the telemetry plugin id via a server-settings UI-schema entry. The generic-endpoint alternative is recorded as a possible future framework generalization, not v1 scope.
- **Execution phasing (user, 2026-09-22)**: 020 lands first (framework hooks, per-call and per-turn tool duration stamping, timestamp fix — no store), then 010 + 025 together (the store is designed once with both LLM and tool rows; store-backed totals for both), then 030 (human time, report-only, no message stamping). Only the store-dependent part of the original 020 scope (now subtask 025) depends on 010.

## Task relations

- SUPERSEDES `tasks/20260801-duration-and-stats-tracking/000-main.md` and its subtasks 010–070 (kept for reference; solutions re-evaluated, most replaced by the store method).
- References `tasks/20260920-generic-cost-tracking.md` as implementation base (completed; not a dependency — the implemented solution is the suitable baseline).
- SUPERSEDES the worktree branch `task/20260910-duration-session-total` (worktree `/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260910-duration-session-total`, commits `a50dbd75`, `57a4cad9`, `2e7fb801`). The worktree was removed 2026-09-23 after subtask 010 landed (salvage complete; the branch history remains in git).

## Subtasks

- [x] `tasks/20260922-duration-and-human-time-tracking/010-session-duration-store.md` (completed 2026-09-23)
- [x] `tasks/20260922-duration-and-human-time-tracking/020-tool-call-duration.md` (completed 2026-09-22)
- [x] `tasks/20260922-duration-and-human-time-tracking/025-tool-duration-store-totals.md` (completed 2026-09-23)
- [ ] `tasks/20260922-duration-and-human-time-tracking/030-human-time-telemetry.md`
- [ ] `tasks/20260922-duration-and-human-time-tracking/040-docs.md`

## Supporting details

### The cost-tracking method (baseline)

1. The measurement owner stamps per-request facts into provider-native message `_metadata` (usage/cost: provider usage extensions; duration: `DurationExtension`).
2. A tracking extension running after the measurement owner (priority-ordered; features finalize after provider + extensions) reads the stamped metadata at `process_chunk`/`finalize`, records one row per request into a SQLite store keyed by `(working_directory, session_id)` with a unique dedup key, best-effort so tracking can never break the request pipeline.
3. The same extension stamps store-backed session totals (raw + formatted, always) back into `_metadata`; `from_native_messages` projects them to public message metadata.
4. Status-bar UI elements render in element-list order; a config choice selects which elements are displayed while all fields stay stored (the `total_usage_breakdown` pattern).
5. An app plugin in the same package exposes report (and optionally reset) actions backed by the same store; the store resolves its path via config override, defaulting under `CRYSTAL_DATA_DIR` (cost precedent: `cost-tracking/cost-tracking.sqlite3`, `resolve_cost_db_path`).

### Dropped from the superseded 20260801 task

Replaced by the store method; recorded so the rationale is not rediscovered:

- Framework `stats.*` storage directory scopes (session/project/user) and `get_stats_dir` accessors (old 010) — the store under `CRYSTAL_DATA_DIR` replaces all three scopes.
- JSONL telemetry buffer, read-pointer files, and the producer/consumer two-plugin split (old 040/050) — event rows in the store replace the buffer; aggregation queries replace the read pointer.
- `session.metadata["stats"]` relocation and session-list fields keyed by it (old 030) — store-backed message metadata replaces the session stats key.
- Project/user stats file plugins with atomic JSON files (old 060) — store queries (top sessions/projects) replace them; the cost report already demonstrates the pattern.
- Per-tool-call lifecycle actions with full-session rewrite freedom, reentrant session lock, and same-thread save adoption (old 010/020) — replaced by a lighter act-point; the heavy design stays on record inside the 020 plan as a rejected alternative.
- Per-message human composition time stamped on user messages (old 050) — deferred; per-message composition data lives in the store, user-message rewriting is out of v1 scope.

### Execution order

020 → 010 + 025 → 030 → 040. Phase 1 (020) lands the framework act-points, per-call and per-turn tool duration stamping, and the timestamp fix in isolation — no store dependency, immediate message-level value, and the riskiest protocol change verified on its own. Phase 2 (010 + 025 together) designs the store once with both LLM and tool row types and lands store-backed totals for both. Phase 3 (030) is human time, report-only, using the store features from 010. Numbering keeps insertion gaps; dependencies (not numbers) express the order: 020 has no dependencies, 025 depends on 010 and 020, 030 depends on 010, 040 depends on all. Only 020 currently carries a full execution plan (its contract is agreed and awaits approval); 010, 025, 030, and 040 receive their plans for approval before their execution starts.