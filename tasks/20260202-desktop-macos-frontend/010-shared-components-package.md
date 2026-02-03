# Subtask: Shared mid-level RN components package

Create a small shared RN components package intended to be reused by both mobile and desktop. The package should include *mid-level components with some logic* (e.g. message/session actions menus, pinned actions UI, session tabs), but avoid:

- Ultra-low-level primitives (`Button`, `Text`, etc.)
- Whole-screen components (e.g. the full chat transcript renderer, markdown renderer)

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260129-frontend-sdk/000-main.md`

## Status

- [x] Done (Phase 5 baseline)

## What exists today (reference)

Mobile currently has mid-level components that mix UI + some logic:

- `MessageActionsBar` uses pinned actions + “more” menu (currently modal-driven):
  - `mobile/crystal-lattice-control-rn/src/components/MessageActionsBar.tsx:1`
- `SessionActionsBar` similarly:
  - `mobile/crystal-lattice-control-rn/src/components/SessionActionsBar.tsx:1`
- Action definitions (keys/labels/default pinned roles):
  - `mobile/crystal-lattice-control-rn/src/messageActions.ts:1`
  - `mobile/crystal-lattice-control-rn/src/sessionActions.ts:1`

Desktop requirements differ:

- Use dropdown/anchored menus instead of modals.
- “Tabs” are session tabs in the main column.

## Work plan

### 0) Scope strategy (important)

This package is intentionally **evolving**.

For Phase 5, do **not** try to pre-decide every shared component up front. Instead:

- Start by extracting a *small* set of components that are already working well in mobile **and** are immediately useful for desktop.
- Add additional exports opportunistically as the desktop UI needs them.
- Treat `tasks/20260202-desktop-macos-frontend/900-shared-components-scope.md` as boundary guidance (what is/isn’t in scope), not a fixed checklist.
- Treat `tasks/20260202-desktop-macos-frontend/930-extractable-subcomponents.md` as a backlog of candidates, not required deliverables for this subtask.

### 1) Create a new package

- Create `packages/frontend-rn-components/`.
- `package.json`:
  - name: `@crystal-lattice/frontend-rn-components`
  - peer deps: `react`, `react-native`
  - deps: `@crystal-lattice/frontend-sdk-react` (and maybe `@crystal-lattice/frontend-sdk`)
- Create `packages/frontend-rn-components/src/index.ts` and export the selected components.

### 2) Define boundaries (authoritative)

Use `tasks/20260202-desktop-macos-frontend/900-shared-components-scope.md` as the canonical scope.

These boundaries should be stable even while the package contents evolve.

Key principle:

- Logic allowed: list/merge/categorize actions, pinned handling, tab state rendering.
- Logic not allowed: backend calls, session/message reducers, controller lifecycle management.

Additional hint (desktop “native feel”):

- Keep a clear separation between:
  - shared UI logic (“model”)
  - platform-specific presentation (“view”)
- This helps if we later adopt more macOS-native UI affordances.
  - See: `tasks/20260202-desktop-macos-frontend/920-native-elements-notes.md`

### 3) Implement an initial, proven set of components

Start with the highest leverage cross-platform pieces that are already proven in the mobile app:

- Extract the shared “actions menu model” from:
  - `mobile/crystal-lattice-control-rn/src/components/MessageActionsBar.tsx:1`
  - `mobile/crystal-lattice-control-rn/src/components/SessionActionsBar.tsx:1`
  - Suggested shape: `useActionsMenuModel(...)` (merge actions, filter, pin/unpin, grouping).
- Add a shared actions menu view with a pluggable surface:
  - `variant: 'dropdown' | 'modal'`
  - Desktop uses `dropdown`.
  - Mobile can keep `modal`.

Implementation hint:

- The `dropdown` variant can be a JS overlay initially.
- Keep an abstraction boundary so a future macOS-native menu/popover can be swapped in.
  - See: `tasks/20260202-desktop-macos-frontend/920-native-elements-notes.md`

If/when the desktop UI needs it, add desktop-first components that are still “shareable”, such as:

- `SessionTabs` (UI): renders tab strip + close buttons; controlled via props.

### 4) Prove reuse by adopting at least one component in mobile

- Replace `mobile/crystal-lattice-control-rn/src/components/MessageActionsBar.tsx` usage in-place, or create a thin wrapper that re-exports the shared component.
- Keep mobile markdown/message rendering untouched.

## Open questions (need user input)

1) Should action definitions (`messageActions.ts`, `sessionActions.ts`) move into the shared components package, or stay app-local?
   - Option A: Move to shared package (more reuse, but can constrain desktop UX).
   - Option B (recommended): Keep definitions app-local, shared components take `ActionDefinition[]` as input.

2) Icon dependency strategy
   - Option A: shared package depends on `react-native-vector-icons`.
   - Option B (recommended): shared package does not depend on an icon lib; it accepts `renderIcon(def)`.

## Verification

- Mobile builds and uses at least one shared component.
- Desktop can use `dropdown` variant without `Modal`.
