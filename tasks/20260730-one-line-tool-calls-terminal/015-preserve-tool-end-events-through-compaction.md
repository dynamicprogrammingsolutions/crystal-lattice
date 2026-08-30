# Preserve Tool End Events Through Application Event Compaction

Parent Task: tasks/20260730-one-line-tool-calls-terminal/000-main.md

The shared application event compactor currently treats every
`tool_partial` event before `tool_results` as redundant. That includes
`phase == "end"` events containing the final display-aware tool result and,
after CL-335, its `message_index`. Terminal rendering depends on that event.
The dropping policy predates CL-335; this subtask corrects the existing shared
behavior independently of the compact renderer follow-up.

## Requirements checklist

- [x] `AgentApplication.compact_events()` preserves `tool_partial` events
      whose phase is `end`, even when a later `tool_results` event for the same
      session/request appears in the same batch.
- [x] Preserved end events retain order, `tool_call_id`, `message_index`,
      final result payload, event id, and all unknown additive fields
      unchanged.
- [x] Redundant `tool_partial` start/stream chunks may still be dropped when
      the corresponding `tool_results` event is present.
- [x] `TerminalApplication.poll_new_events()` returns the preserved end event
      through the production event-store and compaction path.
- [x] Full and compact terminal renderers receive exactly one final tool
      result per call without duplicating already-rendered streamed content.
- [x] HTTP/event consumers retain documented ordering and bounded response
      behavior after the extra semantically terminal event is preserved.

## Research and supporting facts

- **Fact:** `ToolLoopRunner._apply_tool_calls()` yields
  `tool_partial(phase="end")`, then `tool_results`, then
  `session_checkpoint`.
- **Fact:** `compact_events()` currently drops any `tool_partial` encountered
  while scanning backward after `tool_results`; it does not distinguish end
  events from stream chunks.
- **Fact:** terminal polling always calls `compact_events()` before returning
  events to `_poll_events`.
- **Fact:** existing CL-335 renderer tests call `render_event()` directly and
  the core test inspects raw generator output, so neither crosses the
  event-store/compaction boundary.
- **Inference:** this bug can affect earlier full rendering too, especially
  for fast or non-streaming tools whose end event and `tool_results` are
  likely to be polled together.

## Execution plan
Status: Approved

Narrow the pass-one dropping rule in `compact_events()` so only non-terminal
tool partials are considered redundant before `tool_results`. Keep end events
as first-class renderable events. Preserve the existing pass-two rule that
refuses to merge any event when either phase is `end`.

Add focused application-layer tests for compaction permutations:

- start, stream, end, tool-results in one batch;
- end-only non-streaming tool plus tool-results;
- multiple tool calls and multiple request ids interleaved;
- batches split before or after the end event;
- unknown fields and event ids preserved;
- compaction feature flags disabled.

Add an application terminal integration test using `InMemoryEventStore` and
`TerminalApplication.poll_new_events()`. Feed or produce the real event
sequence, poll once so end and results share a batch, render the returned
events, and assert the final tool block/index is visible. This test must use
the production adapter rather than calling `ToolRenderer` directly.

Review server event-list tests because the same compactor is used by HTTP
consumers. Preserve current limits/cursors and update only the semantic claim
that tool end events are retained.

### Implementation decisions and open questions

- Recommendation: fix the shared compactor rather than special-case terminal
  polling; the end event has semantic final-result content for any event
  consumer.
- Recommendation: define `phase == "end"` as terminal for compaction even when
  the payload is malformed, so compaction does not silently destroy
  diagnostic information.
- Confirm whether old legacy `tool_partial` events without a `phase` should
  continue to be droppable. Recommended: preserve current behavior unless a
  test demonstrates that such events carry final results.

### Documentation

- Subtask 060 updates current development documentation for event-compaction
  semantics and the terminal polling boundary.
- No package-user documentation is required solely for this internal
  correction.

### Task checklist

- [x] Add regression tests that fail under the current compaction policy.
- [x] Preserve end events in pass one without weakening stream-chunk
      compaction.
- [x] Add public terminal polling/rendering coverage.
- [x] Review HTTP event-list limit, cursor, and payload tests.
- [x] Run focused core/application event and terminal suites.

### Requirement verification

- A same-batch compaction assertion returns ordered
  `tool_partial(end)`, `tool_results`, and later events.
- The polling-path test renders the end event and its `message_index`.
- Multi-call tests prove each end event appears once and in call order.
- Existing partial-dropping tests prove start/stream compaction remains
  effective.

### Additional implementation verification

- Run event payload-size and event-list response tests to quantify the small
  event-count increase.
- Run a manual fast non-streaming tool request and confirm the result is
  visible without depending on polling timing.

## Completion Notes

- Changed the shared pass-one compaction rule to preserve tool end events.
- Added core permutations for field preservation, multi-call order, unrelated
  requests, and legacy partial dropping.
- Added a production event-store → terminal polling → renderer regression
  proving a same-batch end event remains visible.
- The full application/server and core default suites pass, covering existing
  event-list, cursor, response-limit, and payload-size behavior.