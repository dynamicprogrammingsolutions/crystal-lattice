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
