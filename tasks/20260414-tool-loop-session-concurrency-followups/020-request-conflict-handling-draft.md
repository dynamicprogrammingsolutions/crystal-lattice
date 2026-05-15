# Request Conflict Handling Draft

Draft the broader issue description and candidate solution for request conflicts that are not fully solved by checkpoint-time reconciliation alone, especially across processes or from stale preloaded sessions.

Parent Task: tasks/20260414-tool-loop-session-concurrency-followups/000-main.md
Depends On: tasks/20260414-tool-loop-session-concurrency-followups/010-tool-loop-session-settings-concurrency.md

## Requirements checklist

- [ ] Document the remaining request-conflict scenarios after checkpoint-time reconciliation.
- [ ] Capture a draft proposed solution for earlier detection and durable conflict/error handling.
- [ ] Record how terminal and mobile surface request errors today and where durable status is missing.
- [ ] Keep this task explicitly draft-level so the proposal can evolve before implementation.

## Issue description

The implemented checkpoint-time reconciliation solves the original overwrite problem for concurrent session settings changes and stops many unsafe concurrent edits once a request reaches a checkpoint. However, two important scenarios remain:

1. Concurrent request start from different processes.
   - Example: `server1` starts a request for a session, and `server2` starts another request for the same session at nearly the same time.
   - Because the current active-request guard is in-memory and process-local, both requests may start.
   - One request may later lose on checkpoint persistence, but the other request may never know a conflict happened.

2. Request start from a stale preloaded session snapshot.
   - Example: `server1` completes a request and updates the session file, while `terminal1` still holds an older in-memory session snapshot and then starts a new request.
   - The stale client may only detect the problem later.
   - When the request is stopped due to conflict, we currently avoid writing request-error lifecycle metadata back into the session file if that would overwrite the newer legitimate session state.

Why the remaining issue matters:

- Live `error` events are not enough on their own.
- Terminal and mobile can surface live request errors, but those are event-stream driven and not durable session state.
- A client that reconnects later, missed the event stream, or opened the session after the failure may not have a durable record of the last conflict/error outcome.

## Current error surfacing

Terminal:

- Terminal renders `error` events directly in `application/python/agent_terminal_app/event_rendering.py`.
- The polling loop in `application/python/agent_terminal_app/terminal.py` updates active request state from live events and shows errors while attached.
- There is no durable session-file-backed conflict marker shown on session reload today.

Mobile:

- Mobile chat UI reads `chatState.requestError` and shows it in `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`.
- This covers live event-driven request failures while the controller is attached and receiving updates.
- There is no durable per-session request conflict/error record included in the session payload for later reloads.

Shared implication:

- Event-based error visibility exists.
- Durable request-conflict visibility across reconnects, restarts, or stale clients is still missing.

## Draft proposed solution

This is a draft proposal, not a final solution.

Recommended direction:

1. Add request preflight validation in the shared application layer.
   - Before the request fully starts, compare the caller-provided session snapshot with the latest persisted session.
   - If unchanged, proceed.
   - If only `metadata["overrides"]` changed, adopt the latest overrides and proceed.
   - If messages or other metadata changed, reject the request before any new provider/tool work starts.

2. Add a cross-process session request lease.
   - Store a small sidecar file per session to represent the active request.
   - Acquire it atomically on request start.
   - If another fresh lease exists, reject the new request immediately.
   - Release it on request completion, cancellation, or fatal failure.
   - Use heartbeat/expiry so dead processes do not block the session forever.

3. Add durable request-status sidecar state.
   - Store latest request outcome outside the main session file.
   - This preserves the legitimate winning session state while still recording:
     - `running`
     - `completed`
     - `cancelled`
     - `error`
     - `conflict`
     - `rejected-before-start`
   - Include fields such as:
     - `request_id`
     - `detail`
     - `backup_path`
     - `owner`
     - timestamps

4. Expose latest request status to clients.
   - Either include a small `latest_request_status` payload in session load responses, or expose a dedicated helper/endpoint.
   - Terminal and mobile can then show the last request conflict/error even if the live event stream was missed.

## Notes and constraints

- The sidecar approach is recommended because writing conflict/error metadata into the main session file can itself overwrite the newer legitimate session state.
- Checkpoint-time reconciliation should remain as the fallback safety net even if request preflight and leases are added.
- The exact lease file format, expiry semantics, and API shape are still open for refinement.
- Desktop is not yet complete in this area, so terminal and mobile should remain the main UX references for now.

## Open questions

- Should the durable request status keep only the latest request outcome or a bounded history?
- Should request leases live in `FilesystemSessionStore` or a new small helper owned by `agent_app`?
- Should a request rejected by stale-session preflight use `conflict`, `rejected`, or a more specific status code?
- How should terminal/mobile clear or acknowledge an old request conflict once the user has seen it?