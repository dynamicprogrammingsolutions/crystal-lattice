# Anthropic provider implementation

## Runtime classes

- `anthropic_plugins.provider.AnthropicProvider`
- `anthropic_plugins.tools_extension.AnthropicToolsExtension`
- `anthropic_plugins.reasoning_extension.AnthropicReasoningExtension`
- `anthropic_plugins.reasoning_controls_extension.AnthropicReasoningControlsExtension`
- `anthropic_plugins.context_editing_extension.AnthropicContextEditingExtension`
- `anthropic_plugins.compaction_extension.AnthropicCompactionExtension`
- `anthropic_plugins.usage_extension.AnthropicUsageExtension`
- `anthropic_plugins.prompt_caching_extension.AnthropicPromptCachingExtension`

All seven extension classes plus the provider are registered by
`agent_plugin.json`.

## Provider boundary

`AnthropicProvider` owns:

- Anthropic SDK client construction;
- API-key consumption;
- model discovery;
- ordinary and streaming transport;
- generic ordered content-block accumulation;
- plain text conversion;
- native history;
- request cancellation;
- provider-owned SDK retry configuration;
- safe generic request failures.

The provider's content-block reducer preserves text, thinking,
redacted-thinking, tool-use, and unknown block data. Preserving native data
does not make the provider the owner of the corresponding public feature.

## Extension boundaries

`AnthropicToolsExtension` owns tool schema conversion, call/result projection,
partial input JSON, and Anthropic tool interop.

`AnthropicReasoningExtension` owns streamed reasoning, redacted thinking,
signatures, reasoning metadata, and native-history reconstruction. It
contributes no request config or UI.

`AnthropicReasoningControlsExtension` normalizes official model capability
data, supplies known Claude regex fallbacks, contributes model-specific UI,
and maps normalized settings into `thinking` and `output_config`.
`RequestOptionsFeature` remains the final raw request override.

`AnthropicContextEditingExtension` owns thinking retention, tool-use clearing,
their independent capability gate, request composition, beta requirement, UI,
and applied-edit metadata.

`AnthropicCompactionExtension` owns automatic compaction enablement, trigger,
instructions, model-capability gate, request composition, beta requirement,
and safe public compaction metadata. The complete compaction block remains in
native history.

`AnthropicUsageExtension` owns public token metadata, formatting, turn/session
accumulation, stable turn IDs and terminal/tool-call state, and the standard
cumulative fields consumed by performance extensions. It treats reported
iteration usage as authoritative and exposes separate compaction token classes.

`AnthropicPromptCachingExtension` owns automatic top-level cache configuration,
enabled/TTL UI, and capability gating. Cache usage remains in
`AnthropicUsageExtension`.

Extensions use shared provider state but keep feature state under namespaced
keys:

```text
anthropic_runtime
anthropic_tools
anthropic_usage
```

## Streaming sequence

1. The provider initializes a minimal Messages payload.
2. Tools, context editing, compaction, reasoning controls, and caching add
   their request fields and beta requirements; generic request options run
   last.
3. The SDK yields events normalized to plain dictionaries.
4. The provider updates a lossless ordered assistant block accumulator.
5. Extensions project tool calls, reasoning partials, compaction/edit status,
   and usage.
6. The provider appends one completed native assistant message.
7. Extensions finalize public metadata.
8. Core persists the full provider-native history.

## Verification layout

- `test_provider_unit.py`: transport/config/model/conversion/reducer contracts.
- `test_extensions_unit.py`: isolated extension ownership and mapping.
- `test_stack_integration.py`: deterministic Core stack and persistence.
- `test_ollama_integration.py`: real local Messages transport and application
  loading, model discovery, effort passthrough, usage, and Duration/TPS.
- `test_ollama_reasoning_effort_integration.py`: slow local Granite low/high
  reasoning-size effectiveness.
- `test_anthropic_api_integration.py`: minimal official API verification.
- `test_anthropic_stage3_api_integration.py`: official capability descriptors,
  prompt caching, adaptive interleaving, authentication errors, and
  cancellation.
- `test_context_management_unit.py`: context-management config, UI, tags,
  request ordering, beta validation, block/delta reduction, metadata, and
  iteration usage.
- `test_anthropic_compaction_api_integration.py`: slow official streaming
  compaction, persistence, replay, and follow-up continuation.

The deterministic tests define exact behavior. Ollama tests prove real
compatible transport. Hosted tests cover only official API behavior that the
local endpoint cannot establish.