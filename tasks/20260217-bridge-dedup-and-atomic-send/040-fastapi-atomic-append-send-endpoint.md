# FastAPI: atomic append+send endpoint (`send_message`)

Parent Task: `tasks/20260217-bridge-dedup-and-atomic-send/000-main.md`

Depends On:
* `tasks/20260217-bridge-dedup-and-atomic-send/030-fastapi-send-singleflight-idempotency.md`

## Description

The current frontend workflow is two HTTP calls:

1) `POST /sessions/{id}/messages` (append)
2) `POST /sessions/{id}/send`

This introduces a race/retry window where duplicates can occur (especially under bridge reconnects / client retry logic).

Add a single endpoint that performs both operations **atomically under the same session lock**.

This endpoint must reuse the concepts introduced in Subtask 030:

- **Single-flight** (session-scoped): do not allow a new send while another is running.
- **Idempotency** (key-scoped): allow safe retries without double-append.

## Proposed endpoint

Suggested API:

* `POST /sessions/{session_id}/send_message`
* Request body:
  ```json
  {
    "message": { "role": "user", "content": "...", "multipartContent": [], "metadata": {} },
    "config_overrides": {},
    "idempotency_key": "..." // optional; prefer Idempotency-Key header
  }
  ```

Response:

* `{ status, request_id, session_id }`

Notes:

- Use `Idempotency-Key` header for retries.
- `request_id` must match the event stream (`request_started` / `final` / `request_completed`).

## Implementation details

1. Acquire `app_instance.acquire_session_lock(session_id)` **only for the mutation portion**.
   * Reminder: `acquire_session_lock` is used intermittently while a request runs; do not hold it while running the full send.

2. Idempotency replay:
   - Use the Subtask 030 helper (`Idempotency-Key`) to replay and return the cached response.
   - For correctness under concurrency, check idempotency **inside** the session-lock span as well (double-check pattern).

3. Validate session exists.

4. Single-flight gating:
   - If there is already an active send for the session, do **not** append.
   - Return `409` (conflict) and include the active request id in the response body.

5. Create a `request_id` and reserve it as active send for this session (same mechanism as `/send`).

6. Append message (reuse existing append route logic) and persist it.

7. Store idempotency response before releasing the session lock so retries can't double-append.

8. Release the session lock.

9. Trigger send by starting the background worker thread (Subtask 030), passing the reserved `request_id`.

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

4. **Idempotency key reused with different payload**
   * Call endpoint twice with same `Idempotency-Key` but different message content.
   * Ensure the second returns 409.

## Acceptance criteria

* There is a single endpoint that appends a message and triggers send under one lock.
* Duplicate/retry with idempotency key does not create duplicated messages.
* If a send is already active, endpoint behavior is well-defined and tested.

## Notes (updated after Subtask 030 implementation)

- Subtask 030 already adds broad idempotency support for mutating endpoints via `Idempotency-Key`.
  - The atomic endpoint should reuse the same helper and scope conventions.
- Subtask 030 changes `/send` response to `{status, request_id}`.
  - The atomic endpoint should match this style.

## Implementation notes (to fill in after completion)

- Implemented `POST /sessions/{session_id}/send_message` in `application/python/agent_terminal_app/server.py`.
- The endpoint:
  - Validates the message payload using shared message validation.
  - Uses `Idempotency-Key` (header) with an optional `idempotency_key` body fallback.
  - Performs idempotency replay + response caching while holding the session lock so retries cannot double-append.
  - Reserves the per-session single-flight `request_id` before appending and returns `409` if a send is already active.
  - Appends the message + publishes `message_appended`, then starts the background send worker after releasing the session lock.
- Refactoring note: the append+publish logic and the "session is runnable" validation are shared helpers used by both legacy endpoints and `send_message`.
- Added tests in `application/python/tests/test_agent_terminal_app_server.py` covering:
  - Atomic append+send starts exactly one background request.
  - Active-send conflict returns `409` and does not append.
  - Idempotency replay avoids double-append and reuses the same `request_id`.
  - Reusing the same idempotency key with a different payload returns `409`.
