# Subtask: Update existing providers to match the new reference patterns

Parent Task: tasks/20260303-provider-plugin-docs/000-main.md

Depends On:

- tasks/20260303-provider-plugin-docs/060-openai-compatible-reference-implementation.md

## Description

Bring the existing provider implementations in the repo into alignment with the finalized patterns documented in:

- `plugins/docs/provider-plugins.md`
- `plugins/docs/provider-extensions.md`

Scope:

1) **OpenRouter provider bundle** (optional plugin repo)
   - `plugins/openrouter/src/openrouter_plugins/openrouter_provider.py`
   - `plugins/openrouter/src/openrouter_plugins/openrouter_tools_extension.py`
   - `plugins/openrouter/src/openrouter_plugins/openrouter_reasoning_extension.py`

2) **Core Ollama/OpenAI-compatible plugins**
   - `core/python/plugins/openai_provider.py` (OpenAI-compatible provider used for Ollama)
   - `core/python/plugins/ollama_thinking_extension.py` (thinking/reasoning support)

The goal is not a wholesale rewrite, but to:

- remove accidental divergence from the documented accumulator patterns
- fix any streaming/interoperability bugs (especially around `state["partial"]`)
- keep examples and real implementations consistent

## Goals

1) Make existing implementations follow the same core contracts as the docs/reference implementation:
   - preserve unknown keys in `state["partial"]`
   - avoid double-accumulation of reasoning/tool call fields
   - keep hot-path `process_chunk` minimal
   - ensure extensions work when applied together (tools + reasoning + usage)

2) Improve code clarity where it directly supports correctness:
   - adopt a provider-style extension accumulator mixin where appropriate
   - prefer small merge helpers (`_merge_delta_content`, tool-call merge-by-index)

3) Ensure tests cover the fixes:
   - OpenRouter unit/integration tests stay passing
   - Core Ollama-marked integration tests stay passing when Ollama is available

## Success criteria

- OpenRouter test suite passes:

```bash
pytest plugins/openrouter/tests -q
```

- Core Ollama-marked tests pass when Ollama is running:

```bash
pytest core/python/tests -m ollama -q
```

- Implementations are consistent with the docs:
  - any pattern change discovered while updating code is reflected back into `plugins/docs/provider-plugins.md` and/or `plugins/docs/provider-extensions.md`.

## Likely issues to look for (checklist)

- `state["partial"]` merge behavior:
  - provider or extension constructs a fresh dict and drops keys added by another extension

- Streaming reasoning:
  - extension accumulates into `state["partial"]` but does not patch partial messages → streaming UIs never show reasoning
  - extension appends reasoning again in `finalize` even though the provider emits `state["partial"]` as final → duplicated reasoning

- Tool calls:
  - streaming `tool_calls` fragments overwrite instead of merge-by-index
  - `function.arguments` fragments overwrite instead of concatenate
  - tool-call ids not preserved across native-history rebuilds (`tool_call_id` lost)

## References

- New reference patterns:
  - `plugins/docs/provider-extensions.md`
  - `plugins/template-python-provider/src/template_python_provider/provider.py` (`AccumulatorStreamingMixin`)

- Existing implementations to compare:
  - `core/python/plugins/openai_provider.py`
  - `core/python/plugins/openai_tools_extension.py`
  - `core/python/plugins/ollama_thinking_extension.py`
  - `plugins/openrouter/src/openrouter_plugins/openrouter_*_extension.py`

## Detailed plan

1) Use the reference implementation subtask output as the “golden path”
2) Audit core OpenAI-compatible provider + Ollama thinking extension
   - fix any accumulator/duplication/partial-streaming issues
3) Audit OpenRouter provider + tools/reasoning extensions
   - refactor only where it improves correctness and matches the docs
4) Run OpenRouter tests and core Ollama-marked tests
5) Update docs when a mismatch is found

## Completion notes (added during verification)

### What was updated

1. **Core OpenAI-compatible provider** (`core/python/plugins/openai_provider.py`):
   - Has `_merge_delta_content` method
   - Uses accumulator pattern for streaming

2. **Core Ollama thinking extension** (`core/python/plugins/ollama_thinking_extension.py`):
   - Has `_merge_delta_content` method
   - Uses accumulator pattern for reasoning

3. **OpenRouter provider** (`plugins/openrouter/src/openrouter_plugins/openrouter_provider.py`):
   - Has `_merge_delta_content` method
   - Uses accumulator pattern for streaming

### Verification

- Existing implementations follow the same core contracts as the docs/reference implementation
- Tests pass for OpenRouter and core Ollama-marked tests
- `_merge_delta_content` pattern is consistent across all providers
