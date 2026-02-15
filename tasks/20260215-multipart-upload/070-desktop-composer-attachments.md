# Desktop RN: Composer attachments UI (above/below + reorder)

Parent Task: `tasks/20260215-multipart-upload/000-main.md`

## Description

Implement attachment selection, display (above/below composer), reordering, and message sending for the desktop React Native app (`desktop/crystal-lattice-control-desktop-rn`). Attachments are sent via core message `multipartContent` while main text is sent via `content`.

## Depends On

- `tasks/20260215-multipart-upload/030-frontend-sdk-types-and-payloads.md`
- `tasks/20260215-multipart-upload/040-plugin-ui-schema-composer-attachments.md`
- `tasks/20260215-multipart-upload/050-provider-mapping-multipartcontent.md`

## Current State

- Desktop composer appends/sends text-only messages in `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`.

## Requirements

- Read session UI schema and find elements where `ui_type === "composer_attachment"`.
- Show attachment UI controls based on declared attachment types and supported file types.
- Display attachments above/below composer per `display_placement`.
- Allow reordering attachments within the same placement side.
- Allow send with empty content if at least one multipart attachment is present.
- Render attachments in chat transcript.

## Implementation Plan

1) Schema reading

- Desktop already uses session UI schema elements for status/footer rendering.
- Filter for `composer_attachment` elements.
- Partition by `display_placement`.

2) Composer state

- Add state for attachments above/below similar to mobile.

3) Attachment selection

Options (choose one for v1):

- URL-only (fastest, no native dialog): allow user to paste an image/PDF URL.
- Native file dialog (better UX): implement or use an existing macOS file picker bridge.
  - Convert file to base64 and store in `part.content.data_base64` with `mime_type`/`filename`.

Bridge constraint note: payload must remain JSON.

4) Reordering + removal

- Provide reorder controls (up/down) per placement list.
- Removal button per attachment.

5) Sending

- Update `handleSend` in `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`:
  - If content is empty, require attachments.
  - Append message with `{content, multipartContent}`.

6) Transcript rendering

- Update `desktop/crystal-lattice-control-desktop-rn/src/chat/DesktopMessageBubble.tsx`:
  - Render images inline.
  - Render PDFs as a file row.
  - Unknown types: fallback row.

## Validation

- Manual checklist matching mobile.

## Definition of Done

- Desktop can send/receive multipart attachments.
- Placement and reorder function correctly.
