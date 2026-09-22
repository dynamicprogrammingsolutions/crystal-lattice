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
  `reasoning_tokens`), `estimated_cost`, `actual_cost`, and per-item cost
  columns (`input_cost`, `cached_cost`, `cache_write_cost`, `output_cost`)
  filled from the provider's `usage_cost_breakdown` when available.
  Databases created before the per-item columns existed are migrated in
  place on first open.
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

## Footer total and cost breakdown

The extension contributes `status_bar` UI elements for the current
workspace + session id, aggregated from the store on every request. Session
totals are factual history and are not affected by reset markers.

The total footer is always contributed and unchanged:
`Total: {{data}}` rendering `metadata.cost_session_total_formatted`.

The breakdown items are separate fields with separate UI elements. The
`total_usage_breakdown` config key ("Total usage breakdown") selects which
elements are contributed:

- `none` (default): only the total footer.
- `totals`: total, then one element per item — `input:`, `cached input:`,
  `cache write:`, `output:` — then `requests:`.
- `averages`: total, then `requests:`, `average:`, then one element per
  item average — `input:`, `cached input:`, `cache write:`, `output:`.

Elements are emitted in that order and the platform renders status bar
elements in list order; each element carries an `exists` condition, so
items without recorded data simply do not render (a provider that reports
only a total cost shows just the total, requests, and average).

Both variants are always stored in message metadata as separate raw and
formatted fields, regardless of the config choice (the choice only
controls display):

- `cost_session_total(_formatted)`, `cost_session_requests`,
  `cost_session_requests_formatted`,
  `cost_session_average_cost(_formatted)`
- per item (`input`, `cached`, `cache_write`, `output`):
  `cost_session_<item>_cost(_formatted)` and
  `cost_session_<item>_cost_avg(_formatted)`

Per-item costs come from the provider's `usage_cost_breakdown` metadata:
`openai_responses` computes them from the pricing snapshot or the manual
ChatGPT table (with estimated cached tokens), and the reference provider
from `token_rates` (including an optional `cache_write` rate; cache-write
cost is skipped when the endpoint does not report cache-write tokens or
no rate is configured).

## Actions

- **Show cost report**: reset-aware totals per bucket and overall, with
  request counts and each bucket's last reset time, plus the top 10
  sessions and top 5 projects by cost over the same reset-aware window
  (working directories resolved to project names via `projects.json` under
  the Crystal data directory, falling back to the raw path).
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
- `total_usage_breakdown` (string, default `"none"`, label "Total usage
  breakdown"): which breakdown status-bar elements to contribute —
  `"none"`, `"totals"`, or `"averages"`.
- `track_cost_tracking_summary_csv` (boolean, default `true`): append the
  summary CSV rows.
- `cost_tracking_summary_csv_path` (string, optional): summary CSV path
  override (defaults to `cost-tracking-summary.csv` beside the store).

Application plugin config (`application.cost_tracking`):

- `db_path` (string, optional): store path override for the report/reset
  actions when the session config does not carry one.