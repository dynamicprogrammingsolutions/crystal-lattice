# Anthropic provider product specification

## Purpose

Crystal Lattice needs a direct Anthropic provider that does not depend on
OpenRouter and can also exercise the same Messages protocol through compatible
endpoints such as local Ollama.

The provider must preserve Anthropic-native content blocks, tools, thinking,
usage, caching, and images while presenting the stable core and application
contracts used by other providers.

## Users

Package users need to:

- select the `anthropic` provider explicitly;
- authenticate with an API key supplied by resolved configuration;
- discover supported models automatically;
- send ordinary and streaming conversations;
- run the existing Claude-compatible tool bundle;
- configure reasoning request fields through raw request options while the
  reasoning extension preserves and interprets provider-native thinking;
- enable or disable usage displays, prompt caching, and image attachments
  through provider extensions delivered by their owning tasks;
- point the provider at a compatible local or hosted endpoint;
- understand which features a compatible endpoint does not support;
- receive stable, redacted authentication, validation, rate-limit, provider,
  timeout, overload, and cancellation failures.

Provider authors and maintainers need one package that demonstrates the
portable provider implementation contract without making official Anthropic
behavior a universal assumption for every compatible endpoint.

## Target experience

### API-key configuration

The primary setup uses resolved application configuration:

```json
{
  "providers": {
    "anthropic_api": {
      "provider": "anthropic",
      "auth_mode": "api",
      "api_key": "${env:ANTHROPIC_API_KEY}",
      "base_url": "https://api.anthropic.com",
      "model": "<selected model>"
    }
  }
}
```

The provider may read `ANTHROPIC_API_KEY` directly when no explicit resolved
value is present, but direct environment access is a fallback and never
overrides config.

### Model selection

The official endpoint supplies model choices and capabilities through model
discovery. The UI uses the discovered model ID and display name and enables
provider extensions from published capabilities rather than hardcoded model
name patterns.

Compatible endpoints may expose only model IDs. In that case the UI remains
usable. Baseline tools, reasoning, and usage remain available, while
non-baseline optional extensions require their own explicit boolean
capability.

### Ordinary and tool-enabled conversations

The provider works as an ordinary text provider without optional extensions.
With the standard extension bundle enabled, users can:

- stream text and thinking;
- invoke Claude-compatible tools;
- continue after tool results;
- inspect formatted input, output, cache-read, and cache-write usage;
- use automatic prompt caching with a supported selectable TTL.

### Compatible local endpoint

An Ollama configuration uses the same `anthropic` provider and a different
base URL. Baseline tools, reasoning, and usage require no capability
declaration. Request options remain transparent and endpoint-validated. Image
support is delivered and verified by the separate attachment subtask.

### Failure behavior

The baseline provider sanitizes failures and emits safe user-facing detail
through the current generic request-error event. Provider-owned retries may use
native status and retry information internally. A later portable request-error
task carries structured categories and provider request IDs across application
and client boundaries.

## Compatibility

- Existing OpenRouter Claude agents remain valid and explicitly selectable.
- Existing `claude-tools` schemas, calls, and provider-native results are
  reused rather than forked.
- The provider accepts future OAuth credentials only through the credential
  contract refined by the OAuth task.
- Compatible endpoint presets are ordinary application configuration rather
  than hidden provider profiles.

## Non-goals

- Making direct Anthropic the default agent in the baseline.
- Implementing OAuth login or refresh in the provider.
- Silently falling back to OpenRouter or another provider.
- Implementing server web search or web fetch in the baseline.
- Implementing fast mode, service tiers, general native compaction/context
  editing policy, image attachments, Files API, PDFs, document citations, token counting,
  model-price cost estimation, structured provider request errors, code
  execution, tool search, or programmatic tool calling in the baseline.
- Implementing Message Batches.
- Implementing structured outputs.
- Treating every Anthropic-compatible endpoint as feature-complete.

The baseline does support raw beta context-management request options needed
to verify reasoning-retention profiles. Higher-level compaction and context
editing policy remains outside this provider baseline.