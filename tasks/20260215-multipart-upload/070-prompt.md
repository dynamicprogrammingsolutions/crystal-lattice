Implement desktop (React Native macOS) composer support for attachments driven by per-type `composer_attachment` UI schema elements, including above/below placement, reordering within each side, sending `{content, multipartContent}`, and rendering received attachments.

## Step 1 — Prepare

1) Read the task context and requirements:
- `tasks/20260215-multipart-upload/000-main.md`
- `tasks/20260215-multipart-upload/070-desktop-composer-attachments.md`
- UI schema contract: `tasks/20260215-multipart-upload/040-plugin-ui-schema-composer-attachments.md`

2) Inspect current desktop chat composer and message rendering:
- `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`
- `desktop/crystal-lattice-control-desktop-rn/src/chat/DesktopMessageBubble.tsx`

Note: for the desktop we need the pinnable actions similar to the mobile, and display can be similar. It will differ only in the document picking. Implementation notes were added to the task tasks/20260215-multipart-upload/060-mobile-composer-attachments.md.

3) Inspect how session UI schema is loaded/consumed on desktop.

4) Decide how attachments will be selected on macOS for v1:
- URL-only attach (no native work), or
- file dialog + base64 encoding (requires native bridge/library).

Note: there is one document picker for macos, source checked out here: /Users/ferenci84/Dev/Mine/react-native-document-picker-macos

5) Share a plan with the user:
- Proposed UI changes
- Data model for attachments
- Sending logic and empty-content rule
- Rendering for image/pdf/unknown

Do not implement yet.

## Step 2 — Complete (after user approval)

1) Implement composer attachment state + UI.

2) Implement add/remove/reorder.

3) Update send logic to include `multipartContent`.

4) Update transcript rendering.

5) Run lint/tests if available and provide a manual test checklist.
