# Desktop: Plus-button Attachment Popover + `supports_url` + Metadata Window

## Description

Simplify the macOS (React Native) desktop attachment UX:

- Add a single **plus button** beside the composer input.
- Clicking the plus opens a popover with **one row per (attachment type × method)**.
  - Example: if we have `image` and `pdf`, and both support URL attachments, the popover shows 4 rows.
- Selecting a file opens the native picker; after choosing a file, if metadata needs to be set, open a **separate metadata editor window** (similar to Session Settings).
- Editing metadata later reuses the **same metadata editor window**.
- Extend the plugin UI schema `composer_attachment` element with an explicit `supports_url` boolean.

Parent Task: `tasks/20260215-multipart-upload/000-main.md`

## UX Requirements

- The plus button is placed at the **left side of the composer area**, immediately beside the input, vertically centered.
- The plus popover shows a flat list of actions:
  - `Select <Type>…` (native file picker)
  - `<Type> URL…` (URL attach flow)
  - Repeat per type.
- If metadata must be prompted, open a **separate window**.
  - Top of the window shows an **image preview** (for image attachments).
  - Use the same window for editing via the later “edit” button.

## Schema Change

Add a new optional boolean key on `composer_attachment` UI schema elements:

```json
{
  "ui_type": "composer_attachment",
  "attachment_type": "image",
  "supports_url": true
}
```

Frontend behavior:

- If `supports_url === true`, show a `... URL…` row.
- If `supports_url === false`, hide the URL row.
- If `supports_url` is omitted, default to showing the URL row (back-compat with existing behavior).

## Metadata Prompt Edge Cases (must verify)

- **No metadata fields** (empty / filtered-out `ui_schema`): do not open the metadata editor window; attach with defaults.
- **No required fields**: do not prompt unless `prompt: "always"`.
- **All required fields have defaults**: do not prompt (same as above).

## Implementation Plan

1) **UI schema updates**
   - Add `supports_url` to at least the OpenRouter `image` + `pdf` `composer_attachment` elements.

2) **Composer plus button + popover**
   - Add a `+` button next to the composer input in `desktop/.../src/chat/ChatPane.tsx`.
   - Replace attachment actions in the composer `ActionsMenuBar` with a single plus-popover.
   - Implement a new popover content component that renders a list of rows:
     - `Select <Type>…`
     - `<Type> URL…` (only if `supports_url`)

3) **Attachment metadata editor window**
   - Implement an `AttachmentMetadataWindow` using the existing `openReactWindow` infrastructure.
   - Add a coordinator module (like `sessionSettingsCoordinator.ts`) so `ChatPane` can open the window and receive `onSave` callbacks.
   - Add preview rendering at the top of the window.

4) **Wire add + edit flows to the metadata window**
   - On add: after picking file / entering URL, if metadata needs prompting, open the metadata window; otherwise attach immediately.
   - On edit: the expanded attachments panel edit button opens the same metadata window.

5) **Edge-case handling**
   - Ensure no-metadata-fields and defaults-required behaviors match the “Metadata Prompt Edge Cases” section.

6) **Validation**
   - `npx tsc -p tsconfig.json --noEmit` (desktop)
   - `npm test` (desktop)

## Checklist

- [x] Add `supports_url` to `composer_attachment` UI schema (OpenRouter)
- [x] Implement composer plus button and plus popover rows (file + url)
- [x] Implement `AttachmentMetadataWindow` + coordinator + module registration
- [x] Wire add flow: picker → maybe metadata window → attach
- [x] Wire edit flow: edit button → metadata window → update metadata
- [x] Handle “no metadata fields” and “defaults satisfy required” cases
- [x] Run desktop typecheck + tests

## Implementation Notes

Completed (2026-02-17)

- Added `supports_url` to OpenRouter `composer_attachment` UI elements:
  - `plugins/openrouter/src/openrouter_plugins/openrouter_provider.py`
  - `core/python/plugins/openrouter_provider.py`
- Replaced desktop attachment add UX with a single composer `+` button + popover rows:
  - Added `desktop/crystal-lattice-control-desktop-rn/src/chat/ComposerAttachmentPlusPopoverContent.tsx`
  - Updated `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`
  - Removed unused `desktop/crystal-lattice-control-desktop-rn/src/chat/AttachmentAddPopoverContent.tsx`
- Implemented a dedicated metadata editor window (reused for “add” and “edit”):
  - `desktop/crystal-lattice-control-desktop-rn/src/windows/attachmentMetadataCoordinator.ts`
  - `desktop/crystal-lattice-control-desktop-rn/src/windows/AttachmentMetadataWindow.tsx`
  - Registered module in `desktop/crystal-lattice-control-desktop-rn/index.js`
  - Wired system-close cancellation in `desktop/crystal-lattice-control-desktop-rn/src/DesktopRoot.tsx`
- Metadata prompting edge cases:
  - Exported `hasEditableAttachmentMetadataFields()` and used it to avoid opening the metadata window when there are no editable fields.
  - Defaults/required logic remains based on `shouldPromptForAttachmentMetadata()`.
- Validation:
  - `cd desktop/crystal-lattice-control-desktop-rn && npx tsc -p tsconfig.json --noEmit`
  - `cd desktop/crystal-lattice-control-desktop-rn && npm test`
