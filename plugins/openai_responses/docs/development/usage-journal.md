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
sibling, `CONFIG_DIR`, cwd) — see `resolve_usage_journal_path` in
`chatgpt_usage_journal.py`.

## Record format

One JSON object per line (NDJSON). All records carry a UTC `timestamp`.

`rate_limit_snapshot` — appended by the provider whenever ChatGPT rate-limit
headers are captured, even if the request later fails:

```json
{
  "type": "rate_limit_snapshot",
  "timestamp": "2026-09-19T10:00:00Z",
  "source": "x-codex-headers",
  "plan_type": "plus",
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
- All journal writes are best-effort: failures are swallowed and never break
  the request pipeline.
- Journaling is ChatGPT auth mode only. API-key requests keep the existing
  per-session usage/cost behavior.

## Configuration

Usage-extension config keys:

- `track_chatgpt_usage_journal` (boolean, default `true`): appends request
  usage and snapshots to the journal. Set to `false` to stop journaling.
- `chatgpt_usage_journal_path` (string, optional): journal file override.

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