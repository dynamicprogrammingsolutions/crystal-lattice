# Mobile RN: Composer attachments UI (above/below + reorder)

Parent Task: `tasks/20260215-multipart-upload/000-main.md`

## Description

Implement attachment selection, display (above/below composer), reordering, and message sending for the React Native mobile app (`mobile/crystal-lattice-control-rn`). Attachments are sent via core message `multipartContent` while main text is sent via `content`.

## Depends On

- `tasks/20260215-multipart-upload/030-frontend-sdk-types-and-payloads.md`
- `tasks/20260215-multipart-upload/040-plugin-ui-schema-composer-attachments.md`
- `tasks/20260215-multipart-upload/050-provider-mapping-multipartcontent.md`

## Current State

- Composer uses a single `composeText` string and appends/sends text-only messages.
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx` appends with `chatController.appendMessage({ role: 'user', content: text })`.

## Requirements

- Read session UI schema and find elements where `ui_type === "composer_attachment"`.
- Show attachment UI controls based on declared attachment types and supported file types.
- Display attachments above/below composer per element `display_placement`.
- Allow reordering attachments within the same placement side.
- Send allowed when:
  - `content.trim()` is non-empty, OR
  - there is at least one attachment in multipart.
- Send message payload:
  - `content`: main composer text (may be empty)
  - `multipartContent`: array of attachment part objects (opaque contract)

## Implementation Plan

1) Data model in composer state

- Add state for attachments, partitioned by placement:
  - `attachmentsAbove: MultipartPartDraft[]`
  - `attachmentsBelow: MultipartPartDraft[]`
- Each draft should include:
  - `type` (matches `attachment_type` such as `image` or `pdf`)
  - `content` object (likely includes `url` or `data_base64`, `mime_type`, `filename`)
  - `metadata` object (for optional controls like quality)

2) Read schema and decide UI

- Use existing session UI schema controller (`useSessionUiSchemaController`) already in `SessionChatScreen.tsx`.
- Filter elements for `ui_type === "composer_attachment"`.
- Partition into above/below by `display_placement`.

3) Attachment picking

- Implement picking for:
  - `image` supporting `jpg/png`
  - `pdf` supporting `pdf`

Bridge constraint note: requests must be JSON.

Suggested v1 approach:
- Convert picked files to base64 and store under `part.content.data_base64` plus `mime_type`/`filename`.
- Alternatively (if native deps are a concern), implement URL-only attachments first.

4) Rendering attachments in composer

- Above list: render thumbnails/previews above the TextInput.
- Below list: render under the TextInput.
- Provide reorder UI per list (simple up/down controls acceptable for v1).
- Provide remove button per attachment.

5) Sending

- In `handleSend`:
  - Determine `content` from composeText (may be empty string).
  - Combine multipart: `multipartContent = [...attachmentsAbove, ...attachmentsBelow]`.
  - Append message:
    - `chatController.appendMessage({ role: 'user', content, multipartContent })`
  - Clear composer text + attachments on success.

6) Message rendering

- Update `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx` to render `message.multipartContent`:
  - For `type === 'image'`: render `<Image>` (support `data:` urls or base64)
  - For `type === 'pdf'`: render a tappable row (filename + icon)
  - Unknown types: show a fallback row (`[Attachment: <type>]`)

## Tests / Validation

- Minimal: manual test checklist
  - attachments appear per placement
  - reorder works
  - can send with empty content if attachments exist
  - message list shows attachments after reload

Optional: jest component tests for rendering of multipart attachments.

## Definition of Done

- Mobile app can send/receive multipart attachments.
- Composer is driven by plugin UI schema elements.
- Reordering works within each placement side.

---

## Notes added during completion (2026-02-15)

### Implemented

- Composer attachment support is implemented in `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`:
  - Reads session UI schema `elements` and filters `ui_type === "composer_attachment"`.
  - Maintains draft attachment state split by placement: `attachmentsAbove` / `attachmentsBelow`.
  - Renders per-type attachment buttons plus draft lists above/below the main `TextInput`.
  - Supports remove + reorder (up/down) within each side.
  - Send/append payload includes `{ content, multipartContent }` and allows empty `content` if attachments exist.
- Message rendering is implemented in `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx`:
  - Renders `message.multipartContent` above the text content for all roles.
  - `image` parts render inline via `<Image>`.
  - `pdf` parts render as a tappable row (opens http(s) URLs if possible; otherwise copies URL to clipboard).
  - Unknown types fall back to a generic attachment row.

### Picking strategy (bridge-compatible JSON)

- Image attachments:
  - Uses `react-native-image-picker` for both photo library and camera capture.
  - Adds support for image URLs as attachments (http/https or `data:image/...`), stored as `multipartContent[].content.url`.
- PDF attachments:
  - Uses `react-native-document-picker` and reads base64 via `react-native-fs`.
- Helper: `mobile/crystal-lattice-control-rn/src/attachmentPicking.ts`.

### Native setup notes

- iOS:
  - Added `NSPhotoLibraryUsageDescription` and `NSCameraUsageDescription` to `mobile/crystal-lattice-control-rn/ios/CrystalLatticeControlRN/Info.plist`.
- Android:
  - Per upstream docs, no manifest permissions were added.
  - Added `implementation("androidx.activity:activity:1.9.+")` in `mobile/crystal-lattice-control-rn/android/app/build.gradle` because `minSdkVersion` is 24 (< 30), to ensure the AndroidX Photo Picker backport is available.

### Test notes

- Jest was updated to mock new native dependencies so `npm test` can run in CI/dev without native modules.
  - `mobile/crystal-lattice-control-rn/jest.setup.js`
  - `mobile/crystal-lattice-control-rn/jest.config.js`

---

## Notes added during completion (2026-02-16)

### Plan (agreed in-session)

1) Desktop-style composer actions (pinnable) at top of composer

- Use the standard pinnable actions component (`ActionsMenuBar`) in the composer area (not the screen header).
- Move `Resend` + `Cancel` into this pinned composer actions bar.
- Keep `Send` + `Append` at the bottom.
- Attachment action buttons should be driven by `ui_type: "composer_attachment"` elements and rendered inside the pinnable actions bar.
- Plugins define the attachment action label/title + icon for each attachment type.

2) Add a PDF attachment UI element for OpenRouter (UI-only)

- Add a `composer_attachment` element for `attachment_type: "pdf"` for testing.
- Do not add provider support for PDFs; PDFs should be silently ignored during provider message conversion so the UI can be exercised without breaking sends.

3) Attachment metadata capture and editing

- Support per-attachment metadata as `multipartContent[].metadata`.
- OpenRouter does not support metadata; metadata should be ignored by the provider when processing messages (but persisted in session history).
- Plugins provide metadata UI schema via `metadata_ui` on each `composer_attachment` element.
- Metadata schema + rendering should match the session settings modal (same schema style + rendering).
- Prompt rules:
  - If any metadata field is `required` and has no default, the metadata modal must be shown after selecting the file/image (mandatory to set).
  - Otherwise the plugin controls whether to always prompt or skip (but users can edit metadata later).

4) Compact attachment display in composer

- Replace the vertical attachment lists that push content upward.
- Use a horizontally scrollable thumbnail filmstrip to consume minimal vertical space.
- Provide a single edit affordance for the filmstrip that opens a popup/modal with a vertical list view:
  - One row per attachment
  - Thumbnail on the left
  - Icons: up/down/edit-metadata/delete

5) Attachment display in transcript

- When rendering sent messages that include `multipartContent`, use the same horizontal thumbnail filmstrip display.

6) Keyboard avoidance

- Only the composer input should be keyboard-avoiding.
- If the bottom attachment strip exists, it may be allowed to be covered by the keyboard.

### Implemented (including corrections)

#### Composer: pinnable actions bar (top)

- Implemented a composer actions bar using the shared `ActionsMenuBar` component:
  - Attachment actions are generated from session UI schema `composer_attachment` elements.
  - `Resend` and `Cancel` are in this bar.
  - `Append` and `Send` remain as bottom buttons.
- Added pinned persistence for composer actions using `PinnedActionsContext` (`usePersistentPinnedActions`).
- Files:
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`

#### Plugin-defined titles/icons + PDF UI-only action

- Implemented plugin-driven `composer_attachment` UI schema additions in the OpenRouter plugin (not the core copy):
  - Adds `key` and `icon` to the existing `image` attachment element.
  - Adds a `pdf` attachment element labeled `"PDF (UI only)"` with an icon.
  - Adds `metadata_ui` to both.
- Updated OpenRouter provider conversion to silently ignore non-image multipart parts (so PDF attachments do not break sends).
- Files:
  - `plugins/openrouter/src/openrouter_plugins/openrouter_provider.py`

#### Attachment metadata modal (settings-style)

- Added a metadata modal that renders a settings-style form based on `metadata_ui` supplied by the plugin and stores values into `multipartContent[].metadata`.
- Enforces required fields (blocks save if required fields are missing).
- Prompt logic:
  - If required defaults are missing, the modal is automatically shown after picking.
  - If not required, modal is shown only when plugin `metadata_ui.prompt == "always"`.
- Files:
  - `mobile/crystal-lattice-control-rn/src/components/AttachmentMetadataModal.tsx`
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`

#### Composer attachment rendering: horizontal filmstrip + manage modal

- Replaced the previous vertical draft attachment lists with a horizontal thumbnail filmstrip.
- Implemented a single manage/edit affordance that opens a modal containing a vertical list of all attachments for that placement side, with per-row controls:
  - Thumbnail left
  - Icons: up/down/edit metadata/delete
- The filmstrip manage icon was refined to be a rounded overlay button on the right edge, vertically centered.
- Files:
  - `mobile/crystal-lattice-control-rn/src/components/AttachmentThumbnailStrip.tsx`
  - `mobile/crystal-lattice-control-rn/src/components/ComposerAttachmentsManageModal.tsx`
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`

#### Transcript attachment rendering: shared filmstrip

- Updated message rendering to display `multipartContent` using the shared horizontal filmstrip UI.
- Files:
  - `mobile/crystal-lattice-control-rn/src/components/MessageBubble.tsx`

#### Keyboard avoidance (correction and final state)

- Attempted to change keyboard avoidance to apply only to the composer input area; this caused issues (composer could still be covered) and was reverted.
- Current behavior is restored to the previous state: the entire screen is wrapped in a `KeyboardAvoidingView` (same as before these changes).
- File:
  - `mobile/crystal-lattice-control-rn/src/SessionChatScreen.tsx`

#### Cleanup

- Removed components that were superseded by the filmstrip + manage modal approach:
  - Deleted `mobile/crystal-lattice-control-rn/src/components/ComposerAttachments.tsx`
  - Deleted `mobile/crystal-lattice-control-rn/src/components/AttachmentEditModal.tsx`

#### Note on core OpenRouter provider

- Any UI-schema changes for OpenRouter should live in the plugin package.
- Core copy was reverted to avoid accumulating work in a module scheduled for removal:
  - `core/python/plugins/openrouter_provider.py`
