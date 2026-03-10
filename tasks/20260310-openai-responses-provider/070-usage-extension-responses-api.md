# Usage Extension Responses API

Short description: Implement usage/cost tracking in `openai_responses_usage` extension, including formatted metadata fields for UI and cumulative accounting behavior.

Parent Task: `tasks/20260310-openai-responses-provider/000-main.md`

Depends On: `tasks/20260310-openai-responses-provider/040-provider-streaming-event-normalization-and-finalization.md`

## Implementation

1. Implement usage extraction from Responses lifecycle events/final objects.
2. Attach raw usage metadata and formatted fields.
3. Implement cumulative accounting semantics compatible with existing UI expectations.
4. Keep usage logic extension-only.

## Tests (required in this step)

1. Unit tests for usage extraction and formatted fields.
2. Unit tests for cumulative totals and turn-level totals.
3. Unit tests for behavior with/without tool calls.
4. Integration test asserting usage metadata availability on final assistant messages.

## References

- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_usage_extension.py`
- `plugins/openrouter_responses/tests/test_openrouter_usage_extension_unit.py`
- `plugins/openrouter_responses/tests/test_openrouter_usage_extension_integration.py`
