# Subtask: OpenAI-compatible reference provider + extensions (Ollama integration)

Parent Task: tasks/20260303-provider-plugin-docs/000-main.md

Depends On:

- tasks/20260303-provider-plugin-docs/020-provider-plugins-doc.md
- tasks/20260303-provider-plugin-docs/050-provider-extensions-doc.md

## Description

Create a **real reference implementation** of an OpenAI-compatible provider using the exact step-by-step patterns described in:

- `plugins/docs/provider-plugins.md`
- `plugins/docs/provider-extensions.md`

This is intentionally a reimplementation even though an OpenAI-compatible provider already exists at `core/python/plugins/openai_provider.py`.

The reference provider must:

- be packaged as an optional plugin repo under `plugins/`
- implement the provider streaming accumulator pattern (generic `process_chunk` + provider-specific `extract_delta` / `process_delta`)
- implement tools + reasoning support via provider extensions following the extension accumulator pattern
- run **integration tests against a local Ollama server** using the OpenAI-compatible endpoint

If we discover that any doc pattern is misleading or not end-to-end correct while implementing this, update the docs so they match the reference implementation.

## Requirements / environment assumptions

- Ollama is running locally with the OpenAI-compatible API enabled:
  - default base URL: `http://localhost:11434/v1`
- Model is already pulled:
  - Use Qwen3 0.6B for most tests (likely `qwen3:0.6b`; keep configurable)

## Proposed implementation location

- New plugin repo: `plugins/reference-openai-compatible-provider/`
  - `pyproject.toml`
  - `agent_plugin.json`
  - `README.md` (how to run integration tests)
  - `src/reference_openai_compatible_provider/` with provider + extensions
  - `tests/` with unit + integration tests

## Goals

1) Produce a clean reference provider that follows the docs line-by-line.
2) Validate the full lifecycle end-to-end against Ollama:
   - non-streaming
   - streaming
   - tool calling loop (when supported by model)
   - reasoning/thinking metadata (when supported by model)
3) Update docs when real implementation work reveals gaps.

## Success criteria

Provider works end-to-end against Ollama:

- The plugin can be installed and discovered:

```bash
python -m pip install -e core/python
python -m pip install -e "plugins/reference-openai-compatible-provider[dev]"
```

- Integration tests pass when Ollama is running:

```bash
pytest plugins/reference-openai-compatible-provider/tests -m integration -q
```

Docs match the implementation:

- `plugins/docs/provider-plugins.md` and `plugins/docs/provider-extensions.md` reflect the exact patterns used (names and recommended shapes may differ, but the flow + invariants must align).

## Suggested provider config defaults

- `base_url`: `http://localhost:11434/v1`
- `model`: `qwen3:0.6b` (keep configurable; tests should not hardcode non-portable values)
- `api_key`: optional / unused for Ollama

## Testing strategy

Add a small suite with two layers:

### A) Offline unit tests (always run)

- `_merge_delta_content` preserves unknown keys and accumulates strings
- tool-call merging:
  - merges by `index`
  - concatenates `function.arguments` fragments
- reasoning accumulation:
  - concatenates `delta.reasoning` fragments

### B) Ollama integration tests (marked)

Mark with `@pytest.mark.integration` and `@pytest.mark.ollama` (match existing repo conventions).

- `test_basic_non_streaming_ollama_openai_compat`
  - `send_request` produces an assistant final

- `test_basic_streaming_ollama_openai_compat`
  - `send_request_stream` yields partials then a final

- `test_tools_tool_loop_ollama_openai_compat`
  - register built-in tools (e.g. math/file tools)
  - prompt the model to call a tool
  - run the tool loop (either via `AgentApplication` or by mimicking the loop with `execute_tool_calls`)

- `test_reasoning_metadata_ollama_openai_compat`
  - enable reasoning knob(s) supported by Ollama/model
  - assert `assistant.metadata["reasoning"]` exists (skip if model does not support)

Important: tool calling and reasoning may not be supported by every Ollama model.
If Qwen3 0.6B does not reliably emit tool calls or reasoning, adjust by:

- forcing `tool_choice` when supported, or
- using a second model just for those tests while keeping Qwen3 for core streaming/non-streaming.

## References

Docs (patterns to follow):

- `plugins/docs/provider-plugins.md`
- `plugins/docs/provider-extensions.md`

Existing runtime + tests to copy patterns from:

- `core/python/plugins/openai_provider.py` (OpenAI-compatible transport patterns)
- `core/python/plugins/openai_tools_extension.py` (tools extension)
- `core/python/plugins/ollama_thinking_extension.py` (thinking enablement)
- `core/python/tests/test_openai_compat_ollama.py`
- `core/python/tests/test_ollama_thinking_qwen3.py`
- `core/python/tests/test_openai_tools_with_ollama.py`
- `core/python/tests/test_openai_tools_with_ollama_stream.py`
- `core/python/agent_app/tool_loop.py` (tool loop contract)

## Detailed plan

1) Scaffold the plugin repo (`pyproject.toml`, `agent_plugin.json`, package layout)
2) Implement the provider using the doc’s accumulator pattern
3) Implement tools + reasoning extensions using the doc’s accumulator extension pattern
4) Add offline unit tests for merge helpers + mapping
5) Add Ollama integration tests (skip gracefully if Ollama is unavailable)
6) Run integration tests locally against `qwen3:0.6b`
7) Update docs when the implementation proves a doc gap or mismatch
