# Duration tracking plugin

Generic, provider-agnostic duration tracking for the Crystal Lattice
platform.

The timestamp extension's duration feature (`DurationExtension`,
`plugins/timestamp-extension`) measures each provider call and stamps
the duration facts (`duration_ms`, `duration_started_at`,
`duration_finished_at`) onto the native response owner in `_metadata`.
The owner can be an assistant message or a function/custom tool call when
there is no assistant text. This plugin records one row per measured
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
  `tool_duration_session_average_formatted`), the combined LLM + tool total
  (`duration_session_combined_total`,
  `duration_session_combined_total_formatted`). Completed assistant messages
  without tool calls additionally receive the human time total
  (`human_time_session_total`, `human_time_session_total_formatted`) and the
  completed-turn human-time delta (`human_time_turn_delta`,
  `human_time_turn_delta_formatted`).
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
- `duration_project_resets` — non-destructive report reset markers keyed by
  `working_directory`. Only the latest marker for a project affects its
  current-project report sections.

All writes are best-effort: failures are swallowed and never break the
request pipeline.

## Recording seams

- **Request rows** — the feature's `finalize` scans the round's final
  messages for the duration feature's full stamp triple
  (`duration_ms` plus both timestamps), records the row, and stamps the
  session totals onto the finals and the matching native-tail entries.
  Finalize runs once per LLM round (tool loops share one request id
  across rounds; the round stamps separate the rows). Tool-only LLM responses
  record their measured native function/custom tool-call owner once, even if
  the response has multiple calls. Executed tool outputs are excluded from
  LLM recording. Responses without measured finals (or with the duration
  feature disabled) record nothing.
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
mutates or loads sessions. Every span in a batch uses the application plugin's
`working_directory`: the explicit
`application.duration_tracking.working_directory` value when set, otherwise
the runtime `WORKING_DIR` (the absolute server launch directory). A
`session_id` is stored as an opaque telemetry identifier; it does not need to
name a currently loadable session or configured agent. The whole batch uses
the application plugin's shared database path, which defaults to the Crystal
data directory unless explicitly overridden.

Validation is all-or-none for one upload batch. If any span is malformed, the
action returns a positive `skipped` count without recording a request marker
or any spans from that batch. Frontends isolate the batch, upload valid
neighbors, and remove a singleton span that the server confirms is permanently
invalid from the active queue. A missing application working directory is a
configuration error rather than a span-level rejection.

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
  debounce 2s after a span closes, and flush when a connection becomes
  usable or the app returns to the foreground. Agent work does not defer
  telemetry uploads.
- **Failure handling.** Transient failures retain the spans for retry.
  Definitive failures (HTTP 404/400 — e.g. an unknown plugin id) retain the
  spans too, and the app shows a one-time dismissible warning banner until
  the setting changes. Transient failures retry on a fixed 30-second timer;
  a positive server `skipped` count causes the frontend to isolate the batch,
  upload and remove each accepted span, and discard singleton entries that the
  server confirms it cannot accept. Rejected span data does not imply that the
  plugin is unavailable and does not trigger that warning banner.
- **Diagnostics.** A compact section under the Global Settings telemetry
  plugin field shows collection/connection state, the open and last collected
  surfaces, pending span count, latest upload result, and a ten-row recent
  entries table with upload status, session id, end time, and duration. It
  provides Refresh and Upload now controls; Upload now closes and persists
  the open span before flushing. Uploaded history is scoped to the current app
  run, while pending entries are restored from the durable cache.

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

Factual all-time totals are plain SUM aggregations over stored durations.
Windowed reports treat LLM and tool rows as point events keyed by `time`.
Human rows are intervals: a span crossing a project reset, the seven-day
window boundary, or local midnight contributes only its overlapping portion.

### Surfacing

- The extension's `finalize` stamps `human_time_session_total` +
  `human_time_session_total_formatted` only onto a completed assistant message
  without tool calls (in its own best-effort boundary — a store failure skips
  only these fields), reading `human_time_session_totals` from the same store.
  Like the other duration fields, the total updates at request finalize:
  spans arriving between requests appear after the next request.
- The `Human time: …` status-bar element renders
  `metadata.human_time_session_total_formatted`, gated by its own
  additional-field choice.
- The same completed assistant message receives
  `human_time_turn_delta` + `human_time_turn_delta_formatted`: the difference
  between its cumulative human-time total and the previous completed
  assistant turn. Intermediate tool-call assistant messages receive no
  human-time metadata; their machine-duration metadata remains unchanged. The
  first turn uses zero as its baseline. If a prior completed turn exists
  without a usable total, or the cumulative total regresses, the delta is
  omitted rather than guessed.
- Completed-turn detection recognizes explicit tool-call lists, native
  `has_tool_calls`/`turn.has_tool_calls` flags, nonterminal
  `turn.is_terminal: false` markers, and commentary phases. The same predicate
  governs stamping, baseline selection, and public metadata projection.
- Projection of retained native history recalculates old human deltas from
  its completed-turn snapshots, overriding saved deltas that used an
  intermediate baseline. Projection of only the new finals preserves the
  delta stamped against full history. Neither path reads today's human total
  into an older message.
- The delta is an uploaded snapshot. Human spans that remain open or have not
  reached the plugin when the assistant message finalizes are reflected only
  by a later request. Repair changes the delta calculation, not the uploaded
  total saved when the message finalized.
- The report action has two intentionally different windows:
  - current-project summary, human-ranked top sessions, and LLM-ranked top
    sessions cover records after that project's latest reset (or all project
    history when it has never been reset);
  - the daily breakdown, human-ranked top 3 projects, and human-ranked top 10
    sessions across projects cover today and the six preceding local calendar
    days and ignore reset markers.
- Every ranking table shows human, LLM, and tool time. Project rankings also
  show session-less human time; session-less spans never appear as sessions.
  Human-ranked tables use human-bearing projects/sessions as their population,
  so a human-only row is retained even without an LLM call.
- **Reset duration report** derives the project from the selected session and
  appends a `duration_project_resets` marker after confirmation. Recorded rows,
  fixed seven-day views, message metadata, and status-bar session totals are
  preserved.
- User-facing diagnostics remain factual all-time collection information:
  session and session-less target readiness, shared versus separate stores,
  stored session/application totals, and the latest accepted upload. Absolute
  database paths are not displayed.

## Duration display

Three select configuration elements control presentation without changing
recording:

- `duration_primary` (**Primary duration**): `hidden`, `llm` (default), or
  `llm_tools`. LLM-only renders `LLM duration: …` from
  `metadata.duration_session_total_formatted`; combined renders
  `Duration: …` from
  `metadata.duration_session_combined_total_formatted`.
- `duration_additional_fields` (**Additional time fields**): `none`, `tools`,
  `human` (default), or `tools_human`. Tool time renders as
  `Tool duration: …`; human time renders as `Human time: …`. Selecting human
  also contributes the completed-turn `human time: …` message footer.
- `duration_statistics` (**Duration statistics**): `none` (default), `counts`,
  or `counts_averages`. Statistics use explicit labels: `LLM calls`,
  `LLM average`, `Tool calls`, and `Tool average`. Tool statistics appear
  when tools are included in the primary duration or shown separately.

All raw and formatted fields are stamped regardless of display selection.
Existing configurations remain compatible: when a new setting is absent,
`show_duration_status_total`, `show_human_time_status_total`, and
`duration_breakdown` are interpreted as legacy fallbacks. The old keys are no
longer contributed as editable UI elements.

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

The **Show duration report** session action renders explicitly labeled LLM,
tool, combined LLM + tool, and human durations; LLM/tool call counts and
averages remain separate. The current-project summary and project session
rankings start at that project's latest reset. Separate seven-day daily tables
cover the current project, the current session within that project, and all
projects. Each shows LLM, tool, and human time for seven local calendar dates
(today and the preceding six days), including zero days, plus a total row.
Project tables include session-less human time; session tables exclude it.
Human spans crossing midnight or the window boundary contribute only the
overlapping portion. Seven-day tables and cross-project rankings ignore resets.

The report retains the top 10 sessions by human time for the current project
since reset and across projects for the last seven days, the top 3 projects
by human time for the last seven days, and the current-project sessions ranked
by LLM duration since reset. Rankings show all three times. Project names resolve
from `projects.json` under the Crystal data directory. Human-time diagnostics
show factual all-time collection totals and readiness independently of these
report windows.

The action response retains `daily_totals_last_7_days` for all projects and adds
`daily_totals_project_last_7_days` and `daily_totals_session_last_7_days`, with
the same date-keyed `llm_total_ms`, `tool_total_ms`, and `human_total_ms` values.

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

The local recovery command documented in the package README previews missing
measured rounds and saved metadata corrections without writing. An optional
`--session` filter limits the database query and file repairs to that session
within the selected project. Applying
recovery backs up SQLite and changed session files, inserts only missing
rounds from each session's known tracking window, and repairs LLM cumulative
snapshots and human deltas. Unknown request/model provenance remains null;
unique provenance from other recorded rounds of the same turn is retained.
Session ids and native measurement stamps supply identity without loading an
agent. Reset markers, human spans, tool rows, and message content are preserved.
The summary CSV remains an append-only journal of the original recording
events; recovery does not regenerate it.