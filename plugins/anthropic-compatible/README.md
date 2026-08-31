# Anthropic-Compatible Provider

Direct Anthropic API and Anthropic-compatible Messages provider for the AI
Agent Platform.

The package currently provides:

- ordinary and streaming Messages requests through the Anthropic Python SDK;
- API-key configuration;
- model discovery;
- complete provider-native content-block history;
- request cancellation;
- tool schemas, calls, and results through `AnthropicToolsExtension`;
- thinking, redacted thinking, signatures, and effort controls through
  `AnthropicReasoningExtension`;
- formatted per-message, turn, and session usage through
  `AnthropicUsageExtension`;
- local Ollama compatibility for text, streaming, tools, thinking, and usage.

Prompt caching, image attachments, OAuth, cost estimation, server tools, and
native compaction are not part of the current implementation.

## Installation

From the repository root:

```bash
python -m pip install -e core/python
python -m pip install -e "plugins/anthropic-compatible[dev]"
```

Install `application/python` as well when using the terminal or HTTP app.

## Official Anthropic configuration

Store the key in the repository-root `.env`:

```text
ANTHROPIC_API_KEY=...
```

Example application configuration:

```json
{
  "plugin_cache_dir": "~/.crystal/cache/plugins",
  "plugins": [
    "path:/absolute/path/to/plugins/anthropic-compatible"
  ],
  "providers": {
    "anthropic_api": {
      "provider": "anthropic",
      "api_key": "${env:ANTHROPIC_API_KEY}",
      "base_url": "https://api.anthropic.com",
      "model": "<discovered model id>",
      "timeout": 300,
      "max_tokens": 4096
    }
  },
  "agents": {
    "default": {
      "provider": "anthropic_api"
    }
  }
}
```

Resolved `api_key` configuration is authoritative. Direct
`ANTHROPIC_API_KEY` lookup is a fallback for direct Core use.

## Ollama configuration

Start Ollama and install a model with the required capabilities:

```bash
ollama pull qwen3:0.6b
```

Example:

```json
{
  "plugins": [
    "path:/absolute/path/to/plugins/anthropic-compatible"
  ],
  "providers": {
    "anthropic_local": {
      "provider": "anthropic",
      "api_key": "ollama",
      "base_url": "http://localhost:11434",
      "model": "qwen3:0.6b",
      "timeout": 60,
      "max_tokens": 512
    }
  },
  "agents": {
    "default": {
      "provider": "anthropic_local"
    }
  }
}
```

Compatible endpoints may omit official capabilities or reject fields that the
official API accepts. The current local contract covers text, streaming,
tools, thinking, and usage.

## Provider configuration

Provider-owned keys:

- `provider`: `anthropic`;
- `auth_mode`: currently `api`;
- `api_key`: resolved API key;
- `base_url`: API root, default `https://api.anthropic.com`;
- `model`: selected model ID;
- `anthropic_version`: API version header, default `2023-06-01`;
- `timeout`: request timeout seconds, default `300`;
- `max_retries`: SDK pre-output retry count, default `2`;
- `max_tokens`: maximum generated tokens, default `4096`;
- `headers`: additional non-secret headers.

The provider owns transport, native Messages history, cancellation, model
discovery, and redacted request failures. It remains usable for plain text when
all provider extensions are disabled.

## Tools extension

`AnthropicToolsExtension` is enabled when the provider and tool capability tags
are present.

It:

- converts request-bound schemas to Anthropic tools;
- reconstructs streamed `tool_use` input JSON;
- surfaces calls through assistant `metadata.tool_calls`;
- converts Core tool messages into Anthropic `tool_result` blocks;
- preserves tool IDs and display metadata across session reload.

Actual tools remain separate tool plugins.

## Reasoning extension

Configuration:

- `enable_reasoning`: enable thinking, default `false`;
- `reasoning_effort`: `low`, `medium`, `high`, `xhigh`, or `max` when
  accepted by the model;
- `reasoning_budget_tokens`: manual thinking budget, default `1024`;
- `show_reasoning`: expose reasoning in UI metadata, default `true`.

When reasoning is disabled, the extension sends an explicit disabled thinking
configuration. When enabled, thinking and redacted-thinking blocks remain in
provider-native history, including signatures needed for tool-result
continuation.

Effort support is model-specific. Unsupported models may reject a selected
effort value, so leaving the value unset uses the provider/model default.

## Usage extension

`AnthropicUsageExtension` exposes:

- input, output, total, thinking, cache-read, and cache-creation tokens when
  reported;
- formatted token counts;
- cumulative input/output totals for a multi-generation tool turn;
- session-cumulative totals;
- stable turn totals used by performance extensions.

The extension does not calculate monetary cost or estimate missing cached
tokens.

## Verification

Fast deterministic suite:

```bash
pytest plugins/anthropic-compatible/tests -q
```

Local Ollama:

```bash
pytest plugins/anthropic-compatible/tests -m "integration and ollama" -q
```

Hosted Anthropic:

```bash
pytest plugins/anthropic-compatible/tests \
  -m "integration and api and anthropic" -q
```

Hosted tests require `ANTHROPIC_API_KEY`. Set `ANTHROPIC_TEST_MODEL` to
override the discovered low-cost test model.

## Development documentation

See [development documentation](docs/development/index.md) for implementation
boundaries and the durable provider specification.