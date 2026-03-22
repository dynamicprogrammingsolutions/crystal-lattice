# Fireworks Hosted Provider Verification

Short description: Use Fireworks as the first hosted-provider proof point for the generalized reference OpenAI-compatible provider, while keeping all newly added features generic rather than Fireworks-specific.

Parent Task: tasks/20260322-reference-openai-compatible-provider-generalization/000-main.md
Depends On: tasks/20260322-reference-openai-compatible-provider-generalization/010-ollama-safe-generalization.md

## Why This Exists

After the package is generalized and still verified on Ollama, this subtask proves that the generic implementation actually works against a real hosted OpenAI-like provider. Fireworks is the first hosted target because its docs clearly cover chat completions, tools, reasoning, usage, and OpenAI-compatible setup.

## Scope

### In scope

- Add Fireworks provider examples/config entries.
- Add hosted integration tests using Fireworks.
- Verify the generic reasoning/tool/usage features against a non-Ollama backend.
- Add default config entries under the terminal app default config for Fireworks.

### Out of scope

- Together/SiliconFlow/DeepInfra integration coverage.
- Major new feature work beyond what is needed to make the generic package function correctly on Fireworks.

## Documentation Findings To Use

Fireworks docs indicate:

- OpenAI-compatible usage with base URL `https://api.fireworks.ai/inference/v1`.
- Standard chat completions and tool calling.
- Reasoning support with fields including `reasoning_content`.
- Usage data returned in OpenAI-like responses/streams.
- Importance of preserving reasoning information across tool rounds.
- Fireworks model names are globally identified in docs as `accounts/<ACCOUNT_ID>/models/<MODEL_ID>`.

These findings make Fireworks a strong first hosted verification target for all three generic features: text, tools, and reasoning, plus generic usage tracking.

## Preserved Reasoning Note

This subtask should be the first place where preserved reasoning is treated as an explicit hosted-provider verification target, not just a design goal.

- Many OpenAI-like providers and newer reasoning model families support preserved reasoning across tool rounds, even when the exact field names differ.
- This matters especially for model families such as GLM-5 and for providers that return `reasoning_content` or equivalent preserved reasoning payloads.
- The existing tools + reasoning continuity scenario should be treated as the primary regression for this behavior.
- If Fireworks is the first hosted provider where this can be verified reliably, use this subtask to establish the canonical preserved-reasoning integration test shape that later providers can reuse.

## Fireworks Test Model Matrix

Use these model families for Fireworks integration coverage in this subtask:

- Use Qwen3 8B for all standard Fireworks tests.
- Use GLM 4.7 and Kimi K2.5 for reasoning + tools continuity/integration.

Requested test model constants:

- `fireworks/qwen3-8b`
- `fireworks/glm-4p7`
- `fireworks/kimi-k2p5`

Important setup note from Fireworks docs:

- Fireworks documentation commonly shows fully qualified model names like `accounts/fireworks/models/glm-4p7` and `accounts/fireworks/models/kimi-k2p5` for chat-completions examples.
- When implementing tests/config, verify whether the shorthand aliases above are accepted directly by the OpenAI-compatible endpoint. If not, use the account-qualified names in code while keeping the same model-family choices.

Reasoning setup implications from Fireworks docs:

- Qwen3 models use grammar-based reasoning and have reasoning enabled by default; `reasoning_effort` may be set to `low` / `medium` / `high`, and `none` or `false` disables reasoning.
- GLM 4.7 uses binary on/off reasoning behavior; `none` or `false` disables reasoning, but effort levels do not add more granularity.
- Fireworks also exposes `reasoning_history`, including a documented `preserved` mode for retaining historical `reasoning_content` across turns; GLM-4.7 explicitly documents support for `preserved`.
- This means the test suite should not force a single reasoning-options shape across all Fireworks models. Use model-appropriate request options where reasoning is part of the test scenario.

Recommended request-option setup for the requested test models:

- Qwen3 8B standard tests:
  - use the Qwen3 8B model as the default Fireworks test model
  - for plain text/tools/usage tests, no special reasoning options are required
  - for reasoning-only tests, `reasoning_effort: "low"` is a reasonable explicit setting when needed
- GLM 4.7 reasoning + tools integration:
  - leave reasoning enabled by default unless the test specifically needs to disable it
  - set `reasoning_history: "preserved"` for preserved-reasoning/tool-round continuity checks
- Kimi K2.5 reasoning + tools integration:
  - use Kimi K2.5 as the second reasoning + tools model in the matrix
  - prefer the same preserved-reasoning request shape where supported
  - if `reasoning_history: "preserved"` is not accepted or not documented for the selected Kimi K2.5 endpoint shape, keep the test focused on reasoning + tools continuity and skip only the explicit preserved-history assertion

## Planned Changes

### 1. Default config additions

Update:

- `application/python/agent_terminal_app/default_config/config.json`

Add a Fireworks provider entry using `reference_openai_compatible` and env-configured credentials.

Suggested config shape:

```json
"fireworks": {
  "provider": "reference_openai_compatible",
  "base_url": "https://api.fireworks.ai/inference/v1",
  "api_key": "${env:FIREWORKS_API_KEY}",
  "model": "fireworks/qwen3-8b",
  "timeout": 180,
  "request_options": {
    "reasoning_effort": "low"
  }
}
```

If the default reasoning request option is too model-specific, keep the default provider entry simpler and let tests override `request_options`.

Public config rule:

- Only the API key should be env-based in the default config entry.
- Test code may still use `FIREWORKS_MODEL` or similar env vars/constants for integration selection.

Also add a corresponding agent entry so the provider is easy to use from the terminal app.

### 2. Fireworks integration test setup

Add hosted integration tests under:

- `plugins/reference-openai-compatible-provider/tests/`

Use Fireworks-specific env vars, for example:

- `FIREWORKS_API_KEY`
- `FIREWORKS_BASE_URL` defaulting to `https://api.fireworks.ai/inference/v1`
- test constants or test-only env vars for model overrides if needed

Recommended default test mapping:

- standard/basic/usage/tools/reasoning tests: Qwen3 8B
- reasoning + tools continuity tests: GLM 4.7 and Kimi K2.5

For the reasoning + tools continuity tests, treat GLM 4.7 as the primary documented preserved-reasoning assertion target and Kimi K2.5 as the second required model in the matrix.

### 3. Hosted integration tests to add

Recommended set:

- basic non-streaming request
- basic streaming request
- `/models` / UI smoke test if Fireworks `/models` behavior aligns with the provider assumptions
- tool-calling round trip with one real tool loop
- reasoning metadata extraction using Fireworks-returned reasoning fields, using Qwen3 8B by default
- reasoning + tools continuity regression across at least one tool round, using GLM 4.7 and Kimi K2.5
- usage metadata extraction and normalization in streaming mode
- preserved reasoning regression specifically checking that reasoning payloads survive tool rounds rather than being dropped after mapping

For preserved reasoning assertions:

- GLM 4.7 should explicitly exercise `reasoning_history: "preserved"`.
- Kimi K2.5 should follow the same setup when the endpoint/model combination accepts it; otherwise, keep Kimi K2.5 in the reasoning + tools matrix but allow the strict preserved-history assertion to be conditional.

Suggested files:

- `test_fireworks_integration_basic.py`
- `test_fireworks_integration_usage.py`
- `test_fireworks_integration_reasoning.py`
- `test_fireworks_integration_tools_reasoning.py`

Suggested model usage inside those tests:

- `test_fireworks_integration_basic.py`: Qwen3 8B
- `test_fireworks_integration_usage.py`: Qwen3 8B
- `test_fireworks_integration_reasoning.py`: Qwen3 8B
- `test_fireworks_integration_tools_reasoning.py`: parameterize GLM 4.7 and Kimi K2.5

### 4. Keep the implementation generic

Any code adjustments required for Fireworks should be phrased as generic OpenAI-compatible support, for example:

- preserving `reasoning_content`
- capturing top-level `usage`
- handling stream-final usage chunks
- preserving provider-native reasoning payloads across tool rounds for interleaved-thinking flows

Avoid adding Fireworks-branded normalized fields unless there is no generic alternative.

## Verification Requirements

This subtask is complete only when:

1. The generalized package successfully talks to Fireworks using the reference provider.
2. Basic text requests pass in both non-streaming and streaming modes.
3. Tool calls work for at least one model/tool scenario.
4. Reasoning metadata is preserved when Fireworks returns it.
5. Generic usage metadata is captured from Fireworks.
6. The terminal app default config includes a Fireworks provider entry.

## Risks / Watchouts

- Fireworks model capability varies; use env vars or per-test skips rather than hard-coding brittle model choices.
- Make sure the reasoning+tools regression is checking generic preservation behavior, not Fireworks-only response details.
- If `/models` output differs from the provider's current assumptions, fix only the generic assumptions that are truly safe to generalize.

## Execution Plan Added During Completion

Date added: 2026-03-22

1. Add Fireworks integration scaffolding under `plugins/reference-openai-compatible-provider/tests/`.
   - Add shared helpers for `FIREWORKS_API_KEY`, Fireworks base URL, standard/reasoning model constants, endpoint availability checks, and clean skip behavior for missing credentials, unsupported capabilities, and transient Fireworks rate limits.
   - Add a `fireworks` pytest marker to the package test config.

2. Add Fireworks hosted integration tests for the standard provider behavior.
   - Add basic non-streaming and streaming smoke tests using `fireworks/qwen3-8b` with `reasoning_effort: "none"` so the expected visible text stays stable.
   - Add `/models` / UI smoke coverage against the live Fireworks `/models` endpoint.
   - Add usage coverage, including a streaming case with `stream_options.include_usage`.
   - Add a standard tool-loop round-trip using `fireworks/qwen3-8b` with reasoning disabled for the visible answer path.

3. Split hosted reasoning verification into two separate Fireworks scenarios.
   - Add the existing interleaved-reasoning continuity scenario using the same prompt shape as `plugins/openrouter/tests/reasoning_test`, but run it only on Fireworks Qwen3 8B with reasoning enabled.
   - Keep this test focused on preserved reasoning across the current tool loop only, matching the original intent of the OpenRouter reasoning-test regression.
   - Add a separate explicit `reasoning_history: "preserved"` regression using `fireworks/glm-4p7` and `fireworks/kimi-k2p5` where the first turn hides a random seed word only in reasoning, and the second turn asks for that hidden word after a tool round.

4. Update terminal default config.
   - Add a `fireworks` provider entry in `application/python/agent_terminal_app/default_config/config.json` using `reference_openai_compatible`, base URL `https://api.fireworks.ai/inference/v1`, API key from `${env:FIREWORKS_API_KEY}`, and model `fireworks/qwen3-8b`.
   - Keep provider defaults generic and avoid baking model-specific reasoning controls into the public config entry.
   - Add a matching `fireworks` agent entry for terminal-app discoverability.

5. Verify and document completion.
   - Run the reference-provider test suite, then run the Fireworks-marked tests with the available Fireworks key.
   - If Fireworks returns transient `429 RATE_LIMIT_EXCEEDED` responses, convert those cases into clean skips rather than noisy failures.
   - Append completion notes to this task file summarizing what was implemented and what was verified live.

## Completion Notes Added During Completion

Date added: 2026-03-22

### Implemented

- Added Fireworks hosted integration scaffolding in `plugins/reference-openai-compatible-provider/tests/fireworks_test_utils.py`.
  - Loads `FIREWORKS_API_KEY` from the repo root `.env` when needed.
  - Adds shared Fireworks config helpers, endpoint-availability checks, and clean skip handling for transient Fireworks rate limits.
  - Reuses the generic reference provider, reasoning extension, tools extension, and usage extension exactly as-is.

- Added Fireworks integration tests:
  - `plugins/reference-openai-compatible-provider/tests/test_fireworks_integration_basic.py`
    - basic non-streaming text request using Fireworks Qwen3 8B with `reasoning_effort: "none"`
    - basic streaming text request using the same model/request shape
    - `/models` / UI smoke test against Fireworks model listing
  - `plugins/reference-openai-compatible-provider/tests/test_fireworks_integration_usage.py`
    - non-streaming usage normalization
    - streaming usage normalization with `stream_options.include_usage`
  - `plugins/reference-openai-compatible-provider/tests/test_fireworks_integration_reasoning.py`
    - generic reasoning metadata extraction using Fireworks GLM 4.7 streaming
  - `plugins/reference-openai-compatible-provider/tests/test_fireworks_integration_tools_reasoning.py`
    - standard Fireworks Qwen3 8B tool loop with reasoning disabled for stable visible output
    - interleaved-reasoning continuity regression using the existing `core/python/tests/reasoning_test` fixture on Fireworks Qwen3 8B
    - explicit `reasoning_history: "preserved"` regression for Fireworks GLM 4.7 and Kimi K2.5 using a hidden-word-across-turns scenario where the hidden word is derived privately and must be recalled on the next turn

- Added the `fireworks` pytest marker in `plugins/reference-openai-compatible-provider/pyproject.toml`.

- Updated terminal default config in `application/python/agent_terminal_app/default_config/config.json`.
  - Added a `fireworks` provider entry using `reference_openai_compatible`.
  - Uses base URL `https://api.fireworks.ai/inference/v1` and `${env:FIREWORKS_API_KEY}`.
  - Added a matching `fireworks` agent entry.

### Live verification findings preserved

- Fireworks shorthand model ids such as `fireworks/qwen3-8b`, `fireworks/glm-4p7`, and `fireworks/kimi-k2p5` were accepted by the live chat-completions endpoint.
- Fireworks `/models` returned account-qualified ids such as `accounts/fireworks/models/glm-4p7` and `accounts/fireworks/models/kimi-k2p5` during live checks.
- Fireworks Qwen3 8B required `reasoning_effort: "none"` in the basic/tools/usage tests to keep visible content stable and avoid inline visible reasoning.
- Fireworks GLM 4.7 emitted generic `reasoning_content` in streaming mode and worked as the primary reasoning-metadata verification target.
- Fireworks GLM 4.7 and Kimi K2.5 both worked with the explicit `reasoning_history: "preserved"` follow-up scenario used for the new hidden-word regression.

### Verification performed

- Ran Fireworks-hosted subset:
  - `pytest plugins/reference-openai-compatible-provider/tests -m fireworks -q`
  - Result: `4 passed, 6 skipped, 26 deselected`
  - Skips were expected when Fireworks availability/rate-limit guards triggered during live hosted checks.

- Ran full reference-provider test suite:
  - `pytest plugins/reference-openai-compatible-provider/tests -q`
  - Result: `28 passed, 8 skipped`

### Notes for follow-up subtasks

- The Fireworks verification stayed generic; no Fireworks-specific normalized metadata fields were added to the provider package.
- The Qwen3 interleaved-reasoning continuity regression is intentionally separate from the explicit `reasoning_history: "preserved"` regression.
- The hidden-word preserved-history regression is structured so the answer should only be recoverable from preserved private reasoning across turns, not from visible assistant content.

### Follow-up Adjustment Added During Completion

Date added: 2026-03-22

- Replaced the earlier Qwen3-based tools+reasoning integration coverage after live verification showed Qwen3 frequently emits reasoning in visible `content` on Fireworks unless reasoning is disabled.
- Final hosted reasoning split is:
  - standard single-tool-loop reasoning preservation uses the existing `core/python/tests/reasoning_test` prompt on Fireworks Kimi K2.5 with a fixed request seed (`seed: 2`, `temperature: 0`), because this live combination returned the expected `Clock` answer reliably enough for an integration test
  - explicit cross-turn `reasoning_history: "preserved"` verification runs on Fireworks GLM 4.7 only, because Kimi K2.5 did not behave reliably enough for the second explicit preserved-history regression even after prompt tuning
- Replaced the earlier rate-limit skip behavior with paced hosted calls and retry/backoff behavior.
  - Fireworks test helpers now enforce a default 1 second wait between request starts.
  - Hosted request helpers retry transient Fireworks `429 RATE_LIMIT_EXCEEDED` responses instead of skipping the test.

### Updated verification after follow-up adjustment

- `pytest plugins/reference-openai-compatible-provider/tests -m fireworks -q`
  - Result: `10 passed, 26 deselected`
- `pytest plugins/reference-openai-compatible-provider/tests -q`
  - Result: `36 passed`

## Follow-Up: Configurable Token Rate-Based Cost Calculation

Date added: 2026-03-22

### Requirement

Add the ability for users to configure token pricing rates for providers that do not return cost data in the usage response (e.g., Fireworks). When configured, the usage extension should calculate cost from these rates instead of relying on `usage.cost` or `usage.cost_details.upstream_inference_cost`.

### Config Shape

The pricing configuration should be a single object under a `token_rates` key. Rates are specified in **dollars per million tokens** for intuitive configuration:

```json
{
  "provider": "reference_openai_compatible",
  "base_url": "https://api.fireworks.ai/inference/v1",
  "api_key": "${env:FIREWORKS_API_KEY}",
  "model": "fireworks/qwen3-8b",
  "token_rates": {
    "input": 0.10,
    "cached": 0.01,
    "completion": 0.30
  }
}
```

- `input`: Rate per million input (prompt) tokens (in USD)
- `cached`: Rate per million cached tokens (in USD) — typically discounted compared to `input`
- `completion`: Rate per million completion (output) tokens (in USD)

### Implementation Notes

1. **Where to implement**: Modify `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/usage_extension.py`.

2. **Cost calculation logic**:
   - If `usage.cost` or `usage.cost_details.upstream_inference_cost` is present, use that (provider-returned cost takes precedence).
   - Otherwise, check for `token_rates` in the provider config (available via `state["config"]` during extension processing).
   - Calculate cost as (rates are in $/million tokens, so divide by 1,000,000):
     ```
     cost = (prompt_tokens - cached_tokens) * (input_rate / 1_000_000)
           + cached_tokens * (cached_rate / 1_000_000)
           + completion_tokens * (completion_rate / 1_000_000)
     ```
   - If `cached_rate` is not configured, treat cached tokens the same as regular input tokens (use `input_rate`).

3. **Config propagation**: The usage extension receives `state` dict which contains `config` from the provider. The extension can access `state["config"]["token_rates"]` during `process_chunk` or `from_native_messages`.

4. **Reference implementation**: The `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_usage_extension.py` shows the pattern for cost extraction and formatting, but it sources cost from the response. This new feature sources rates from config instead.

5. **UI elements**: Existing UI elements (`usage_total_cost_formatted`, cumulative cost fields) should work unchanged since they consume the calculated cost from metadata.

### Tests to Add

- Unit test: verify cost calculation when `token_rates` is configured and provider returns no cost (using per-million rates).
- Unit test: verify precedence (provider-returned cost wins over calculated cost).
- Unit test: verify fallback behavior when `cached_rate` is missing (cached tokens charged at input rate).
- Unit test: verify cached tokens are discounted correctly when `cached_rate` is set.
- Unit test: verify cost is correctly computed for large token counts (e.g., 1M tokens at $0.10/M = $0.10).
- Integration test: verify on Fireworks with configured `token_rates` that cost metadata appears correctly.

### Config Schema Update

Add `token_rates` to the provider's config schema:

```python
"token_rates": {
    "type": "object",
    "required": False,
    "description": "Token pricing rates in USD per million tokens",
    "properties": {
        "input": {"type": "number", "description": "Rate per million input tokens (USD)"},
        "cached": {"type": "number", "description": "Rate per million cached tokens (USD)"},
        "completion": {"type": "number", "description": "Rate per million completion tokens (USD)"},
    },
}
```

### Acceptance Criteria

1. Users can configure `token_rates` under a single config key.
2. When configured, cost is calculated from token counts and rates.
3. Provider-returned cost takes precedence over calculated cost.
4. Existing tests continue to pass.
5. New unit tests cover the cost calculation logic.
6. Fireworks config example in default config can optionally demonstrate the feature (or users can add it manually).