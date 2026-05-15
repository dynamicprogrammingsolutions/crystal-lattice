# Snapshot Cursor Alignment Race Tests

Add deterministic regression coverage for snapshot/cursor alignment during in-flight requests, especially the bridge-sensitive case where delayed polling or reloads can observe a session snapshot and its checkpoint cursor at mismatched boundaries.

## Requirements checklist

- [x] Add a server/API regression that samples `/sessions/{id}/messages` during an in-flight request and validates snapshot/cursor alignment against `/events` across a delay matrix.
- [x] Add frontend SDK integration coverage that combines delayed persistence with transport latency and verifies controllers do not become permanently dirty or loop while reopening/reloading.
- [x] Keep the assertions focused on the public contract: snapshot history must align to the returned checkpoint cursor.

Parent Task: `tasks/20260408-connection-recovery/000-main.md`

Depends On: `tasks/20260408-connection-recovery/020-mobile-resume-lifecycle-and-chat-recovery.md`

## Problem framing

- The suspected bug is not "later events exist after the returned cursor"; that is normal.
- The actual contract break is:
  - `/sessions/{id}/messages` returns a snapshot whose messages are not aligned to the same stable checkpoint as `cursor_event_id`.
  - If the snapshot already contains messages whose corresponding `message_appended` / `final` / `tool_results` event is still *after* that cursor, replaying events from the cursor can mark the frontend dirty.
  - Likewise, the snapshot must not omit messages whose history-mutating event is already *before* that cursor.
- Bridge latency likely amplifies the race by stretching the time between reload, polling restart, and event arrival, but the root invariant is backend snapshot/cursor alignment.

## Agreed implementation plan

### 1. Deterministic server/API regression

- Use a delayed session-store wrapper around `FilesystemSessionStore` so persistence takes an artificial amount of time (for example `100ms`).
- Use a deterministic test provider that keeps a request active long enough to sample snapshots while the request is still evolving.
- During the in-flight request, collect snapshots from `/sessions/{id}/messages`.
- For each sampled snapshot with non-null `cursor_event_id`, query `/events?session_id=...&since_id=<cursor>` at a delay matrix such as:
  - `0ms`
  - `100ms`
  - `500ms`
- Assert the public alignment invariant:
  - let `next_index = last_snapshot_index + 1`
  - the first history-mutating event after the cursor, if any, must begin exactly at `next_index`
  - `message_appended.index === next_index`
  - `final.start_index === next_index`
  - `tool_results.start_index === next_index`
- Fail if any such event starts before `next_index`, because that proves the snapshot already contains messages that are still after the advertised cursor.

### 2. Frontend SDK integration matrix

- Extend the real backend harness so the integration server can start with delayed session-store behavior.
- Add transport wrappers with per-endpoint latency for:
  - `/sessions/{id}/messages`
  - `/events`
- Run a small timing matrix, for example:
  - no delay
  - messages `50ms`, events `0ms`
  - messages `0ms`, events `50ms`
  - messages `50ms`, events `50ms`
- Spin up multiple `ChatController` instances against the same session, reopening/reloading at different offsets during the same in-flight request.
- Assert that each controller eventually settles cleanly:
  - no permanent `dirty`
  - no reload loop
  - no stuck `loading`
  - indices remain monotonic and unique
  - state settles after request completion

### 3. Fix only after the regressions exist

- Write the regressions first.
- Then adjust implementation so `/messages` snapshots and their returned cursor align to the same stable checkpoint boundary.
- Re-run nearby dirty/cursor/reload/restart tests afterward.

## Execution plan

Added during completion.

1. Add a delayed session-store helper usable from both direct Python server tests and the TS integration backend runner.
2. Implement the server/API alignment-matrix regression using only public route/function results.
3. Implement the frontend SDK integration matrix with per-endpoint transport delays and multiple controllers.
4. Run the new regressions first to confirm whether the alignment bug reproduces deterministically.
5. If the regressions fail, implement the smallest fix that restores snapshot/cursor alignment and rerun the broader affected suites.

## Completion Notes

Added during completion.

- Added a delayed-session-store server regression in `application/python/tests/test_agent_terminal_app_server.py` that samples `/sessions/{id}/messages` during an in-flight request and queries `/events` against each sampled cursor at a delay matrix of `0ms`, `100ms`, and `500ms`.
- Strengthened the reproducer to use a real persisted tool-loop session:
  - raw `Session` / `Message` seeding preserves assistant `metadata.tool_calls`
  - this yields real `tool_calls`, `tool_results`, and later assistant `final` phases during the request
- Added a backend test-control endpoint in `application/python/agent_terminal_app/server.py` that injects a persisted pending tool-call assistant message for integration tests.
- Added a frontend SDK tool-loop timing matrix in `packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts` that:
  - starts the real backend with delayed checkpoint publication
  - seeds a persisted pending tool-call session through the test-control endpoint
  - applies independent response latency to `/messages` and `/events`
  - spins up multiple `ChatController` instances reopening/reloading the same session at different offsets
  - asserts that controllers settle cleanly without permanent dirty state or stuck loading
- Extended the TS integration backend runner and harness to support delayed session persistence and delayed checkpoint publication:
  - `scripts/run_backend_server_for_ts_integration_tests.py`
  - `packages/frontend-sdk/src/integration/harness.ts`
- Implemented the alignment fix:
  - `AgentApplication.send_request` now records checkpoint events under the same application-layer session lock used for checkpoint persistence in `core/python/agent_app/application_future.py`
  - the final post-completion `request_id=None` checkpoint now comes from `AgentApplication.send_request`, so terminal- and HTTP-started requests share the same snapshot semantics
  - the FastAPI background worker in `application/python/agent_terminal_app/server.py` no longer uses `session_checkpoint` events to publish persistence checkpoints
  - `TerminalApplication` also no longer publishes checkpoints when it observes internal `session_checkpoint` events
  - legacy `session_checkpoint` events remain available as the simple progress API used by tests and examples
- Current status:
  - the tool-loop timing regressions are green with the new alignment fix in place
  - this covers the bridge-sensitive class of bug where a delayed reopen/reload can observe snapshot/cursor drift during checkpoint publication
- Verification:
  - `pytest application/python/tests/test_agent_terminal_app_server.py -q -k "messages_snapshots_stay_aligned_with_cursor_across_delayed_events_matrix"`: passed
  - `pytest application/python/tests/test_agent_terminal_app_server.py -q -k "tool_loop_snapshots_can_expose_history_ahead_of_cursor_when_checkpoint_lags"`: passed
  - `pytest application/python/tests/test_agent_terminal_app_server.py -vv -k "checkpoint_cursor_after_final_event or checkpoint_cursor_after_message_appended or list_session_messages_includes_cursor_event_id_after_request or list_session_messages_exposes_active_request_id_during_and_after_request" --maxfail=1`: passed
  - `pytest core/python/tests/test_application_layer_tools.py -q`: passed
  - `RUN_BACKEND_INTEGRATION=1 npx vitest run src/integration/__tests__/backend.integration.test.ts -t "O: tool-loop reopen matrix stays aligned across delayed checkpoint publication"`: passed
  - `RUN_BACKEND_INTEGRATION=1 npx vitest run src/integration/__tests__/backend.integration.test.ts`: passed
  - `npm test` in `packages/frontend-sdk`: passed
  - `pytest application/python/tests/test_terminal_application.py -q -k "send_request"`: passed
  - `pytest application/python/tests/test_terminal_application.py -q -k "terminal_started_request_clears_active_request_id_for_http_snapshots"`: passed
  - `pytest core/python/tests/test_application_layer_streaming.py -q`: passed