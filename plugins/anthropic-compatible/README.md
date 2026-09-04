# Anthropic-Compatible Provider

Direct Anthropic API and Anthropic-compatible Messages provider for the AI
Agent Platform.

The package currently provides:

- ordinary and streaming Messages requests through the Anthropic Python SDK;
- API-key configuration;
- model discovery;
- discovered-model dropdowns, manual model IDs, and compact composer model
  selection through the standard configuration UI contract;
- complete provider-native content-block history;
- request cancellation;
- tool schemas, calls, and results through `AnthropicToolsExtension`;
- thinking, redacted thinking, signatures, and native-history reconstruction
  through `AnthropicReasoningExtension`;
- official capability-driven reasoning settings and UI through
  `AnthropicReasoningControlsExtension`;
- raw request-body overrides through `RequestOptionsFeature`;
- standard and beta Anthropic SDK requests with configurable beta features
  and beta headers;
- formatted per-message, turn, and session usage through
  `AnthropicUsageExtension`;
- automatic 5-minute or 1-hour prompt caching through
  `AnthropicPromptCachingExtension`;
- local Ollama compatibility for discovery, text, streaming, tools, thinking,
  usage, duration/TPS, and reasoning-effort passthrough.

Image attachments, OAuth, cost estimation, server tools, and native compaction
are not part of the current implementation.

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
      "capabilities": {
        "anthropic_reasoning_controls": true,
        "prompt_caching": true
      },
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
ollama pull qwen3.5:0.8b
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
      "model": "qwen3.5:0.8b",
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

Raw reasoning effort values use `request_options.output_config.effort`.
Ollama validates and interprets the selected model's supported levels. Do not
also set `thinking.type` when testing graded effort because Ollama gives the
explicit boolean thinking mode precedence.

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
- `betas`: beta identifiers passed through the SDK beta Messages API;
- `beta_headers`: beta identifiers composed into the Anthropic beta header.

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

The reasoning extension contributes no request config or UI. It interprets
thinking and redacted-thinking blocks, streams visible reasoning, and
preserves signatures and complete native blocks needed for continuation.

`AnthropicReasoningControlsExtension` separately uses official model
capabilities or known Claude model fallbacks to expose exact mode and effort
options. Its settings are:

- `anthropic_reasoning_mode`;
- `anthropic_reasoning_effort`;
- `anthropic_reasoning_budget_tokens`;
- `anthropic_reasoning_display`.

See [Anthropic reasoning controls](docs/reasoning-controls.md) for capability
precedence, request mapping, compatible endpoint opt-in, and the complete
copyable `$variants` fallback.

Raw request options remain available as the final override. Manual thinking:

```json
{
  "request_options": {
    "thinking": {
      "type": "enabled",
      "budget_tokens": 1024
    }
  }
}
```

Adaptive thinking:

```json
{
  "request_options": {
    "thinking": {
      "type": "adaptive",
      "display": "summarized"
    },
    "output_config": {
      "effort": "high"
    }
  }
}
```

Beta context management uses provider beta config plus a raw request body:

```json
{
  "betas": ["context-management-2025-06-27"],
  "request_options": {
    "context_management": {
      "edits": [
        {
          "type": "clear_thinking_20251015",
          "keep": "all"
        }
      ]
    }
  }
}
```

Register the request-options feature whenever these fields are used. The
provider reserves `messages`, `system`, and `stream`; unknown compatible
request fields are forwarded through the SDK body escape hatch.

## Prompt caching extension

Enable the official capability:

```json
{
  "capabilities": {
    "prompt_caching": true
  }
}
```

The extension defaults to:

```json
{
  "enable_prompt_caching": true,
  "prompt_cache_ttl": "5m"
}
```

`prompt_cache_ttl` accepts `5m` or `1h`. The extension adds top-level automatic
`cache_control` for the request only. It does not add cache markers to retained
native history. Explicit raw `request_options.cache_control` wins.

## Usage extension

`AnthropicUsageExtension` exposes:

- input, output, total, thinking, cache-read, and cache-creation tokens when
  reported;
- separate 5-minute and 1-hour cache-creation token counts;
- formatted token counts;
- cumulative input/output totals for a multi-generation tool turn;
- session-cumulative totals;
- stable turn IDs and terminal/tool-call state;
- stable turn totals used by performance extensions, including
  `DurationExtension` turn TPS.

The extension does not calculate monetary cost or estimate missing cached
tokens.

## Verification

Fast deterministic suite:

```bash
pytest plugins/anthropic-compatible/tests -q
```

Local Ollama:

```bash
pytest plugins/anthropic-compatible/tests \
  -m "integration and ollama and not slow_integration" -q
```

The normal local suite defaults to `qwen3.5:0.8b`. Override it with
`OLLAMA_ANTHROPIC_MODEL`.

Reasoning-effort effectiveness uses Granite 4.2 3B:

```bash
ollama pull granite4.2:3b
pytest \
  plugins/anthropic-compatible/tests/test_ollama_reasoning_effort_integration.py \
  -m "integration and ollama and slow_integration" -q
```

Override that model with `OLLAMA_ANTHROPIC_EFFORT_MODEL`.

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