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

## Execution Plan Added During Completion

Date added: 2026-03-22

### Chosen approach

Implement this subtask in one staged pass, keeping `AgentCore` unchanged unless a blocker appears. The current package architecture is already close to the target: the provider is mostly a generic transport layer, while the remaining Ollama coupling lives in the reasoning extension, docs, default config, and thin test coverage.

Execution stages:

1. Provider cleanup and usage plumbing.
2. Reasoning extension generalization.
3. New generic usage extension.
4. Descriptor/export/doc/default-config updates.
5. Unit coverage for parsing/preservation.
6. Ollama-only integration verification.

### Concrete plan

#### 1. Refactor the provider surface

- Update `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/provider.py`.
- Remove unconditional `supports_thinking` from `get_tags()`.
- Keep the provider as a generic OpenAI-compatible transport.
- Add the minimum provider-side support needed for usage extraction in non-streaming mode.

Important implementation note:

- A usage extension alone cannot recover non-streaming usage with the current provider, because `call_api()` currently extracts only `choices[0].message` and drops the top-level completion payload, including `usage`.
- The provider should therefore preserve raw `usage` on the returned native assistant message, likely via `_metadata["usage"]`, so extensions can normalize it consistently.

#### 2. Rewrite the reasoning extension as parse/preserve logic

- Update `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/reasoning_extension.py`.
- Remove package-owned `think` schema, checkbox UI, init state, and request payload mutation.
- Stop treating Ollama `think` as a first-class package concept.
- Change dependency gating so the extension no longer requires `supports_thinking`.

Target behavior:

- Parse `reasoning` when present.
- Parse `reasoning_content` when present.
- Preserve `reasoning_details` unchanged when present.
- Accumulate streaming reasoning fragments conservatively.
- Preserve provider-native reasoning fields across tool rounds by writing assistant metadata fields back into native assistant messages in `to_native_messages()`.
- Restore those fields into core metadata from native messages in `from_native_messages()`.

Implementation guidance:

- Follow the same preservation pattern already used by `tools_extension.py` for `tool_calls` and `tool_call_id`.
- Keep reasoning payloads opaque and generic; do not normalize provider-specific detail schemas.
- Add a sensible fallback for length-mismatch cases if needed, so reasoning does not disappear when final/native lists differ.

#### 3. Add a minimal generic usage extension

- Create `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/usage_extension.py`.
- Export only a minimal shared metadata surface:
  - `metadata.usage`
  - `metadata.usage_prompt_tokens`
  - `metadata.usage_completion_tokens`
  - `metadata.usage_total_tokens`
  - `metadata.usage_reasoning_tokens` when present
  - formatted prompt/completion/total/reasoning token strings if straightforward and useful

Normalization constraints:

- Keep extra provider fields only inside raw `metadata.usage`.
- Do not add costs, cumulative-cost fields, routing metadata, caching metadata, or provider-branded token fields.
- For reasoning tokens, check common nested OpenAI-like shapes such as:
  - `completion_tokens_details.reasoning_tokens`
  - `output_tokens_details.reasoning_tokens`

#### 4. Update package exports and descriptor

- Update `plugins/reference-openai-compatible-provider/agent_plugin.json` to include the new usage extension entry.
- Update `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/__init__.py` to export the provider and extensions explicitly.

#### 5. Rewrite README to reflect the generalized package

- Update `plugins/reference-openai-compatible-provider/README.md`.
- Reframe the package as generic OpenAI-compatible chat-completions support.
- Present Ollama only as one example backend.
- Show reasoning enablement through `request_options`, for example `{"think": true}` for Ollama compatibility.
- Document that reasoning, tools, and usage are model/provider dependent.
- Document the new generic usage metadata behavior.

#### 6. Update the default Ollama config safely

- Update `application/python/agent_terminal_app/default_config/config.json`.
- Remove the top-level package-owned `think: true` from the default `ollama` provider entry.

Default-config recommendation:

- Prefer omitting default `request_options.think` in the public config unless local verification shows it is reliably safe across the default Ollama path.
- Rationale: `think` is model-fragile, and the public default config should not assume all Ollama models support it.
- Keep reasoning enablement documented as an opt-in example via `request_options`.

#### 7. Expand tests

Add or update unit tests for:

- extraction from `reasoning`
- extraction from `reasoning_content`
- preservation of `reasoning_details`
- preservation of reasoning metadata through `to_native_messages()` / `from_native_messages()`
- usage normalization from prompt/completion/total token counts
- reasoning token extraction from nested usage detail objects
- removal of package-owned `think` behavior

Add or update Ollama integration tests for:

- basic non-streaming request
- basic streaming request
- models/UI smoke test
- tool-calling request and tool loop continuation
- reasoning metadata with `request_options={"think": true}` when supported
- usage metadata when emitted, otherwise skip cleanly

If preserved reasoning through tool rounds cannot be exercised reliably on Ollama:

- cover that behavior with unit tests in this subtask
- leave stronger end-to-end verification to the hosted-provider subtasks

### Research conclusions preserved for the next agent

- No `AgentCore` change appears necessary for reasoning preservation. `AgentCore` already supports native-history continuity as long as provider-native fields are preserved in native messages and reconstructed in `from_native_messages()`.
- The current code comment in `core/python/agent_core/core.py` around native-history rebuilds is an explicit confirmation of this contract.
- The strongest internal reference for reasoning preservation is the OpenRouter reasoning extension, but only its preservation strategy should be borrowed; provider-specific request-shaping and extra metadata should not be ported.
- The existing tools extension in this package is already the right local pattern to follow for provider-native round-tripping.

## Completion Notes Added During Completion

Date added: 2026-03-22

### Implemented

- Generalized the reference provider package away from package-owned Ollama `think` behavior.
- Removed unconditional `supports_thinking` from `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/provider.py`.
- Added minimal non-streaming usage preservation in the provider by attaching top-level response `usage` to native assistant `_metadata`, enabling the new usage extension to normalize it.

- Rewrote `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/reasoning_extension.py` into a generic parse/preserve extension.
  - No package-owned `think` config schema or UI.
  - No request mutation.
  - Parses `reasoning`, `reasoning_content`, and `reasoning_details`.
  - Preserves reasoning metadata across tool rounds through `to_native_messages()` / `from_native_messages()`.
  - Includes a length-mismatch fallback so reasoning survives common final/native shape differences.

- Added `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/usage_extension.py`.
  - Normalizes `metadata.usage`.
  - Normalizes prompt/completion/total token counts.
  - Extracts reasoning token counts from common nested OpenAI-like usage shapes.
  - Captures streaming `usage` chunks into the provider partial state so final assistant messages can surface them.

- Updated package exports and descriptor:
  - `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/__init__.py`
  - `plugins/reference-openai-compatible-provider/agent_plugin.json`

- Rewrote `plugins/reference-openai-compatible-provider/README.md` to describe the package as generic OpenAI-compatible support, document Ollama only as an example backend, and show reasoning enablement via `request_options`.

- Updated `application/python/agent_terminal_app/default_config/config.json` so the public `ollama` entry no longer depends on package-owned top-level `think` config.

### Tests Added / Updated

- Added reasoning unit coverage in `plugins/reference-openai-compatible-provider/tests/test_reasoning_extension_unit.py`.
- Added usage unit coverage in `plugins/reference-openai-compatible-provider/tests/test_usage_extension_unit.py`.
- Updated provider tag expectations in `plugins/reference-openai-compatible-provider/tests/test_models_ui_unit.py`.
- Updated Ollama integration tests to register `RequestOptionsFeature` and use `request_options: {"think": true}` for reasoning enablement instead of package-owned `think`.
- Added `plugins/reference-openai-compatible-provider/tests/test_ollama_integration_usage.py` with clean skip behavior when Ollama does not emit usage.

### Verification Performed

- Ran formatting:
  - `python -m black plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider plugins/reference-openai-compatible-provider/tests`
- Ran package tests:
  - `pytest plugins/reference-openai-compatible-provider/tests -q`
  - Result: `25 passed, 1 skipped`
- Validated edited default config parses as JSON.

### Notes For Follow-up Subtasks

- This subtask keeps reasoning request enablement provider-agnostic by relying on `request_options`, but does not introduce hosted-provider-specific controls.
- Preserved reasoning through tool rounds is now covered at the package/unit level and ready for stronger hosted-provider verification in later subtasks.
- The new usage extension intentionally keeps the normalized surface minimal; hosted-provider subtasks should avoid expanding it with provider-specific billing metadata.

### Follow-up Adjustment Added During Completion

Date added: 2026-03-22

- Removed `reasoning_details` from the generic reference provider package surface after follow-up review.
- Final generic reasoning support in this package is limited to `reasoning` and `reasoning_content` only.
- Rationale: `reasoning_details` should remain provider-specific rather than being treated as shared OpenAI-compatible metadata in this package.