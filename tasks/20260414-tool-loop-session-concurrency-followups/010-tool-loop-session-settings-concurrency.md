# Tool Loop Session Settings Concurrency

Investigate and implement safe session persistence during a running tool loop so session settings can be changed concurrently without being overwritten, while conflicting non-settings edits stop the request and preserve a backup.

Parent Task: tasks/20260414-tool-loop-session-concurrency-followups/000-main.md

## Requirements checklist

- [x] Preserve concurrent session settings changes made while a tool loop is running.
- [x] Detect other concurrent session changes and stop the request with an error instead of overwriting them.
- [x] Save a backup of the in-memory tool-loop session on conflict and include that fact in the surfaced error.
- [x] Keep the change focused in shared application-layer code so all applications benefit.
- [x] Add regression tests for merge, conflict, stop, and backup behavior.

## Context

Problem summary:

- The request/tool loop operates on an in-memory `Session` snapshot for the duration of the request.
- Session checkpoints are persisted later by consumers of `session_checkpoint` events.
- The filesystem session store uses blind last-writer-wins replacement, so a later checkpoint can overwrite concurrent settings edits.

Relevant code paths inspected:

- `core/python/agent_app/tool_loop.py`
  - `ToolLoopRunner._run_llm_phase()` emits `session_checkpoint` after each LLM phase.
  - `ToolLoopRunner._apply_tool_calls()` emits `session_checkpoint` after tool results.
  - `ToolLoopRunner.run()` advances `current_session` through the whole request.
- `core/python/agent_app/application_future.py`
  - `AgentApplication.send_request()` prepares the request once, resolves config once, and then delegates to `ToolLoopRunner`.
  - It currently forwards `session_checkpoint` events without reconciling against the persisted session.
- `core/python/agent_app/sessions.py`
  - `FilesystemSessionStore.save()` writes `<session_id>.json.tmp` and then replaces the main file.
  - No optimistic concurrency, no versioning, no backup support today.
- `application/python/agent_terminal_app/server.py`
  - `_run_send_request_background()` persists every `session_checkpoint` and then persists the final session again.
  - Save failures are currently swallowed with logging, which is not suitable for concurrency conflict handling.
- `application/python/agent_terminal_app/terminal_app.py`
  - `TerminalApplication.send_message()` does the same checkpoint persistence flow for terminal-driven requests.
- Session settings updates today are primarily stored in `session.metadata["overrides"]`:
  - `application/python/agent_terminal_app/server.py` in `patch_session_overrides()`
  - `application/python/agent_terminal_app/terminal_app.py` in `update_override()`

Important findings:

- The existing session lock is process-local only:
  - `AgentApplication.acquire_session_lock()` delegates to `InMemoryEventStore.acquire_session_lock()`
  - `InMemoryEventStore.acquire_session_lock()` uses a per-session `threading.Lock`
  - This coordinates threads/app instances sharing the same in-memory event store, but does not protect against cross-process writers or direct file edits.
- Because checkpoint persistence happens after `ToolLoopRunner` emits the event, the tool loop may continue before reconciliation/persistence finishes.
- That means a plain “consumer notices conflict and emits error” approach is not sufficient if we want checkpoint saving to be a real safety barrier before later tool execution.

## Proposed design

High-level direction:

- Keep persistence and reconciliation in the shared application layer, not in terminal/server-specific consumers.
- Keep `ToolLoopRunner` mostly session-in/session-out, but add an optional checkpoint callback so checkpoint handling becomes synchronous and authoritative.
- Treat checkpoint persistence as a barrier: the loop does not continue until the callback succeeds or raises.

Core behavioral rules:

- Allowed concurrent change:
  - `session.metadata["overrides"]` changed externally while the loop was running.
  - In that case, merge the latest stored overrides into the tool-loop checkpoint session and continue.
- Conflicts that should stop the request:
  - Message list changed externally.
  - `agent_id` changed externally.
  - Session plugin selection or other non-override metadata changed externally.
  - Same message count but message contents/metadata changed externally.
- On conflict:
  - Save the in-memory tool-loop session to a backup file.
  - Raise a dedicated exception carrying the backup path and a clear message.
  - Emit an `error` event and stop the request before later phases continue.

Detection strategy:

- Use file state (`mtime_ns` and optionally size) only as a fast path.
- If file state is unchanged since the request baseline, skip reload/reconcile and save normally.
- If file state changed, reload the persisted session and perform targeted semantic comparison.

Targeted comparison strategy:

- Fast checks first:
  - session id mismatch => conflict
  - message count changed from the expected baseline => conflict
  - metadata changed only in `overrides` => merge
  - metadata changed in any other key => conflict
- If message counts are equal but file state changed, compare a lightweight message fingerprint to detect edits without doing a full expensive deep compare on every checkpoint.
  - A reasonable fingerprint is a stable hash of each `Message.to_dict()` or of selected message fields.
- Avoid relying on `mtime` correctness for safety; use it only to avoid unnecessary reloads.

Checkpoint callback/barrier design:

- Add an optional callback to `ToolLoopRunner`, something like:
  - `on_session_checkpoint: Callable[[Session], Session | None] | None = None`
- When absent, existing behavior is preserved.
- When present:
  - `ToolLoopRunner` calls it at each checkpoint candidate before continuing.
  - The callback may return the same session, or a reconciled session with merged settings.
  - The callback may raise a dedicated concurrency exception to stop the loop.
- The emitted `session_checkpoint` event should carry the returned/reconciled session, not the stale pre-save one.
- `ToolLoopRunner` should continue from that returned session so later phases see the merged settings snapshot.

Why this design:

- It keeps the save/reconcile logic in the right layer.
- It keeps the change shared across all apps using `AgentApplication.send_request()`.
- It turns checkpoint persistence into an actual synchronization point, which avoids the loop proceeding into later tools/LLM phases after a checkpoint conflict has already been detected.

## Suggested implementation areas

Likely files to change:

- `core/python/agent_app/tool_loop.py`
  - Add optional checkpoint callback support.
  - Update checkpoint emission code so the callback can transform or reject the checkpoint session.
  - Ensure callback-raised errors stop the loop cleanly and surface as `error` events.
- `core/python/agent_app/application_future.py`
  - Add shared reconcile/persist helper for checkpoint sessions.
  - Pass a closure/lambda into `ToolLoopRunner` from `send_request()`.
  - Refresh the effective config/session used for subsequent phases after a checkpoint merge so changed settings can affect later phases.
- `core/python/agent_app/sessions.py`
  - Add file-state helper(s), for example current path stats and a backup writer.
  - Consider adding a helper that loads the latest stored session and returns basic file-state info together.
- `application/python/agent_terminal_app/server.py`
  - Simplify/remove duplicate checkpoint-save logic as much as possible once shared application-layer handling owns reconciliation.
  - Ensure final save does not blindly overwrite after a conflict path.
- `application/python/agent_terminal_app/terminal_app.py`
  - Same as server path: preserve shared behavior, avoid swallowing concurrency errors.

## Execution plan

Added during planning/completion of this task file.

1. Add a dedicated application-layer concurrency error and file-state helpers.
   - Introduce a small exception type for checkpoint conflicts that includes a human-readable detail and backup path.
   - Extend `FilesystemSessionStore` with focused helpers for reading current file state and writing a backup snapshot.

2. Add shared reconciliation logic in `AgentApplication`.
   - Implement a helper that takes:
     - the request baseline session
     - the current checkpoint session from the tool loop
     - baseline file-state information from request start
     - request id
   - The helper should:
     - fast-path when the session file state is unchanged
     - reload the latest persisted session when the file changed
     - allow only `metadata["overrides"]` drift and merge it
     - treat all other drift as conflict
     - write a backup and raise on conflict

3. Turn checkpoint handling into a synchronous barrier in `ToolLoopRunner`.
   - Add an optional `on_session_checkpoint` callback argument.
   - Invoke it for each checkpoint candidate before yielding the checkpoint event.
   - Use the callback return value as the new `current_session`.
   - If the callback raises, emit an `error` event and stop the loop immediately.
   - Preserve current behavior when no callback is provided so existing tests/callers stay compatible where possible.

4. Wire the callback from `AgentApplication.send_request()`.
   - Capture request-start baseline session and baseline file-state.
   - Pass a closure into `ToolLoopRunner` that calls the new reconcile/persist helper.
   - After a successful merged checkpoint, ensure later phases use the reconciled session and refreshed effective config so changed settings apply to subsequent phases.

5. Trim duplicate outer save behavior in terminal/server consumers.
   - Keep them consuming the shared request stream, but avoid blind checkpoint/final overwrite behavior that would bypass the new shared reconciliation semantics.
   - Preserve event publication/checkpoint cursor behavior.

6. Add regression tests in shared application-layer test suites.
   - No external change => checkpoint succeeds normally.
   - Override-only external change => override is preserved and merged into later saved session.
   - External message append/edit => conflict error, backup saved, request stops.
   - External non-override metadata change => conflict error.
   - Callback optionality/backward compatibility for `ToolLoopRunner`.
   - Request-error lifecycle still runs on the new conflict path.

7. Add end-to-end terminal/server tests.
   - Running request plus concurrent override update preserves the override.
   - Running request plus concurrent message or other metadata change emits an error and does not overwrite the external change.
   - Error detail includes backup information.

## Test plan details

Planned tests to add:

- `core/python/tests`
  - Focused unit tests for reconcile/classification logic.
  - `ToolLoopRunner` checkpoint callback tests:
    - callback omitted => existing behavior
    - callback returns updated session => runner continues from updated session
    - callback raises => runner emits error and stops before later phases
  - `AgentApplication.send_request()` flow tests:
    - override-only concurrent change is merged and preserved
    - conflict stops request and runs `request_error` lifecycle
    - backup file is created and path is surfaced
- `application/python/tests`
  - HTTP background send regression:
    - concurrent override edit survives a later checkpoint
    - concurrent message edit or metadata conflict stops request with visible error
  - Terminal send regression:
    - same behavior as HTTP path through shared application logic

Test notes:

- Correctness tests should assert semantic behavior, not depend on `mtime` alone.
- File-state fast-path tests should verify that unchanged file state avoids unnecessary reconcile work, but should not be the only safety coverage.
- The exact target test files may depend on where the shared helper lands; likely candidates include:
  - `core/python/tests/test_application_layer_tools.py`
  - `core/python/tests/test_application_session_lifecycles.py`
  - a new focused application-layer concurrency test file if that reads more cleanly
  - `application/python/tests/test_agent_terminal_app_server.py`
  - `application/python/tests/test_terminal_application.py`

## Open decisions

- Scope of “settings” for phase 1:
  - Recommended: only `session.metadata["overrides"]`
  - Recommended conflict: `plugins`, `agent_id`, or any other metadata drift
- Backup naming:
  - Recommend deterministic names near the session file such as:
    - `<session_id>.tool-loop-conflict.<request_id>.<timestamp>.json`
- Error surfacing:
  - Recommend a dedicated error detail mentioning that a backup was saved and where

## Completion Notes

Added during task-file creation after investigation and planning.

- Confirmed that the root overwrite problem comes from blind session-file replacement combined with long-lived in-memory tool-loop sessions.
- Ruled out relying on the existing session lock for correctness because it is process-local only.
- Refined the initial proposal away from purely consumer-side post-hoc detection toward a checkpoint callback/barrier so the tool loop waits for save/reconciliation before continuing.
- Updated during implementation:
  - Added filesystem session file-state helpers and backup writing support in `core/python/agent_app/sessions.py`.
  - Added synchronous checkpoint and phase-boundary callbacks in `core/python/agent_app/tool_loop.py`.
  - Moved checkpoint reconciliation/persistence into shared `AgentApplication.send_request()` flow so all applications using the shared request path benefit automatically.
  - Added pre-phase session sync so override-only external changes can affect the next loop phase instead of waiting until a later save.
  - Removed the old blind checkpoint/final persistence from terminal/server request consumers; they now treat checkpoint events as already-persisted snapshots and only keep local/session event bookkeeping.
  - Added focused regression coverage in `core/python/tests/test_application_tool_loop_session_concurrency.py` for:
    - concurrent override merge that changes the next phase config
    - concurrent non-settings edit that stops the request and saves a backup
  - Verified with:
    - `pytest core/python/tests/test_application_tool_loop_session_concurrency.py -q`
    - `pytest core/python/tests/test_application_layer_tools.py -q -vv`
    - `pytest core/python/tests/test_application_session_lifecycles.py::test_request_prepare_and_complete_lifecycles_update_checkpoint_session -q -vv`
    - `pytest application/python/tests/test_terminal_application.py -q`
  - Current caveat:
    - when a concurrency conflict is detected, the request stops and preserves the backup as intended, but request-error lifecycle metadata is not forced back into the conflicted session file if that would itself overwrite the external edit.

## Follow-up improvement

Added after implementation to capture the next scoped enhancement for this subtask.

- Catch stale/conflicting session state earlier, before the request fully starts:
  - On request start, compare the caller-provided session snapshot against the latest persisted session.
  - If unchanged, proceed normally.
  - If only `session.metadata["overrides"]` changed, adopt the latest overrides and proceed.
  - If messages or other metadata changed, reject the request before the first LLM/tool phase begins.
- This should remain a focused enhancement to the current shared application-layer request path, separate from the broader cross-process conflict-handling design tracked in `tasks/20260414-tool-loop-session-concurrency-followups/020-request-conflict-handling-draft.md`.

## Task checklist

- [x] Add request-start preflight validation in the shared application layer.
- [x] Reuse current override-only merge vs. non-override conflict classification before the first phase.
- [x] Add regression tests for stale terminal-held request start, fresh concurrent server request behavior, and the unresolved append-and-send race.
- [x] Document the unresolved cross-process append race as a known failing regression to drive later work.

## Follow-up execution plan

Added during follow-up planning/completion after the initial implementation.

1. Add a shared preflight helper in `AgentApplication.send_request()`.
   - Compare the caller-provided session snapshot with the latest persisted session before `request_prepare` and before any provider/tool work starts.
   - If unchanged, proceed with the provided session.
   - If only `session.metadata["overrides"]` changed, adopt the latest stored overrides and continue from the merged session.
   - If messages changed or other metadata changed, raise the existing shared concurrency error immediately.

2. Run preflight before the first request phase and update the checkpoint baseline.
   - Wire the preflight helper into the top of `send_request()`.
   - When override-only drift is adopted, refresh the in-memory request baseline so the first phase and later checkpoint sync use the updated persisted state instead of re-detecting the same change.
   - On preflight conflict, emit an `error` event and stop before any new LLM/tool output is generated.

3. Keep checkpoint-time reconciliation as the fallback safety net.
   - This follow-up only catches stale/conflicting starts earlier.
   - Changes that happen after the request begins must still be handled by the existing phase-boundary sync and checkpoint barrier logic.

4. Add flow-focused regression tests that match real entry paths.
   - Core/application-level:
     - stale terminal-held session start after the session advanced elsewhere => preflight `error`, no new request output, stored session unchanged
     - override-only drift before request start => request starts successfully and uses the adopted override immediately
   - Server-level:
     - request A running while request B starts through the server path with a fresh reload => request B may still start under the current design, but it must surface an `error` event later rather than silently overwriting state
     - cross-process-style `send_message` append race => keep a currently failing regression that documents the real unsolved behavior: one side may notice the conflict first and stop while the other side may not notice at all

5. Keep assertions aligned with the current solution boundary.
   - Assert live `error` event visibility, because that is what mobile/server clients rely on today.
   - Do not yet assert durable request-error recovery on reopen; that belongs to `tasks/20260414-tool-loop-session-concurrency-followups/015-durable-request-error-log-and-lightweight-client-cache.md`.

## Follow-up completion notes

Added during follow-up planning before implementation of the early preflight enhancement.

- Refined the test plan away from purely synthetic “message was externally edited” cases toward real request-entry flows.
- Clarified the important distinction between:
  - terminal-held stale sessions, which should fail early once preflight exists
  - server-request flows that reload fresh persisted state, which may still only fail later until broader active-request coordination is added
- Captured the cross-process `send_message` append race as an intentionally unresolved regression that should remain visible until a later fix propagates the conflict to both competing requests.
- Updated during follow-up implementation:
  - Added shared request-start preflight validation in `core/python/agent_app/application_future.py`.
  - Refactored the shared concurrency logic down to one store-aware reconcile entry point plus one strict compatibility merge helper in `core/python/agent_app/application_future.py`.
  - Tightened preflight so request start now requires exact message equality with the persisted session; direct tests that were relying on unsaved in-memory appends before `send_request(...)` were updated to persist first, matching the intended terminal/server flow.
  - Added focused regressions in `core/python/tests/test_application_tool_loop_session_concurrency.py` for:
    - override-only preflight adoption before the first phase
    - stale terminal-held request start failing before the first phase
    - fresh concurrent request start from the same persisted baseline failing later with an `error` event
    - mergeable non-protected metadata such as pinned state being preserved before request start and during the tool loop
    - the unresolved cross-process append-and-send race as an intentionally failing regression
  - Verified passing coverage with:
    - `pytest core/python/tests/test_application_tool_loop_session_concurrency.py -k 'not cross_process' -q -vv`
    - `pytest core/python/tests/test_application_layer_tools.py -q -vv`
    - `pytest core/python/tests/test_application_layer_basic.py -q -vv`
    - `pytest core/python/tests/test_tool_preparation.py -q -vv`
    - `pytest core/python/tests/test_application_layer_streaming.py -q -vv`
    - `pytest application/python/tests/test_terminal_application.py -q`
  - Verified the known failing regression with:
    - `pytest core/python/tests/test_application_tool_loop_session_concurrency.py::test_cross_process_append_then_send_should_eventually_stop_both_requests -q -vv`