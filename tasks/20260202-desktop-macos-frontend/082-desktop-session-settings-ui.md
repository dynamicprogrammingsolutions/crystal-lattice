# Subtask: Session settings UI (schema-driven overrides)

Implement a desktop-friendly session settings UI for the active chat tab.

This surfaces server-provided session config schema and overrides (same backend endpoints used by mobile), but with a desktop-first presentation (dropdown/popover/window; no full-screen modal).

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/081-desktop-chat-header-and-session-actions.md`

## Status

- [ ] Not started

## Plan (with checkpoints)

### Chunk 1: Shared form + mobile migration

- Create shared settings form body:
  - Add `packages/frontend-rn-components/src/settings/SessionSettingsCard.tsx`.
  - Add `packages/frontend-rn-components/src/settings/SessionSettingsSurface.tsx`.
  - Export from `packages/frontend-rn-components/src/index.ts`.
- Component responsibilities:
  - Accept data + callbacks only (no data fetching).
  - Render a scrollable list of config entries based on `UiSchemaElement[]`.
  - Support field types used today:
    - `checkbox` (toggle + inline revert)
    - `select` (chip-style options + revert)
    - `string` / `multiline` text (editable TextInput + explicit Save + revert)
  - Callbacks (exact signature):
    - `onToggleCheckbox(key, next)`
    - `onSelectOption(key, value)`
    - `onSaveText(key, value)`
    - `onRevertToDefault(key)`
  - Display “value source” tags similar to mobile (e.g. `config` vs `default`) using `baseConfig` + `schemaByKey`.

- Migrate mobile to use the shared form body:
  - Keep mobile’s modal surface and network logic local in `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx`.
  - Keep current behavior:
    - filter to config elements (`ui_type === 'config'` or missing)
    - optimistic patching for checkboxes (rollback on failure)
    - save button for text fields
    - revert-to-default calls `deleteSessionOverride`

Checkpoint (manual):

- Mobile:
  - Open session settings modal; confirm UI schema + overrides load.
  - Toggle a checkbox; confirm it persists after closing/reopening.
  - Change a select; confirm it persists after closing/reopening.
  - Revert a value; confirm the override is removed and effective value matches base/default.

### Chunk 2: Desktop JS settings surface (window content + coordinator)

- Create a JS coordinator (patterned after `desktop/.../src/windows/applicationActionDialogCoordinator.ts`) to hold active settings window state:
  - New file: `desktop/crystal-lattice-control-desktop-rn/src/windows/sessionSettingsCoordinator.ts`
  - State should include at least: `id`, `connectionId`, `sessionId`, and a `backend` reference (or a provider function) plus `onClose` handler.

- Create the RN root component that will render inside the desktop window:
  - New file: `desktop/crystal-lattice-control-desktop-rn/src/windows/SessionSettingsWindow.tsx`
  - Wrap in `ThemeProvider` using `useDesktopTheme` (same as `AgentPickerWindow.tsx`).
  - On open (when coordinator state is set), load in parallel:
    - `backend.getSessionUiSchema(sessionId)`
    - `backend.getSessionOverrides(sessionId)`
    - `backend.getSessionConfigSchema(sessionId)` (build `schemaByKey`)
    - `backend.getSessionBaseConfig(sessionId)`
  - Render `SessionSettingsCard` and wire callbacks to backend methods:
    - optimistic updates for checkbox/select where safe
    - text fields save via explicit Save
    - revert via `backend.deleteSessionOverride(sessionId, key)`
  - If server lacks capabilities (via `backend.getCapabilities()`), show a friendly “Not supported by this backend” message.

### Chunk 3: macOS native window plumbing (DesktopWindowManager)

- Add native module surface for opening/closing the window:
  - Extend `desktop/crystal-lattice-control-desktop-rn/src/windows/desktopWindowManager.ts` with:
    - `openSessionSettingsWindow(params?: { title?: string }): void`
    - `closeSessionSettingsWindow(): void`
  - Register the RN root component:
    - `desktop/crystal-lattice-control-desktop-rn/index.js` add `AppRegistry.registerComponent('SessionSettingsWindow', ...)`.

- Implement native window creation + lifecycle:
  - Update `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/DesktopWindowManager.h` and `.mm`.
  - Mirror existing patterns used for `openAgentPicker` / `openApplicationActionDialogWindow`.
  - On window close via titlebar:
    - emit an event like `sessionSettingsWindowCancelled` so JS can clear coordinator state.

Checkpoint (manual):

- Desktop:
  - “Settings…” opens a macOS window reliably.
  - Closing via window controls triggers cleanup (no stale coordinator state).
  - Reopening works repeatedly (no duplicate windows).

### Chunk 4: Wire into the chat header

- Add a “Settings…” action to the chat header actions in `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx`:
  - Add a new action key (e.g. `settings`) to `BUILTIN_SESSION_ACTIONS`.
  - Only enable when `backend != null`.
  - On invoke:
    - set coordinator state for `{ connectionId, sessionId }`
    - call `DesktopWindowManager.openSessionSettingsWindow({ title: 'Session settings' })`

Checkpoint (manual):

- Desktop end-to-end:
  - Settings is disabled offline, enabled online.
  - Toggle/select/text-save/revert all persist and survive closing/reopening the settings window.
  - Opening settings for different tabs/sessions targets the correct session.

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

- `packages/frontend-rn-components/src/settings/SessionSettingsCard.tsx`
- `packages/frontend-rn-components/src/settings/SessionSettingsSurface.tsx`

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
