# Provider Core Conversion And Nonstreaming SDK

Short description: Implement the OpenAI Responses provider core for non-streaming requests and core/native conversions, deliberately excluding tools/reasoning/usage/verbosity domain behaviors.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On: `tasks/20260310-openai-responses-provider/020-scaffold-openai-responses-plugin-package.md`

## Implementation

1. Implement provider identity/config:
- provider name/tag family (`provider:openai_responses`, `openai_responses`, `supports_streaming`)
- config keys (`model`, `api_key`, `base_url`, `timeout`)
- optional model discovery using SDK where feasible
2. Implement `init` and `initialize_request` for Responses endpoint.
3. Implement `to_native_messages` and `from_native_messages` for generic Responses item shapes.
4. Implement `call_api` using OpenAI SDK non-streaming call path.
5. Keep provider free of tools/reasoning/usage/verbosity business logic.

## Tests (required in this step)

1. Unit tests for config schema, tags, and request initialization.
2. Unit tests for core->native and native->core conversions (text, tool output item pass-through expectations, metadata retention).
3. Unit tests for non-streaming call path with mocked SDK client.
4. Negative-path tests for bad payload/config and error handling.

## References

- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/provider.py`
- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py`
- `core/python/agent_core/plugin/provider.py`

## Completion notes (added during completion)

### Changes made

1. Implemented provider core in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`:
- provider identity/config/tags preserved as:
  - `provider:openai_responses`
  - `openai_responses`
  - `supports_streaming`
- strict config resolution/validation for `model`, `api_key`, `base_url`, `timeout`
- env-based API key resolution (`config.api_key` fallback to `OPENAI_API_KEY`)
- `init` now creates normalized config + SDK client (`OpenAI(...)`)
- `initialize_request` now builds canonical `/responses` request envelope in state
- implemented generic `to_native_messages` / `from_native_messages`:
  - message item conversion for core roles (`system`, `user`, `assistant`, `developer`)
  - `tool` role conversion to `function_call_output`
  - `_metadata` round-trip retention (excluding `native_indices`)
  - per-message `native_indices` reconstruction on provider->core conversion
- implemented non-streaming `call_api` via OpenAI SDK:
  - validates native input items
  - strips internal `_metadata` before send
  - calls `client.responses.create(..., stream=False)`
  - normalizes SDK response payload and extracts output items
  - attaches response metadata (`response_id` and `usage`) to native output items
- kept streaming/process/finalize as minimal no-op placeholders for later streaming subtask.

2. Added dedicated unit tests for 030 scope in:
- `plugins/openai_responses/tests/test_openai_responses_provider_unit.py`

3. Added real API integration test (model `gpt-5-mini`) in:
- `plugins/openai_responses/tests/test_openai_responses_provider_integration.py`

4. Added reproducible fixture generation script + generated fixture:
- script: `plugins/openai_responses/tests/scripts/generate_nonstreaming_fixture.py`
- fixture: `plugins/openai_responses/tests/fixtures/openai_responses_gpt5mini_nonstreaming.json`

### Tests run

1. `pytest plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q`
- result: `10 passed`

2. `pytest plugins/openai_responses/tests/test_openai_responses_provider_integration.py -q`
- result: `1 passed`

3. `pytest plugins/openai_responses/tests -q`
- result: `16 passed`

### Open issues

1. None blocking for subtask 030.
2. Streaming normalization/finalization remains intentionally deferred to subtask 040.
