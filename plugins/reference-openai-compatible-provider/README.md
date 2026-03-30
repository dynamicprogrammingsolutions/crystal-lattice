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

When `endpoint_options` is provided, the provider emits a config UI dropdown for `base_url`. Selecting an option updates `base_url` directly, so model discovery, request URLs, and rate-limit scoping automatically follow the selected endpoint.

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