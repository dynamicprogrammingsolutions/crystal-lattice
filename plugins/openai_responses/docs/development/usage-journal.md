# ChatGPT usage journal

This page describes the append-only ChatGPT usage journal: what it records,
where it lives, how the provider and usage extension write it, and how it can
be inspected by date.

## Purpose

The journal gives ChatGPT-backed usage a durable, reconstructable history:

- every captured ChatGPT rate-limit snapshot (usage-percent history, including
  reset-time changes);
- every ChatGPT-backed request's estimated usage together with the
  rate-limit snapshot observed on the same response (usage contributors);
- manual reset markers appended from the UI so usage totals can start
  counting from a chosen point.

The journal is **append-only**: records are never rewritten or truncated by
the platform. There is no automatic rotation; date-based filtering and CSV
export are the inspection path.

## File location

Default path: `auth/chatgpt-usage-journal.ndjson`, a sibling of
`auth/chatgpt-rate-limits.json`. Resolution follows the same chain as the
rate-limits file (`chatgpt_usage_journal_path` override, credentials-path
sibling, `CRYSTAL_DATA_DIR`, cwd) — see `resolve_usage_journal_path` in
`chatgpt_usage_journal.py`.

Usage files are user-owned data, so their default root is the Crystal data
directory (`CRYSTAL_DATA_DIR`, default `~/.crystal`) rather than the active
config file location (`CONFIG_DIR`), which can point at copied config assets
(for example in the cloud runtime). On a normal install both point at
`~/.crystal`, so existing files stay where they are.

## Record format

One JSON object per line (NDJSON). All records carry a UTC `timestamp`.
Snapshot and request records also carry the request's `session_id` (from the
core request context) and `working_directory` (resolved to an absolute path),
so usage contributors can be attributed per session and per workspace; both
fields are omitted when unavailable.

`rate_limit_snapshot` — appended by the provider whenever ChatGPT rate-limit
headers are captured, even if the request later fails:

```json
{
  "type": "rate_limit_snapshot",
  "timestamp": "2026-09-19T10:00:00Z",
  "source": "x-codex-headers",
  "plan_type": "plus",
  "session_id": "0e0a...",
  "working_directory": "/Users/me/Dev/project",
  "snapshots": [ { "limit_id": "codex", "primary": { "used_percent": 42.0, "window_minutes": 300, "resets_at": 1775995500 }, "secondary": null, "credits": null } ]
}
```

`request_usage` — appended by the usage extension when a ChatGPT-backed
response's usage is finalized (exactly one record per response, on both the
streaming and non-streaming paths):

```json
{
  "type": "request_usage",
  "timestamp": "2026-09-19T10:00:01Z",
  "response_id": "resp_...",
  "model": "gpt-5",
  "service_tier": "default",
  "session_id": "0e0a...",
  "working_directory": "/Users/me/Dev/project",
  "input_tokens": 1000,
  "cached_tokens": 800,
  "cache_write_tokens": 0,
  "output_tokens": 50,
  "reasoning_tokens": 5,
  "estimated_cached_tokens": 800,
  "estimated_cost": 0.001234,
  "usage": { "...": "projected raw usage payload" },
  "rate_limits": { "captured_at": "2026-09-19T10:00:00Z", "snapshots": [ "..." ] }
}
```

`cached_tokens` holds the effective cached-read count (the turn-aware
estimate for ChatGPT mode, as described in
[Cost estimation](cost-estimation.md)); `estimated_cached_tokens` records the
estimate itself. `rate_limits` carries the snapshot observed on the same
response — taken from shared provider state when available, otherwise from
the latest persisted rate-limits file — so each request's plan-limit state
(left percentage, next reset time) can be reconstructed.

`usage_reset` — appended by the `chatgpt-auth-app` reset action:

```json
{ "type": "usage_reset", "timestamp": "2026-09-19T12:00:00Z", "source": "chatgpt_auth_app" }
```

## Write path

- The provider's `_capture_chatgpt_rate_limits` (called at stream creation)
  persists the latest merged snapshot to `chatgpt-rate-limits.json` as
  before, stashes the parsed snapshots in shared provider state under
  `_openai_responses_chatgpt_rate_limit_snapshots`, and appends the
  `rate_limit_snapshot` journal record.
- The usage extension's `_build_usage_metadata` appends the
  `request_usage` record when the effective auth mode is `chatgpt`.
- Each response is journaled at most once: before appending, the extension
  skips records whose `response_id` is already present in the journal, so
  re-finalize/rebuild paths (for example a session re-render) cannot
  duplicate records.
- All journal writes are best-effort: failures are swallowed and never break
  the request pipeline.
- Journaling is ChatGPT auth mode only. API-key requests keep the existing
  per-session usage/cost behavior.

## Configuration

Usage-extension config keys:

- `cost_bucket` (string, default `openai-responses`): base name of the
  provider-defined cost bucket used by the generic cost tracking plugin. The
  provider appends the active endpoint suffix (`-chatgpt` for the ChatGPT
  backend, `-api` for the OpenAI API) to form the final bucket — for example
  `openai-responses-chatgpt`, or `openai-chatgpt` / `openai-api` with
  `cost_bucket: "openai"`. The final bucket is always defined by the provider.
- `track_chatgpt_usage_journal` (boolean, default `true`): appends request
  usage and snapshots to the journal. Set to `false` to stop journaling.
- `chatgpt_usage_journal_path` (string, optional): journal file override.
- `track_chatgpt_usage_summary_csv` (boolean, default `true`): also appends
  the simplified summary CSV row whenever a journal record is written. Set
  to `false` to write only the NDJSON journal.
- `chatgpt_usage_summary_csv_path` (string, optional): summary CSV file
  override.

## Simplified summary CSV

Alongside the journal, a simplified CSV is appended at the same time as each
journal record. Default path: `auth/chatgpt-usage-summary.csv`, a sibling of
the journal (or the `chatgpt_usage_summary_csv_path` override).

Columns:

```csv
time,working_directory,session_id,estimated_cost,total_cost,used_percent
2026-09-19T10:00:01Z,/Users/me/Dev/project,0e0a...,0.001234,0.01234,42.0
```

- `time` — the record's UTC timestamp;
- `working_directory` / `session_id` — the request's absolute workspace and
  session id (empty for reset markers);
- `estimated_cost` — the record's own estimated cost (empty for snapshots
  and reset markers);
- `total_cost` — estimated cost accumulated since the most recent reset
  marker (computed from the journal, so it includes the record being
  summarized; `0` on reset rows);
- `used_percent` — the primary-window used percent carried by the record's
  rate-limit snapshot (empty when none was captured).

Reset markers append a zeroed-`total_cost` row so the reset boundary stays
visible in the simplified view. The CSV is append-only, best-effort, and
disabled with `track_chatgpt_usage_summary_csv: false`.

## Reading the journal

`chatgpt_usage_journal.py` provides readers used by the UI report and the
inspection script:

- `iter_journal_records(path, from_dt, to_dt)` — inclusive date filtering;
- `totals_since_last_reset(path, ...)` — request/token/cost totals after the
  most recent reset marker;
- `latest_rate_limits(path, at_dt=...)` — left percentage and next reset
  time at a specific point in time;
- `percent_history(path, ...)` — chronological per-window percent entries;
- `export_journal_csv(path, target, ...)` — CSV export (one row per snapshot
  window, request, or reset).

The `chatgpt-auth-app` plugin reads the same journal with a self-contained
reader (`chatgpt_auth_app/usage_journal.py`) so the application plugin stays
dependency-free; the journal file format is the shared contract.

CLI inspection:

```bash
python plugins/openai_responses/scripts/inspect_chatgpt_usage_journal.py
python plugins/openai_responses/scripts/inspect_chatgpt_usage_journal.py \
    --from 2026-09-01 --to "2026-09-19 14:30"
python plugins/openai_responses/scripts/inspect_chatgpt_usage_journal.py \
    --at "2026-09-19 14:30"
python plugins/openai_responses/scripts/inspect_chatgpt_usage_journal.py \
    --csv out/usage.csv
```

`--from`/`--to`/`--at` accept a date (`2026-09-19`) or date and time
(`2026-09-19 14:30`) interpreted in the server's own timezone.

## Cost buckets and the generic cost tracking plugin

The provider emits the `cost_tracking` capability tag, which enables the
generic cost tracking plugin (`plugins/cost-tracking`). The usage extension
stamps the provider-defined bucket into message metadata as `usage_bucket`
(see the `cost_bucket` config key above), alongside the usage and estimated
cost metadata the cost tracking extension records. See
`plugins/cost-tracking/docs/` for the store, the footer total, and the
report/reset actions.

The usage extension no longer contributes a chat status-bar element: the
stateless per-message cumulative total (`show_usage_status_total`) was
retired in favor of the cost tracking plugin's store-backed session total,
aggregated by workspace and session id. Per-message footers (turn cost,
token cumulatives) are unchanged.

## UI

The `chatgpt-auth-app` plugin exposes session actions (gated to OpenAI
Responses sessions with `auth_mode` `auto` or `chatgpt`):

- **Show ChatGPT usage report**: totals since the last reset marker, current
  left percentage and next reset time per window, and percent-history
  summary. The report display embeds a `from`/`to` text form; the
  **Apply date range** follow-up action re-runs the report narrowed to the
  inclusive range (dates and optional times in the server's timezone).
- **Reset ChatGPT usage tracking**: appends the `usage_reset` marker after a
  confirm dialog. Journal history is preserved.
- **Show ChatGPT account status** additionally shows estimated usage
  accumulated since the last reset.