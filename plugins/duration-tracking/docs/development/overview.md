# Duration tracking plugin

Generic, provider-agnostic duration tracking for the Crystal Lattice
platform.

The timestamp extension's duration feature (`DurationExtension`,
`plugins/timestamp-extension`) measures each provider request and stamps
the duration facts (`duration_ms`, `duration_started_at`,
`duration_finished_at`) onto the assistant owner message in
provider-native `_metadata`. This plugin records one row per measured
request into a SQLite store, feeds the chat status bar a store-backed
session total, and exposes a report action.

Measurement stays in the duration feature; the tracking plugin never
measures time itself. It runs after the duration feature in the feature
finalize chain (priority 210 vs. 200) so the stamps it reads are already
in place.

## Components

- `DurationTrackingExtension` (feature plugin, no capability tags — works
  for every provider): records one row per measured request and one row
  per executed tool call, and stamps the store-backed session totals
  into message metadata — LLM totals (`duration_session_total`,
  `duration_session_total_formatted`, `duration_session_requests`,
  `duration_session_requests_formatted`, `duration_session_average`,
  `duration_session_average_formatted`) and tool totals
  (`tool_duration_session_total`,
  `tool_duration_session_total_formatted`,
  `tool_duration_session_calls`,
  `tool_duration_session_calls_formatted`,
  `tool_duration_session_average`,
  `tool_duration_session_average_formatted`).
- `DurationTrackingAppPlugin` (application plugin): the session action
  **Show duration report**.

## Store

Default path: `duration-tracking/duration-tracking.sqlite3` under the
Crystal data directory (`CRYSTAL_DATA_DIR`, default `~/.crystal`);
override with the `duration_tracking_db_path` config key (provider
config for the feature, `application.duration_tracking.db_path` for the
application plugin; the session config override wins over the
application-level one).

Tables:

- `duration_requests` — one row per measured provider request: `time`
  (the request's `duration_finished_at` stamp), `session_id`,
  `working_directory`, `model`, `request_id` (unique — re-finalize and
  rebuild paths cannot duplicate rows), `duration_ms`,
  `duration_started_at`, `duration_finished_at`.
- `tool_durations` — one row per executed tool call (recorded by the same
  package on the framework's `finalize_tool_call` seam): the request
  columns plus `tool_call_id`, `tool_name`, `tool_plugin`, and
  `tool_error`. The composite unique index
  `(working_directory, session_id, request_id, tool_call_id)` means "one
  row per call per request per session"; rows with a NULL key component
  do not dedup.

All writes are best-effort: failures are swallowed and never break the
request pipeline.

## Recording seams

- **Request rows** — the feature's `finalize` scans the request's final
  messages for the duration feature's full stamp triple
  (`duration_ms` plus both timestamps), records the row, and stamps the
  session totals onto the finals and the matching native-tail entries.
  Requests without assistant finals (or with the duration feature
  disabled) record nothing.
- **Tool rows** — the feature's `finalize_tool_call` records from the
  per-call stamps on the tool-result message it receives in the chain;
  it reads only that message, never the session history.

## Status bar

The `Total duration: …` element renders
`metadata.duration_session_total_formatted`. The `duration_breakdown`
config select (`none` / `totals` / `averages`) adds `requests:` and
`average:` elements for the LLM totals plus `tools:`, `tool calls:`, and
`tool average:` elements for the tool totals; all fields are always
stored in message metadata and the config only selects which are
displayed. The `show_duration_status_total` toggle gates the status-bar
elements without affecting recording.

## Summary CSV

A growing `duration-tracking-summary.csv` is appended beside the SQLite
store (default enabled; `track_duration_tracking_summary_csv` gates it,
`duration_tracking_summary_csv_path` overrides the location). One row is
appended per freshly recorded request with the columns `time`,
`working_directory`, `session_id`, `model`, `duration`, and
`session_total_duration` (the rolling session total, matching the
status-bar semantics). Tool calls are not appended to the CSV; they live
in the SQLite store and the report.

## Report

The **Show duration report** session action renders the overall recorded
duration, request count, and per-request average, plus the overall tool
duration, tool call count, and tool average, and the top sessions and
top projects by duration with a separate `Tools` column (project names
resolve from `projects.json` under the Crystal data directory). Tool
duration is never merged into the LLM total. Totals cover all recorded
requests; there are no reset windows.

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