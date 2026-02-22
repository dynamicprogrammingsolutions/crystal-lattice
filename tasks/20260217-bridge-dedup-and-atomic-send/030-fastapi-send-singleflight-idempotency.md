# FastAPI: single-flight `/send` per session + idempotency keys

Parent Task: `tasks/20260217-bridge-dedup-and-atomic-send/000-main.md`

## Description

Even with bridge-level deduplication, clients can retry (timeouts, reconnects) and race conditions can still trigger multiple `/send` calls for the same session.

This subtask adds **server-side protection**:

* Only one in-flight send per session (“single-flight”).
* Idempotency keys so client retries can safely replay results without duplicating side effects.

These are intentionally **separate concepts**:

- Single-flight is **session-scoped** and blocks *all* concurrent sends for the session.
- Idempotency is **key-scoped** and replays the same result only when the client repeats the same key.

## Current behavior (code references)

`application/python/agent_terminal_app/server.py`:

* `POST /sessions/{session_id}/send` starts a background thread unconditionally.
  * Route: around lines ~1320–1370.
* Background worker `_run_send_request_background` loads session and calls `app_instance.send_request(... stream=True)`.
  * Function: around lines ~634–770.

There is no concurrency gating before spawning the thread.

## Plan

### 1) Single-flight: per-session send gating

- Add a process-local registry in `application/python/agent_terminal_app/server.py`:
  - `active_send_request_by_session: Dict[str, str]` guarded by a dedicated `threading.Lock()`.
- In `POST /sessions/{session_id}/send`:
  - Validate session exists and agent config is resolvable (keep current 404/400 semantics).
  - Atomically reserve a request id for the session:
    - If another send is already active for this session, do not spawn a worker; return the existing request id.
    - Otherwise generate a request id and record it as active.
  - Spawn the background worker after leaving any session-lock spans.
- In `_run_send_request_background`:
  - Pass the reserved request id into `AgentApplication.send_request(..., request_id=...)`.
  - Clear the active entry in a `finally:` block (only if the stored value still matches).

### 2) Idempotency: reusable helper for mutating endpoints

- Support `Idempotency-Key` header.
- Add a small in-memory idempotency cache keyed by `(scope, Idempotency-Key)` with TTL.
  - Include a payload fingerprint; if the same key is reused with a different payload for the same scope, return `409`.
- Apply this guard broadly to **mutating endpoints** (POST/PUT/PATCH/DELETE).

### 3) Response shape

- Extend `/send` response to include `{ status, request_id }`.
- Ensure `request_id` matches `request_started` / `final` / `request_completed` events.

## Proposed changes

### A) Single-flight: track active send per session

Single-flight is **session-scoped** and applies only to `/send` (and the upcoming
atomic append+send endpoint): while a request is running for a session, no other
send may start for that session, regardless of idempotency key.

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

### B) Idempotency: client-supplied keys for mutating endpoints

Idempotency is **key-scoped** and should be available broadly across mutating
endpoints (POST/PUT/PATCH/DELETE), not just `/send`.

Support an `Idempotency-Key` header (or request body field) on `/send`:

* Store: `idempotency_cache[(scope, key)] = response` with TTL.
* If the same key is seen again for the same scope:
  * return the cached response
  * do not perform side effects again.
* If the same key is reused with a different payload for the same scope:
  * return `409` (conflict)

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

4. **Other mutating endpoints**
   * Add at least one regression test proving broad idempotency for a non-send
     mutating endpoint (e.g. `POST /sessions`).

Implementation note for tests:

* You may need to monkeypatch `_run_send_request_background` or the agent core to avoid long tool loops.
* Alternatively, configure a very fast “echo provider” agent.

## Acceptance criteria

* Concurrent duplicate calls to `/sessions/{session_id}/send` do not trigger multiple request runs.
* Replaying with the same idempotency key returns the original request_id.
* The request_id returned by `/send` matches the one in `request_started` / `final` events.

## Implementation notes (done)

### Single-flight (`/send` only)

- Implemented process-local single-flight registry:
  - `application/python/agent_terminal_app/server.py:56`
- `/send` now reserves or reuses a per-session `request_id` and returns it:
  - `application/python/agent_terminal_app/server.py:1548`
- Background worker now accepts `request_id` and passes it into `AgentApplication.send_request` so events line up:
  - `application/python/agent_terminal_app/server.py:807`

### Idempotency (broad)

- Implemented reusable idempotency helper with TTL, max size, and payload fingerprinting:
  - `application/python/agent_terminal_app/server.py:95`
- Applied `Idempotency-Key` handling to all non-GET endpoints in `server.py`.
- Implementation detail for tests: route functions are often called directly, so default FastAPI `Header(...)` parameters can be `fastapi.params.Header` objects; idempotency key parsing explicitly ignores non-strings:
  - `application/python/agent_terminal_app/server.py:102`

### Tests / compatibility adjustments

- Updated `/send` response assertions in:
  - `application/python/tests/test_agent_terminal_app_server.py`
  - `application/python/tests/test_agent_terminal_app_server_openrouter_multipart_http_integration.py`
- Added regression tests for:
  - `/send` single-flight
  - `/send` idempotency replay
  - `POST /sessions` idempotency replay
  - `application/python/tests/test_agent_terminal_app_server.py`
- Updated the OpenRouter "puzzle" integration test to wait for the background request to finish before asserting on file changes:
  - `application/python/tests/test_agent_terminal_app_openrouter_puzzle.py`

### Limitations

- Both single-flight and idempotency caches are **process-local** and in-memory.
  - If the server is run with multiple worker processes, these protections do not coordinate across processes.
