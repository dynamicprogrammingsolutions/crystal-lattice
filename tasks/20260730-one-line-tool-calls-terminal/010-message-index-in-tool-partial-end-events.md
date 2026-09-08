# Add `message_index` To `tool_partial` End Events

Parent Task: tasks/20260730-one-line-tool-calls-terminal/000-main.md

The live terminal renderer needs each tool call's session message index so a
compact one-line rendering can display `[<index>]` and the user can expand it
later with `/list <index>`. The index is computable at emit time inside the
tool loop but is not currently included in the event payload.

## Requirements checklist

- [x] `tool_partial` events with `phase == "end"` include a
      `"message_index"` integer field equal to the session index the tool
      message will occupy once appended.
- [x] Existing consumers are unaffected (additive field only; no renames).
- [x] Unit test asserts the field is present and correct for a multi-tool-call
      streaming request (echo/fake tools are fine; no real provider needed).

## Where to change

`core/python/agent_app/tool_loop.py`, `_apply_tool_calls` (~lines 370-519):

- `start_index = len(session.messages)` is captured before the loop
  (~line 389).
- Per call, the end event is yielded at ~lines 464-474:

  ```python
  yield {
      "type": "tool_partial",
      ...
      "phase": "end",
      "payload": {"result": last_final},
  }
  ```

- The tool message is appended AFTER that yield via `core.add_message`
  (~line 487), which appends exactly one message per call. Therefore at the
  moment of the end-event yield, the index the message will occupy is
  `len(current_session.messages)`. Use that directly (it is more robust than
  `start_index + i` in case an earlier call in the batch failed to append).

## Notes

- Do NOT add the field to `phase=start/stream` events; the index is only
  guaranteed correct at end time, and only the end phase needs it for the
  compact one-liner.
- `tool_results` events already carry `start_index` (~line 517); leave them
  unchanged.
- Event size budgets are tested in
  `application/python/tests/test_event_payload_size_budget.py` and
  `core/python/tests/` — one small int field is safely within budget, but run
  those tests.

## Test pointers

- Existing streaming tool-loop tests to mirror:
  `core/python/tests/test_application_layer_tools.py` (~line 104 collects
  `tool_partial` events) and
  `core/python/tests/test_application_layer_streaming.py` (~line 315).
