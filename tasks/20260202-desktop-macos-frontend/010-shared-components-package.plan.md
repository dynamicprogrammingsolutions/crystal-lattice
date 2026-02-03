# Implementation plan: 010 — Shared mid-level RN components package

This plan covers the initial implementation of `tasks/20260202-desktop-macos-frontend/010-shared-components-package.md`.

The goal is to introduce a *small, evolving* shared RN components package that extracts already-proven, high-leverage UI logic from mobile and makes it reusable for desktop (RN macOS) without locking either app into the other’s presentation choices.

## Success criteria (Phase 5)

- A new workspace package exists at `packages/frontend-rn-components/` and can be imported from RN projects.
- The package exports at least one shared “mid-level” component/hook used by mobile.
- The exported APIs are flexible enough to support desktop requirements (dropdown/anchored menus) without forcing mobile to adopt desktop UI patterns.
- No backend calls and no controller lifecycle logic live in this package.

## Non-goals (Phase 5)

- Do not attempt to extract all candidate components in `tasks/20260202-desktop-macos-frontend/930-extractable-subcomponents.md`.
- Do not build a full “chat view” shared UI.
- Do not introduce a new cross-app theme system or a shared icon library dependency.
- Do not require desktop to use mobile’s markdown renderer or modal UX.

## Proposed initial scope (what to ship first)

Ship a reusable “Actions menu” foundation, extracted from these mobile components:

- `mobile/crystal-lattice-control-rn/src/components/MessageActionsBar.tsx`
- `mobile/crystal-lattice-control-rn/src/components/SessionActionsBar.tsx`

This includes:

1) Shared model (reusable logic)

- Merge base + extra action definitions.
- Apply `availableActions` filtering.
- Determine pinned vs overflow actions.
- Provide pin/unpin helpers.

2) Shared view building blocks (minimal, theme-agnostic)

- A menu content renderer that can be hosted in either:
  - a modal surface (mobile)
  - a dropdown/anchored surface (desktop)

Mobile should be able to keep its existing look by using render props/style overrides.

## Package scaffolding

Create `packages/frontend-rn-components/` with:

- `packages/frontend-rn-components/package.json`
  - `name`: `@crystal-lattice/frontend-rn-components`
  - `private: true`
  - `main`/`types`: `src/index.ts` (match existing SDK packages)
  - `peerDependencies`: `react`, `react-native`
  - Avoid hard dependencies on `react-native-vector-icons`.
- `packages/frontend-rn-components/tsconfig.json`
  - Match `packages/frontend-sdk-react/tsconfig.json` (JSX enabled, strict, `noEmit`).
- `packages/frontend-rn-components/src/index.ts`
  - Export the model + components.

Optional (recommended) for maintainability:

- Add a small test suite for the model logic (not the RN views).
  - Use `vitest` (already used by `@crystal-lattice/frontend-sdk`).
  - Keep tests pure (no React test renderer required).

## API design (initial)

### Shared types

Define types in `packages/frontend-rn-components/src/actions/types.ts`:

- `ActionKey = string`
- `ActionDefinition`
  - Required fields: `key: string`, `label: string`
  - Allow additional fields via index signature (`[k: string]: any`) so apps can attach fields like `iconName` locally.

### Model

Implement in `packages/frontend-rn-components/src/actions/model.ts`:

- `buildActionsMenuModel(...)` (keep the API simple and string-keyed)
  - Inputs:
    - `baseActions: readonly ActionDefinition[]`
    - `extraActions?: readonly ActionDefinition[]`
    - `availableActions?: readonly string[]` (optional)
    - `pinned: readonly string[]`
    - `isActionDisabled?: (key: string) => boolean`
  - Outputs:
    - `actionsByKey: Record<string, ActionDefinition>`
    - `orderedActions: ActionDefinition[]` (base + extras, de-duped by key)
    - `visiblePinned: ActionDefinition[]` (in pinned order, filtered)
    - `visibleOverflow: ActionDefinition[]` (the rest)

Also add small pure helpers:

- `togglePinnedKey(pinned: readonly string[], key: string): string[]`
- `normalizeActionDefinitions(...)` (merge/dedupe)

### Hook

Implement in `packages/frontend-rn-components/src/actions/useActionsMenuModel.ts`:

- `useActionsMenuModel(...)`
  - Wraps `buildActionsMenuModel` in `useMemo`.
  - Provides a `togglePinned(key)` callback that calls `onChangePinned`.
  - Keeps this hook “view-agnostic”.

### View building blocks

Implement in `packages/frontend-rn-components/src/actions/`:

1) `ActionsMenuContent`

- Renders the list of actions (labels + pin toggles).
- Accepts render overrides so apps can plug in icons and styling.
- Does **not** decide whether this is modal vs dropdown.

2) `ActionsMenuSurface`

- A thin abstraction around “where the menu lives”.
- Provide two initial surfaces:
  - `ModalMenuSurface` (uses `Modal` internally; intended for mobile)
  - `DropdownMenuSurface` (uses `Modal` internally as a portal; intended for desktop)

Phase 5 baseline for `DropdownMenuSurface`:

- Render a transparent `Modal` with:
  - a full-window backdrop `Pressable` to dismiss on outside click
  - an absolutely-positioned menu container placed near the trigger
- Positioning strategy:
  - require a `ref` for the trigger element (or an `anchorLayout` passed in)
  - call `measureInWindow` when opening to get `(x, y, width, height)`
  - place the menu at approximately `(x, y + height)`
  - clamp to the window bounds (use `Dimensions.get('window')`) so the menu stays visible
- This approach meets the UX requirement (“items appear close to the trigger”) while staying swappable later for a native `NSMenu`/`NSPopover` implementation.

3) (Optional) `PinnedActionsBar`

- Composite component that:
  - Renders pinned actions row + “more” button.
  - Uses the model to render an overflow menu (with either surface).
- Keep it customizable via:
  - `renderIcon(def)`
  - style overrides
  - `variant: 'modal' | 'dropdown'`

If this composite ends up too constraining, ship only the primitives (model + content + surfaces) and keep per-app bars as wrappers.

## Mobile adoption plan (prove reuse)

Goal: mobile builds with at least one shared export in active use, with minimal behavior changes.

1) Wire dependency

- Add to `mobile/crystal-lattice-control-rn/package.json`:
  - `"@crystal-lattice/frontend-rn-components": "file:../../packages/frontend-rn-components"`

2) Update Metro config

- Update `mobile/crystal-lattice-control-rn/metro.config.js`:
  - Add `packages/frontend-rn-components` to `watchFolders`.
  - Add mapping in `resolver.extraNodeModules` for `@crystal-lattice/frontend-rn-components`.

3) Integrate in a low-risk way

Preferred approach:

- Keep the existing files as “presentation wrappers”:
  - `mobile/.../MessageActionsBar.tsx`
  - `mobile/.../SessionActionsBar.tsx`
- Replace their internal model logic (merge/filter/pin toggling) with `useActionsMenuModel`.

This keeps mobile’s theme + icon setup intact and validates that the shared API is usable.

## Follow-up / next extractions (not required for 010)

- `SessionTabs` once the desktop layout implementation starts (`050`/`080`).
- `ExpandableSection` / disclosure UI once desktop message/tool output rendering stabilizes.

## Risks / decisions to confirm before coding

Decisions confirmed:

- `DropdownMenuSurface` may use `Modal` internally as a portal; the key UX requirement is that items appear close to the trigger to minimize mouse movement.
- Keep the public API string-keyed (avoid heavy generics for ergonomics).
- Ship minimal view primitives (model + hook + small components). Apps can use either the components or the hook-only path.

Remaining risks to watch:

- Cross-platform `measureInWindow` quirks (especially on RN macOS). Keep the surface implementation isolated.
- Clipping/positioning edge cases (near bottom/right edges, window resize). Start with simple clamping.

## Verification checklist

- `npm install` works at repo root for the new workspace package.
- `packages/frontend-rn-components` exports are importable.
- Mobile Metro resolves the package without duplicate-module errors.
- Mobile builds and uses at least one shared export.
