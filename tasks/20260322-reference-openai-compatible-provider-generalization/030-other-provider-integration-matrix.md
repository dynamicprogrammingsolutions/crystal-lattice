# Other Provider Integration Matrix

Short description: Add hosted integration coverage for Together, SiliconFlow, and DeepInfra using the already-generalized reference provider package, without expanding the package surface with provider-specific features.

Parent Task: tasks/20260322-reference-openai-compatible-provider-generalization/000-main.md
Depends On: tasks/20260322-reference-openai-compatible-provider-generalization/010-ollama-safe-generalization.md, tasks/20260322-reference-openai-compatible-provider-generalization/020-fireworks-hosted-provider-verification.md

## Why This Exists

After Fireworks proves the generalized package works on one hosted provider, this subtask widens confidence across the remaining provider set. The feature set should already exist by this point; the goal here is mostly validation, provider-specific test selection, and default-config completion.

## Scope

### In scope

- Add Together integration tests.
- Add SiliconFlow integration tests.
- Add DeepInfra integration tests.
- Add default config entries for these providers under the terminal app default config.
- Add any small generic compatibility adjustments discovered during testing.

### Out of scope

- Adding new major package features that were not already introduced by subtasks 010 and 020.
- Porting OpenRouter-only features.

## Provider-Specific Notes From Investigation

### Z-ai

https://docs.z.ai/api-reference/llm/chat-completion

### Together

- OpenAI-compatible `/v1` setup.
- Standard tool calling and usage support.
- Reasoning is model-dependent.
- Some models have caveats about combining thinking and tools, so test-model selection matters.
- Suggested default-config base URL: `https://api.together.xyz/v1`
- Suggested public config secret env var: `TOGETHER_API_KEY`

### SiliconFlow

- OpenAI-compatible `/v1` setup.
- Standard tools and usage.
- `reasoning_content` is important and should be preserved across tool rounds for supported models.
- Suggested default-config base URL: `https://api.siliconflow.com/v1`
- Suggested public config secret env var: `SILICONFLOW_API_KEY`

### DeepInfra

- OpenAI-compatible endpoint shape under `/v1/openai`.
- Basic chat, streaming, usage, and model-specific function support are documented.
- Reasoning support is less uniformly documented and should be treated conservatively.
- Suggested default-config base URL: `https://api.deepinfra.com/v1/openai`
- Suggested public config secret env var: `DEEPINFRA_API_KEY`

## Planned Changes

### 1. Default config additions

Update:

- `application/python/agent_terminal_app/default_config/config.json`

Add provider entries for:

- `together`
- `siliconflow`
- `deepinfra`

Each should use `reference_openai_compatible`, env-based API keys, literal default model IDs, and minimal default request options.

Adjust this requirement as follows:

- Only API keys should be env-based in the public default config.
- Public config should not introduce model env vars.
- Tests may still use model-specific env vars or constants where needed.

Also add corresponding agent entries for discoverability.

### 2. Integration test matrix

Add provider-specific integration tests that all exercise the same generic package behavior:

- basic non-streaming request
- basic streaming request
- tool-calling scenario where the selected model supports it
- usage extraction where the provider returns usage
- reasoning extraction where the selected model supports it

Recommended provider-specific expectations:

- Together
  - basic
  - streaming
  - tools
  - usage
  - reasoning only on a suitable model
  - reasoning+tools only if the selected model docs support that combination
  - preserved reasoning verification only when the selected model/provider combination actually supports it
- SiliconFlow
  - basic
  - streaming
  - tools
  - usage
  - reasoning
  - reasoning+tools continuity regression focused on `reasoning_content` preservation
- DeepInfra
  - basic
  - streaming
  - usage
  - tools on a model documented with function support
  - reasoning optional or skip-heavy unless a clearly documented reasoning-capable model is selected
  - preserved reasoning verification optional and model-dependent

Suggested test files:

- `test_together_integration_basic.py`
- `test_together_integration_reasoning_tools.py`
- `test_siliconflow_integration_basic.py`
- `test_siliconflow_integration_reasoning_tools.py`
- `test_deepinfra_integration_basic.py`
- `test_deepinfra_integration_tools_usage.py`

## Verification Requirements

This subtask is complete only when:

1. Together, SiliconFlow, and DeepInfra each have at least basic hosted integration coverage.
2. The package behavior remains generic rather than branching into provider-specific extension logic.
3. Any provider-specific request knobs are passed via config or `request_options`, not encoded as package-owned feature flags.
4. The terminal app default config contains entries for all four target OpenAI-like providers plus Ollama.

## Risks / Watchouts

- Do not force a single model choice across all providers; use env vars and capability-aware skips.
- Be conservative about reasoning assertions on DeepInfra until a reliable documented reasoning-capable model is chosen.
- If provider-specific quirks are discovered, first ask whether they can be handled by configuration before adding code branches.
- Keep this subtask focused on validation breadth rather than more feature development.
- Reuse the existing tools + reasoning continuity scenario as the main preserved-reasoning regression where provider/model support makes it viable.