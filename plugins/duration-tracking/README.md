# duration-tracking

Generic, provider-agnostic duration tracking plugin for the Crystal Lattice
platform.

The timestamp extension's duration feature (`DurationExtension`) measures
each provider call and stamps the duration facts onto its native response
owner, including a function/custom tool call when the response has no
assistant text. This plugin records one row per measured provider call
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
project's latest reset, and reset-independent seven-day views: daily
LLM/tool/human breakdowns for the current project, current session, and all
projects, each with a seven-day total row; the top 10 sessions across projects;
and the top 3 projects. Rankings are based on human time while also showing LLM
and tool time; the current-project LLM-ranked session table is retained. Project
tables include session-less human time separately. All frontend spans use the
application plugin's server-level working directory, defaulted from runtime
`WORKING_DIR`, and its shared database; ingestion stores session ids without
loading sessions or resolving their agents. The mobile app collects the spans
behind an opt-in `Time tracking` toggle with a frontend-owned telemetry
plugin id (default `duration_tracking_app`). See
`docs/development/overview.md` for the store schema, recording seams,
the human-time span contract (including the frontend collection notes),
configuration, and the completed-turn human-time delta. The delta is stored
on the final assistant message without tool calls and compares the cumulative
uploaded human time with the previous completed turn. Intermediate tool-call
assistant messages carry machine-duration totals but no human-time metadata.
Native tool-call flags and nonterminal turn markers are recognized even when
the tool calls are separate response items. Retained history projection repairs
old human-time deltas from the completed turns' saved uploaded totals.

To recover missing LLM rounds from local session histories, preview an explicit
project and database:

```bash
python -m duration_tracking_plugins.recovery \
  --db ~/.crystal/duration-tracking/duration-tracking.sqlite3 \
  --project /absolute/path/to/project \
  --session "session-id"
```

Add `--apply` to backfill rows and repair saved duration metadata. The command
backs up the database and changed session files under the database directory's
`backups/` folder. It uses measured native stamps, deduplicates existing rounds,
and only recovers sessions and time windows already represented in that
database. It does not need the session's original agent configuration.
The optional `--session` argument limits both database recovery and metadata
repair to that session within the selected project. Omit it to recover all
tracked sessions in the project. Multiple projects can be supplied with
repeated `--project` arguments.
Files changed during recovery are left for a later run. The append-only summary
CSV is not rewritten by recovery; the SQLite reports and saved session
metadata are repaired.

## Development

```bash
python -m pip install -e "plugins/duration-tracking[dev]"
pytest plugins/duration-tracking/tests -q
```

The integration tests run real `AgentApplication` requests against the
local echo provider with the production duration feature and tracking
feature (`pytest plugins/duration-tracking/tests -m integration -q`).