Implement mobile (React Native) composer support for attachments driven by per-type `composer_attachment` UI schema elements, including above/below placement, reordering within each side, sending `{content, multipartContent}`, and rendering received attachments.

## Step 1 — Prepare

1) Read the task context and requirements:
- `tasks/20260215-multipart-upload/000-main.md`
- `tasks/20260215-multipart-upload/060-mobile-composer-attachments.md`
- UI schema contract: `tasks/20260215-multipart-upload/040-plugin-ui-schema-composer-attachments.md`

2) Inspect current mobile chat composer and message rendering:
- `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`
- `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx`
- Any helper utilities used by the screen/components

3) Inspect how session UI schema is already loaded/consumed:
- `useSessionUiSchemaController` usage in `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`

4) Identify missing dependencies/decisions for picking files:
- Determine whether to implement URL-only attachments or add native picker + base64 reading.
- Ensure approach stays bridge-compatible (JSON only).

5) Share a plan with the user:
- Proposed UI/UX changes (buttons, lists, reorder controls)
- Data model for draft attachments
- Sending rules (allow empty content iff attachments exist)
- Rendering strategy for image/pdf/unknown

Do not implement yet.

## Step 2 — Complete (after user approval)

1) Implement composer attachment state + UI.

2) Implement attachment add/remove/reorder.

3) Update send logic to include `multipartContent`.

4) Update message rendering to display multipart attachments.

5) Run lint/tests if available and provide a manual test checklist.
