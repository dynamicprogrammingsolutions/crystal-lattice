# Provider Streaming Event Normalization And Finalization

Short description: Implement OpenAI SDK streaming handling in provider, including event normalization and finalize behavior, without moving tools/reasoning/usage/verbosity domain logic into provider.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On: `tasks/20260310-openai-responses-provider/030-provider-core-conversion-and-nonstreaming-sdk.md`

## Implementation

1. Implement `stream_api` with OpenAI SDK streaming API.
2. Normalize SDK events into provider-native chunk dicts suitable for extension processing.
3. Implement provider `process_chunk` and `finalize` for generic text/lifecycle handling.
4. Ensure full native history invariants are preserved in streaming path.
5. Do not implement extension-owned logic (tool/reasoning/usage/verbosity) here.

## Tests (required in this step)

1. Unit tests for streaming event normalization from mocked SDK stream events.
2. Unit tests for partial emission + finalize semantics.
3. Unit tests ensuring no raw chunk artifacts pollute native history.
4. Regression tests for provider wrapper compatibility (`send_request_stream` behavior).

## References

- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py`
- `core/python/agent_core/plugin/provider.py`
- `plugins/docs/provider-plugins.md`
