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

## Review note (added after review of subtask 030)

1. Usage extraction/attachment logic currently present in `openai_responses_provider` must be moved into this extension during 070 completion.
2. 070 should include removing provider-owned usage shaping and re-homing behavior here:
- extract usage from non-streaming response object and streaming completion payloads
- attach raw usage and formatted usage metadata to final assistant message(s)
- keep cumulative accounting semantics in extension-only code
