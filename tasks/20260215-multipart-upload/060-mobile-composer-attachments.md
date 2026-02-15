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
