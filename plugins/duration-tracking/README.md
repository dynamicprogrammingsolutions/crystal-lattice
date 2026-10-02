# duration-tracking

Generic, provider-agnostic duration tracking plugin for the Crystal Lattice
platform.

The timestamp extension's duration feature (`DurationExtension`) measures
each provider call and stamps the duration facts onto the assistant
owner message. This plugin records one row per measured provider call
(LLM round) into a
SQLite store under the Crystal data directory, renders the store-backed
session totals in the chat status bar (aggregated by workspace + session
id), and exposes session actions for a duration report and a non-destructive
per-project report reset. The status display
has three compact choices for the primary duration (LLM or LLM + tools),
separate tool/human fields, and counts/averages. Duration is factual history:
status totals remain all-time even when the report has been reset.

It also tracks **human time**: frontends report user-activity spans
(`{session_id|null, from, to}` — the frontend computes the durations) in
batches through the `record_human_time_spans` application action; the
plugin dedups by request id, resolves range overlaps so no two stored rows
ever overlap, and surfaces the per-session human time total in the status
bar (`Human time: …`) and the report. The report also includes compact
human-time diagnostics, current-project totals and rankings since that
project's latest reset, and reset-independent seven-day views: a daily
LLM/tool/human breakdown, the top 10 sessions across projects, and the top 3
projects. Rankings are based on human time while also showing LLM and tool
time; the current-project LLM-ranked session table is retained. Project
tables include session-less human time separately. Session-less
collection defaults to the runtime `WORKING_DIR`, so it uses the same default
database without additional configuration. The mobile app collects the spans
behind an opt-in `Time tracking` toggle with a frontend-owned telemetry
plugin id (default `duration_tracking_app`). See
`docs/development/overview.md` for the store schema, recording seams,
the human-time span contract (including the frontend collection notes),
configuration, and the completed-turn human-time delta. The delta is stored
on the final assistant message without tool calls and compares the cumulative
uploaded human time with the previous completed turn. Intermediate tool-call
assistant messages carry machine-duration totals but no human-time metadata.

## Development

```bash
python -m pip install -e "plugins/duration-tracking[dev]"
pytest plugins/duration-tracking/tests -q
```

The integration tests run real `AgentApplication` requests against the
local echo provider with the production duration feature and tracking
feature (`pytest plugins/duration-tracking/tests -m integration -q`).