# Anthropic native context management

The Anthropic-compatible package provides two optional provider extensions:

- `AnthropicCompactionExtension` for automatic native compaction;
- `AnthropicContextEditingExtension` for thinking retention and tool-use
  clearing.

These features use Anthropic's native Messages context-management protocol.
They do not replace provider-independent prompt summarization and do not
delete the visible conversation.

## Availability

The selected model's discovered capability descriptor enables each extension
independently.

- Compaction requires `compact_20260112`.
- Context editing requires thinking clearing, tool-use clearing, or both.

Compatible endpoints without capability descriptors can opt in explicitly:

```json
{
  "capabilities": {
    "anthropic_compaction": true,
    "anthropic_context_editing": true
  }
}
```

These booleans expose the feature extensions. They do not make an incompatible
endpoint accept Anthropic fields.

## Automatic compaction

The extension schema defaults compaction to disabled so package users opt in
explicitly. The shipped direct Anthropic configuration enables it for models
that advertise support:

```json
{
  "enable_anthropic_compaction": true,
  "anthropic_compaction_trigger_tokens": 150000,
  "anthropic_compaction_instructions": "Preserve decisions and unresolved work."
}
```

Settings:

| Setting | Default | Purpose |
|---|---:|---|
| `enable_anthropic_compaction` | `false` | Enables automatic request-time compaction |
| `anthropic_compaction_trigger_tokens` | `150000` | Input-token threshold; minimum `50000` |
| `anthropic_compaction_instructions` | omitted | Additional summary guidance |

The shipped direct configuration uses `800000` for the current
one-million-token Sonnet and Opus models.

The extension adds:

```json
{
  "type": "compact_20260112",
  "trigger": {
    "type": "input_tokens",
    "value": 150000
  },
  "pause_after_compaction": false
}
```

It also selects the required `compact-2026-01-12` beta for that request.

When compaction occurs, Anthropic returns a `compaction` content block. The
package stores the complete block, including opaque encrypted continuation
data, in provider-native history and sends it unchanged on later requests.
Encrypted content is not copied into public message metadata.

The visible assistant metadata includes:

- `anthropic_compaction.occurred`;
- `anthropic_compaction.block_count`;
- `anthropic_compaction.readable_summary_count`.

## Thinking retention

`anthropic_thinking_retention` accepts:

- `provider_default`: do not add a thinking-retention edit;
- `all`: retain all thinking turns;
- `turns`: retain the number selected by
  `anthropic_thinking_turns_to_keep`.

Example:

```json
{
  "anthropic_thinking_retention": "turns",
  "anthropic_thinking_turns_to_keep": 2
}
```

The `all` mode maps to:

```json
{
  "type": "clear_thinking_20251015",
  "keep": "all"
}
```

The shipped direct Anthropic configuration uses `all`.

## Tool-use clearing

The extension schema defaults tool-use clearing to disabled. The shipped
direct Anthropic configuration enables it, uses a `100000` token trigger, and
keeps five recent tool uses:

```json
{
  "enable_anthropic_tool_use_clearing": true,
  "anthropic_tool_use_clear_trigger_tokens": 100000,
  "anthropic_tool_uses_to_keep": 5,
  "anthropic_tool_use_clear_at_least_tokens": 10000,
  "anthropic_clear_tool_inputs": false,
  "anthropic_tool_use_excluded_tools": ["read_file"]
}
```

Settings:

| Setting | Default | Purpose |
|---|---:|---|
| `enable_anthropic_tool_use_clearing` | `false` | Enables old tool-use clearing |
| `anthropic_tool_use_clear_trigger_tokens` | `100000` | Input-token threshold; minimum `10000` |
| `anthropic_tool_uses_to_keep` | `3` | Most recent tool uses retained |
| `anthropic_tool_use_clear_at_least_tokens` | omitted | Minimum tokens that must be removable |
| `anthropic_clear_tool_inputs` | `false` | Also clear tool inputs |
| `anthropic_tool_use_excluded_tools` | `[]` | Tool names never cleared |

Current one-million-token Sonnet and Opus defaults raise the tool-use clearing
trigger to `200000`.

Thinking retention is added before tool-use clearing, as required by the
Anthropic context-editing protocol. Compaction is added after both clearing
strategies.

Context editing uses the `context-management-2025-06-27` beta. Applied edit
statistics are surfaced through:

- `anthropic_context_editing.applied_edit_count`;
- `anthropic_context_editing.cleared_input_tokens`;
- `anthropic_context_editing.cleared_thinking_turns`;
- `anthropic_context_editing.cleared_tool_uses`.

The provider may remove these items from the context it evaluates, but the
package keeps the local transcript and canonical native history intact.

## Session settings

Supported models expose six primary session settings:

- enable automatic compaction;
- compaction trigger tokens;
- thinking retention;
- enable tool-use clearing;
- tool-use clearing trigger tokens;
- recent tool uses to keep.

These are session policies and are not pinned into the message composer.

Expert settings remain configuration-only:

- `anthropic_compaction_instructions`;
- `anthropic_thinking_turns_to_keep`;
- `anthropic_tool_use_clear_at_least_tokens`;
- `anthropic_clear_tool_inputs`;
- `anthropic_tool_use_excluded_tools`.

When recent-turn thinking retention is selected, its UI label shows the
configured count. Set the count in configuration when a value other than the
default latest turn is needed.

## Raw request options

`request_options.context_management` is applied after both extensions and
replaces their generated context-management object. This remains the escape
hatch for provider fields not represented by extension settings.

Raw context-management edits must configure the corresponding provider beta.
An explicit `anthropic-beta` header remains authoritative and is validated
against the final edit list.

## Usage

When Anthropic reports `usage.iterations`, the usage extension sums all
message and compaction iterations exactly once. It exposes separate
compaction fields including:

- `usage_compaction_iterations`;
- `usage_compaction_input_tokens`;
- `usage_compaction_output_tokens`;
- `usage_compaction_cached_tokens`;
- `usage_compaction_cache_write_tokens`;
- 5-minute and 1-hour compaction cache-write tokens.

Turn and session cumulative usage, plus duration/TPS integration, use the same
complete normalized totals.

## Limitations

- Native compaction is automatic and token-triggered; there is no manual
  visible-prefix action.
- The package currently sends `pause_after_compaction: false`.
- Managed automatic continuation for raw
  `pause_after_compaction: true` requests is not provided.
- The package retains pre-compaction local/native history. Anthropic treats the
  returned compaction block as continuation state.
- Compatible endpoints may reject explicitly enabled features through their
  normal provider error.

## Verification

Fast deterministic suite:

```bash
pytest plugins/anthropic-compatible/tests -q
```

Local compatible-endpoint omission and regression coverage:

```bash
pytest plugins/anthropic-compatible/tests \
  -m "integration and ollama and not slow_integration" -q
```

The real long-context compaction test is intentionally slow and uses the
hosted API:

```bash
pytest \
  plugins/anthropic-compatible/tests/test_anthropic_compaction_api_integration.py \
  -m "integration and api and anthropic and slow_integration" -q
```