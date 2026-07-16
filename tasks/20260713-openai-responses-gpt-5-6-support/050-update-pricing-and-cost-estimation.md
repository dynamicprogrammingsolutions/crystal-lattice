# Update GPT-5.6 Pricing and Cost Estimation

Update the OpenAI pricing parser and snapshots for GPT-5.6's new cache-write column and service-tier rates, and fix API-equivalent cost estimates for ChatGPT-authenticated GPT-5.6 usage.

## Requirements checklist

- [ ] Update the pricing parser to support the new four-price row shape.
- [ ] Preserve support for legacy three-price rows.
- [ ] Store cache-write price separately from cached-input/read price.
- [ ] Refresh standard, batch, flex, and priority rates for Sol, Terra, and Luna.
- [ ] Keep cost estimation correct for default/standard, flex, and priority service tiers.
- [ ] Parse and preserve `usage.input_tokens_details.cache_write_tokens`.
- [ ] Charge reported cache-write tokens at the cache-write rate without double-counting them as ordinary input.
- [ ] Preserve and display cache-write token counts in usage metadata and cumulative turn usage.
- [ ] Make ChatGPT GPT-5.6 usage produce a non-zero API-equivalent estimate when usage is available.
- [ ] Verify the session-owned prompt cache key is generated, remains stable, and is sent on ChatGPT requests.
- [ ] Clearly label/document ChatGPT dollar cost as an estimate, not subscription billing.
- [ ] Add or update parser, merge, resolver, and cost-estimation unit tests.
- [ ] Add a separate real API pricing/usage integration test.
- [ ] Add separate saved-login ChatGPT default-tier and priority-tier pricing tests and run them with credentials from `~/.crystal`.
- [ ] Update pricing documentation and checked-in snapshot provenance.
- [ ] Report unavailable or rejected API/ChatGPT credentials as not-run verification with the exact reason.

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
