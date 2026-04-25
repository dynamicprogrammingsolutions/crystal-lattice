# OpenRouter Responses API Provider (Streaming + Tools)

Short description: Add a first-class OpenRouter provider that calls the `/responses` endpoint (including streaming) while keeping existing tools/providers working with minimal change. Introduce a lightweight one-direction adapter + accessor layer for tool schemas and tool calls so the provider can speak Responses-native wire formats without forcing an immediate repo-wide tool schema refactor.

## Subtasks

- [x] `tasks/20260309-openrouter-responses-provider/010-tool-schema-and-call-adapters-and-accessors.md`
- [x] `tasks/20260309-openrouter-responses-provider/020-implement-openrouter-responses-provider.md`
- [ ] `tasks/20260309-openrouter-responses-provider/030-fix-gpt54-phase-reasoning-streaming.md`
- [x] `tasks/20260309-openrouter-responses-provider/040-refactor-native-history-to-responses-items.md`
- [x] `tasks/20260309-openrouter-responses-provider/050-fix-native-indices-and-slicing-integration.md`
- [ ] `tasks/20260309-openrouter-responses-provider/060-dual-provider-coexistence-tags-and-agent-application-integration.md`

Suggested execution order: `010` -> `020`.

Follow-ups after `040`: `050` then `060`.

## Context / motivation

- The existing OpenRouter provider targets `/chat/completions` and assumes OpenAI chat-completions streaming chunk shapes.
- OpenRouter’s `/responses` endpoint is desired (including streaming) and should be treated as first-class, not as “Responses but converted into chat-completions on the hot path”.
- The current tool ecosystem is explicitly “OpenAI-style” (`ToolPlugin.get_tool_schemas`) and the tool loop expects `assistant.metadata.tool_calls` in OpenAI-ish shapes.

This task keeps OpenAI-ish tool schemas/calls as the *canonical internal representation for now*, and introduces small adapter classes (one direction each) plus accessor classes (read-only “views”) to reduce tight coupling to a single wire format.

## References

- OpenRouter Responses API: https://openrouter.ai/docs/api/api-reference/responses/create-responses.md
- OpenAI Responses API reference: https://platform.openai.com/docs/api-reference/responses
- OpenAI streaming guide (SSE): https://platform.openai.com/docs/guides/streaming
- OpenRouter GPT-5.4 migration notes (phase/commentary preservation): https://openrouter.ai/docs/guides/guides/evaluate-and-optimize/model-migrations/gpt-5-4.md

## Guardrail (added during review)

- Keep `plugins/openrouter_responses/tests/test_openrouter_tools_reasoning_integration.py` strict on the reasoning oracle (`"Clock"`) from the `reasoning_test` fixture.
- Do not replace the correctness assertion with weaker checks like "non-empty final answer" just to make all models pass.
- If model/provider variance causes failures, treat that as a performance/regression signal and handle it at test-selection policy level, not by weakening assertions.
