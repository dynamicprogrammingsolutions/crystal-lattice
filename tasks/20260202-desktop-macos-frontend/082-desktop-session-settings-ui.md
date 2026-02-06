# Subtask: Session settings UI (schema-driven overrides)

Implement a desktop-friendly session settings UI for the active chat tab.

This surfaces server-provided session config schema and overrides (same backend endpoints used by mobile), but with a desktop-first presentation (dropdown/popover/window; no full-screen modal).

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/081-desktop-chat-header-and-session-actions.md`

## Status

- [ ] Not started

## Context to read first (files + line numbers)

- Backend session settings endpoints (read 100–106): `packages/frontend-sdk/src/backend/backend.ts:100`
- Mobile session settings implementation (logic + field rendering; read 48–111 and 210–260):
  - `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx:48`
  - `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx:210`
- Desktop window manager capabilities (existing windows/popovers; read 1–58): `desktop/crystal-lattice-control-desktop-rn/src/windows/desktopWindowManager.ts:1`
- Desktop pattern for “form dialog in window/popover” (plugin action dialog; read 320–387): `desktop/crystal-lattice-control-desktop-rn/src/panels/SessionsPanel.tsx:320`

## Requirements

- Must support backend capabilities `sessionUiSchema` and `sessionConfigOverrides`.
- Must support common field types used by the UI schema (at least):
  - checkbox
  - select
  - string / multiline text
- Must support:
  - optimistic updates for simple fields where possible
  - revert-to-default (delete override)
- Desktop presentation should avoid RN `Modal` for a full-screen settings experience.

## Deliverables

### 1) Extract a shared form body (reduce duplication)

Create a shared settings form component in `@crystal-lattice/frontend-rn-components` (new folder is OK):

- `packages/frontend-rn-components/src/settings/SessionSettingsForm.tsx`

It should:

- Accept data + callbacks, not fetch on its own.
- Render a scrollable list of config entries.
- Implement the per-field UI and call callbacks:
  - `onToggleCheckbox(key, next)`
  - `onSelectOption(key, value)`
  - `onSaveText(key, value)`
  - `onRevertToDefault(key)`

Then migrate mobile `SessionSettingsModal` to use the shared form body (keep the modal surface mobile-local).

### 2) Desktop settings surface

Implement a desktop-first surface to host the shared form:

- Recommended: new macOS window or popover via `DesktopWindowManager` (similar to application action dialog windows).
- Alternative (Phase 5 baseline): a large anchored popover using `DropdownMenuSurface`.

If adding a new window/popover type:

- Add a new RN root component under `desktop/crystal-lattice-control-desktop-rn/src/windows/`.
- Extend the native module in `desktop/crystal-lattice-control-desktop-rn/macos/**/DesktopWindowManager.mm` to open/close it.

### 3) Wire into the chat header

- Add a “Settings…” entry/button in the header created in `081`.
- Only enable settings when `backend != null`.

## Verification

- Open settings for a session; confirm it loads UI schema + overrides.
- Toggle a checkbox; confirm it persists and survives closing/reopening settings.
- Change a select; confirm it persists.
- Revert a value; confirm the override is removed.
