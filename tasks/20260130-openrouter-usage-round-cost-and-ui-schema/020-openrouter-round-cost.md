Parent Task: tasks/20260130-openrouter-usage-round-cost-and-ui-schema/000-main.md

Depends On:
- tasks/20260130-openrouter-usage-round-cost-and-ui-schema/010-config-aware-ui-schema-and-conditions.md

# OpenRouter “Rond cost” / round-cost field

Add a “Round cost” (user called it “Rond cost”) computed as **total assistant cost since the last user message**, and show it only on the final assistant message for the round (the one that has no tool calls).

## Where to implement

- Extension code: `plugins/openrouter/src/openrouter_plugins/openrouter_usage_extension.py`

This extension already:

- Extracts `usage` from streaming chunks.
- Computes `current_cost` using `usage.cost` or BYOK fallback `usage.cost_details.upstream_inference_cost`.
- Attaches metadata to the provider-native partial assistant message in `state["partial"]`.
- Mirrors those `_metadata` fields into core message metadata in `from_native_messages`.

## Desired behavior

- Only on the “final” assistant message of a tool loop turn:
  - Definition: assistant message where `tool_calls` is missing or empty.
  - (Tool-call assistant messages should not show round cost.)
- `round_cost` includes:
  - The cost of any intermediate assistant messages after the last user message (including tool-call assistant messages)
  - Plus the cost of the final assistant message itself.

## Proposed metadata keys

Attach to current assistant message `_metadata` (and mirror into core message `metadata`):

- `usage_total_cost_round` (float)
- `usage_total_cost_round_formatted` (string, e.g. `$0.002066`)

Label:

- UI template should say `Rond cost: {{data}}` if you want to preserve the user-facing spelling.

## Round-cost calculation approach

At the moment we process the final usage chunk for the current request, we have:

- `native_messages`: provider-native history up to this request (does not necessarily include the current assistant partial)
- `state["partial"]`: provider-native partial assistant message for this request (includes `tool_calls` if it’s a tool-call message)
- `usage` dict for the current request (contains tokens and cost)

Algorithm (sum-from-last-user boundary):

1) Identify the last user message index in `native_messages`.
2) For all provider-native assistant messages *after* that user index, sum their per-message cost from `_metadata.usage`.
   - Use the same BYOK-aware cost extraction helper as cumulative cost.
3) Add `current_cost` for the current assistant message.

Why this works:

- In this agent architecture, tool calls produce additional assistant/tool messages after the last user message.
- The “round” is defined by the segment between the last user message and the final assistant completion.

Edge cases:

- No prior user messages: treat boundary as “start of history”.
- Missing prior usage on intermediate assistant messages: treat missing cost as `0.0`.
- If the current message has tool calls: do not attach round-cost metadata.

## UI schema changes

This is where dynamic UI schema (Subtask 010) matters:

- Add config toggle (per session override): e.g. `openrouter_usage_show_round_cost: bool`.
- Implement config-aware UI elements to include the footer when enabled.
  - `{"ui_type": "message_footer", "data": "metadata.usage_total_cost_round_formatted", "template": "Rond cost: {{data}}"}`

Without the dynamic UI schema work, you could still add this footer unconditionally, but it won’t be switchable per session.

## Acceptance criteria

- Final assistant messages (no tool calls) include `metadata.usage_total_cost_round(_formatted)`.
- Tool-call assistant messages do not include the round-cost fields.
- When enabled, the UI schema includes a footer element rendering “Rond cost”.
