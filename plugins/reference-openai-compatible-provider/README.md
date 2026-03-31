# Reference OpenAI-Compatible Provider

Generic OpenAI-compatible Chat Completions provider package for the AI Agent Platform.

This package is intended as a reusable baseline for OpenAI-like backends, including local servers such as Ollama and hosted providers that expose `/v1/chat/completions`-style APIs.

Supports:

- non-streaming and streaming chat completions
- OpenAI-style tool calling
- generic reasoning metadata extraction and preservation when providers return reasoning fields
- generic usage metadata extraction when providers return `usage`

Reasoning, tools, and usage are provider- and model-dependent.

## Quickstart (Ollama example)

Prerequisites:

- Ollama is running (`ollama serve`)
- a compatible model is available (for example `ollama pull qwen3:0.6b`)

Create a terminal app config (example: `config_ollama.json`):

```json
{
  "plugin_cache_dir": "~/.crystal/cache/plugins",
  "providers": {
    "ollama": {
      "provider": "reference_openai_compatible",
      "base_url": "http://localhost:11434/v1",
      "model": "qwen3:0.6b",
      "timeout": 180,
      "request_options": {
        "think": true
      }
    }
  },
  "plugins": [
    "path:/absolute/path/to/plugins/reference-openai-compatible-provider",
    "path:/absolute/path/to/plugins/feature-request-options"
  ],
  "agents": {
    "default": {"provider": "ollama"}
  }
}
```

Run the terminal app:

```bash
cd application/python
python -m agent_terminal_app --console --config /path/to/config_ollama.json
```

`request_options.think` is only an Ollama-compatible example. Other providers may use different request options, nested reasoning controls, or no reasoning toggle at all.

## Configuration

Configuration is a single flat dict passed to the provider and all enabled plugins.

In application configs, provider settings live under `providers.<provider_id>` and may be overridden per-agent under `agents.<agent_id>`.

### Provider config keys

These keys are read by `reference_openai_compatible_provider.provider.OpenAICompatibleProvider`:

- `provider` (string): provider selector used by the application config
  - value: `reference_openai_compatible`
- `model` (string, required): model id to send in the request payload
- `base_url` (string): OpenAI-compatible base URL; the provider appends `/chat/completions`
  - default: `https://api.openai.com/v1`
- `endpoint_options` (object, optional): labeled base URL choices that render an endpoint selector bound to `base_url`
  - example: `{ "General": "https://api.z.ai/api/paas/v4", "Coding": "https://api.z.ai/api/coding/paas/v4" }`
- `api_key` (string, optional): bearer token for hosted OpenAI-compatible APIs
- `timeout` (number, optional): request timeout in seconds
  - default: `60`
- `debug_stream` (boolean, optional): log decoded streaming chunks as they are received
  - default: `false`
- `min_request_interval_seconds` (number, optional): minimum spacing between requests to the same `base_url` scope
  - default: `0.0`
- `rate_limit_retry_delays_seconds` (list or comma-separated string, optional): retry delays used for HTTP 429 responses
  - default: `[]`
- `respect_retry_after_header` (boolean, optional): when retrying HTTP 429 responses, honor the response `Retry-After` header
  - default: `true`
- `retry_on_status` (object, optional): maps HTTP status codes to retry delay lists for pre-stream retries
  - default: `{}`
- `retry_on_timeout` (list or comma-separated string, optional): retry delays used for request timeout exceptions before streaming begins
  - default: `[]`
- `stream_recovery` (object, optional): mid-stream recovery policy for SSE connection failures
  - default: `{ "mode": "disabled", "max_retries": 3 }`
  - keys:
    - `mode`: `"disabled"`, `"early_only"`, or `"aggressive"`
    - `max_retries`: maximum number of stream recovery attempts when recovery is enabled

When `endpoint_options` is provided, the provider emits a config UI dropdown for `base_url`. Selecting an option updates `base_url` directly, so model discovery, request URLs, and rate-limit scoping automatically follow the selected endpoint.

### Complete provider config example

This example shows all provider-owned config keys together. `request_options` is intentionally omitted here because it is provided by the separate `feature-request-options` plugin.

```json
{
  "providers": {
    "zai": {
      "provider": "reference_openai_compatible",
      "base_url": "https://api.z.ai/api/paas/v4",
      "endpoint_options": {
        "General": "https://api.z.ai/api/paas/v4",
        "Coding": "https://api.z.ai/api/coding/paas/v4"
      },
      "api_key": "${env:ZAI_API_KEY}",
      "model": "glm-4.5-air",
      "timeout": 180,
      "debug_stream": false,
      "min_request_interval_seconds": 0.5,
      "rate_limit_retry_delays_seconds": [1, 3, 5],
      "respect_retry_after_header": true,
      "retry_on_status": {
        "500": [2, 5, 10],
        "502": [1, 3]
      },
      "retry_on_timeout": [1, 3, 5],
      "stream_recovery": {
        "mode": "early_only",
        "max_retries": 3
      }
    }
  }
}
```

### Request options

To pass additional OpenAI-compatible request parameters such as `temperature`, `max_tokens`, `stop`, or provider-specific reasoning toggles, load the `request_options` feature plugin and set `request_options` in config.

Example:

```json
{
  "plugins": [
    "path:/absolute/path/to/plugins/reference-openai-compatible-provider",
    "path:/absolute/path/to/plugins/feature-request-options"
  ],
  "providers": {
    "demo": {
      "provider": "reference_openai_compatible",
      "base_url": "https://example.com/v1",
      "model": "demo-model",
      "request_options": {
        "temperature": 0.2,
        "max_tokens": 256
      }
    }
  }
}
```

### Tool calling

Tool support is enabled automatically when tool plugins are loaded:

- tool schemas are injected into `config["tools"]`
- requests include OpenAI-style `tools` and `tool_choice` when tools are present
- assistant tool calls are surfaced as `metadata["tool_calls"]`

To actually run tools, load one or more tool plugins. Example with built-in math tools:

```json
{
  "plugins": [
    "path:/absolute/path/to/plugins/reference-openai-compatible-provider",
    "plugins.math_tools.MathTools"
  ]
}
```

### Reasoning metadata

The reasoning extension is now a generic parse/preserve layer. It does not own a package-specific `think` config key.

When provider-native assistant messages include these fields, they are surfaced into core message metadata:

- `reasoning`
- `reasoning_content`

When these fields are attached to assistant metadata during a tool loop, the extension writes them back into provider-native assistant messages so they survive native-history reconstruction for follow-up requests.

### Usage metadata

When the provider returns `usage`, the usage extension surfaces a minimal shared metadata shape:

- `metadata.usage`
- `metadata.usage_prompt_tokens`
- `metadata.usage_completion_tokens`
- `metadata.usage_total_tokens`
- `metadata.usage_reasoning_tokens` when present
- formatted token-count variants such as `metadata.usage_total_tokens_formatted`

Provider-specific or extra usage fields stay inside raw `metadata.usage`.

## Retries and error recovery

The provider has three retry/recovery mechanisms. All pre-stream retries share a **global attempt counter**, so the total retry budget is bounded by the longest configured delay list across mechanisms.

### Rate-limit retries (HTTP 429)

Retries on HTTP 429 responses with configurable backoff and `Retry-After` header support.

- `rate_limit_retry_delays_seconds` (list or comma-separated string): delay in seconds before each retry attempt. List length = maximum retries.
  - default: `[]` (no retries)
  - example: `[1, 3, 5]` — retry up to 3 times with 1s, 3s, 5s delays
- `respect_retry_after_header` (boolean): when `true`, waits at least the number of seconds specified by the response's `Retry-After` header (uses the larger of the header value and the configured delay).
  - default: `true`
- `min_request_interval_seconds` (number): minimum time between consecutive requests to the same `base_url` scope, used for request pacing.
  - default: `0.0` (no pacing)

```json
{
  "rate_limit_retry_delays_seconds": [1, 3, 5],
  "respect_retry_after_header": true,
  "min_request_interval_seconds": 0.5
}
```

### Status code retries (pre-stream)

Retries on configurable HTTP status codes (for example 500, 502, 503) before the response body is consumed.

- `retry_on_status` (object): maps HTTP status codes to delay lists. Keys are status code numbers (as strings in JSON). Values follow the same format as `rate_limit_retry_delays_seconds`. List length = maximum retries for that code.
  - default: `{}` (no retries)
  - example: `{"500": [2, 5, 10], "502": [1, 3]}`

```json
{
  "retry_on_status": {
    "500": [2, 5, 10],
    "502": [1, 3]
  }
}
```

### Timeout retries (pre-stream)

Retries when the HTTP request times out (`requests.exceptions.Timeout` — covers both connect and read timeouts).

- `retry_on_timeout` (list or comma-separated string): delay in seconds before each retry attempt. List length = maximum retries.
  - default: `[]` (no retries — timeout exceptions propagate immediately)
  - example: `[1, 3, 5]`

```json
{
  "retry_on_timeout": [1, 3, 5]
}
```

### Stream recovery (mid-stream)

Recovers from connection errors that occur *during* an active SSE stream (for example connection drops, chunked encoding errors). The provider re-issues the full HTTP request and starts a new stream.

- `stream_recovery` (object):
  - `mode` (string): recovery strategy.
    - `"disabled"` — no recovery, connection errors propagate immediately. (default)
    - `"early_only"` — recover only if no visible text content was emitted before the error. Safe for most cases since the consumer hasn't seen partial output yet.
    - `"aggressive"` — recover even after partial content was already streamed. The new request replays from the beginning, so the consumer may see duplicate content.
  - `max_retries` (integer): maximum number of recovery attempts.
    - default: `3` (when mode is not `"disabled"`)

```json
{
  "stream_recovery": {
    "mode": "early_only",
    "max_retries": 3
  }
}
```

### Retry and recovery example

```json
{
  "providers": {
    "my_provider": {
      "provider": "reference_openai_compatible",
      "base_url": "https://api.example.com/v1",
      "model": "gpt-4",
      "rate_limit_retry_delays_seconds": [1, 3, 5],
      "retry_on_status": {
        "500": [2, 5, 10],
        "502": [1, 3]
      },
      "retry_on_timeout": [1, 3, 5],
      "stream_recovery": {
        "mode": "early_only",
        "max_retries": 3
      }
    }
  }
}
```

### Global attempt counter

Pre-stream retries (429, status codes, timeouts) share a single global attempt counter. For example, with `retry_on_status: {"500": [2, 5, 8]}` and `retry_on_timeout: [1, 3, 5]`:

| Attempt | Error | Delay source | Delay |
|---|---|---|---|
| 0 | HTTP 500 | `retry_on_status[500][0]` | 2s |
| 1 | Timeout | `retry_on_timeout[1]` | 3s |
| 2 | HTTP 500 | `retry_on_status[500][2]` | 8s |
| 3 | Timeout | no entry at index 3 | **raises** |

Stream recovery uses its own separate counter.

## Troubleshooting

- `404` or connection errors: confirm `base_url` includes the `/v1` prefix, because the provider appends `/chat/completions`
- missing tool calls: tool calling is model-dependent; use a model that supports tools and a prompt that strongly requests tool usage
- missing reasoning metadata: enable the appropriate provider/model request option through `request_options` if needed, and confirm the model actually emits reasoning fields
- missing usage metadata: some providers or local servers do not return `usage` for all endpoints or modes

## Developer Notes

### Install

From the repo root:

```bash
python -m pip install -e core/python
python -m pip install -e "plugins/reference-openai-compatible-provider[dev]"
```

### Tests

Unit tests:

```bash
pytest plugins/reference-openai-compatible-provider/tests -q
```

Integration tests (requires a local Ollama server):

```bash
pytest plugins/reference-openai-compatible-provider/tests -m integration -q
```

Environment overrides used by the Ollama integration tests:

- `OLLAMA_OPENAI_BASE_URL` (default `http://localhost:11434/v1`)
- `OLLAMA_OPENAI_MODEL` (default `qwen3:0.6b`)

### Debugging streaming

Set `debug_stream: true` in provider config to log decoded streaming chunks. Avoid enabling this when sending secrets because responses may include sensitive data.