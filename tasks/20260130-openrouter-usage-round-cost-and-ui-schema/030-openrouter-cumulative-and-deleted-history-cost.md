Parent Task: tasks/20260130-openrouter-usage-round-cost-and-ui-schema/000-main.md

Depends On:
- tasks/20260130-openrouter-usage-round-cost-and-ui-schema/010-config-aware-ui-schema-and-conditions.md

# Incremental cumulative cost + deleted/summarized history cost

Improve cumulative cost tracking so it remains stable across message deletion/summarization, and optionally expose “deleted/summarized history cost” as a separate field.

## Background

The current OpenRouter usage extension computes cumulative cost by summing per-message costs from prior assistant messages each time it sees a `usage` chunk:

- `plugins/openrouter/src/openrouter_plugins/openrouter_usage_extension.py` (see the loop near where `base_total` is computed)

This has two shortcomings:

1) It can’t intentionally preserve a “total cost so far” when prior messages are deleted/summarized (because the history is gone).
2) It can’t expose the delta (“cost of deleted/summarized history”) without comparing to another baseline.

## Example session / observed structure

Session with BYOK usage payload:

- `./.crystal/sessions/6d016aaf-bec9-491c-ba44-8b6dbb5944bd.json`
  - BYOK has `usage.cost == 0` and real cost at `usage.cost_details.upstream_inference_cost`.
  - The message metadata includes `usage_total_cost_cumulative` and shows a delta between that and current-cost.

## Desired behavior

### A) Incremental cumulative cost

Instead of recalculating from scratch, track cumulative cost as:

- `new_total = last_known_total + current_message_cost`

Where `last_known_total` is taken from the last assistant message in retained native history that has `_metadata.usage_total_cost_cumulative`.

Fallback:

- If no previous `usage_total_cost_cumulative` exists (first usage-bearing message), compute `last_known_total` by summing visible per-message costs in history.

This makes totals stable across:

- User deleting messages
- Summarization that removes a range of messages

…because the remaining messages can still carry a “total so far” forward.

### B) Deleted/summarized history cost (delta)

Compute:

- `visible_total = sum(cost of assistant messages that are still present in native_messages) + current_cost`
- `deleted_cost = max(0, new_total - visible_total)`

Interpretation:

- If messages were deleted/summarized, `new_total` preserves historical cost (via incremental tracking) while `visible_total` can only see remaining messages.
- The delta approximates “cost of deleted/summarized history”.

## Proposed metadata keys

On the current assistant message `_metadata` (and mirrored into core metadata):

- Existing:
  - `usage_total_cost_cumulative`
  - `usage_total_cost_cumulative_formatted`

- New (only when enabled):
  - `usage_total_cost_deleted`
  - `usage_total_cost_deleted_formatted`

## UI schema changes

Per-session toggle via config override (requires Subtask 010):

- `openrouter_usage_show_deleted_cost: bool`

UI element recommendation:

- Keep total cost in status bar:
  - `metadata.usage_total_cost_cumulative_formatted`
- Add a second status-bar entry for deleted cost when enabled:
  - `metadata.usage_total_cost_deleted_formatted` with template `Deleted: {{data}}`

Rationale: the template system currently only supports `{{data}}`; using a second entry avoids expanding template syntax.

## Implementation notes

- Use a single helper to extract numeric cost from a `usage` dict:
  - Prefer `usage["cost"]` if non-zero/truthy.
  - Otherwise use `usage["cost_details"]["upstream_inference_cost"]`.
- Be careful with BYOK `cost == 0` which is falsy; this is why the existing `or` fallback works.
- Clamp `deleted_cost` at `>= 0` to avoid negative results caused by historical bugs or malformed data.

## Acceptance criteria

- Cumulative cost continues increasing correctly even after message deletions/summarization.
- When enabled, an additional “Deleted:” status-bar field is shown and is `0` when no history was deleted.
