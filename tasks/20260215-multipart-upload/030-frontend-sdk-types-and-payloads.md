# Frontend SDK: Message types + REST payload support for `multipartContent`

Parent Task: `tasks/20260215-multipart-upload/000-main.md`

## Description

Extend the TypeScript frontend SDK types and REST backend so clients can send/receive `multipartContent` on messages.

## Depends On

- `tasks/20260215-multipart-upload/020-server-append-multipartcontent.md`

## Current State

- `ApiMessage` in `packages/frontend-sdk/src/types/messages.ts:3` has `{ role, content, metadata? }`.
- `AgentBackend.appendMessage()` type in `packages/frontend-sdk/src/backend/backend.ts` only includes `content` and optional `metadata`.
- REST payload builder in `packages/frontend-sdk/src/backend/restBackend.ts` posts `{role, content, metadata?}`.

## Requirements

- Add optional `multipartContent` to message types.
- Ensure REST backend includes `multipartContent` when provided.
- Preserve backward compatibility for clients that ignore multipart.
- Do not change semantics of `content` selection helpers; `content` remains primary display text.

## Implementation Plan

1) Update message types

- File: `packages/frontend-sdk/src/types/messages.ts`
- Extend `ApiMessage`:
  - `multipartContent?: any[] | null;`
  - Keep type intentionally permissive in SDK v1 (opaque/extensible contract).

2) Update backend interface

- File: `packages/frontend-sdk/src/backend/backend.ts`
- Extend the `appendMessage` message parameter to include optional `multipartContent`.

3) Update REST backend payload

- File: `packages/frontend-sdk/src/backend/restBackend.ts`
- In `appendMessage(...)`, include `multipartContent` when present.

4) Update chat controller passthrough

- File: `packages/frontend-sdk/src/chat/chatController.ts`
- Ensure `appendMessage()` accepts and forwards `multipartContent`.

5) Tests

- File: `packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts`
- Add a test case that appends a message with `multipartContent` and then lists messages to assert it roundtrips.

## Definition of Done

- SDK compiles with updated types.
- REST append includes multipart payload.
- Integration test covers roundtrip.
