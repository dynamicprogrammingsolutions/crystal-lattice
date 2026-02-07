# Subtask: Session settings UI (schema-driven overrides)

Implement a desktop-friendly session settings UI for the active chat tab.

This surfaces server-provided session config schema and overrides (same backend endpoints used by mobile), but with a desktop-first presentation (dropdown/popover/window; no full-screen modal).

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260202-desktop-macos-frontend/081-desktop-chat-header-and-session-actions.md`

## Status

- [x] Initial implementation done (mobile-shared UI + desktop window)
- [x] Refactor Stage 1 done (shared logic + headless host)
- [x] Refactor Stage 2 done (desktop app-owned rendering)
- [x] Refactor Stage 3 done (mobile app-owned rendering; pixel-identical)
- [ ] Refactor Stage 4 pending

## Implementation Notes (current state)

As of the latest implementation pass, session settings exist end-to-end for mobile + desktop, with app-owned rendering in both apps.

### Shared UI components (mobile-styled)

- `packages/frontend-rn-components/src/settings/SessionSettingsCard.tsx`
  - Extracted from the original mobile modal implementation.
  - Contains the default rendering for `checkbox`, `select` (chip-style), and text settings.
  - Includes the mobile “card frame” (width/maxHeight/padding), title, loading/error/empty-state, and a footer Close button.
- `packages/frontend-rn-components/src/settings/SessionSettingsSurface.tsx`
  - Provides the mobile modal overlay and click-outside-to-close behavior.

Note: these components are now legacy and scheduled for removal in Stage 4.

### Mobile

- `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx`
  - Loads session settings via backend:
    - `getSessionUiSchema`, `getSessionOverrides`, `getSessionConfigSchema`, `getSessionBaseConfig`
  - Filters elements to config settings (`ui_type === 'config'` or missing).
  - Uses shared logic + headless host from `@crystal-lattice/frontend-sdk-react` and renders the UI in-app (kept pixel-identical).

### Desktop

- Desktop macOS window plumbing (new RN root `SessionSettingsWindow`) was added:
  - `desktop/crystal-lattice-control-desktop-rn/index.js` registers `SessionSettingsWindow`.
  - `desktop/crystal-lattice-control-desktop-rn/src/windows/desktopWindowManager.ts` exposes open/close.
  - `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/DesktopWindowManager.mm` creates an `NSWindow` hosting the RN root.
  - `desktop/crystal-lattice-control-desktop-rn/src/windows/sessionSettingsCoordinator.ts` holds JS state (backend/sessionId/etc).
  - `desktop/crystal-lattice-control-desktop-rn/src/windows/SessionSettingsWindow.tsx` loads the same data and renders a desktop-owned frame/renderers via `SessionSettingsHost`.
  - `desktop/crystal-lattice-control-desktop-rn/src/chat/ChatPane.tsx` includes a “Settings…” action to open the window.

### Known limitation

- Stage 4 still pending: remove the now-legacy shared RN UI components (`SessionSettingsCard` / `SessionSettingsSurface`).

## Refactor Plan (staged; app-owned rendering + logic-only sharing)

Goal: keep mobile visuals intact while moving *rendering* fully into each app (mobile/desktop/web React), and only sharing the logic needed to compute effective values, tag labels, and consistent filtering.

### Stage 1: Add shared logic + headless host in `@crystal-lattice/frontend-sdk-react`

- Add session settings logic helpers to `packages/frontend-sdk-react/src/sessionSettings/*`:
  - Filter UI schema elements to “config settings” (key present + `ui_type === 'config'` or missing)
  - Build `schemaByKey`
  - Build `SessionSettingItem[]` containing only:
    - raw `UiSchemaElement`
    - `effectiveValue`, `hasOverride`, `tagLabel`, and related derived state
- Add a headless `SessionSettingsHost` component (React-only; no RN/DOM) that:
  - Accepts `renderers` as a single object keyed by `item.type`
  - Accepts `renderFrame` as a single render prop to wrap children

Checkpoint:

- Build-time only (no UI changes yet).
- Run `packages/frontend-sdk-react` tests (or typecheck) after adding the module.

Stage 1 notes:

- Implemented new module under `packages/frontend-sdk-react/src/sessionSettings/` and exported it from `packages/frontend-sdk-react/src/index.ts`.
- Added unit tests in `packages/frontend-sdk-react/src/sessionSettings/logic.test.ts` and enabled `vitest` in `packages/frontend-sdk-react/package.json`.

### Stage 2: Desktop migrates to app-owned rendering + desktop frame

- Update `desktop/crystal-lattice-control-desktop-rn/src/windows/SessionSettingsWindow.tsx`:
  - Stop using `SessionSettingsCard`
  - Use shared `SessionSettingsHost` + logic to build items
  - Provide a desktop-specific frame (no modal overlay, no mobile card frame, no in-content Close button)
  - Provide desktop `renderers` keyed by element type

Checkpoint (manual):

- Desktop window has desktop layout (no mobile frame/Close button).
- Toggle/select/text-save/revert all still persist.

Stage 2 notes:

- Migrated `desktop/crystal-lattice-control-desktop-rn/src/windows/SessionSettingsWindow.tsx` to:
  - Use `filterConfigUiSchemaElements`, `buildConfigSchemaByKey`, `buildSessionSettingItems` from `@crystal-lattice/frontend-sdk-react`.
  - Render via `SessionSettingsHost` with desktop-owned `renderFrame` (scroll container, padding, header).
  - Provide app-owned `renderers` keyed by type (`checkbox`, `select`, `text`, `multiline`) with a text-like fallback.
- Desktop-specific UI behaviors:
  - `checkbox` renders using a wrapped AppKit checkbox (`NSButtonTypeSwitch`).
  - `select` renders using a wrapped AppKit popup (`NSPopUpButton`).
  - Header includes a Close button styled like other desktop primary buttons.
- Desktop window no longer renders the mobile “card frame” (it uses a full-window layout).

Native components added (desktop macOS target):

- `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/MacCheckboxManager.mm`
- `desktop/crystal-lattice-control-desktop-rn/macos/CrystalLatticeControlDesktopRN-macOS/MacSelectManager.mm`
- JS wrappers:
  - `desktop/crystal-lattice-control-desktop-rn/src/native/MacCheckbox.tsx`
  - `desktop/crystal-lattice-control-desktop-rn/src/native/MacSelect.tsx`

### Stage 3: Mobile migrates last (must be visually identical)

- Update `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx`:
  - Stop using `SessionSettingsSurface`
  - Implement the same UI via app-owned `renderFrame` + `renderers`
  - Use shared logic to build items and consistent tags/effective values

Checkpoint (manual):

- Mobile modal is pixel-identical to current.
- Interactions are unchanged.

Stage 3 notes:

- Migrated `mobile/crystal-lattice-control-rn/src/components/SessionSettingsModal.tsx` to:
  - Stop using `SessionSettingsSurface`.
  - Use `filterConfigUiSchemaElements`, `buildConfigSchemaByKey`, `buildSessionSettingItems` from `@crystal-lattice/frontend-sdk-react`.
  - Render via `SessionSettingsHost` with app-owned `renderFrame` and app-owned `renderers`.
- Kept the modal overlay, card layout, styles, and strings identical by copying the existing `SessionSettingsSurface` + `SessionSettingsCard` presentation into the mobile component.

### Stage 4: Cleanup shared RN components

- Remove:
  - `packages/frontend-rn-components/src/settings/SessionSettingsCard.tsx`
  - `packages/frontend-rn-components/src/settings/SessionSettingsSurface.tsx`
- Remove exports from `packages/frontend-rn-components/src/index.ts`
- Remove `react-native-vector-icons` peer dependency if no longer needed by the package.

Checkpoint:

- Mobile + desktop build without the removed components.

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

- Refactor requirements:
  - Shared modules must be React-usable (no `react-native` or DOM dependencies).
  - Apps must provide:
    - renderers keyed by element type via a single `renderers` object
    - a single `renderFrame` wrapper for the surface/frame
  - Apps must be able to add support for new element types by adding a renderer key.

## Deliverables (refactor)

- Stage 1: `@crystal-lattice/frontend-sdk-react` exports logic helpers + `SessionSettingsHost`.
- Stage 2: desktop window uses app-owned frame + renderers (no mobile card frame).
- Stage 3: mobile modal uses app-owned frame + renderers (pixel-identical).
- Stage 4: remove baseline shared RN UI components.
