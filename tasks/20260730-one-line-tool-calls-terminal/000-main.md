# CL-335: One-Line Tool Calls In The Terminal (Live View)

When the LLM makes many tool calls in a row, the terminal's live streaming view
prints a multi-line block per call (`Tool:` header + full/limited output +
footer with tool name/timestamp/call id). A few calls push the user's earlier
messages off screen. This task adds a slash-command toggle that collapses each
live tool call/result to a single compact line, plus a way to re-print any
specific tool message in full detail by its message index.

## Requirements checklist

- [x] Live tool-result events expose the stored message index needed for
      expand-by-index behavior.
- [x] The terminal can opt into a compact live tool-result presentation while
      preserving full stored output for `/list <index>`.
- [x] The original command, configuration default, tests, and initial user
      documentation are present.
- [x] Renderable `tool_partial` end events survive application event
      compaction and reach terminal consumers with their payload and
      `message_index` unchanged.
- [x] Compact tool presentation keeps the technical tool name and renders the
      compact result on its own physical line without concatenated duplicate
      identity text.
- [x] Interrupted, cancelled, failed, and completed calls release all
      transient renderer state.
- [x] `/compact` remains available for future context compaction; the tool
      output feature uses an approved, explicit command and mode vocabulary.
- [x] The terminal shows coherent in-progress state for the request, LLM
      phases, and tool execution in both full and compact tool-output modes.
- [x] Deterministic automated coverage exercises terminal state transitions
      and at least one real pseudo-terminal rendering path without a hosted
      provider.
- [x] User documentation explains important terminal commands and application
      configuration behavior, while development documentation explains the
      changed event, renderer, progress, and terminal-testing boundaries.

## Subtasks

- [x] `tasks/20260730-one-line-tool-calls-terminal/010-message-index-in-tool-partial-end-events.md`
- [x] `tasks/20260730-one-line-tool-calls-terminal/015-preserve-tool-end-events-through-compaction.md`
- [x] `tasks/20260730-one-line-tool-calls-terminal/020-compact-live-tool-rendering.md`
- [x] `tasks/20260730-one-line-tool-calls-terminal/030-compact-toggle-slash-command-and-expand.md`
- [x] `tasks/20260730-one-line-tool-calls-terminal/040-tests-and-docs.md`
- [x] `tasks/20260730-one-line-tool-calls-terminal/050-terminal-progress-and-interactive-ui-tests.md`
- [x] `tasks/20260730-one-line-tool-calls-terminal/060-terminal-user-and-development-documentation.md`

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

## Post-completion follow-up

Review on 2026-08-25 identified follow-up work that extends and corrects the
completed implementation.

- **Fact:** the shared event-compaction policy that drops `tool_partial`
  events before `tool_results` predates the CL-335 commit. CL-335 did not
  introduce that policy, but its one-line rendering depends on the
  `tool_partial` end event and therefore exposes the existing loss as a
  user-visible failure. The same policy can also hide pre-existing full
  rendering for fast or non-streaming tools.
- **Decision:** compact presentation retains the technical tool name as a
  header and puts the tool-provided/fallback one-line result on a dedicated
  following line.
- **Decision:** progress work is intentionally wider than compact tool output;
  it covers request, LLM, and tool phases and evaluates actual terminal
  rewriting behavior.
- **Question:** choose the replacement command for tool-output presentation.
  The recommendation is `/tool-output one-line|full`, with `/tool-output`
  reporting current state and no `/compact` compatibility alias.
- **Question:** choose the startup discoverability policy. The recommendation
  is a concise quick-help summary with a configuration option to select
  `summary`, `hint`, or `off`, rather than printing the full command catalog
  on every launch.

## Execution plan
Status: Approved

Execute the follow-up as five bounded workstreams. First correct the shared
event-compaction contract so downstream rendering can rely on end events.
Then refine compact rendering and command naming. Build the broader progress
model and terminal test harness only after the underlying event stream is
stable. Finish by aligning user and development documentation with the
approved behavior and verified output.

The event correction remains an independent subtask because it fixes shared
application behavior that existed before CL-335. The renderer and command
corrections remain post-completion follow-ups in their existing owner
subtasks. Progress/testing and documentation receive new subtasks because
their scope is wider than the original compact renderer implementation.

### Implementation decisions and open questions

- Recommended command: `/tool-output one-line|full`; no-argument invocation
  reports state, and `/compact` is not registered as an alias.
- Recommended progress surface: extend the existing `prompt_toolkit` bottom
  toolbar with event-driven request/LLM/tool state and explicit redraw
  invalidation. Keep an append-only fallback if real pseudo-terminal testing
  shows rewriting is unreliable in a supported environment.
- Recommended terminal UI test stack:
  - pure state/reducer tests for most transitions;
  - existing `prompt_toolkit` pipe-input/AppSession tests for input and command
    integration;
  - a real POSIX pseudo-terminal driver for rendering behavior;
  - a terminal screen emulator only if raw ANSI assertions prove too brittle.
- Approval is needed for the exact replacement command, whether the
  application config key is renamed, the startup-help default, and adding
  test-only PTY/screen-emulation dependencies.

### Documentation

- Keep the README concise and route detailed terminal usage to an
  application-owned user page under `application/python/docs/`.
- Document command modes, runtime versus persisted configuration, one-line
  result fallback/truncation, progress behavior, cancellation, and expansion.
- Update application development documentation for event compaction,
  renderer lifecycle state, progress ownership, prompt redraw, and layered
  terminal UI testing.
- Change maintained configuration/schema sources and regenerate reference
  output through the documentation preparation workflow; do not hand-maintain
  generated copies as independent sources.

### Task checklist

- [x] Approve or revise the material command, config-key, startup-help, and
      terminal-test-framework decisions.
- [x] Complete the event-compaction correction in subtask 015.
- [x] Complete renderer formatting and cleanup follow-up in subtask 020.
- [x] Complete command/config naming follow-up in subtask 030.
- [x] Complete progress indicators and deterministic UI harness in subtask
      050.
- [x] Complete user/development documentation and discoverability in subtask
      060.
- [x] Re-run focused and package-level verification and update requirement
      evidence before completion.

### Requirement verification

- Event compaction: a public polling-path test proves a same-batch
  `tool_partial(end)` plus `tool_results` still yields the end event, and the
  terminal renders it.
- Compact presentation: exact normalized output assertions prove the tool
  name and one-line result occupy separate lines and `/list <index>` still
  expands the stored message.
- Cleanup: cancellation/error/completion tests prove renderer state returns to
  empty without relying on private timing.
- Command: command registry, completion, help, state-reporting, explicit mode,
  and reserved `/compact` behavior are covered.
- Progress/UI: deterministic event-transition tests plus a fixed-size
  pseudo-terminal test prove visible request, LLM, and tool progress and clean
  prompt restoration.
- Documentation: authored user/development pages, indexes, generated
  reference preparation, and tested examples agree with delivered behavior.

### Additional implementation verification

- Run the fast core and application suites affected by event compaction and
  terminal rendering.
- Run the new terminal UI lane on each supported POSIX CI environment and
  record any Windows/non-TTY fallback boundary explicitly.
- Manually exercise a fast tool, a silent long-running tool, a streaming tool,
  an LLM-only request, cancellation, and repeated tool-loop phases in a real
  terminal before marking progress rendering complete.

## Implementation Notes

- 2026-08-25: User approved the recommended decisions:
  `/tool-output one-line|full`, `tool_output_live_one_line`, configurable
  startup help with default `summary`, bottom-toolbar progress with a static
  semantic state first, Pexpect for the POSIX PTY lane, and Pyte only if the
  PTY prototype needs terminal-screen emulation.

### Follow-up completion notes

- Shared event compaction now preserves `tool_partial(phase="end")` while
  continuing to drop redundant start/stream chunks before `tool_results`.
- Compact tool results render as a technical tool header plus one dedicated
  preview line. Renderer state is request-aware and cleared through one
  cleanup path on end, completion, cancellation, error, and terminal reset.
- `/compact` is no longer registered. `/tool-output` reports or selects
  `one-line|full`; the startup config key is
  `tool_output_live_one_line`.
- `TerminalProgressState` reduces public events into static request, LLM, and
  tool toolbar status. Prompt invalidation keeps asynchronous state visible
  without periodic refresh or animation frames.
- The deterministic terminal UI lane uses Pexpect for the fixed-size POSIX PTY
  and CPR replies, and Pyte for visible-screen/cursor semantics. It verifies
  request → LLM → tool transitions, asynchronous permanent output, typed-buffer
  restoration, and Ctrl-Q shutdown.
- User docs moved to `application/python/docs/terminal.md`; development docs
  map event compaction, renderer/progress ownership, prompt redraw, and the
  layered test strategy.
- Verification:
  - application default suite: 351 passed, 90 deselected;
  - core default suite: 468 passed, 26 deselected, 1 expected xfail;
  - docs-site tests: 15 passed;
  - MkDocs prepare/build/reference refresh: passed;
  - focused Ruff and Black checks: passed;
  - `git diff --check` and JSON validation: passed.
- Pyright was not run because the executable is not installed in the current
  environment. No Pyright claim is made.
