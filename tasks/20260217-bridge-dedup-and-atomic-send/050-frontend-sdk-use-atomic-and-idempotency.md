# Frontend SDK: use atomic append+send + idempotency keys

Parent Task: `tasks/20260217-bridge-dedup-and-atomic-send/000-main.md`

Depends On:
* `tasks/20260217-bridge-dedup-and-atomic-send/040-fastapi-atomic-append-send-endpoint.md`

## Description

Update the frontend SDK (and by extension the mobile app) so that a user “Send” action becomes one atomic HTTP call and includes an idempotency key.

This reduces duplicate requests under network retries and makes bridge transport safer.

Notes (updated after Subtask 030 scope change):

- Subtask 030 adds `Idempotency-Key` support broadly across mutating endpoints, not just `/send`.
- `/sessions/{id}/send` now returns `{status, request_id}`.
- The frontend should treat idempotency as a general-purpose retry mechanism and use it consistently for mutating requests where retries are possible.

## Current behavior (code references)

* `packages/frontend-sdk/src/chat/chatController.ts`:
  * `appendMessage()` → `backend.appendMessage()`
  * `send()` → `backend.send()`
* `packages/frontend-sdk/src/backend/restBackend.ts`:
  * `appendMessage()` POST `/sessions/{id}/messages`
  * `send()` POST `/sessions/{id}/send`
* `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`:
  * `handleSend` does `appendMessage` then `send`.

## Proposed changes

### A) Add new backend method for atomic turn

In `packages/frontend-sdk/src/backend/backend.ts` add:

* `sendTurn(sessionId, { message, configOverrides?, idempotencyKey? })`

Implement in `packages/frontend-sdk/src/backend/restBackend.ts`:

* POST to `/sessions/{id}/send_message`
* Include `Idempotency-Key` header if provided
* Expect response `{status, request_id, session_id?}` (exact shape depends on 040)

### B) Update ChatController API

Option 1 (preferred): add `chatController.sendTurn()` and update UI to call it.

Option 2: keep current methods but modify `send()` to optionally include a pending message; this is harder because messages are appended separately today.

### C) Generate and reuse idempotency key per send click

In UI (`mobile/.../SessionChatScreen.tsx`):

* generate a UUID when user presses Send
* call atomic endpoint once
* if request errors and user retries, reuse the same idempotency key (store it in component state until success/failure is terminal)

At minimum, ensure within a single press attempt the key is stable.

Implementation guidance:

- Generate a UUID per user-initiated send attempt.
- Reuse the same UUID across all retries of the same attempt (timeout, bridge reconnect, app resume).
- When a request succeeds (or is acknowledged with a `request_id`), persist the UUID alongside that `request_id` until the request completes so the UI can safely retry polling/refresh without re-sending.

### D) Transport-level support

If `Transport.request` doesn’t currently accept per-request headers in the calling path, ensure headers can be passed through.

* `BridgeTransport.request` already accepts `headers?: Record<string, string>`.
* Ensure `FetchTransport` does as well.

### E) Tests

* `packages/frontend-sdk` unit/integration tests:
  1. `sendTurn` calls correct endpoint with correct payload and idempotency header.
  2. (Optional) an integration test that simulates retry: same key results in same request_id response.

* Add/adjust tests to reflect Subtask 030 response changes:
  - `backend.send()` (legacy `/send`) should accept an optional idempotency key header and handle `{status, request_id}`.
  - Mutating endpoints that can be retried (message append, actions) should be able to pass idempotency keys as well.

## Acceptance criteria

* Pressing Send uses one HTTP request (append+send) rather than two.
* Idempotency-Key is sent and stable per attempt.
* Existing legacy flows remain supported (but are no longer used by the primary UI path).

Additional acceptance criteria (due to Subtask 030 broad idempotency):

- Frontend SDK supports `Idempotency-Key` for other retry-prone mutating calls (at minimum: legacy `appendMessage`, legacy `send`, and `executeAction`).
