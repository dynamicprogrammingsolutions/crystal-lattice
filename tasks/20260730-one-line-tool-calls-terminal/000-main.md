# CL-335: One-Line Tool Calls In The Terminal (Live View)

When the LLM makes many tool calls in a row, the terminal's live streaming view
prints a multi-line block per call (`Tool:` header + full/limited output +
footer with tool name/timestamp/call id). A few calls push the user's earlier
messages off screen. This task adds a slash-command toggle that collapses each
live tool call/result to a single compact line, plus a way to re-print any
specific tool message in full detail by its message index.

## Task checklist

- [x] `tasks/20260730-one-line-tool-calls-terminal/010-message-index-in-tool-partial-end-events.md`
- [x] `tasks/20260730-one-line-tool-calls-terminal/020-compact-live-tool-rendering.md`
- [x] `tasks/20260730-one-line-tool-calls-terminal/030-compact-toggle-slash-command-and-expand.md`
- [x] `tasks/20260730-one-line-tool-calls-terminal/040-tests-and-docs.md`

## Problem (reproduced)

Prompt used to reproduce (with a working provider, e.g. Gemini via OpenRouter):

```
List the files in the current directory, then read the contents of README.md,
then read the contents of package.json, and summarize what this project does.
```

Observed output per tool call in the live view:

```
Tool:
<full or line-limited tool output, up to 20-100 lines>
list_directory tool_call_id: tool_list_directory_Gt1awVLuFJ29VfQ9VF0i
```

Three calls produced ~40+ lines of tool plumbing before the final assistant
summary appeared.

## Desired behaviour

- New slash command (working name `/compact`) toggles live compact mode for
  the current terminal run. When ON, each tool call renders as one line, e.g.:

  ```
  [7] Tool: read_file README.md (truncated)
  ```

  including the message index so the user can expand it later.
- Expansion by index reuses the existing `/list <index>` command, which
  already re-prints a single message in full (`short=False`). No new
  full-render logic is needed; the compact line just has to display the index.
- Default remains full (current) rendering; compact is opt-in per run, with an
  optional application-config default.

## Architecture summary (researched; verified against code)

Rendering has two distinct paths that already share content-selection logic:

1. **Live streaming path** — `_poll_events` in
   `application/python/agent_terminal_app/terminal.py` (~line 374) polls
   events and calls `TerminalRenderContext.render_event`.
   `ToolRenderer.render_event` in
   `application/python/agent_terminal_app/event_rendering.py` (~line 608)
   handles `tool_partial` events: it streams output lines for
   `phase=start/stream` and prints header/content/footer for `phase=end`
   (~lines 622-684). This path has NO compact mode today and always renders
   with `include_index=False`.
2. **History list path** — `/list [short] [range]`
   (`_cmd_list` in `terminal.py` ~line 1580) calls
   `ToolRenderer.render_message` (~line 793), which DOES support
   `short=True`: it prefers `metadata.display.single_line` via
   `_select_content_from_message(msg, short=True)` (~line 565) and condenses
   to a single line via config keys `tool_output_short_one_line`,
   `tool_output_short_char_limit`, `tool_output_short_line_limit`
   (schema in `terminal_app.py` `get_application_config_schema()` ~line 1046).

Key reuse facts (verified):

- The compact content (`metadata.display`, incl. optional `single_line`) is
  computed live at tool-execution time in `core.iter_tool_messages`
  (`core/python/agent_core/core.py` ~lines 4620-4692, via
  `tool.to_display_format(...)`) and attached to the tool message BEFORE it is
  yielded. The `tool_partial` end event wraps that same message as
  `payload["result"]` (`core/python/agent_app/tool_loop.py` ~lines 464-474).
  So live and stored views read the exact same dict — no new short-output
  logic is needed, only wiring.
- `_select_content_from_message` is already shared between the live end-phase
  path (~line 635, currently called with default `short=False`) and the list
  path (~line 801, called with `short=short`).
- Message indices: `message_appended` events already carry `"index"`
  (`terminal_app.py` ~lines 323, 887); `final` and `tool_results` events carry
  `start_index` + ordered `messages` (`tool_loop.py` ~lines 242-247, 513-519).
  The granular `tool_partial` events carry only `tool_call_id` — the index is
  computable at emit time (`len(current_session.messages)` just before
  `core.add_message` appends the tool message) but is not in the payload yet.
  Subtask 010 adds it.

## Constraints

- The terminal is an append-only scrolling stream (`prompt_toolkit`
  `PromptSession` + `patch_stdout`), NOT a redrawable TUI. True in-place
  collapse/expand (Claude Code style) is out of scope; expansion re-prints
  the full message further down the scrollback via `/list <index>`.
- Per `application/python/agent_terminal_app/AGENTS.md`: `terminal.py` stays
  UI-only; non-trivial logic belongs in `terminal_app.py`; rendering changes
  must preserve readability in a plain terminal; new behaviour needs tests in
  `application/python/tests`.

## Completion Notes (added during completion)

All four subtasks implemented and verified on 2026-07-30.

- `core/python/agent_app/tool_loop.py`: `tool_partial` end events now carry
  `message_index` (`len(current_session.messages)` at yield time, before the
  tool message is appended). Additive field only.
- `application/python/agent_terminal_app/event_rendering.py`:
  - `ToolRenderer` takes an optional `compact_supplier`; the mode is fixed per
    call at the first event seen (`_call_modes`) so mid-call toggles never mix
    modes.
  - Compact end events render one line via `_render_compact_line`
    (`[<index>] Tool: <name> <short content>`); start/stream/summary output is
    suppressed for compact calls.
  - The `/list short` condensing branch was factored into `_condense_short`
    and is shared by both views.
  - `TerminalRenderContext` accepts and forwards `compact_supplier`.
- `application/python/agent_terminal_app/terminal.py`: new `/compact [on|off]`
  command (+ completion), `ui_state["compact_tool_calls"]` seeded from
  `_initial_compact_state` (config key `tool_output_live_compact`), supplier
  wired at both `TerminalRenderContext` construction sites.
- `application/python/agent_terminal_app/terminal_app.py`: config schema entry
  for `tool_output_live_compact` (bool, default False).
- Tests: `application/python/tests/test_terminal_compact_tool_rendering.py`
  (9 tests) and `test_streaming_tool_partial_end_events_carry_message_index`
  in `core/python/tests/test_application_layer_tools.py`. All pass, plus
  regression suites (terminal app 40, server 48, core tools/streaming/event
  size 20).
- Docs: `application/python/README.md` (command list + "Compact Tool Calls"
  section), `docs/reference/default-config.md`, and
  `default_config/config.json` gained the new key.
- Live smoke test: `/compact` toggles with the expand hint; `/compact bogus`
  prints usage.

Known limitation (by design): expansion re-prints the message further down
the scrollback via `/list <index>`; the original compact line is not redrawn
in place (append-only terminal). Note `/list <negative-index>` without a
colon is rejected by the existing range normalization — use `/list -1:` for
negative indices; compact lines always show non-negative indices, so
`/list <index>` works for them.
