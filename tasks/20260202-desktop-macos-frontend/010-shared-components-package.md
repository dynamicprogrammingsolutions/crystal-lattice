# Subtask: Shared mid-level RN components package

Create a small shared RN components package intended to be reused by both mobile and desktop. The package should include *mid-level components with some logic* (e.g. message/session actions menus, pinned actions UI, session tabs), but avoid:

- Ultra-low-level primitives (`Button`, `Text`, etc.)
- Whole-screen components (e.g. the full chat transcript renderer, markdown renderer)

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260129-frontend-sdk/000-main.md`

## Status

- [x] Done (Phase 5 baseline)

## Deliverables (implemented)

### New package

- Created `packages/frontend-rn-components/` as `@crystal-lattice/frontend-rn-components`.
- Peer dependencies: `react`, `react-native`, `react-native-vector-icons`.
- Export surface: `packages/frontend-rn-components/src/index.ts`.

### Shared theme (cross-app)

- Added a shared theme module (light/dark + provider/hook):
  - `packages/frontend-rn-components/src/theme.ts`
- Mobile now re-exports the shared theme to avoid churn in imports:
  - `mobile/crystal-lattice-control-rn/src/theme.ts`

### Shared “actions menu” UI (logic + visuals)

This is the reference/PoC shared component set for later extractions.

- Model + hook:
  - `packages/frontend-rn-components/src/actions/model.ts`
  - `packages/frontend-rn-components/src/actions/useActionsMenuModel.ts`
- Shared UI (default visuals + escape hatches):
  - `packages/frontend-rn-components/src/actions/ActionsMenuContent.tsx`
  - `packages/frontend-rn-components/src/actions/ActionsMenuPanel.tsx`
  - `packages/frontend-rn-components/src/actions/ActionsMenuBar.tsx`
- Modal + dropdown surfaces (platform-dependent placement is isolated here):
  - `packages/frontend-rn-components/src/actions/MenuSurfaces.tsx`

### Proved reuse in mobile (no duplication)

- Both mobile bars are now thin wrappers over the shared `ActionsMenuBar`:
  - `mobile/crystal-lattice-control-rn/src/components/MessageActionsBar.tsx`
  - `mobile/crystal-lattice-control-rn/src/components/SessionActionsBar.tsx`
- Standardized styling to the original `MessageActionsBar` sizing (icon sizes, spacing) to avoid duplication.

## Implementation notes (important for other subtasks)

- **Theme must be provided at the app root** to get correct colors in shared UI.
  - Use `ThemeProvider` + `useSystemTheme()` from `@crystal-lattice/frontend-rn-components`.
- **Anchored dropdown menus use `Modal` as a portal**.
  - `DropdownMenuSurface` measures the trigger with `measureInWindow` and positions the menu close to it.
  - For desktop, this meets the “minimal mouse movement” UX requirement.
  - You can override `backdropStyle` for desktop to avoid dimming (e.g. transparent backdrop).
- **Measuring anchors in RN requires `collapsable={false}`** in many cases.
  - `ActionsMenuBar` wraps the trigger anchor with `collapsable={false}` so `measureInWindow` works.
  - Reuse this pattern for future anchored UI (popover/tooltips).
- **Action definitions stay app-local**, but shared UI expects `iconName` by default.
  - If desktop uses a different icon naming scheme, pass `getIconName`.
- **Filtering behavior** in the model:
  - `availableActions` filters `baseActions` only.
  - `extraActions` (e.g. plugin-provided actions) are always included.
- **Future shared components guideline**:
  - Prefer exporting “full default visuals” + theme tokens + escape hatches.
  - Keep platform-specific placement/behavior isolated in small surface components.

## Verification

- `packages/frontend-rn-components` has unit tests for the pure model:
  - `packages/frontend-rn-components/src/actions/model.test.ts`
- Mobile Metro is configured to resolve workspace packages:
  - `mobile/crystal-lattice-control-rn/metro.config.js`
