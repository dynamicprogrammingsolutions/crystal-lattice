Parent Task: tasks/20260922-duration-and-human-time-tracking/000-main.md

Depends On:
- tasks/20260922-duration-and-human-time-tracking/010-session-duration-store.md

# Human Time Telemetry

Track human time from frontend-reported activity spans recorded into the duration store, with ingestion via a plugin-defined action. The frontend collects activity and computes actual durations — it sends only a session id (or null, e.g. session-list scrolling) and a from/to range; the plugin consolidates overlapping spans (multiple frontends, retries) and stores each span with its duration, so reporting is simple aggregation over durations (user decision, 2026-09-24, replacing the earlier point-event design). Human time surfaces per session in the footer, similar to the other duration fields, and in the report action. The mobile frontend's collector is in scope (user decision, 2026-09-24).

## Requirements checklist

### Backend (plugin) requirements — contract simplified 2026-09-24; overlap + dedup rules corrected 2026-09-25 — completed 2026-09-25 (Phase A)

- [x] An application-plugin action accepts frontend-reported activity spans in batches via the existing `executeAction` path; no new SDK method or HTTP endpoint is added. A span is `{session_id: string|null, from: ISO-8601 UTC, to: ISO-8601 UTC}` — nothing else (no event types, no span ids, no details).
- [x] Each upload request carries a frontend-assigned request id; the plugin skips already-processed request ids (retry dedup). Range overlap rules are NOT the deduplication mechanism (user correction, 2026-09-25).
- [x] The plugin computes and stores each span's actual duration (`to − from`) alongside `from`/`to`, so reports are simple aggregations over durations (sum per session; date-based bucketing is a follow-up and will anchor on start or end time, never both).
- [x] No two rows in the store may have overlapping ranges. Overlap resolution (user correction, 2026-09-25): the first entry wins — an entry's `to` (end) time is its timestamp for priority, earlier end wins over later entries. A losing span is trimmed to its non-overlapping remainders (possibly split into multiple entries; fully-covered spans store nothing). Example: existing 8:14–8:16 and 8:18–8:19, new 8:15–8:20 (different sessions) → the new span stores as two entries, 8:16–8:18 and 8:19–8:20.
- [x] Special cases (user correction, 2026-09-25): spans with the same session key (session id equal, or both null) merge into one union entry; a session-bearing entry always beats a session-less one regardless of order — the session-less entry is trimmed against it. Example: of 8:14–8:16, 8:18–8:19, and new 8:15–8:20, if only 8:18–8:19 has a session, it is kept separate with its range intact and the two session-less entries merge around it (trimmed where they would overlap it).
- [x] Spans are recorded as rows in the same duration store; spans with a null session id (e.g. session-list activity) are stored keyed by working directory only.
- [x] Per-session human time surfaces in the footer, similar to the other duration fields: a config-selected status-bar element backed by store-backed session totals stamped as message metadata (raw + formatted), projected via `from_native_messages` — the same mechanism as `duration_session_total`.
- [x] The report action includes the per-session human time total.
- [x] The span contract (action shape, request id, span schema, batching, overlap rules) is documented.
- [x] Ingestion is best-effort: telemetry failures never break requests, saves, or the report.

Dropped by the 2026-09-24 simplification (superseding earlier approved requirements): the review/composition split, per-message composition data (correlation ids), the four event types, per-span event ids, and the server-side max-idle threshold (span closing moves to the frontend).

### Frontend (mobile app) requirements — scope added 2026-09-24

- [x] The frontend collects activity and turns it into actual durations: an activity burst opens a span, inactivity closes it (from = first activity, to = last activity); spans carry the session id of the screen the user was active on, or null for session-less surfaces (e.g. the session list).
- [x] The frontend stores spans in its cache and they are not lost until successfully uploaded: spans persist across app restarts, and failed uploads retain every span for retry.
- [x] Each upload batch carries a request id that stays stable across retries of that batch (server-side request-id dedup makes retries idempotent); a new batch gets a new id.
- [x] Uploads are efficient and reliable on mobile: closed spans upload in debounced batches (not per span) without waiting for agent work, pending spans flush when the connection becomes usable and when the app foregrounds, and transient failures retry on a fixed timer (superseded by approved follow-up 035 on 2026-09-24).
- [x] A frontend setting — in the global settings surface, alongside the font-size choices — opts the user in to time tracking, and a frontend-owned configuration right under it names the telemetry plugin id (defaulting to the plugin name), because users own the plugins they enable (user decision, 2026-09-24).
- [x] If time tracking is enabled but the plugin is not enabled or not working (the upload action fails definitively), the app warns the user once through the standard notification display developed for plugin-emitted notifications (the top orange warning banner, not a popup); transient failures retry silently (user decision, 2026-09-24).
- [x] The frontend uploads through the existing `executeAction` path.
- [x] Desktop and terminal collectors remain follow-up consumers of the same contract (explicit exclusion).

## Supporting details

### Facts

- Frontends already call `executeAction({pluginId, actionId, inputs})` through the `AgentBackend` interface (`packages/frontend-sdk/src/backend/backend.ts`); the cost report/reset actions already flow through this path including bridge/mobile usage. No SDK change is needed for the action transport.
- The duration-tracking app plugin (from 010) is the host for the ingestion action; the store resolution is shared (`_db_path`).
- The footer/status-bar mechanism: store-backed session totals are stamped as raw + formatted message metadata at request finalize and projected via `from_native_messages`; config-selected status-bar elements render them (`duration_session_total` pattern from 010 — the human-time element mirrors it).
- The standard notification display for plugin-emitted notifications: `emitDisplayPresentation` + `normalizeDisplayEnvelope` → `DisplayEnvelope` pipeline → `NotificationBannerHost` banner rail (`applicationNotificationsController.ts`); client-side warnings use the identical path.
- The transport decision is approved: plugin-defined action. Discovery is frontend-owned explicit configuration (user decision, 2026-09-24, resolving the review below). The generic telemetry endpoint with plugin-defined hooks that are also actions was reviewed and recorded as a possible future framework generalization, not v1 scope (see parent task).

### Design points to pin in this subtask's plan

- Span schema: `{session_id: string|null, from: ISO UTC, to: ISO UTC}` per span; the batch is `{spans: [...]}` (session id is per span because batches may mix session and session-less activity).
- Overlap consolidation: spans for the same `(working_directory, session_id)` that overlap or touch merge into one (min from, max to, recomputed duration); a retried span is just an overlapping span, which makes retries idempotent without ids.
- Working-directory resolution: spans with a session id resolve the session's working directory (matching LLM/tool rows); null-session spans use the application-level working directory (plugin config override → app config → the store default base).
- Span validation: `from ≤ to`, both parseable (tolerant ISO), duration computed server-side; malformed spans skip with counts; batch cap (1000 spans).
- Footer element: `Human time: {{data}}` reading `metadata.human_time_session_total_formatted`, config-gated like the other duration fields (show toggle defaulting on); the extension stamps the raw + formatted totals at finalize from the store.
- Report: a human-time line in the session report (simple SUM); date-based reports are a follow-up.
- Frontend collector scope: the mobile app's collector is in scope (user decision, 2026-09-24) — span tracking, durable caching, batched non-conflicting upload, opt-in setting, and collectors (chat screen and session-less surfaces); the desktop and terminal collectors remain follow-up work consuming the same contract.
- Frontend collection outcomes (user, revised 2026-09-24 in follow-up 035): spans must be stored at the frontend and not lost until successfully uploaded; upload is debounced and batched, does not wait for ordinary agent work, flushes on foreground/connection availability, and retries transient failures; an opt-in setting in the global settings surface gates tracking.

## Execution plan — Phase A: backend telemetry (store, ingestion, report)

Status: Approved (user, 2026-09-25 — the revised span contract with request-id dedup and the no-overlap/first-entry-wins rules, including both interpretation points as presented; execution starts at chunk 1).

Phase 3: human time telemetry on the landed `plugins/duration-tracking` package. The frontend computes activity durations (spans) and reports them through a plugin-defined action on the existing `executeAction` path; the plugin dedups by request id, resolves range overlaps (no two rows ever overlap), stores spans with their durations, and human time surfaces per session in the footer (like the other duration fields) and in the report. No SDK or HTTP endpoint changes (all transport surfaces exist and are verified below).

### Data contract: what is sent, and where/how the duration is constructed (user design, 2026-09-24; dedup/overlap corrected 2026-09-25)

**What the app sends** — one `executeAction` call per batch, nothing else:

```
executeAction({
  pluginId: "<telemetry plugin id from the frontend setting>",  // default "duration_tracking_app"
  actionId: "record_human_time_spans",
  actionOwner: "application",
  inputs: {
    request_id: "req-7f3a...",   // frontend-assigned; stable across retries of this batch
    spans: [
      { session_id: "s-abc123", from: "2026-09-24T10:00:00.000Z", to: "2026-09-24T10:05:12.480Z" },
      { session_id: null,       from: "2026-09-24T10:06:01.000Z", to: "2026-09-24T10:07:30.000Z" },
    ],
  },
})
```

- A span is exactly `{session_id, from, to}` — the session the user was active on, or `null` for session-less activity (e.g. session-list scrolling); `session_id` is per span because batches may mix both.
- `from`/`to` — device-clock ISO-8601 UTC; the range of one activity burst (from first activity to last activity — the frontend closes the span on inactivity, so idle gaps never enter a span).
- **The frontend computes the actual duration** — the plugin only validates, resolves overlaps, and stores `duration_ms = to − from`.
- `request_id` — frontend-assigned per upload batch, kept stable across retries of that batch; the plugin skips already-processed request ids. **Deduplication is by request id, never by range** (user correction, 2026-09-25).
- No event types, no span ids, no details, no message content, no user identity. Batches cap at 1000 spans.

**Where the duration is constructed** — on the frontend (span closing on inactivity). The plugin adds the stored `duration_ms` per span so reports are simple aggregations (SUM of durations); date-based reports are a follow-up and will anchor on start or end time, never both.

**How double-counting is prevented** — two mechanisms, deliberately separate (user correction, 2026-09-25):

1. **Retry dedup**: the request id; a retried batch is skipped as already processed.
2. **Range overlap resolution**: no two rows in the store ever overlap. The first entry wins — an entry's `to` (end) time is its priority timestamp, so an earlier-ending entry beats a later one even when batches arrive out of order. Losing spans are trimmed to their non-overlapping remainders (possibly split into multiple entries; fully-covered spans store nothing). Special cases: same session key (session id equal, or both null) → merge into one union entry; a session-bearing entry always beats a session-less one regardless of end times. Details and the user's worked examples in the overlap-resolution model below.

### Approach

- **Host**: the existing `DurationTrackingAppPlugin` gains the ingestion action; the tracking extension gains the human-time totals stamping + footer element; the store gains the spans + processed-requests tables. No new plugin class, no manifest change; the store resolution stays shared (`_db_path`).
- **Transport**: frontends call `executeAction({pluginId, actionId: "record_human_time_spans", actionOwner: "application", inputs: {request_id, spans}})`. Verified: `execute_application_action` validates plugin/action/inputs and delegates; `request_id` is a plain validated string param, and the `spans` param declared `{"type": "array", "required": True}` passes validation because unknown param types are "accept any" (`_action_param_type_matches`), so the plugin validates the span structure itself.
- **Surfacing**: the same store-backed-totals mechanism as the other duration fields — the extension stamps `human_time_session_total` (raw + formatted) at request finalize, `from_native_messages` projects them, and a config-selected status-bar element renders `Human time: {{data}}` in the footer; the report action adds a human-time line.
- **Best-effort boundary**: malformed individual spans are skipped with counts; the action raises only on structurally invalid batches (missing/empty request id, non-list spans, batch over the size cap) — an explicit API call may fail loudly, but telemetry can never break requests, saves, or the report.

### Store design: span rows (`duration_store.py`)

New tables in the same schema block (CREATE IF NOT EXISTS — existing databases gain them on next open, no migration):

```sql
CREATE TABLE IF NOT EXISTS human_time_spans (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT,
    working_directory TEXT NOT NULL,
    from_time TEXT NOT NULL,
    to_time TEXT NOT NULL,
    duration_ms INTEGER NOT NULL,
    request_id TEXT
);
CREATE INDEX IF NOT EXISTS idx_human_time_spans_session
ON human_time_spans(working_directory, session_id);

CREATE TABLE IF NOT EXISTS human_time_requests (
    request_id TEXT PRIMARY KEY,
    processed_at TEXT NOT NULL
);
```

- `session_id` is NULL for session-less activity (project-level rows).
- `duration_ms` is computed at ingestion (`to − from`) and stored so reports are plain SUM aggregations; `from_time`/`to_time` are kept for the future date-based reports (anchored on one end, never both) and serve as the overlap-resolution keys.
- `request_id` on span rows (traceability); the `human_time_requests` table is the dedup gate — an id present there means the batch was already processed.
- Functions:
  - `record_human_time_spans(db_path, *, working_directory, request_id, spans) -> {"recorded": int, "merged": int, "skipped": int, "duplicate": bool}` — if `request_id` is already processed, returns `{"duplicate": True, ...}` without touching spans; otherwise records the request id, then validates each span (`session_id` string or null; `from`/`to` parse as tolerant ISO-8601, naive normalized to UTC; `from ≤ to`), computes `duration_ms`, and applies the overlap-resolution model below. Batch cap: 1000 spans per call (ValueError beyond).
  - `human_time_session_totals(db_path, *, working_directory, session_id) -> {"total_ms": int, "span_count": int}` — SUM of `duration_ms` for the session.
  - `human_time_project_totals(db_path, *, working_directory)` — SUM over all rows (including session-less) for future project-level use.

### Overlap-resolution model (user correction, 2026-09-25)

Invariant: **no two rows in the store ever have overlapping ranges** — SUM aggregation can never double-count.

For each incoming span S (processed in batch order), with key `(working_directory, session_id)`:

1. Find stored rows whose range overlaps S (strict overlap; touching ranges may coexist or merge per the rules below).
2. **Same session key** (row session id equals S's, including both null) → merge into one union row (min from, max to, recomputed duration).
3. **Different session keys** → the winner keeps (or extends) its full range; the loser is trimmed to its non-overlapping remainders (possibly split into multiple entries; empty remainders drop):
   - A session-bearing entry always beats a session-less entry, regardless of end times.
   - Two session-bearing entries with different sessions: the **first entry wins** — priority by the entry's `to` (end) time (earlier end wins, so late-arriving batches with earlier activity still win); ties keep the existing row (stability).
4. Merging may extend a row into fresh overlaps → iterate until the invariant holds.

Worked examples (the user's):

- Default (different sessions): existing 8:14–8:16 and 8:18–8:19; new 8:15–8:20 → the new span is trimmed to **two entries: 8:16–8:18 and 8:19–8:20**; the existing entries keep their ranges.
- Session wins: same three spans, but only 8:18–8:19 has a session → 8:18–8:19 is kept separate with its range intact; the two session-less spans merge into one union and are trimmed where they would overlap the session-bearing entry (final: 8:14–8:18 and 8:19–8:20 session-less, plus the untouched 8:18–8:19).

### Ingestion action

`record_human_time_spans` on `DurationTrackingAppPlugin`:

- `get_actions` addition: `{"id": "record_human_time_spans", "inputs": {"request_id": {"type": "string", "required": True}, "spans": {"type": "array", "required": True}}}`. No session-action UI element — this is a machine-facing action frontends call directly.
- `execute_action` resolves the store via the existing `_db_path` (plugin config → default; per-span session config overrides when the span carries a session id) and the working directory per span: spans with a `session_id` load that session's resolved config (matching how LLM/tool rows are keyed); null-session spans use the application-level working directory (plugin config override → app config → the store default base).
- Returns `{"recorded": N, "merged": M, "skipped": K, "duplicate": bool}` — no display payload.

### Footer element + report line

- **Extension stamping**: `DurationTrackingExtension.finalize` additionally queries `human_time_session_totals` and stamps `human_time_session_total` + `human_time_session_total_formatted` alongside the existing duration totals (same `_attach_internal_md` pattern; best-effort — a store failure skips the fields, never the request).
- **Status-bar element**: `Human time: {{data}}` reading `metadata.human_time_session_total_formatted`, gated by a config key mirroring the others (`show_human_time_status_total`, default on), contributed in element-list order next to the other duration fields.
- **Projection**: `from_native_messages` projects the two new fields like the other session totals.
- **Report**: `show_duration_report` gains a `- Human time: X` line for the current session (simple SUM; shown when a total exists). Top sessions/projects tables stay LLM + tool; human columns are deferred with the date-based reports.

### Test-first chunks

Each chunk: tests first (red), implement, green.

1. **Store: span rows + request dedup + overlap resolution + totals** — red: `test_duration_store_unit.py` additions (`record_human_time_spans` batch recording; request-id dedup (same id → `duplicate`, spans untouched); the user's worked examples (default trim into two entries; session-wins with session-less merge-and-trim); same-session union merge; session-less vs session-bearing trim both directions; different-session first-entry-wins by end time (including a late-arriving batch with an earlier end winning); fully-covered span stores nothing; touching spans; malformed-span skipping; `from > to` skipping; duration computation; batch cap; `human_time_session_totals` SUM; `human_time_project_totals`). Green: the store additions.
2. **Ingestion action** — red: `test_duration_tracking_app_plugin_unit.py` additions (happy-path batch via `execute_action`, missing request id raises, per-span working-directory resolution (session spans vs null-session spans), malformed batch shapes raise, per-span skipping counts, duplicate request id returns `duplicate` without changes, unknown session skips that span). Green: the action.
3. **Extension stamping + footer element + projection** — red: extension unit tests (finalize stamps `human_time_session_total` raw + formatted from the store alongside the other totals; store failure skips the fields; `from_native_messages` projects them) + UI-element tests (the `Human time:` element, config gate, ordering next to the other duration fields). Green: the extension + element changes.
4. **Report line** — red: report tests (human-time line renders from seeded spans, absent without spans). Green.
5. **Integration** — red: `test_duration_tracking_agent_application_integration.py` additions (ingest spans through `app.execute_application_action` — the same entry the HTTP route uses; assert resolved rows per the overlap rules, request-id dedup on a retry, finalize-stamped message metadata carrying the human-time total, and the report line). Green.
6. **Docs + sweep** — extend `README.md` + `docs/development/overview.md` with the span contract (frontend-owned plugin id configuration, action shape, request id and dedup, span schema, batching, overlap-resolution rules with examples, footer element, report line); full sweep: package suite, ruff/black/pyright; core/application/timestamp suites only if files outside the package change (they should not — no framework changes in this subtask).

### Implementation decisions and open questions

- Resolved — contract (user, 2026-09-24): frontend-computed spans `{session_id|null, from, to}`; no event types/span ids/details; the plugin stores `duration_ms`; reporting is simple SUM aggregation; date-based reports are a follow-up (anchored on start or end, never both).
- Resolved — dedup and overlap rules (user correction, 2026-09-25): request-id dedup (frontend-assigned, stable across retries; the plugin skips processed ids); range overlap is NOT the dedup mechanism. No two rows ever overlap: first entry wins by end-time priority (earlier `to` wins; ties keep the existing row); losers trim to non-overlapping remainders (possibly split); same session key (equal session ids or both null) merges into a union entry; session-bearing always beats session-less regardless of end times.
- Resolved — dropped by the simplification (superseding earlier approvals): the review/composition split, per-message composition data, the four event types, per-span event ids, and the server-side max-idle threshold (span closing is a frontend concern).
- Resolved — surfacing (user, 2026-09-24): per-session human time in the footer similar to the other duration fields (store-backed totals stamped as message metadata + config-selected status-bar element) plus a report line — superseding the earlier "report action only, no status-bar elements" decision.
- Resolved — discovery (user, 2026-09-24): no server-side discovery element; the frontend owns an explicit telemetry-plugin configuration defaulting to the plugin name (see the discovery review outcome below).
- Resolved — timestamps: tolerant parsing (`Z` suffix, naive → UTC); device-clock values; an entry's `to` time doubles as its priority timestamp.
- Resolved — batch cap 1000 spans per call (ValueError beyond); per-span failures skip with counts, never raise.
- Open (minor, pin during chunk 1): whether touching (non-overlapping) ranges of different sessions stay separate or merge — proposal: stay separate (only true overlap triggers resolution; same-key touching merges since they share the session key).
- Open (minor, pin during chunk 2): whether the ingestion result envelope should also echo the resolved `working_directory` for frontend diagnostics — proposal: include it; harmless and useful.
- Open (minor, pin during chunk 3): whether the footer also surfaces a session-less (project-level) total somewhere, or session-less spans surface only in future project/date reports — proposal: v1 shows only the per-session total; session-less spans are stored for the follow-up reports.

### Documentation

- `plugins/duration-tracking/README.md` + `docs/development/overview.md`: the span contract — frontend-owned plugin id configuration, action shape, request id and dedup, span schema, batching, overlap-resolution rules with the worked examples, stored duration, footer element, report line, and the frontend collector boundary (mobile in scope per Phase B; desktop/terminal follow-up consumers).
- 040 later does the cross-subtask documentation pass.

### Task checklist

- [x] Plan approval for the revised span contract (user, 2026-09-25 — including both interpretation points)
- [x] Chunk 1: store span rows + request dedup + overlap resolution + totals (red/green — 22 store tests green; same-session merge keyed by session id across working directories, pinned by test)
- [x] Chunk 2: ingestion action (red/green — per-span session/plugin-config resolution, request-id dedup, unknown-session and session-less-without-config skipping, batch shape errors)
- [x] Chunk 3: extension stamping + footer element + projection (red/green — `human_time_session_total` raw+formatted stamped in its own best-effort boundary; `Human time:` status-bar element with its own `show_human_time_status_total` gate; prefix projection)
- [x] Chunk 4: report line (red/green — `- Human time:` line shown when spans exist, `human_time` in the result envelope, best-effort)
- [x] Chunk 5: integration through the public action path (red/green — `execute_application_action` ingestion with per-span resolution, request-id dedup, same-session merge, session untouched; footer metadata + report line asserted end to end)
- [x] Chunk 6: span contract docs + full sweep (README + overview contract sections; 118 package tests green; ruff/black/pyright clean; no files outside the package changed, so no cross-package suites required)
- [x] Update the parent task's requirement checkboxes for the 030 scope (scope-change text updated 2026-09-24/25; the parent requirement stays open until Phase B lands the frontend collector)

## Implementation Notes (Phase A — executed 2026-09-25)

- All six Phase A chunks landed test-first; 118 package tests green (22 new store tests, 8 ingestion-action tests, 5 extension/projection tests, 6 UI-element tests updated/added, 2 report tests, 2 integration tests), ruff/black/pyright clean, no files outside `plugins/duration-tracking` changed.
- **Session identity decision (chunk 1)**: same-session merge matches by session id across working directories — "the same session" is the session id, not the `(working_directory, session_id)` key; a later batch resolving the same session under a different working directory consolidates the union under the incoming resolution (pinned by `test_human_time_same_session_merges_across_working_directories`). Session-less rows merge only within the same working directory.
- **Resolved open questions**: touching ranges of different sessions stay separate (only strict overlap triggers resolution; same-session touching merges) — pinned by `test_human_time_touching_different_sessions_stay_separate`; the ingestion envelope does NOT echo a working directory (per-span resolution makes a single echo misleading) but adds an `absorbed` count (valid spans fully covered by winning entries) beyond the planned shape; v1 footer shows only the per-session total (session-less spans surface in future project/date reports).
- **Session-less spans need a configured working directory**: there is no framework-level application working directory, so session-less spans resolve `application.duration_tracking.working_directory`; without it they skip (documented in the contract section).
- The human-time status-bar element has its own gate `show_human_time_status_total`, independent of `show_duration_status_total` (both default on).
- The report line shows when `span_count > 0`; the report envelope carries `human_time` (totals dict or None).
- The human stamping lives in its own best-effort boundary inside `_record_and_build_metadata`: a store failure skips only the `human_time_session_*` fields, never the duration fields or the request.

### Requirement verification

| Requirement | Evidence |
|---|---|
| Span ingestion via the existing `executeAction` path; no new SDK method or endpoint | Integration test calls `app.execute_application_action` (the HTTP route's entry) with a span batch; no SDK/server diffs in the change set |
| Spans are `{session_id\|null, from, to}` only; the plugin stores the computed duration | Store unit tests (duration computation, validation, skipping); action unit tests (shape enforcement) |
| Request-id dedup (retries never re-apply; range is not the dedup) | Store unit test (same request id → `duplicate`, rows untouched) + integration retry assertion |
| No overlapping rows: first-entry-wins trim, same-session merge, session-beats-session-less | Store unit tests covering the user's two worked examples + merge/trim directions + end-time priority (incl. late-arriving earlier batch) |
| Null-session spans stored keyed by working directory | Store unit test (session-less rows; project totals include them; session totals exclude them) |
| Per-session footer surfacing like the other duration fields | Extension unit tests (finalize stamps raw + formatted) + UI-element tests (config gate, ordering) + integration assertion on message metadata |
| Report includes the per-session human time total | Report unit test (line renders from seeded spans, absent without spans) |
| Span contract documented | README/overview contract sections land in chunk 6 |
| Best-effort: telemetry never breaks requests, saves, or the report | Per-span skip counts (unit), malformed-batch loudness limited to the explicit action call, stamping failure skips fields not requests |

### Additional implementation verification

- The ingestion action never mutates sessions (no save path) — asserted in the integration test (session unchanged after ingestion).
- The footer total updates at request finalize (like the other duration fields) — spans arriving between requests appear after the next request; asserted in the integration test.
- The report stays correct with zero spans (no line) and with only session-less spans (no per-session line).
- Suites after the sweep: duration-tracking green (default + integration); ruff/black clean; pyright no new findings; core/application/timestamp suites re-run only if any file outside the package changed.

## Discovery mechanism review (user-requested before implementation, 2026-09-24)

How the attachment contract targets a single plugin (verified in code):

- UI elements carry `plugin` — the app layer stamps the contributing plugin id onto every element (`get_application_ui_schema`) — plus an optional `action_owner`; `runApplicationAction` executes `executeAction({pluginId: element.plugin, actionId: element.action_id, actionOwner: element.action_owner})` (`packages/frontend-sdk/src/plugins/actionRunner.ts`).
- Attachment elements name their action plugin explicitly via `attachment_action_plugin`, falling back to the element's own `plugin` field (`resolveAttachmentActionPluginId`, `packages/frontend-sdk/src/plugins/attachmentActions.ts`). There is no settings lookup — **the element itself is the discovery surface**.
- Server-side routing: `execute_action_with_metadata` routes `action_owner == "application"` (or an app-plugin action-definition match) to `execute_application_action`, so `executeAction({pluginId, actionId, actionOwner: "application"})` deterministically targets one app plugin.

Options for the telemetry discovery:

- **Option A — settings value (as originally drafted in Phase A)**: a server-scoped element `human_time_telemetry_plugin` (string, default `"duration_tracking_app"`); the frontend reads the patched settings value or the element default.
  - Pros: user-redirectable to another plugin; visible in the settings UI.
  - Cons: a user-editable plugin id is a breakable footgun; a raw plugin-id string field is poor settings UX; the value duplicates what the element's own `plugin` field already carries.
- **Option B — element-carried plugin (attachment-contract alignment)**: the frontend finds the server-settings element by its stable key and reads its `plugin` field (stamped by the app layer = the telemetry plugin). The element's editable value is only the threshold; the plugin id is not user-editable. Under this option the separate `human_time_telemetry_plugin` element is dropped and the single `human_time_max_idle_seconds` element serves both purposes: presence = telemetry available, `plugin` = ingestion target, value = threshold.
  - Pros: exactly the attachment contract's established pattern; discovery from the UI schema alone; "plugin active" = element present; no breakable value; no extra backend element.
  - Cons: not user-redirectable without a code change.
- **Option C — hybrid**: `element.plugin` is the default; a patched `human_time_telemetry_plugin` settings value overrides it when present.
  - Pros: redirectable with a safe default.
  - Cons: two sources of truth; the raw id field still appears in the settings UI.

**Recommendation was Option B; user decision (2026-09-24) went further explicit: Option D — frontend-owned configuration.** Users own the plugins they enable, so the telemetry plugin id is a frontend-owned setting placed right under the time-tracking toggle, defaulting to the plugin name (`duration_tracking_app`). No server-side discovery element exists (Phase A contributes only the threshold element). Plugin availability is detected by failure: when tracking is enabled but the plugin is not enabled or not working (the upload action fails definitively), the app warns the user once through the normal notification path — the top orange warning banner (`emitDisplayPresentation` with `display: {presentation: 'banner', variant: 'warning'}`, rendered by `NotificationBannerHost`; verified the app already uses this path) — not a popup. Options A–C remain on record as the reviewed alternatives.

## Execution plan — Phase B: frontend collection and upload (mobile app)

Status: Approved (user, 2026-09-25 — "proceed to the next step" after Phase A landed and was committed as 72bf88c8; execution starts at chunk 1. Direction: stop before the first XCTest run for desktop approval; Detox runs do not need confirmation.)

Scope: the RN mobile app (`mobile/crystal-lattice-control-rn`) tracks user activity as spans (frontend-computed durations), buffers them durably, and uploads them in batches through the ingestion action landed in Phase A. Desktop and terminal collectors remain follow-up consumers of the same contract (explicit exclusion). Phase A lands and is tested first; this phase starts after the plugin stage is verified (user direction, 2026-09-24).

### Approach

- A new app module `src/humanTimeTelemetry/` owns span tracking, caching, scheduling, configuration, and upload. The app wires it: App.tsx provides the backend/connection/busy context; the chat screen and session-less surfaces report user activity; GlobalSettingsModal hosts the opt-in toggle and the telemetry-plugin configuration.
- **Span tracker** (the frontend computes the actual duration, per the 2026-09-24 contract):
  - A user activity (focus, scroll, typing, tap) on a surface opens a span if none is open; each subsequent activity updates the span's end; after an inactivity interval with no activity the span closes (`from` = first activity, `to` = last activity — idle gaps never enter a span) and is queued for upload.
  - Switching surfaces (e.g. chat session → session list) closes the current span and opens a new one.
  - A span carries the session id of the surface the user was active on, or `null` for session-less surfaces (e.g. the session list) — the `{session_id|null, from, to}` contract; no types, no ids, no details.
- **Cache** (`spanCache.ts`): AsyncStorage-backed (the app's existing storage mechanism), keyed per connection id; entries `{connectionId, span}`. Spans append best-effort (a storage failure drops that span, never blocks the UI) and are retained until an upload confirms them — restarts, connection switches, and upload failures never lose recorded spans.
- **Uploader** (`uploader.ts`): drains the cache in batches (cap per `executeAction` call, e.g. 100 spans — under the backend's 1000 cap; loop until drained). Each batch carries a frontend-assigned **request id that stays stable across retries of that batch** (a fresh id per new batch) — the backend's request-id dedup makes retries idempotent. Scheduling outcomes (the user's trigger ideas, stated as outcomes):
  - flush when a connection becomes usable and idle — first open defers until in-flight work settles;
  - flush after user inactivity (debounce after the last activity — the same inactivity that closes the span);
  - flush when the oldest pending span ages past a limit;
  - defer while the app reports busy (an `isBusy` callback from the app's request-status wiring);
  - on failure: keep every span with its request id, retry on the next trigger.
- **Opt-in + telemetry-plugin configuration (user decision, 2026-09-24)**: GlobalSettingsModal gains a "Time tracking" toggle (persisted app preference, default off) and, right under it, a frontend-owned "Telemetry plugin" configuration (text input, default `duration_tracking_app`) — users own the plugins they enable. Uploads target that plugin id via `executeAction({pluginId, actionId: "record_human_time_spans", actionOwner: "application", inputs: {request_id, spans}})`. Collection runs when the toggle is on.
- **One-time warning (user decision, 2026-09-24)**: when tracking is enabled but the plugin is not enabled or not working — an upload attempt fails definitively (unknown plugin / unknown action resolution failure; transient or network errors do not warn and just retry) — the app warns once through **the standard notification display already developed for plugin-emitted notifications** (verified: plugin notifications flow through `emitDisplayPresentation` + `normalizeDisplayEnvelope` into the same `DisplayEnvelope` pipeline and `NotificationBannerHost` banner rail; the client-side warning uses that identical path with `presentation: 'banner'`, `variant: 'warning'` — the top orange bar), never a popup. Once per app run; re-armed if the user changes the telemetry-plugin setting or toggles tracking off and on.
- **No SDK changes**: everything uses `executeAction` and existing storage/notification wiring.

### Test plan (user direction, 2026-09-24: e2e Detox validates the feature; unit/component tests cover the internals)

Three tiers, matching the repo's test-realism rules:

**Tier 1 — E2E Detox (the feature's integration validation; at least one test covers the real connection with the real plugin).**

New `e2e/humanTimeTelemetry.e2e.test.ts` + `detox:test:human-time:ios` / `detox:test:human-time:android` scripts (the existing per-feature Detox convention; the suite runs the real release app in a simulator):

1. **Happy path (required)**: the test setup spawns the real Python server (the repo's runner script pattern from the jest integration harness — `run_backend_server_for_ts_integration_tests.py` with a temp config enabling the duration-tracking plugin + echo provider; prerequisite: the package installed in the repo venv). The app connects via the connections UI (manual method; iOS sim reaches the host via 127.0.0.1, Android emulator via 10.0.2.2), the test enables time tracking in the global settings, opens a session, types in the composer, sends a message, scrolls the transcript (the `transcriptScroll.e2e.test.ts` pattern), waits for the natural inactivity flush, then asserts the human-time total: the footer element (from Phase A) shows a non-zero `Human time:` value on the session screen (and/or the duration report action shows the human-time line). This crosses app UI → SDK transport → HTTP server → plugin action → store → footer/report → app UI.
2. **Warning path**: with tracking enabled and the telemetry-plugin setting pointed at a non-existent plugin id, the orange warning banner appears once (and does not reappear on the next failed flush).

**Tier 2 — Component/platform tests (jest + react-native-testing-library; scrolling/typing collector behavior if the e2e cannot drive it stably, plus deterministic coverage of the span logic):**

- Span tracker: activity opens/extends a span; inactivity closes it with `from`/`to` = first/last activity; surface switch closes and reopens; session vs null-session attribution (mocked telemetry context; the e2e covers the same paths on-platform, these pin the logic deterministically).
- Settings UI: the toggle and the telemetry-plugin field render, persist, and gate collection (toggle off → no spans).
- Warning: a definitive upload failure emits the warning banner envelope exactly once; a transient failure does not; changing the setting re-arms the warning.

**Tier 3 — Unit tests (pure logic, mocked backend/storage):**

- Cache: append/load/remove-only-after-confirm, per-connection keying, restart survival (state reloaded from storage).
- Uploader: batch cap + drain loop, request id stable across retries (fresh per batch), failure retains spans, busy defers, idle/inactivity/max-age triggers fire, per-connection targeting (right backend, right plugin id, right action shape with `request_id`, `actionOwner: "application"`).
- Span tracker core: burst detection, inactivity closing, ISO-UTC timestamps, `{session_id|null, from, to}` shape.

### Test-first chunks

1. **Span tracker core + cache** — red: Tier 3 tracker/cache tests. Green: the span tracker + `spanCache.ts`.
2. **Uploader/scheduler** — red: Tier 3 uploader tests (including request-id stability across retries). Green: `uploader.ts`.
3. **Opt-in + telemetry-plugin config + warning** — red: Tier 2 settings/warning tests. Green: the GlobalSettingsModal rows + the warning emission.
4. **Span collectors + app wiring** — red: Tier 2 tracker tests at the screen level. Green: collectors + the context/provider + App.tsx wiring.
5. **E2E Detox** — red: `e2e/humanTimeTelemetry.e2e.test.ts` (both cases) + the package.json scripts; run against a spawned real server. Green: fix wiring gaps; the happy-path test passes against the real plugin end to end.
6. **Docs + sweep** — the frontend side of the contract (span collection, request ids, opt-in and plugin configuration, warning behavior, retention and batching) in the plugin README/overview and the mobile app docs; mobile jest suites green; lint/typecheck; the Detox suite runnable via its script.

### Implementation decisions and open questions

- Resolved — discovery (user, 2026-09-24): frontend-owned explicit configuration under the time-tracking toggle, defaulting to `duration_tracking_app`; no server-side discovery element; definitive upload failures trigger a one-time orange banner warning (see the review outcome above).
- Resolved — module placement: `src/humanTimeTelemetry/` in the mobile app for v1; extraction into a shared package happens with the desktop follow-up if duplication appears.
- Resolved — the frontend computes durations (spans close on inactivity); upload retries are idempotent via the request id (stable per batch across retries, fresh per batch; user correction, 2026-09-25) — not via range overlap.
- Resolved — opt-in default off; the toggle and the telemetry-plugin field live in GlobalSettingsModal alongside the display preferences and persist via the app's AsyncStorage preference wiring.
- Resolved — per-connection cache keys: spans collected on a connection upload only to that connection's backend.
- Resolved — the inactivity interval that closes a span doubles as the upload debounce (proposal: 30s; pinned during chunk 1); max span age before forced flush: 5 minutes.
- Resolved — e2e tooling: Detox (the repo's existing e2e infrastructure, iOS simulator primary, Android script provided); no new XCTest target is introduced — Detox drives the same native UI layer.
- Open (minor, pin during chunk 5): whether the e2e drives scroll via the existing transcript-scroll pattern on both platforms or covers scroll only in the component tier on one platform.

### Documentation

- `plugins/duration-tracking/README.md` contract section gains the frontend-side notes: span collection, opt-in and telemetry-plugin settings, warning behavior, durable retention and batching.
- Mobile app docs: the time-tracking setting and its behavior (what is collected, where it goes, how to disable).
- E2E docs: how to run `detox:test:human-time:ios` and its server-spawn prerequisite.

### Task checklist

- [x] Discovery mechanism decision (user, 2026-09-24 — frontend-owned explicit config; recorded in both phases)
- [x] Phase A landed and verified (dependency) (committed as 72bf88c8)
- [x] Chunk 1: span tracker core + cache (red/green — 16 tests; burst open/extend, inactivity close with from/to = first/last activity, surface switch, null-session attribution, zero-duration spans, dispose; per-connection AsyncStorage cache with serialized appends, remove-first-after-confirm, restart survival, malformed-state self-heal, 5000-span soft cap, storage-failure drop via injectable store)
- [x] Chunk 2: uploader/scheduler (red/green — 11 tests; batched drain with per-batch content-derived request ids stable across retries, busy/disabled/no-connection deferral, definitive 404/400 classification with one-shot warning hook, transient retention, close-debounce coalescing, max-age check, per-connection targeting, exact action shape)
- [x] Chunk 3: opt-in + plugin config + warning (red/green — 6 tests; `timeTrackingEnabled`/`timeTrackingPluginId` in MobileGlobalPreferences with normalize + defaults, HomeWorkspace setters + persistence, GlobalSettingsModal toggle + telemetry-plugin rows, warning banner envelope via the standard display pipeline with a stable display id; full mobile suite 239 green)
- [x] Chunk 4: span collectors + app wiring (red/green — 5 provider tests: gating by the toggle, activity→span→inactivity close→debounced upload with the exact action shape, null-session attribution, connection-open busy deferral with idle retry, one-time warning banner on definitive failure with span retention; collectors wired: composer typing + transcript scroll + send in SessionChatScreen, list scroll + row taps in SessionsScreen; provider mounted in ConnectedRoot with running-status/active-request busy derivation; full mobile suite 244 green, tsc clean)
- [x] Chunk 5: two-tier real-backend verification — COMPLETED VIA `tasks/20260922-duration-and-human-time-tracking/031-human-time-detox-e2e.md` (2026-09-24): the Jest integration tier is 3/3 green for upload → server → plugin → stored-total surfacing, retry dedup, and definitive-failure retention; the focused iOS Detox tier is green for real typing/sending and Sessions-list activity → positive session/session-less SQLite rows. The current Android APKs built, but the configured AVD blocked before assertions in Espresso root-view/ANR handling; 031 records the exact environment failure as allowed by its requirement.
- [x] Chunk 6: docs + mobile suite sweep — mobile telemetry development page and README aligned to the two-tier design; 246 unit tests, focused integration 3/3, and `tsc --noEmit` green.

### Requirement verification

| Requirement | Evidence |
|---|---|
| The frontend computes durations (spans close on inactivity; `{session_id\|null, from, to}`) | Tier 3 tracker tests + Tier 2 screen-level tests; e2e drives real activity on-platform |
| Spans stored at the frontend, not lost until successfully uploaded | Tier 3 cache tests (restart survival, remove-only-after-confirm); uploader failure test retains spans |
| Upload efficient and reliable (debounced batches, foreground/connection flush, fixed transient retry, no agent-work gate) | Follow-up 035 uploader/provider tests plus the existing real-backend integration |
| Opt-in toggle + frontend-owned telemetry-plugin config next to font sizes | Tier 2 settings tests (render, persist, gate); e2e enables tracking through the real settings UI |
| One-time orange-banner warning on definitive plugin failure | Tier 2 warning tests (once, not on transient failures, re-armed on setting change) + real-backend Jest definitive-failure classification/retention |
| Uploads via `executeAction` with a request id stable across retries | Tier 3 uploader tests (action shape, `request_id`, `actionOwner`) + real-backend Jest retry dedup + focused Detox upload into the real plugin store |
| Session-less activity (e.g. session-list scrolling) tracked with null session id | Tier 2 tracker tests + focused iOS Detox positive-duration `session_id: null` SQLite assertion |
| Desktop/terminal remain follow-up consumers | Scope statement; no desktop/terminal files in the change set |

### Additional implementation verification

- The two tiers touch at the real SQLite store: focused Detox proves app UI → collector/cache/uploader → HTTP action → plugin rows; the real-backend Jest tier starts from deterministic cached spans and proves transport → server → plugin rows → next-request metadata surfacing. Neither tier substitutes a mocked backend for its claimed boundary.
- Collection never blocks the UI: storage appends are fire-and-forget; the uploader runs off the render path.
- The mobile suite's existing tests stay green (no regressions in SessionChatScreen/GlobalSettingsModal behavior); the new e2e file follows the suite's launch-harness and platform-quirk conventions.

## Task relations

- Takes over `tasks/20260801-duration-and-stats-tracking/040-human-time-telemetry-plugin.md` and `050-human-time-tracking-plugin.md` (superseded; their JSONL buffer, read pointer, and two-plugin split are replaced by store rows and queries).

## Post-completion follow-up

Subtask
`tasks/20260922-duration-and-human-time-tracking/035-human-time-upload-and-diagnostics.md`
completed the user-approved upload simplification on 2026-09-24. Mobile
uploads no longer wait for agent work or max-age polling: closed spans upload
after a two-second debounce, pending spans flush on connection availability
and app foregrounding, and transient failures retry after 30 seconds. The
follow-up also added compact Global Settings diagnostics, user-facing
human-time diagnostics to Show duration report, and all-or-none ingestion so
positive skipped counts cannot silently drain the frontend cache.

Subtask
`tasks/20260922-duration-and-human-time-tracking/070-session-presence-and-inactivity-semantics.md`
superseded the frontend collection details on 2026-09-25. Mobile now tracks
foreground time while a session is open and creates no session-less spans;
desktop uses activity bursts that include a configurable inactivity grace
period and also creates no session-less spans. The ingestion contract remains
unchanged and continues accepting null-session spans for compatibility.