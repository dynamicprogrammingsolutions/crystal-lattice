# Duration tracking plugin

Generic, provider-agnostic duration tracking for the Crystal Lattice
platform.

The timestamp extension's duration feature (`DurationExtension`,
`plugins/timestamp-extension`) measures each provider call and stamps
the duration facts (`duration_ms`, `duration_started_at`,
`duration_finished_at`) onto the assistant owner message in
provider-native `_metadata`. This plugin records one row per measured
provider call (LLM round) into a SQLite store, feeds the chat status
bar a store-backed session total, and exposes a report action.

Measurement stays in the duration feature; the tracking plugin never
measures time itself. It runs after the duration feature in the feature
finalize chain (priority 210 vs. 200) so the stamps it reads are already
in place.

## Components

- `DurationTrackingExtension` (feature plugin, no capability tags — works
  for every provider): records one row per measured provider call (LLM
  round) and one row
  per executed tool call, and stamps the store-backed session totals
  into message metadata — LLM totals (`duration_session_total`,
  `duration_session_total_formatted`, `duration_session_requests`,
  `duration_session_requests_formatted`, `duration_session_average`,
  `duration_session_average_formatted`), tool totals
  (`tool_duration_session_total`,
  `tool_duration_session_total_formatted`,
  `tool_duration_session_calls`,
  `tool_duration_session_calls_formatted`,
  `tool_duration_session_average`,
  `tool_duration_session_average_formatted`), and the human time total
  (`human_time_session_total`, `human_time_session_total_formatted`).
- `DurationTrackingAppPlugin` (application plugin): the session action
  **Show duration report** and the machine-facing
  **`record_human_time_spans`** ingestion action.

## Store

Default path: `duration-tracking/duration-tracking.sqlite3` under the
Crystal data directory (`CRYSTAL_DATA_DIR`, default `~/.crystal`);
override with the `duration_tracking_db_path` config key (provider
config for the feature, `application.duration_tracking.db_path` for the
application plugin; the session config override wins over the
application-level one).

Tables:

- `duration_requests` — one row per measured provider call (LLM round):
  `time` (the round's `duration_finished_at` stamp), `session_id`,
  `working_directory`, `model`, `request_id` (grouping key — all rounds
  of a tool-loop request share it), `duration_ms`,
  `duration_started_at`, `duration_finished_at`. The partial unique
  index `(working_directory, session_id, duration_started_at,
  duration_finished_at)` means "one row per round per session", so
  re-finalize and rebuild paths cannot duplicate a round while every
  round of a tool loop records; rows without measurement stamps do not
  dedup. The count basis matches the cost store's per-response rows:
  `requests:` counts LLM calls.
- `tool_durations` — one row per executed tool call (recorded by the same
  package on the framework's `finalize_tool_call` seam): the request
  columns plus `tool_call_id`, `tool_name`, `tool_plugin`, and
  `tool_error`. The composite unique index
  `(working_directory, session_id, request_id, tool_call_id)` means "one
  row per call per request per session"; rows with a NULL key component
  do not dedup.
- `human_time_spans` — one row per resolved user-activity span: `session_id`
  (NULL for session-less activity), `working_directory`, `from_time`,
  `to_time`, `duration_ms` (computed at ingestion as `to − from`), and
  the originating `request_id`. No two rows ever overlap (see the human
  time contract below).
- `human_time_requests` — the request-id dedup gate: one row per processed
  upload batch (`request_id`, `processed_at`).

All writes are best-effort: failures are swallowed and never break the
request pipeline.

## Recording seams

- **Request rows** — the feature's `finalize` scans the round's final
  messages for the duration feature's full stamp triple
  (`duration_ms` plus both timestamps), records the row, and stamps the
  session totals onto the finals and the matching native-tail entries.
  Finalize runs once per LLM round (tool loops share one request id
  across rounds; the round stamps separate the rows). Requests without
  assistant finals (or with the duration feature
  disabled) record nothing.
- **Tool rows** — the feature's `finalize_tool_call` records from the
  per-call stamps on the tool-result message it receives in the chain;
  it reads only that message, never the session history.

## Human time telemetry

Frontends (the mobile app in scope; desktop and terminal are follow-up
consumers of the same contract) track user activity and compute the actual
durations: an activity burst opens a span, inactivity closes it (`from` =
first activity, `to` = last activity — idle gaps never enter a span).
Spans carry the session id of the surface the user was active on, or
`null` for session-less activity (e.g. session-list scrolling).

### Ingestion action

One `executeAction` call per batch (cap: 1000 spans per call):

```
executeAction({
  pluginId: "<telemetry plugin id>",   // the frontend's own setting,
                                       // default "duration_tracking_app"
  actionId: "record_human_time_spans",
  actionOwner: "application",
  inputs: {
    request_id: "req-…",               // frontend-assigned; stable across
                                       // retries of this batch
    spans: [
      { session_id: "s-…",  from: "2026-09-25T08:00:00Z", to: "2026-09-25T08:05:00Z" },
      { session_id: null,   from: "2026-09-25T09:00:00Z", to: "2026-09-25T09:02:00Z" },
    ],
  },
})
```

The action returns span-level counts
(`recorded`, `merged`, `skipped`, `absorbed`, `duplicate`) and never
mutates sessions. Working-directory resolution: spans with a session id
load that session's resolved config (the same keying as the LLM/tool
rows; unknown sessions skip); session-less spans use the
`application.duration_tracking.working_directory` config value — without
it they cannot be keyed and skip.

### Frontend collection (mobile)

The mobile app owns collection (see its
`docs/development/human-time-telemetry.md` for module ownership):

- **Opt-in.** Collection is off by default; the `Time tracking` toggle in
  the app's global settings enables it. The telemetry plugin id is a
  frontend-owned text setting next to the toggle (default
  `duration_tracking_app`) — the frontend does not discover the plugin.
- **Spans.** Composer typing, transcript scrolling, and sending record
  activity on the open session; session-list scrolling and row taps record
  session-less activity (`session_id: null`). An activity burst opens a
  span; 30s of inactivity closes it; leaving the foreground closes the
  open span.
- **Retention and batching.** Spans persist in per-connection AsyncStorage
  until the backend confirms the batch, so restarts and failed uploads do
  not lose data. Uploads batch up to 100 spans per call with a
  content-derived `request_id` (stable across retries, fresh per batch),
  debounce 2s after a span closes, force-flush spans older than 5 minutes,
  and defer while a request is running on that connection.
- **Failure handling.** Transient failures retain the spans for retry.
  Definitive failures (HTTP 404/400 — e.g. an unknown plugin id) retain the
  spans too, and the app shows a one-time dismissible warning banner until
  the setting changes.

### Deduplication and overlap rules

Two separate mechanisms:

- **Retry dedup is by request id, never by range.** Each batch carries a
  frontend-assigned `request_id` that stays stable across retries of that
  batch; a processed id returns `duplicate: true` without touching spans.
- **No two stored rows ever overlap.** The first entry wins — an entry's
  `to` (end) time is its priority timestamp, so an earlier-ending entry
  beats a later one even when batches arrive out of order (ties keep the
  existing row). A losing span is trimmed to its non-overlapping
  remainders (possibly split into several entries; fully-covered spans
  store nothing). Special cases: spans of the same session (equal session
  ids, matched across working directories) merge into one union entry,
  and a session-bearing entry always beats a session-less one regardless
  of end times.

Worked example (different sessions): existing 8:14–8:16 and 8:18–8:19, a
new 8:15–8:20 stores as two entries, 8:16–8:18 and 8:19–8:20. If only
8:18–8:19 has a session, it keeps its range and the two session-less
entries merge around it (8:14–8:18 and 8:19–8:20).

Because `duration_ms` is stored per row, reports are plain SUM
aggregations over durations; date-based reports are a follow-up and will
anchor on start or end time, never both.

### Surfacing

- The extension's `finalize` stamps `human_time_session_total` +
  `human_time_session_total_formatted` onto the assistant message
  metadata (in its own best-effort boundary — a store failure skips only
  these fields), reading `human_time_session_totals` from the same store.
  Like the other duration fields, the total updates at request finalize:
  spans arriving between requests appear after the next request.
- The `Human time: …` status-bar element renders
  `metadata.human_time_session_total_formatted`, gated by its own
  `show_human_time_status_total` config toggle (default on; independent
  of `show_duration_status_total`).
- The report action includes a `- Human time: …` line for the current
  session, shown when spans were recorded.

## Status bar

The `Total duration: …` element renders
`metadata.duration_session_total_formatted` and the `Human time: …`
element renders `metadata.human_time_session_total_formatted` (its own
`show_human_time_status_total` gate). The `duration_breakdown`
config select (`none` / `totals` / `averages`) adds `requests:` and
`average:` elements for the LLM totals plus `tools:`, `tool calls:`, and
`tool average:` elements for the tool totals; all fields are always
stored in message metadata and the config only selects which are
displayed. The `show_duration_status_total` toggle gates the duration
status-bar elements without affecting recording.

## Summary CSV

A growing `duration-tracking-summary.csv` is appended beside the SQLite
store (default enabled; `track_duration_tracking_summary_csv` gates it,
`duration_tracking_summary_csv_path` overrides the location). One row is
appended per freshly recorded LLM round with the columns `time`,
`working_directory`, `session_id`, `model`, `duration`, and
`session_total_duration` (the rolling session total, matching the
status-bar semantics). Tool calls are not appended to the CSV; they live
in the SQLite store and the report.

## Report

The **Show duration report** session action renders the overall recorded
duration, request count, and per-request average, plus the overall tool
duration, tool call count, and tool average, the current session's human
time total, and the top sessions and top projects by duration with a
separate `Tools` column (project names resolve from `projects.json` under
the Crystal data directory). Tool duration is never merged into the LLM
total. Totals cover all recorded requests; there are no reset windows.

## Tests

```bash
pytest plugins/duration-tracking/tests -q
```

Unit tests cover the store, the recording/stamping/projection behavior,
the UI elements, and the report action. The integration tests run real
`AgentApplication` requests through the echo provider with the production
plugins and assert rows land in the store and totals reach the public
assistant message metadata, including across a tool-loop turn and a
session reload.