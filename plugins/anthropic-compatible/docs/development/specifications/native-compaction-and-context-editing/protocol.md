# Anthropic native context-management protocol

## Betas

| Behavior | Required beta |
|---|---|
| `compact_20260112` | `compact-2026-01-12` |
| `clear_thinking_20251015` | `context-management-2025-06-27` |
| `clear_tool_uses_20250919` | `context-management-2025-06-27` |

A request combining compaction and clearing strategies requires both betas.

## Edit ordering

Extension-generated edits use this order:

1. `clear_thinking_20251015`;
2. `clear_tool_uses_20250919`;
3. `compact_20260112`.

Raw `request_options.context_management` is applied later and may replace the
complete extension-generated value.

## Compaction request

```json
{
  "context_management": {
    "edits": [
      {
        "type": "compact_20260112",
        "trigger": {
          "type": "input_tokens",
          "value": 150000
        },
        "pause_after_compaction": false
      }
    ]
  }
}
```

`instructions` is optional. The trigger value must be at least 50,000.

## Context-editing requests

Retain all thinking:

```json
{
  "type": "clear_thinking_20251015",
  "keep": "all"
}
```

Retain a bounded number of recent thinking turns:

```json
{
  "type": "clear_thinking_20251015",
  "keep": {
    "type": "thinking_turns",
    "value": 2
  }
}
```

Clear old tool uses:

```json
{
  "type": "clear_tool_uses_20250919",
  "trigger": {
    "type": "input_tokens",
    "value": 100000
  },
  "keep": {
    "type": "tool_uses",
    "value": 3
  },
  "clear_tool_inputs": false
}
```

`clear_at_least` and `exclude_tools` are optional.

## Compaction response block

```json
{
  "type": "compaction",
  "content": "<summary or null>",
  "encrypted_content": "<opaque continuation data or null>"
}
```

The complete block is provider-native continuation data. Unknown additive
fields and optional `cache_control` values are preserved.

Streaming starts the same block and applies:

```json
{
  "type": "compaction_delta",
  "content": "<current summary or null>",
  "encrypted_content": "<current opaque data or null>"
}
```

The delta replaces current values; it is not concatenated.

## Completion and pause

The supported extension path sends `pause_after_compaction: false`, so the
request proceeds to an ordinary terminal or tool-use stop reason.

Raw configurations using `true` may receive
`stop_reason: "compaction"`. Managed automatic resubmission is outside this
specification.

## Applied edits

`message_delta.context_management.applied_edits` can report:

- `cleared_input_tokens`;
- `cleared_thinking_turns`;
- `cleared_tool_uses`.

These values are response statistics. They do not replace local history.

## Iteration usage

`usage.iterations` can contain entries with:

- `type: "message"`;
- `type: "compaction"`;
- future additive iteration types.

Known message and compaction entries contribute to normalized billable totals.
Compaction entries also contribute to the separate compaction usage detail.
Unknown iteration types remain in raw provider usage and are ignored
conservatively by normalized calculations until supported.