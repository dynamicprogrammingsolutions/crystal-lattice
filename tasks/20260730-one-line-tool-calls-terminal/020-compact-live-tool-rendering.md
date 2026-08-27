# Compact (One-Line) Live Tool Rendering In `ToolRenderer`

Parent Task: tasks/20260730-one-line-tool-calls-terminal/000-main.md
Depends On: tasks/20260730-one-line-tool-calls-terminal/010-message-index-in-tool-partial-end-events.md

Teach the live `tool_partial` rendering path in
`application/python/agent_terminal_app/event_rendering.py` a compact mode
that collapses each tool call to a single line, reusing the short-mode
content selection and truncation logic that already exists for
`/list short`. Do not duplicate that logic.

## Requirements checklist

- [x] `TerminalRenderContext` accepts a compact-mode supplier (e.g.
      `compact_supplier: Callable[[], bool]`) and passes it to `ToolRenderer`.
      The toggle state itself lives in the terminal UI layer (subtask 030);
      rendering only reads it per event so mid-request toggling works.
- [x] When compact mode is ON, `ToolRenderer.render_event`:
  - [x] suppresses streamed output for `phase=start/stream` (no header, no
        body lines) — output for the call is deferred to the end event;
  - [x] on `phase=end`, prints exactly ONE line combining index, tool name,
        and short content, e.g.
        `[7] Tool: read_file README.md (truncated)` — colors consistent with
        existing header/footer styling (BLUE header token, YELLOW tool name,
        GRAY content is a reasonable starting point);
  - [x] uses `event["message_index"]` (from subtask 010) for `[<index>]`;
        omit the bracket cleanly if the field is absent (older events);
  - [x] selects content via the existing
        `_select_content_from_message(result, short=True)` (~line 565), which
        already prefers `metadata.display.single_line`;
  - [x] condenses/truncates via the existing short-mode branch logic used by
        `render_message` (~lines 801-824: single-line join +
        `tool_output_short_char_limit`); factor that branch into a small
        shared helper rather than copy-pasting it.
- [x] When compact mode is OFF, behaviour is byte-for-byte identical to
      today (full streaming + header/content/footer on end).
- [x] Per-call bookkeeping (`_open_calls`, `_line_buffers`,
      `_printed_lines/_printed_chars`, `_truncated_calls`) stays consistent
      if the user toggles compact mode mid-call: read the supplier once per
      call (e.g. record the mode at `phase=start` keyed by call id, falling
      back to the current value at `end` for calls with no start), so a call
      never renders half-streamed then also one-lined.

## Current code map (verified)

- `ToolRenderer.render_event` — event_rendering.py ~lines 608-773.
  - `phase=end` branch ~lines 622-684: prints header + content (with
    `_apply_tool_limits`) + footer when no stream chunks were seen; footer
    only otherwise; flushes per-call line buffers.
  - `phase=start/stream` branch ~lines 686-773: prints header once per
    call id, then line-buffered streaming with full-view limits.
  - `part_type == "summary"` payloads (~line 696) are printed unconditionally
    today (exit codes / stderr); in compact mode suppress these too — the
    one-liner is the whole visible output (the full detail remains available
    via `/list <index>`).
- `ToolRenderer.render_message` short branch — ~lines 801-824. This is the
  logic to factor out and reuse.
- Short-mode config already loaded in `ToolRenderer.__init__` ~lines 557-563
  (`tool_output_short_char_limit`, `tool_output_short_one_line`,
  `tool_output_short_line_limit`).
- `TerminalRenderContext.__init__` — ~lines 830-841; constructed in
  `terminal.py` `_run_terminal` (~line 1979) and defensively in `_cmd_list`
  (~line 1634). Both construction sites need the new supplier argument
  (default `lambda: False` keeps tests/back-compat working).

## Notes / edge cases

- The `AssistantRenderer` "tools: N call(s): ..." summary line only exists in
  the list view (`render_message` ~line 524), not the live path — no change
  needed there.
- Lifecycle noise (`request_started`/`completed`) and log lines are out of
  scope for this ticket.
- Footer metadata (timestamp, `tool_call_id`) is intentionally dropped from
  the compact line except the tool name; it remains available via
  `/list <index>`.

## Post-completion follow-up

### Follow-up requirements checklist

- [x] Compact rendering keeps the technical `metadata.tool_name` visible in a
      header line containing the message index.
- [x] The compact result is rendered on one dedicated following line, using
      `metadata.display.single_line` when available and the existing
      condensed/truncated fallback otherwise.
- [x] The renderer never concatenates the tool name and compact result into
      one line; exact-output tests use representative real display payloads
      such as `Read: README.md` and shell command previews.
- [x] Per-call renderer state is released after normal completion,
      cancellation, request error, request completion, and renderer/session
      reset.
- [x] Call bookkeeping cannot collide across requests when a tool call id is
      absent or reused.

## Execution plan
Status: Approved

Refactor compact output into a small two-line block:

```text
[7] Tool: read_file
    Read: README.md
```

The first line owns stable technical identity and expansion index. The second
line owns the tool-provided compact preview. Do not attempt string-prefix
deduplication: `display.single_line` is an opaque tool-owned preview and is
kept intact on its dedicated line. If no preview exists, select display-aware
full content, collapse whitespace, and apply the existing short character
limit.

Centralize transient-state cleanup in one helper instead of repeating
individual `dict.pop` calls. Key call state by request plus call identity, or
otherwise prove that missing/reused ids cannot share state. Teach the renderer
to observe request terminal events before its current `tool_partial` early
return, and clear matching state on cancellation, error, and completion.
Renderer replacement/session switching must also start from empty transient
state.

### Implementation decisions and open questions

- Decided output boundary: technical tool name in the header; one-line result
  on its own line.
- Recommended indentation: four spaces before the result, with existing gray
  styling. Confirm this visual during the PTY work in subtask 050.
- Prefer a composite `(request_id, tool_call_id)` state key with a generated
  event-local fallback for missing ids. If this complicates legacy events,
  document and test the narrower safe alternative.
- Progress indicators are not implemented here; subtask 050 owns running
  state and line rewriting.

### Documentation

- User-visible wording and examples are owned by subtask 060.
- Update renderer docstrings/comments here so “compact” no longer claims the
  complete call occupies exactly one physical line.

### Task checklist

- [x] Add exact-output regression cases using representative tool display
      payloads.
- [x] Split compact header and result rendering.
- [x] Introduce centralized per-call cleanup and request-aware state keys.
- [x] Clear state on all terminal request outcomes and renderer reset.
- [x] Verify full mode and `/list` rendering remain unchanged.

### Requirement verification

- Exact line-array assertions match the approved two-line format.
- Fallback content remains one physical line and obeys the short character
  limit.
- Tests that start a call and then cancel/error/complete prove all transient
  state collections are empty.
- Two requests with reused or missing call ids do not inherit each other's
  mode or buffers.

### Additional implementation verification

- Run compact renderer, terminal event-rendering, cancellation, and existing
  tool display tests.
- Exercise representative shell, read, write, image, error, and empty-result
  display payloads.

### Follow-up completion notes

- Compact output now uses `[index] Tool: <technical-name>` followed by one
  indented compact-result line.
- `display.single_line` remains opaque and intact; fallback content is
  whitespace-condensed and short-limit truncated.
- All transient collections use request/call keys and one cleanup helper.
- Completion, cancellation, error, session change, and renderer reset coverage
  proves state returns to empty; reused and missing call ids are isolated.
- Existing full renderer, display-aware output, and `/list` tests pass.
