# Subtask: Shared mid-level RN components package

Create a small shared RN components package intended to be reused by both mobile and desktop. The package should include *mid-level components with some logic* (e.g. message/session actions menus, pinned actions UI, session tabs), but avoid:

- Ultra-low-level primitives (`Button`, `Text`, etc.)
- Whole-screen components (e.g. the full chat transcript renderer, markdown renderer)

Parent Task: `tasks/20260202-desktop-macos-frontend/000-main.md`

Depends On:

- `tasks/20260129-frontend-sdk/000-main.md`

## Status

- [ ] Not started

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

### 1) Create a new package

- Create `packages/frontend-rn-components/`.
- `package.json`:
  - name: `@crystal-lattice/frontend-rn-components`
  - peer deps: `react`, `react-native`
  - deps: `@crystal-lattice/frontend-sdk-react` (and maybe `@crystal-lattice/frontend-sdk`)
- Create `packages/frontend-rn-components/src/index.ts` and export the selected components.

### 2) Define component boundaries (authoritative)

Use `tasks/20260202-desktop-macos-frontend/900-shared-components-scope.md` as the canonical scope.

Key principle:

- Logic allowed: list/merge/categorize actions, pinned handling, tab state rendering.
- Logic not allowed: backend calls, session/message reducers, controller lifecycle management.

### 3) Implement components

Start with the highest leverage cross-platform pieces:

- `PinnedActionsBar` (headless-ish): renders pinned action icons + “more” menu.
- `ActionsMenu` (UI): supports `variant: 'dropdown' | 'modal'`.
  - Desktop uses `dropdown`.
  - Mobile can keep `modal`.
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
