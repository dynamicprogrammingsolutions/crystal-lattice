# FastAPI: single-flight `/send` per session + idempotency keys

Parent Task: `tasks/20260217-bridge-dedup-and-atomic-send/000-main.md`

## Description

Even with bridge-level deduplication, clients can retry (timeouts, reconnects) and race conditions can still trigger multiple `/send` calls for the same session.

This subtask adds **server-side protection**:

* Only one in-flight send per session (“single-flight”).
* Optional idempotency key so repeated calls return the same `request_id` and do not start another run.

## Current behavior (code references)

`application/python/agent_terminal_app/server.py`:

* `POST /sessions/{session_id}/send` starts a background thread unconditionally.
  * Route: around lines ~1320–1370.
* Background worker `_run_send_request_background` loads session and calls `app_instance.send_request(... stream=True)`.
  * Function: around lines ~634–770.

There is no concurrency gating before spawning the thread.

## Proposed changes

### A) Track active send per session (single-flight)

Add a small in-memory registry in `server.py`:

* `active_request_by_session: Dict[str, str]`
* guarded by a `threading.Lock()`

On `/send`:

1. Acquire `app_instance.acquire_session_lock(session_id)` (already available on `AgentApplication`).
2. Check if `active_request_by_session[session_id]` exists:
   * if yes: return `409 Conflict` or `200` with `{ status: "already_running", request_id }`.
3. Otherwise:
   * generate a `request_id` now
   * store it in `active_request_by_session`
   * start background worker thread passing that request_id

In `_run_send_request_background`:

* ensure it calls `app_instance.send_request(... request_id=<the one created>)` so the event stream is keyed.
* in a `finally:` block, clear `active_request_by_session[session_id]` if it matches.

### B) Idempotency key support

Support an `Idempotency-Key` header (or request body field) on `/send`:

* Store: `last_request_by_idempotency_key[(session_id, key)] = request_id` with TTL.
* If same key seen again:
  * return `{ status: "idempotent_replay", request_id }`
  * do not start new worker.

TTL can be simple (timestamp + cleanup on access), or LRU.

### C) Responses

Since current `/send` returns `{}` and expects clients to poll events, extend response:

* Always return `{ request_id, status }`.
* This helps clients correlate.

### D) Tests

Add tests to `application/python/tests/test_agent_terminal_app_server.py`:

1. **Single-flight**
   * Start app, create session.
   * Call `/send` twice quickly.
   * Assert only one background request begins.
   * Verify response of second call indicates already running.

2. **Idempotency replay**
   * Call `/send` with same `Idempotency-Key` twice.
   * Assert both return same `request_id`.
   * Assert only one send worker started.

3. **Idempotency different keys**
   * Two different keys should start two different request_ids, but still should be gated if first is still running.

Implementation note for tests:

* You may need to monkeypatch `_run_send_request_background` or the agent core to avoid long tool loops.
* Alternatively, configure a very fast “echo provider” agent.

## Acceptance criteria

* Concurrent duplicate calls to `/sessions/{session_id}/send` do not trigger multiple request runs.
* Replaying with the same idempotency key returns the original request_id.
* The request_id returned by `/send` matches the one in `request_started` / `final` events.
