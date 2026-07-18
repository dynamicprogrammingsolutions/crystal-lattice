# Update GPT-5.6 Pricing and Cost Estimation

Update the OpenAI pricing parser and snapshots for GPT-5.6's new cache-write column and service-tier rates, and fix API-equivalent cost estimates for ChatGPT-authenticated GPT-5.6 usage.

## Requirements checklist

- [x] Update the pricing parser to support the new four-price row shape.
- [x] Preserve support for legacy three-price rows.
- [x] Store cache-write price separately from cached-input/read price.
- [x] Refresh standard, batch, flex, and priority rates for Sol, Terra, and Luna.
- [x] Keep cost estimation correct for default/standard, flex, and priority service tiers.
- [x] Parse and preserve `usage.input_tokens_details.cache_write_tokens`.
- [x] Charge reported cache-write tokens at the cache-write rate without double-counting them as ordinary input.
- [x] Preserve and display cache-write token counts in usage metadata and cumulative turn usage.
- [x] Make ChatGPT GPT-5.6 usage produce a non-zero API-equivalent estimate when usage is available.
- [x] Verify the session-owned prompt cache key is generated, remains stable, and is sent on ChatGPT requests.
- [x] Clearly label/document ChatGPT dollar cost as an estimate, not subscription billing.
- [x] Add or update parser, merge, resolver, and cost-estimation unit tests.
- [x] Add a separate real API pricing/usage integration test.
- [x] Add separate saved-login ChatGPT default-tier and priority-tier pricing tests and run them with credentials from `~/.crystal`.
- [x] Update pricing documentation and checked-in snapshot provenance.
- [x] Report unavailable or rejected API/ChatGPT credentials as not-run verification with the exact reason.

Parent Task: `tasks/20260713-openai-responses-gpt-5-6-support/000-main.md`

## Root cause

Relevant implementation:

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_pricing.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_usage_extension.py`
- `plugins/openai_responses/src/openai_responses_plugins/data/openai_model_pricing.json`
- `plugins/openai_responses/src/openai_responses_plugins/data/openai_chatgpt_manual_models.json`
- `scripts/refresh_openai_responses_pricing.py`
- `plugins/openai_responses/tests/test_openai_responses_pricing_unit.py`
- `plugins/openai_responses/tests/test_openai_responses_chatgpt_usage_manual_integration.py`
- `plugins/openai_responses/tests/test_openai_responses_chatgpt_auth_manual_integration.py`

Current `_ROW_RE` expects:

```text
model, input, cached input, output
```

The current OpenAI table now contains:

```text
model, input, cached input, cache writes, output
```

Because the regex expects only three prices after the model name, the refresh
script currently misses GPT-5.5 and GPT-5.6 rows. A temporary refresh on July
13, 2026 produced only 35 older model entries and no GPT-5.6 family entries.

The usage path currently reads only:

```text
usage.input_tokens_details.cached_tokens
```

GPT-5.6 reports billable cache writes separately as:

```text
usage.input_tokens_details.cache_write_tokens
```

Implicit caching is the GPT-5.6 default and can create a billable managed cache
write even when the client does not add an explicit cache breakpoint. Accurate
pricing must therefore use the reported cache-write counter. It must not infer
write tokens from prompt shape, cache keys, or estimated cache hits.

Explicit cache breakpoint support is intentionally out of scope for this task
and for the parent task. The current use case will continue to use implicit
caching.

## Authoritative GPT-5.6 rates

Prices are dollars per one million tokens.

Standard:

| Model | Input | Cached input | Cache writes | Output |
| --- | ---: | ---: | ---: | ---: |
| `gpt-5.6-sol` | 5.00 | 0.50 | 6.25 | 30.00 |
| `gpt-5.6-terra` | 2.50 | 0.25 | 3.125 | 15.00 |
| `gpt-5.6-luna` | 1.00 | 0.10 | 1.25 | 6.00 |

Batch and Flex:

| Model | Input | Cached input | Cache writes | Output |
| --- | ---: | ---: | ---: | ---: |
| `gpt-5.6-sol` | 2.50 | 0.25 | 3.125 | 15.00 |
| `gpt-5.6-terra` | 1.25 | 0.125 | 1.5625 | 7.50 |
| `gpt-5.6-luna` | 0.50 | 0.05 | 0.625 | 3.00 |

Priority:

| Model | Input | Cached input | Cache writes | Output |
| --- | ---: | ---: | ---: | ---: |
| `gpt-5.6-sol` | 10.00 | 1.00 | 12.50 | 60.00 |
| `gpt-5.6-terra` | 5.00 | 0.50 | 6.25 | 30.00 |
| `gpt-5.6-luna` | 2.00 | 0.20 | 2.50 | 12.00 |

## ChatGPT pricing findings

The usage extension resolves pricing in this order:

1. checked-in pricing snapshot;
2. manual ChatGPT pricing entries as fallback.

For ChatGPT, it estimates cached tokens from retained native history because the
ChatGPT backend does not necessarily report cached-token details in the same way
as the API.

A real one-turn saved-login request using `gpt-5.6-luna` on July 13, 2026
returned:

```text
content_ok=True
auth_mode=chatgpt
service_tier=default
has_usage=True
usage_total_cost=0.0
has_formatted_cost=False
estimated_cached_tokens=0
```

The zero estimate occurs because neither the pricing snapshot nor the manual
fallback currently contains `gpt-5.6-luna`.

ChatGPT users are generally governed by subscription limits/rate limits rather
than direct API per-token billing. The framework's dollar value should therefore
be documented as an API-equivalent estimate useful for comparison, not an
invoice amount.

## Prompt cache key findings

The framework already has the correct cache-key lifecycle for the current
implicit-caching use case:

1. The bundled `openai_responses` plugin includes
   `OpenAIResponsesPromptCachingExtension`.
2. `enable_prompt_cache_key` defaults to enabled.
3. The extension registers `ensure_prompt_cache_key` for both `session_create`
   and `request_prepare`.
4. `AgentApplication` stores the generated `opcache_<uuid>` value in
   `session.metadata["overrides"]["prompt_cache_key"]`.
5. Effective config resolution merges that session override into each request.
6. The prompt-caching extension writes the value to top-level
   `payload["prompt_cache_key"]`.
7. This injection applies to both API and ChatGPT authentication modes.
8. For ChatGPT, only the older `prompt_cache_retention` field is stripped; the
   cache key remains in the request.

Existing application tests already prove:

- a key is generated when a session is created;
- a missing key on a legacy session is repaired at `request_prepare`;
- the repaired key reaches the provider request;
- a fork currently preserves the existing key.

A live saved-login diagnostic on July 13, 2026 used `gpt-5.6-luna` and confirmed:

```text
content_ok=True
prompt_cache_key_sent=True
retention_sent=False
```

The ChatGPT backend accepted the request with the key.

This is conceptually aligned with current Codex behavior. Codex derives a stable
cache key from the thread ID, sends it on every Responses request, and reuses it
for follow-up turns and remote compaction. This framework uses a generated
session-owned UUID instead of the thread/session ID itself, but the important
semantics are the same: one stable key per conversation scope.

Automatic generation is specifically an `AgentApplication` lifecycle behavior.
Raw `AgentCore` callers do not automatically run the `session_create` and
`request_prepare` lifecycle triggers. A direct SDK caller must therefore provide
`prompt_cache_key` in config, invoke the relevant extension action, or use
`AgentApplication`. ChatGPT integration coverage for this task should use the
application/session lifecycle when verifying automatic generation, rather than
passing a manual key and claiming generation was tested.

## Implementation plan

1. Replace the fragile fixed-column regex with parsing that accepts both:
   - legacy model/input/cached/output rows;
   - new model/input/cached/cache-write/output rows.
2. Add a pricing field such as:

   `cache_write_per_1m`

3. Preserve `cached_input_per_1m` for cache reads.
4. Update pricing-block normalization and merge helpers to retain the new field.
5. Parse `input_tokens_details.cache_write_tokens` as a non-negative integer.
6. Split input tokens into mutually exclusive buckets:

   ```text
   cached_read_tokens = cached_tokens
   cache_write_tokens = cache_write_tokens
   ordinary_input_tokens =
       max(0, input_tokens - cached_read_tokens - cache_write_tokens)
   ```

7. Calculate:

   ```text
   ordinary_input_tokens * input_per_1m
   + cached_read_tokens * cached_input_per_1m
   + cache_write_tokens * cache_write_per_1m
   + output_tokens * output_per_1m
   ```

8. Clamp or reject inconsistent usage details so malformed counters cannot
   produce negative ordinary-input tokens or double-count the same input token.
9. Preserve cache-write counts in public/internal usage metadata, formatted
   fields, and cumulative turn totals.
10. For ChatGPT:
    - preserve a backend-reported `cache_write_tokens` value when present;
    - continue estimating cached-read tokens according to current ChatGPT
      behavior;
    - do not invent cache-write tokens when the ChatGPT backend omits them;
    - document that write-inclusive ChatGPT cost is exact only to the extent the
      backend reports the write counter.
11. Refresh the checked-in snapshot from official pricing pages.
12. Keep manual ChatGPT entries as fallback only. Add GPT-5.6 manual fallback
   pricing only if it is still needed after the snapshot parser is corrected.
13. Ensure `service_tier: "default"` resolves to standard pricing and
   `service_tier: "priority"` resolves to priority pricing.
14. Keep Pro reasoning mode on normal selected-model rates; do not add a Pro
   multiplier.
15. Do not add `prompt_cache_options`, `prompt_cache_breakpoint`, or explicit
    cache mode support.
16. Preserve the current API contract:
    - `AgentApplication` automatically generates and repairs session-owned keys;
    - raw `AgentCore` callers may supply a manual key;
    - do not add hidden mutable provider state for cache-key generation.

## Test requirements

Unit tests in `test_openai_responses_pricing_unit.py`:

- parse old three-price rows;
- parse new four-price GPT-5.6 rows;
- capture `cache_write_per_1m`;
- parse standard, batch, flex, and priority tiers;
- merge multiple tier pages without losing fields;
- preserve old model pricing;
- estimate default/standard GPT-5.6 cost;
- estimate flex cost;
- estimate priority cost;
- estimate cached-read cost;
- parse and preserve `cache_write_tokens`;
- estimate cache-write cost at `cache_write_per_1m`;
- verify ordinary input excludes both cached-read and cache-write tokens;
- verify a mixed usage example calculates all four token buckets correctly;
- verify missing `cache_write_tokens` defaults to zero;
- verify malformed/oversized detail counters do not produce negative or
  double-counted input;
- resolve dated snapshot IDs and aliases correctly;
- confirm refreshed snapshot includes all three GPT-5.6 models.

Usage extension unit tests:

- expose the current response's cache-write count and formatted value;
- preserve cache-write usage in provider-native metadata;
- include cache-write tokens in cumulative turn metadata;
- preserve a ChatGPT-reported cache-write counter when replacing/estimating
  `cached_tokens`;
- do not synthesize ChatGPT cache-write tokens when the backend omits them.

Separate real API integration test:

- Use a low-cost model such as `gpt-5.6-luna`.
- Make a minimal API-authenticated request.
- Assert usage metadata is present.
- Assert the resolved pricing entry is GPT-5.6 Luna.
- Assert estimated cost is positive and formatted.
- Verify reported/default service tier handling.
- Use a stable `prompt_cache_key`.
- Where the response reports `cache_write_tokens`, assert the estimator uses the
  cache-write rate.
- Run a follow-up request with the same key and inspect both cached-read and
  cache-write counters rather than assuming a hit.
- Gate on `OPENAI_API_KEY`.

Separate ChatGPT saved-login tests:

1. Default-tier test:
   - use `gpt-5.6-luna`;
   - assert `usage_effective_auth_mode == "chatgpt"`;
   - accept/report `usage_service_tier == "default"` as currently observed;
   - assert usage exists;
   - assert estimated cost is positive after the pricing fix;
   - assert formatted estimated cost exists;
   - retain estimated cached-token assertions;
   - assert a session-owned `opcache_*` key is present in session overrides;
   - record the outgoing request and assert that exact key is sent;
   - send a follow-up turn and assert the same key is reused;
   - preserve and price `cache_write_tokens` if the ChatGPT backend reports it;
   - report explicitly when the ChatGPT backend omits the write counter.

2. Priority/Fast test:
   - extend or add a separate test using
     `OpenAIResponsesFastModeExtension`;
   - assert the outgoing request uses `service_tier: "priority"`;
   - when the backend reports priority, assert priority pricing is used;
   - if the account/model does not receive priority, report the backend tier
     explicitly rather than claiming priority pricing was verified.

Run with:

```bash
CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna" \
  pytest <chatgpt-pricing-tests> \
    -m "manual_integration and integration and openai" -q
```

Documentation:

- Update `plugins/openai_responses/README.md` pricing and usage sections.
- Document all four token-price columns.
- State clearly that ChatGPT dollar cost is an API-equivalent estimate.
- Document implicit cache-write accounting and the reported-counter formula.
- Document that explicit cache boundaries are intentionally unsupported for the
  current use case.
- Document that ChatGPT cache-write cost cannot be inferred when its backend
  omits `cache_write_tokens`.

## Execution plan

(Approved and added during completion. The ChatGPT cached-token estimation
logic is preserved as-is; only cache-write accounting is added on top.)

### 1. Pricing-table parsing

Replace the fixed 3-column `_ROW_RE` with a variable-column parser that
interprets rows by position:

- 3 columns → legacy `input, cached_input, output`
- 4 columns → new `input, cached_input, cache_write, output`

`cache_write_per_1m` is stored as `Optional[float]` (same convention as
`cached_input_per_1m`).

### 2. Snapshot schema changes

Additive field `cache_write_per_1m` on each tier pricing block and on the
top-level `pricing` projection. Keep `version: 2`.

### 3. Usage extraction

Read `usage.input_tokens_details.cache_write_tokens` as a non-negative int.
Split input into three mutually exclusive buckets:

```text
cached_read_tokens    = max(0, cached_tokens)
cache_write_tokens    = max(0, cache_write_tokens)
ordinary_input_tokens = max(0, input_tokens - cached_read - cache_write)
```

### 4. Cache-write accounting and cost formula

```text
estimated = (
    ordinary_input_tokens * input_per_1m
  + cached_read_tokens   * cached_input_per_1m
  + cache_write_tokens   * cache_write_per_1m
  + output_tokens        * output_per_1m
) / 1_000_000.0
```

Clamp inconsistent detail counters so the larger counter is reduced to fit
within `input_tokens` and `ordinary_input_tokens` is clamped to 0. When
`cache_write_tokens > 0` but `cache_write_per_1m` is missing, fall back to
`input_per_1m`.

### 5. Cumulative metadata and usage formatting

Preserve the existing ChatGPT cached-read estimation logic unchanged. Add
cache-write fields on top:

- `usage_cache_write_tokens_formatted`
- `usage_turn_cache_write_tokens_cumulative`
- `usage_turn_cache_write_tokens_cumulative_formatted`

For ChatGPT mode: preserve any backend-reported `cache_write_tokens` in
`effective_usage`; do NOT synthesize it from the cached-read estimate.
Continue replacing `cached_tokens` with the estimate (current behavior).

### 6. Where changes belong

| Area | Files |
| --- | --- |
| Pricing parsing | `openai_responses_pricing.py` |
| Usage formatting | `openai_responses_usage_extension.py` |
| Checked-in data | `data/openai_model_pricing.json`, `data/openai_chatgpt_manual_models.json` |
| Tests | `tests/test_openai_responses_pricing_unit.py`, `tests/test_openai_responses_usage_extension_unit.py`, new `tests/test_openai_responses_pricing_real_api.py`, new `tests/test_openai_responses_chatgpt_pricing_manual_integration.py` |
| Docs | `plugins/openai_responses/README.md` |

### 7. Human decisions

- Malformed counters: clamp, do not reject.
- Double-count prevention: `ordinary = max(0, input - cached - write)`.
- ChatGPT omitted write counters: do not synthesize; report explicitly.
- Manual pricing fallbacks: only add GPT-5.6 manual entries if the refreshed
  snapshot still misses a model or tier.

### 8. Changed contracts

Pricing block dict adds `cache_write_per_1m: Optional[float]`. Public usage
metadata adds the three cache-write fields listed above. Cost formula as in
section 4.

### 9. Unit tests

18 pricing parser/resolver/estimator tests in
`test_openai_responses_pricing_unit.py` (including a mixed
ordinary/read/write/output calculation for `gpt-5.6-sol` standard tier
expected to cost `$0.054`).

6 usage extension tests in `test_openai_responses_usage_extension_unit.py`
covering per-turn, cumulative, native-metadata, ChatGPT-reported,
ChatGPT-omitted, and UI-element cases.

### 10. Integration tests

- Real API test in `test_openai_responses_pricing_real_api.py` gated on
  `OPENAI_API_KEY`, using `gpt-5.6-luna` and a stable `prompt_cache_key`.
- ChatGPT saved-login default-tier test using `AgentApplication` (so the
  `opcache_*` key is auto-generated) and a `_RecordingChatGPTProvider`.
- ChatGPT saved-login priority-tier (Fast mode) test that `xfail`s with an
  explicit message when the backend does not report `priority`.

### 11. Snapshot refresh, provenance, and documentation

Refresh via `python scripts/refresh_openai_responses_pricing.py`. If the live
fetch fails, hand-edit using the authoritative rates from the "Authoritative
GPT-5.6 rates" section and document the fallback. Update README with the
four-bucket formula, cache-write column, ChatGPT estimate caveat, and
explicit-cache-boundary exclusion.

### 12. Implementation order

1. Parser + estimator fix in `openai_responses_pricing.py`
2. Pricing unit tests
3. Usage extension fix in `openai_responses_usage_extension.py`
4. Usage extension unit tests
5. Snapshot refresh
6. Manual fallback check
7. Real API integration test
8. ChatGPT saved-login integration tests
9. README update
10. Full non-integration suite

### 13. Verification commands

```bash
pytest plugins/openai_responses/tests -q
pytest plugins/openai_responses/tests/test_openai_responses_pricing_unit.py -q
pytest plugins/openai_responses/tests/test_openai_responses_usage_extension_unit.py -q
pytest plugins/openai_responses/tests/test_openai_responses_pricing_real_api.py \
  -m "integration and api and not slow_integration and openai" -q
CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna" \
  pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_pricing_manual_integration.py \
    -m "manual_integration and integration and openai" -q
ruff check plugins/openai_responses/src plugins/openai_responses/tests scripts/refresh_openai_responses_pricing.py
black plugins/openai_responses/src plugins/openai_responses/tests scripts/refresh_openai_responses_pricing.py
pyright
```

### 14. Risks and expected limitations

- Live pricing page structure change → hand-edit fallback.
- ChatGPT backend variability → report actual values, do not assert fixed.
- Priority tier availability → `xfail` with explicit message.
- Cache-write price fallback to `input_per_1m` is pragmatic; documented.
- Explicit cache boundaries are out of scope.
- ChatGPT cache-write cost cannot be inferred when omitted.
- ChatGPT cached-read estimate is preserved as-is, not replaced.
- Pro reasoning mode uses normal rates, no multiplier.
- Raw `AgentCore` callers must supply `prompt_cache_key` manually.

## Completion Notes

(Added during completion.)

### What was done

1. **Parser fix** (`openai_responses_pricing.py`): replaced the fixed 3-column
   `_ROW_RE` with a variable-column parser that captures the model name plus
   a variable-length price-cell list. A new `_PRICE_CELL_RE` extracts
   individual price cells. The parser interprets rows by position:
   3 cells → legacy (input, cached, output); 4 cells → new
   (input, cached, cache_write, output). `cache_write_per_1m` is stored as
   `Optional[float]`, matching the `cached_input_per_1m` convention.

2. **Estimator fix** (`openai_responses_pricing.py`): `estimate_usage_cost`
   now reads `usage.input_tokens_details.cache_write_tokens`, splits input
   into three mutually exclusive buckets (ordinary, cached-read, cache-write),
   and applies the four-bucket cost formula. Inconsistent detail counters are
   clamped (the larger counter is reduced to fit; ordinary is clamped to 0).
   When `cache_write_tokens > 0` but `cache_write_per_1m` is missing, the
   estimator falls back to `input_per_1m` so legacy models remain estimable.

3. **`_pricing_block_from_mapping`** extended to read `cache_write_per_1m`.

4. **Usage extension** (`openai_responses_usage_extension.py`):
   - Added `_usage_cache_write_tokens` helper.
   - Added `_effective_cache_write_tokens_from_internal` helper.
   - Extended `_build_usage_metadata` to:
     - Emit `usage_cache_write_tokens_formatted` when the count is present
       and non-zero.
     - Track `usage_turn_cache_write_tokens_cumulative` and
       `usage_turn_cache_write_tokens_cumulative_formatted` across the turn.
     - Preserve backend-reported `cache_write_tokens` in ChatGPT mode (no
       synthesis from the cached-read estimate).
   - Added the `usage_cache_write_tokens_formatted` UI footer element with
     `exists` condition.
   - Added the three new keys to `_PUBLIC_USAGE_METADATA_KEYS`.
   - **Preserved the existing ChatGPT cached-read estimation logic
     unchanged** — the `_estimated_cached_tokens_for_current` heuristic
     continues to replace `cached_tokens` for ChatGPT-mode pricing.

5. **Snapshot refresh**: ran
   `python scripts/refresh_openai_responses_pricing.py` successfully. The
   refreshed `openai_model_pricing.json` now includes `gpt-5.6-sol`,
   `gpt-5.6-terra`, and `gpt-5.6-luna` with all four tiers (standard, batch,
   flex, priority) and `cache_write_per_1m` for each tier. Rates match the
   authoritative rates from the task file. No manual GPT-5.6 fallback entry
   was needed. The existing `gpt-5.5` manual entry in
   `openai_chatgpt_manual_models.json` was left unchanged.

6. **Unit tests**:
   - `test_openai_responses_pricing_unit.py`: added 18 new tests covering
     legacy 3-column parsing, new 4-column parsing, all GPT-5.6 tiers, merge
     preservation, default/flex/priority estimation, cached-read rate,
     cache-write rate, ordinary exclusion, mixed-bucket calculation
     (`gpt-5.6-sol` standard = $0.054), missing counter defaults, missing
     price fallback, oversized counter clamping, and snapshot refresh
     regression.
   - `test_openai_responses_usage_extension_unit.py`: added 6 new tests
     covering cache-write formatted footer, cumulative turn totals, native
     metadata preservation, ChatGPT-reported cache-write preservation,
     ChatGPT-omitted cache-write (no synthesis), and UI element presence.
   - Updated 2 existing manual-fallback tests to use an empty snapshot via
     `pricing_snapshot_path` (the refreshed snapshot now includes `gpt-5.5`,
     so the default snapshot can no longer exercise the manual fallback).
   - Updated the UI elements test to include the new cache-write footer.

7. **Real API integration test** (`test_openai_responses_pricing_real_api.py`):
   gated on `OPENAI_API_KEY`. Uses `gpt-5.6-luna` with a stable
   `prompt_cache_key`. Verifies the snapshot resolves GPT-5.6 Luna with
   `cache_write_per_1m`, usage metadata is present, cost is positive and
   formatted, and follow-up counters are reported. Explicitly prints when
   `cache_write_tokens` is absent. **Result: 1 passed** (run with
   `OPENAI_API_KEY` from `.env`). The API response did not report
   `cache_write_tokens` for the short test prompt; the test explicitly
   reported this and skipped the cache-write rate verification.

8. **ChatGPT saved-login integration tests**
   (`test_openai_responses_chatgpt_pricing_manual_integration.py`):
   - Default-tier test: uses `AgentApplication` to verify auto-generation of
     the `opcache_*` key, then uses `_RecordingChatGPTProvider` to verify the
     exact key is sent and reused on a follow-up turn. Asserts positive
     estimated cost, `usage_effective_auth_mode == "chatgpt"`, and preserved
     estimated cached tokens. Explicitly reports when the backend omits
     `cache_write_tokens`. **Result: 1 passed** with
     `CHATGPT_TEST_STATE_DIR="$HOME/.crystal"` and
     `OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna"`. Backend reported
     `service_tier=default` and omitted `cache_write_tokens`; the test
     explicitly reported both.
   - Priority-tier (Fast mode) test: verifies the outgoing request uses
     `service_tier: "priority"` and the `opcache_*` key is sent. `xfail`s
     with an explicit message when the backend does not report `priority`.
     **Result: 1 xfailed** (backend reported `default`, not `priority` —
     the test correctly `xfail`ed with the explicit message).

9. **README** (`plugins/openai_responses/README.md`): added a
   "Pricing snapshot and cost estimation" subsection documenting the four
   token-price columns, the three-bucket split, the cost formula, the
   cache-write price fallback, the clamp behavior, and implicit cache-write
   accounting. Added a "ChatGPT cost estimate caveat" subsection stating
   that ChatGPT dollar cost is an API-equivalent estimate, not subscription
   billing, and that cache-write cost cannot be inferred when the backend
   omits `cache_write_tokens`. Added an "Explicit cache boundaries"
   subsection stating that `prompt_cache_options`/`prompt_cache_breakpoint`
   are intentionally unsupported.

### Verification commands and results

```bash
# Fast default package suite (non-integration)
pytest plugins/openai_responses/tests -q
# Result: 328 passed, 3 failed (pre-existing attachment failures), 70 deselected

# Pricing unit tests
pytest plugins/openai_responses/tests/test_openai_responses_pricing_unit.py -q
# Result: 28 passed

# Usage extension unit tests
pytest plugins/openai_responses/tests/test_openai_responses_usage_extension_unit.py -q
# Result: 24 passed

# Real API pricing integration test (requires OPENAI_API_KEY)
pytest plugins/openai_responses/tests/test_openai_responses_pricing_real_api.py \
  -m "integration and api and not slow_integration and openai" -q
# Result: 1 passed

# ChatGPT saved-login pricing tests (requires ~/.crystal credentials)
CHATGPT_TEST_STATE_DIR="$HOME/.crystal" \
OPENAI_RESPONSES_CHATGPT_MODEL="gpt-5.6-luna" \
  pytest plugins/openai_responses/tests/test_openai_responses_chatgpt_pricing_manual_integration.py \
    -m "manual_integration and integration and openai" -q
# Result: 1 passed, 1 xfailed (priority-tier xfailed as expected)

# Lint/format
ruff check <modified files>  # All checks passed
black <modified files>        # All files formatted
```

### Pre-existing failures (not caused by this task)

Three tests in `test_openai_responses_native_history_regressions.py` fail
both before and after these changes:
- `test_uploaded_attachment_history_rebuilds_original_multipart_content`
- `test_uploaded_attachment_history_slice_and_fork_keep_coherent_native_segments`
- `test_session_asset_attachment_history_rebuilds_original_asset_ref`

These are attachment-upload regressions unrelated to pricing/usage and were
confirmed failing on the base commit before any changes.

### Credential/API gating

- `OPENAI_API_KEY` was available in the repo root `.env` and the real API
  test ran successfully (1 passed).
- `~/.crystal/auth/chatgpt-auth.json` was available and valid. Both ChatGPT
  saved-login tests ran successfully (1 passed, 1 xfailed as expected).
- No credentials were printed or logged.

### Files changed

- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_pricing.py`
- `plugins/openai_responses/src/openai_responses_plugins/openai_responses_usage_extension.py`
- `plugins/openai_responses/src/openai_responses_plugins/data/openai_model_pricing.json`
- `plugins/openai_responses/tests/test_openai_responses_pricing_unit.py`
- `plugins/openai_responses/tests/test_openai_responses_usage_extension_unit.py`
- `plugins/openai_responses/tests/test_openai_responses_pricing_real_api.py` (new)
- `plugins/openai_responses/tests/test_openai_responses_chatgpt_pricing_manual_integration.py` (new)
- `plugins/openai_responses/README.md`
