# Reference OpenAI-compatible provider (Ollama)

This plugin repo provides a **reference implementation** of an OpenAI-compatible provider and provider extensions (tools + reasoning).

It is intended to be read alongside:

- `plugins/docs/provider-plugins.md`
- `plugins/docs/provider-extensions.md`

## Install + test

From the repo root:

```bash
python -m pip install -e core/python
python -m pip install -e "plugins/reference-openai-compatible-provider[dev]"
```

### Offline unit tests

```bash
pytest plugins/reference-openai-compatible-provider/tests -q
```

### Ollama integration tests (OpenAI-compatible API)

Assumes Ollama is running with the OpenAI-compatible API enabled:

- Base URL: `http://localhost:11434/v1`

Run:

```bash
pytest plugins/reference-openai-compatible-provider/tests -m integration -q
```

Optional environment overrides:

- `OLLAMA_OPENAI_BASE_URL` (default `http://localhost:11434/v1`)
- `OLLAMA_OPENAI_MODEL` (default `qwen3:0.6b`)

Note: the provider itself defaults `base_url` to `https://api.openai.com/v1` (matching the core OpenAI-compatible provider). The tests default to Ollama's local endpoint via `OLLAMA_OPENAI_BASE_URL`.
