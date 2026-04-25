# OpenAI Responses Provider Plugin (SDK-First, Extension-Centric)

Short description: Create a new `openai_responses` plugin bundle using the OpenAI Python SDK and the Responses API, with strict separation of concerns so tools/reasoning/usage/verbosity logic lives in dedicated extensions and each implementation step ships with tests.

## Subtasks

- [x] `tasks/20260310-openai-responses-provider/010-architecture-scope-and-boundaries.md`
- [x] `tasks/20260310-openai-responses-provider/020-scaffold-openai-responses-plugin-package.md`
- [x] `tasks/20260310-openai-responses-provider/030-provider-core-conversion-and-nonstreaming-sdk.md`
- [x] `tasks/20260310-openai-responses-provider/040-provider-streaming-event-normalization-and-finalization.md`
- [x] `tasks/20260310-openai-responses-provider/042-native-compaction-instruction-message-exclusion.md` (Design umbrella - split into 043-047, optionally 048)
- [ ] `tasks/20260310-openai-responses-provider/043-native-message-preparation-for-compaction.md`
  - PARTIALLY SUPERSEDED BY `tasks/20260310-openai-responses-provider/045-message-injection-compaction-request-messages.md`
- [x] `tasks/20260310-openai-responses-provider/045-message-injection-compaction-request-messages.md`
- [x] `tasks/20260310-openai-responses-provider/044-visible-rebuild-from-compacted-native-output.md`
- [ ] `tasks/20260310-openai-responses-provider/046-manual-range-selection-native-compaction.md`
- [ ] `tasks/20260310-openai-responses-provider/047-auto-compaction-after-request-complete.md`
- [ ] `tasks/20260310-openai-responses-provider/048-config-based-role-normalization.md` (Optional)
- [x] `tasks/20260310-openai-responses-provider/050-tools-extension-responses-api.md`
- [x] `tasks/20260310-openai-responses-provider/060-reasoning-extension-responses-api.md`
- [x] `tasks/20260310-openai-responses-provider/061-openai-responses-native-conversion-and-reasoning-followup-regressions.md`
- [x] `tasks/20260310-openai-responses-provider/062-cross-provider-agent-switch-native-rebuild-regressions.md`
- [x] `tasks/20260310-openai-responses-provider/070-usage-extension-responses-api.md`
- [x] `tasks/20260310-openai-responses-provider/080-verbosity-extension-responses-api.md`
- [x] `tasks/20260310-openai-responses-provider/090-integration-native-retention-and-regression-tests.md`
- [x] `tasks/20260310-openai-responses-provider/095-native-compaction-provider-extension.md`
- [x] `tasks/20260310-openai-responses-provider/100-docs-readme-and-config-examples.md`
- [x] `tasks/20260310-openai-responses-provider/110-replaced-by-provider-extension-session-actions-020.md`
- [x] `tasks/20260310-openai-responses-provider/120-model-discovery-provider-ui-and-doc-followup.md`
- [x] `tasks/20260310-openai-responses-provider/130-prompt-caching-session-key-extension.md`
- [x] `tasks/20260310-openai-responses-provider/140-openai-image-pdf-upload-and-upload-modes.md`
- [x] `tasks/20260310-openai-responses-provider/141-session-asset-storage-and-action-driven-attachments.md`
- [x] `tasks/20260310-openai-responses-provider/150-web-search-extension-and-citation-preservation.md`
- [x] `tasks/20260310-openai-responses-provider/160-openai-flex-processing-extension-and-provider-retries.md`

## Status

- `010` completed during planning handoff (this task-file creation step).
- `020` through `070` have already been implemented.
- `100` has already been completed, but `120` is a targeted follow-up because provider model discovery and model-selection UI were left in placeholder form.
- `095` is a late-stage native compaction subtask and includes its own high-level prerequisite core capability scope (no separate prerequisite task file).
- `042` is now the broad design umbrella for the later split tasks rather than the preferred implementation unit.
- `043` is now partially superseded: the broader `AgentApplication`-owned action lifecycle design is no longer the preferred implementation path. The explicit action-side request preparation contract now lives in core, while the remaining message-injection compaction behavior gap is tracked separately in `045`. Note: `system`/`developer` role normalization is intentionally excluded and handled separately in the optional `048`.
- `045` implemented native compaction request-message override support for normal API-mode system/developer message injection, including `_metadata` stripping on outbound compact input and restoration of the leading stored system/developer message when preserved by the compacted output.
- `044` implemented direct visible rebuild from compacted native output, removing the default placeholder transcript round-trip while preserving follow-up request continuity.
- `046` is the manual compaction UX follow-up for summarize-range-style visible range selection plus a `compact up to here` message action, with real integration coverage to determine whether non-prefix compaction is actually supported.
- `047` is the post-request auto-compaction follow-up for a separate action/lifecycle path that runs only after a successful request has completed and the session has already been saved.
- `048` is an **optional** follow-up for config-based `system`/`developer` role normalization across the entire codebase, enabling manual `developer` message support. It can be done in parallel with or after the compaction subtasks.
- `130` is a late-stage prompt-caching/session-key subtask that depends on a separate generic prerequisite task directory:
  - `tasks/20260312-provider-extension-session-settings-lifecycle/000-main.md`
- `140` is a staged attachment/upload follow-up and explicitly allows the implementing agent to create `141+` subtasks when splitting work across stages.
- `141` is the Stage 3 follow-up for action-driven attachments backed by application-owned session asset storage, including frontend upload UX and attachment preview continuity for sent messages.
- `150` is a late-stage web-search follow-up for the OpenAI Responses bundle, including citation/source preservation and frontend visibility.
- `160` is a flex-processing follow-up that keeps the provider responsible for applying request/service-tier/retry behavior while a dedicated extension owns UI/config and request override shaping.
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
