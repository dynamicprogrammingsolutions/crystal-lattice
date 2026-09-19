# Cost estimation

This page describes how the `openai_responses` bundle estimates dollar cost
for API-key and ChatGPT auth modes, including the pricing snapshot format,
token-bucket splitting, and ChatGPT-specific caveats.

## Pricing snapshot

The checked-in pricing snapshot at
`src/openai_responses_plugins/data/openai_model_pricing.json` is the runtime
source of truth for estimated dollar cost. Refresh it from the official
OpenAI pricing page with:

```bash
python plugins/openai_responses/benchmark/refresh_openai_responses_pricing.py
```

The `pricing_snapshot_path` provider config key can override the checked-in
snapshot path when needed.

## Persisted usage boundary

The provider passes the complete response `usage` object to the usage extension
as transient private metadata. The extension uses that object to calculate
token fields, cached-token estimates, cost, turn totals, service tier, and
display metadata.

Persisted core and provider-native usage metadata retains this explicit
allowlist:

- `input_tokens`
- `input_tokens_details.cached_tokens`
- `input_tokens_details.cache_write_tokens`
- `output_tokens`
- `output_tokens_details.reasoning_tokens`
- `completion_tokens_details.reasoning_tokens`
- `total_tokens`

The root fields and detail fields reported by current OpenAI Responses usage
remain inspectable, along with the compatibility completion-token reasoning
path used by the extension. Other provider usage roots and nested detail fields
are transient and are not retained in the session. This includes
ChatGPT/Codex `usage.attribution`, whose items and request fields can grow with
request history, as well as any future upstream field that has not been
adopted into the local usage contract.

Existing monolithic JSON sessions created before this behavior can be cleaned
with the maintenance command described in
[Usage persistence sanitization](usage-sanitization.md).

## Snapshot format

Each model entry has a top-level `pricing` block (the standard-tier
projection) and a `service_tiers` mapping with per-tier rates. The supported
tiers are `standard`, `batch`, `flex`, and `priority`.

Each tier pricing block has up to four token-price columns:

- `input_per_1m`: ordinary input tokens (dollars per 1M tokens)
- `cached_input_per_1m`: cached-read tokens (cache hits)
- `cache_write_per_1m`: billable cache-write tokens (GPT-5.6+; omitted on
  legacy models)
- `output_per_1m`: output/completion tokens

## Token-bucket splitting

The cost estimator splits `usage.input_tokens` into three mutually exclusive
input buckets so the same token is never charged twice:

```text
cached_read_tokens    = max(0, usage.input_tokens_details.cached_tokens)
cache_write_tokens    = max(0, usage.input_tokens_details.cache_write_tokens)
ordinary_input_tokens = max(0, input_tokens - cached_read_tokens - cache_write_tokens)
```

The estimated cost is:

```text
estimated = (
    ordinary_input_tokens * input_per_1m
  + cached_read_tokens   * cached_input_per_1m
  + cache_write_tokens   * cache_write_per_1m
  + output_tokens        * output_per_1m
) / 1_000_000.0
```

## Fallbacks and clamping

When `cache_write_tokens > 0` but the resolved pricing block has no
`cache_write_per_1m` (e.g., a legacy model with only three price columns),
the estimator falls back to `input_per_1m` for the cache-write bucket so the
model remains estimable.

When the reported detail counters are inconsistent (their sum exceeds
`input_tokens`), the estimator reduces the larger counter to fit and clamps
`ordinary_input_tokens` to zero. This keeps cost estimation deterministic and
non-negative without rejecting the whole payload.

## Implicit cache writes

GPT-5.6 implicit caching can create a billable managed cache write even when
the client does not add an explicit cache breakpoint. The estimator uses the
reported `cache_write_tokens` counter; it does not infer write tokens from
prompt shape, cache keys, or estimated cache hits.

## ChatGPT cached-token estimation

ChatGPT-backed Responses usage currently estimates cached tokens using
turn-aware heuristics. That estimate is kept separate from the raw provider
usage payload and is used for ChatGPT-mode pricing instead of any
backend-reported cached-token field. By default it is not displayed; enable
`show_estimated_cached_tokens` to show the footer.

### Estimator logic

The estimator considers user boundaries and usage-bearing assistant or
tool-call generations; tool results are ignored. Within one user turn, the
immediately previous generation's input is the cached-prefix candidate. If
that candidate is larger than the current input, the prefix is considered
invalidated by compaction or another history change and the estimate is `0`.

For the first generation after a user message, the estimator compares the
current input with both the first and last inputs from the preceding
populated turn:

- if current input is strictly greater than the previous turn's last input,
  reasoning is treated as preserved and that last input is the estimate;
- otherwise, the previous turn's first input is used as the conservative
  interleaved-reasoning estimate when it does not exceed current input;
- if even that interleaved candidate exceeds current input, the prefix is
  considered invalidated and the estimate is `0`.

The estimate is an observability and pricing heuristic, not a
provider-reported or billing-grade cache measurement. It does not expose the
inferred preserved/interleaved classification as metadata.

The same effective cached-token count and estimated cost are also appended to
the append-only ChatGPT usage journal together with the rate-limit snapshot
observed on the same response; see
[Usage journal](usage-journal.md).

## ChatGPT cost estimate caveat

ChatGPT users are generally governed by subscription limits/rate limits rather
than direct API per-token billing. The dollar value produced by this framework
is an **API-equivalent estimate** useful for comparison, not an invoice
amount.

For ChatGPT-backed requests:

- Cached-read tokens are estimated using the turn-aware heuristic described
  above; the estimate replaces `cached_tokens` for pricing.
- `cache_write_tokens` is **not** synthesized from the estimate. When the
  ChatGPT backend reports `cache_write_tokens`, the estimator prices it at the
  cache-write rate. When the backend omits `cache_write_tokens`, the estimate
  cannot include cache-write cost and reports only ordinary + cached-read +
  output. The usage footer explicitly reports when the write counter is
  absent.
- `service_tier: "default"` resolves to standard pricing;
  `service_tier: "priority"` (Fast mode) resolves to priority pricing.

## Explicit cache boundaries

Explicit cache-boundary support (`prompt_cache_options`,
`prompt_cache_breakpoint`) is intentionally unsupported for the current use
case. The framework relies on implicit caching and the session-owned
`prompt_cache_key`.