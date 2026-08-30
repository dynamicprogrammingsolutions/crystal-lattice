# Terminal rendering, progress, and UI testing

This page maps the current terminal event, rendering, progress, and interactive
test implementation. It does not redefine the application event contract.

## Ownership

- `core/python/agent_app/tool_loop.py` emits request, assistant, tool, result,
  checkpoint, cancellation, and completion events.
- `core/python/agent_app/application_future.py` compacts event batches without
  mutating the event store.
- `application/python/agent_terminal_app/terminal_app.py` polls events for the
  active terminal session.
- `application/python/agent_terminal_app/event_rendering.py` owns permanent
  terminal scrollback rendering.
- `application/python/agent_terminal_app/terminal_progress.py` reduces public
  events into transient request/LLM/tool progress.
- `application/python/agent_terminal_app/terminal.py` owns prompt input,
  command dispatch, bottom-toolbar projection, redraw invalidation, and
  terminal-only state.

## Event-compaction invariant

Within one session/request batch, the application compactor can drop:

- assistant partials preceding a final assistant event;
- tool start/stream chunks preceding `tool_results`.

It preserves `tool_partial` events whose phase is `end`. Those events carry
the final display-aware result used by terminal renderers and can include the
stored `message_index`. Preserving the event also keeps unknown additive fields
and event-store ids intact.

Tests must cross both boundaries:

1. direct `AgentApplication.compact_events()` permutations;
2. event store → `TerminalApplication.poll_new_events()` → renderer.

Direct renderer tests alone do not verify the production polling path.

## Permanent tool rendering

Full mode streams text with per-call line/character accounting and prints
final metadata. One-line mode suppresses permanent stream chunks and prints:

```text
[7] Tool: read_file
    Read: README.md
```

Call state is keyed by request and call id. A single cleanup path releases
open-call, buffer, accounting, truncation, and mode state after:

- tool end;
- request completion;
- cancellation;
- request error;
- session/renderer reset.

The tool-provided `display.single_line` value is opaque. It remains intact on
the result line; the technical `tool_name` remains in the header.

## Message-header invariant

User, System, Assistant, and Tool headers delegate to one shared header writer.
It emits one explicit empty line immediately before the colored/indexed header.
The invariant applies to live and stored-message rendering, including compact
tool headers. It excludes lifecycle/status and message detail lines.

Live `message_appended` events already carry `index`; User/System rendering
uses that field. Assistant lifecycle events carry the LLM phase
`message_index`, equal to the final event's `start_index`. The value is
provisional until a final assistant message commits, so cancellation can leave
no stored message at the displayed index.

## Progress model

`TerminalProgressState` is immutable and reduced from public events. It
represents:

- idle;
- request running;
- LLM running;
- tool running, with call/name when available.

The most specific child phase wins. Request running is the fallback between
LLM/tool phases. Request completion, cancellation, errors, session changes,
and shutdown return to idle.

The bottom toolbar calls `format_terminal_progress()` alongside agent,
session, and plugin status fields. `_poll_events()` updates progress before
permanent rendering and invalidates the active prompt application when state
changes. Progress is static and event-driven; no periodic animation or refresh
loop creates idle redraw traffic.

Permanent lifecycle and message output remains available when a terminal
cannot display the toolbar. Headless `--no-tty` mode uses pipe input and dummy
output.

## Deterministic test layers

### Pure reducer and renderer tests

Use table-driven synthetic events for:

- request/LLM/tool transitions;
- multiple tools;
- unrelated request ids;
- completion/cancellation/error cleanup;
- exact compact output;
- state isolation for missing or reused call ids.

These tests are the primary cross-platform coverage.

### In-process prompt tests

Use `prompt_toolkit` pipe input/AppSession or a controlled `PromptSession`
replacement for command dispatch, prompt configuration, startup guidance, and
headless lifecycle behavior. These tests do not claim to verify cursor
rewriting.

### Real pseudo-terminal screen tests

`test_terminal_progress_pty.py` uses:

- Pexpect to spawn and drive the production `_run_terminal` prompt loop in a
  fixed 100×24 POSIX PTY;
- a file-driven fake event source for explicit request/LLM/tool barriers;
- CPR responses because a bare PTY does not emulate terminal device replies;
- Pyte to interpret differential ANSI/VT output into visible screen rows.

Screen assertions verify what a user sees rather than requiring unchanged text
to be re-emitted in every terminal diff. The test also verifies that partially
typed input survives asynchronous output and that the Ctrl-Q binding still
exits cleanly.

The PTY test is marked `terminal_ui` and is POSIX-only. Windows and non-TTY
behavior remain covered by reducer, command, and headless tests unless a
Windows console driver is added later.

## Verification

Focused commands:

```bash
pytest application/python/tests/test_terminal_progress.py -q
pytest application/python/tests/test_terminal_progress_pty.py -q -m terminal_ui
pytest application/python/tests/test_terminal_compact_tool_rendering.py -q
pytest core/python/tests/test_application_event_compaction.py -q
```

Run the application and core default suites before delivery. Manually inspect
a real terminal with an LLM-only request, a silent tool, a streaming tool,
multiple tool calls, cancellation, and narrow terminal width.