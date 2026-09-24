# duration-tracking

Generic, provider-agnostic duration tracking plugin for the Crystal Lattice
platform.

The timestamp extension's duration feature (`DurationExtension`) measures
each provider request and stamps the duration facts onto the assistant
owner message. This plugin records one row per measured request into a
SQLite store under the Crystal data directory, renders the store-backed
session total in the chat status bar (aggregated by workspace + session
id), and exposes a session action for a duration report. Duration is
factual history: there are no reset windows.

It also tracks **human time**: frontends report user-activity spans
(`{session_id|null, from, to}` — the frontend computes the durations) in
batches through the `record_human_time_spans` application action; the
plugin dedups by request id, resolves range overlaps so no two stored rows
ever overlap, and surfaces the per-session human time total in the status
bar (`Human time: …`) and the report. See
`docs/development/overview.md` for the store schema, recording seams,
the human-time span contract, and configuration.

## Development

```bash
python -m pip install -e "plugins/duration-tracking[dev]"
pytest plugins/duration-tracking/tests -q
```

The integration tests run real `AgentApplication` requests against the
local echo provider with the production duration feature and tracking
feature (`pytest plugins/duration-tracking/tests -m integration -q`).