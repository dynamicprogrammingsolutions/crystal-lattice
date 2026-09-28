# Complete hard cancellation and add soft request cancellation

Audit and complete foreground shell-tool hard cancellation, while preserving
the existing hard-cancel action and adding a distinct soft-cancel workflow that
lets the active tool finish before stopping the request.

## Requirements checklist

- [x] R1. The existing request-cancel operation remains backward compatible
  and continues to mean hard cancellation: active providers are cancelled,
  active cooperative foreground tools are interrupted, and no later request
  phase starts.
- [x] R2. Every first-party foreground Bash/shell execution path used by the
  application responds promptly to hard cancellation and terminates the whole
  launched process tree rather than only its immediate parent.
- [x] R3. A new soft-cancel operation cancels an active provider call, but does
  not interrupt an already-running foreground tool; that tool finishes
  normally, its final result is appended and checkpointed, and the request
  stops before another tool or provider phase starts.
- [x] R4. A hard cancel issued after a soft cancel escalates the same request
  and interrupts a still-running foreground tool; cancellation races before
  live request registration preserve the strongest requested mode.
- [x] R5. Successfully handed-off explicit background commands are not
  retroactively terminated by either request-cancel mode and remain governed
  by their existing background-process stop mechanisms.
- [x] R6. The HTTP API, embedded mobile runtime, frontend SDK, chat controller,
  terminal, mobile client, and desktop client expose soft cancellation while
  retaining access to hard cancellation for an active request.
- [x] R7. Request lifecycle events identify whether an observed cancellation
  was soft or hard without breaking clients that consume the existing
  `request_cancelled` event.

## Scope

This task covers:

- request-level hard/soft cancellation state and escalation;
- provider-versus-tool cancellation signaling;
- first-party Bash/shell foreground execution;
- HTTP, embedded runtime, terminal, SDK, mobile, and desktop surfaces;
- cancellation event metadata;
- focused specifications and current-behavior documentation.

It does not change the operation-specific cancellation model used by managed
background jobs, add durable cancellation history, or introduce a new generic
operation framework.

## Requirement questions

None. The behavior and public boundaries below were approved before this task
was created.

## Approved decisions

- `POST /requests/{request_id}/cancel` and the existing
  `cancel_request`/`cancelRequest` APIs retain hard-cancel semantics.
- The new HTTP operation is
  `POST /requests/{request_id}/soft-cancel`, with a
  `soft_cancel_requested` acknowledgement.
- Soft cancellation interrupts an active provider as existing cancellation
  does, but tools receive a hard-only cancellation channel and therefore
  finish normally after soft cancellation.
- `request_cancelled` remains the terminal cancellation event and gains a
  backward-compatible `cancellation_mode` field with value `soft` or `hard`.
- Hard cancellation can promote a previously soft-cancelled request; soft
  cancellation can never downgrade hard cancellation.
- The existing mobile/desktop cancel action remains hard cancellation. A
  separate `Soft cancel request` action is added, and hard cancellation stays
  available after soft cancellation so the user can escalate.
- Explicit background commands remain owned by their existing background
  lifecycle after successful handoff.

## Supporting details

### Shell cancellation audit

| Implementation | Current state | Relevant boundary |
|---|---|---|
| Codex `shell` | Hard cancellation works through its streaming path | `plugins/codex-tools/src/codex_tools/shell_tool.py` |
| Codex `shell_command` | Hard cancellation works through async and sync streaming paths | `plugins/codex-tools/src/codex_tools/shell_command_tool.py` |
| Claude `Bash` | Cancellation is accepted only through discarded optional arguments and is not forwarded | `plugins/claude-tools/src/claude_tools/claude_bash_tool.py` |
| Gemini `run_shell_command` | Does not accept or forward cancellation | `plugins/gemini-tools/src/gemini_tools/gemini_shell_tool.py` |
| Qwen `bash` | Does not accept or forward cancellation | `plugins/qwen-tools/src/qwen_tools/qwen_shell_tool.py` |
| Kimi `Shell` | Does not accept or forward cancellation | `plugins/kimi-tools/src/kimi_tools/kimi_shell_tool.py` |
| Grok `bash` | Does not accept or forward cancellation and has no execution timeout | `plugins/grok-tools/src/grok_tools/grok_shell_tool.py` |
| Generic `.bash` plugin host | Streaming execution has neither a cancellation callback nor process-group termination | `core/python/agent_core/tool_hosts/bash_tool_plugin.py` |
| Codex legacy shell | Disabled by default; streaming execution has no cancellation callback and timeout kills only the immediate process | `plugins/codex-tools/src/codex_tools/shell_tool_legacy.py` |

Claude, Gemini, Qwen, Kimi, and Grok use
`plugins/tool-compat-shared/src/tool_compat_shared/shell_engine.py`. The shared
runner already isolates foreground subprocesses and terminates their process
groups on timeout, so one optional hard-cancellation input there can provide
the common execution behavior. Each wrapper still needs to accept, forward,
and format cancellation coherently.

The generic Bash host and Codex legacy shell own independent synchronous
subprocess loops and need localized use of the shared process-launch and
process-tree termination helpers.

### Current cancellation flow

- `AgentApplication` owns request cancellation registration, including
  cancellation requested before the live controller exists.
- `RequestCancellation` currently has one event and one callback collection;
  setting the event invokes provider and tool callbacks without distinction.
- `ToolLoopRunner` checks request cancellation before phases and after each
  completed tool. Its existing post-tool checkpoint is the correct safe
  boundary for soft cancellation.
- `AgentCore.iter_tool_messages` forwards the supplied cancellation object to
  tool hooks. The application must therefore pass a tool-specific hard-only
  view rather than requiring each tool to understand soft-cancel policy.
- Frontend streaming state already retains `activeRequestId` until
  `request_cancelled` or `request_completed`, which naturally keeps a softly
  cancelled request active while its current tool finishes.

### Target cancellation model

The request controller needs three related signals:

1. overall stop requested, set by soft or hard cancellation and observed by
   tool-loop checkpoints;
2. provider interruption, set by soft or hard cancellation and supplied to
   provider execution;
3. tool interruption, set only by hard cancellation and supplied to tool
   execution.

Pre-registration cancellation state must record `soft` or `hard` per request
instead of only request-ID membership. Registration initializes all channels
atomically from that mode. Promotion from soft to hard signals the tool
channel immediately.

## Execution plan

Status: Approved

Execution was authorized after task creation. The overlapping application and
frontend modifications observed during planning were no longer present at
execution start; the unrelated deleted mobile certificate resource remains
out of scope and must be preserved.

Implement the work in dependency order. First make the cancellation controller
able to represent overall stop, provider interruption, and hard-only tool
interruption without changing the existing hard-cancel API. Replace the
pre-cancelled request-ID set with mode-aware state under the existing lock and
make hard mode dominant under races.

Thread the provider channel through provider calls and the tool channel through
`AgentCore.iter_tool_messages`. Continue using overall stop state for
`ToolLoopRunner` checkpoints. Preserve the current sequence in which a
completed tool result is appended, emitted, and checkpointed before the outer
loop observes cancellation. Ensure only the currently active tool completes;
do not begin another queued tool or another provider phase after soft
cancellation. Include `cancellation_mode` on the terminal
`request_cancelled` event.

Complete shell hard cancellation next. Add an optional cancellation input to
the shared async shell runner, register it only for foreground execution,
schedule existing process-tree termination on the runner's event loop, remove
the callback in `finally`, and distinguish cancellation from timeout in its
result. Forward the hard-only tool channel through Claude, Gemini, Qwen, Kimi,
and Grok. Apply the established isolated-process-group/callback pattern to the
generic Bash host and disabled Codex legacy shell. Preserve each vendor's
model-facing schema and formatting. Do not attach request cancellation to a
background command after successful handoff.

Add `AgentApplication.soft_cancel_request`, retaining
`AgentApplication.cancel_request` as hard cancellation. Add the FastAPI
soft-cancel route with its own idempotency scope and mirror it in the embedded
mobile Python runtime. The bridge transports should need no product logic;
verify that generic HTTP forwarding carries the new route. Keep coordinator
shutdown and timeout-driven cancellation hard.

Extend the frontend backend interface, REST adapter, and chat controller with
`softCancelRequest` and `softCancelActiveRequest`. Add mobile and desktop
composer actions with stable test identifiers. Keep the existing cancel
action/button wired to hard cancellation, keep hard cancellation enabled after
a soft-cancel acknowledgement, and prevent accidental duplicate soft requests
without clearing the active request locally. Add terminal `/soft-cancel`;
retain `/cancel` and its existing shortcut as hard cancellation.

### Implementation decisions and open questions

- Decision: application orchestration owns the soft-versus-hard policy; tool
  plugins receive only the hard-only tool cancellation channel.
- Decision: soft cancellation preserves provider interruption while allowing
  an already-running foreground tool to finish.
- Decision: the public hard-cancel API and route remain unchanged.
- Decision: cancellation mode is added to `request_cancelled`; no separate
  immediate `request_cancel_requested` event is required in this task.
- Decision: background tasks are outside request cancellation after handoff.
- Decision: no new terminal keyboard shortcut is required for soft cancel;
  `/soft-cancel` is sufficient.
- Open questions: none.

### Documentation

Create an application-owned specification because `AgentApplication` defines
the behavior and independently maintained server, SDK, frontend, and plugin
packages consume it:

- Create
  `application/python/docs/development/specifications/request-cancellation/index.md`
  describing the public hard/soft semantics, provider and tool channels,
  escalation, pre-registration races, events, background-task boundary, and
  compatibility guarantees.
- Create
  `application/python/docs/development/specifications/request-cancellation/requirements.md`
  with stable requirement IDs and separate implementation, verification, and
  documentation states.
- Link the specification from
  `application/python/docs/development/index.md`.

When implementation lands, update current documentation rather than presenting
target behavior early:

- `application/python/docs/development/request-execution.md`: controller
  states, phase boundaries, escalation, registration races, checkpoint
  behavior, shutdown behavior, and background exclusions.
- `core/python/docs/events.md`: the `cancellation_mode` field on
  `request_cancelled` and terminal-event semantics.
- `application/python/README.md`: both HTTP cancellation endpoints and their
  observable difference.
- `application/python/docs/terminal.md`: `/cancel` as immediate/hard and
  `/soft-cancel` as stop-after-current-tool.
- `packages/frontend-sdk/docs/development/request-cancellation.md`: backend
  methods, controller behavior, active-request state, and escalation UX; link
  it from `packages/frontend-sdk/docs/development/index.md`.
- `plugins/tool-compat-shared/README.md`: shared foreground shell cancellation
  contract and explicit background handoff boundary.
- Update individual shell package READMEs only where they make a cancellation
  or process-lifecycle claim affected by the implementation; do not duplicate
  the shared engine contract into every vendor README.

Do not edit `docs_site/prepared/` or `docs_site/dist/`. Run documentation-site
preparation/build validation only after maintained sources are updated.

### Task checklist

- [x] Reconcile the plan with the then-current working tree and preserve
  unrelated local changes.
- [x] Split overall stop, provider interruption, and hard-only tool
  interruption in the request cancellation controller.
- [x] Make pre-registration cancellation mode-aware and hard-dominant.
- [x] Route the provider and tool cancellation channels through the correct
  core/application boundaries.
- [x] Preserve finished tool result append, event, and checkpoint behavior
  before soft cancellation terminates the loop.
- [x] Add cancellation mode to cancellation events.
- [x] Add shared foreground shell cancellation and result state.
- [x] Forward hard cancellation through Claude, Gemini, Qwen, Kimi, and Grok
  shell wrappers.
- [x] Add hard cancellation and process-tree termination to the generic Bash
  host and Codex legacy shell.
- [x] Add application, FastAPI, embedded-runtime, and terminal soft-cancel
  operations.
- [x] Extend frontend SDK and chat controller APIs.
- [x] Add mobile and desktop soft-cancel actions while preserving hard-cancel
  escalation.
- [x] Add focused unit, integration, HTTP, transport, SDK, and UI tests.
- [x] Create and update the specification and documentation listed above.
- [x] Run focused package verification, then proportionate adjacent suites.

### Requirement verification

- R1: Existing hard-cancel application tests must continue to prove provider
  interruption, foreground tool interruption, terminal lifecycle events, and
  follow-up request isolation. Existing public endpoint and SDK tests must
  continue using the unchanged hard-cancel route.
- R2: For each shell execution family, run a real foreground subprocess that
  spawns a descendant, issue hard cancellation through the production tool
  boundary, assert prompt request completion, and verify both parent and child
  are gone. Shared-engine wrappers may share engine-level process-tree
  evidence, but each wrapper needs focused proof that it forwards the token.
- R3: An application integration test must soft-cancel a gated finite tool,
  verify the tool is not interrupted, release it, assert its normal result is
  appended and checkpointed, and assert no subsequent queued tool or provider
  phase starts.
- R4: Application concurrency tests must cover early soft cancellation,
  early hard cancellation, soft-to-hard promotion during an active tool, and
  both request-order races with hard mode winning.
- R5: Background integration tests must verify that a successfully handed-off
  background command remains alive after request cancellation and can still be
  stopped through its existing process-specific mechanism.
- R6: A real FastAPI HTTP test must exercise both routes. Frontend SDK tests
  must cross the production REST adapter. Mobile and desktop component/native
  tests must select both actions by stable identifiers and verify the correct
  backend method, including hard escalation after soft acknowledgement. The
  embedded runtime and bridge adapter need route-level forwarding coverage.
- R7: Core/application event tests and frontend reducer tests must verify
  `cancellation_mode` for both modes while confirming existing consumers still
  treat `request_cancelled` as terminal.

### Additional implementation verification

- Run focused Python suites for the application layer, terminal server, shared
  shell engine, Claude Tools, Codex Tools, Gemini Tools, Qwen Tools, Kimi
  Tools, and Grok Tools.
- Run frontend SDK and frontend React package tests, plus focused mobile and
  desktop component/native tests for composer actions.
- Run lint/type checks for all touched Python and TypeScript packages.
- Prepare and build the documentation site from maintained sources; do not
  refresh unrelated generated reference snapshots.
- Hosted provider tests are not required for the cancellation state machine
  when deterministic provider and real subprocess integration tests cross the
  relevant boundaries. Run a selective hosted smoke test only if provider
  adapter changes extend beyond passing the existing cancellation channel.

## Implementation Notes

- The request controller now owns separate overall-stop, provider-interrupt,
  and hard-only tool-interrupt signals. Provider adapter behavior remains
  unchanged because the controller preserves its existing callback interface;
  tools receive the hard-only signal from `ToolLoopRunner`.
- Pre-registration cancellation storage is mode-aware. Hard mode is dominant,
  and soft-to-hard promotion signals an already-running tool immediately.
- The shared async shell engine now reports `cancelled` separately from
  `timed_out` and awaits its scheduled process-tree termination before closing
  the event loop. Claude, Gemini, Qwen, Kimi, and Grok forward that signal.
- The generic Bash host and disabled Codex legacy shell use isolated process
  groups and cancellation callbacks. Active Codex `shell` and
  `shell_command` already had the required behavior and were retained.
- HTTP, embedded runtime, terminal, SDK, mobile, and desktop soft-cancel
  surfaces were added. Frontends keep the hard action enabled after soft
  acknowledgement and suppress duplicate soft requests for the same active
  request.
- The bridge required no product logic change because it forwards arbitrary
  HTTP paths; its raw-transfer test now exercises the soft-cancel route.
- Existing explicit background-command tests emit asyncio subprocess
  transport cleanup warnings after successful runs. The new focused
  background-handoff test passes cleanly; redesigning the older background
  transport lifecycle is outside this task.

## Completion Notes

Implemented hard cancellation across all audited first-party foreground shell
paths and added end-to-end soft request cancellation.

Requirement evidence:

- R1/R4/R7: application cancellation tests cover existing hard behavior,
  pre-registration soft/hard modes, hard dominance, escalation, and
  `cancellation_mode`.
- R2: real subprocess tests cover shared-engine descendant termination,
  generic Bash process-tree termination, active Codex paths, Codex legacy,
  Claude, Gemini, Qwen, Kimi, and Grok forwarding.
- R3: a gated finite-tool application integration test proves soft cancel does
  not interrupt the active tool, persists its normal result and checkpoint,
  and does not start a second queued tool or provider phase.
- R5: focused shared-engine coverage proves a pre-cancelled request does not
  claim an explicit background command after handoff.
- R6: FastAPI `TestClient`, bridge forwarding, frontend SDK/controller tests,
  embedded-runtime compilation, mobile typecheck, and focused mobile/desktop
  component tests cover the public surfaces.

Verification completed:

- Core full suite: 591 passed, 26 deselected, 1 expected failure.
- Application server suite: 51 passed, 11 deselected.
- Focused core cancellation/Bash suite: 30 passed.
- Shared shell engine: 78 passed, 1 skipped.
- Claude Bash: 40 passed.
- Codex shell families: 90 passed.
- Gemini shell: 32 passed.
- Qwen shell: 30 passed.
- Kimi shell: 33 passed.
- Grok shell: 18 passed.
- Frontend SDK: 353 passed.
- Frontend SDK React: 24 passed.
- Mobile and desktop focused component tests: 6 passed.
- Mobile TypeScript typecheck passed.
- Ruff checks passed for the task-owned Python implementation and tests.
- Documentation preparation and MkDocs build passed with existing navigation
  and link warnings.
- `git diff --check` passed.

Blocked or unrelated verification:

- The full application suite reached 425 passed, 1 skipped, and 82 deselected,
  but failed one unrelated Claude system-message test because its temporary
  workspace instruction did not contain the expected task-guidance sentence.
- Desktop TypeScript checking remains blocked by pre-existing URL, declaration
  ordering, optional-string, and theme errors outside the changed cancellation
  lines. Focused desktop Jest tests passed.
- The unrelated deleted
  `mobile/crystal-lattice-control-rn/ios/CrystalLatticePythonRuntime/Resources/reviewer-proxy-ca.pem`
  worktree change was preserved.

## Post-completion follow-up

- Corrected mobile soft-cancel enablement after user testing showed that the
  duplicate-request latch left soft cancellation disabled for the remainder
  of an active request. Mobile soft and hard cancellation now use the same
  enabled-state predicate in both Composer actions and Session actions.
- Removed the mobile request-ID latch and updated frontend cancellation
  documentation. Desktop behavior was not changed by this follow-up.
- Verified with the mobile TypeScript build, the focused
  `SessionChatScreenRangeFallback` component test, and `git diff --check`.