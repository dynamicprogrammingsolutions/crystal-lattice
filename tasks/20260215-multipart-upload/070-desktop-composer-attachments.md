# Desktop RN: Composer attachments UI (above/below + reorder)

Parent Task: `tasks/20260215-multipart-upload/000-main.md`

## Description

Implement attachment selection, display (above/below composer), reordering, and message sending for the desktop React Native app (`desktop/crystal-lattice-control-desktop-rn`). Attachments are sent via core message `multipartContent` while main text is sent via `content`.

Desktop should mirror the mobile UX where possible:

- Attachment actions are driven by per-type `composer_attachment` UI schema elements.
- Composer actions are pinnable (desktop already uses `ActionsMenuBar`; attachments should integrate there).
- Attachments support per-attachment metadata (`multipartContent[].metadata`), driven by `metadata_ui` in the schema.
- Metadata editing should use a **popover** on desktop.

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

## Implementation Plan (Approved)

This plan reflects the agreed approach (native `NSOpenPanel` + URL option + metadata popover).

### 1) Schema reading

- Desktop already loads session UI schema via `useSessionUiSchemaController` in `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`.
- Filter for `ui_type === "composer_attachment"`.
- Partition attachment drafts by `display_placement: "above" | "below"`.

### 2) Composer state (draft attachments)

- Keep two draft lists in `ChatPane.tsx`:
  - `attachmentsAbove: ComposerAttachmentDraft[]`
  - `attachmentsBelow: ComposerAttachmentDraft[]`

Draft shape (frontend-owned):

- `draftId` (stable key for reorder/delete)
- `type` (schema `attachment_type`, e.g. `image`, `pdf`)
- `content` (JSON-friendly):
  - `url?: string` for URL attachments
  - `data_base64?: string`, `mime_type?: string`, `filename?: string` for file attachments
- `metadata?: any` stored as `multipartContent[].metadata`

### 3) Attachment selection (v1)

For each attachment type element, provide **two ways to attach**:

- Native macOS file dialog (`NSOpenPanel`) → base64 payload
  - Implement a native bridge module (new `RCTBridgeModule`) that opens `NSOpenPanel`, reads the selected file, and returns `{ filename, mime_type, data_base64 }`.
  - Respect schema `supported_file_types` (extensions) by filtering allowed types.
  - Enforce a reasonable max file size to avoid huge JSON payloads.

- URL attachment (like mobile)
  - Provide a small UI to paste/type a URL.
  - Store it directly as `multipartContent[].content.url`.

Bridge constraint note: payload must remain JSON; no multipart/form-data.

### 4) Composer UI (pinnable actions + placement)

- Integrate attachment actions into the existing pinnable composer action bar (`ActionsMenuBar`) in `ChatPane.tsx`.
  - Action label/icon should come from schema (`label`, optional `icon`, and `key` when present).
  - Attachment actions should be pinnable the same way as other composer actions.

- Render compact attachment display per side:
  - Horizontal thumbnail strip above composer when `attachmentsAbove.length > 0`.
  - Horizontal thumbnail strip below composer when `attachmentsBelow.length > 0`.
  - Provide a single “manage” affordance per strip.

### 5) Reordering + removal (per-side)

- Reorder is per-side only:
  - Up/down moves within `attachmentsAbove` or within `attachmentsBelow`.
- Removal deletes a draft by `draftId`.

### 6) Attachment metadata UI (desktop popover)

- Support `metadata_ui` on each `composer_attachment` element.
- Store values into the selected draft’s `metadata` and include it in `multipartContent[].metadata` when sending.
- Metadata editing should be shown via a **desktop popover**.
- Prompt rules (match mobile semantics):
  - If `metadata_ui` contains required fields that have no default and are missing after picking, show the popover immediately.
  - If `metadata_ui.prompt === "always"`, show after picking.
  - Otherwise, allow editing later via the manage UI.

### 7) Sending `{content, multipartContent}`

- Update `handleSend` in `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`:
  - Send allowed when `content.trim().length > 0` OR there is at least one attachment.
  - If `content` is empty and attachments exist, send `content: ""`.
  - Include `multipartContent` as:
    - `[{ type, content, metadata }]` from both sides, preserving per-side order.
  - Clear composer text and attachment drafts on success.

### 8) Transcript rendering (received attachments)

- Update `desktop/crystal-lattice-control-desktop-rn/src/chat/DesktopMessageBubble.tsx`:
  - Render `message.multipartContent` above the text content for all roles.
  - `image`: render inline thumbnail using `content.url` or a `data:` URL derived from `data_base64`.
  - `pdf`: render a file tile/row (filename + icon).
  - Unknown types: fallback tile/row.

## Validation

- Manual checklist matching mobile.

## Definition of Done

- Desktop can send/receive multipart attachments.
- Placement and reorder function correctly.

---

## Implementation Notes (added 2026-02-17)

- Implemented native macOS file picker via `NSOpenPanel` that returns JSON `{ filename, mime_type, data_base64 }`.
  - Files: `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/MacAttachmentPicker.mm`, `desktop/crystal-lattice-control-desktop-rn/src/native/MacAttachmentPicker.ts`.
  - Xcode project wiring updated at `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN.xcodeproj/project.pbxproj`.

- Implemented desktop composer attachments end-to-end:
  - Schema-driven `ui_type: "composer_attachment"` actions added to the pinnable composer action bar in `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`.
  - Attachment picking supports both file-pick and URL attachment (mirrors mobile semantics).
  - Draft attachment state maintained per-side (`above`/`below`), reorder/delete per side, and sent as `multipartContent` along with `content`.
  - Sending is allowed with empty text if attachments exist.

- Implemented transcript rendering of received attachments:
  - `desktop/crystal-lattice-control-desktop-rn/src/chat/DesktopMessageBubble.tsx` renders `message.multipartContent` (image thumbnails / pdf tiles / fallback).

- Desktop attachment management UI: filmstrip + inline expanded management.
  - Filmstrip UI: `desktop/crystal-lattice-control-desktop-rn/src/chat/AttachmentThumbnailStrip.tsx` (now uses a chevron overlay button at top-right).
  - Expanded inline management UI (replaces the modal flow): `desktop/crystal-lattice-control-desktop-rn/src/chat/ComposerAttachmentsExpandedPanel.tsx`.
  - Expanded management renders with no frame/title, replaces filmstrip when open, and keeps chevron control top-right (rendered above list to avoid covering row buttons) via `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`.

- Metadata editing popover changed to a single-submit form UX:
  - Removed per-field “Save” buttons and the per-field delete/revert-to-default affordance.
  - User edits fields and submits with the bottom Save button.
  - Keyboard: `Tab` advances between text inputs, `Enter` submits (unless `Shift+Enter`), `Esc` cancels.
  - File: `desktop/crystal-lattice-control-desktop-rn/src/chat/AttachmentMetadataPopoverContent.tsx`.

- Popover anchoring fix:
  - Metadata popover now anchors to the clicked row’s edit button in the expanded management panel (rather than the composer actions “…” menu) by capturing an `anchorTag` with `findNodeHandle`.
  - Files: `desktop/crystal-lattice-control-desktop-rn/src/chat/ComposerAttachmentsExpandedPanel.tsx`, `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`.
