# Implement OpenRouter `/responses` Provider (Streaming)

Short description: Implement a new OpenRouter provider plugin that targets the OpenRouter `/responses` endpoint and supports streaming. Use the adapters/accessors from subtask `010` so that existing tools can be injected and tool calls can be surfaced to the existing tool loop.

Parent Task: `tasks/20260309-openrouter-responses-provider/000-main.md`

Depends On: `tasks/20260309-openrouter-responses-provider/010-tool-schema-and-call-adapters-and-accessors.md`

## Goals

1. Provide a first-class OpenRouter provider that calls `POST /responses`.
2. Support streaming (SSE) end-to-end.
3. Surface tool calls into `assistant.metadata.tool_calls` in the canonical OpenAI-ish shape so the existing tool loop can execute.
4. Keep existing OpenRouter chat-completions provider intact.

## Online resources / references

Primary assumption: OpenRouter `/responses` is compatible with OpenAI’s Responses API semantics (including streaming), even if OpenRouter’s documentation does not fully specify streaming event shapes.

- OpenRouter Responses API: https://openrouter.ai/docs/api/api-reference/responses/create-responses.md
- OpenAI Responses API (create): https://platform.openai.com/docs/api-reference/responses
- OpenAI streaming guide (SSE): https://platform.openai.com/docs/guides/streaming
- OpenAI tool calling (for the Responses API): https://platform.openai.com/docs/guides/function-calling
- OpenRouter GPT-5.4 migration/behavior notes (phase/commentary preservation): https://openrouter.ai/docs/guides/guides/evaluate-and-optimize/model-migrations/gpt-5-4.md

Empirical verification is expected and required:

- Capture and inspect raw SSE frames from OpenRouter `/responses` for at least:
  - text deltas
  - tool call deltas (including incremental arguments)
  - reasoning/thinking/commentary signals
  - usage/cost blocks

### Empirical verification checklist (OpenAI Responses-style streaming)

OpenAI Responses streaming commonly uses SSE where each `data:` line is a JSON event object with a `type` field (some servers may also emit an SSE `event:` field). When validating OpenRouter compatibility, capture raw frames and check for these *example* event types and invariants:

1. **Lifecycle / boundaries**
   - Expect a starting event such as `response.created`.
   - Expect a terminal event such as `response.completed` (or equivalent) which carries final usage metadata.
   - Expect an error event such as `response.failed` / `response.error` on failure (or a non-200 HTTP response with a JSON error body).

2. **Text streaming**
   - Expect incremental text events like `response.output_text.delta` (with small `delta` strings).
   - Expect a completion marker like `response.output_text.done`.
   - Verify that deltas can be concatenated in order to reconstruct the final assistant text.

3. **Output items**
   - Expect item boundary events like `response.output_item.added` and `response.output_item.done`.
   - Verify item indexing/ids are stable across the stream and are sufficient to associate later deltas with the correct item.

4. **Tool calls (function calling)**
   - Expect tool-call item creation via `response.output_item.added` with an item resembling a `function_call`.
   - Expect argument streaming events like `response.function_call_arguments.delta` and a corresponding `response.function_call_arguments.done`.
   - Verify that each tool call has a stable call id (e.g. `call_id`) plus a function name, and that arguments arrive as an incrementally-built JSON string.

5. **Reasoning / thinking / commentary (GPT-5.4 specific)**
   - Verify whether OpenRouter streams separate “thinking/commentary” signals as dedicated event types (often something like `response.reasoning.delta` / `response.reasoning.done`), as distinct output items, or as fields on output items.
   - Verify preservation of any “phase” and “commentary” semantics described in the OpenRouter GPT-5.4 guide.

6. **Usage / cost metadata**
   - Verify where usage appears (often on `response.completed`), and whether intermediate usage updates appear during the stream.
   - Confirm fields needed by the existing OpenRouter usage UI (prompt tokens, completion tokens, reasoning tokens, cost) can be extracted.

7. **Robustness**
   - Confirm the stream may include non-JSON keepalive lines or blank lines; the parser must ignore safely.
   - Confirm UTF-8 decoding and ensure tool arguments do not get corrupted by incorrect charset detection.

Implementation note: during bring-up, add a debug mode that writes raw SSE frames/events to a file for inspection so that adapter/event handling can be corrected without guesswork.


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

- Integration tests (guarded by `OPENROUTER_API_KEY`):
  - Basic streaming text response via `/responses`.
  - Tool calling via `/responses` and verify the tool loop runs end-to-end.

### GPT-5.4 focused integration test (expensive; minimal tokens)

Add a dedicated integration test using `openai/gpt-5.4` via OpenRouter:

- Must be designed to be low token usage (short prompt, low max output tokens, minimal tool output).
- Must exercise both:
  - tool calling (at least 1–2 tool calls)
  - thinking/commentary signals
- Must be multi-step so the response produces “phase” + “commentary” semantics that the provider preserves/accumulates correctly (see GPT-5.4 guide link above).

Recommendation:

- Mark as `@pytest.mark.expensive` (or similar) and gate execution behind an env var (e.g. `OPENROUTER_RUN_EXPENSIVE=1`) in addition to `OPENROUTER_API_KEY`.

### Port/copy existing OpenRouter integration tests

Where compatible with `/responses`, port existing OpenRouter integration tests to run against the new provider as well (either by parameterizing provider selection or duplicating minimal variants):

- Tools end-to-end test (`plugins/openrouter/tests/test_agent_application_openrouter_puzzle.py`) should be runnable with the new provider.
- Multipart/image test (`plugins/openrouter/tests/test_openrouter_multipart_integration.py`) should be evaluated for `/responses` compatibility and ported if the input image shape is supported.
- Any additional OpenRouter integration coverage that is endpoint-agnostic should be duplicated for `/responses`.

## Open questions

- Exact OpenRouter `/responses` streaming event shapes (OpenRouter docs are sparse; likely similar to OpenAI Responses SSE).
- How OpenRouter represents tool-call argument deltas in streaming and how to accumulate them robustly.
- Whether OpenRouter expects different tool schema shapes than OpenAI’s Responses API (verify empirically).

## Plan (added during completion)

1. Add `OpenRouterResponsesProvider` plugin and register it.
2. Build `/responses` requests from core history and tool schemas.
3. Implement an SSE parser + streaming reducer for text/tool calls.
4. Parse non-streaming `/responses` JSON into canonical outputs.
5. Add unit + integration tests and validate with real SSE frames.

## Completion notes (added during completion)

- Added `OpenRouterResponsesProvider` as a separate plugin package under `plugins/openrouter_responses/`.
- Implemented `/responses` request building, SSE parsing, streaming reduction, and non-streaming parsing.
- Implemented tool schema conversion (OpenAI chat -> Responses) and tool call surfacing (Responses -> canonical OpenAI-chat `metadata.tool_calls`).
- Added unit and integration tests (including config-file AgentApplication coverage) under `plugins/openrouter_responses/tests/`.
