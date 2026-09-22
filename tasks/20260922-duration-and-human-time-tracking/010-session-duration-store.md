Parent Task: tasks/20260922-duration-and-human-time-tracking/000-main.md

# Session Duration Store

Track per-request LLM duration in a SQLite store with the cost-tracking method and surface store-backed session duration totals, replacing the history-scan session total implemented on the dropped worktree branch `task/20260910-duration-session-total`.

## Requirements checklist

- [ ] One row per provider request is recorded in a SQLite duration store, keyed by `(working_directory, session_id)`, deduplicated per request, best-effort so tracking failures never break the request pipeline.
- [ ] Measurement stays in `DurationExtension` (its per-message and per-turn stamping is unchanged); a new tracking plugin records rows from the duration metadata `DurationExtension` already stamps.
- [ ] Store-backed session duration totals (total, request count, per-request average — raw and formatted) are stamped on the request's assistant message metadata and projected to public message metadata.
- [ ] Status-bar elements render the totals in fixed element-list order; a config choice selects which elements are displayed while all fields remain stored (mirroring the `total_usage_breakdown` pattern).
- [ ] A report action shows session duration totals and top sessions/projects by duration, backed by the same store.
- [ ] Duration tracking works for all providers, including providers without usage metadata (no capability gating, unlike the cost extension's `cost_tracking` tag).
- [ ] The store resolves its path like the cost store: config override wins, otherwise a default under `CRYSTAL_DATA_DIR`.
- [ ] The dropped worktree branch's reusable parts are ported: the finalize stamping shape, the `from_native_messages` projection pattern, the independent status-bar config key, and the test scenarios (multi-request tool turns, Responses-style owners, malformed metadata, independent UI toggles).

## Supporting details

### Facts

- `DurationExtension` (`plugins/timestamp-extension/src/timestamp_extension/duration_extension.py`) is a `FeaturePlugin` (priority 200). `initialize_request` records `duration_started_at` (ISO UTC) and `duration_started_at_mono` in shared state; `finalize` computes `duration_ms`, stamps `duration_started_at`, `duration_finished_at`, `duration_ms`, `duration_formatted`, `turn_duration_ms`, `turn_duration_formatted` (plus turn TPS when usage tokens exist) on the selected owner assistant message's `_metadata` and the matching native history entry. It does not stamp during streaming; everything is known only at request end.
- Pipeline order: provider + extensions finalize first, then the feature finalize chain (core.py:2455–2471); extensions and features are priority-sorted, lower numbers first (provider.py:222–232). A tracking feature with priority > 200 sees `DurationExtension`'s stamps in its own `finalize`.
- `FeaturePlugin` has no `process_chunk`; the tracking plugin does all recording and stamping in `finalize` (sufficient because duration is only known at request end) and projects stored fields in `from_native_messages`.
- Shared provider state carries `_request_context` with `session_id` and `request_id` (provider.py:234; the cost extension already reads `session_id` from it) — the dedup key and session identity are available without new plumbing.
- The cost-tracking package is the template: `plugins/cost-tracking/` with `agent_plugin.json` (extension + application entries), `src/cost_tracking_plugins/{cost_store,cost_tracking_extension,cost_tracking_app_plugin}.py`, package-local tests, README, docs.
- Status-bar ordering contract: `get_ui_schema` aggregates elements in plugin/list order; the terminal renders them in that order joined by two spaces — element list order is the ordering mechanism. Each element carries `data` (dotted metadata path), `template` (`{{data}}` substitution), and a `condition` (`{path, exists}`).
- The cost store's report pattern to mirror: reset-aware bucket report, `top_sessions` (limit 10), `top_projects` (limit 5), project display names resolved from `projects.json` under `CRYSTAL_DATA_DIR`.
- Worktree branch facts: base `acb4f867` is 65 commits behind develop; the whole cost-tracking plugin landed after it. Its `_sum_session_duration_ms` history scan, `_duration_extension_owner` marker, and legacy fallback are replaced by store queries; its `total_duration_ms`/`total_duration_formatted` public keys never shipped (branch unmerged), so no compatibility is needed.

### Proposed naming (pin in this subtask's plan)

- Package `plugins/duration-tracking`; store `duration_store.py`; DB `duration-tracking/duration-tracking.sqlite3` under `CRYSTAL_DATA_DIR` with a `duration_tracking_db_path` config override.
- Metadata fields mirroring `cost_session_*`: `duration_session_total`, `duration_session_total_formatted`, `duration_session_requests`(+`_formatted`), `duration_session_average`(+`_formatted`).
- Status bar: `Total duration: {{data}}` first; a `none/totals/averages`-style config selects extra elements.

### Decisions to pin in this subtask's plan

- Exact metadata/config key names (proposal above).
- Whether the duration report includes reset windows (the cost store's reset pattern is cheap to mirror; resets are less meaningful for time than for budgets).
- Whether the tracking extension also stamps a summary CSV (cost precedent exists; optional).
- Test placement: package-local unit tests plus one application-level integration test mirroring `test_cost_tracking_agent_application_integration.py`.

### Execution position and shared schema design

Per the phasing decision (2026-09-22), this subtask executes in phase 2, after 020 (framework hooks + tool-call stamping) has landed, and together with 025 (tool rows + tool totals). Consequences:

- `DurationExtension` already implements `finalize_tool_call` (020's recommended stamping owner); its LLM per-message/turn stamping is unchanged, which is what this subtask records from.
- The store schema is designed once with both row types: the LLM request-duration rows from this subtask and the tool-call-duration rows from 025 land in the same schema revision, in the same SQLite DB.
- The tracking extension hooks both recording seams: request `finalize` for LLM rows (this subtask) and `finalize_tool_call` for tool rows (025), stamping both total sets at request finalize.

## Task relations

- Replaces the dropped worktree branch `task/20260910-duration-session-total` (see parent task).
- Uses `tasks/20260920-generic-cost-tracking.md` as implementation base.