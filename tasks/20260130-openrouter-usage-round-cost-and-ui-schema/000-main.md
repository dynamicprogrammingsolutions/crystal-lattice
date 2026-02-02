# OpenRouter Usage Enhancements + Config-aware UI Schema

Improve the OpenRouter usage/cost tracking extension and add the missing UI-schema capabilities needed to make the new fields configurable per-session.

This task set is intentionally **separate** from the sandboxing prerequisites work, but it is related to (and should reference) the existing session-aware UI task:

- Related: `tasks/20260128-sandboxing-prereqs/040-session-aware-app-plugin-ui-and-conditions.md`

## Background / Current State

- OpenRouter usage extension (the one actually used by the plugin bundle) is:
  - `plugins/openrouter/src/openrouter_plugins/openrouter_usage_extension.py`
- This extension captures `native_chunk["usage"]` during **streaming**, stores it on the provider-native partial assistant message in `_metadata`, and mirrors it into core-message `metadata` in `from_native_messages`.
- BYOK cost comes back as `usage.cost == 0` and the real cost is in `usage.cost_details.upstream_inference_cost` (see example session below).

### Recent fix already applied

- The cumulative summing logic previously used the *current* chunk’s BYOK cost as a fallback while iterating prior messages.
- That bug was fixed in:
  - `plugins/openrouter/src/openrouter_plugins/openrouter_usage_extension.py`

## Example sessions (for real payload shapes)

- OpenRouter `usage` dict shape with BYOK fields:
  - `./.crystal/sessions/6d016aaf-bec9-491c-ba44-8b6dbb5944bd.json`
    - Example shows `usage.is_byok == True` and `usage.cost_details.upstream_inference_cost`.

## Subtasks

- `tasks/20260130-openrouter-usage-round-cost-and-ui-schema/010-config-aware-ui-schema-and-conditions.md`
- `tasks/20260130-openrouter-usage-round-cost-and-ui-schema/020-openrouter-round-cost.md`
- `tasks/20260130-openrouter-usage-round-cost-and-ui-schema/030-openrouter-cumulative-and-deleted-history-cost.md`
- `tasks/20260130-openrouter-usage-round-cost-and-ui-schema/040-openrouter-token-breakdown-and-ui-toggles.md`
- `tasks/20260130-openrouter-usage-round-cost-and-ui-schema/050-tests-and-fixtures.md`
