# Anthropic-compatible endpoint capabilities

## Purpose

The `anthropic` provider supports the official Anthropic API and compatible
Messages endpoints through one transport and native-message model.

Compatible endpoint setup remains explicit. The provider does not select a
hidden runtime profile or use capability configuration to rewrite requests.

## Baseline provider tags

The compatible APIs in the baseline contract support:

- streaming;
- tools and tool results;
- reasoning/thinking;
- input/output usage.

The provider therefore emits these tags without capability configuration:

- `provider:anthropic`;
- `supports_streaming`;
- `supports_tools`;
- `supports_reasoning`;
- `supports_usage`.

Ordinary official Anthropic and Ollama configurations do not repeat these
baseline features in a `capabilities` mapping.

## Optional capability configuration

Boolean capabilities are reserved for non-baseline optional extensions that
are not supported by every compatible API.

A key is added only with the extension that consumes its tag. Task 010 first
uses this contract for prompt caching:

```json
{
  "capabilities": {
    "prompt_caching": true
  }
}
```

`prompt_caching: true` emits the tag required by
`AnthropicPromptCachingExtension`. False or omission emits no tag.

The mapping does not:

- select endpoints, models, credentials, headers, or SDK methods;
- validate, remove, or rewrite request options;
- describe unknown, partial, tolerated, or unsupported behavior;
- replace endpoint documentation.

Extensions whose required optional tag is absent remain disabled and therefore
do not automatically add their feature request fields. Explicit raw request
options still reach the provider transport. If an endpoint rejects them, the
normal sanitized provider error informs the user.

Future feature tasks may add one boolean capability for their own extension
when the feature is not part of the baseline compatible contract.

## Reusable configuration

Convenience setups are ordinary application mixins or copied config, not
provider-internal profiles.

Official Anthropic configuration remains explicit:

```json
{
  "base_url": "https://api.anthropic.com",
  "api_key": "${env:ANTHROPIC_API_KEY}"
}
```

An Ollama setup remains explicit:

```json
{
  "base_url": "http://localhost:11434",
  "api_key": "ollama",
  "model": "qwen3.5:0.8b"
}
```

The official configuration may add
`capabilities.prompt_caching: true` when the prompt-caching extension is
delivered. Ollama does not.

## Model discovery

The provider normalizes:

- official Anthropic model data;
- OpenAI-style `data` arrays containing model IDs and optional names;
- minimal ID/name-only catalogs.

Published model capability data is preserved. Missing capabilities do not
invent model support.

Discovery uses the Anthropic SDK path derived from `base_url`. Discovery
failure returns an empty list so users can enter a model ID manually. A
separate catalog URL can be added later if a real compatible endpoint requires
one.

## Request behavior

Capability configuration does not filter requests.

- Provider-owned `messages`, history-derived `system`, and `stream` remain
  protected.
- SDK beta selection and beta-header composition remain provider transport
  behavior.
- Generic request options pass supported SDK fields normally.
- Unknown compatible request fields use the SDK body escape hatch.
- Explicit `extra_body` values retain precedence.
- Endpoint validation failures surface through the provider's sanitized
  request error.

## Testing compatible configurations

Baseline tools, reasoning, usage, and streaming behavior is covered directly
by deterministic and real-endpoint tests.

Every non-baseline optional capability must have:

- deterministic tag/extension-gating tests;
- positive deterministic feature tests;
- at least one real endpoint test when practical;
- documented endpoint and model prerequisites.

The required local Ollama configuration verifies model discovery, ordinary and
streaming requests, tools, thinking, usage, raw effort passthrough, and
duration/TPS interoperability with `qwen3.5:0.8b`.

A separate slow test uses `granite4.2:3b` to prove that Anthropic
`output_config.effort` changes reasoning size. It compares five `low` and five
`high` samples using the median and a calibrated 2.0x margin. The request omits
`thinking.type` so Ollama applies the graded effort value.

Tests do not infer behavioral support merely because an endpoint accepts an
unrelated raw request option.