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

## Approved plan (added during completion)

1. Audit the current `openai_responses` provider and usage scaffold to confirm where usage data is available in non-streaming and streaming flows, and identify any remaining provider-owned usage behavior that must stay out of scope.
2. Implement `OpenAIResponsesUsageExtension` so it:
- extracts usage from `response.completed` chunks and non-streaming final native items,
- attaches raw `usage` plus formatted usage fields onto the final assistant message metadata,
- computes cumulative totals and turn-level totals with the same separator semantics expected by the existing UI,
- keeps all usage shaping/accounting in the extension only.
3. Add tests in `plugins/openai_responses/tests` covering:
- usage extraction + formatted fields,
- cumulative totals and turn-level totals,
- behavior with and without tool calls,
- integration coverage that final assistant messages expose usage metadata.
4. Run the relevant `pytest` targets for the new unit/integration coverage, then append completion notes to `tasks/20260310-openai-responses-provider/070-usage-extension-responses-api.md`.

## Completion notes (added during completion)

### What changed

1. Implemented `OpenAIResponsesUsageExtension` in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_usage_extension.py`.
- usage extraction now happens in the extension for streaming `response.completed` events
- non-streaming usage metadata is attached in the extension during `finalize`
- public metadata fields now match the existing OpenRouter usage extension field names:
  - `usage`
  - `has_tool_calls`
  - `usage_prompt_tokens_formatted`
  - `usage_cached_tokens_formatted`
  - `usage_completion_tokens_formatted`
  - `usage_total_cost_formatted`
  - `usage_total_cost_cumulative`
  - `usage_total_cost_cumulative_formatted`
  - `usage_turn_cost_cumulative`
  - `usage_turn_cost_cumulative_formatted`
  - `usage_turn_reasoning_tokens_cumulative`
  - `usage_turn_reasoning_tokens_cumulative_formatted`
- cumulative and turn-level accounting semantics were aligned with the OpenRouter usage extension separator behavior
- usage UI elements were updated to use the same field paths/templates as the OpenRouter usage extension

2. Made the minimal provider-side transport change needed for non-streaming extension visibility in `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`.
- provider now carries raw response usage in private native metadata key `_openai_responses_usage_raw`
- provider still does not attach public usage fields
- provider now strips `_openai_responses_*` helper metadata from provider->core metadata conversion so helper transport data does not leak into user-facing message metadata

3. Added unit coverage in `plugins/openai_responses/tests/test_openai_responses_usage_extension_unit.py`.
- streaming usage extraction + formatted fields
- tool-call turn detection and assistant-item attachment
- non-streaming finalize path using provider-private raw usage metadata
- UI field-path parity with the OpenRouter usage extension

4. Added integration coverage in `plugins/openai_responses/tests/test_openai_responses_usage_extension_integration.py`.
- real non-streaming OpenAI call using `OPENAI_API_KEY` from repo `.env`
- asserts final assistant message metadata includes usage fields
- asserts persisted native history contains attached usage metadata

### Files touched

1. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py`
2. `plugins/openai_responses/src/openai_responses_plugins/openai_responses_usage_extension.py`
3. `plugins/openai_responses/tests/test_openai_responses_usage_extension_unit.py`
4. `plugins/openai_responses/tests/test_openai_responses_usage_extension_integration.py`

### Tests run

1. `pytest plugins/openai_responses/tests/test_openai_responses_usage_extension_unit.py plugins/openai_responses/tests/test_openai_responses_usage_extension_integration.py plugins/openai_responses/tests/test_openai_responses_provider_unit.py -q`
- result: `27 passed`

2. `pytest plugins/openai_responses/tests -q`
- result: `46 passed`

3. `ruff check plugins/openai_responses/src/openai_responses_plugins/openai_responses_provider.py plugins/openai_responses/src/openai_responses_plugins/openai_responses_usage_extension.py plugins/openai_responses/tests/test_openai_responses_usage_extension_unit.py plugins/openai_responses/tests/test_openai_responses_usage_extension_integration.py`
- result: `All checks passed`

### Outcomes

1. Subtask `070` scope completed.
2. Public usage field names now match the existing OpenRouter usage extension field set.
3. Usage ownership is extension-centric; provider involvement is limited to private raw transport metadata needed for the non-streaming extension path.

### Open issues

1. OpenAI Responses usage payloads currently do not include cost fields in the real API responses exercised here, so cost-specific public fields are present only when the upstream payload includes cost information; cumulative cost fields still resolve deterministically to zero-valued totals when cost is absent.
