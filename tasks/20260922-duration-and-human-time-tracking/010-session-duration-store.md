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

### Facts verified after 020 landed (2026-09-23)

- 020 is complete (all chunks, follow-up included; see its Completion Notes). The stamps this subtask records from exist: `duration_ms`/`_formatted`/`duration_started_at`/`_finished_at` on tool-result messages (`finalize_tool_call`) and on the assistant owner message plus `turn_duration_*`/`turn_tool_duration_*` (`finalize`, relocated there by the 020 follow-up).
- **Tracking plugin kind constraint (material)**: `DurationExtension` is a `FeaturePlugin` (priority 200), and both the request-pipeline finalize chain and the `finalize_tool_call` hook chain run extensions before features. The duration stamps are produced by `DurationExtension` *inside those chains*, so the tracking plugin must be a **`FeaturePlugin` with priority > 200** (e.g. 210) to receive the already-stamped messages at both seams. The cost extension's shape (`ProviderExtensionPlugin`, priority 70) does **not** transfer: it reads usage stamped by the provider adapter before any finalize runs, whereas duration stamps are created in the same chain the tracking plugin reads from. A cost-style extension-kind tracking plugin would run before `DurationExtension` and record nothing.
- The `finalize_tool_call` context carries `session_id`/`request_id` (from the caller's context) plus the call facts, so tool rows have their dedup key and session identity without new plumbing; the request-pipeline state carries `_request_context` for LLM rows.
- The 020 follow-up also landed the UI-element ordering contract (effective `order` stamped by the owner, stable-sorted `get_ui_schema`), so this subtask's status-bar elements should rely on element `order` rather than list position alone.

## Execution plan

Status: Approved

This plan covers the store foundation of phase 2: the `plugins/duration-tracking` package, the SQLite store (schema for **both** row types, designed once per the phasing decision), the tracking feature recording LLM request rows and stamping store-backed LLM session totals, status-bar elements, and the report action. Subtask 025 executes immediately after this plan's chunks on the same package (tool-row functions, the `finalize_tool_call` seam, tool totals, tool UI elements, report tool columns).

### Approach

Mirror `plugins/cost-tracking` structurally; the differences are deliberate and each traces to a requirement or a verified fact:

1. **Plugin kind and priority**: `DurationTrackingExtension` is a `FeaturePlugin` with priority **210** — not the cost extension's `ProviderExtensionPlugin`/70 shape. `DurationExtension` (feature, 200) creates the duration stamps inside the feature finalize chain and the `finalize_tool_call` chain; the tracking plugin must run after it in both chains to read them (extensions finalize before features, so an extension-kind tracker would receive unstamped messages and record nothing).
2. **No capability gating**: no `required_tags` — duration is provider-independent (requirement; `DurationExtension` measures wall time itself).
3. **No buckets**: duration has no provider-defined bucket concept; the store has no bucket column and the report has no bucket section (overall totals + top sessions + top projects).
4. **Recording seams**: request `finalize` for LLM rows (duration is only known at request end; `FeaturePlugin` has no `process_chunk`), `finalize_tool_call` for tool rows (025). Requests that produce no assistant finals record no LLM row — `DurationExtension` stamps nothing in that case, and the tracking plugin records only from stamps.
5. **No resets in v1** (decision below): the report shows factual all-time totals.

### Package layout (mirrors cost-tracking)

- `plugins/duration-tracking/agent_plugin.json` — module `duration_tracking_plugins`; entries `duration_tracking_plugins.duration_tracking_extension.DurationTrackingExtension` (kind `features`) and `duration_tracking_plugins.duration_tracking_app_plugin.DurationTrackingAppPlugin` (kind `application`).
- `plugins/duration-tracking/pyproject.toml` — name `duration-tracking`, src layout, `agent_plugin.json` as a data file, pytest config with the `integration` marker (cost template).
- `src/duration_tracking_plugins/`: `duration_store.py`, `duration_tracking_extension.py`, `duration_tracking_app_plugin.py`.
- `tests/`: `test_duration_store_unit.py`, `test_duration_tracking_extension_unit.py`, `test_duration_tracking_app_plugin_unit.py`, `test_duration_tracking_agent_application_integration.py` (marked `integration`; public-path setup mirroring the cost integration test — real `AgentApplication.send_request` against a stub OpenAI Responses endpoint with the production provider and plugins).
- `README.md` + `docs/development/overview.md` (package-local; 040 does the final cross-subtask pass).

### Store design (`duration_store.py`)

Both tables land in this subtask so 025 needs no schema migration:

```sql
CREATE TABLE duration_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time TEXT NOT NULL,
    session_id TEXT,
    working_directory TEXT,
    model TEXT,
    request_id TEXT,
    duration_ms INTEGER,
    duration_started_at TEXT,
    duration_finished_at TEXT
);
CREATE UNIQUE INDEX idx_duration_requests_request_id
    ON duration_requests(request_id) WHERE request_id IS NOT NULL;
CREATE INDEX idx_duration_requests_session
    ON duration_requests(working_directory, session_id);

CREATE TABLE tool_durations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    time TEXT NOT NULL,
    session_id TEXT,
    working_directory TEXT,
    model TEXT,
    request_id TEXT,
    tool_call_id TEXT,
    tool_name TEXT,
    tool_plugin TEXT,
    duration_ms INTEGER,
    duration_started_at TEXT,
    duration_finished_at TEXT,
    tool_error TEXT
);
CREATE UNIQUE INDEX idx_tool_durations_call
    ON tool_durations(working_directory, session_id, request_id, tool_call_id)
    WHERE tool_call_id IS NOT NULL;
CREATE INDEX idx_tool_durations_session
    ON tool_durations(working_directory, session_id);
```

- The tool-durations composite key includes `request_id` because some providers reuse sequential call ids across requests within one session; the key means "one row per call per request per session". Rows with a NULL component of the key do not dedup (SQLite unique indexes treat NULLs as distinct) — acceptable, documented.
- Functions follow the cost template (`_connect`, `_ensure_schema` with a PRAGMA-based migration hook, module-level `_write_lock`, `utcnow_iso`): `resolve_duration_db_path` (`duration_tracking_db_path` config override → `CRYSTAL_DATA_DIR` → cwd fallback; default relative path `duration-tracking/duration-tracking.sqlite3`), `record_request_duration` (returns `False` on `IntegrityError` so re-finalize never duplicates), `session_totals` (LLM: `total_ms`, `request_count`), `top_sessions` (limit 10), `top_projects` (limit 5). 025 adds `record_tool_duration`, `tool_session_totals`, and the tool columns in the top queries.
- No resets table and no reset functions (decision below).

### The tracking feature (`duration_tracking_extension.py`)

`DurationTrackingExtension(FeaturePlugin)` — name `duration_tracking`, version `0.1.0`, priority 210, no `required_tags`.

- `finalize(final_messages, native_messages, state, *, context=None)`:
  1. Guard: if any final already carries `_metadata.duration_session_total`, return unchanged (already processed — the cost re-finalize guard).
  2. Find the record source: scan finals (reversed) for an assistant message whose `_metadata` carries the full `DurationExtension` stamp set (`duration_ms` int ≥ 0, `duration_started_at` and `duration_finished_at` strings). Absent → return unchanged (DurationExtension disabled or no measurement).
  3. Record one LLM row: `request_id` from `state["_request_context"]`, `working_directory` via the cost `_working_directory` helper on `state["config"]`, `model` from config, row `time` = the `duration_finished_at` stamp (actual request end; falls back to `utcnow_iso()`). Best-effort: store exceptions swallow and skip stamping.
  4. Query `session_totals` and stamp onto all finals and the matching native-tail entries (the cost `_attach_internal_md` pattern): `duration_session_total`, `duration_session_total_formatted`, `duration_session_requests`, `duration_session_requests_formatted`, `duration_session_average`, `duration_session_average_formatted`. Totals are stamped even when zero (cost stamps zero totals too); the average divides by the row count (rows only exist for measured requests).
- `finalize_tool_call` (025): records tool rows from the stamped core message; returns the message unchanged.
- `from_native_messages`: promote `duration_session_*` (and, from 025 on, `tool_duration_session_*`) from native `_metadata` to public metadata via `native_indices` (cost projection pattern, prefix scan picking the last candidate).
- `get_config_schema`: `track_durations` (boolean, default True), `duration_tracking_db_path` (string), `show_duration_status_total` (boolean, default True), `duration_breakdown` (select `none`/`totals`/`averages`, default `none`), `track_duration_tracking_summary_csv` (boolean, default True), `duration_tracking_summary_csv_path` (string).
- `get_ui_elements`: a config select for `duration_breakdown` (always contributed so the choice stays editable), then status-bar elements — `Total duration: {{data}}` (`metadata.duration_session_total_formatted`) when the show toggle is on; `totals` mode adds `requests: {{data}}`; `averages` mode adds `requests:` + `average: {{data}}` (025 extends both modes with tool elements). Elements rely on the core-stamped effective `order` (020 follow-up); no manual ordering.

### Report action (`duration_tracking_app_plugin.py`)

`DurationTrackingAppPlugin` — name `duration_tracking_app`; one session action `show_duration_report` (UI element in the app band, bar-chart icon, no dialog). Report markdown: overall totals (total duration, requests, average), top sessions (limit 10), top projects (limit 5) with project display names resolved from `projects.json` under `CRYSTAL_DATA_DIR` — the cost report shape minus buckets and resets. 025 adds the tool columns. DB path resolution mirrors the cost app plugin (session config override → plugin config → default).

### Test-first chunks

Each chunk: write the tests first, verify red, implement, verify green.

1. **Store module (LLM part)** — red: `test_duration_store_unit.py` (schema creation; path resolution override/env/cwd; record + dedup by `request_id`; `session_totals`; `top_sessions`/`top_projects`; misuse raises). Green: `duration_store.py` with both table schemas and the LLM functions.
2. **Package scaffolding** — `pyproject.toml`, `agent_plugin.json`, module init, the feature class with its config schema; a smoke test that the application loads the package's plugins.
3. **LLM recording + totals stamping** — red: `test_duration_tracking_extension_unit.py` (records from fixture stamps; re-finalize dedup via the guard + the unique index; totals raw + formatted stamped on finals and the native tail; projection via `native_indices`; no stamps → no row and no totals; `track_durations=False` → nothing; store failure swallowed; malformed stamp values skipped; no assistant finals → unchanged). Green: `finalize` + `from_native_messages`.
4. **UI elements** — red: element tests (select always present; total element gated by the show toggle; breakdown modes add the right elements with the right conditions). Green: `get_ui_elements`.
5. **Report action** — red: `test_duration_tracking_app_plugin_unit.py` (report markdown, top sessions/projects, db path resolution, missing session). Green: the app plugin.
6. **Summary CSV** — red: CSV tests (rows appended with rolling session totals, header on a fresh file, disabled by config, path override). Green: CSV helpers + the finalize hookup.
7. **Integration** — red: `test_duration_tracking_agent_application_integration.py` (real `AgentApplication.send_request` against the stub endpoint; a multi-request tool turn; assert LLM rows land, the assistant message carries the store-backed totals in public metadata after projection; malformed metadata tolerated; the show toggle and breakdown config behave independently of `duration_extension_show_duration`). Green.
8. **Docs + sweep** — `README.md`, `docs/development/overview.md`; `pytest plugins/duration-tracking/tests -q`, `pytest core/python/tests -q`, `pytest application/python/tests -q`, `pytest plugins/timestamp-extension/tests -q`; ruff/black on changed files; pyright.

Worktree salvage mapping (requirement): the finalize stamping shape and the `from_native_messages` projection follow the branch's approach but read store totals instead of scanning history; the status-bar config keys are independent of `duration_extension_show_duration`; the branch's test scenarios (multi-request tool turns, Responses-style owners, malformed metadata, independent toggles) are covered in chunks 3 and 7.

### Implementation decisions and open questions

- **Resolved in plan — no reset windows for duration v1**: time is factual history, not a budget; the report shows all-time totals. No `duration_resets` table, no reset action. Resets can be added later without breaking the schema (a new table), mirroring how cost grew its per-item columns.
- **Resolved in plan — summary CSV included, default enabled**: mirrors the cost CSV (`duration-tracking-summary.csv` beside the store; `duration_tracking_summary_csv_path` override; `track_duration_tracking_summary_csv` gate). One row per LLM request with the rolling session total; tool calls are not appended as CSV rows (they live in SQLite and the report).
- **Resolved in plan — no buckets**: no bucket column, no bucket report section.
- **Resolved in plan — row time**: the LLM row's `time` is the stamped `duration_finished_at` (the actual request end), falling back to `utcnow_iso()`; 025's tool rows use their `duration_finished_at` stamp the same way.
- **Resolved in plan — totals always stamped, zeros included**: mirrors cost; the status-bar element conditions render on existence, and zero totals are meaningful ("no time recorded yet").
- Open (minor, pin during chunk 3): the exact record-source predicate — proposal is the full stamp triple (`duration_ms` + both timestamps) to avoid mistaking foreign metadata; loosen only if a real provider flow needs it.
- No open contract decisions. The kind/priority constraint is settled fact (FeaturePlugin, 210 — see the verified facts above).

### Documentation

- `plugins/duration-tracking/README.md`: the store, config keys, metadata fields, status-bar elements and the breakdown config, the report action, the summary CSV.
- `plugins/duration-tracking/docs/development/overview.md`: architecture, recording seams, schema, and the "measurement stays in `DurationExtension`; the tracking plugin records from stamps" rule.
- 040 later verifies cross-subtask accuracy and extends the README with the telemetry contract (030).

### Task checklist

- [x] Obtain plan approval (plan moved to Approved 2026-09-23)
- [x] Chunk 1: store module — both table schemas + LLM functions (red/green)
- [x] Chunk 2: package scaffolding; plugins load (manifest smoke test)
- [x] Chunk 3: LLM recording + totals stamping + projection
- [x] Chunk 4: UI elements + config schema
- [x] Chunk 5: report action
- [x] Chunk 6: summary CSV
- [x] Chunk 7: application integration test
- [x] Chunk 8: package docs + full sweep (package 59, core 569, application 422 + 1 known pre-existing failure, timestamp-extension 26; ruff/black/pyright clean)
- [x] Remove the dropped worktree `/Users/ferenci84/Dev/Mine/ai-agent-platform-worktrees/20260910-duration-session-total` (clean, removed 2026-09-23)

### Requirement verification

| Requirement | Evidence |
|---|---|
| One row per request, keyed `(working_directory, session_id)`, deduplicated, best-effort | Store unit tests (dedup by `request_id`, `IntegrityError` path) + integration test (rows match requests across a multi-request turn) + fault-injection test (unwritable store path never breaks `send_request`) |
| Measurement stays in `DurationExtension`; the tracking plugin records from stamps | Extension unit tests feed fixture stamps only (no clock); source inspection — the tracking plugin reads stamps and rows, never measures |
| Store-backed totals (total, request count, average — raw + formatted) stamped and projected | Extension unit tests (all six fields on finals + native tail) + integration test (public assistant metadata after `from_native_messages`) |
| Status-bar elements in element order; config selects display while all fields stay stored | UI element tests (element list, conditions, show toggle, breakdown modes) + integration test (independent of the `DurationExtension` footer toggle) |
| Report action with totals and top sessions/projects | App plugin unit tests + the integration test's report invocation |
| All providers, no capability gating | No `required_tags` (asserted); integration runs through the echo provider with the production plugins; unit tests use plain fixture messages |
| Store path resolution like the cost store | Store unit tests (config override, `CRYSTAL_DATA_DIR`, cwd fallback) |
| Worktree salvage ported | Chunk 3/7 test scenarios (multi-request tool turns, Responses-style owners, malformed metadata, independent toggles) + the finalize/projection shape reading store totals |

### Additional implementation verification

- Re-finalize and native-rebuild paths do not duplicate rows (the stamp guard + the unique index, both tested).
- Concurrency: the module-level write lock serializes writers (mirroring cost); no interleaving test needed beyond cost's precedent.
- The known pre-existing failure `test_claude_system_message_helpers` (stale TASKS v5 assertion) stays out of scope.
- Suites after the sweep: `plugins/duration-tracking` (hermetic integration tests run in the default suite, mirroring cost-tracking; `-m integration` selects them), core, application, timestamp-extension all green; ruff/black clean; pyright introduces no new findings.

## Implementation Notes

- 2026-09-23: Executed chunks 1–8 in order, test-first per chunk. Package: `plugins/duration-tracking` (module `duration_tracking_plugins`; `DurationTrackingExtension` FeaturePlugin priority 210, `DurationTrackingAppPlugin` application kind).
- Record-source predicate refinement (resolves the plan's open question): the source scan does NOT require `role == "assistant"` — `DurationExtension` can select owners via `turn`/`usage` metadata without an assistant role, so the full stamp triple (`duration_ms` int ≥ 0 + both timestamp strings) is the sole discriminator. Kept strict; no provider flow needed loosening.
- Plan deviations (minor): (1) "misuse raises" store test replaced by coercion tests — `duration_requests` has no required field to validate (cost's ValueError guards its NOT NULL bucket); malformed values coerce to NULL like cost's `_coerce_int`. (2) The integration test uses the echo-provider harness from 020's `test_application_tool_duration_stamping.py` instead of a stub OpenAI Responses server — same public path (`AgentApplication.send_request`), hermetic, and proven; it covers a tool-loop request, multi-request accumulation, reload survival, and the independent footer toggle. (3) The integration tests are hermetic and run in the package's default suite (mirroring cost-tracking's pyproject, which also does not exclude them); `-m integration` still selects them.
- `DurationTrackingAppPlugin` subclasses `ApplicationPlugin` explicitly (like `DurationExtension` subclasses `FeaturePlugin`) and implements the protocol's `get_commands` no-op; the manifest smoke test checks kind via `__mro__` membership because the runtime_checkable Protocols have non-method members (isinstance/issubclass unusable at runtime; pyright rejects isinstance on them).
- The app plugin's session-action element uses `order: 14` (cost's report/reset use 12/13) so the report action groups after the cost actions in the app band.
- Suite results: package 59 passed (incl. 4 integration), core 569 passed + 26 deselected + 1 xfailed, application 422 passed + 1 known pre-existing failure (`test_claude_system_message_helpers`, stale TASKS v5 assertion, out of scope), timestamp-extension 26 passed. ruff/black clean; pyright 0 errors on the package.
- Worktree `20260910-duration-session-total` removed after the salvage was complete (clean tree, final commit `2e7fb801`).

## Completion Notes

- Outcome: 010 complete (2026-09-23). The `plugins/duration-tracking` package records one LLM request row per measured request into `duration-tracking/duration-tracking.sqlite3` (keyed `(working_directory, session_id)`, deduped by unique `request_id`, best-effort), stamps store-backed session totals (`duration_session_total`, `_requests`, `_average` — raw + formatted) onto the finals and the native tail, projects them to public assistant metadata, contributes config-selected status-bar elements, appends the summary CSV, and exposes the `show_duration_report` session action. Both table schemas (LLM + tool) landed so 025 needs no migration.
- Requirement evidence: all eight requirements verified per the plan's verification table — store unit tests, extension unit tests (recording, dedup guard + unique index, stamping, projection, malformed stamps, best-effort fault injection), UI element tests, app plugin tests, the manifest smoke test, and 4 integration tests through the real `AgentApplication.send_request` path (rows land, totals reach public metadata, accumulate across requests, survive a save/reload round-trip, work in a tool-loop turn, and behave independently of the `duration_extension_show_duration` footer toggle).
- Verification performed: full sweep listed in Implementation Notes; nothing blocked.
- Plan deviations and findings: recorded in Implementation Notes (predicate refinement, echo harness, hermetic integration in the default suite, explicit protocol subclassing).
- Unresolved/deferred: none for 010. 025 executes next on the same package (tool rows + tool totals); the pre-existing application-suite failure remains out of scope pending the user's decision.

## Task relations

- Replaces the dropped worktree branch `task/20260910-duration-session-total` (see parent task).
- Uses `tasks/20260920-generic-cost-tracking.md` as implementation base.