# Terminal Progress Indicators And Deterministic Interactive UI Tests

Parent Task: tasks/20260730-one-line-tool-calls-terminal/000-main.md
Depends On: tasks/20260730-one-line-tool-calls-terminal/015-preserve-tool-end-events-through-compaction.md
Depends On: tasks/20260730-one-line-tool-calls-terminal/020-compact-live-tool-rendering.md
Depends On: tasks/20260730-one-line-tool-calls-terminal/030-compact-toggle-slash-command-and-expand.md

Add coherent in-progress presentation for the whole terminal request lifecycle,
not only compact tool output. The terminal should communicate request, LLM,
and tool execution state while preserving readable streamed output and prompt
editing. This subtask also establishes deterministic coverage for actual
interactive terminal behavior and evaluates whether prompt line rewriting is
reliable enough for production use.

## Requirements checklist

- [x] A frontend-owned progress state model represents idle, request-running,
      LLM-running, and tool-running phases, including request and tool
      identity where available.
- [x] Request, assistant/LLM, and tool lifecycle events drive deterministic
      progress transitions in full and one-line tool-output modes.
- [x] Cancellation, errors, request completion, session changes, and shutdown
      always clear progress and restore a clean prompt.
- [x] In-progress presentation does not permanently add a new scrollback line
      for every animation frame or event.
- [x] Normal streamed assistant/tool output remains readable while progress is
      visible, and prompt input is not corrupted by asynchronous event output.
- [x] A safe fallback exists for non-TTY or rewrite-incompatible environments.
- [x] Tests use injected/manual time and event barriers rather than arbitrary
      sleeps for state and animation assertions.
- [x] Automated coverage includes pure state tests, in-process
      `prompt_toolkit` interaction tests, and at least one fixed-size real
      pseudo-terminal screen-behavior test.
- [x] The selected terminal UI test dependencies, supported platforms, CI
      lane, fixture ownership, and debugging workflow are documented.

## Research and testing options

The repository already uses `prompt_toolkit` and has two useful lower-level
patterns:

- `_run_terminal_headless()` runs the real console path inside
  `create_app_session()` with `create_pipe_input()` and `DummyOutput()`.
- `test_run_terminal_uses_compact_erasing_prompt` replaces `PromptSession` to
  inspect prompt configuration.

These are appropriate for deterministic command/input/state tests but do not
prove what a human sees after cursor movement and line rewriting.

Candidate test layers:

1. **Pure progress reducer/presenter tests**
   - Fastest and cross-platform.
   - Assert event-to-state transitions, labels, priority, cleanup, and fixed
     animation frames.
   - Must be the primary coverage.
2. **In-process `prompt_toolkit` pipe-input tests**
   - Drive key input and commands without a real terminal.
   - Assert application state and command outcomes, not exact renderer bytes.
   - Reuse the package's existing headless infrastructure.
3. **Real pseudo-terminal subprocess tests**
   - Drive `crystal-lattice --console` through a PTY, send commands/keys,
     control rows/columns, and observe actual TTY-specific output.
   - Best boundary for prompt restoration and rewrite behavior.
   - Recommendation: evaluate `pexpect` as a test-only POSIX driver.
4. **Terminal screen emulation**
   - Feed captured ANSI/VT output into an in-memory screen and assert visible
     rows/cursor rather than brittle raw escape sequences.
   - Recommendation: add `pyte` only if the PTY spike shows that raw output
     assertions are unstable or insufficient.
5. **Manual/tmux capture**
   - Useful for exploratory diagnostics and visual review.
   - Not suitable as the primary automated gate because timing, installed
     tools, and host terminal configuration are difficult to control.

## Execution plan
Status: Approved

Start with a short, bounded prototype using the existing bottom toolbar. It is
already owned by `prompt_toolkit`, remains visible while the prompt is active,
and avoids manually writing carriage-return/erase sequences into patched
stdout. Extend the toolbar supplier with progress state and explicitly
invalidate/redraw the active prompt application when `_poll_events` changes
that state.

Keep progress calculation separate from terminal drawing:

- create an immutable or conventionally immutable progress state;
- implement a pure reducer from public events to the next state;
- format a stable semantic label separately from animation frames;
- inject a clock/frame source or use an explicit tick event;
- let `_poll_events` update state and request redraw;
- keep ordinary message/event renderers responsible for permanent scrollback.

Suggested event mapping:

- `request_started` → request running fallback;
- `assistant_message(start)` → LLM step running;
- reasoning/content partials may refine the LLM label without resetting time;
- `tool_calls` identifies upcoming tools;
- `tool_partial(start/stream)` → active tool;
- `tool_partial(end)` → finish that tool and return to request/next phase;
- `final`, `request_completed`, `request_cancelled`, and `error` → clear or
  transition according to the actual lifecycle order.

Prototype both a static label and a spinner. Keep animation only if it can be
driven by a controlled refresh interval and does not cause excessive CPU,
flicker, or prompt corruption. If toolbar rewriting fails in a supported
terminal, retain the pure model and use a minimal append-only phase message
fallback without animation.

For PTY verification, use a deterministic echo/fake provider and tools that
wait on test-controlled synchronization primitives. The test controls when
the LLM/tool phase starts, emits output, completes, fails, or cancels. Fix
terminal dimensions and environment, capture output continuously, and assert
visible screen states at explicit barriers. Do not use hosted APIs or
wall-clock sleeps to manufacture progress duration.

### Implementation decisions and open questions

- Recommended production surface: the existing bottom toolbar plus explicit
  prompt invalidation, not hand-written ANSI rewriting.
- Recommended initial test driver: `pexpect` on POSIX as a dev/test
  dependency. It drives a real PTY and allows fixed terminal dimensions.
- Recommended screen assertion strategy: first assert semantic transitions and
  prompt recovery through Pexpect; add `pyte` if final-screen/cursor
  assertions need VT emulation.
- Open platform question: define whether the real-PTY lane is required on
  macOS and Linux only, with Windows covered by reducer/pipe-input tests, or
  whether a Windows console driver is required now.
- Open UX question: exact labels and priority when LLM and tool lifecycle
  events overlap. Recommendation: show the most specific active child phase,
  with request-running as fallback.
- Open animation question: static status versus spinner frames. Recommendation:
  deliver static state first and enable animation only after deterministic PTY
  evidence.

### Documentation

- Subtask 060 documents user-visible progress behavior and current
  implementation/testing architecture.
- If a new reusable terminal test harness is added, document fixture usage and
  failure diagnostics in `application/python/docs/development/`.

### Task checklist

- [x] Prototype bottom-toolbar invalidation with request/LLM/tool events.
- [x] Select PTY driver, screen assertion approach, platform support, and CI
      marker/dependency policy.
- [x] Implement pure progress state/reducer/formatter.
- [x] Integrate progress updates with terminal polling and prompt redraw.
- [x] Add cleanup/fallback behavior for every terminal lifecycle outcome.
- [x] Add deterministic reducer and pipe-input tests.
- [x] Add fixed-size real-PTY tests for visible state and prompt restoration.
- [x] Run manual supported-terminal observations and record implementation
      findings.

### Requirement verification

- Table-driven reducer tests cover all public event transitions and cleanup.
- In-process prompt tests prove commands/input continue working during state
  changes.
- PTY tests observe request, LLM, and tool progress at controlled barriers,
  then observe the original prompt and typed buffer restored after completion,
  cancellation, and asynchronous output.
- Full and one-line tool-output scenarios produce the same progress lifecycle
  while retaining their distinct permanent result rendering.
- Non-TTY tests prove headless startup/shutdown remains clean.

### Additional implementation verification

- Test narrow and wide terminal widths, resize if supported, color/no-color
  behavior, rapid phases, long silent phases, streamed output, multiple tool
  calls, cancellation, and exceptions.
- Monitor redraw frequency/CPU in a manual long-running request before
  enabling animation by default.

## Completion Notes

- Added immutable `TerminalProgressState`, a pure reducer, and a stable
  formatter for request, LLM, and tool phases.
- The existing bottom toolbar projects progress; event updates invalidate the
  active prompt without periodic idle redraw.
- Progress is deliberately static. Existing lifecycle/permanent output is the
  fallback when a toolbar is unavailable; `--no-tty` remains safe.
- Added application `dev` dependencies for Pexpect and Pyte plus the
  `terminal_ui` marker.
- The fixed 100×24 PTY harness uses production `_run_terminal`, explicit JSON
  event barriers, CPR replies, and a Pyte screen. It verifies visible request,
  LLM, and tool state, typed-buffer restoration through asynchronous tool and
  request output, and Ctrl-Q shutdown.
- Repeated PTY debugging observed differential line rewriting directly and
  motivated screen-level assertions; animation was not enabled.
- POSIX owns real-PTY coverage. Cross-platform reducer, renderer, command,
  startup, and headless tests remain in the default suite.