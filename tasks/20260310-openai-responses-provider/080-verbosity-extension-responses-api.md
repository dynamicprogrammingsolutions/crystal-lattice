# Verbosity Extension Responses API

Short description: Implement verbosity control in `openai_responses_verbosity` extension with model-gated tags and request payload shaping.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On: `tasks/20260310-openai-responses-provider/040-provider-streaming-event-normalization-and-finalization.md`

## Implementation

1. Implement verbosity config schema/UI.
2. Gate extension by capability tags (for example `supports_verbosity`).
3. Inject verbosity into request payload shape expected by Responses API.
4. Keep verbosity logic extension-only.

## Tests (required in this step)

1. Unit tests for init and request mutation behavior.
2. Unit tests for no-op behavior when verbosity is unset/invalid.
3. Unit tests for tag-gated visibility/activation.
4. Integration smoke test with verbosity set.

## References

- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_verbosity_extension.py`
- `plugins/openrouter_responses/tests/test_openrouter_verbosity_extension_unit.py`
- `plugins/openrouter_responses/tests/test_openrouter_verbosity_integration.py`

## Execution plan (added during completion)

1. Implement `OpenAIResponsesVerbosityExtension` so it validates/stores verbosity config, respects tag/UI gating, and injects `text.verbosity` into the Responses payload while preserving existing `text.format` data.
2. Add minimal provider capability tagging in `OpenAIResponsesProvider.get_tags()` so GPT-5 family models expose `supports_verbosity`, while keeping all request shaping in the extension.
3. Add unit tests covering init behavior, no-op behavior for unset/invalid values, tag-gated UI visibility, and request payload mutation.
4. Add one OpenAI integration smoke test that sends a real Responses request with verbosity enabled, using `OPENAI_API_KEY` from the repo root `.env`.
5. Run the relevant verbosity-focused test files and record results here in completion notes.

## Completion notes (added during completion)

### What changed

1. Implemented `OpenAIResponsesVerbosityExtension` in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_verbosity_extension.py`.
- Added config schema description.
- Added tag-gated UI visibility via `ext:openai_responses_verbosity`.
- Validated/stored verbosity state under `openai_responses_verbosity`.
- Injected `payload["text"]["verbosity"]` in `initialize_request` while preserving existing `text.format` and defaulting to `{"type": "text"}` when needed.

2. Added minimal provider capability gating in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`.
- `get_tags()` now adds `supports_verbosity` for GPT-5 family models only.
- No request shaping or verbosity behavior was added to the provider.

3. Added unit coverage in `plugins/openai_responses/tests/test_openai_responses_verbosity_extension_unit.py`.
- Covers metadata/tags, UI gating, init no-op/valid behavior, request no-op behavior, and payload mutation behavior.

4. Updated provider tag assertions in `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`.
- Added regression coverage that non-GPT-5 models do not advertise `supports_verbosity`.

5. Added integration smoke coverage in `plugins/openai_responses/tests/test_openai_responses_verbosity_integration.py`.
- Uses `OPENAI_API_KEY` from the repo root `.env`.
- Confirms a real non-streaming OpenAI Responses request succeeds with `verbosity="high"`.

### Files touched

1. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_verbosity_extension.py`
2. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
3. `plugins/openai_responses/tests/test_openai_responses_verbosity_extension_unit.py`
4. `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`
5. `plugins/openai_responses/tests/test_openai_responses_verbosity_integration.py`
6. `tasks/20260310-openai-responses-provider/080-verbosity-extension-responses-api.md`

### Tests run

1. `pytest plugins/openai_responses/tests/test_openai_responses_verbosity_extension_unit.py -q`
- result: `11 passed`

2. `pytest plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q`
- result: `23 passed`

3. `pytest plugins/openai_responses/tests/test_openai_responses_metadata_sanity.py -q`
- result: `2 passed`

4. `pytest plugins/openai_responses/tests/test_openai_responses_verbosity_integration.py -q`
- result: `1 passed`

### Outcomes

1. Verbosity remains extension-only.
2. Capability gating now works for GPT-5 family models.
3. Unit and OpenAI integration coverage for subtask 080 are in place and passing.

### Open issues

1. None blocking for subtask 080.
