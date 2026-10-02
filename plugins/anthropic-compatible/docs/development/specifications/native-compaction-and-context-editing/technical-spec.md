# Anthropic native context-management technical specification

## Architecture

```text
AnthropicProvider
  beta transport composition, raw event reduction, cancellation

AnthropicContextEditingExtension
  context-editing capability, config/UI, clearing edits, applied-edit metadata

AnthropicCompactionExtension
  compaction capability, config/UI, compaction edit, block interpretation

AnthropicUsageExtension
  iteration-aware normalized usage and compaction token details
```

The two feature extensions share package-private pure helpers for capability
inspection, context-management edit composition, and request-local beta
requirements. Neither extension owns credentials, SDK clients, retries, or
request cancellation.

## Capability gating

The official selected-model descriptor is primary:

- `context_management.compact_20260112.supported` enables the compaction tag;
- `context_management.clear_thinking_20251015.supported` or
  `clear_tool_uses_20250919.supported` enables the context-editing tag.

Compatible endpoints may declare:

```json
{
  "capabilities": {
    "anthropic_compaction": true,
    "anthropic_context_editing": true
  }
}
```

Values are boolean feature gates only. They do not validate, filter, or
rewrite explicit request options. There is no compaction model-name fallback.

## Configuration

`AnthropicCompactionExtension` owns:

| Key | Behavior |
|---|---|
| `enable_anthropic_compaction` | Opt into automatic compaction; default `false` |
| `anthropic_compaction_trigger_tokens` | Input-token trigger; default `150000`, minimum `50000` |
| `anthropic_compaction_instructions` | Optional summary instructions |

`AnthropicContextEditingExtension` owns:

| Key | Behavior |
|---|---|
| `anthropic_thinking_retention` | `provider_default`, `all`, or `turns` |
| `anthropic_thinking_turns_to_keep` | Positive count used by `turns` |
| `enable_anthropic_tool_use_clearing` | Enable tool-use clearing |
| `anthropic_tool_use_clear_trigger_tokens` | Input-token trigger; default `100000`, minimum `10000` |
| `anthropic_tool_uses_to_keep` | Recent tool uses retained; default `3` |
| `anthropic_tool_use_clear_at_least_tokens` | Optional minimum removable token count |
| `anthropic_clear_tool_inputs` | Whether tool inputs are also cleared |
| `anthropic_tool_use_excluded_tools` | Tool names excluded from clearing |

The common scalar settings have ordinary config UI. Advanced list/minimum
settings remain config-only when exposing them would add persistent inactive
controls or provider-protocol detail without a common user benefit.

The shipped direct Anthropic provider explicitly sets:

```json
{
  "enable_anthropic_compaction": true,
  "anthropic_compaction_trigger_tokens": 150000,
  "anthropic_thinking_retention": "all",
  "enable_anthropic_tool_use_clearing": true,
  "anthropic_tool_use_clear_trigger_tokens": 100000,
  "anthropic_tool_uses_to_keep": 5
}
```

Known one-million-token variants override only the two trigger values. Feature
extensions still require capability tags, so configured defaults do not send
unsupported fields.

UI exposes six primary settings: compaction enablement/trigger, thinking
retention, and tool-use clearing enablement/trigger/retained count.
Compaction instructions, recent-thinking count, clear-at-least threshold,
input clearing, and excluded tools remain configuration-only.

## Request lifecycle

1. Model discovery preserves official capability descriptors.
2. Provider/extension tag resolution enables only supported optional features.
3. Context editing contributes thinking retention and then tool-use clearing.
4. Compaction appends its edit last.
5. Each active extension records its request-local required beta.
6. Generic request options run afterward and remain the final request-body
   override.
7. The provider validates the final edit list against effective betas and
   selects the beta SDK Messages resource.

Request-local beta requirements are composed with configured `betas` and
`beta_headers`. An explicit `anthropic-beta` request/header value retains the
existing precedence. If it omits a beta required by the final request, provider
validation fails before transport.

## Native history and visible projection

The provider reducer preserves ordered `compaction` content blocks. Streaming
`compaction_delta` replaces the block's current `content` and
`encrypted_content`, matching the SDK accumulator behavior.

Null-content compaction blocks remain valid native no-op blocks. Runtime
scratch fields are removed before persistence and wire reuse.

The initial implementation retains pre-compaction native and visible history.
The compaction block still becomes part of canonical native continuation
state. Public metadata may include occurrence/count/readable-summary flags but
never copies `encrypted_content`.

Context-editing applied statistics are retained in assistant metadata. The
client transcript is not edited because the response does not provide a
replacement client history.

## Usage

When `usage.iterations` is present, it is the authoritative complete billing
breakdown for the response. Normalized usage:

- sums all message and compaction iterations;
- does not add the top-level fields again;
- preserves input, output, cache-read, total cache-write, 5-minute
  cache-write, 1-hour cache-write, and reasoning classes where reported;
- separately records compaction iteration count and token classes.

When iterations are absent, existing top-level usage normalization remains
unchanged.

Turn/session cumulative fields and duration/TPS interoperability continue to
use normalized totals. Cost estimation consumes the same reported classes in
its separate task.

## Cancellation and failures

Compaction occurs inside the ordinary request. Existing request-ID
cancellation closes the active SDK stream/client. A response that does not
reach coherent `message_stop` is not finalized, so a partial compaction block
cannot enter completed native history.

Provider errors remain bounded and redacted. Explicit incompatible endpoint
configuration is allowed to reach the endpoint and fail normally.

## Compatibility

Ollama and other compatible endpoints without the optional capability emit no
compaction/context-editing tags. The extensions remain inactive and baseline
Messages behavior is unchanged.

The package does not add preventive request filtering. Raw native request
options can still exercise endpoint-defined behavior.

## Verification

Deterministic tests define exact config, UI, tag, edit, beta, block/delta,
metadata, usage, cancellation, and composition behavior.

Core stack tests prove persistence/reload and a follow-up request with the
complete compaction block. Local Ollama tests prove omission and baseline
regression behavior.

One slow hosted streaming test uses the minimum supported trigger, observes a
real compaction block and compaction iteration, reloads the session, and
continues the conversation. Existing hosted context-management tests are
reused where they already prove thinking retention.