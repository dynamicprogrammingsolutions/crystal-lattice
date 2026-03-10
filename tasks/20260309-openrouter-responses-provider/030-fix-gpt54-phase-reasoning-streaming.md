# Fix GPT-5.4 Phase Preservation + Reasoning Delta Streaming (`/responses`)

Short description: Improve the OpenRouter `/responses` provider to (a) stream reasoning summary deltas as `partial` events so terminal/UI can render “thinking: …” live, (b) preserve GPT-5.4 “phase” (and related fields) in stored native messages per the OpenRouter GPT-5.4 migration guide, and (c) simplify streaming finalization by using the full `response.completed` object for stored history instead of reconstructing the final message from deltas.

Parent Task: `tasks/20260309-openrouter-responses-provider/000-main.md`

Depends On:
- `tasks/20260309-openrouter-responses-provider/020-implement-openrouter-responses-provider.md`

## Plan

1. Capture the true `/responses` streaming shapes for GPT‑5.4 using `debug_sse_path`.
2. Fix reasoning delta streaming by handling `response.reasoning_summary_text.delta` (and close variants) in the provider and emitting partial messages with `metadata.reasoning`.
3. Preserve GPT‑5.4 “phase” (and related fields) in the stored final assistant message by retaining those keys when extracting/storing reasoning output items.
4. Simplify streaming finalization:
   - emit deltas only for UI streaming
   - store the completed response object from `response.completed`
   - construct the stored native assistant message from that full object in `finalize()`
5. Add/extend tests:
   - unit tests for reasoning delta partial emission and “final-from-completed” behavior
   - an env-gated “expensive” GPT‑5.4 integration test that asserts:
     - reasoning partials are emitted
     - phase is preserved when present in the completed response
