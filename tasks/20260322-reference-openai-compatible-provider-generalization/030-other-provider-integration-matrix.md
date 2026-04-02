# Other Provider Integration Matrix

Short description: Add hosted integration coverage for Z.ai using the already-generalized reference provider package, update the terminal default config, and keep any provider-specific behavior flowing through generic `request_options` rather than new package-owned features.

Parent Task: tasks/20260322-reference-openai-compatible-provider-generalization/000-main.md
Depends On: tasks/20260322-reference-openai-compatible-provider-generalization/010-ollama-safe-generalization.md, tasks/20260322-reference-openai-compatible-provider-generalization/020-fireworks-hosted-provider-verification.md

## Task checklist

- [x] Update this subtask scope from the original wider provider matrix to a Z.ai-first hosted integration pass.
- [x] Add Z.ai hosted integration test scaffolding and pytest marker support.
- [x] Add Z.ai basic, usage, reasoning, and tools/reasoning integration coverage.
- [x] Add Z.ai provider and agent entries to `application/python/agent_terminal_app/default_config/config.json`.
- [x] Run targeted live verification with `ZAI_API_KEY` and record completion notes.

## Why This Exists

After Fireworks proved the generalized package on one hosted provider, the next practical target is Z.ai. The feature set should already exist by this point; the goal here is primarily hosted validation, provider-specific test selection, and default-config completion without expanding the runtime package surface.

## Scope

### In scope

- Add Z.ai integration tests.
- Add a Z.ai default config entry under the terminal app default config.
- Add a matching Z.ai agent entry for discoverability.
- Add only small generic compatibility adjustments if live testing reveals a real reusable gap.

### Out of scope

- Adding new major package features that were not already introduced by subtasks 010 and 020.
- Re-expanding this subtask back into the original Together/SiliconFlow/DeepInfra matrix during this pass.
- Porting OpenRouter-only features.

## Provider-Specific Notes From Investigation

### Z-ai

https://docs.z.ai/api-reference/llm/chat-completion

- General OpenAI-compatible base URL: `https://api.z.ai/api/paas/v4`
- The general endpoint documents `chat/completions`, tools/function calling, streaming, and usage.
- Returned assistant messages may include `reasoning_content`, which should already be handled by the generalized reasoning extension.
- Provider/model-specific knobs such as `thinking`, `thinking.clear_thinking`, JSON mode, and any tool-choice override should flow through `request_options`.
- Z.ai docs only clearly guarantee `tool_choice: "auto"`, so tests should avoid depending on `required`, named-tool forcing, or other less-portable variants.
- Suggested public config secret env var: `ZAI_API_KEY`
- Suggested default public config model: `glm-4.5-air`
- Suggested hosted tools/reasoning model: `glm-4.7`

### Original wider matrix note

The original intent for this file was Together + SiliconFlow + DeepInfra validation. That wider matrix remains useful follow-up work, but this task is now intentionally narrowed to Z.ai-first hosted verification because the reference provider package and reasoning/usage/request-options plumbing are already in place and Z.ai is the next concrete provider requested for live validation.

## Planned Changes

### 1. Default config additions

Update:

- `application/python/agent_terminal_app/default_config/config.json`

Add a provider entry for:

- `zai`

It should use `reference_openai_compatible`, an env-based API key, a literal default model ID, and minimal default request options.

Adjust this requirement as follows:

- Only API keys should be env-based in the public default config.
- Public config should not introduce model env vars.
- Tests may still use model-specific env vars or constants where needed.

Also add a corresponding agent entry for discoverability.

### 2. Integration test matrix

Add Z.ai integration tests that exercise the same generic package behavior already verified on Fireworks:

- basic non-streaming request
- basic streaming request
- tool-calling scenario where the selected model supports it
- usage extraction where the provider returns usage
- reasoning extraction where the selected model supports it

Recommended Z.ai provider-specific expectations:

- Basic and streaming tests should disable thinking through `request_options` so visible text remains deterministic.
- Usage tests should validate both non-streaming usage and streaming usage via `stream_options.include_usage`.
- Reasoning tests should use the returned `reasoning_content` field and verify that the generalized reasoning extension surfaces it correctly.
- Tools + reasoning tests should use a model that reliably supports Z.ai tools and thinking together.
- Preserved cross-turn reasoning should be attempted only with a documented thinking request shape such as `{"thinking": {"type": "enabled", "clear_thinking": false}}`.

Suggested test files:

- `zai_test_utils.py`
- `test_zai_integration_basic.py`
- `test_zai_integration_usage.py`
- `test_zai_integration_reasoning.py`
- `test_zai_integration_tools_reasoning.py`

## Verification Requirements

This subtask is complete only when:

1. Z.ai has at least basic hosted integration coverage.
2. The package behavior remains generic rather than branching into provider-specific extension logic.
3. Any Z.ai-specific request knobs are passed via config or `request_options`, not encoded as package-owned feature flags.
4. The terminal app default config contains a `zai` provider entry and matching agent entry.

## Risks / Watchouts

- Do not add Z.ai-specific runtime branching unless a live-tested compatibility gap clearly cannot be solved via config or generic request handling.
- Be conservative about tool-choice assertions because Z.ai docs clearly document `auto` but not the full wider tool-choice matrix.
- Prefer disabling thinking in basic/usage tests for deterministic visible output.
- Reuse the existing reasoning and tools continuity shapes where they fit, but do not force a preserved-reasoning assertion unless the selected Z.ai model/request shape supports it reliably.

## Execution plan

Added during completion on 2026-03-30.

1. Update this task file to reflect the narrowed Z.ai-first scope and completion checklist.
2. Extract the smallest useful provider-agnostic hosted-test helpers from the existing Fireworks scaffolding.
   - Move repo-root `.env` loading and shared `build_reference_core()` construction into a shared helper.
   - Keep provider-specific base URL, model defaults, and availability checks in thin provider helpers.
3. Add Z.ai hosted test utilities.
   - Use `ZAI_API_KEY` from the repo root `.env`.
   - Default `ZAI_BASE_URL` to `https://api.z.ai/api/paas/v4`.
   - Default `glm-4.5-air` for basic/usage coverage.
   - Default `glm-4.7` for tools/reasoning coverage.
4. Add Z.ai integration tests.
   - Basic non-streaming and streaming smoke tests with thinking disabled.
   - Usage tests for non-streaming and streaming with `stream_options.include_usage`.
   - Reasoning extraction tests using returned `reasoning_content`.
   - Tools + reasoning tests that rely on generic `request_options` and preserve provider-native reasoning/tool fields through the existing extensions.
5. Add optional terminal default config support.
   - Add a `zai` provider entry using `reference_openai_compatible`.
   - Add a matching `agents.zai` entry.
6. Run targeted live verification with the provided Z.ai key and record the outcome in completion notes.

## Completion Notes

Added during completion on 2026-03-30.

### Implemented

- Added shared hosted-test helpers in `plugins/reference-openai-compatible-provider/tests/hosted_test_utils.py`.
  - Moved repo-root `.env` loading there.
  - Moved shared `build_reference_core()` construction there.
- Updated `plugins/reference-openai-compatible-provider/tests/fireworks_test_utils.py` to use the shared hosted helper instead of keeping its own duplicate core/env setup.
- Added Z.ai hosted integration scaffolding in `plugins/reference-openai-compatible-provider/tests/zai_test_utils.py`.
  - Uses `ZAI_API_KEY` from the repo root `.env`.
  - Defaults to base URL `https://api.z.ai/api/paas/v4`.
  - Defaults to `glm-4.5-air` for basic/usage coverage and `glm-4.7` for reasoning/tools coverage.
  - Includes light availability checking and paced retry handling for rate limits.
- Added Z.ai integration tests:
  - `plugins/reference-openai-compatible-provider/tests/test_zai_integration_basic.py`
  - `plugins/reference-openai-compatible-provider/tests/test_zai_integration_usage.py`
  - `plugins/reference-openai-compatible-provider/tests/test_zai_integration_reasoning.py`
  - `plugins/reference-openai-compatible-provider/tests/test_zai_integration_tools_reasoning.py`
- Added a `turn reasoning` usage footer in `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/usage_extension.py` so assistant messages can show `metadata.usage_turn_reasoning_tokens_cumulative_formatted` in the same general style as the responses-based providers.
- Added a live Z.ai integration assertion that verifies turn-reasoning accumulation across a single tool-using assistant turn by checking both the tool-call assistant message and the final assistant message in stored session history.
- Added the `zai` pytest marker in `plugins/reference-openai-compatible-provider/pyproject.toml`.
- Added a terminal default-config provider entry and matching agent entry for Z.ai in `application/python/agent_terminal_app/default_config/config.json`.

### Generic fix discovered during implementation

- Found and fixed a generic non-streaming tool-loop bug in `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/usage_extension.py`.
  - Root cause: `OpenAICompatibleUsageExtension.finalize()` emptied the full native history when `final_messages` was empty, which happens on non-streaming assistant tool-call turns where the assistant tool-call message is emitted by `call_api()` rather than by provider `finalize()`.
  - This broke follow-up tool turns by leaving sessions with `native_messages: []` before appending tool results.
  - Fix: preserve `native_messages` unchanged when `final_messages` is empty.
- Found and fixed a second generic non-streaming usage-finalization gap in `core/python/agent_core/plugin/provider.py`.
  - Root cause: provider extensions were not finalizing non-streaming `call_api()` finals against the full native history, so turn-level usage metadata on assistant messages could miss earlier assistant steps from the same turn.
  - Fix: run extension `finalize()` hooks in the provider wrapper's non-streaming `call_api()` path after full history is merged.
- Strengthened `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/usage_extension.py` rebuild behavior so turn reasoning cumulative metadata is recomputed for every assistant message in a turn, including assistant tool-call messages that are followed by tool results.
- Added a regression test for that behavior in `plugins/reference-openai-compatible-provider/tests/test_usage_extension_unit.py`.

### Additional cleanup discovered during verification

- Corrected a pre-existing Fireworks UI-schema assertion in `plugins/reference-openai-compatible-provider/tests/test_fireworks_integration_basic.py` so it accepts the provider's current `dropdown` model selector shape.

### Live verification summary

- Live raw API checks against Z.ai succeeded for:
  - `/models`
  - basic non-streaming chat completion
  - JSON mode via `response_format`
  - tool-call generation
  - streaming usage via `stream_options.include_usage`
  - manual two-turn tool continuation with preserved thinking on `glm-4.7`
- Live pytest verification succeeded for:
  - `plugins/reference-openai-compatible-provider/tests/test_usage_extension_unit.py`
  - all new Z.ai hosted integration tests
  - `plugins/reference-openai-compatible-provider/tests/test_fireworks_integration_basic.py`