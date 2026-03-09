# Implement OpenRouter `/responses` Provider (Streaming)

Short description: Implement a new OpenRouter provider plugin that targets the OpenRouter `/responses` endpoint and supports streaming. Use the adapters/accessors from subtask `010` so that existing tools can be injected and tool calls can be surfaced to the existing tool loop.

Parent Task: `tasks/20260309-openrouter-responses-provider/000-main.md`

Depends On: `tasks/20260309-openrouter-responses-provider/010-tool-schema-and-call-adapters-and-accessors.md`

## Goals

1. Provide a first-class OpenRouter provider that calls `POST /responses`.
2. Support streaming (SSE) end-to-end.
3. Surface tool calls into `assistant.metadata.tool_calls` in the canonical OpenAI-ish shape so the existing tool loop can execute.
4. Keep existing OpenRouter chat-completions provider intact.

## Proposed implementation outline

### A) New provider plugin

- Add `OpenRouterResponsesProvider` under `plugins/openrouter/src/openrouter_plugins/`.
- Register it in `plugins/openrouter/agent_plugin.json`.
- Provider config schema mirrors `OpenRouterProvider` (api key, base_url, model, timeout, site_url, app_name).
- Provider tags should clearly distinguish this provider (e.g. `provider:openrouter_responses`, `openrouter_responses`, `supports_streaming`).

### B) Request building

- Map core messages into Responses `input` payload (text + images + tool results).
- Inject tool schemas using the adapter plan:
  - Read `config["tools"]` (already populated by core), which contains OpenAI chat-style schemas.
  - Convert to Responses-native tool schema list via declared schema adapters.

### C) Streaming

- Implement an SSE parser that supports `event:` + `data:` framing.
- Accumulate streaming deltas into provider state so `finalize` can emit a final assistant message.
- Parse Responses-native tool-call events and translate them into canonical OpenAI-ish `metadata.tool_calls` using declared call adapters.

### D) Non-streaming

- Parse the final Responses JSON into the same canonical core message output shape.

### E) Tests

- Unit tests for parsing Responses tool-call objects/events into canonical `metadata.tool_calls`.
- Integration test (guarded by `OPENROUTER_API_KEY`) that exercises:
  - a simple streaming text response
  - tool calling (at least one tool) via `/responses` and verifies the tool loop runs

## Open questions

- Exact OpenRouter `/responses` streaming event shapes (OpenRouter docs are sparse; likely similar to OpenAI Responses SSE).
- How OpenRouter represents tool-call argument deltas in streaming and how to accumulate them robustly.
- Whether OpenRouter expects different tool schema shapes than OpenAI’s Responses API (verify empirically).
