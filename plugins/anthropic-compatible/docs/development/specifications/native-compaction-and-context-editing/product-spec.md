# Anthropic native context-management product specification

## Purpose

Long Anthropic conversations can exceed useful context limits while retaining
tool results, thinking blocks, and other provider-native continuation data.
Anthropic native context management reduces the active server context without
replacing the visible conversation with a generic client-generated summary.

## Users

Package users need to:

- use automatic native compaction for supported models and override it when
  needed;
- choose a compaction threshold and optional summary instructions;
- retain all thinking, retain a selected number of recent thinking turns, or
  leave thinking retention to the provider;
- clear old tool uses according to explicit token and retention policy;
- inspect whether compaction or context editing occurred;
- continue a persisted conversation with the returned compaction block;
- use compatible endpoints without receiving unsupported automatic fields.

Provider maintainers need separate extensions for compaction and context
editing because models and compatible endpoints may support one without the
other.

## Target behavior

### Capability and opt-in

Official model descriptors are authoritative. A selected model that advertises
`compact_20260112` exposes compaction controls. A selected model that advertises
thinking or tool-use clearing exposes context-editing controls.

Compatible endpoints can opt in through explicit boolean capabilities.
Missing support produces no feature tag, request field, or feature UI.

Capability support makes the controls available. Package-local schema defaults
remain conservative, while the shipped direct Anthropic configuration
explicitly enables supported compaction and tool-use clearing and retains all
thinking.

### Shipped defaults and UI

The default direct Anthropic configuration uses:

- automatic compaction at `150000` tokens;
- keep-all thinking retention;
- tool-use clearing at `100000` tokens with five recent tool uses retained.

Current one-million-token Sonnet and Opus variants override the compaction
trigger to `800000` and the tool-use clearing trigger to `200000`.

Session UI exposes the feature toggles, thresholds, thinking-retention mode,
and retained tool-use count. Expert options such as custom compaction
instructions, exact recent-thinking count, clear-at-least threshold, input
clearing, and excluded tools remain configuration-only.

### Automatic compaction

When enabled, compaction is included in the ordinary Messages request as the
last context-management edit. Users configure:

- an input-token trigger;
- optional summarization instructions.

The initial implementation always requests
`pause_after_compaction: false`. The server compacts and continues the same
request.

A successful response can contain a `compaction` content block alongside the
ordinary answer or tool use. The complete block remains in canonical
provider-native history and is sent back verbatim on later requests.

The visible transcript remains readable as the original conversation plus the
ordinary assistant response. Native continuation state, not the visible
projection, is authoritative.

### Context editing

Thinking retention supports:

- provider default behavior;
- retaining all thinking turns;
- retaining a configured number of recent thinking turns.

Tool-use clearing supports:

- an input-token trigger;
- the number of recent tool uses to retain;
- an optional minimum number of tokens that must be clearable;
- optional tool-input clearing;
- an exclusion list of tool names.

Context editing changes the context evaluated by the provider. It does not
delete or rewrite the local transcript or canonical native history.

### Usage and status

Public metadata can state that compaction occurred and show non-sensitive
compaction/edit counts. Opaque encrypted continuation data remains only in
native history.

When Anthropic reports `usage.iterations`, normalized usage includes every
message and compaction iteration exactly once. Compaction token classes remain
separately available for later cost estimation.

## Compatibility

- Generic prompt summarization remains available to other providers and is not
  redefined.
- Raw request options remain the final protocol escape hatch.
- Existing thinking, tools, usage, duration/TPS, and prompt caching continue
  to compose with native context management.
- An explicitly enabled incompatible endpoint may reject the request through
  its normal provider error. The plugin does not silently remove requested
  fields or select another provider.

## Non-goals

- Manual compaction of an arbitrary visible prefix.
- A dedicated compaction endpoint or background compaction operation.
- Local deletion of the pre-compaction transcript.
- Managed automatic continuation for `pause_after_compaction: true`.
- Provider-independent compaction configuration.
- Monetary cost estimation.