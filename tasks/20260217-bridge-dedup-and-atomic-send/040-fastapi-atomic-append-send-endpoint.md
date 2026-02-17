# FastAPI: atomic append+send endpoint

Parent Task: `tasks/20260217-bridge-dedup-and-atomic-send/000-main.md`

Depends On:
* `tasks/20260217-bridge-dedup-and-atomic-send/030-fastapi-send-singleflight-idempotency.md`

## Description

The current frontend workflow is two HTTP calls:

1) `POST /sessions/{id}/messages` (append)
2) `POST /sessions/{id}/send`

This introduces a race/retry window where duplicates can occur (especially under bridge reconnects / client retry logic).

Add a single endpoint that performs both operations **atomically under the same session lock**.

## Proposed endpoint

Suggested API:

* `POST /sessions/{session_id}/turns` (or `/send_message`)
* Request body:
  ```json
  {
    "message": { "role": "user", "content": "...", "multipartContent": [], "metadata": {} },
    "config_overrides": {},
    "idempotency_key": "..." // optional if not using header
  }
  ```

Response:

* `{ status, request_id, session_id }`

## Implementation details

1. Acquire `app_instance.acquire_session_lock(session_id)` **only for the mutation portion**.
   * Reminder: `acquire_session_lock` is used intermittently while a request runs; do not hold it while running the full send.
2. Validate session exists.
3. Check single-flight state (from Subtask 030) and decide behavior if active.
4. Append message (reuse existing append route logic) and persist it.
5. Release the session lock.
6. Trigger send by starting the background worker thread (Subtask 030), passing the chosen `request_id`.

Important: define semantics if there is already an active send:

* Option A (strict): reject with 409 and do not append.
* Option B (queue-like): append but return "already_running" and do not start a second request.

Prefer **Option A** for correctness and to avoid multiple user turns being appended without being processed.

If Option A is used, the active-send check must happen *inside* the session-lock span so that “check + append” is atomic from the perspective of other session mutations.

## Tests

Add tests in `application/python/tests/test_agent_terminal_app_server.py`:

1. **Atomicity**
   * Call new endpoint once; ensure message appended and request started.

2. **Reject when active**
   * Start a send (or simulate active_request marker) then call endpoint.
   * Ensure it returns 409 and message was not appended.

3. **Idempotency**
   * Call endpoint twice with same `Idempotency-Key`.
   * Ensure only one message is appended and only one send started.

## Acceptance criteria

* There is a single endpoint that appends a message and triggers send under one lock.
* Duplicate/retry with idempotency key does not create duplicated messages.
* If a send is already active, endpoint behavior is well-defined and tested.
