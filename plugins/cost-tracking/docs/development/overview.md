# Cost tracking plugin

Generic, provider-agnostic cost tracking for the Crystal Lattice platform.

Cost-aware providers emit the `cost_tracking` capability tag and stamp a
provider-defined cost bucket into request metadata. This plugin records one
row per request into a SQLite store, feeds the chat status bar a store-backed
session total, and exposes report and reset actions.

## Components

- `CostTrackingExtension` (provider extension, `required_tags:
  ["cost_tracking"]`): records one row per request and stamps the
  store-backed session total into message metadata
  (`cost_session_total`, `cost_session_total_formatted`,
  `cost_session_requests`).
- `CostTrackingAppPlugin` (application plugin): session actions
  **Show cost report** and **Reset cost tracking**.

## Store

Default path: `cost-tracking/cost-tracking.sqlite3` under the Crystal data
directory (`CRYSTAL_DATA_DIR`, default `~/.crystal`); override with the
`cost_tracking_db_path` config key (extension config, or
`application.cost_tracking.db_path` for the application plugin).

Tables:

- `cost_requests` — one row per request: `time`, `bucket`, `session_id`,
  `working_directory`, `model`, `response_id` (unique — re-finalize/rebuild
  paths cannot duplicate rows), token counts (`input_tokens`,
  `cached_tokens`, `cache_write_tokens`, `output_tokens`,
  `reasoning_tokens`), `estimated_cost`, and `actual_cost`.
- `cost_resets` — reset markers (`time`, `bucket`).

Cost columns: `actual_cost` holds a cost reported by the provider (for
example `usage.cost`); `estimated_cost` holds the provider's estimate when no
actual cost is available. Totals prefer the actual cost and fall back to the
estimated cost.

All writes are best-effort: failures are swallowed and never break the
request pipeline.

## Summary CSV

A growing `cost-tracking-summary.csv` is appended beside the SQLite store.
One row is appended per freshly recorded request, plus one marker row per
reset. Columns:

- `time` — same timestamp as the store row (or the reset marker time).
- `bucket` — the provider-defined cost bucket.
- `working_directory` / `session_id` / `model` — the request's project
  (workspace), session, and model.
- `cost` — the per-request cost (actual when the provider reported one,
  otherwise the estimate).
- `session_total_cost` — rolling total for the (working_directory,
  session_id) pair; factual history, not affected by resets (matches the
  footer semantics).
- `bucket_total_cost` — rolling total for the bucket since its most recent
  reset marker (matches the report semantics); reset marker rows carry
  `0.0` here with the request columns empty.

Rows are only appended for freshly inserted store rows — duplicate
response ids (re-finalize/rebuild paths) never append. CSV writes are
best-effort and never break the request pipeline or the reset action.

## Buckets

The bucket base can be altered by config (`cost_bucket`), but the final
bucket is always defined by the provider that emits the capability tag:

- `openai_responses`: `<base>-chatgpt` for the ChatGPT backend,
  `<base>-api` for the OpenAI API (default base `openai-responses`).
- `reference-openai-compatible-provider`: `<base>-<endpoint-host-slug>`
  (default base `openai-compatible`), e.g.
  `openai-compatible-api-fireworks-ai`.

## Footer total

The extension contributes a `status_bar` UI element rendering
`metadata.cost_session_total_formatted` — the cost total for the current
workspace + session id, aggregated from the store on every request. This
replaces the retired stateless per-message cumulative totals. Session totals
are factual history and are not affected by reset markers.

## Actions

- **Show cost report**: reset-aware totals per bucket and overall, with
  request counts and each bucket's last reset time.
- **Reset cost tracking**: appends a reset marker for one bucket (form
  dialog with a `bucket` text field). Subsequent report totals for that
  bucket cover only records recorded after the marker; recorded history is
  preserved.

## Configuration

Extension config keys:

- `track_costs` (boolean, default `true`): record cost rows.
- `cost_tracking_db_path` (string, optional): store path override.
- `show_cost_status_total` (boolean, default `true`): contribute the
  status-bar session total.
- `track_cost_tracking_summary_csv` (boolean, default `true`): append the
  summary CSV rows.
- `cost_tracking_summary_csv_path` (string, optional): summary CSV path
  override (defaults to `cost-tracking-summary.csv` beside the store).

Application plugin config (`application.cost_tracking`):

- `db_path` (string, optional): store path override for the report/reset
  actions when the session config does not carry one.