# Ollama-Safe Generalization

Short description: Refactor the reference OpenAI-compatible provider package to be more generic, add generic usage/reasoning support, and keep it verifiably working on Ollama before introducing hosted-provider verification.

Parent Task: tasks/20260322-reference-openai-compatible-provider-generalization/000-main.md
Depends On: None

## Why This Exists

This subtask creates the generic architecture and test surface while keeping verification local and low-risk. The package should still run correctly on Ollama after these changes, even though the package is no longer conceptually Ollama-specific.

## Scope

### In scope

- Remove or isolate Ollama-specific request-shaping from the package's generic extension logic.
- Make the reasoning extension generic enough to parse common OpenAI-like reasoning fields.
- Add a generic usage extension with minimum shared fields.
- Update package docs and plugin descriptor.
- Add more integration tests, but keep them runnable against Ollama only in this stage.
- Update default config so the `ollama` provider no longer relies on package-owned `think` config.

### Out of scope

- Hosted-provider verification.
- Fireworks/Together/SiliconFlow/DeepInfra-specific integration test setup.
- Adding provider-specific features beyond what can remain generic.

## Current Code References

- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/provider.py`
  - `get_tags()` currently claims `supports_thinking` for every backend.
  - `initialize_request()`, `call_api()`, and `stream_api()` are already a good generic base.
- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/reasoning_extension.py`
  - Uses `think` config.
  - Injects `payload["think"] = True`.
  - Only handles `reasoning`, not `reasoning_content` or `reasoning_details`.
- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/tools_extension.py`
  - Already generic enough to keep as the main tools extension.
- `plugins/reference-openai-compatible-provider/agent_plugin.json`
  - Needs a new entry for the usage extension once added.
- `plugins/reference-openai-compatible-provider/README.md`
  - Needs to stop presenting the package as Ollama-specific.
- `application/python/agent_terminal_app/default_config/config.json`
  - Current `ollama` entry uses `think: true` and should be migrated.

## Planned Changes

### 1. Reasoning extension generalization

Refactor the reasoning extension so it becomes a parsing/preservation extension instead of an Ollama-request-shaping extension.

Target behavior:

- Do not require a package-owned `think` config key for generic reasoning behavior.
- Prefer using `request_options` for provider/model-specific enablement.
- Parse and surface reasoning from these provider-native fields when present:
  - `reasoning`
  - `reasoning_content`
  - `reasoning_details`
- Preserve provider-native reasoning data in native history when it appears on assistant messages.
- Ensure preserved reasoning survives outbound native-history reconstruction for follow-up tool rounds, not just final-message metadata mapping.
- Keep in mind that preserved-reasoning behavior is becoming common across OpenAI-like providers and newer reasoning models, including GLM-5-style model families, so the extension should not assume Ollama-only or provider-specific semantics.

Recommended compatibility approach:

- Remove unconditional `supports_thinking` from the provider tag set.
- If temporary Ollama compatibility is needed, allow an opt-in compatibility path in docs/examples via `request_options: {"think": true}` rather than keeping `think` as a package-owned concept.

### 2. Add generic usage extension

Create a new extension in this package, for example:

- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/usage_extension.py`

Expected normalized metadata:

- `metadata.usage`
- `metadata.usage_prompt_tokens`
- `metadata.usage_completion_tokens`
- `metadata.usage_total_tokens`
- `metadata.usage_reasoning_tokens` when present
- formatted variants for prompt/completion/total/reasoning token counts if useful to existing UIs

Important constraints:

- Do not port OpenRouter cost/cumulative-cost logic.
- Keep any extra provider fields inside raw `metadata.usage` rather than normalizing provider-specific keys.
- Keep the normalized surface intentionally minimal and shared; avoid introducing provider-branded token or billing metadata.

### 3. Package descriptor and imports

Update these files:

- `plugins/reference-openai-compatible-provider/agent_plugin.json`
- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/__init__.py`

Add the new usage extension as an exported extension entry.

### 4. README rewrite

Rewrite `plugins/reference-openai-compatible-provider/README.md` so it:

- describes the package as generic OpenAI-compatible chat-completions support
- documents Ollama only as one example backend
- shows reasoning enablement through `request_options`
- documents the new generic usage extension behavior
- clearly explains that reasoning/tool/usage support is model/provider dependent

### 5. Ollama default config update

Update:

- `application/python/agent_terminal_app/default_config/config.json`

Replace the current Ollama `think: true` setup with `request_options` if Ollama reasoning should stay enabled by default.

Example target shape:

```json
"ollama": {
  "provider": "reference_openai_compatible",
  "base_url": "http://localhost:11434/v1",
  "model": "qwen3:0.6b",
  "timeout": 180,
  "request_options": {
    "think": true
  }
}
```

If this turns out to be too model-fragile for default config, document it and omit the default `think` request option.

Public config rule for this and later subtasks:

- Only secrets should be env-based in the public default config entries.
- Do not introduce public config env vars like `OLLAMA_MODEL`, `FIREWORKS_MODEL`, `TOGETHER_MODEL`, etc.
- Tests may still use provider-specific env vars or constants for model selection.

## Tests To Add Or Update

### Unit tests

Add or update unit tests for:

- reasoning field extraction from `reasoning`
- reasoning field extraction from `reasoning_content`
- preservation of `reasoning_details`
- usage normalization from `usage.prompt_tokens`, `usage.completion_tokens`, `usage.total_tokens`
- optional extraction of reasoning token counts when present in nested usage structures
- removal or deprecation of package-owned `think` handling

Suggested files:

- `plugins/reference-openai-compatible-provider/tests/test_reasoning_extension_unit.py`
- `plugins/reference-openai-compatible-provider/tests/test_usage_extension_unit.py`
- update existing merge/helper tests as needed

### Integration tests on Ollama only

Keep integration execution local in this stage.

Recommended test set:

- basic non-streaming request
- basic streaming request
- models/UI smoke test
- tool-calling request and tool loop continuation
- reasoning metadata test only when Ollama/model actually emits reasoning
- usage metadata test only if Ollama emits usage; otherwise the test should skip cleanly
- preserved reasoning through tool rounds test if Ollama/model supports it; otherwise this may remain unit-tested only in this subtask and become a hosted-provider integration requirement later

Suggested file changes:

- rename or replace `test_ollama_integration_basic.py`
- rename or replace `test_ollama_integration_tools_reasoning.py`
- add `test_ollama_integration_usage.py` if useful

Guidance:

- It is acceptable for some generic features to be untestable on Ollama and therefore only unit-tested in this subtask.
- Usage integration should be skipped if Ollama does not return `usage`.
- Reasoning integration should be skipped if the chosen model/server does not emit reasoning.
- If preserved reasoning through tool rounds cannot be reliably exercised on Ollama, add the unit/internals coverage needed here and leave the stronger end-to-end verification to hosted-provider subtasks.

## Verification Requirements

This subtask is complete only when:

1. The package no longer conceptually depends on Ollama-specific config like `think`.
2. Generic reasoning and usage code exists and is unit-tested.
3. Integration tests still pass against Ollama for the subset of features Ollama actually supports.
4. The default config still provides a working Ollama option.

## Risks / Watchouts

- Do not make reasoning support depend on tags that are too optimistic for all providers.
- Avoid introducing Fireworks- or OpenRouter-specific field names as package-wide normalized fields.
- Be careful preserving provider-native assistant message fields across tool rounds.
- If preserving `reasoning_content` requires changes to provider message conversion, keep them minimal and generic.