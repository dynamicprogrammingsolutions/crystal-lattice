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

Important note about `acquire_session_lock`:

* `AgentApplication.acquire_session_lock(session_id)` is a **process-local lock** provided by the event store (see `core/python/agent_app/application_future.py`), and the server already acquires/releases it multiple times while a request runs (e.g., around checkpoint saves).
* Therefore, do **not** hold this lock for the full duration of a request. Use it only for short critical sections (session file mutation / consistent reads) and use a separate lock for the “single-flight” bookkeeping.

Add a small in-memory registry in `server.py`:

* `active_request_by_session: Dict[str, str]`
* guarded by a `threading.Lock()`

On `/send`:

1. Validate session exists (as today). Any operations that touch session files should continue to use `with app_instance.acquire_session_lock(session_id):`.
2. Single-flight gating should be done with the dedicated in-memory lock (`active_request_lock`), not with the session lock:
   * if `active_request_by_session[session_id]` exists: return 409 or `{status:"already_running", request_id: existing}`.
   * else generate a `request_id`, store it, proceed.
3. Start the background worker thread **after** releasing any session lock scope.

In `_run_send_request_background`:

* ensure it calls `app_instance.send_request(... request_id=<the one created>)` so the event stream is keyed.
* in a `finally:` block, clear `active_request_by_session[session_id]` if it matches.

Avoid introducing any long-lived `acquire_session_lock` spans inside the worker; keep existing behavior (lock only around checkpoint saves / persistence).

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
