# OpenAI Responses Provider Plugin (SDK-First, Extension-Centric)

Short description: Create a new `openai_responses` plugin bundle using the OpenAI Python SDK and the Responses API, with strict separation of concerns so tools/reasoning/usage/verbosity logic lives in dedicated extensions and each implementation step ships with tests.

## Subtasks

1. `tasks/20260310-openai-responses-provider/010-architecture-scope-and-boundaries.md`
2. `tasks/20260310-openai-responses-provider/020-scaffold-openai-responses-plugin-package.md`
3. `tasks/20260310-openai-responses-provider/030-provider-core-conversion-and-nonstreaming-sdk.md`
4. `tasks/20260310-openai-responses-provider/040-provider-streaming-event-normalization-and-finalization.md`
5. `tasks/20260310-openai-responses-provider/050-tools-extension-responses-api.md`
6. `tasks/20260310-openai-responses-provider/060-reasoning-extension-responses-api.md`
7. `tasks/20260310-openai-responses-provider/070-usage-extension-responses-api.md`
8. `tasks/20260310-openai-responses-provider/080-verbosity-extension-responses-api.md`
9. `tasks/20260310-openai-responses-provider/090-integration-native-retention-and-regression-tests.md`
10. `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`
11. `tasks/20260310-openai-responses-provider/100-docs-readme-and-config-examples.md`
12. `tasks/20260310-openai-responses-provider/110-replaced-by-provider-extension-session-actions-020.md`
13. `tasks/20260310-openai-responses-provider/120-model-discovery-provider-ui-and-doc-followup.md`
14. `tasks/20260310-openai-responses-provider/130-prompt-caching-session-key-extension.md`

## Status

- `010` completed during planning handoff (this task-file creation step).
- `020` through `070` have already been implemented.
- `100` has already been completed, but `120` is a targeted follow-up because provider model discovery and model-selection UI were left in placeholder form.
- `095` is a late-stage native compaction subtask and includes its own high-level prerequisite core capability scope (no separate prerequisite task file).
- `130` is a late-stage prompt-caching/session-key subtask that depends on a separate generic prerequisite task directory:
  - `tasks/20260312-provider-extension-session-settings-lifecycle/000-main.md`
- Remaining subtasks are implementation work.

## Architectural intent (must hold across all subtasks)

1. Provider owns transport and generic Responses-native history mechanics only.
2. Domain logic stays in extensions:
- tool schema injection and tool-call accumulation/reconstruction -> tools extension
- reasoning request knobs and reasoning metadata surfacing -> reasoning extension
- usage accounting/formatting -> usage extension
- verbosity request shaping -> verbosity extension
3. Any provider-side fallback for tools/reasoning must be minimal and justified by a concrete framework invariant.
4. Every implementation subtask must include tests in the same change.

## Key references collected during investigation

- Plugin authoring and execution order:
- `plugins/docs/provider-plugins.md`
- `plugins/docs/provider-extensions.md`
- `plugins/docs/plugin-execution-order.md`
- Template provider package:
- `plugins/template-python-provider/src/template_python_provider/provider.py`
- `plugins/template-python-provider/src/template_python_provider/extension.py`
- Existing OpenAI-compatible reference (chat-completions):
- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/provider.py`
- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/tools_extension.py`
- `plugins/reference-openai-compatible-provider/src/reference_openai_compatible_provider/reasoning_extension.py`
- OpenRouter Responses implementation (source of reusable ideas and anti-patterns to avoid):
- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py`
- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_tools_extension.py`
- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_reasoning_extension.py`
- `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_usage_extension.py`
- Tool schema/call interop adapters already in core:
- `core/python/agent_core/tool_interop.py`

## Acceptance criteria (global)

1. New plugin package name is `openai_responses`.
2. OpenAI SDK is used for API calls (non-streaming + streaming paths).
3. `usage` and `verbosity` are included in v1 as separate extensions.
4. Extension-centric separation is explicit in code and tests.
5. Unit + integration tests cover non-streaming, streaming, tool loop, reasoning, usage, verbosity, and native-history continuity.
6. Late-stage follow-up capabilities may add new extension-owned features when they preserve the same provider-vs-extension boundaries.

## Environment setup (handoff)

1. Use `OPENAI_API_KEY` from repo root `.env` for integration and smoke tests.
2. Do not hardcode API keys in code, tests, docs, or task completion notes.
3. In any new-chat execution prompt, explicitly mention that `OPENAI_API_KEY` is available via root `.env`.
