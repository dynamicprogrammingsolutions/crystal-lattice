# Shared components scope (mid-level, reusable, customizable)

This file defines what “shared components” means for Phase 5.

Goal: share components that speed up building new frontends while still allowing significant customization (e.g. desktop can choose a different markdown renderer).

## Not in scope

- Primitive UI atoms like `Button`, `TextInput`, etc.
- Full screen implementations (full chat view, full sessions list screen).
- Any component that directly calls backend APIs.

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

### 2) Session tab strip

- Controlled `SessionTabs` component:
  - renders a tab list with close buttons
  - supports optional reorder later

Key customization points:

- Render tab title (session title, agent name, etc.)
- Styling for active/inactive/dirty state

### 3) “Inspector” header widgets (future)

Not required for Phase 5, but design for extension:

- Agent selector dropdown
- Render options dropdown
- Session settings dropdown

## Proposed package

- Path: `packages/frontend-rn-components/`
- Name: `@crystal-lattice/frontend-rn-components`
- Depends on:
  - `react`, `react-native` (peer)
  - `@crystal-lattice/frontend-sdk-react` (dep)
