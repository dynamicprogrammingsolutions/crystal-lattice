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