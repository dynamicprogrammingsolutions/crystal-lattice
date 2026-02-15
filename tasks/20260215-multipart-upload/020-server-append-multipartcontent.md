# Server: Accept `multipartContent` on append endpoint

Parent Task: `tasks/20260215-multipart-upload/000-main.md`

## Description

Update the FastAPI server so clients can append messages containing optional `multipartContent` while keeping `content` as the main text field (may be empty if multipart exists).

## Depends On

- `tasks/20260215-multipart-upload/010-core-message-multipartcontent.md`

## Current State

- Append endpoint: `application/python/agent_terminal_app/server.py:839` (`POST /sessions/{session_id}/messages`).
- Validation currently requires `role` and `content` to be strings.
- Calls `core.add_message(session, normalized_role, content, metadata, base_config)`.

## Requirements

- Accept optional `multipartContent` in request JSON.
- Allow `content` to be empty string when `multipartContent` has at least one entry.
- Preserve existing behavior for old clients that only send `{role, content, metadata}`.
- Treat multipart parts as opaque; no server-side schema enforcement beyond basic JSON-shape checks (optional).

## Implementation Plan

1) Update payload parsing

- In `add_message()` (`application/python/agent_terminal_app/server.py:839`):
  - Read `multipartContent = payload.get("multipartContent")`.
  - Keep reading `role`, `content`, `metadata`.

2) Update validation

- Continue requiring `role` as string.
- `content` must be a string, but may be empty.
- If `content` is empty/whitespace, require `multipartContent` to be a non-empty list.
- If `multipartContent` is provided:
  - Must be a list; elements should be dicts (optional strictness).
  - Do not validate per-part `type/content/metadata` beyond being dict-like.

3) Update call into core

- Call the updated `core.add_message()` signature that can accept multipart.
- Ensure stored session history includes multipart.

4) Event payload

- The server currently publishes a `message_appended` event containing `message: last_message.to_dict()`.
- Ensure this `to_dict()` includes `multipartContent` so frontends can observe it via events if they rely on event payloads.

5) Optional: sessions list preview

- `/sessions` currently derives preview from the first user message `content`.
- Decide whether to adjust preview generation when `content` is empty but multipart exists.
  - Suggested: if no content, show a placeholder like `[Attachment]` or use first text part if any.
  - This is optional; frontends can also display `""` previews.

## Tests

- Add/extend server tests under `application/python/tests`:
  - Append with `content: ""` + non-empty `multipartContent` succeeds.
  - Listing messages returns the multipart content.
  - Old payload with only content still works.

## Definition of Done

- Endpoint accepts multipart payloads and persists them.
- Empty `content` is allowed when multipart exists.
- Tests validate behavior.
