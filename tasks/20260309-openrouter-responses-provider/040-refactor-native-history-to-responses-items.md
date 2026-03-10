# Refactor OpenRouter `/responses` Provider to Use Responses-Native History

Short description: Refactor `OpenRouterResponsesProvider` so that `native_messages` are **truly native to the OpenAI/OpenRouter Responses API** (i.e. a list of `/responses` “items”), and so that streaming stores and replays completed output items unchanged. Move any necessary “synthesis” strictly into `to_native_messages`/`from_native_messages` conversions.

Parent Task: `tasks/20260309-openrouter-responses-provider/000-main.md`

## Why this refactor

The framework uses `session.metadata["native_messages"]` as the authoritative provider-native history across turns. For the `/responses` provider, “native” should mean **Responses API items**, not chat-like `{role, content}` dicts.

Current code still treats provider-native history as chat-like dicts and synthesizes a single assistant message out of `response.completed`. This violates “native means native”, and makes phase preservation/tool calls harder than necessary.

## Current behavior (as of 2026-03-09)

- Provider-native history is *chat-like* messages (`{"role": ..., "content": ...}`), not Responses items.
  - See `OpenRouterResponsesProvider.to_native_messages()` and `.from_native_messages()` in `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py:243` and `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py:309`.
- Requests are built by converting chat-like messages into Responses `input` items using `_native_messages_to_responses_input()`.
  - See `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py:408` and `_build_request_body()` at `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py:504`.
- Streaming:
  - Partials are emitted for `response.output_text.delta` and `response.reasoning*.delta`.
  - Finalization happens on `response.completed`, but the provider **synthesizes** a single assistant “native message” (chat-like dict) from the completed response.
  - See `process_chunk()` at `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py:660` and `_response_json_to_native_assistant()` at `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py:706`.
- Phase preservation (GPT‑5.4): the provider extracts phase texts into `metadata.responses_output_messages` (compact `{phase,text}` records) and re-injects them next turn.
  - See injection in `_native_messages_to_responses_input()` at `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py:454`.

## Target behavior / design (clean path)

### New invariant

`native_messages` for this provider MUST be a `list[dict]` of Responses API items.

Additional convention (matches existing providers like `core/python/plugins/openai_provider.py`):
- Provider/extensions may attach internal per-item metadata under a special `"_metadata"` key.
- `"_metadata"` MUST be stripped out just before sending the request so the wire `"input"` contains only Responses-native fields.

Examples of “native items”:
- `{"type": "message", "role": "user", "content": [{"type": "input_text", "text": "..."}]}`
- `{"type": "message", "role": "assistant", "phase": "commentary", "content": [{"type": "output_text", "text": "..."}]}` (output)
- `{"type": "function_call", "call_id": "...", "name": "...", "arguments": "..."}`
- `{"type": "function_call_output", "call_id": "...", "output": "..."}`
- `{"type": "reasoning", ...}`

### Storage rule

If `response.completed` contains `response.output`, the provider should emit **those output items unchanged** as `final_messages`, and they should be appended unchanged into `session.metadata["native_messages"]`.

Clarification: “unchanged” refers to the Responses-native fields. It is allowed (and expected) that providers/extensions attach internal fields like `"_metadata"` onto items for persistence, as long as those fields are stripped before the next request is sent.

No “assistant chat dict” should be synthesized/stored at the provider layer.

### Conversion rule

Any “synthesis” needed for the internal tool loop / UI must happen in:
- `to_native_messages(core_messages, state)` (core → native items), and
- `from_native_messages(native_items, state)` (native items → core messages)

This lets the persisted history remain exactly Responses-native.

Additional: core message `metadata` that must persist across turns should be stored into native items under `"_metadata"`, and reconstructed back into core `metadata` in `from_native_messages`. Avoid persisting `native_indices` into `"_metadata"` (providers like `openai_provider` explicitly drop it).

## GPT‑5.4 phasing (why this matters)

OpenRouter’s GPT‑5.4 migration guidance describes assistant outputs as multiple message items tagged with `phase` (e.g. `commentary` vs `final_answer`) and recommends preserving/replaying that `phase` across multi-turn flows.

With “native history = output items unchanged”, phase is preserved automatically because the assistant message items (including `phase`) are stored and replayed verbatim in the next request’s `input`.

## Implementation notes / step-by-step

### 1) Define the native item schema for this provider

- Decide what subset of Responses items we support for round-tripping, at minimum:
  - `message` (user/system/assistant) with `input_text` and `input_image` parts (for inputs)
  - `message` (assistant) with `output_text` parts (for outputs)
  - `function_call` (assistant tool request)
  - `function_call_output` (tool results)
  - `reasoning` (if present; keep unchanged)

### 2) Rewrite request building to be “native in, native out”

- Replace `_native_messages_to_responses_input()` usage. After the refactor, `_build_request_body()` should essentially do:

  - `input_items = override if override else native_messages`
  - validate that `input_items` are Responses items (allow extra internal keys like `"_metadata"`)
  - `items_to_send = strip _metadata from each item` (functional, no in-place mutation)
  - return `{**request["payload"], "input": items_to_send}`

- Update the validator (`_validate_message_list`) to validate Responses items rather than chat-like role/content.

### 3) Rewrite `to_native_messages` (core → Responses items)

Goal: when no native history exists, we can reconstruct a full Responses-native `input` list from canonical core messages.

Mapping guidance:
- core `role in {"user","system","assistant"}` with string content → `message` item with `content:[{"type":"input_text","text":...}]`.
- core multipart images → include `{"type":"input_image","image_url":...}` parts.
- core tool outputs (role=`tool`) → emit `function_call_output` item with `call_id` (from `metadata.tool_call_id`) and `output`.
- core assistant tool_calls (from `metadata.tool_calls`) → emit `function_call` items (one per tool call).

Important: functional style only (no in-place mutation of input params/state).

Also: preserve any core `metadata` that should survive this rebuild in the native item’s `"_metadata"` field (excluding `native_indices`).

### 4) Rewrite `from_native_messages` (Responses items → core)

Goal: convert a Responses-native item stream into core canonical messages used by the UI and tool loop.

Suggested conversion strategy:
- For each `message` item:
  - create a core message with `role`, joined `output_text` / `input_text` parts as `content`.
  - store `phase` (if present) in core `metadata.phase` (or similar), so UI can display it if desired.
  - merge any native `"_metadata"` into core `metadata` (dropping `native_indices`).
- For `function_call` items:
  - create a core assistant message with `content:""` and `metadata.tool_calls=[...]` (converted via the tool interop registry).
  - This is the canonical shape the tool loop understands.
  - merge any native `"_metadata"` into that core message `metadata`.
- For `function_call_output` items:
  - create a core tool message (`role:"tool"`) with `content=output` and `metadata.tool_call_id=call_id`.
  - merge any native `"_metadata"` into core `metadata`.
- For other items (e.g. `reasoning`): optionally convert to assistant messages with metadata (or ignore for core content) but MUST keep native storage unchanged.

### 5) Streaming changes: emit output items unchanged

- In `process_chunk()`:
  - keep emitting partial content/reasoning deltas (UI streaming)
  - on `response.completed`, emit `final_messages = response["output"]` (a list of Responses items) without transforming them
  - append those items to the provider’s `current_native` so `ProviderWrapper` persists them for the session.

Metadata convention:
- If the provider or extensions need to persist response-level details (e.g. `usage`, formatted usage fields), attach them under `"_metadata"` on the appropriate output item(s) in native history.
- Ensure `"_metadata"` is stripped when building the next request.

This removes the need for `_response_json_to_native_assistant()` in the hot path.

### 6) Tool-loop correctness: “commentary then tool call”

In `/responses`, the model may emit a phased assistant message (commentary) and then emit `function_call` items.

Under this refactor:
- Partials:
  - UI sees text deltas as partial assistant content (optionally annotate with phase later).
- Finals:
  - On `response.completed`, `final_messages` includes BOTH the assistant `message` item(s) (with `phase`) and the `function_call` item(s), unchanged.
- `from_native_messages()` must convert those `function_call` items into a core assistant message with `metadata.tool_calls` so the tool loop executes them.

Optional nice-to-have (not required to ship): track `item_id -> phase` from `response.output_item.added` so partial deltas can be annotated with `metadata.phase` while streaming. This can be done with an immutable map in `state` and does not require accumulating output text.

## Files to change

- Provider implementation: `plugins/openrouter_responses/src/openrouter_responses_plugins/openrouter_responses_provider.py:243`
- Potentially update extensions if they assume chat-like native messages (tools/reasoning/usage/websearch/verbosity). Most extensions should remain request-payload-only.
- Tests across `plugins/openrouter_responses/tests/` that currently assume chat-like finals.

Framework reference:
- Provider wrapper streaming contract: `core/python/agent_core/plugin/provider.py:490`

## Test/verification checklist

Unit:
- `pytest plugins/openrouter_responses/tests/test_openrouter_provider_unit.py -q`
- `pytest plugins/openrouter_responses/tests/test_openrouter_responses_provider_unit.py -q`

Integration (requires `OPENROUTER_API_KEY`):
- `pytest plugins/openrouter_responses/tests/test_openrouter_responses_basic_integration.py -q`
- `pytest plugins/openrouter_responses/tests/test_openrouter_tools_reasoning_integration.py -q`

Expensive GPT‑5.4 phase/reasoning (requires `OPENROUTER_RUN_EXPENSIVE=1`):
- `OPENROUTER_RUN_EXPENSIVE=1 pytest plugins/openrouter_responses/tests/test_openrouter_gpt54_phase_reasoning_expensive.py -q`

## Acceptance criteria

- `session.metadata["native_messages"]` for `/responses` sessions is a list of Responses items (not chat-like dicts).
- On `response.completed`, the provider appends `response.output` items to native history unchanged.
- Multi-turn GPT‑5.4 phase is preserved automatically (assistant message items with `phase` are replayed verbatim in the next request input).
- Tool calls work end-to-end: a `function_call` item in native history becomes a canonical core assistant message with `metadata.tool_calls`, triggering the tool loop.
- No in-place mutation of state/params (functional style).

## Gotchas / decisions to document

- Whether to store *both* input and output items in one `native_messages` list (recommended), or to store input-only plus some other linkage (harder).
- How to represent “assistant message content” in core when the native stream contains multiple phased messages.
- Whether to pass through native `reasoning` items into core metadata (optional) vs leaving them native-only.

## Completion Notes (added during completion)

- Refactored `OpenRouterResponsesProvider` so `native_messages` are Responses API items and requests send `input` by stripping per-item `"_metadata"`.
- Changed streaming/non-streaming finalization to persist `response.output` items (with optional internal `"_metadata"` attached) instead of synthesizing chat-like assistant dicts.
- Updated conversions so `function_call` items become canonical core `assistant.metadata.tool_calls` at the end of each response segment (tool-loop compatibility), and core messages carry `metadata.native_indices` when message counts differ.
- Adjusted internal metadata policy:
  - Provider persists only response-level fields not present in native items (`response_id` on all output items; `usage` on a single primary output item).
  - Provider derives and surfaces UI-required fields on core message metadata (`reasoning` summary and `url_citations`) while preserving the full native items unchanged for replay.
- Updated `/responses` extensions that assumed chat-like natives:
  - Tools extension is request-only (no-op message transforms).
  - Usage extension attaches formatted usage fields into native item `"_metadata"` on `response.completed`.
  - Claude caching extension injects/strips `cache_control` on Responses `input_text` parts.
- Updated `SystemMessageFeature` to support Responses-item native histories (inserts/renders system message as `type: "message"` items).
- Tests run (unit only):
  - `pytest plugins/openrouter_responses/tests -q -m "not integration"`
  - `pytest plugins/feature-system-message/tests -q`
- Tests run (integration):
  - `pytest plugins/openrouter_responses/tests/test_openrouter_responses_basic_integration.py -q`
  - `pytest plugins/openrouter_responses/tests/test_openrouter_tools_reasoning_integration.py -q`
  - `pytest plugins/openrouter_responses/tests/test_openrouter_usage_extension_integration.py -q`
  - `pytest plugins/openrouter_responses/tests/test_openrouter_reasoning_integration.py -q`
  - `pytest plugins/openrouter_responses/tests/test_openrouter_reasoning_streaming_vs_nonstreaming.py -q`
  - `pytest plugins/openrouter_responses/tests/test_openrouter_websearch_integration.py -q`
  - `pytest plugins/openrouter_responses/tests/test_claude_caching_feature_openrouter_integration.py -q`
  - `pytest plugins/openrouter_responses/tests/test_openrouter_models_api_integration.py -q`
  - `pytest plugins/openrouter_responses/tests/test_openrouter_tools_comprehensive.py -q`
- Tests run (expensive):
  - `OPENROUTER_RUN_EXPENSIVE=1 pytest plugins/openrouter_responses/tests/test_openrouter_gpt54_phase_reasoning_expensive.py -q`
