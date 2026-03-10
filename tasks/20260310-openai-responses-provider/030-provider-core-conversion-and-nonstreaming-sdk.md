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
