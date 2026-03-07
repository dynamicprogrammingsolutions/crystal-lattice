# OpenAI-compatible provider (Ollama)

OpenAI-compatible Chat Completions provider for the AI Agent Platform.

Supports:

- Non-streaming and streaming `/v1/chat/completions`
- OpenAI-style tool calling (`tools` request payload + `tool_calls` deltas)
- Thinking/reasoning via Ollama’s `think: true` request option (surfaces as assistant `metadata["reasoning"]`)

## Quickstart (terminal app)

Prerequisites:

- Ollama is running (`ollama serve`)
- A model is available (for example: `ollama pull qwen3:0.6b`)

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
      "think": true
    }
  },
  "plugins": [
    "path:/absolute/path/to/plugins/reference-openai-compatible-provider"
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

## Configuration

Configuration is a single flat dict passed to the provider and all enabled plugins.

In application configs (terminal/HTTP app), provider settings live under `providers.<provider_id>`, and may be overridden per-agent under `agents.<agent_id>`.

### Provider config keys

These keys are read by `reference_openai_compatible_provider.provider.OpenAICompatibleProvider`:

- `provider` (string): provider selector used by the application config.
  - Value: `reference_openai_compatible`
- `model` (string, required): model id to send in the request payload.
  - Example (Ollama): `qwen3:0.6b`
- `base_url` (string): OpenAI-compatible base URL. The provider appends `/chat/completions`.
  - Example (Ollama): `http://localhost:11434/v1`
  - Default: `https://api.openai.com/v1`
- `api_key` (string, optional): bearer token for hosted OpenAI-compatible APIs.
  - Not required for Ollama.
- `timeout` (number, optional): request timeout in seconds.
  - Default: `60`
- `debug_stream` (boolean, optional): log streaming chunks (truncated) as they are received.
  - Default: `false`

### Thinking / reasoning (`think`)

This plugin provides a provider extension that:

- adds `"think": true` to the request payload when enabled, and
- accumulates streamed `delta.reasoning` fragments into assistant `metadata["reasoning"]`.

Config key:

- `think` (boolean, optional): enable thinking.
  - Default: `false`

Support is model/server dependent.

### Tool calling

Tool support is enabled automatically when tool plugins are loaded:

- Tool schemas are injected into the provider config as `config["tools"]`.
- Requests include OpenAI-style `tools` and `tool_choice` when tools are present.
- Assistant tool calls are surfaced on the core message as `metadata["tool_calls"]`.

To actually run tools, load one or more tool plugins. Example (built-in math tools):

```json
{
  "plugins": [
    "path:/absolute/path/to/plugins/reference-openai-compatible-provider",
    "plugins.math_tools.MathTools"
  ]
}
```

### Extra OpenAI request options

To pass additional OpenAI-compatible request parameters (for example `temperature`, `max_tokens`, or `stop`), load the `request_options` feature plugin and set `request_options` in config.

Example:

```json
{
  "plugins": [
    "path:/absolute/path/to/plugins/reference-openai-compatible-provider",
    "path:/absolute/path/to/plugins/feature-request-options"
  ],
  "providers": {
    "ollama": {
      "provider": "reference_openai_compatible",
      "base_url": "http://localhost:11434/v1",
      "model": "qwen3:0.6b",
      "request_options": {"temperature": 0.2}
    }
  }
}
```

## Troubleshooting

- `404` or connection errors: confirm `base_url` includes the `/v1` prefix (the provider appends `/chat/completions`).
- Tool calls missing: tool calling is model-dependent; try a model that supports tool calling and use a prompt that strongly requests tool usage.
- Reasoning missing: set `think: true` and use a model that supports thinking/reasoning deltas.

## Developer notes

### Install

From the repo root:

```bash
python -m pip install -e core/python
python -m pip install -e "plugins/reference-openai-compatible-provider[dev]"
```

### Tests

- Unit tests:

```bash
pytest plugins/reference-openai-compatible-provider/tests -q
```

- Integration tests (requires a local Ollama server):

```bash
pytest plugins/reference-openai-compatible-provider/tests -m integration -q
```

Environment overrides used by the integration tests:

- `OLLAMA_OPENAI_BASE_URL` (default `http://localhost:11434/v1`)
- `OLLAMA_OPENAI_MODEL` (default `qwen3:0.6b`)

### Debugging streaming

Set `debug_stream: true` in provider config to log decoded streaming chunks (truncated). Avoid enabling this when sending secrets (for example API keys) because responses may include sensitive data.
