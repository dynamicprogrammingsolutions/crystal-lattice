# Anthropic provider implementation

## Runtime classes

- `anthropic_plugins.provider.AnthropicProvider`
- `anthropic_plugins.tools_extension.AnthropicToolsExtension`
- `anthropic_plugins.reasoning_extension.AnthropicReasoningExtension`
- `anthropic_plugins.usage_extension.AnthropicUsageExtension`

All four classes are registered by `agent_plugin.json`.

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

`AnthropicReasoningExtension` owns thinking configuration and UI, request
shaping, streamed reasoning, redacted thinking, signatures, and reasoning
metadata.

`AnthropicUsageExtension` owns public token metadata, formatting, turn/session
accumulation, and the standard cumulative fields consumed by performance
extensions.

Extensions use shared provider state but keep feature state under namespaced
keys:

```text
anthropic_runtime
anthropic_tools
anthropic_reasoning
anthropic_usage
```

## Streaming sequence

1. The provider initializes a minimal Messages payload.
2. Tools and reasoning extensions add their request fields.
3. The SDK yields events normalized to plain dictionaries.
4. The provider updates a lossless ordered assistant block accumulator.
5. Extensions project tool calls, reasoning partials, and usage.
6. The provider appends one completed native assistant message.
7. Extensions finalize public metadata.
8. Core persists the full provider-native history.

## Verification layout

- `test_provider_unit.py`: transport/config/model/conversion/reducer contracts.
- `test_extensions_unit.py`: isolated extension ownership and mapping.
- `test_stack_integration.py`: deterministic Core stack and persistence.
- `test_ollama_integration.py`: real local Messages transport and application
  loading.
- `test_anthropic_api_integration.py`: minimal official API verification.

The deterministic tests define exact behavior. Ollama tests prove real
compatible transport. Hosted tests cover only official API behavior that the
local endpoint cannot establish.