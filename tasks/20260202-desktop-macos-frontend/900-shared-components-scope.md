# Shared components scope (mid-level, reusable, customizable)

This file defines what “shared components” means for Phase 5.

Goal: share components that speed up building new frontends while still allowing significant customization (e.g. desktop can choose a different markdown renderer).

## Not in scope

- Primitive UI atoms like `Button`, `TextInput`, etc.
- Full screen implementations (full chat view, full sessions list screen).
- Any component that directly calls backend APIs.

Clarification:

- It can still be in scope to share *presentational row/bubble components* (e.g. `SessionListItem`, `MessageBubble`) as long as:
  - they don’t own whole-screen layout
  - they don’t call backend APIs directly
  - they stay customizable (icons, menus, render mode)

## In scope (candidates)

### 1) Action UI (message + session)

These components contain meaningful UI logic:

- Pinned actions bar (pinned icons + overflow menu)
- Overflow menu rendering and pin/unpin interaction
- “Disable action” logic via props

Key customization points:

- Provide action definitions via props (do not force shared action keys across apps).
- Provide icon rendering via props (avoid locking into `react-native-vector-icons`).
- Provide menu rendering style via variant:
  - mobile: modal
  - desktop: anchored dropdown

Implementation hint:

- Consider splitting “model” from “view”:
  - shared: `useActionsMenuModel(...)`
  - platform UI: `ActionsMenuView` (potentially via `*.macos.tsx` overrides later)

### 2) Session tab strip

- Controlled `SessionTabs` component:
  - renders a tab list with close buttons
  - supports optional reorder later

Key customization points:

- Render tab title (session title, agent name, etc.)
- Styling for active/inactive/dirty state

Implementation hint:

- RN macOS adds desktop-specific props/events (hover, focus ring, tooltips, key handling).
- Keep the component API stable and allow later macOS-specific enhancements without changing callers.
  - See: `tasks/20260202-desktop-macos-frontend/920-native-elements-notes.md`

### 3) “Inspector” header widgets (future)

### 4) Presentational building blocks (optional)

These are not required for Phase 5, but are candidates if they reduce duplication:

- `MessageBubble` (or per-role message bubble components)
- `SessionListItem` (a reusable visual row used by sessions lists)

These should remain “dumb” renderers that accept props/state and callback handlers.

Not required for Phase 5, but design for extension:

- Agent selector dropdown
- Render options dropdown
- Session settings dropdown

Implementation hint:

- For “dropdowns”, it may be simplest to start with a JS overlay-based menu.
- Keep a path open for a future macOS-native `NSMenu`/`NSPopover` implementation.
  - See: `tasks/20260202-desktop-macos-frontend/920-native-elements-notes.md`

## Proposed package

- Path: `packages/frontend-rn-components/`
- Name: `@crystal-lattice/frontend-rn-components`
- Depends on:
  - `react`, `react-native` (peer)
  - `@crystal-lattice/frontend-sdk-react` (dep)
