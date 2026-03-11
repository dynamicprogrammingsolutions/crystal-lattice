# Reasoning Extension Responses API

Short description: Implement reasoning-specific logic in `openai_responses_reasoning` extension, including request-side config wiring and metadata extraction from streaming/final responses.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On: `tasks/20260310-openai-responses-provider/040-provider-streaming-event-normalization-and-finalization.md`

## Implementation

1. Implement reasoning config schema/UI (`enable_reasoning`, `reasoning_effort`, optional `reasoning_summary`, optional max tokens).
2. Merge reasoning settings into request flow (prefer `request_options` pattern when appropriate).
3. Parse reasoning deltas/items in extension `process_chunk`.
4. Surface reasoning fields in core metadata in `from_native_messages`.
5. Keep provider free of reasoning business logic as far as possible.

## Tests (required in this step)

1. Unit tests for config -> request mutation behavior.
2. Unit tests for reasoning delta accumulation behavior.
3. Unit tests for final metadata extraction.
4. Integration tests covering non-streaming and streaming reasoning visibility.

## References

- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_reasoning_extension.py`
- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/reasoning_extension.py`
- `core/python/plugins/request_options_feature.py`

## Approved plan (added during completion)

1. Implement `OpenAIResponsesReasoningExtension` in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py` so it:
- stores reasoning config in extension state during `init`
- merges reasoning options into `config.request_options` during `initialize_request`
- accumulates streaming reasoning metadata from Responses events in `process_chunk`
- attaches reasoning metadata to final assistant messages in `finalize` and `from_native_messages`
2. Make the minimum provider-side capability change in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py` to advertise reasoning support tags only, without moving reasoning logic into the provider.
3. Add dedicated unit tests for request shaping, streaming accumulation, and final metadata extraction in a new reasoning-focused test file under `plugins/openai_responses/tests/`.
4. Add integration coverage, likely by extending `plugins/openai_responses/tests/test_openai_responses_provider_integration.py` or adding a sibling reasoning integration file, using `RequestOptionsFeature` so the extension can actually participate in the request pipeline.
5. Run the relevant `plugins/openai_responses` tests, then append the approved plan and completion notes to this task file.

## Completion notes (added during completion)

### What changed

1. Implemented reasoning request shaping and metadata extraction in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py`.
- reasoning config is normalized during `init`
- reasoning options are merged into `config.request_options.reasoning` during `initialize_request`
- streaming reasoning deltas and reasoning output items are accumulated in extension-owned state during `process_chunk`
- reasoning metadata is attached to final assistant native items in `process_chunk`/`finalize`
- reasoning metadata is also reconstructed from native indices in `from_native_messages`

2. Added the minimum provider-side capability tags in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`.
- provider now advertises `supports_reasoning` and `supports_reasoning_effort`
- no reasoning request shaping or reasoning extraction logic was moved into the provider

3. Added unit coverage in `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py`.
- request config to `request_options` mutation
- streaming reasoning delta accumulation into partial metadata
- reasoning metadata extraction from native indices
- scripted streaming integration through `AgentCore.send_request_stream`

4. Added real integration coverage in `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py`.
- non-streaming reasoning metadata visibility with the real OpenAI Responses API
- streaming reasoning metadata visibility with the real OpenAI Responses API

5. Updated provider tag expectations in `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`.

### Files touched

1. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_reasoning_extension.py`
2. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
3. `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py`
4. `plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py`
5. `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`
6. `tasks/20260310-openai-responses-provider/060-reasoning-extension-responses-api.md`

### Tests run

1. `pytest plugins/openai_responses/tests/test_openai_responses_reasoning_extension_unit.py -q`
- result: `4 passed`

2. `pytest plugins/openai_responses/tests/test_openai_responses_reasoning_extension_integration.py -q`
- result: `2 passed`

3. `pytest plugins/openai_responses/tests -q`
- result: `40 passed`

### Outcomes

1. Subtask `060` implemented within extension-owned scope.
2. Reasoning request shaping now works with the OpenAI Responses API request format used by the SDK.
3. Final assistant metadata exposes reasoning output via extension logic in both non-streaming and streaming flows.

### Open issues

1. `enable_reasoning` is translated into a valid Responses API `reasoning.effort` value rather than sending `reasoning.enabled`, because the OpenAI Responses API rejected `reasoning.enabled` during real integration testing.
