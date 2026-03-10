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
