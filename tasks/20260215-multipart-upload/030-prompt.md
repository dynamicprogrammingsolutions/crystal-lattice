Extend the TypeScript frontend SDK so messages can include optional `multipartContent`, and ensure REST append requests include it when present.

## Step 1 — Prepare

1) Read the task context and requirements:
- `tasks/20260215-multipart-upload/000-main.md`
- `tasks/20260215-multipart-upload/030-frontend-sdk-types-and-payloads.md`

2) Inspect current SDK message types and backend interfaces:
- `packages/frontend-sdk/src/types/messages.ts`
- `packages/frontend-sdk/src/backend/backend.ts`
- `packages/frontend-sdk/src/backend/restBackend.ts`
- `packages/frontend-sdk/src/chat/chatController.ts`

3) Inspect existing integration tests for backend append/list patterns:
- `packages/frontend-sdk/src/integration/__tests__/backend.integration.test.ts`

4) Identify any downstream call sites in mobile/desktop that might need type updates.

5) Share a plan with the user:
- Exact type changes (keeping `multipartContent` intentionally opaque)
- REST payload changes
- Test additions/updates

Do not implement yet.

## Step 2 — Complete (after user approval)

1) Implement type changes and update all compile errors.

2) Update REST backend to send `multipartContent`.

3) Add/update the integration test to cover a roundtrip.

4) Run the relevant test(s) (`npm test` or package-level tests as configured) and report results.
