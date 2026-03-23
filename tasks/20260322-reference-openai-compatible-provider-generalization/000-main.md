# Reference OpenAI-Compatible Provider Generalization

Short description: Generalize `plugins/reference-openai-compatible-provider` from an Ollama-leaning sample into a reusable OpenAI-compatible provider package that still works on Ollama, adds generic reasoning and usage handling, and is verified against hosted providers in stages.

## Goal

Turn the reference provider package into a generic chat-completions provider for OpenAI-like backends while preserving Ollama support and using Ollama as the first verification target.

Required outcomes:

1. Remove Ollama-specific request shaping from the provider package surface where possible.
2. Keep reasoning/tool support generic and provider-agnostic, using `request_options` for provider/model-specific enablement.
3. Add a generic usage extension with minimum shared fields only.
4. Add default config entries under `application/python/agent_terminal_app/default_config/config.json` for multiple OpenAI-like providers.
5. Expand integration coverage in stages:
   - Stage 1: still verify on Ollama only.
   - Stage 2: verify on Fireworks as the first hosted provider.
   - Stage 3: add integration coverage for Together, SiliconFlow, and DeepInfra.

Follow-up to keep visible but out of current implementation scope:

- Consider porting generic OpenAI-compatible multipart/image support later. The OpenRouter provider already has a useful reference implementation for `multipartContent` <-> OpenAI `content` block conversion, but the current task sequence is intentionally focused on text, reasoning, tools, and usage first.

## Subtasks

- [x] `tasks/20260322-reference-openai-compatible-provider-generalization/010-ollama-safe-generalization.md`
- [x] `tasks/20260322-reference-openai-compatible-provider-generalization/020-fireworks-hosted-provider-verification.md`
- [ ] `tasks/20260322-reference-openai-compatible-provider-generalization/030-other-provider-integration-matrix.md`

## Current State Summary

The current reference package is still Ollama-centered in configuration, docs, and tests.

Key code references:

- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/provider.py`
  - Always advertises `supports_thinking` in `get_tags()` around lines 170-176.
  - Otherwise is already fairly generic for `/models`, `/chat/completions`, streaming, and basic final message handling.
- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/reasoning_extension.py`
  - Uses a package-owned `think` config key.
  - Injects `payload["think"] = True`, which is Ollama-specific.
  - Only extracts string reasoning from `reasoning`, and does not preserve richer reasoning payloads like `reasoning_content` or `reasoning_details`.
- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/tools_extension.py`
  - Already follows generic OpenAI-style `tools` / `tool_calls` behavior and should be retained as the base tool-calling extension.
- `plugins/reference-openai-compatible-provider/README.md`
  - Still presented as an Ollama provider and documents `think` as the reasoning switch.
- `plugins/reference-openai-compatible-provider/tests/test_ollama_integration_basic.py`
  - Basic hosted-shape smoke tests, but only on Ollama.
- `plugins/reference-openai-compatible-provider/tests/test_ollama_integration_tools_reasoning.py`
  - Tool and reasoning coverage, but reasoning is still tied to `think` and Ollama.
- `application/python/agent_terminal_app/default_config/config.json`
  - Current `ollama` provider entry still sets `think: true` around lines 501-510.

## Documentation Research Summary

These provider docs were investigated as targets for generic support:

- Fireworks
  - OpenAI-compatible base URL under `/inference/v1`.
  - Supports chat completions, tools, reasoning controls, `reasoning_content`, and usage.
  - Documentation strongly supports preserving reasoning/tool data across tool rounds.
- Together
  - OpenAI-compatible `/v1` chat API.
  - Supports tools and usage broadly.
  - Reasoning controls and returned fields are model-dependent.
  - Some models have caveats around combining thinking and tools.
- SiliconFlow
  - OpenAI-compatible `/v1` chat API.
  - Supports tools, usage, and `reasoning_content`.
  - Docs explicitly require preserving reasoning content across tool-calling rounds for some models.
- DeepInfra
  - OpenAI-compatible `/v1/openai` endpoint shape.
  - Standard usage fields and model-specific function/tool capability.
  - Reasoning support is less uniformly documented at the provider level and should be treated as model-specific.

## Design Direction

The package should be reorganized around these principles:

1. The provider handles generic OpenAI-compatible chat-completions transport and message conversion.
2. The tools extension remains generic and provider-agnostic.
3. The reasoning extension becomes a parsing/preservation layer, not a provider-specific request shaper.
4. Provider/model-specific enablement of reasoning should go through `plugins.request_options_feature.RequestOptionsFeature`.
5. A new usage extension should normalize only the minimum shared fields:
   - raw `usage`
   - prompt/input tokens
   - completion/output tokens
   - total tokens
   - reasoning tokens when present
   - formatted token strings where useful for UI
6. Avoid OpenRouter-only features such as routing metadata, web search, Claude caching, or cost accounting.
7. Preserve reasoning payloads not only on inbound parsing but also in outbound provider-native history used for follow-up tool rounds.
8. Keep public default config entries simple: use env vars only for secrets like API keys, while models/base URLs may remain as literals or be overridden elsewhere.

## Extra Research Notes Worth Preserving

- A preserved-reasoning capability is increasingly important across OpenAI-like providers and newer reasoning models. Treat the existing tools + reasoning continuity scenario as the core regression for this family of behavior.
- This matters especially for providers/models that return `reasoning_content` or similar preserved reasoning payloads during tool use, including newer model families such as GLM-5. Even when exact field names differ, the package should preserve provider-native reasoning data across tool rounds rather than only surfacing it on the final mapped core message.
- Multipart/image support and verbosity control were both identified during investigation as possible future additions, but they are intentionally deferred from the current scope so the package can first be generalized around text, reasoning, tools, and usage.

## Proposed Cross-Task Sequence

1. First make the package generic without breaking Ollama.
2. Then add Fireworks-hosted verification as the first non-local provider proof point.
3. Then add the remaining provider integration matrix without materially changing the feature set.

## Notes For The Implementing Agent

- Preserve backwards compatibility where reasonable, but the long-term API should stop encouraging `think` as a first-class package concept.
- If a temporary compatibility bridge is needed for Ollama during subtask 010, keep it narrowly scoped and document a path to eventual cleanup.
- The first subtask is allowed to land generic functionality that is only verified on Ollama, as long as the new code and tests are structured for later hosted-provider reuse.
- Keep new behavior in this package generic even when subtask 020 verifies it only through Fireworks.