Parent Task: tasks/20260130-openrouter-usage-round-cost-and-ui-schema/000-main.md

Depends On:
- tasks/20260130-openrouter-usage-round-cost-and-ui-schema/020-openrouter-round-cost.md
- tasks/20260130-openrouter-usage-round-cost-and-ui-schema/030-openrouter-cumulative-and-deleted-history-cost.md
- tasks/20260130-openrouter-usage-round-cost-and-ui-schema/040-openrouter-token-breakdown-and-ui-toggles.md

# Tests + fixtures for OpenRouter usage extension

Add regression tests for the new cost/token fields.

## Scope

Test the plugin-bundle version of the extension:

- `plugins/openrouter/src/openrouter_plugins/openrouter_usage_extension.py`

Avoid relying on live OpenRouter API calls; use unit tests that call `process_chunk()` and `from_native_messages()` directly.

## Suggested test file

- Add: `plugins/openrouter/tests/test_openrouter_usage_extension_unit.py`

## Useful fixtures

### A) Real usage dict shape

Use the BYOK sample payload from:

- `./.crystal/sessions/6d016aaf-bec9-491c-ba44-8b6dbb5944bd.json`

Expected properties (as observed):

- `usage.is_byok == True`
- `usage.cost == 0`
- `usage.cost_details.upstream_inference_cost` is a float
- `usage.completion_tokens_details.reasoning_tokens` present

### B) Minimal streaming chunk

Construct a fake streaming chunk that matches what the provider passes to extensions:

```python
native_chunk = {"usage": usage_dict}
```

You don’t need full `choices` content for these tests since the usage extension only reads `native_chunk["usage"]`.

## Test cases

1) BYOK cost extraction

- Given `usage.cost == 0` and `usage.cost_details.upstream_inference_cost == X`, verify:
  - `usage_total_cost_formatted == f"${X:.6f}"`

2) Incremental cumulative total

- Given prior assistant native message with `_metadata.usage_total_cost_cumulative == A` and current cost `B`, verify:
  - New message has cumulative `A + B`.

3) Deleted/summarized delta

- Arrange history so that:
  - Last known cumulative is `A`.
  - Visible per-message sum is `V`.
  - Current cost is `B`.
- Verify:
  - `deleted_cost == max(0, (A + B) - (V + B)) == max(0, A - V)`.

4) Round cost

- Arrange `native_messages` with:
  - … older messages
  - last `role == "user"`
  - then one or more assistant messages (including tool-call ones)
- Verify round cost equals sum of assistant costs after last user + current cost.

5) No tool calls gating

- When `state["partial"]` contains `tool_calls` (non-empty), verify round-cost fields are NOT written.
- When tool_calls missing/empty, verify they ARE written.

## Notes / gotchas

- `process_chunk()` writes `_metadata` onto `state["partial"]`, so tests must provide `state = {"partial": {...}}`.
- The extension does not currently capture usage for non-streaming `call_api()` responses; keep tests scoped to streaming behavior unless you explicitly extend non-streaming handling.
