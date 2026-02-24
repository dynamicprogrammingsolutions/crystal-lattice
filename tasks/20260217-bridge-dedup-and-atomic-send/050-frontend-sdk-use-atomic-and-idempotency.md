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

### A) Add new backend method for atomic send

In `packages/frontend-sdk/src/backend/backend.ts` add:

* `sendMessage(sessionId, { message, configOverrides?, idempotencyKey? })`

Implement in `packages/frontend-sdk/src/backend/restBackend.ts`:

* POST to `/sessions/{id}/send_message`
* Always include an `Idempotency-Key` header:
  - If caller provides `idempotencyKey`, use it.
  - Otherwise generate a fresh key in the SDK for this request.
* Expect response `{status, request_id, session_id?}` (exact shape depends on 040)

### B) Update ChatController API

Option 1 (preferred): add `chatController.sendMessage()` and update UI to call it.

Option 2: keep current methods but modify `send()` to optionally include a pending message; this is harder because messages are appended separately today.

### C) Idempotency key behavior

Generate a fresh idempotency key per SDK request invocation (low-level guard against duplicate HTTP delivery/retries).

- The SDK should generate the key automatically for mutating requests.
- The frontend has the option to provide a key explicitly via SDK method params, but the mobile UI will not do this today.
- Do not reuse keys across separate user button presses.

### D) Transport-level support

If `Transport.request` doesn’t currently accept per-request headers in the calling path, ensure headers can be passed through.

* `BridgeTransport.request` already accepts `headers?: Record<string, string>`.
* Ensure `FetchTransport` does as well.

### E) Tests

* `packages/frontend-sdk` unit/integration tests:
  1. `sendMessage` calls correct endpoint with correct payload and idempotency header.
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

## Implementation notes (added during completion)

- Added `generateIdempotencyKey()` in `packages/frontend-sdk/src/utils/idempotency.ts`.
- Updated `packages/frontend-sdk/src/backend/backend.ts`:
  - Added `sendMessage(...)` (atomic append+send).
  - Added optional `idempotencyKey` plumbing for other mutating calls (append/send/actions/plugins/etc).
- Updated `packages/frontend-sdk/src/backend/restBackend.ts`:
  - Implemented `sendMessage(...)` → `POST /sessions/{id}/send_message`.
  - Added `Idempotency-Key` header to mutating requests, generating a fresh key per request invocation unless caller provides one.
- Updated `packages/frontend-sdk/src/chat/chatController.ts`:
  - Added `ChatController.sendMessage(...)`.
  - Threaded optional `idempotencyKey` through `appendMessage()` and `send()` wrappers.
  - Updates `activeRequestId` immediately when `{request_id}` is returned.
- Updated `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`:
  - `handleSend` now uses the atomic `chatController.sendMessage(...)` call.
  - Added a UI guard to prevent sending while `activeRequestId` is set (avoids 409 conflict from the atomic endpoint).
- Tests:
  - Updated `packages/frontend-sdk/src/backend/restBackend.sessionPlugins.test.ts` to account for the new `Idempotency-Key` header.
  - Added `packages/frontend-sdk/src/backend/restBackend.idempotency.test.ts` to cover default-generated keys and caller-provided overrides.
